from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import uvicorn

from uniquode.environment import ENV_APP_RELOAD, load_environment

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_RELOAD = False
APP_TARGET = "uniquode.asgi:app"
RELOAD_ENV_VAR = ENV_APP_RELOAD


def runtime_project_root() -> Path:
    source_project_root = Path(__file__).resolve().parents[2]
    if (source_project_root / "pyproject.toml").is_file():
        return source_project_root

    return Path.cwd()


def env_requests_reload(value: str | None) -> bool:
    if value is None:
        return DEFAULT_RELOAD

    return value.strip().lower() in {"1", "true", "on"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="runserver",
        description="Start the local Uvicorn development server.",
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--reload", dest="reload", action="store_true", default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    env = load_environment(project_root=runtime_project_root())
    reload_env_value = env.get(RELOAD_ENV_VAR, None) or None
    reload_enabled = (
        args.reload
        if args.reload is not None
        else env_requests_reload(reload_env_value)
    )

    uvicorn.run(
        APP_TARGET,
        host=args.host,
        port=args.port,
        reload=reload_enabled,
    )
