from pathlib import Path
from textwrap import dedent

import click
import pytest
import wybra.tools.validate as validate_module
from click.testing import CliRunner
from fastapi.routing import APIRoute, APIRouter
from wybra.core.composition import (
    AppConfig,
    RouteOptions,
    StaticOptions,
    TemplateOptions,
)
from wybra.tools.settings import ProjectSettings
from wybra.tools.validate import main as validate_main
from wybra.tools.validation.core import ValidationResult
from wybra.tools.validation.registry import (
    ValidationDiscoveryError,
    discover_validation_targets,
)
from wybra.web.validation import _contains_post_form, validate_web

from app.settings import Settings
from app.validation import validate_app

TEST_ROUTE_PREFIXES = {
    "app": {"default": ""},
    "wybra.web": {"partials": "", "api": ""},
    "wybra.auth": {"account": "/account", "api": ""},
}


def _write_validation_module(
    root: Path,
    module_name: str,
    validation_body: str,
) -> None:
    module_root = root / module_name
    module_root.mkdir()
    (module_root / "__init__.py").write_text("", encoding="utf-8")
    (module_root / "validation.py").write_text(
        dedent(validation_body),
        encoding="utf-8",
    )


def _app_config(tmp_path: Path, modules: tuple[str, ...]) -> AppConfig:
    return AppConfig(
        config_path=tmp_path / "app.toml",
        project_root=tmp_path,
        modules=modules,
        routes=RouteOptions(
            prefixes={
                module_name: dict(TEST_ROUTE_PREFIXES[module_name])
                for module_name in modules
                if module_name in TEST_ROUTE_PREFIXES
            }
        ),
        templates=TemplateOptions(auto_reload=True, cache_size=0),
        static=StaticOptions(
            url_path="/static/",
            root=None,
            export_root=Path("static"),
        ),
    )


def test_validate_command_checks_web_foundation(capsys) -> None:
    exit_code = validate_main(["web"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "web: ok" in captured.out


def test_validate_command_checks_persistence_foundation(capsys) -> None:
    exit_code = validate_main(["persistence"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "persistence: ok" in captured.out


def test_validate_command_default_runs_registered_targets(capsys) -> None:
    exit_code = validate_main([])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "web: ok" in captured.out
    assert "persistence: ok" in captured.out


def test_validate_command_help_returns_cleanly(capsys) -> None:
    exit_code = validate_main(["--help"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run project validation checks" in captured.out
    assert captured.err == ""


def test_validate_command_verbose_lists_registered_checks(capsys) -> None:
    exit_code = validate_main(["--verbose"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "web: ok" in captured.out
    assert "persistence: ok" in captured.out
    assert "ok: template context providers validate" in captured.out
    assert "ok: module routers compose:" in captured.out
    assert "ok: template exists: public/pages/home.html" in captured.out
    assert "ok: template exists: identity/pages/login.html" in captured.out
    assert "ok: POST form CSRF field exists: identity/pages/login.html" in (
        captured.out
    )
    assert "ok: static asset exists: styles/app.css" in captured.out
    assert "ok: theme token present: --web-core-colour-page-bg" in captured.out
    assert "ok: database URL uses supported async SQLAlchemy driver" in captured.out
    assert "ok: Alembic config exists:" in captured.out
    assert "ok: Alembic config does not force in-memory SQLite" in captured.out
    assert "ok: Alembic migration file exists: env.py" in captured.out
    assert "ok: module migration version locations exist:" in captured.out
    assert "ok: Alembic migration revision exists" in captured.out
    assert "ok: development database initialisation command is available:" in (
        captured.out
    )
    assert "uv run wybra-migrate init" in captured.out


def test_validate_command_does_not_mask_unrelated_value_errors(monkeypatch) -> None:
    def raise_unrelated_value_error(_args: object) -> Settings:
        raise ValueError("programmer error")

    monkeypatch.setattr(validate_module, "_build_settings", raise_unrelated_value_error)

    with pytest.raises(ValueError, match="programmer error"):
        validate_module.main(["web"])


def test_resolve_targets_raises_domain_error_for_unknown_targets() -> None:
    with pytest.raises(
        validate_module.UnknownValidationTargetError,
        match="Unknown validation target\\(s\\): foo",
    ):
        validate_module._resolve_targets(("foo",), ("web",))


def test_validation_targets_are_discovered_from_configured_modules(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_validation_module(
        tmp_path,
        "first_validation_module",
        """
        from wybra.tools.validation.core import ValidationResult

        def validate_first(settings):
            return ValidationResult(name="first", errors=())

        validation_targets = {"first": validate_first}
        """,
    )
    _write_validation_module(
        tmp_path,
        "second_validation_module",
        """
        from wybra.tools.validation.core import ValidationResult

        def validate_second(settings):
            return ValidationResult(name="second", errors=())

        validation_targets = {"second": validate_second}
        """,
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    targets = discover_validation_targets(
        ("app", "first_validation_module", "second_validation_module")
    )

    assert tuple(targets) == ("app", "first", "second")
    assert isinstance(targets["app"](Settings()), ValidationResult)
    assert isinstance(targets["first"](Settings()), ValidationResult)


def test_unlisted_module_validation_targets_are_not_discovered(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_validation_module(
        tmp_path,
        "listed_validation_module",
        """
        from wybra.tools.validation.core import ValidationResult

        def validate_listed(settings):
            return ValidationResult(name="listed", errors=())

        validation_targets = {"listed": validate_listed}
        """,
    )
    _write_validation_module(
        tmp_path,
        "unlisted_validation_module",
        """
        from wybra.tools.validation.core import ValidationResult

        def validate_unlisted(settings):
            return ValidationResult(name="unlisted", errors=())

        validation_targets = {"unlisted": validate_unlisted}
        """,
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    targets = discover_validation_targets(("listed_validation_module",))

    assert tuple(targets) == ("listed",)
    assert "unlisted" not in targets


def test_malformed_validation_surface_fails_clearly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_validation_module(
        tmp_path,
        "malformed_validation_module",
        """
        validation_targets = {"broken": object()}
        """,
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    with pytest.raises(ValidationDiscoveryError, match="must be callable"):
        discover_validation_targets(("malformed_validation_module",))


def test_validate_command_runs_discovered_module_targets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    _write_validation_module(
        tmp_path,
        "command_validation_module",
        """
        from wybra.tools.validation.core import ValidationResult

        def validate_command_target(settings):
            return ValidationResult(name="command-target", errors=())

        validation_targets = {"command-target": validate_command_target}
        """,
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setattr(
        validate_module,
        "_build_settings",
        lambda _overrides: ProjectSettings(
            project_root=tmp_path,
            app_config=_app_config(tmp_path, ("command_validation_module",)),
        ),
    )

    exit_code = validate_main([])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "command-target: ok\n"
    assert captured.err == ""


def test_validate_app_checks_home_health_template_and_static_assets() -> None:
    result = validate_app(Settings())

    assert result.is_ok
    assert result.name == "app"
    descriptions = {check.description for check in result.checks}
    assert "home route exists: /" in descriptions
    assert "health route exists: /health" in descriptions
    assert "home page template exists: public/pages/home.html" in descriptions
    assert "home page static asset exists: styles/home.css" in descriptions


def test_validate_app_reports_missing_home_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    router = APIRouter()

    @router.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    monkeypatch.setattr(
        "app.validation._app_routes",
        lambda: tuple(route for route in router.routes if isinstance(route, APIRoute)),
    )

    result = validate_app(Settings())

    assert not result.is_ok
    assert "Missing home route: /" in result.errors


def test_validate_app_reports_missing_health_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    router = APIRouter()

    @router.get("/", name="public:home")
    async def home() -> str:
        return "home"

    monkeypatch.setattr(
        "app.validation._app_routes",
        lambda: tuple(route for route in router.routes if isinstance(route, APIRoute)),
    )

    result = validate_app(Settings())

    assert not result.is_ok
    assert "Missing health route: /health" in result.errors


def test_validate_command_reports_malformed_validation_surface(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    _write_validation_module(
        tmp_path,
        "command_malformed_validation_module",
        """
        validation_targets = ["not", "a", "mapping"]
        """,
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setattr(
        validate_module,
        "_build_settings",
        lambda _overrides: ProjectSettings(
            project_root=tmp_path,
            app_config=_app_config(tmp_path, ("command_malformed_validation_module",)),
        ),
    )

    exit_code = validate_main([])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "validation discovery: failed" in captured.err
    assert "must expose `validation_targets` as a mapping" in captured.err


def test_validate_command_unknown_target_returns_usage_error(capsys) -> None:
    exit_code = validate_main(["foo"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "Unknown validation target(s): foo" in captured.err


def test_validate_click_command_reports_unknown_target() -> None:
    result = CliRunner().invoke(validate_module.validate_command, ["foo"])

    assert result.exit_code == 2
    assert "Unknown validation target(s): foo" in result.output


def test_validate_main_treats_falsy_click_exception_as_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class FalsyExitClickException(click.ClickException):
        exit_code = 0

    def raise_click_exception(*_args, **_kwargs) -> None:
        raise FalsyExitClickException("invalid usage")

    monkeypatch.setattr(validate_module.validate_command, "main", raise_click_exception)

    assert validate_main([]) == 1

    captured = capsys.readouterr()
    assert "invalid usage" in captured.err


def test_validate_command_accepts_normalisable_static_url_path(capsys) -> None:
    exit_code = validate_main(["web", "--static-url-path", "static"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "web: ok" in captured.out


def test_validate_command_rejects_blank_static_url_path(capsys) -> None:
    exit_code = validate_main(["web", "--static-url-path", "   "])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "static_url_path must not be blank." in captured.err


def test_validate_web_omitting_wybra_web_does_not_use_default_static_root(
    tmp_path: Path,
) -> None:
    result = validate_web(
        ProjectSettings(
            project_root=tmp_path,
            app_config=_app_config(tmp_path, ("app",)),
        )
    )

    assert not result.is_ok
    assert "Missing static asset: styles/app.css" in result.errors


def test_validate_post_form_detection_accepts_html_attribute_variants() -> None:
    assert _contains_post_form("<form METHOD='POST' action='/login'>")
    assert _contains_post_form('<form action="/login" method = "post">')
    assert _contains_post_form("<form action=/login method=post>")
    assert _contains_post_form(
        """
        <form
          action="/login"
          method = " POST "
        >
        """
    )
    assert not _contains_post_form('<form method="get" action="/login">')
    assert not _contains_post_form('<form method="postish" action="/login">')
    assert not _contains_post_form('<form data-method="post" action="/login">')
    assert not _contains_post_form('<form method="post"')


def test_validate_web_reports_missing_configured_module(tmp_path) -> None:
    settings = ProjectSettings(
        project_root=tmp_path,
        app_config=AppConfig(
            config_path=tmp_path / "app.toml",
            project_root=tmp_path,
            modules=("missing_validation_app",),
            routes=RouteOptions(prefixes={}),
            templates=TemplateOptions(auto_reload=True, cache_size=0),
            static=StaticOptions(
                url_path="/static/",
                root=None,
                export_root=Path("static"),
            ),
        ),
    )

    result = validate_web(settings)

    assert not result.is_ok
    assert result.errors == (
        "Configured module surface validation failed: Configured module "
        "'missing_validation_app' could not be imported.",
    )


def test_validate_command_rejects_unsupported_database_url(capsys) -> None:
    exit_code = validate_main(["persistence", "--database-url", "sqlite://:memory:"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Database URL must use sqlite+aiosqlite:// or postgresql+asyncpg://" in (
        captured.err
    )


def test_validate_command_rejects_empty_database_url_override(capsys) -> None:
    exit_code = validate_main(["persistence", "--database-url", ""])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Database URL must not be empty." in captured.err


def test_validate_command_verbose_lists_failed_checks(capsys) -> None:
    exit_code = validate_main(
        ["persistence", "--verbose", "--database-url", "sqlite://:memory:"]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "persistence: failed" in captured.err
    assert "ok: database URL is configured: sqlite://:memory:" in captured.err
    assert "failed: database URL uses supported async SQLAlchemy driver" in (
        captured.err
    )
    assert "Database URL must use sqlite+aiosqlite:// or postgresql+asyncpg://" in (
        captured.err
    )


def test_validate_command_redacts_database_url_password(capsys) -> None:
    exit_code = validate_main(
        [
            "persistence",
            "--verbose",
            "--database-url",
            "postgresql+asyncpg://user:password@host.example/app",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "postgresql+asyncpg://***:***@host.example/app" in captured.out
    assert "postgresql+asyncpg://user:password@host.example/app" not in captured.out
    assert "password" not in captured.out


def test_validate_command_redacts_database_url_username_without_password(
    capsys,
) -> None:
    exit_code = validate_main(
        [
            "persistence",
            "--verbose",
            "--database-url",
            "postgresql+asyncpg://alice@host.example/app",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "postgresql+asyncpg://***@host.example/app" in captured.out
    assert "postgresql+asyncpg://alice@host.example/app" not in captured.out
    assert "alice" not in captured.out


def test_validate_command_reports_missing_alembic_structure(tmp_path, capsys) -> None:
    exit_code = validate_main(
        [
            "persistence",
            "--migrations-root",
            str(tmp_path / "missing-migrations"),
            "--alembic-config",
            str(tmp_path / "missing-alembic.ini"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Missing Alembic config" in captured.err
    assert "Missing Alembic migrations root" in captured.err


def test_validate_command_reports_missing_templates(tmp_path, capsys) -> None:
    template_root = tmp_path / "templates"
    static_root = tmp_path / "static"
    static_root.mkdir()

    exit_code = validate_main(
        [
            "web",
            "--template-root",
            str(template_root),
            "--static-root",
            str(static_root),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Missing template" in captured.err


def test_validate_command_reports_template_decode_errors(tmp_path, capsys) -> None:
    template_root = tmp_path / "templates"
    static_root = tmp_path / "static"
    (template_root / "identity/pages").mkdir(parents=True)
    static_root.mkdir()
    (template_root / "identity/pages/login.html").write_bytes(b"\xff")

    exit_code = validate_main(
        [
            "web",
            "--template-root",
            str(template_root),
            "--static-root",
            str(static_root),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Unable to read" in captured.err
    assert "identity/pages/login.html" in captured.err
