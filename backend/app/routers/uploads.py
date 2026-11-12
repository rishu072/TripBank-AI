import hashlib

from fastapi import APIRouter, Depends

from ..config import settings
from ..deps import TripCtx, organizer
from ..errors import AppError
from ..utils import now

router = APIRouter(tags=["uploads"])


@router.post("/trips/{trip_id}/uploads/signature")
def signature(ctx: TripCtx = Depends(organizer)):
    if not (settings.cloudinary_cloud_name and settings.cloudinary_api_key and settings.cloudinary_api_secret):
        raise AppError("UPLOADS_NOT_CONFIGURED", "Receipt uploads are not configured", 503)
    params = {"folder": f"tripbank/{ctx.tid}", "timestamp": str(int(now().timestamp()))}
    to_sign = "&".join(f"{k}={params[k]}" for k in sorted(params)) + settings.cloudinary_api_secret
    return {**params, "signature": hashlib.sha1(to_sign.encode()).hexdigest(), "api_key": settings.cloudinary_api_key, "cloud_name": settings.cloudinary_cloud_name}
