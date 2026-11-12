from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .db import db
from .errors import AppError
from .security import decode_token
from .utils import oid

bearer = HTTPBearer(auto_error=False)


@dataclass
class TripCtx:
    trip: dict
    member: dict
    user: dict

    @property
    def tid(self) -> str:
        return str(self.trip["_id"])

    @property
    def uid(self) -> str:
        return str(self.user["_id"])

    @property
    def is_organizer(self) -> bool:
        return self.member["role"] == "organizer"


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    if not creds:
        raise AppError("UNAUTHENTICATED", "Sign in required", 401)
    payload = decode_token(creds.credentials)
    user = db.users.find_one({"_id": oid(payload["sub"])})
    if not user or user.get("token_version", 0) != payload.get("ver"):
        raise AppError("UNAUTHENTICATED", "Session expired or invalid", 401)
    return user


def load_ctx(trip_id: str, user: dict) -> TripCtx:
    try:
        trip = db.trips.find_one({"_id": oid(trip_id)})
    except AppError:
        trip = None
    member = None
    if trip:
        member = db.trip_members.find_one({"trip_id": trip_id, "user_id": str(user["_id"]), "status": "active"})
    if not trip or not member:
        raise AppError("NOT_TRIP_MEMBER", "You are not a member of this trip", 403)
    return TripCtx(trip, member, user)


def trip_member(trip_id: str, user: dict = Depends(current_user)) -> TripCtx:
    return load_ctx(trip_id, user)


def organizer(ctx: TripCtx = Depends(trip_member)) -> TripCtx:
    if not ctx.is_organizer:
        raise AppError("NOT_ORGANIZER", "Only the organizer can do this", 403)
    return ctx
