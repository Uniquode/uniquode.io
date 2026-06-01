from __future__ import annotations

import os
import sys
from collections.abc import Callable, Sequence
from typing import Any

import click
from alembic import command
from alembic.config import Config
from alembic.util.exc import CommandError as AlembicError
from sqlalchemy.exc import SQLAlchemyError

from uniquode.configuration import ConfigurationError
from uniquode.environment import ENV_DATABASE_URL
from uniquode.runserver import runtime_project_root
from uniquode.settings import Settings, load_settings

DATABASE_URL_HELP = (
    "Override the configured SQLAlchemy async database URL for this migration command."
)


def _database_url_option[F: Callable[..., Any]](function: F) -> F:
    """Add the optional ``database_url: str | None`` Click option."""

    return click.option("--database-url", help=DATABASE_URL_HELP)(function)


@click.group(
    name="migrate",
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Run application schema migrations through Alembic.",
)
@_database_url_option
@click.pass_context
def migrate_command(ctx: click.Context, database_url: str | None) -> None:
    ctx.ensure_object(dict)
    ctx.obj["database_url"] = database_url


@migrate_command.command("upgrade", help="Upgrade schema revisions.")
@_database_url_option
@click.argument("revision", default="head", required=False)
@click.pass_context
def upgrade_command(ctx: click.Context, revision: str, database_url: str | None) -> int:
    return _run_migration(
        _database_url_for_command(ctx, database_url),
        lambda config: command.upgrade(config, revision),
    )


@migrate_command.command("downgrade", help="Downgrade schema revisions.")
@_database_url_option
@click.argument("revision")
@click.pass_context
def downgrade_command(
    ctx: click.Context, revision: str, database_url: str | None
) -> int:
    return _run_migration(
        _database_url_for_command(ctx, database_url),
        lambda config: command.downgrade(config, revision),
    )


@migrate_command.command("current", help="Show the current database revision.")
@_database_url_option
@click.pass_context
def current_command(ctx: click.Context, database_url: str | None) -> int:
    return _run_migration(
        _database_url_for_command(ctx, database_url),
        command.current,
    )


@migrate_command.command("history", help="Show migration history.")
@_database_url_option
@click.pass_context
def history_command(ctx: click.Context, database_url: str | None) -> int:
    return _run_migration(
        _database_url_for_command(ctx, database_url),
        command.history,
    )


def _database_url_for_command(
    ctx: click.Context, command_database_url: str | None
) -> str | None:
    if command_database_url is not None:
        return command_database_url

    if ctx.obj is None:
        return None

    if not isinstance(ctx.obj, dict):
        raise click.UsageError(
            "Invalid Click context object for migrate; expected a dictionary."
        )

    root_database_url = ctx.obj.get("database_url")
    if root_database_url is None:
        return None
    if not isinstance(root_database_url, str):
        raise click.UsageError(
            "Invalid root database_url type "
            f"{type(root_database_url)!r}; expected a string."
        )
    return root_database_url


def _run_migration(
    database_url: str | None,
    operation: Callable[[Config], None],
) -> int:
    try:
        settings = _build_settings(database_url)
    except ConfigurationError as exc:
        print("configuration: failed", file=sys.stderr)
        print(f"- {exc}", file=sys.stderr)
        return 1

    config = build_alembic_config(settings)
    try:
        operation(config)
    except (AlembicError, SQLAlchemyError) as exc:
        print("migration: failed", file=sys.stderr)
        print(f"- {exc}", file=sys.stderr)
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    try:
        result = migrate_command.main(
            args=None if argv is None else list(argv),
            prog_name="migrate",
            standalone_mode=False,
        )
    except click.exceptions.Exit as exc:
        return int(exc.exit_code or 0)
    except click.ClickException as exc:
        exc.show()
        return int(exc.exit_code or 1)
    return int(result or 0)


def build_alembic_config(settings: Settings) -> Config:
    config = Config(str(settings.alembic_config))
    config.set_main_option("script_location", settings.migrations_root.as_posix())
    config.set_main_option(
        "sqlalchemy.url", _alembic_config_value(settings.database_url)
    )
    return config


def _alembic_config_value(value: str) -> str:
    return value.replace("%", "%%")


def _build_settings(database_url: str | None) -> Settings:
    project_root = runtime_project_root()
    if database_url is None:
        return load_settings(project_root=project_root)

    if not database_url.strip():
        raise ConfigurationError("DATABASE_URL must not be blank.")

    environment = dict(os.environ)
    environment[ENV_DATABASE_URL] = database_url
    return load_settings(environ=environment, project_root=project_root)
