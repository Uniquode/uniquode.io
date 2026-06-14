from wevra.core.asgi import load_asgi_app

from app.app import create_app

app = load_asgi_app(create_app)
