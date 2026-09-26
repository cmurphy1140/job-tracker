import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tracker_digest import cli
from tracker_digest.cli import main


class FakeGmailClient:
    """Stands in for build_gmail_client()'s return value in CLI tests."""

    def __init__(self):
        self.calls = []

    def users(self):
        return self

    def drafts(self):
        return self

    def create(self, userId, body):
        self.calls.append((userId, body))
        return self

    def execute(self):
        return {"id": "draft-42"}


class TestCli(unittest.TestCase):
    def test_cli_end_to_end_with_sample(self):
        sample_path = Path(__file__).parent.parent / "sample" / "leads.csv"
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "review-log.json"
            # Answers "y" to Northwind, "n" to Harbor Analytics
            with patch("builtins.input", side_effect=["y", "n"]):
                with patch.object(cli.gmail, "build_gmail_client", return_value=FakeGmailClient()):
                    with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                        exit_code = main([
                            "draft",
                            str(sample_path),
                            "--today", "2026-09-18",
                            "--log", str(log_path),
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
            with patch.object(cli.gmail, "build_gmail_client", return_value=FakeGmailClient()):
                with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                    main([
                        "draft", str(csv_path),
                        "--today", "2026-09-18",
                        "--log", str(log_path),
                    ])
            output = mock_stdout.getvalue()
            self.assertIn("line 3: Bad", output)
            self.assertNotIn("line 2: Bad", output)

    def test_draft_creates_a_gmail_draft_from_the_approved_items(self):
        sample_path = Path(__file__).parent.parent / "sample" / "leads.csv"
        fake_client = FakeGmailClient()

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "review-log.json"
            with patch("builtins.input", side_effect=["y", "n"]):
                with patch.object(cli.gmail, "build_gmail_client", return_value=fake_client):
                    with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                        exit_code = main([
                            "draft", str(sample_path),
                            "--today", "2026-09-18",
                            "--log", str(log_path),
                        ])

            self.assertEqual(exit_code, 0)
            self.assertEqual(len(fake_client.calls), 1)
            self.assertEqual(fake_client.calls[0][0], "me")
            self.assertIn("draft-42", mock_stdout.getvalue())

    def test_draft_reports_expired_token_instead_of_crashing(self):
        sample_path = Path(__file__).parent.parent / "sample" / "leads.csv"

        def raise_invalid_grant():
            raise Exception("invalid_grant: Token has been expired or revoked.")

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "review-log.json"
            with patch("builtins.input", side_effect=["y", "n"]):
                with patch.object(cli.gmail, "build_gmail_client", side_effect=raise_invalid_grant):
                    with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                        exit_code = main([
                            "draft", str(sample_path),
                            "--today", "2026-09-18",
                            "--log", str(log_path),
                        ])

            self.assertEqual(exit_code, 1)
            self.assertIn("auth", mock_stdout.getvalue())

    def test_auth_stores_client_secret_and_refresh_token(self):
        calls = []

        def fake_authorize(client_secret_json, flow_runner=None, write_secret=None):
            calls.append(client_secret_json)

        with tempfile.TemporaryDirectory() as tmpdir:
            secret_path = Path(tmpdir) / "client_secret.json"
            secret_path.write_text('{"installed": {"client_id": "x"}}')
            with patch.object(cli.gmail, "authorize", fake_authorize):
                with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                    exit_code = main(["auth", "--client-secret", str(secret_path)])

            self.assertEqual(exit_code, 0)
            self.assertEqual(calls, ['{"installed": {"client_id": "x"}}'])
            output = mock_stdout.getvalue()
            self.assertIn("tracker-digest-gmail", output)
            self.assertNotIn("client_id", output)  # never prints the secret


if __name__ == "__main__":
    unittest.main()
