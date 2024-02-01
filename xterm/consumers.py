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

MAX_READ_BYTES = 1024 * 20
MAX_CONNECTION = 1
CONNECTION_LIMIT_CODE = 4000
LOGGED_OUT_CODE = 4001
USER_AUTH_FAIL_CODE = 4002
TERMINAL_CLOSED_CODE = 4003
connections = 0


def valid_username(username):
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
        self.t = threading.Thread(target=self.read_and_forward_pty_output, args=(), daemon=True)
        self.stop_event = threading.Event()
        self.pid = os.getpid()
        self.terminal_started = False

    def read_and_forward_pty_output(self):
        print("process started")
        epoll = select.epoll()
        epoll.register(self.fd, select.EPOLLIN)
        while True:
            time.sleep(0.1)
            pid, status = os.waitpid(self.child_pid, os.WNOHANG)
            if pid == self.child_pid:
                print(f"child {pid} exited with status code {status}")
                self.close(TERMINAL_CLOSED_CODE)
                break
            event = epoll.poll(timeout=1)
            if self.stop_event.is_set():
                break
            if event:
                output = os.read(self.fd, MAX_READ_BYTES).decode()
                self.send(json.dumps({'type': 'pty_output', 'output': output}))
        print("thread exited")
        return

    def create_terminal(self, username):
        print(f"check username {username}")
        if not valid_username(username):
            self.send("username doesn't exist")
            return
        (self.child_pid, self.fd) = pty.fork()
        if self.child_pid == 0:
            os.execv("/bin/su", ("--login", "vagente"))
        print(f"parent: {os.getpid()}")
        print(f"child: {self.child_pid}")
        self.send(json.dumps({'type': 'init', 'username': username}))
        self.t.start()
        self.terminal_started = True

    def connect(self):
        if not self.scope["user"].is_verified() or not self.scope["user"].is_superuser:
            self.close()
            return
        global connections
        lock = threading.Lock()
        with lock:
            if connections > MAX_CONNECTION:
                raise Exception
            if connections == MAX_CONNECTION:
                self.accept()
                self.close(code=CONNECTION_LIMIT_CODE)
                return
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
        if close_code != TERMINAL_CLOSED_CODE and self.terminal_started:
            self.stop_event.set()
            self.t.join()
            os.kill(self.child_pid, signal.SIGKILL)
            os.wait()
        lock = threading.Lock()
        global connections
        with lock:
            connections -= 1
            if connections < 0:
                raise Exception
        print('disconnected')

    def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            return
        try:
            data: dict = json.loads(text_data)
            data_type = data["type"]
        except Exception as e:
            print(e)
            return
        if data_type == "pty_input":
            try:
                content = data["content"]
            except KeyError:
                return
            if type(content) is str:
                os.write(self.fd, data["content"].encode())
        elif data_type == "resize":
            try:
                rows = data["rows"]
                cols = data["cols"]
            except KeyError:
                return
            if type(rows) is int and type(cols) is int:
                try:
                    termios.tcsetwinsize(self.fd, (data["rows"], data["cols"]))
                except Exception as e:
                    print(e)
        elif not self.terminal_started and data_type == "init":
            try:
                username = data["username"]
            except KeyError:
                return
            self.create_terminal(username)
        else:
            self.send("invalid data type/already initialized")
