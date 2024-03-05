import json

from channels.generic.websocket import WebsocketConsumer

from file_manager import *
from file_manager.file_manager import FileManager


class FileManagerConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = None
        self.funcs = None

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
        try:
            self.manager = FileManager()
        except ValueError:
            self.accept()
            self.close(code=4000)
        self.funcs = {
            LIST_FILE: self.manager.list_files,
            CREATE_FILE: self.manager.touch,
            DELETE_FILE: self.manager.delete,
            MOVE_FILE: self.manager.move,
            COPY_FILE: self.manager.copy,
            MAKE_DIR: self.manager.mkdir,
        }
        self.accept()

    def disconnect(self, close_code):
        pass
