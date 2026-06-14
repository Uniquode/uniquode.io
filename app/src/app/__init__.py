from importlib.metadata import version

from app.app import setup_site
from app.config import module_config

__version__ = version("app")

__all__ = ("__version__", "module_config", "setup_site")
