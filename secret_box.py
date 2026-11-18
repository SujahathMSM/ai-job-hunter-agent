"""Encryption for secrets stored in the database (currently users' SMTP passwords).

Production requires DATA_ENCRYPTION_KEY (a Fernet key, generate one with
`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`).
Local installs get a random key generated once in data/.data_key.
"""
import os
from functools import lru_cache
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from config import DATA_DIR, is_production_mode

PREFIX = "enc:v1:"
KEY_FILE = DATA_DIR / ".data_key"


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    env_key = os.getenv("DATA_ENCRYPTION_KEY", "").strip()
    if env_key:
        return Fernet(env_key.encode())
    if is_production_mode():
        raise RuntimeError("CRITICAL SECURITY ERROR: DATA_ENCRYPTION_KEY must be set in production mode.")
    if KEY_FILE.exists():
        return Fernet(KEY_FILE.read_text(encoding="utf-8").strip().encode())
    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)
    try:
        os.chmod(KEY_FILE, 0o600)
    except OSError:
        pass
    return Fernet(key)


def is_encrypted(value: Optional[str]) -> bool:
    return bool(value) and value.startswith(PREFIX)


def encrypt(plaintext: str) -> str:
    if not plaintext:
        return ""
    return PREFIX + _fernet().encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt(stored: Optional[str]) -> str:
    """Returns the plaintext, or "" if the value can't be decrypted (e.g. the key changed).
    Values saved before encryption existed are returned as-is."""
    if not stored:
        return ""
    if not is_encrypted(stored):
        return stored
    try:
        return _fernet().decrypt(stored[len(PREFIX):].encode("ascii")).decode("utf-8")
    except InvalidToken:
        print("[Secret Box] Stored secret could not be decrypted with the current key; it must be re-entered.")
        return ""
