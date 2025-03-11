import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shop_back.settings")

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing ORM models.
django_asgi_app = get_asgi_application()

from chat.routing import websocket_urlpatterns  # ✅ Import from routing.py


application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        ),
    }
)
