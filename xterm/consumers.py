import sys

from channels.generic.websocket import WebsocketConsumer
import threading
import os
import pty
import select
import subprocess
import struct
import fcntl
import termios
import signal
import time
import json

MAX_READ_BYTES = 1024 * 20
MAX_CONNECTION = 1
CONNECTION_LIMIT_CODE = 4000
LOGGED_OUT_CODE = 4001
USER_AUTH_FAIL_CODE = 4002
TERMINAL_CLOSED_CODE = 4003
connections = 0


class XtermConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fd = None
        self.child_pid = None
        self.t = threading.Thread(target=self.read_and_forward_pty_output, args=(), daemon=True)
        self.stop_event = threading.Event()
        self.pid = os.getpid()

    def set_winsize(self, row, col, xpix=0, ypix=0):
        winsize = struct.pack("HHHH", row, col, xpix, ypix)
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)

    def read_and_forward_pty_output(self):
        print("process started")
        epoll = select.epoll()
        epoll.register(self.fd, select.EPOLLIN)
        while True:
            time.sleep(0.01)
            pid, status = os.waitpid(self.child_pid, os.WNOHANG)
            if pid == self.child_pid:
                self.close(TERMINAL_CLOSED_CODE)
                break
            event = epoll.poll(timeout=5)
            if event:
                output = os.read(self.fd, MAX_READ_BYTES).decode()
                if self.stop_event.is_set():
                    break
                self.send(json.dumps({'type': 'pty_output', 'output': output}))
        print("thread exited")
        return

    def connect(self):
        if not self.scope["user"].is_verified() or not self.scope["user"].is_superuser:
            self.close()
            return
        global connections
        lock = threading.Lock()
        with lock:
            if connections > MAX_CONNECTION:
                raise ValueError
            if connections == MAX_CONNECTION:
                self.accept()
                self.close(code=CONNECTION_LIMIT_CODE)
                return
        (self.child_pid, self.fd) = pty.fork()
        if self.child_pid == 0:
            subprocess.run("bash")
            os._exit(0)
        print(f"parent: {os.getpid()}")
        print(f"child: {self.child_pid}")
        os.write(self.fd, b"cd\rclear\r")
        self.t.start()
        with lock:
            connections += 1
        self.accept()

    def disconnect(self, close_code):
        print(f"close code {close_code}")
        if close_code == CONNECTION_LIMIT_CODE:
            print("connection limit reached")
            return
        elif close_code == 1006:
            print("User auth failed(Connection rejected)")
            return
        if close_code != TERMINAL_CLOSED_CODE:
            self.stop_event.set()
            os.kill(self.child_pid, signal.SIGKILL)
            os.wait()
            self.t.join()
        lock = threading.Lock()
        global connections
        with lock:
            connections -= 1
            if connections < 0:
                raise ValueError
        print('disconnected')

    def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            print("no text_data")
            return
        try:
            data = json.loads(text_data)
        except Exception as e:
            print(e)
            return
        if data["type"] == "pty_input":
            os.write(self.fd, data["content"].encode())
        elif data["type"] == "resize":
            self.set_winsize(data["rows"], data["cols"])
        else:
            raise TypeError(json.dumps(data))
