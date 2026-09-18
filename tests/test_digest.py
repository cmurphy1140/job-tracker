import datetime
import unittest

from tracker_digest.digest import render
from tracker_digest.stale import RowProblem, StaleRow

TODAY = datetime.date(2026, 9, 18)


class Render(unittest.TestCase):
    def test_header_carries_the_date(self):
        self.assertEqual(render([], [], TODAY).splitlines()[0], "Tracker digest for 2026-09-18")

    def test_empty_digest_says_so(self):
        self.assertIn("Nothing is waiting on a reply.", render([], [], TODAY))

    def test_one_line_per_stale_row(self):
        text = render([StaleRow("Northwind", "Implementation Specialist", "https://example.com/1", 29)], [], TODAY)
        self.assertIn("Northwind | Implementation Specialist | 29 days quiet | https://example.com/1", text)
        self.assertNotIn("Nothing is waiting", text)

    def test_problems_get_their_own_section(self):
        text = render([], [RowProblem(7, "Granite Data", "date_applied is not a date: 'not-a-date'")], TODAY)
        self.assertIn("Needs fixing", text)
        self.assertIn("line 7", text)
        self.assertIn("Granite Data", text)

    def test_no_problem_section_when_there_are_none(self):
        self.assertNotIn("Needs fixing", render([], [], TODAY))


if __name__ == "__main__":
    unittest.main()
