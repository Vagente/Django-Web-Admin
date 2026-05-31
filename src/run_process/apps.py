from django.apps import AppConfig
from django.core.cache import cache
from . import RUNPROCESS_CON_CACHE_KEY

class RunProcessConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'run_process'

    def ready(self):
        if cache.get(RUNPROCESS_CON_CACHE_KEY) is not None:
            cache.delete(RUNPROCESS_CON_CACHE_KEY)