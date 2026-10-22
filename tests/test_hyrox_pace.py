import subprocess
import sys
import unittest
from pathlib import Path

PACE = Path(__file__).resolve().parents[1] / "skills/hyrox-pacing/scripts/hyrox_pace.py"


def pace(*args):
    return subprocess.run([sys.executable, "-I", str(PACE), *args], capture_output=True, text=True, check=True).stdout


def seconds(clock):
    parts = [int(p) for p in clock.split(":")]
    total = 0
    for part in parts:
        total = total * 60 + part
    return total


class HyroxPaceTests(unittest.TestCase):
    def test_plan_ends_exactly_on_the_goal_with_the_default_roxzone(self):
        lines = [line for line in pace("plan", "1:25:00").splitlines() if "cumulative" in line]
        self.assertEqual(len(lines), 16)
        self.assertEqual(seconds(lines[-1].split("cumulative")[1].strip()), 85 * 60)
        self.assertIn("transitions 45s", pace("plan", "1:25:00").splitlines()[0])

    def test_percentile_and_divisions(self):
        self.assertIn("men", pace("divisions"))
        self.assertRegex(pace("percentile", "1:25:00", "--division", "men"), r"\d")


if __name__ == "__main__":
    unittest.main()
