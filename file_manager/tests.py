from django.conf import settings
from django.test import TestCase
from file_manager.file_manager import FileManager
from pathlib import Path


class FileManagerTestCase(TestCase):
    def setUp(self):
        manager = FileManager()
        root = Path('/home/test')

    
