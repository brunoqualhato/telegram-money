from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .auth import bootstrap_owner
from .config import settings
from .crud import audit, rows
from .db import SessionLocal
from .routers import (
    auth,
    documents,
    events,
    integrations,
    notifications,
    portfolio,
    reports,
    rules,
    system,
    treasury,
)
from .services.ai import available_models


@asynccontextmanager
async def lifespan(app):
    # O esquema é criado por Alembic, nunca por create_all em produção.
    with SessionLocal() as db:
        bootstrap_owner(db)
        if settings().demo_mode:
            from .seed import seed_demo

            seed_demo(db)
    yield


app = FastAPI(title="Telegram Money", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=list(
        {"localhost", "127.0.0.1", "testserver", urlparse(settings().app_origin).hostname or "localhost"}
    ),
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    if request.url.path.startswith("/api/") and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        if request.headers.get("origin") != settings().app_origin.rstrip("/"):
            return JSONResponse({"detail": "Origem da requisição inválida"}, status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    if not request.url.path.startswith(("/docs", "/openapi.json", "/redoc")):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
    return response


# Registro de rotas modulares por domínio
app.include_router(system.router)
app.include_router(auth.router)
app.include_router(portfolio.router)
app.include_router(rules.router)
app.include_router(notifications.router)
app.include_router(events.router)
app.include_router(documents.router)
app.include_router(treasury.router)
app.include_router(reports.router)
app.include_router(integrations.router)

frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if (frontend_dist / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")


@app.get("/")
def index():
    if not (frontend_dist / "index.html").exists():
        return JSONResponse(
            {"message": "Compile o painel: cd frontend && npm ci && npm run build", "docs": "/docs"}
        )
    return FileResponse(frontend_dist / "index.html")


__all__ = ["app", "audit", "rows", "available_models"]
