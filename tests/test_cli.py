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

    def test_blank_line_does_not_shift_reported_problem_line(self):
        # Header is line 1, a blank line is line 2, the bad row is line 3.
        csv_text = (
            "date_found,company,title,status,date_applied,last_contact,url\n"
            "\n"
            "2026-08-01,Bad,Role,applied,not-a-date,,https://example.com\n"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "leads.csv"
            csv_path.write_text(csv_text)
            log_path = Path(tmpdir) / "review-log.json"
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                main([str(csv_path), "--today", "2026-09-18", "--log", str(log_path)])
            output = mock_stdout.getvalue()
            self.assertIn("line 3: Bad", output)
            self.assertNotIn("line 2: Bad", output)


if __name__ == "__main__":
    unittest.main()
