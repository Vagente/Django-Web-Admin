from channels.generic.websocket import WebsocketConsumer
import threading
import os
import pty
import select
import termios
import signal
import time
import json
import pwd
from .constants import *

xterm_connections = 0


def valid_username(username):
    if not type(username) is str:
        return False
    for p in pwd.getpwall():
        shell = p[-1].split("/")[-1]
        if shell != "nologin" and shell != "false" and p[0] == username:
            return True
    return False


class XtermConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fd = None
        self.child_pid = None
        self.t = None
        self.stop_event = threading.Event()
        self.terminal_started = False
        self.connected = False

    def read_and_forward_pty_output(self):
        print("thread started")
        epoll = select.epoll()
        epoll.register(self.fd, select.EPOLLIN)
        while True:
            time.sleep(0.1)
            pid, status = os.waitpid(self.child_pid, os.WNOHANG)
            if pid == self.child_pid:
                print(f"child {pid} exited with status code {status}")
                self.terminal_started = False
                self.send(json.dumps({JSON_TYPE: TYPE_EXITED}))
                break
            event = epoll.poll(timeout=1)
            if self.stop_event.is_set():
                break
            if event:
                output = os.read(self.fd, XTERM_MAX_READ_BYTES).decode()
                self.send(json.dumps({JSON_TYPE: TYPE_PTY_OUTPUT, JSON_CONTENT: output}))
        print("thread exited")
        return

    def create_terminal(self, username):
        if self.t is not None:
            self.t.join()
        if not valid_username(username):
            self.send(json.dumps({JSON_TYPE: TYPE_ERROR, JSON_CONTENT: "Invalid username"}))
            return
        (self.child_pid, self.fd) = pty.fork()
        if self.child_pid == 0:
            term_env: dict = {"TERM": os.environ["TERM"]}
            os.chdir(os.path.expanduser("~" + username))
            os.execve("/bin/su", ("--login", username), term_env)
        print(f"parent: {os.getpid()}")
        print(f"child: {self.child_pid}")
        self.send(json.dumps({JSON_TYPE: TYPE_INIT, JSON_CONTENT: username}))
        self.t = threading.Thread(target=self.read_and_forward_pty_output, args=(), daemon=True)
        self.t.start()
        self.terminal_started = True

    def connect(self):
        if not self.scope["user"].is_verified() or not self.scope["user"].is_superuser:
            self.close()
            return
        global xterm_connections
        lock = threading.Lock()
        with lock:
            if xterm_connections > XTERM_MAX_CONNECTION:
                self.close()
                raise Exception
            if xterm_connections == XTERM_MAX_CONNECTION:
                self.accept()
                self.close(code=XTERM_CONNECTION_LIMIT_CODE)
                return
        with lock:
            xterm_connections += 1
        self.connected = True
        self.accept()

    def disconnect(self, close_code):
        print(f"close code {close_code}")
        if self.terminal_started:
            self.stop_event.set()
            pid, status = os.waitpid(self.child_pid, os.WNOHANG)
            if pid == self.child_pid:
                os.kill(self.child_pid, signal.SIGKILL)
                os.waitpid(self.child_pid, 0)
        if self.t is not None:
            self.t.join()
        if self.connected:
            lock = threading.Lock()
            global xterm_connections
            with lock:
                xterm_connections -= 1
                if xterm_connections < 0:
                    raise Exception
            print('disconnected')

    def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            return
        try:
            data: dict = json.loads(text_data)
            data_type = data[JSON_TYPE]
        except Exception as e:
            print(f"error {e}")
            return
        if data_type == TYPE_PTY_INPUT:
            try:
                content = data[JSON_CONTENT]
            except KeyError:
                return

            if type(content) is str:
                os.write(self.fd, content.encode())
        elif data_type == TYPE_RESIZE:
            try:
                rows = data["rows"]
                cols = data["cols"]
            except KeyError:
                return

            if type(rows) is int and type(cols) is int:
                try:
                    termios.tcsetwinsize(self.fd, (data["rows"], data["cols"]))
                except Exception as e:
                    print(f"another error {e}")

        elif not self.terminal_started and data_type == TYPE_INIT:
            try:
                username = data[JSON_CONTENT]
            except KeyError:
                return

            self.create_terminal(username)
        else:
            self.send("invalid data type/terminal already started")
