import fcntl
import json
import os
import pty
import pwd
import select
import signal
import struct
import termios
import threading
import time

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
        self.child_pid = None
        self.t = None
        self.stop_event = threading.Event()
        self.connected = False
        self._child_alive = False
        cache.add(XTERM_CON_CACHE_KEY, 0, timeout=None)

    def child_process_alive(self):
        """
        returns True if the child process is alive, False otherwise or if the child process pid is None
        """
        if self.child_pid is not None and self._child_alive:
            pid, status = os.waitpid(self.child_pid, os.WNOHANG)
            if pid == self.child_pid:
                print(f"Child process {self.child_pid} exited with status {status}")
                self._child_alive = False
        return self._child_alive

    def read_and_forward_pty_output(self):
        if settings.DEBUG:
            print("Started terminal forward")
        epoll = select.epoll()
        epoll.register(self.fd, select.EPOLLIN)
        while True:
            time.sleep(0.05)
            if not self.child_process_alive():
                self.send(json.dumps({JSON_TYPE: TYPE_EXITED}))
                break
            if self.stop_event.is_set():
                break
            event = epoll.poll(timeout=1)
            if event and event[0][1] == select.EPOLLIN:
                output = os.read(self.fd, XTERM_MAX_READ_BYTES).decode()
                self.send(json.dumps({JSON_TYPE: TYPE_PTY_OUTPUT, JSON_CONTENT: output}))
        if settings.DEBUG:
            print("Ended terminal forward")

    def create_child_process(self, username):
        if not valid_username(username):
            self.send(json.dumps({JSON_TYPE: TYPE_ERROR, JSON_CONTENT: "Invalid username"}))
            return False
        if self.child_process_alive():
            os.kill(self.child_pid, signal.SIGKILL)
            os.waitpid(self.child_pid, 0)
        (self.child_pid, self.fd) = pty.fork()
        if self.child_pid == 0:
            try:
                term = os.environ["TERM"] if "TERM" in os.environ else "xterm-256color"
                term_env: dict = {"TERM": term}
                os.chdir(os.path.expanduser("~" + username))
                os.execve("/bin/su", ("django_su", "--login", username), term_env)
            except Exception as e:
                print(f"Error in create child process in xterm: {e}")
                self.send(json.dumps({JSON_TYPE: TYPE_ERROR, JSON_CONTENT: "Failed to create shell process"}))
                return False
        self._child_alive = True
        if self.child_process_alive():
            print(f"child process {self.child_pid} started")
        else:
            print(f"child process {self.child_pid} exited too early")
            return False
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
        print(f"close code {close_code}")
        if self.child_process_alive():
            os.kill(self.child_pid, signal.SIGTERM)
        if self.t is not None and self.t.is_alive():
            self.stop_event.set()
            self.t.join()
        if self.child_process_alive():
            os.kill(self.child_pid, signal.SIGKILL)
            os.waitpid(self.child_pid, 0)
            print(f"Child process {self.child_pid} exited by SIGKILL")
        else:
            print(f"Child process {self.child_pid} exited by SIGTERM")
        if not self.connected:
            raise StopConsumer
        with cache.lock(REDIS_LOCK_PREFIX + XTERM_CON_CACHE_KEY):
            cache.decr(XTERM_CON_CACHE_KEY, delta=1)
            if cache.get(XTERM_CON_CACHE_KEY) == 0:
                cache.delete(XTERM_CON_CACHE_KEY)
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
