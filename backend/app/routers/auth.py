import logging
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends
from pymongo.errors import DuplicateKeyError

from ..config import settings
from ..db import db
from ..errors import AppError
from ..ratelimit import limiter
from ..schemas import ForgotIn, LoginIn, RegisterIn, ResetIn
from ..security import DUMMY_HASH, create_token, hash_password, sha, verify_password
from ..utils import now

router = APIRouter(prefix="/auth", tags=["auth"])
log = logging.getLogger("tripbank")


def public_user(u):
    return {
        "id": str(u["_id"]),
        "name": u["name"],
        "email": u["email_normalized"],
        "avatar_url": u.get("avatar_url"),
        "theme": u.get("theme", "system"),
        "notifications": u.get("notifications", {}),
    }


@router.post("/register", status_code=201)
def register(body: RegisterIn, _=Depends(limiter("register", 10, 60))):
    doc = {
        "name": body.name.strip(),
        "email_normalized": body.email.lower().strip(),
        "password_hash": hash_password(body.password),
        "avatar_url": None,
        "theme": "system",
        "notifications": {"email": True},
        "token_version": 0,
        "created_at": now(),
    }
    try:
        res = db.users.insert_one(doc)
    except DuplicateKeyError:
        raise AppError("EMAIL_TAKEN", "An account with this email already exists", 409)
    user = db.users.find_one({"_id": res.inserted_id})
    return {"access_token": create_token(user), "token_type": "bearer", "user": public_user(user)}


@router.post("/login")
def login(body: LoginIn, _=Depends(limiter("login", 10, 60))):
    user = db.users.find_one({"email_normalized": body.email.lower().strip()})
    ok = verify_password(body.password, user["password_hash"] if user else DUMMY_HASH)
    if not user or not ok:
        raise AppError("INVALID_CREDENTIALS", "Email or password is incorrect", 401)
    return {"access_token": create_token(user), "token_type": "bearer", "user": public_user(user)}


@router.post("/forgot-password", status_code=202)
def forgot(body: ForgotIn, _=Depends(limiter("forgot", 5, 60))):
    user = db.users.find_one({"email_normalized": body.email.lower().strip()})
    if user:
        token = secrets.token_urlsafe(32)
        db.users.update_one(
            {"_id": user["_id"]}, {"$set": {"reset_hash": sha(token), "reset_expires_at": now() + timedelta(minutes=30)}}
        )
        if settings.app_env != "production":
            origin = settings.frontend_origin.split(",")[0]
            log.warning("Password reset link: %s/reset-password?token=%s", origin, token)
    return {"status": "If the account exists, a reset link has been issued"}


@router.post("/reset-password")
def reset(body: ResetIn, _=Depends(limiter("reset", 5, 60))):
    user = db.users.find_one({"reset_hash": sha(body.token)})
    if not user or user.get("reset_expires_at") is None or user["reset_expires_at"] < now():
        raise AppError("RESET_INVALID", "Reset link is invalid or expired", 400)
    db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"password_hash": hash_password(body.new_password)}, "$inc": {"token_version": 1}, "$unset": {"reset_hash": "", "reset_expires_at": ""}},
    )
    return {"status": "Password updated"}
