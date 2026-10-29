import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from env_snapshot.cli import main
from env_snapshot.core import SAFE_ENV, diff_snapshots, snapshot, to_markdown


class SnapshotTests(unittest.TestCase):
    def test_structure(self):
        s = snapshot(include_packages=False)
        for key in ("created", "os", "hardware", "python", "env", "git", "files"):
            self.assertIn(key, s)
        self.assertTrue(s["python"]["version"].startswith("3."))

    def test_no_secrets_recorded(self):
        os.environ["MY_SECRET_TOKEN"] = "hunter2"
        try:
            s = snapshot(include_packages=False)
            self.assertNotIn("MY_SECRET_TOKEN", s["env"])
            self.assertTrue(set(s["env"]) <= set(SAFE_ENV))
        finally:
            del os.environ["MY_SECRET_TOKEN"]

    def test_file_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "data.csv")
            with open(p, "wb") as fh:
                fh.write(b"abc")
            s = snapshot(extra_files=[p], include_packages=False)
            self.assertEqual(s["files"][p], "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_diff(self):
        a = {"os": {"system": "Linux"}, "python": {"version": "3.11.4"}, "packages": {"numpy": "1.26.0", "old": "1"},
             "git": {"commit": "aaaaaaaaaaaa"}, "files": {"d.csv": "1"}}
        b = {"os": {"system": "Linux"}, "python": {"version": "3.12.1"}, "packages": {"numpy": "2.0.0", "new": "2"},
             "git": {"commit": "bbbbbbbbbbbb"}, "files": {"d.csv": "2"}}
        d = diff_snapshots(a, b)
        self.assertIn("python.version: 3.11.4 -> 3.12.1", d)
        self.assertIn("package changed: numpy 1.26.0 -> 2.0.0", d)
        self.assertIn("package removed: old 1", d)
        self.assertIn("package added: new 2", d)
        self.assertIn("file changed: d.csv", d)
        self.assertEqual(diff_snapshots(a, a), [])

    def test_markdown_and_cli(self):
        s = snapshot(include_packages=False)
        self.assertIn("# Computational environment", to_markdown(s))
        with tempfile.TemporaryDirectory() as d:
            o1, md = os.path.join(d, "e1.json"), os.path.join(d, "env.md")
            with redirect_stdout(io.StringIO()):
                main(["capture", "-o", o1, "--markdown", md, "--no-packages"])
            with open(o1, encoding="utf-8") as fh:
                self.assertIn("python", json.load(fh))
            self.assertTrue(os.path.exists(md))
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(main(["diff", o1, o1]), 0)


if __name__ == "__main__":
    unittest.main()
