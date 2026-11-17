"""Tests for outbound-fetch guarding, secret encryption, file ownership and the LLM client."""
import sqlite3
from pathlib import Path
from unittest import mock

import pytest
from cryptography.fernet import Fernet

import api
import secret_box
from net_safety import UnsafeURLError, assert_public_url, safe_get


# --- Outbound fetch guard ---------------------------------------------------

@pytest.mark.parametrize("url", [
    "http://127.0.0.1/",
    "http://localhost/",
    "http://169.254.169.254/latest/meta-data/",
    "http://10.1.2.3/",
    "http://192.168.0.1/",
    "http://[::1]/",
    "http://[::ffff:127.0.0.1]/",
    "http://0.0.0.0/",
    "file:///etc/passwd",
    "gopher://127.0.0.1/",
    "http://8.8.8.8:8005/",
    "https://user:pass@8.8.8.8/",
])
def test_internal_and_non_web_urls_are_blocked(url):
    with pytest.raises(UnsafeURLError):
        assert_public_url(url)


def test_public_ip_literal_is_allowed():
    assert assert_public_url("https://8.8.8.8/") == "https://8.8.8.8/"


def test_redirect_into_internal_network_is_blocked():
    redirect = mock.Mock(is_redirect=True, is_permanent_redirect=False, headers={"Location": "http://127.0.0.1/admin"})
    with mock.patch("net_safety.requests.get", return_value=redirect) as get:
        with pytest.raises(UnsafeURLError):
            safe_get("https://8.8.8.8/")
    assert get.call_count == 1  # never connected to the internal hop


def test_website_parser_reports_blocked_address():
    from ingestion.intake_engine import IntakeEngine
    result = IntakeEngine(user_id="user_hardening1").scrape_personal_website("http://169.254.169.254/")
    assert "can't be fetched" in result["error"]


# --- SMTP password encryption -----------------------------------------------

@pytest.fixture
def fresh_key(monkeypatch):
    monkeypatch.setenv("DATA_ENCRYPTION_KEY", Fernet.generate_key().decode())
    secret_box._fernet.cache_clear()
    yield
    secret_box._fernet.cache_clear()


def test_secret_round_trip(fresh_key):
    token = secret_box.encrypt("app-password-123")
    assert token.startswith(secret_box.PREFIX) and "app-password-123" not in token
    assert secret_box.decrypt(token) == "app-password-123"


def test_smtp_password_stored_encrypted_and_legacy_rows_migrated(fresh_key, tmp_path):
    from outreach.tracker import ApplicationTracker
    db = tmp_path / "apps.db"
    tracker = ApplicationTracker(db_path=db)
    tracker.save_user_settings("default", {"smtp_user": "me@example.com", "smtp_password": "s3cret"})

    raw = sqlite3.connect(db).execute("SELECT smtp_password FROM user_settings WHERE user_id='default'").fetchone()[0]
    assert raw.startswith(secret_box.PREFIX) and "s3cret" not in raw
    assert tracker.get_user_settings("default")["smtp_password"] == "s3cret"

    # A plaintext row written by an older version is encrypted on next startup
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE user_settings SET smtp_password='legacy-plain' WHERE user_id='default'")
    ApplicationTracker(db_path=db)
    raw = sqlite3.connect(db).execute("SELECT smtp_password FROM user_settings WHERE user_id='default'").fetchone()[0]
    assert raw.startswith(secret_box.PREFIX)
    assert tracker.get_user_settings("default")["smtp_password"] == "legacy-plain"


def test_wrong_key_yields_empty_password_not_crash(fresh_key, monkeypatch):
    token = secret_box.encrypt("s3cret")
    monkeypatch.setenv("DATA_ENCRYPTION_KEY", Fernet.generate_key().decode())
    secret_box._fernet.cache_clear()
    assert secret_box.decrypt(token) == ""


# --- File ownership -----------------------------------------------------------

@pytest.fixture
def data_dirs(tmp_path, monkeypatch):
    uploads, generated = tmp_path / "uploads", tmp_path / "generated"
    uploads.mkdir(); generated.mkdir()
    monkeypatch.setattr(api, "UPLOADS_DIR", uploads)
    monkeypatch.setattr(api, "GENERATED_DIR", generated)
    monkeypatch.delenv("ALLOW_DEV_AUTH", raising=False)
    return uploads, generated


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-1.4")
    return path


def test_own_folder_allowed_but_prefix_sibling_folder_denied(data_dirs):
    uploads, _ = data_dirs
    mine = _touch(uploads / "user_abc" / "cv.pdf")
    sibling = _touch(uploads / "user_abcd" / "cv.pdf")
    assert api.validate_safe_user_file_path(str(mine), "user_abc") == mine.resolve()
    with pytest.raises(api.HTTPException) as e:
        api.validate_safe_user_file_path(str(sibling), "user_abc")
    assert e.value.status_code == 403


def test_shared_folder_requires_exact_owner_prefix(data_dirs):
    _, generated = data_dirs
    mine = _touch(generated / "Europass_CV_user_abc_Acme.pdf")
    theirs = _touch(generated / "Europass_CV_user_abcd_Acme.pdf")
    name_contains_me = _touch(generated / "Cover_Letter_user_zzz_user_abc_.pdf")
    assert api.validate_safe_user_file_path(str(mine), "user_abc")
    for other in (theirs, name_contains_me):
        with pytest.raises(api.HTTPException):
            api.validate_safe_user_file_path(str(other), "user_abc")


def test_traversal_and_system_files_denied(data_dirs):
    uploads, _ = data_dirs
    with pytest.raises(api.HTTPException):
        api.validate_safe_user_file_path(str(uploads / "user_abc" / ".." / ".." / "applications.db"), "user_abc")
    with pytest.raises(api.HTTPException):
        api.find_user_file_by_name("../applications.db", "user_abc")


def test_preview_lookup_hides_other_users_files(data_dirs):
    uploads, _ = data_dirs
    _touch(uploads / "manual_user_abcd_cv_1_x.pdf")
    with pytest.raises(api.HTTPException) as e:
        api.find_user_file_by_name("manual_user_abcd_cv_1_x.pdf", "user_abc")
    assert e.value.status_code == 404


# --- LLM client ---------------------------------------------------------------

def test_gemini_key_sent_in_header_not_url(monkeypatch):
    from generators import llm_client
    client = llm_client.LLMClient("gemini")
    client.gemini_key, client.openai_key, client.anthropic_key = "g-key-123", "", ""
    ok = mock.Mock(status_code=200, json=lambda: {"candidates": [{"content": {"parts": [{"text": "hello"}]}}]})
    with mock.patch.object(llm_client.requests, "post", return_value=ok) as post:
        assert client.generate("hi") == "hello"
    url = post.call_args.args[0]
    assert "g-key-123" not in url
    assert post.call_args.kwargs["headers"]["x-goog-api-key"] == "g-key-123"
    assert post.call_args.kwargs["timeout"][1] >= 60
