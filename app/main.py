import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from app.database.session import engine
from app.routers.tasks import router as tasks_router
from app.routers.ui import router as ui_router

logger = logging.getLogger("task_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tables are created by Alembic migrations; engine is warmed for health.
    yield
    engine.dispose()


app = FastAPI(
    title="Task Management API",
    description="Create, list, filter, update status, and delete tasks.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log method, path, status, and duration for each request."""
    request_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()
    logger.info("%s %s [req=%s]", request.method, request.url.path, request_id)
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled error [req=%s]", request_id)
        raise
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s in %.2fms [req=%s]",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request_id,
    )
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Return structured JSON for HTTPException.detail when it is a dict with code/message."""
    if isinstance(exc.detail, dict) and "code" in exc.detail and "message" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "http_error",
                "message": str(exc.detail) if exc.detail else exc.__class__.__name__,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Keep validation errors consistent and beginner-friendly.
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {"code": "validation_error", "message": "Request validation failed."},
            "details": exc.errors(),
        },
    )


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}


app.include_router(tasks_router)
app.include_router(ui_router)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


configure_logging()
