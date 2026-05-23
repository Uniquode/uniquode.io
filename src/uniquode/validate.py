import argparse
from dataclasses import dataclass
from pathlib import Path

from public.routes import build_public_route_set
from uniquode.settings import Settings
from uniquode.web.renderer import TemplateRenderer
from uniquode.web.style_contract import (
    REQUIRED_STATIC_ASSETS,
    REQUIRED_THEME_SELECTORS,
    REQUIRED_THEME_TOKENS,
)


@dataclass(frozen=True, slots=True)
class ValidationResult:
    name: str
    errors: tuple[str, ...]

    @property
    def is_ok(self) -> bool:
        return not self.errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validate",
        description="Run project validation checks.",
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Validation targets to run. Defaults to all registered targets.",
    )
    parser.add_argument(
        "--template-root",
        type=Path,
        help="Override the configured template root for web validation.",
    )
    parser.add_argument(
        "--static-root",
        type=Path,
        help="Override the configured static root for web validation.",
    )
    parser.add_argument(
        "--static-url-path",
        help="Override the configured static URL prefix for web validation.",
    )
    return parser


def _resolve_targets(targets: list[str]) -> tuple[str, ...]:
    if not targets:
        return ("web",)

    invalid_targets = sorted(set(targets) - {"web"})
    if invalid_targets:
        invalid = ", ".join(invalid_targets)
        raise SystemExit(f"Unknown validation target(s): {invalid}")

    return tuple(dict.fromkeys(targets))


def validate_web(settings: Settings) -> ValidationResult:
    errors: list[str] = []

    if not settings.template_root.is_dir():
        errors.append(f"Missing template root: {settings.template_root}")

    if not settings.static_root.is_dir():
        errors.append(f"Missing static root: {settings.static_root}")

    if not settings.static_url_path.strip():
        errors.append("Static URL path must not be empty.")

    route_set = build_public_route_set()
    renderer = TemplateRenderer(settings.template_root)

    for definition in route_set.page_routes + route_set.partial_routes:
        template_name = getattr(definition.view, "template_name", None)
        if template_name is None:
            continue

        template_path = settings.template_root / template_name
        if not template_path.is_file():
            errors.append(f"Missing template: {template_path}")
            continue

        try:
            renderer.environment.get_template(template_name)
        except Exception as exc:  # pragma: no cover - defensive guard
            errors.append(f"Template load failed for {template_name}: {exc}")

    for asset in REQUIRED_STATIC_ASSETS:
        asset_path = settings.static_root / asset
        if not asset_path.is_file():
            errors.append(f"Missing static asset: {asset_path}")
            continue

        if asset != "styles/app.css":
            continue

        stylesheet_content = asset_path.read_text()
        for token in REQUIRED_THEME_TOKENS:
            if token not in stylesheet_content:
                errors.append(f"Missing theme token: {token}")

        for selector in REQUIRED_THEME_SELECTORS:
            if selector not in stylesheet_content:
                errors.append(f"Missing theme selector: {selector}")

    return ValidationResult(name="web", errors=tuple(errors))


def _build_settings(args: argparse.Namespace) -> Settings:
    defaults = Settings()
    return Settings(
        app_name=defaults.app_name,
        database_url=defaults.database_url,
        template_root=args.template_root or defaults.template_root,
        static_root=args.static_root or defaults.static_root,
        static_url_path=args.static_url_path or defaults.static_url_path,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = _build_settings(args)
    exit_code = 0

    for target in _resolve_targets(args.targets):
        if target != "web":
            continue

        result = validate_web(settings)
        if result.is_ok:
            print(f"{result.name}: ok")
            continue

        exit_code = 1
        print(f"{result.name}: failed")
        for error in result.errors:
            print(f"- {error}")

    return exit_code
