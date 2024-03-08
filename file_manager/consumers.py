import json
import threading

from channels.generic.websocket import WebsocketConsumer

from file_manager import *
from file_manager.file_manager import FileManager


class FileManagerConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = None
        self.funcs = None
        self.t = None
        self.stop_event = threading.Event()

    def send_folder_size(self, path):
        last_item = None
        for s in self.manager.get_dir_size():
            if last_item is not None:
                self.send(json.dumps([DIR_SIZE, False, s, path]))
            last_item = s
        self.send(json.dumps([DIR_SIZE, True, last_item, path]))

    def create_thread(self, path):
        if self.t is not None and self.t.is_alive():
            self.stop_event.set()
            self.t.join()
            self.stop_event.clear()
        self.t = threading.Thread(target=self.send_folder_size, args=(path,), daemon=True)
        self.t.start()

    def receive(self, text_data=None, bytes_data=None):
        try:
            if text_data is None:
                return
            arr: list = json.loads(text_data)
            data_type = arr[DATA_TYPE]
            data_args = arr[DATA_ARGS]
            if data_type == DIR_SIZE:
                self.create_thread(data_args[0])
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
