import base64
import datetime
import unittest
from email import message_from_bytes, policy

from tracker_digest.draft import build_message
from tracker_digest.stale import StaleRow


class TestBuildMessage(unittest.TestCase):
    def _decode(self, raw: str):
        raw_bytes = base64.urlsafe_b64decode(raw.encode("ascii"))
        return message_from_bytes(raw_bytes, policy=policy.default)

    def test_empty_approved_list(self):
        raw = build_message([], datetime.date(2026, 9, 18))
        msg = self._decode(raw)
        self.assertIn("Tracker digest for 2026-09-18", msg["Subject"])
        body = msg.get_content()
        self.assertIn("Nothing is waiting on a reply.", body)
        self.assertIn("To", msg)
        self.assertEqual(msg["To"], "")

    def test_one_item(self):
        approved = [StaleRow(company="Northwind Software", title="Backend Engineer",
                              url="https://example.com/northwind", days_quiet=10)]
        raw = build_message(approved, datetime.date(2026, 9, 18))
        msg = self._decode(raw)
        body = msg.get_content()
        self.assertIn("Northwind Software | Backend Engineer | 10 days quiet | https://example.com/northwind", body)

    def test_several_items(self):
        approved = [
            StaleRow(company="Northwind Software", title="Backend Engineer",
                      url="https://example.com/northwind", days_quiet=10),
            StaleRow(company="Granite Data", title="Data Analyst",
                      url="https://example.com/granite", days_quiet=8),
        ]
        raw = build_message(approved, datetime.date(2026, 9, 18))
        msg = self._decode(raw)
        body = msg.get_content()
        self.assertIn("Northwind Software | Backend Engineer | 10 days quiet | https://example.com/northwind", body)
        self.assertIn("Granite Data | Data Analyst | 8 days quiet | https://example.com/granite", body)


if __name__ == "__main__":
    unittest.main()
