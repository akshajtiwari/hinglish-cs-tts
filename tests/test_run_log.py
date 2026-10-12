import json
import tempfile
import unittest

from switchmos import run_log


class TestRunLog(unittest.TestCase):
    def test_manifest_lifecycle(self):
        with tempfile.TemporaryDirectory() as root:
            run_dir = run_log.start_run("unit", {"lr": 1e-5, "bs": 8}, seed=3, root=root,
                                        datasets={"somos": {"version": "7378801"}}, ledger_ids=["L-0001"])
            manifest = json.loads((run_dir / "manifest.json").read_text())
            self.assertEqual(manifest["status"], "running")
            self.assertEqual(manifest["seed"], 3)
            self.assertEqual(len(manifest["config_sha256"]), 64)
            self.assertIn("commit", manifest["git"])
            self.assertIn("python", manifest["hardware"])
            run_log.finish_run(run_dir, metrics={"srcc": 0.5}, outputs=["x.pt"])
            manifest = json.loads((run_dir / "manifest.json").read_text())
            self.assertEqual(manifest["status"], "ok")
            self.assertEqual(manifest["metrics"]["srcc"], 0.5)
            self.assertGreaterEqual(manifest["wall_clock_s"], 0)

    def test_same_config_same_hash(self):
        with tempfile.TemporaryDirectory() as root:
            first = run_log.start_run("a", {"x": 1, "y": 2}, 0, root=root)
            second = run_log.start_run("b", {"y": 2, "x": 1}, 0, root=root)
            first_hash = json.loads((first / "manifest.json").read_text())["config_sha256"]
            second_hash = json.loads((second / "manifest.json").read_text())["config_sha256"]
            self.assertEqual(first_hash, second_hash)


if __name__ == "__main__":
    unittest.main()
