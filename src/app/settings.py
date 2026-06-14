from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from wevra.config import BaseSettings, ConfigDef
from wevra.core.exceptions import ConfigurationError

from app.config import DEFAULT_APP_NAME, module_config

__all__ = ("ConfigurationError", "Settings")


@dataclass(frozen=True, slots=True)
class Settings(BaseSettings):
    module_config: ClassVar[ConfigDef] = module_config

    name: str = DEFAULT_APP_NAME

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ConfigurationError("[app].name must not be blank.")

    @property
    def app_name(self) -> str:
        return self.name
