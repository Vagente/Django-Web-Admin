from django.conf import settings
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(settings.BASE_ROOT_URL + r"ws/stats/", consumers.StatsConsumer.as_asgi()),
]
