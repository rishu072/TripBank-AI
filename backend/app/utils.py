from datetime import date, datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId

from .db import db
from .errors import AppError

HIDDEN = {"password_hash", "invite_hash", "token_version", "reset_hash", "reset_expires_at"}


def now():
    return datetime.now(timezone.utc)


def today():
    return date.today().isoformat()


def oid(value):
    try:
        return ObjectId(str(value))
    except (InvalidId, TypeError):
        raise AppError("NOT_FOUND", "Resource not found", 404)


def clean(doc):
    out = {}
    for k, v in doc.items():
        if k in HIDDEN:
            continue
        if k == "_id":
            out["id"] = str(v)
        elif isinstance(v, ObjectId):
            out[k] = str(v)
        elif isinstance(v, datetime):
            out[k] = v.isoformat()
        elif isinstance(v, dict):
            out[k] = clean(v)
        elif isinstance(v, list):
            out[k] = [clean(i) if isinstance(i, dict) else i for i in v]
        else:
            out[k] = v
    return out


def audit(trip_id, actor_id, action, detail=None):
    db.audit_events.insert_one(
        {"trip_id": trip_id, "actor_id": actor_id, "action": action, "detail": detail or {}, "created_at": now()}
    )
