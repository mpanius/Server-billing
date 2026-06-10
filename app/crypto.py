from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

FERNET_PREFIX = "fernet:"


def cipher() -> Fernet | None:
    key = settings.app_encryption_key.strip()
    if not key:
        return None
    return Fernet(key.encode("utf-8"))


def encrypt_secret(value: str) -> str:
    if not value or value.startswith(FERNET_PREFIX):
        return value
    active_cipher = cipher()
    if active_cipher is None:
        return value
    token = active_cipher.encrypt(value.encode("utf-8")).decode("utf-8")
    return FERNET_PREFIX + token


def decrypt_secret(value: str) -> str:
    if not value:
        return ""
    if not value.startswith(FERNET_PREFIX):
        return value
    active_cipher = cipher()
    if active_cipher is None:
        return ""
    token = value.removeprefix(FERNET_PREFIX).encode("utf-8")
    try:
        return active_cipher.decrypt(token).decode("utf-8")
    except InvalidToken:
        return ""


def is_encrypted(value: str) -> bool:
    return bool(value and value.startswith(FERNET_PREFIX))
