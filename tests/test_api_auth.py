"""Authentication guard tests: identity must come from a signed token, and every
non-public API route must require it."""
import pytest
from fastapi.testclient import TestClient

import api
from api import app, create_access_token, get_current_user_id

PUBLIC_ROUTES = {
    "/api/health",
    "/api/auth/register",
    "/api/auth/login",
    "/api/auth/google",
    "/api/auth/google/config",
    # Refuse with 403 unless single-user local mode is enabled
    "/api/auth/users",
    "/api/auth/switch",
}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("ALLOW_DEV_AUTH", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    return TestClient(app)


def _requires_auth(route) -> bool:
    stack = list(route.dependant.dependencies)
    while stack:
        dep = stack.pop()
        if dep.call is get_current_user_id:
            return True
        stack.extend(dep.dependencies)
    return False


def test_every_non_public_route_requires_auth():
    unguarded = [
        r.path for r in app.routes
        if getattr(r, "path", "").startswith("/api/")
        and r.path not in PUBLIC_ROUTES
        and not _requires_auth(r)
    ]
    assert unguarded == []


@pytest.mark.parametrize("method,path", [
    ("get", "/api/profile"),
    ("get", "/api/settings"),
    ("get", "/api/tracker/applications"),
    ("get", "/api/jobs/stream"),
    ("get", "/api/jobs/remote"),
    ("get", "/api/jobs/dubai"),
    ("get", "/api/hr/by-role/stream"),
    ("get", "/api/portals"),
    ("post", "/api/jobs/search"),
    ("post", "/api/hr/by-company"),
    ("post", "/api/cv/generate-pdf"),
    ("post", "/api/cv-hunter/search"),
])
def test_anonymous_requests_are_rejected(client, method, path):
    assert getattr(client, method)(path).status_code == 401


def test_identity_cannot_be_spoofed_by_header_or_query(client):
    assert client.get("/api/profile", headers={"X-User-Id": "default"}).status_code == 401
    assert client.get("/api/profile?user_id=default").status_code == 401
    assert client.get("/api/auth/me", headers={"X-User-Id": "admin"}).status_code == 401


def test_invalid_token_is_rejected(client):
    assert client.get("/api/settings", headers={"Authorization": "Bearer not-a-jwt"}).status_code == 401
    assert client.get("/api/settings?access_token=not-a-jwt").status_code == 401


def test_valid_token_is_accepted_via_header_and_query(client):
    token = create_access_token("user_auth_test_1", "auth.test@example.com")
    assert client.get("/api/settings", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    assert client.get(f"/api/settings?access_token={token}").status_code == 200


def test_user_switching_and_listing_disabled_without_local_mode(client):
    assert client.get("/api/auth/users").status_code == 403
    assert client.post("/api/auth/switch", json={"user_id": "default"}).status_code == 403


def test_body_user_id_cannot_redirect_to_another_profile(client):
    assert api.resolve_target_user("user_a", "user_b") == "user_a"


def test_local_mode_serves_loopback_clients_only(monkeypatch):
    monkeypatch.setenv("ALLOW_DEV_AUTH", "true")
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    local = TestClient(app, client=("127.0.0.1", 50000))
    remote = TestClient(app, client=("203.0.113.9", 50000))
    assert local.get("/api/settings").status_code == 200
    assert remote.get("/api/settings").status_code == 401
    assert api.resolve_target_user("user_a", "user_b") == "user_b"


def test_local_mode_is_ignored_in_production(monkeypatch):
    monkeypatch.setenv("ALLOW_DEV_AUTH", "true")
    monkeypatch.setenv("APP_ENV", "production")
    local = TestClient(app, client=("127.0.0.1", 50000))
    assert local.get("/api/settings").status_code == 401
    assert local.post("/api/auth/switch", json={"user_id": "default"}).status_code == 403


def test_no_hardcoded_jwt_secret():
    assert not hasattr(api, "DEFAULT_DEV_JWT_SECRET")
    assert len(api.JWT_SECRET) >= 32
