from __future__ import annotations

import logging
import shutil
import subprocess

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.config import FRONTEND_DIST_DIR, ROOT_DIR, settings
from app.db import SessionLocal, init_db
from app.models import Setting
from app.routes import register_dynamic_gateway_routes, router
from app.services import ensure_default_state, minimal_status_html


logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("api_translate")


def _build_frontend() -> tuple[bool, str | None]:
    frontend_dir = ROOT_DIR / "frontend"
    if not frontend_dir.exists():
        return False, "The frontend source folder is missing."
    if shutil.which("npm") is None:
        return False, "npm is not installed, so AI-Translator cannot build the dashboard automatically."

    commands = []
    if not (frontend_dir / "node_modules").exists():
        commands.append(["npm", "install"])
    commands.append(["npm", "run", "build"])

    for command in commands:
        try:
            result = subprocess.run(command, cwd=frontend_dir, capture_output=True, text=True, timeout=900)
        except subprocess.TimeoutExpired:
            return False, f"{' '.join(command)} timed out after 15 minutes."
        except Exception as exc:  # noqa: BLE001
            return False, f"{' '.join(command)} could not start: {exc}"
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "Unknown build error.").strip()
            return False, detail

    return FRONTEND_DIST_DIR.exists(), None if FRONTEND_DIST_DIR.exists() else "The frontend build finished but dist output was not created."


def frontend_setup_html(error: str | None = None) -> str:
    message = error or "The dashboard assets are not available yet."
    return f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>AI-Translator Dashboard Setup</title>
  <style>
    body {{ background:#09090b; color:#f4f4f5; font-family:Arial,sans-serif; margin:0; padding:32px; }}
    .card {{ background:#18181b; border:1px solid #27272a; border-radius:20px; padding:24px; max-width:840px; }}
    code, pre {{ background:#0f0f14; border-radius:12px; padding:2px 6px; }}
    pre {{ padding:16px; overflow:auto; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>AI-Translator dashboard is not in minimal mode.</h1>
    <p>The app started normally, but the built React dashboard is missing or could not be generated automatically.</p>
    <p><strong>Reason:</strong> {message}</p>
    <p>To build it manually:</p>
    <pre>cd frontend
npm install
npm run build</pre>
    <p>Then restart <code>python main.py</code>.</p>
    <p>If you intentionally want the lightweight status page, run <code>python main.py --minimal</code>.</p>
  </div>
</body>
</html>
"""


def create_app(minimal: bool = False) -> FastAPI:
    docs_url = "/docs" if settings.docs_enabled else None
    redoc_url = "/redoc" if settings.docs_enabled else None
    app = FastAPI(title=settings.app_name, version="0.1.0", docs_url=docs_url, redoc_url=redoc_url)
    app.state.minimal_mode = minimal
    frontend_ready = FRONTEND_DIST_DIR.exists()
    frontend_error: str | None = None
    if not minimal and not frontend_ready:
        frontend_ready, frontend_error = _build_frontend()
    app.state.frontend_ready = frontend_ready
    app.state.frontend_error = frontend_error

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
            "frontendBuilt": frontend_ready,
            "docsEnabled": settings.docs_enabled,
        }

    if frontend_ready and not minimal:
        assets_dir = FRONTEND_DIST_DIR / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False, response_model=None)
        async def serve_frontend(full_path: str) -> Response:
            requested_path = FRONTEND_DIST_DIR / full_path
            if full_path and requested_path.exists() and requested_path.is_file():
                return FileResponse(requested_path)
            return FileResponse(FRONTEND_DIST_DIR / "index.html")

    elif minimal:

        @app.get("/", include_in_schema=False)
        async def serve_status() -> HTMLResponse:
            with SessionLocal() as db:
                ensure_default_state(db)
                return HTMLResponse(minimal_status_html(db))

    else:

        @app.get("/", include_in_schema=False)
        async def serve_frontend_setup() -> HTMLResponse:
            return HTMLResponse(frontend_setup_html(frontend_error))

    return app
