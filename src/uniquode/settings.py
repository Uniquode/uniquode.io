from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "uniquode"
    database_url: str = "sqlite://:memory:"
