import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .db import client, ensure_indexes
from .errors import AppError
from .routers import ai, auth, expenses, payments, statements, trips, uploads, users, webhooks

log = logging.getLogger("tripbank")


@asynccontextmanager
async def lifespan(_app):
    if settings.app_env == "production" and settings.jwt_secret in ("", "change-me"):
        raise RuntimeError("JWT_SECRET must be set in production")
    ensure_indexes()
    yield


app = FastAPI(title="SplitWise AI - TripBank API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.frontend_origin.split(",") if o.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error(_req: Request, exc: AppError):
    return JSONResponse(status_code=exc.status, content={"error": {"code": exc.code, "message": exc.message}})


@app.exception_handler(RequestValidationError)
async def validation_error(_req: Request, exc: RequestValidationError):
    fields = [{"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_ERROR", "message": "Please check the highlighted fields", "fields": fields}})


@app.exception_handler(Exception)
async def unhandled(_req: Request, exc: Exception):
    log.exception("unhandled error", exc_info=exc)
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "Something went wrong"}})


api = APIRouter(prefix="/api/v1")
for r in (auth, users, trips, payments, webhooks, expenses, ai, statements, uploads):
    api.include_router(r.router)


@api.get("/health")
def health():
    try:
        client.admin.command("ping")
        return {"status": "ok", "database": "up"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "degraded", "database": "down"})


app.include_router(api)


@app.get("/health")
def root_health():
    return health()
