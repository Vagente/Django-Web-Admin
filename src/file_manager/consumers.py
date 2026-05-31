import json
import threading

from channels.generic.websocket import WebsocketConsumer

from file_manager import *
from file_manager.file_manager import FileManager
from channels.exceptions import StopConsumer
from django.core.cache import cache
from django.db import DataError


class FileManagerConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = None
        self.funcs = None
        self.t = None
        self.stop_event = threading.Event()
        cache.add(FILEMAN_CON_CACHE_KEY, 0, timeout=None)

    def send_folder_size(self, path):
        last_item = next(self.manager.get_dir_size(path))
        if type(last_item) == tuple:
            self.send(json.dumps([DIR_SIZE, True, last_item, path]))
            print("send folder size exited")
            return
        for data in self.manager.get_dir_size(path):
            if self.stop_event.is_set():
                print("send folder size thread ended by signal")
                return
            self.send(json.dumps([DIR_SIZE, False, last_item, path]))
            last_item = data
        self.send(json.dumps([DIR_SIZE, True, last_item, path]))
        print("send folder size threaded completed")

    def create_thread(self, arg):
        if self.t is not None and self.t.is_alive():
            self.stop_event.set()
            self.t.join()
            self.send(json.dumps([CANCEL_DIR_SIZE, True, None]))
            self.stop_event.clear()
        self.t = threading.Thread(target=self.send_folder_size, args=arg, daemon=True)
        self.t.start()
        print("file manager thread started")

    def receive(self, text_data=None, bytes_data=None):
        try:
            if text_data is None:
                return
            arr: list = json.loads(text_data)
            data_type = arr[DATA_TYPE]
            data_args = arr[DATA_ARGS]
            if data_type == DIR_SIZE:
                self.create_thread(data_args)
            elif data_type == CANCEL_DIR_SIZE:
                if self.t.is_alive() and self.t is not None:
                    self.stop_event.set()
                    self.t.join()
                    self.stop_event.clear()
            else:
                status, res = self.funcs[data_type](*data_args)
                self.send(json.dumps([data_type, status, res]))

        except json.decoder.JSONDecodeError or KeyError:
            return

    def connect(self):
        if not self.scope["user"].is_verified or not self.scope["user"].is_superuser:
            self.close()
            raise StopConsumer
        with cache.lock(REDIS_LOCK_PREFIX + FILEMAN_CON_CACHE_KEY):
            num = cache.get(FILEMAN_CON_CACHE_KEY)
            if num > FILEMAN_MAX_CON:
                self.close()
                raise DataError(f"xterm connections {num} exceeds max connection")
            elif num == FILEMAN_MAX_CON:
                self.accept()
                self.close(code=FILEMAN_CONNECTION_LIMIT_CODE)
                raise StopConsumer
            else:
                cache.incr(FILEMAN_CON_CACHE_KEY, delta=1)
        try:
            self.manager = FileManager()
        except ValueError:
            self.accept()
            self.close(code=FILEMAN_INIT_ERR_CODE)
            raise StopConsumer
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
        if self.t is not None and self.t.is_alive():
            self.stop_event.set()
            self.t.join()
            self.stop_event.clear()
        with cache.lock(REDIS_LOCK_PREFIX + FILEMAN_CON_CACHE_KEY):
            cache.decr(FILEMAN_CON_CACHE_KEY, delta=1)
            if cache.get(FILEMAN_CON_CACHE_KEY) == 0:
                cache.delete(FILEMAN_CON_CACHE_KEY)
        raise StopConsumer
