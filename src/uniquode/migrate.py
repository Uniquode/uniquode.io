from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

from alembic import command
from alembic.config import Config

from uniquode.configuration import ConfigurationError
from uniquode.environment import ENV_DATABASE_URL
from uniquode.runserver import runtime_project_root
from uniquode.settings import Settings, load_settings


def build_parser() -> argparse.ArgumentParser:
    database_url_parent = argparse.ArgumentParser(add_help=False)
    _add_database_url_argument(database_url_parent, default=argparse.SUPPRESS)

    parser = argparse.ArgumentParser(
        prog="migrate",
        description="Run application schema migrations through Alembic.",
    )
    _add_database_url_argument(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)

    upgrade = subparsers.add_parser(
        "upgrade",
        help="Upgrade schema revisions.",
        parents=[database_url_parent],
    )
    upgrade.add_argument("revision", nargs="?", default="head")

    downgrade = subparsers.add_parser(
        "downgrade",
        help="Downgrade schema revisions.",
        parents=[database_url_parent],
    )
    downgrade.add_argument("revision")

    subparsers.add_parser(
        "current",
        help="Show the current database revision.",
        parents=[database_url_parent],
    )
    subparsers.add_parser(
        "history",
        help="Show migration history.",
        parents=[database_url_parent],
    )
    return parser


def _add_database_url_argument(
    parser: argparse.ArgumentParser,
    *,
    default: str | None = None,
) -> None:
    parser.add_argument(
        "--database-url",
        default=default,
        help=(
            "Override the configured SQLAlchemy async database URL for this "
            "migration command."
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        settings = _build_settings(args.database_url)
    except ConfigurationError as exc:
        print("configuration: failed", file=sys.stderr)
        print(f"- {exc}", file=sys.stderr)
        return 1

    config = build_alembic_config(settings)
    match args.command:
        case "upgrade":
            command.upgrade(config, args.revision)
        case "downgrade":
            command.downgrade(config, args.revision)
        case "current":
            command.current(config)
        case "history":
            command.history(config)
        case _:  # pragma: no cover - argparse restricts choices
            raise RuntimeError(f"Unsupported migration command: {args.command}")

    return 0


def build_alembic_config(settings: Settings) -> Config:
    config = Config(str(settings.alembic_config))
    config.set_main_option("script_location", settings.migrations_root.as_posix())
    config.set_main_option("sqlalchemy.url", settings.database_url)
    return config


def _build_settings(database_url: str | None) -> Settings:
    project_root = runtime_project_root()
    if database_url is None:
        return load_settings(project_root=project_root)

    if not database_url.strip():
        raise ConfigurationError("DATABASE_URL must not be blank.")

    environment = dict(os.environ)
    environment[ENV_DATABASE_URL] = database_url
    return load_settings(environ=environment, project_root=project_root)
