from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_TEMPLATE_ROOT = Path("src/templates")
DEFAULT_STATIC_ROOT = Path("src/static")


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "uniquode"
    database_url: str = "sqlite://:memory:"
    project_root: Path = field(default_factory=Path.cwd)
    template_root: Path = DEFAULT_TEMPLATE_ROOT
    static_root: Path = DEFAULT_STATIC_ROOT
    static_url_path: str = "/static/"

    def __post_init__(self) -> None:
        project_root = self.project_root.resolve()
        object.__setattr__(self, "project_root", project_root)
        object.__setattr__(
            self,
            "template_root",
            self._resolve_path(self.template_root, project_root, DEFAULT_TEMPLATE_ROOT),
        )
        object.__setattr__(
            self,
            "static_root",
            self._resolve_path(self.static_root, project_root, DEFAULT_STATIC_ROOT),
        )

    @staticmethod
    def _resolve_path(path: Path, project_root: Path, default_path: Path) -> Path:
        resolved_path = path or default_path
        if not resolved_path.is_absolute():
            resolved_path = project_root / resolved_path

        return resolved_path.resolve()

    @property
    def static_mount_path(self) -> str:
        return f"/{self.static_url_path.strip('/')}"
