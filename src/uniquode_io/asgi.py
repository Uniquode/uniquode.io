from wybra.core.asgi import load_asgi_app

from uniquode_io.app import create_app

app = load_asgi_app(create_app)
