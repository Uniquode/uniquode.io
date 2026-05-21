from __future__ import annotations

import argparse
from collections.abc import Sequence

import uvicorn

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_RELOAD = True
APP_TARGET = "uniquode.asgi:app"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="runserver",
        description="Start the local Uvicorn development server.",
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--reload",
        dest="reload",
        action="store_true",
        default=DEFAULT_RELOAD,
    )
    parser.add_argument("--no-reload", dest="reload", action="store_false")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    uvicorn.run(
        APP_TARGET,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
