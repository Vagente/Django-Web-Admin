from django.apps import AppConfig
from django.core.cache import cache
from . import FILEMAN_CON_CACHE_KEY

class FileManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'file_manager'

    def ready(self):
        if cache.get(FILEMAN_CON_CACHE_KEY) is not None:
            cache.delete(FILEMAN_CON_CACHE_KEY)