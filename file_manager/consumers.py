import json

from channels.generic.websocket import WebsocketConsumer

from file_manager.file_manager import FileManager
from file_manager import *


class FileManagerConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        manager = FileManager()
        self.funcs = [manager.list_files, manager.list_root_files, manager.touch,
                      manager.delete_file, manager.copy_file, manager.move, manager.copy_dir, manager.mkdir,
                      manager.delete_folder]

    def receive(self, text_data=None, bytes_data=None):
        try:
            if text_data is None:
                return
            arr: list = json.loads(text_data)
            data_type = arr[DATA_TYPE]
            data_args = arr[DATA_ARGS]

            if 0 <= data_type <= DELETE_DIR:
                res = self.funcs[data_type](*data_args)
                self.send(json.dumps([data_type, res]))
            else:
                print("Invalid data type")
        except json.decoder.JSONDecodeError:
            raise ValueError

    def connect(self):
        if not self.scope["user"].is_verified() or not self.scope["user"].is_superuser:
            self.close()
            return
        self.accept()

    def disconnect(self, close_code):
        pass
