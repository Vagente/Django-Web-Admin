"""
ASGI config for djangoWeb project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

from xterm.routing import websocket_urlpatterns as x_url
from file_manager.routing import websocket_urlpatterns as f_url
from dashboard.routing import websocket_urlpatterns as d_url
from run_process.routing import websocket_urlpatterns as r_url

from dashboard.middleware import OTPAuthMiddleware


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoWeb.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(OTPAuthMiddleware(URLRouter(x_url + f_url + d_url + r_url)))
        ),
    }
)
