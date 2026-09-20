import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tracker_digest.cli import main


class TestCli(unittest.TestCase):
    def test_cli_end_to_end_with_sample(self):
        sample_path = Path(__file__).parent.parent / "sample" / "leads.csv"
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "review-log.json"
            # Answers "y" to Northwind, "n" to Harbor Analytics
            with patch("builtins.input", side_effect=["y", "n"]):
                with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                    exit_code = main([
                        str(sample_path),
                        "--today", "2026-09-18",
                        "--log", str(log_path)
                    ])

            self.assertEqual(exit_code, 0)
            output = mock_stdout.getvalue()
            self.assertIn("Tracker digest for 2026-09-18", output)
            self.assertIn("Northwind Software", output)
            self.assertNotIn("Harbor Analytics |", output)  # Rejected
            self.assertIn("Needs fixing", output)
            self.assertIn("Granite Data", output)
            self.assertTrue(log_path.exists())


if __name__ == "__main__":
    unittest.main()
