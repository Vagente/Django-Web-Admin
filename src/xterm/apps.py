from django.apps import AppConfig
from django.core.cache import cache
from .constants import XTERM_CON_CACHE_KEY

class XtermConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'xterm'

    def ready(self):
        if cache.get(XTERM_CON_CACHE_KEY) is not None:
            cache.delete(XTERM_CON_CACHE_KEY)