import sys

from uniquode.app import create_app
from uniquode.configuration import ConfigurationError


def load_asgi_app():
    try:
        return create_app()
    except ConfigurationError as exc:
        message = f"Application configuration failed: {exc}"
        print(message, file=sys.stderr)
        raise SystemExit(message) from None


app = load_asgi_app()
