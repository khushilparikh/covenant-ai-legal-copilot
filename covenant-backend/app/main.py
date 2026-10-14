import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import audit, auth, billing, chat, compliance, comparison, contracts, dashboard, redline, search
from app.core.config import get_settings
from app.db.database import Base, engine

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="AI-powered contract analysis and compliance management platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Return a JSON 500 *with CORS headers* so the browser shows the real error
    instead of a misleading 'blocked by CORS policy' message."""
    traceback.print_exception(type(exc), exc, exc.__traceback__)
    origin = request.headers.get("origin", "")
    headers = {}
    if origin in settings.CORS_ORIGINS:
        headers = {"Access-Control-Allow-Origin": origin, "Access-Control-Allow-Credentials": "true"}
    return JSONResponse(status_code=500, content={"detail": f"{type(exc).__name__}: {exc}"}, headers=headers)


app.include_router(auth.router)
app.include_router(contracts.router)
app.include_router(compliance.router)
app.include_router(chat.router)
app.include_router(comparison.router)
app.include_router(dashboard.router)
app.include_router(search.router)
app.include_router(redline.router)
app.include_router(audit.router)
app.include_router(billing.router)


@app.on_event("startup")
def on_startup():
    # For a class project, create_all is simpler than running Alembic
    # migrations every time. Swap for `alembic upgrade head` (see
    # alembic/README) once the schema needs versioned migrations.
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": settings.APP_NAME}
