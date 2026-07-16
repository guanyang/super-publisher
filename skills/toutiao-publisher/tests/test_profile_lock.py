import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from profile_lock import ProfileLock, ProfileLockedError


class ProfileLockTest(unittest.TestCase):
    def test_only_one_agent_can_hold_the_shared_profile_lock(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            lock_path = Path(temp_dir) / "profile.lock"
            first = ProfileLock(lock_path)
            second = ProfileLock(lock_path)

            first.acquire()
            with self.assertRaises(ProfileLockedError):
                second.acquire()

            first.release()
            second.acquire()
            second.release()

    def test_unlocked_stale_metadata_is_replaced(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            lock_path = Path(temp_dir) / "profile.lock"
            lock_path.write_text(json.dumps({"pid": 99999999, "token": "stale"}))

            lock = ProfileLock(lock_path)
            lock.acquire()

            self.assertEqual(json.loads(lock_path.read_text())["pid"], os.getpid())
            lock.release()
