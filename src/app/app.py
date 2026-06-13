from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from wevra import start_site
from wevra.config import MappingConfigSource
from wevra.web.forms.csrf import CsrfProtector
from wevra.web.security import SecurityHeaderOptions

from app.settings import Settings, load_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or load_settings()
    app = FastAPI(
        title=app_settings.app_name,
        lifespan=start_site(config_source=_config_source(app_settings)),
    )
    app.state.settings = app_settings
    app.state.static_mount_path = app_settings.static_mount_path
    csrf_cookie_secure = app_settings.csrf_cookie_secure
    if csrf_cookie_secure is None:  # pragma: no cover - Settings normalises this
        raise RuntimeError("CSRF cookie security setting was not normalised.")
    app.state.csrf = CsrfProtector(
        app_settings.csrf_token_secret,
        cookie_secure=csrf_cookie_secure,
    )
    app.state.security_header_options = SecurityHeaderOptions(
        cross_origin_opener_policy=app_settings.cross_origin_opener_policy,
    )
    if app_settings.uses_filesystem_template_root:
        app.state.template_root = app_settings.template_root
    if app_settings.uses_filesystem_static_root:
        app.state.static_app = _static_app(app_settings)
    return app


def _config_source(settings: Settings) -> MappingConfigSource:
    values: dict[str, dict[str, Any]] = {
        "app": {
            "config_path": _config_path(settings),
            "project_root": settings.project_root,
            "modules": settings.modules,
            "database_url": settings.database_url,
        },
        "app.routes": {"prefixes": settings.route_prefixes},
        "app.templates": {
            "auto_reload": settings.template_auto_reload,
            "cache_size": settings.template_cache_size,
        },
        "app.static": {
            "url_path": settings.static_url_path,
            "export_root": settings.app_config.static.export_root
            if settings.app_config is not None
            else settings.project_root,
        },
    }
    if settings.app_config is not None and settings.app_config.auth:
        values["auth"] = dict(settings.app_config.auth)

    return MappingConfigSource(values, source="app-settings")


def _static_app(settings: Settings) -> StaticFiles:
    static_root = settings.static_root
    if static_root is None:  # pragma: no cover - Settings normalises this
        raise RuntimeError("Filesystem static root was not normalised.")
    return StaticFiles(directory=static_root, check_dir=False)


def _config_path(settings: Settings) -> Path:
    if settings.app_config is not None:
        return settings.app_config.config_path

    return settings.project_root / "app.toml"
