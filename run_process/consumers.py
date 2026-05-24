import fcntl
import json
import os
import pty
import select
import signal
import struct
import termios
import threading
import time

from channels.exceptions import StopConsumer
from channels.generic.websocket import WebsocketConsumer

from . import *

runp_connections = 0
runp_lock = threading.Lock()

class RunProcessConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fd = None
        self.child_pid = None
        self.t = None
        self.stop_event = threading.Event()
        self.connected = False
        self._child_alive = False
        self.processes = [('/bin/bash', ['-c', '/bin/journalctl -n 100 -f'])]

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
        print("thread started")
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
        print("thread exited")

    def create_child_process(self, process_idx):
        if self.child_process_alive():
            os.kill(self.child_pid, signal.SIGKILL)
            os.waitpid(self.child_pid, 0)
        (self.child_pid, self.fd) = pty.fork()
        if self.child_pid == 0:
            try:
                os.execv(self.processes[process_idx][0], ['django_run_process'] + self.processes[process_idx][1])
            except IndexError as e:
                return False
            except Exception as e:
                print(f"Error in create child process in run_process: {e}")
                self.send(json.dumps({JSON_TYPE: TYPE_ERROR, JSON_CONTENT: "Failed to create process"}))
                return False
            # os.execv('/bin/bash', ['django_run_process', '-c', '/bin/journalctl -n 100 -f'])
            # os.execv('/bin/journalctl', ['django_run_process', '-f'])
        self._child_alive = True
        print(f"child process {self.child_pid} started")
        return True

    def create_thread(self):
        if self.t is not None and self.t.is_alive():
            self.stop_event.set()
            self.t.join()
            self.stop_event.clear()
        self.t = threading.Thread(target=self.read_and_forward_pty_output, args=(), daemon=True)
        self.t.start()

    def connect(self):
        if not self.scope["user"].is_verified or not self.scope["user"].is_staff:
            self.close()
            raise StopConsumer
        global runp_connections
        global runp_lock
        with runp_lock:
            if runp_connections > XTERM_MAX_CONNECTION:
                self.close()
                print(f"runprocess_connection {runp_connections} exceeds max connection")
                raise StopConsumer
            elif runp_connections == XTERM_MAX_CONNECTION:
                self.accept()
                self.close(code=XTERM_CONNECTION_LIMIT_CODE)
                raise StopConsumer
            runp_connections += 1
        self.connected = True
        self.accept()

    def disconnect(self, close_code):
        print(f"close code {close_code}")
        if self.t is not None and self.t.is_alive():
            self.stop_event.set()
            self.t.join()
        if self.child_process_alive():
            os.kill(self.child_pid, signal.SIGKILL)
            os.waitpid(self.child_pid, 0)
            print(f"Child process {self.child_pid} exited by SIGKILL")
        if self.connected:
            global runp_connections
            global runp_lock
            with runp_lock:
                runp_connections -= 1
                if runp_connections < 0:
                    print(f"runprocess_connection {runp_connections} is less than 0")
                    raise StopConsumer
            print('disconnected')
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
                    pass
            elif data_type == TYPE_RESIZE:
                rows = data["rows"]
                cols = data["cols"]
                if type(rows) is int and type(cols) is int:
                    try:
                        termios.tcsetwinsize(self.fd, (rows, cols))
                    except Exception as e:
                        print(f"another error {e}")

            elif data_type == TYPE_INIT:
                process_num = data[JSON_CONTENT]
                status = self.create_child_process(process_num)
                if status:
                    self.create_thread()
                    self.send(json.dumps({JSON_TYPE: TYPE_INIT}))
        except KeyError or json.decoder.JSONDecodeError as e:
            print("Error in run_process.consumers: ")
            print(e)
