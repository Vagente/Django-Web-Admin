import fcntl
import json
import os
import pty
import pwd
import select
import sys
import struct
import termios
import threading
import time
import subprocess
from subprocess import TimeoutExpired
from pathlib import PosixPath

from channels.exceptions import StopConsumer
from django.core.cache import cache
from django.db import DataError
from channels.generic.websocket import WebsocketConsumer

from .constants import *


def valid_username(username):
    if not type(username) is str:
        return False
    for p in pwd.getpwall():
        shell = p[-1].split("/")[-1]
        if shell != "nologin" and shell != "false" and p[0] == username:
            return True
    return False


def set_winsize(fd, row, col, xpix=0, ypix=0):
    winsize = struct.pack("HHHH", row, col, xpix, ypix)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)


class XtermConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fd = None
        # self.child_pid = None
        self.t = None
        self.stop_event = threading.Event()
        self.connected = False
        # self._child_alive = False
        self.sub_process: subprocess.Popen | None = None
        cache.add(XTERM_CON_CACHE_KEY, 0, timeout=None)

    def child_process_alive(self):
        """
        returns True if the child process is alive, False otherwise or if the child process pid is None
        """
        if self.sub_process is None or self.sub_process.poll() is not None:
            return False
        return True

    def read_and_forward_pty_output(self):
        if settings.DEBUG:
            print("Started terminal forward")
        epoll = select.epoll()
        epoll.register(self.fd, select.EPOLLIN)
        while True:
            time.sleep(0.05)
            if not self.child_process_alive():
                print(self.sub_process)
                self.send(json.dumps({JSON_TYPE: TYPE_EXITED}))
                os.close(self.fd)
                print(f"subprocess {self.sub_process.pid} exited")
                break
            if self.stop_event.is_set():
                break
            event = epoll.poll(timeout=1)
            if event and event[0][1] == select.EPOLLIN:
                output = os.read(self.fd, XTERM_MAX_READ_BYTES).decode()
                self.send(json.dumps({JSON_TYPE: TYPE_PTY_OUTPUT, JSON_CONTENT: output}))
        if settings.DEBUG:
            print("Ended terminal forward")

    def create_child_process(self, username: str):
        if not valid_username(username):
            self.send(json.dumps({JSON_TYPE: TYPE_ERROR, JSON_CONTENT: "Invalid username"}))
            return False
        if self.sub_process is not None and self.sub_process.poll() is None:
            self.sub_process.terminate()
            try:
                self.sub_process.wait(3)
            except TimeoutExpired:
                self.sub_process.kill()
        self.fd, slave = pty.openpty()
        python_exe = sys.executable
        setup_path = PosixPath(__file__).parent / 'shell_setup.py'
        if not setup_path.exists():
            return False
        self.sub_process = subprocess.Popen([python_exe, setup_path,
                                             "--username", username, "--slave_fd", str(slave)], stdin=slave,
                                            stdout=slave, stderr=slave, pass_fds=(slave,), start_new_session=True)
        os.close(slave)
        if settings.DEBUG:
            print(f"Subprocess {self.sub_process.pid} created")
        return True

    def create_thread(self):
        if self.t is not None and self.t.is_alive():
            self.stop_event.set()
            self.t.join()
            self.stop_event.clear()
        self.t = threading.Thread(target=self.read_and_forward_pty_output, args=(), daemon=True)
        self.t.start()

    def connect(self):
        if not self.scope["user"].is_verified or not self.scope["user"].is_superuser:
            self.close()
            raise StopConsumer
        with cache.lock(REDIS_LOCK_PREFIX + XTERM_CON_CACHE_KEY):
            num = cache.get(XTERM_CON_CACHE_KEY)
            if num > XTERM_MAX_CON:
                self.close()
                raise DataError(f"xterm connections {num} exceeds max connection")
            elif num == XTERM_MAX_CON:
                self.accept()
                self.close(code=XTERM_CONNECTION_LIMIT_CODE)
                raise StopConsumer
            else:
                cache.incr(XTERM_CON_CACHE_KEY, delta=1)
        self.connected = True
        self.accept()

    def disconnect(self, close_code):
        if settings.DEBUG:
            print(f"close code {close_code}")
        if self.t is not None and self.t.is_alive():
            self.stop_event.set()
            self.t.join()
        if self.child_process_alive():
            self.sub_process.terminate()
        try:
            self.sub_process.wait(3)
        except TimeoutExpired:
            self.sub_process.kill()
            print(f"Child process {self.sub_process.pid} exited by SIGKILL")
        else:
            print(f"Child process {self.sub_process.pid} exited by SIGTERM")
        if not self.connected:
            print(self.connected)
            raise StopConsumer
        with cache.lock(REDIS_LOCK_PREFIX + XTERM_CON_CACHE_KEY):
            cache.decr(XTERM_CON_CACHE_KEY, delta=1)
            if cache.get(XTERM_CON_CACHE_KEY) == 0:
                cache.delete(XTERM_CON_CACHE_KEY)
        try:
            os.close(self.fd)
        except OSError as e:
            if e.errno != 9:
                raise OSError(e)
        raise StopConsumer

    def receive(self, text_data=None, bytes_data=None):
        try:
            if text_data is None:
                return
            data: dict = json.loads(text_data)
            if type(data) is not dict:
                return
            data_type = data[JSON_TYPE]

            if data_type == TYPE_PTY_INPUT:
                content = data[JSON_CONTENT]
                if type(content) is str:
                    os.write(self.fd, content.encode())
            elif data_type == TYPE_RESIZE:
                rows = data["rows"]
                cols = data["cols"]
                if type(rows) is int and type(cols) is int:
                    try:
                        termios.tcsetwinsize(self.fd, (rows, cols))
                        # set_winsize(self.fd, rows, cols)
                    except Exception as e:
                        print(f"another error {e}")

            elif data_type == TYPE_INIT:
                username = data[JSON_CONTENT]
                status = self.create_child_process(username)
                if status:
                    self.create_thread()
                    self.send(json.dumps({JSON_TYPE: TYPE_INIT}))
        except KeyError or json.decoder.JSONDecodeError as e:
            print(f"Error in run_process.consumers: {e}")
