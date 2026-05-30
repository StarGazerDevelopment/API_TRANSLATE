from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.config import FRONTEND_DIST_DIR, settings
from app.db import SessionLocal, init_db
from app.models import Setting
from app.routes import register_dynamic_gateway_routes, router
from app.services import ensure_default_state, minimal_status_html


logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("api_translate")


def create_app(minimal: bool = False) -> FastAPI:
    docs_url = "/docs" if settings.docs_enabled else None
    redoc_url = "/redoc" if settings.docs_enabled else None
    app = FastAPI(title=settings.app_name, version="0.1.0", docs_url=docs_url, redoc_url=redoc_url)
    app.state.minimal_mode = minimal

    init_db()
    with SessionLocal() as db:
        ensure_default_state(db)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        with SessionLocal() as db:
            ensure_default_state(db)
            record = db.scalar(select(Setting).limit(1))
            secure_headers_enabled = bool(record.secure_headers_enabled) if record else True
            if secure_headers_enabled:
                response.headers["X-Frame-Options"] = "DENY"
                response.headers["X-Content-Type-Options"] = "nosniff"
                response.headers["Referrer-Policy"] = "same-origin"
                response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        return response

    @app.on_event("startup")
    def startup() -> None:
        init_db()
        with SessionLocal() as db:
            ensure_default_state(db)
        register_dynamic_gateway_routes(app)
        logger.info("AI-Translator started. Minimal mode=%s", minimal)

    @app.exception_handler(Exception)
    async def unhandled_error(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server error: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})

    app.include_router(router)

    @app.get("/api/runtime")
    async def runtime() -> dict[str, object]:
        return {
            "name": settings.app_name,
            "minimalMode": minimal,
            "frontendBuilt": FRONTEND_DIST_DIR.exists(),
            "docsEnabled": settings.docs_enabled,
        }

    if FRONTEND_DIST_DIR.exists() and not minimal:
        assets_dir = FRONTEND_DIST_DIR / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False, response_model=None)
        async def serve_frontend(full_path: str) -> Response:
            requested_path = FRONTEND_DIST_DIR / full_path
            if full_path and requested_path.exists() and requested_path.is_file():
                return FileResponse(requested_path)
            return FileResponse(FRONTEND_DIST_DIR / "index.html")

    else:

        @app.get("/", include_in_schema=False)
        async def serve_status() -> HTMLResponse:
            with SessionLocal() as db:
                ensure_default_state(db)
                return HTMLResponse(minimal_status_html(db))

    return app
