from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

import click
import pytest
import wybra.tools.validate as validate_module
from click.testing import CliRunner
from fastapi.routing import APIRoute, APIRouter
from wybra.config import AppConfigSource, ConfigService
from wybra.core.composition import (
    AppConfig,
    AssetOptions,
    RouteOptions,
    TemplateOptions,
)
from wybra.core.routes.validation import validate_routes
from wybra.template.validation import _contains_post_form
from wybra.tools.settings import ProjectSettings
from wybra.tools.validate import main as validate_main
from wybra.tools.validation.core import ValidationResult
from wybra.tools.validation.registry import (
    ValidationDiscoveryError,
    discover_validation_targets,
)

from config_support import TEST_ROUTE_PREFIXES
from uniquode_io.settings import Settings
from uniquode_io.validation import validate_app


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
        assets=AssetOptions(
            url_path="/static/",
            root=Path("static"),
        ),
    )


def _project_settings(tmp_path: Path, modules: tuple[str, ...]) -> ProjectSettings:
    app_config = _app_config(tmp_path, modules)
    return ProjectSettings(
        project_root=tmp_path,
        app_config=app_config,
        config=ConfigService([AppConfigSource(app_config)]),
    )


@dataclass(frozen=True, slots=True)
class WebValidationTestSettings:
    project_root: Path
    app_config: AppConfig | None = None
    template_root: Path | None = None
    static_root: Path | None = None
    static_url_path: str = "/static/"
    template_auto_reload: bool | None = None
    template_cache_size: int = 400

    @property
    def modules(self) -> tuple[str, ...]:
        assert self.app_config is not None
        return self.app_config.modules

    @property
    def uses_filesystem_template_root(self) -> bool:
        return self.template_root is not None

    @property
    def uses_filesystem_static_root(self) -> bool:
        return self.static_root is not None


def test_validate_command_checks_route_foundation(capsys) -> None:
    exit_code = validate_main(["routes"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "routes: ok" in captured.out


def _stub_out_scopes_target(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the "scopes" built-in target with a no-op for this test.

    Scope-catalogue validation opens a live database connection (and, for
    apps that use it, a real keychain-backed secret) to detect drift between
    declared and persisted scopes. That live-infrastructure dependency is
    exercised end-to-end by the smoke test (see smoke_test.sh); these tests
    are only concerned with the validate CLI's own plumbing (default target
    selection, verbose output, module-discovered targets), so scopes is
    stubbed out here to keep them fast and hermetic.
    """
    monkeypatch.setitem(
        validate_module.BUILTIN_VALIDATION_TARGETS,
        "scopes",
        lambda settings: ValidationResult(name="scopes", errors=()),
    )


def test_validate_command_default_runs_registered_targets(
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_out_scopes_target(monkeypatch)

    exit_code = validate_main([])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "routes: ok" in captured.out


def test_validate_command_help_returns_cleanly(capsys) -> None:
    exit_code = validate_main(["--help"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run project validation checks" in captured.out
    assert captured.err == ""


def test_validate_command_verbose_lists_registered_checks(
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_out_scopes_target(monkeypatch)

    exit_code = validate_main(["--verbose"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "routes: ok" in captured.out
    assert "ok: template context providers validate" in captured.out
    assert "ok: configured route modules compose:" in captured.out
    assert "ok: template exists: public/pages/home.html" in captured.out
    assert "ok: template loads: public/pages/home.html" in captured.out


def test_validate_command_verbose_checks_are_scoped_to_project_templates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    project_config = project_root / "app.toml"
    project_config.write_text(
        """
        [app]
        modules = ["uniquode_io"]

        [app.templates]
        auto_reload = true
        cache_size = 0

        [app.assets]
        url_path = "/static/"
        root = "static"
        """,
        encoding="utf-8",
    )

    project_settings = _app_config(
        project_root,
        modules=("uniquode_io",),
    )
    monkeypatch.setenv("APP_CONFIG", str(project_config))
    monkeypatch.setattr(
        validate_module,
        "_build_settings",
        lambda _overrides: ProjectSettings(
            project_root=project_root,
            app_config=project_settings,
            config=ConfigService([AppConfigSource(project_settings)]),
        ),
    )

    exit_code = validate_main(["template", "--verbose"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "template: ok" in captured.out
    assert "ok: template exists: public/pages/home.html" in captured.out
    assert "ok: template exists: components/head_icons.html" in captured.out
    assert "identity/pages/login.html" not in captured.out


def test_validate_command_does_not_mask_unrelated_value_errors(monkeypatch) -> None:
    def raise_unrelated_value_error(_args: object) -> Settings:
        raise ValueError("programmer error")

    monkeypatch.setattr(validate_module, "_build_settings", raise_unrelated_value_error)

    with pytest.raises(ValueError, match="programmer error"):
        validate_module.main(["routes"])


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
        ("uniquode_io", "first_validation_module", "second_validation_module")
    )

    assert tuple(targets) == ("uniquode_io", "first", "second")
    assert isinstance(targets["uniquode_io"](Settings()), ValidationResult)
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
        lambda _overrides: _project_settings(tmp_path, ("command_validation_module",)),
    )
    _stub_out_scopes_target(monkeypatch)

    exit_code = validate_main([])

    captured = capsys.readouterr()
    assert exit_code == 0
    output_lines = set(captured.out.splitlines())
    assert {"assets: ok", "template: ok", "command-target: ok"} <= output_lines
    assert captured.err == ""


def test_validate_app_checks_home_health_template_and_static_assets() -> None:
    result = validate_app(Settings())

    assert result.is_ok
    assert result.name == "uniquode_io"
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
        "uniquode_io.validation._app_routes",
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
        "uniquode_io.validation._app_routes",
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
        lambda _overrides: _project_settings(
            tmp_path,
            ("command_malformed_validation_module",),
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
    exit_code = validate_main(["assets", "--static-url-path", "static"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "assets: ok" in captured.out


def test_validate_command_rejects_blank_static_url_path(capsys) -> None:
    exit_code = validate_main(["assets", "--static-url-path", "   "])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "static_url_path must not be blank." in captured.err


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


def test_validate_routes_reports_missing_configured_module(tmp_path) -> None:
    settings = WebValidationTestSettings(
        project_root=tmp_path,
        app_config=AppConfig(
            config_path=tmp_path / "app.toml",
            project_root=tmp_path,
            modules=("missing_validation_app",),
            routes=RouteOptions(prefixes={}),
            templates=TemplateOptions(auto_reload=True, cache_size=0),
            assets=AssetOptions(
                url_path="/static/",
                root=Path("static"),
            ),
        ),
    )

    result = validate_routes(settings)

    assert not result.is_ok
    assert result.errors == (
        "Configured route module validation failed: Configured module "
        "'missing_validation_app' could not be imported.",
    )


def test_validate_command_reports_missing_templates(tmp_path, capsys) -> None:
    template_root = tmp_path / "templates"
    static_root = tmp_path / "static"
    static_root.mkdir()

    exit_code = validate_main(
        [
            "template",
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
            "template",
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
