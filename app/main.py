"""
EdgeChat Backend — FastAPI app entry point.
Run: uvicorn app.main:app --reload
Docs: http://localhost:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.dependencies import SessionDep, engine
from app.models import Base
from app.api.v1 import auth as auth_router, ai as ai_router, chat as chat_router, usage as usage_router
from app.middleware import RequestIDMiddleware, RateLimitMiddleware, UsageLogMiddleware, REQUEST_ID_HEADER
from app.core.redis_client import init_redis, close_redis
from app.core.mongo import init_mongo, close_mongo

# Lifespan: create tables on startup, init Redis (Step 6), dispose on shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_redis()
    await init_mongo()
    try:
        yield
    finally:
        await close_mongo()
        await close_redis()
        await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend for mobile AI app: auth, chat, vision, summarization",
    version="0.1.0",
    lifespan=lifespan,
)

# Step 5 — Middleware order: first added = outermost. Request ID first, then rate limit (Step 6), then CORS.
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(UsageLogMiddleware)

# CORS: allow frontend/mobile to call API. Origins from config (comma-separated or "*").
_origins = ["*"] if settings.CORS_ORIGINS.strip() == "*" else [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Step 5 — Global exception handlers: consistent JSON and request_id for tracing
def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    body = {"detail": exc.detail}
    if rid := _request_id(request):
        body["request_id"] = rid
    response = JSONResponse(status_code=exc.status_code, content=body)
    if rid := _request_id(request):
        response.headers[REQUEST_ID_HEADER] = rid
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    body = {"detail": "Internal server error"}
    if rid := _request_id(request):
        body["request_id"] = rid
    response = JSONResponse(status_code=500, content=body)
    if rid := _request_id(request):
        response.headers[REQUEST_ID_HEADER] = rid
    return response


app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(ai_router.router, prefix="/api/v1")
app.include_router(chat_router.router, prefix="/api/v1")
app.include_router(usage_router.router, prefix="/api/v1")


@app.get("/")
def root():
    """Step 0–1: app name from config."""
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/api/v1/health/db")
async def health_db(session: SessionDep):
    """Step 2: verify DB connection and session. Runs a simple query."""
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


@app.get("/api/v1/health/mongo")
async def health_mongo():
    """Day 4 Step 2: verify MongoDB connection."""
    from app.core.mongo import get_database
    db = get_database()
    if db is None:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "mongo": "not initialized"},
        )
    try:
        await db.client.admin.command("ping")
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "mongo": "connection failed"},
        )
    return {"status": "ok", "mongo": "connected"}
