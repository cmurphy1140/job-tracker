# job-tracker

Python package behind the `tracker-digest` command: reads a job-application CSV, finds applications quiet for seven or more days, and drafts a weekly digest after a person reviews each item. Codename Linosa.

## Rules

- `src/` and `tests/` are Murph's to change. `find_stale`, `render` and `review` are his own code; do not edit them.
- Nothing is sent. Gmail support creates a draft only, and has been tested with fake clients only.
- No real applications, contacts or credentials in the repo. `sample/leads.csv` is synthetic; Gmail secrets stay in the macOS Keychain.
- Standard library only for the core tool and its tests (Python 3.10+). Gmail libraries are an optional extra.
- Every claim carries its check: Checked, Recorded or UNTESTED.
- `CLAUDE.md` is a symlink to this file.

## Where status lives

The vault note `Projects/active/job-tracker/job-tracker.md` in Archipelago. `STATE.md` points to it; nothing else records status. Dated test counts are in the README Status line.

## The check

```
scripts/check.sh
```

Runs every test under `tests/`, prints the counts and ends with `check: passed`. CI (`.github/workflows/tests.yml`) runs the same command.

Run: `tracker-digest sample/leads.csv --today 2026-09-18`.
