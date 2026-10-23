import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from switchmos import files


class TestFiles(unittest.TestCase):
    def test_save_and_load_roundtrip_and_no_tmp_left(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sub" / "x.json"
            files.save_json(path, {"a": 1, "b": [1, 2]})
            self.assertEqual(files.load_json(path), {"a": 1, "b": [1, 2]})
            self.assertFalse((Path(folder) / "sub" / "x.json.tmp").exists())

    def test_load_missing_returns_default(self):
        self.assertEqual(files.load_json("/nonexistent/none.json", default=7), 7)

    def test_file_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "abc.txt"
            path.write_bytes(b"abc")
            self.assertEqual(files.file_hash(path), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
            self.assertEqual(files.file_hash(path, "md5"), "900150983cd24fb0d6963f7d28e17f72")

    def test_claim(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "claim_00001"
            self.assertTrue(files.claim(path))
            self.assertFalse(files.claim(path))             # held by this running process
            finished = subprocess.Popen(["true"])
            finished.wait()
            path.write_text(str(finished.pid))              # a claim left by a process that has ended
            self.assertTrue(files.claim(path))
            self.assertEqual(path.read_text(), str(os.getpid()))


if __name__ == "__main__":
    unittest.main()
