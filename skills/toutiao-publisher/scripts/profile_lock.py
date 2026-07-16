import json
import os
import time
import uuid
from pathlib import Path

if os.name == "nt":
    import msvcrt
else:
    import fcntl


class ProfileLockedError(RuntimeError):
    def __init__(self, lock_path, holder=None):
        self.lock_path = Path(lock_path)
        self.holder = holder or {}
        pid = self.holder.get("pid", "unknown")
        super().__init__(
            f"Shared Chrome profile is already in use by process {pid}: {self.lock_path}"
        )


def ensure_private_directory(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.chmod(0o700)
    return path


def ensure_private_file(path):
    path = Path(path)
    if path.exists():
        path.chmod(0o600)
    return path


class ProfileLock:
    """Cross-agent lock for one persistent Chrome profile."""

    def __init__(self, lock_path):
        self.lock_path = Path(lock_path)
        self.token = uuid.uuid4().hex
        self.acquired = False
        self._file = None

    def _read_holder(self):
        try:
            return json.loads(self.lock_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError):
            return {}

    def acquire(self):
        ensure_private_directory(self.lock_path.parent)
        payload = {
            "pid": os.getpid(),
            "token": self.token,
            "created_at": time.time(),
        }
        self._file = open(self.lock_path, "a+", encoding="utf-8")
        ensure_private_file(self.lock_path)
        try:
            if os.name == "nt":
                self._file.seek(0)
                if not self._file.read(1):
                    self._file.write(" ")
                    self._file.flush()
                self._file.seek(0)
                msvcrt.locking(self._file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(self._file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, OSError):
            holder = self._read_holder()
            self._file.close()
            self._file = None
            raise ProfileLockedError(self.lock_path, holder)

        self._file.seek(0)
        self._file.truncate()
        json.dump(payload, self._file)
        self._file.flush()
        os.fsync(self._file.fileno())
        self.acquired = True
        return self

    def release(self):
        if not self.acquired:
            return
        try:
            if os.name == "nt":
                self._file.seek(0)
                msvcrt.locking(self._file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(self._file.fileno(), fcntl.LOCK_UN)
        finally:
            self._file.close()
            self._file = None
            self.acquired = False

    def __enter__(self):
        return self.acquire()

    def __exit__(self, _exc_type, _exc, _traceback):
        self.release()
