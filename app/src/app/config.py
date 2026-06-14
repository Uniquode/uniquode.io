from __future__ import annotations

from typing import Final

from wevra.config import ConfigDef, ConfigField, ConfigSection

DEFAULT_APP_NAME: Final = "uniquode"

module_config: Final = ConfigDef(
    {
        "app": ConfigSection(
            fields=(ConfigField(name="name", default=DEFAULT_APP_NAME),),
        )
    }
)

__all__ = ("DEFAULT_APP_NAME", "module_config")
