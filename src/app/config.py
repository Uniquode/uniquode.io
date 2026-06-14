from __future__ import annotations

from typing import Final

from wevra.config import ConfigDef, ConfigField, ConfigGroup

DEFAULT_APP_NAME: Final = "uniquode"

module_config: Final = ConfigDef(
    {
        "app": ConfigGroup(
            fields=(ConfigField(name="name", default=DEFAULT_APP_NAME),),
        )
    }
)

__all__ = ("DEFAULT_APP_NAME", "module_config")
