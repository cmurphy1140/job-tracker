"""Decide which applications have gone quiet.

The rule, in one place so the tests can pin it down:
  - only rows with status "applied" count
  - the clock starts at last_contact if present, otherwise date_applied
  - a row is stale when that date is `days` or more before `today`
  - a row whose dates cannot be parsed is reported as a problem, never silently dropped
"""
import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class StaleRow:
    company: str
    title: str
    url: str
    days_quiet: int


@dataclass(frozen=True)
class RowProblem:
    line: int          # 1-based line number in the CSV, header is line 1
    company: str
    reason: str


def find_stale(rows, today: datetime.date, days: int = 7):
    """Return (stale, problems) for an iterable of dict rows.

    `stale` is a list of StaleRow sorted by days_quiet, longest first.
    `problems` is a list of RowProblem for applied rows with unreadable dates.
    """
    stale = []
    problems = []

    for idx, r in enumerate(rows):
        line = r.get("_line", idx + 2)
        status = (r.get("status") or "").strip().lower()
        if status != "applied":
            continue

        company = r.get("company", "")
        title = r.get("title", "")
        url = r.get("url", "")
        last_contact = (r.get("last_contact") or "").strip()
        date_applied = (r.get("date_applied") or "").strip()

        date_str = last_contact if last_contact else date_applied
        field_name = "last_contact" if last_contact else "date_applied"

        if not date_str:
            problems.append(RowProblem(line, company, "no date_applied or last_contact found"))
            continue

        try:
            ref_date = datetime.date.fromisoformat(date_str)
        except Exception:
            problems.append(RowProblem(line, company, f"{field_name} is not a date: '{date_str}'"))
            continue

        days_quiet = (today - ref_date).days
        if days_quiet >= days:
            stale.append(StaleRow(company=company, title=title, url=url, days_quiet=days_quiet))

    stale.sort(key=lambda s: s.days_quiet, reverse=True)
    return stale, problems
