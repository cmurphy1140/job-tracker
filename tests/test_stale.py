import datetime
import unittest

from tracker_digest.stale import find_stale

TODAY = datetime.date(2026, 9, 18)


def row(company, status="applied", applied="", last="", title="Role", url="https://example.com"):
    return {"company": company, "title": title, "status": status,
            "date_applied": applied, "last_contact": last, "url": url}


class FindStale(unittest.TestCase):
    def test_applied_row_with_no_contact_counts_from_date_applied(self):
        stale, problems = find_stale([row("A", applied="2026-09-01")], TODAY)
        self.assertEqual([(s.company, s.days_quiet) for s in stale], [("A", 17)])
        self.assertEqual(problems, [])

    def test_last_contact_resets_the_clock(self):
        stale, _ = find_stale([row("A", applied="2026-08-01", last="2026-09-15")], TODAY)
        self.assertEqual(stale, [])

    def test_exactly_seven_days_is_stale(self):
        stale, _ = find_stale([row("A", applied="2026-09-11")], TODAY)
        self.assertEqual(len(stale), 1)

    def test_six_days_is_not(self):
        stale, _ = find_stale([row("A", applied="2026-09-12")], TODAY)
        self.assertEqual(stale, [])

    def test_only_applied_rows_count(self):
        rows = [row("Lead", status="lead"), row("Rejected", status="rejected", applied="2026-08-01")]
        stale, problems = find_stale(rows, TODAY)
        self.assertEqual((stale, problems), ([], []))

    def test_longest_quiet_first(self):
        rows = [row("Newer", applied="2026-09-05"), row("Older", applied="2026-08-20")]
        stale, _ = find_stale(rows, TODAY)
        self.assertEqual([s.company for s in stale], ["Older", "Newer"])

    def test_days_threshold_is_configurable(self):
        stale, _ = find_stale([row("A", applied="2026-09-08")], TODAY, days=14)
        self.assertEqual(stale, [])

    def test_unreadable_date_is_reported_not_dropped(self):
        rows = [row("Good", applied="2026-09-01"), row("Bad", applied="not-a-date")]
        stale, problems = find_stale(rows, TODAY)
        self.assertEqual([s.company for s in stale], ["Good"])
        self.assertEqual([(p.line, p.company) for p in problems], [(3, "Bad")])

    def test_applied_row_with_no_dates_is_a_problem(self):
        _, problems = find_stale([row("Blank")], TODAY)
        self.assertEqual(len(problems), 1)


if __name__ == "__main__":
    unittest.main()
