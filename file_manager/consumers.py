import json

from channels.generic.websocket import WebsocketConsumer

from file_manager.file_manager import FileManager

DATA_TYPE = 0
CHANGE_PATH = 0
LIST_FILE = 1
LIST_ROOT_RILE = 2
CREATE_FILE = 3
DELETE_FILE = 4
COPY_FILE = 5
MOVE_FILE = 6
COPY_DIR = 7
MAKE_DIR = 8
DELETE_DIR = 9

EXECUTE_STATUS = 20

DATA_ARGS = 1

ALL_FUNCTIONS = [CREATE_FILE, LIST_FILE, LIST_ROOT_RILE, CREATE_FILE, DELETE_FILE, COPY_FILE, MOVE_FILE, COPY_DIR,
                 MAKE_DIR, DELETE_DIR]


class FileManagerConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        manager = FileManager()
        self.funcs = [manager.change_current_path, manager.list_files, manager.list_root_files, manager.touch,
                      manager.delete_file, manager.copy_file, manager.move, manager.copy_dir, manager.mkdir,
                      manager.delete_folder]

    def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            return
        arr: list = json.loads(text_data)
        data_type = arr[DATA_TYPE]
        data_args = arr[DATA_ARGS]

        if 0 <= data_type <= DELETE_DIR:
            res = self.funcs[data_type](*data_args)
            self.send(json.dumps([EXECUTE_STATUS, res]))
        else:
            print("Invalid data type")

    def connect(self):
        if not self.scope["user"].is_verified() or not self.scope["user"].is_superuser:
            self.close()
            return
        self.accept()

    def disconnect(self, close_code):
        pass
