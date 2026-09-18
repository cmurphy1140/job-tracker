"""Command line entry point:  python -m tracker_digest.cli sample/leads.csv"""
import argparse
import csv
import datetime
import sys

from .digest import render
from .review import review
from .stale import find_stale


def main(argv=None):
    parser = argparse.ArgumentParser(description="Draft a digest of applications that have gone quiet.")
    parser.add_argument("csv_path")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--today", type=datetime.date.fromisoformat, default=datetime.date.today())
    parser.add_argument("--log", default="review-log.json")
    args = parser.parse_args(argv)

    with open(args.csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    stale, problems = find_stale(rows, args.today, args.days)

    def ask(item):
        return input(f"Include {item.company} ({item.days_quiet} days quiet)? [y/N] ").strip().lower() == "y"

    approved = review(stale, ask, args.log)
    print(render(approved, problems, args.today))
    return 0


if __name__ == "__main__":
    sys.exit(main())
