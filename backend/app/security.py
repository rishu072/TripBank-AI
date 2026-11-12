import hashlib
import secrets
from datetime import timedelta

import bcrypt
import jwt

from .config import settings
from .errors import AppError
from .utils import now

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
DUMMY_HASH = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt()).decode()


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode()[:72], hashed.encode())
    except ValueError:
        return False


def create_token(user: dict) -> str:
    exp = now() + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user["_id"]), "ver": user.get("token_version", 0), "exp": exp}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise AppError("UNAUTHENTICATED", "Session expired or invalid", 401)


def sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def norm_code(code: str) -> str:
    return "".join(ch for ch in code.upper() if ch.isalnum())


def new_invite_code() -> str:
    raw = "".join(secrets.choice(ALPHABET) for _ in range(8))
    return f"{raw[:4]}-{raw[4:]}"
