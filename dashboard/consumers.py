import json
import threading
import time

import psutil
from channels.generic.websocket import WebsocketConsumer


class StatsConsumer(WebsocketConsumer):
    def __init__(self):
        super().__init__()
        self.t = None
        self.stop_event = threading.Event()

    def send_stats(self):
        # ignore the first call which always returns 0
        psutil.cpu_percent()
        time.sleep(0.1)
        while True:
            if self.stop_event.is_set():
                break
            res = [psutil.cpu_percent()]
            memory = psutil.virtual_memory()
            res.append([memory.percent, memory.total - memory.available, memory.total])
            swap = psutil.swap_memory()
            res.append([swap.percent, swap.used, swap.total])
            storage = psutil.disk_usage('/')
            res.append([storage.percent, storage.used, storage.total])
            self.send(json.dumps(res))
            time.sleep(3)

    def create_thread(self):
        if self.t is not None and self.t.is_alive():
            self.stop_event.set()
            self.t.join()
            self.stop_event.clear()
        self.t = threading.Thread(target=self.send_stats, args=(), daemon=True)
        self.t.start()

    def connect(self):
        if not self.scope['user'].is_authenticated:
            self.close()
        self.accept()
        self.create_thread()

    def disconnect(self, close_code):
        if self.t is not None and self.t.is_alive():
            self.stop_event.set()
            self.t.join()

    def receive(self, text_data=None, bytes_data=None):
        pass
