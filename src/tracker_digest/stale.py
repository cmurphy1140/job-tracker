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
    raise NotImplementedError("Connor: implement me; tests/test_stale.py describes the behaviour")
