from importlib.metadata import PackageNotFoundError, version

from uniquode_io.app import setup_site
from uniquode_io.config import module_config

try:
    __version__ = version("uniquode-io")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ("__version__", "module_config", "setup_site")
