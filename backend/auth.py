"""Password hashing + JWT (HS256) using stdlib only — no pip needed."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
ALG = "HS256"
EXP_HOURS = 12


def hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return dk.hex(), salt.hex()


def verify_password(password: str, pw_hash: str, salt_hex: str) -> bool:
    calc, _ = hash_password(password, salt_hex)
    return hmac.compare_digest(calc, pw_hash)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_json(obj: dict) -> str:
    return _b64url(json.dumps(obj, separators=(",", ":")).encode())


def create_token(user_id: int, email: str, exp_hours: int = EXP_HOURS) -> str:
    header = _b64url_json({"alg": ALG, "typ": "JWT"})
    payload = _b64url_json({"sub": user_id, "email": email, "exp": int(time.time()) + exp_hours * 3600})
    sig = _b64url(hmac.new(SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{sig}"


def verify_token(token: str) -> dict | None:
    try:
        header_b64, payload_b64, sig = token.split(".")
        expected = _b64url(hmac.new(SECRET.encode(), f"{header_b64}.{payload_b64}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            return None
        pad = "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + pad).decode())
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None
