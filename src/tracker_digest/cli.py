"""Command line entry point:  python -m tracker_digest.cli draft sample/leads.csv

Two subcommands (milestone 3, see docs/milestone-3-design.md):
  auth   one-time OAuth sign-in; stores the client secret and refresh token
         in the Keychain.
  draft  reviews the tracker as before, then creates a Gmail draft from the
         approved items.
"""
import argparse
import csv
import datetime
import sys

from . import gmail
from .digest import render
from .draft import build_message
from .review import review
from .stale import find_stale


def _run_auth(args):
    with open(args.client_secret, encoding="utf-8") as f:
        client_secret_json = f.read()
    gmail.authorize(client_secret_json)
    print(
        f"Saved the Gmail client secret and refresh token to the Keychain "
        f"({gmail.CLIENT_SECRET_SERVICE}, {gmail.REFRESH_TOKEN_SERVICE})."
    )
    return 0


def _run_draft(args):
    with open(args.csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            r["_line"] = reader.line_num
            rows.append(r)

    stale, problems = find_stale(rows, args.today, args.days)

    def ask(item):
        return input(f"Include {item.company} ({item.days_quiet} days quiet)? [y/N] ").strip().lower() == "y"

    approved = review(stale, ask, args.log)
    print(render(approved, problems, args.today))

    if not approved:
        return 0

    try:
        client = gmail.build_gmail_client()
        raw = build_message(approved, args.today)
        result = gmail.create_draft(client, raw)
    except Exception as exc:
        if "invalid_grant" in str(exc):
            print(f"The Gmail sign-in has expired. Rerun `python3 -m tracker_digest.cli auth --client-secret <path>` to re-authorize.")
            return 1
        raise

    print(f"Created Gmail draft {result['id']}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Draft a digest of applications that have gone quiet.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    auth_parser = subparsers.add_parser("auth", help="One-time Gmail sign-in; stores secrets in the Keychain.")
    auth_parser.add_argument("--client-secret", required=True, help="Path to the OAuth client JSON downloaded from Google Cloud Console.")
    auth_parser.set_defaults(func=_run_auth)

    draft_parser = subparsers.add_parser("draft", help="Review the tracker and create a Gmail draft from the approved items.")
    draft_parser.add_argument("csv_path")
    draft_parser.add_argument("--days", type=int, default=7)
    draft_parser.add_argument("--today", type=datetime.date.fromisoformat, default=datetime.date.today())
    draft_parser.add_argument("--log", default="review-log.json")
    draft_parser.set_defaults(func=_run_draft)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
