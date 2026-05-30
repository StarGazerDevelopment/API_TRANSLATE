from __future__ import annotations

import argparse

import uvicorn

from app.config import settings
from app.main import create_app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run API_Translate.")
    parser.add_argument("--minimal", action="store_true", help="Run without the React dashboard.")
    parser.add_argument("--host", default=settings.app_host, help="Bind host.")
    parser.add_argument("--port", type=int, default=settings.app_port, help="Bind port.")
    parser.add_argument("--reload", action="store_true", help="Enable auto reload.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app = create_app(minimal=args.minimal)
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
