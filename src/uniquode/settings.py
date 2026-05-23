from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "uniquode"
    database_url: str = "sqlite://:memory:"
    template_root: Path = PROJECT_ROOT / "src/templates"
    static_root: Path = PROJECT_ROOT / "src/static"
    static_url_path: str = "/static/"

    @property
    def static_mount_path(self) -> str:
        return f"/{self.static_url_path.strip('/')}"
