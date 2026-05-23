from django.urls import re_path

from django.conf import settings
from . import consumers

websocket_urlpatterns = [
    re_path(f"^({settings.BASE_ROOT_URL}|run_process/)" + r"ws/run_process/", consumers.RunProcessConsumer.as_asgi()),
]
