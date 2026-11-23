import csv
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DioTransformTest(unittest.TestCase):
    def test_comma_and_semicolon_exports(self):
        content = '<sco>\n<sec><par><lno>ABC</lno></par></sec>\n</sco>\n<translation>One, two; three</translation>'

        for delimiter in (",", ";"):
            with self.subTest(delimiter=delimiter), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                parsers = root / "parsers"
                parsers.mkdir()
                shutil.copy(ROOT / "parsers" / "__init__.py", parsers)
                shutil.copytree(
                    ROOT / "parsers" / "dio",
                    parsers / "dio",
                    ignore=shutil.ignore_patterns("tests", "__pycache__"),
                )
                (parsers / "dio" / "tests").mkdir()
                input_dir = root / "data" / "input"
                input_dir.mkdir(parents=True)
                with (input_dir / "dio_public_raw.csv").open("w", encoding="utf-8", newline="") as file:
                    writer = csv.writer(file, delimiter=delimiter)
                    writer.writerow(["id", "content", "type", "norm_iri"])
                    writer.writerow([41, content, "dio-inscriptions-raw", "dio~test"])

                env = os.environ.copy()
                env["PYTHONPATH"] = str(root)
                result = subprocess.run(
                    [sys.executable, str(parsers / "dio" / "transform.py")],
                    cwd=root,
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                with (root / "data" / "output" / "dio_public_raw.csv").open(
                    encoding="utf-8", newline=""
                ) as file:
                    rows = list(csv.DictReader(file, delimiter=";"))
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["id"], "41")
                self.assertEqual(rows[0]["content"], content)


if __name__ == "__main__":
    unittest.main()
