import json

from channels.generic.websocket import WebsocketConsumer

from file_manager.file_manager import FileManager
from file_manager import *


class FileManagerConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        manager = FileManager()
        self.funcs = {
            LIST_FILE: manager.list_files,
            CREATE_FILE: manager.touch,
            DELETE_FILE: manager.delete,
            MOVE_FILE: manager.move,
            COPY_FILE: manager.copy,
            MAKE_DIR: manager.mkdir,
        }

    def receive(self, text_data=None, bytes_data=None):
        try:
            if text_data is None:
                return
            arr: list = json.loads(text_data)
            data_type = arr[DATA_TYPE]
            data_args = arr[DATA_ARGS]

            status, res = self.funcs[data_type](*data_args)
            self.send(json.dumps([data_type, status, res]))

        except json.decoder.JSONDecodeError or KeyError:
            return

    def connect(self):
        if not self.scope["user"].is_verified or not self.scope["user"].is_superuser:
            self.close()
            return
        self.accept()

    def disconnect(self, close_code):
        pass
