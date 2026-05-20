import argparse
import pickle
import socket
import uuid
from collections import deque
from pathlib import Path
from threading import Thread
from time import sleep

QUEUE_STATE_PATH: str = str(Path(__file__).parent) + "/queue_state.txt"


class TaskQueueServer:
    def __init__(self, ip: str, port: int, path: str, timeout: int):
        self._ip: str = ip
        self._port: int = port
        self._path: str = path
        self._timeout: int = timeout
        self._queues: dict[str, deque[dict[str, bytes]]] = self._recover_queue_state()
        self._active_tasks: dict[str, deque[dict[str, bytes]]] = {}

    def add(self, queue_name: str, data: bytes) -> bytes:
        deque_value = {"id": str(uuid.uuid4()).encode(), "data": data}
        self._queues.setdefault(queue_name, deque()).append(deque_value)
        return deque_value["id"]

    def _process_task_thread(self, queue_name: str, task_id: dict[str, bytes]) -> None:
        sleep(self._timeout)
        try:
            task_to_return = next(task for task in self._active_tasks[queue_name] if task_id == task["id"])
            self._active_tasks[queue_name].remove(task_to_return)
            self._queues[queue_name].appendleft(task_to_return)
            print(f"RETURNED {self._queues=}")
        except Exception:
            print(f"TASK NOT FOUND IN { self._active_tasks=}")

    def _save_queue_state(self):
        queue_dump: bytes = pickle.dumps(self._queues)
        with open(QUEUE_STATE_PATH, "wb") as f:
            f.write(queue_dump)

    def _recover_queue_state(self):
        queue_state_file_path = Path(QUEUE_STATE_PATH)

        if queue_state_file_path.exists() and queue_state_file_path.stat().st_size != 0:
            with open(queue_state_file_path, "rb") as f:
                return pickle.loads(f.read())

        return {}

    def get(self, queue_name) -> bytes:
        queue: deque | None = self._queues.get(queue_name)

        if queue is None:
            return b"NONE"

        first_elem: dict[str, bytes] = queue.popleft()
        self._active_tasks.setdefault(queue_name, deque())
        self._active_tasks[queue_name].append(first_elem)

        task_timeout_thread = Thread(target=self._process_task_thread, args=(queue_name, first_elem["id"]))
        task_timeout_thread.start()

        return first_elem["id"] + " ".encode() + first_elem["data"] if first_elem is not None else b"NONE"

    def run(self) -> None:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self._ip, self._port))
        server_socket.listen(1)

        while True:
            try:
                current_conn, addr = server_socket.accept()
                while True:
                    data = current_conn.recv(1_000_000)
                    if not data:
                        continue

                    command = data.split()
                    method = command[0]

                    if method == b"ADD":
                        queue_name = command[1].decode()
                        response = self.add(queue_name=queue_name, data=command[2] + " ".encode() + command[3])
                        current_conn.send(response)

                    elif method == b"GET":
                        queue_name = command[1].decode()
                        response = self.get(queue_name=queue_name)
                        current_conn.send(response)
                    elif method == b"IN":
                        queue_name: str = command[1].decode()
                        task_id: bytes = command[2]

                        exists = any(item.get("id") == task_id for item in self._queues.get(queue_name, {})) or any(
                            item.get("id") == task_id for item in self._active_tasks.get(queue_name, {})
                        )

                        if exists:
                            current_conn.send(b"YES")
                        else:
                            current_conn.send(b"NO")

                    elif method == b"ACK":
                        queue_name: str = command[1].decode()
                        task_id: bytes = command[2]

                        tasks_queue: deque | None = self._queues.get(queue_name, None)
                        active_tasks_queue: deque | None = self._active_tasks.get(queue_name, None)

                        if not tasks_queue or not active_tasks_queue:
                            current_conn.send(b"NO")
                            continue

                        def find_task(queue: deque[dict[str, bytes]]) -> dict | None:
                            return next((task for task in queue if task_id == task["id"]), None)

                        task = find_task(active_tasks_queue)
                        target_queue = active_tasks_queue

                        if task is None:
                            task = find_task(tasks_queue)
                            target_queue = tasks_queue

                        if task is None:
                            current_conn.send(b"NO")
                            continue

                        target_queue.remove(task)
                        current_conn.send(b"YES")

                else:
                    current_conn.send(b"ERROR")
            except KeyboardInterrupt:
                self._save_queue_state()
                current_conn.send(b"OK")
                break


def parse_args():
    parser = argparse.ArgumentParser(description="This is a simple task queue server with custom protocol")
    parser.add_argument("-p", action="store", dest="port", type=int, default=5555, help="Server port")
    parser.add_argument("-i", action="store", dest="ip", type=str, default="0.0.0.0", help="Server ip adress")
    parser.add_argument("-c", action="store", dest="path", type=str, default="./", help="Server checkpoints dir")
    parser.add_argument(
        "-t", action="store", dest="timeout", type=int, default=60, help="Task maximum GET timeout in seconds"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    server = TaskQueueServer(**args.__dict__)
    server.run()
