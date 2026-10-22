import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "update_benchmarks.py"


class UpdateBenchmarksTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        for rel in ("skills", ".claude-plugin"):
            shutil.copytree(ROOT / rel, self.tmp / rel)
        self.current = self.tmp / "skills/hyrox-pacing/references/benchmarks.json"
        self.output = self.tmp / "github_output"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_update(self, payload: str):
        source = self.tmp / "downloaded.json"
        source.write_text(payload, encoding="utf-8")
        return subprocess.run(
            [sys.executable, "-I", str(SCRIPT), str(source), "--root", str(self.tmp)],
            capture_output=True, text=True, env={"GITHUB_OUTPUT": str(self.output)},
        )

    def versions(self):
        skill = (self.tmp / "skills/hyrox-pacing/SKILL.md").read_text(encoding="utf-8")
        market = json.loads((self.tmp / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        return skill.split("version: ", 1)[1].split("\n", 1)[0], market["plugins"][0]["version"]

    def test_unchanged_data_leaves_everything_alone(self):
        before = self.versions()
        result = self.run_update(self.current.read_text(encoding="utf-8"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.versions(), before)
        self.assertIn("changed=false", self.output.read_text())

    def test_new_data_is_written_verbatim_and_bumps_the_patch_version(self):
        data = json.loads(self.current.read_text(encoding="utf-8"))
        data["generatedAt"] = "2099-01-01T00:00:00Z"
        payload = json.dumps(data, indent=1) + "\n"
        major, minor, patch = self.versions()[0].split(".")
        result = self.run_update(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.current.read_text(encoding="utf-8"), payload)
        expected = f"{major}.{minor}.{int(patch) + 1}"
        self.assertEqual(self.versions(), (expected, expected))
        self.assertIn("changed=true", self.output.read_text())
        self.assertIn(f"version={expected}", self.output.read_text())

    def test_invalid_data_is_rejected_and_nothing_changes(self):
        before = self.current.read_text(encoding="utf-8")
        for payload in ("not json", json.dumps({"divisions": {}}), json.dumps({"stations": [], "divisions": {"men": {}}, "generatedAt": "x"})):
            with self.subTest(payload=payload[:30]):
                result = self.run_update(payload)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.current.read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()
