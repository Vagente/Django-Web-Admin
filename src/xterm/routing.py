from django.urls import re_path
from django.conf import settings
from . import consumers

websocket_urlpatterns = [
    re_path(f"^({settings.BASE_ROOT_URL})" + r"ws/xterm/", consumers.XtermConsumer.as_asgi()),
]
