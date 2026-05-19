from tortoise import Tortoise

from uniquode.settings import Settings

TORTOISE_MODELS = ["uniquode.models"]


def build_tortoise_config(settings: Settings) -> dict[str, object]:
    return {
        "connections": {"default": settings.database_url},
        "apps": {
            "models": {
                "models": TORTOISE_MODELS,
                "default_connection": "default",
            }
        },
    }


async def init_database(settings: Settings) -> None:
    await Tortoise.init(config=build_tortoise_config(settings))


async def close_database() -> None:
    await Tortoise.close_connections()
