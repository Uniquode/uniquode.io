from fastapi import FastAPI
from wybra import start_site
from wybra.config import SettingsConfigSource, load_configured_settings

from uniquode_io.settings import Settings


def create_app(
    settings: Settings | None = None,
    *,
    config_source: SettingsConfigSource | None = None,
) -> FastAPI:
    if settings is not None and config_source is None:
        raise ValueError("config_source is required when explicit settings are passed.")
    app_settings = settings or load_configured_settings(
        Settings,
        config_source=config_source,
    )
    app = FastAPI(
        title=app_settings.app_name,
        lifespan=start_site(config_source=config_source),
    )
    app.state.settings = app_settings
    return app


async def setup_site(_site: object) -> None:
    """Optional app startup hook.

    Wybra calls this when the app module is listed in ``[app].modules``.
    Keep app-specific capabilities, services, or lifecycle setup here. This
    generated stub can be removed when the app has no startup work.
    """
