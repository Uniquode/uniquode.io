from html.parser import HTMLParser

from public.routes import build_public_route_set
from uniquode.routes.identity import build_identity_route_set
from uniquode.settings import Settings
from uniquode.validation.core import (
    ValidationCheck,
    ValidationResult,
    read_text_for_validation,
    record_check,
)
from uniquode.web.renderer import TemplateRenderer
from uniquode.web.style_contract import (
    REQUIRED_STATIC_ASSETS,
    REQUIRED_THEME_SELECTORS,
    REQUIRED_THEME_TOKENS,
)


class PostFormParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.contains_post_form = False

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag.lower() != "form":
            return

        for name, value in attrs:
            if name.lower() == "method" and value is not None:
                if value.strip().lower() == "post":
                    self.contains_post_form = True
                return


def validate_web(settings: Settings) -> ValidationResult:
    errors: list[str] = []
    checks: list[ValidationCheck] = []

    record_check(
        checks,
        errors,
        passed=settings.template_root.is_dir(),
        description=f"template root exists: {settings.template_root}",
        error=f"Missing template root: {settings.template_root}",
    )

    record_check(
        checks,
        errors,
        passed=settings.static_root.is_dir(),
        description=f"static root exists: {settings.static_root}",
        error=f"Missing static root: {settings.static_root}",
    )

    record_check(
        checks,
        errors,
        passed=bool(settings.static_url_path.strip()),
        description=f"static URL path is configured: {settings.static_url_path}",
        error="Static URL path must not be empty.",
    )

    route_sets = (
        build_public_route_set(),
        build_identity_route_set(settings.identity_options),
    )
    renderer = TemplateRenderer(settings.template_root)

    for route_set in route_sets:
        route_definitions = tuple(route_set.page_routes) + tuple(
            getattr(route_set, "partial_routes", ())
        )
        for definition in route_definitions:
            template_name = getattr(definition.view, "template_name", None)
            if template_name is None:
                continue

            template_path = settings.template_root / template_name
            if not record_check(
                checks,
                errors,
                passed=template_path.is_file(),
                description=(
                    f"route template exists: {definition.name} -> {template_name}"
                ),
                error=f"Missing template: {template_path}",
            ):
                continue

            template_content = read_text_for_validation(
                template_path,
                checks,
                errors,
                description=f"template reads as UTF-8: {template_name}",
            )
            if template_content is None:
                continue

            if _contains_post_form(template_content):
                record_check(
                    checks,
                    errors,
                    passed='name="{{ csrf_field_name }}"' in template_content,
                    description=f"POST form CSRF field exists: {template_name}",
                    error=(
                        f"POST form template must include CSRF field: {template_path}"
                    ),
                )

            try:
                renderer.environment.get_template(template_name)
            except Exception as exc:  # pragma: no cover - defensive guard
                record_check(
                    checks,
                    errors,
                    passed=False,
                    description=f"template loads: {template_name}",
                    error=f"Template load failed for {template_name}: {exc}",
                )
            else:
                record_check(
                    checks,
                    errors,
                    passed=True,
                    description=f"template loads: {template_name}",
                )

    for asset in REQUIRED_STATIC_ASSETS:
        asset_path = settings.static_root / asset
        if not record_check(
            checks,
            errors,
            passed=asset_path.is_file(),
            description=f"static asset exists: {asset}",
            error=f"Missing static asset: {asset_path}",
        ):
            continue

        if asset != "styles/app.css":
            continue

        stylesheet_content = read_text_for_validation(
            asset_path,
            checks,
            errors,
            description=f"static asset reads as UTF-8: {asset}",
        )
        if stylesheet_content is None:
            continue

        for token in REQUIRED_THEME_TOKENS:
            record_check(
                checks,
                errors,
                passed=token in stylesheet_content,
                description=f"theme token present: {token}",
                error=f"Missing theme token: {token}",
            )

        for selector in REQUIRED_THEME_SELECTORS:
            record_check(
                checks,
                errors,
                passed=selector in stylesheet_content,
                description=f"theme selector present: {selector}",
                error=f"Missing theme selector: {selector}",
            )

    return ValidationResult(name="web", errors=tuple(errors), checks=tuple(checks))


def _contains_post_form(template_content: str) -> bool:
    parser = PostFormParser()
    parser.feed(template_content)
    parser.close()
    return parser.contains_post_form
