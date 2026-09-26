# tracker-digest

A small command-line tool that reads a job-application tracker (CSV), finds applications that have gone quiet, and drafts a weekly digest. Nothing leaves the program until a person approves it, and every approval is logged.

Status: **core functions implemented and tested.** `find_stale`, `render`, `review`, and the `cli` all pass their tests (32/32, including Gmail draft creation and the one-time sign-in).

## The problem

A job search produces dozens of open applications. The ones that matter most on any given Monday are the ones that have heard nothing for a week, and those are exactly the ones that are easy to lose in a spreadsheet.

## Decisions

- **The rule lives in one function.** `find_stale` decides what "gone quiet" means (status, which date starts the clock, the threshold). Everything else is formatting.
- **Bad data is reported, not dropped.** A row with an unreadable date shows up under "Needs fixing" with its line number.
- **A human review step sits before output.** `review` asks about each item and appends every decision to `review-log.json`, so a run can be audited afterwards.
- **No dependencies.** Standard library only, tests included (`unittest`), so it runs anywhere Python 3.10+ does.

## One tradeoff

The review step makes the tool slower to use than a fully automatic digest. That is on purpose: the next milestone creates email drafts, and a wrong automatic message to an employer costs more than thirty seconds of review.

## Run it

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

```bash
PYTHONPATH=src python3 -m tracker_digest.cli sample/leads.csv --today 2026-09-18
```

`sample/leads.csv` is synthetic. No real applications or contacts are in this repository.

## Gmail drafts

Turns the approved digest into a real Gmail **draft** (never sends anything). Needs the three Google libraries in `requirements-gmail.txt` (`pip install -r requirements-gmail.txt`) — the core tool and its tests need none of them.

**One-time setup in Google Cloud Console** (a personal project, not a shared one): create a project, enable the Gmail API, configure the OAuth consent screen (External, Testing, with your own account added as a test user), then create a **Desktop app** OAuth client and download its client secret JSON. Full steps and citations: [docs/milestone-3-design.md](docs/milestone-3-design.md#step-3-setup-researched).

**Sign in once:**

```bash
python3 -m tracker_digest.cli auth --client-secret ~/Downloads/client_secret.json
```

Opens a browser to Google's consent screen, then stores the client secret and the resulting refresh token in the macOS Keychain (`tracker-digest-gmail`, `tracker-digest-gmail-token`) — never in a file in this repository.

**Create a draft from the approved items:**

```bash
python3 -m tracker_digest.cli draft sample/leads.csv --today 2026-09-18
```

Runs the same review step as before, then creates one Gmail draft from whatever was approved and prints its draft id.

**Re-consent every ~7 days.** In Google's Testing publishing status, a refresh token expires seven days after the last consent. When `draft` reports that the sign-in has expired, rerun `auth` with the same client secret file — no need to repeat the Cloud Console setup.

## How it is tested

20 tests pin the behaviour (`PYTHONPATH=src python3 -m unittest discover -s tests -v`, run 2026-09-26: 20 passed, 0 failed): the seven-day boundary (exactly seven is stale, six is not), last contact resetting the clock, only `applied` rows counting, sort order, a configurable threshold, unreadable and missing dates, the digest's text contract, the review log being appended across runs rather than overwritten, one integration test driving `cli.main()` end to end against the sample file, and one pinning the right line number when the CSV has blank lines (see the debugging story below).

## Milestones

1. [x] `find_stale`, `render`, `review` pass their tests.
2. [x] `cli` end to end on the sample file; add one integration test that drives `main()` with a fake `input`.
3. [x] Gmail API: create a **draft** digest (never send). Credentials stay out of the repository. Design: [docs/milestone-3-design.md](docs/milestone-3-design.md). All 3 steps done: `draft.build_message`, `gmail.create_draft` / Keychain helpers, and the `auth` / `draft` CLI commands (see "Gmail drafts" below).
4. [x] A short debugging story in this README: one real bug, how it was found, how the fix was verified.

## Debugging story: the wrong line number

**The bug.** A tracker row with an unreadable date is meant to show up under "Needs fixing" with its line number, so you can go straight to it. With a blank line anywhere above that row, the report pointed one line too high: a bad date on line 3 came out as `line 2: Bad`. Anyone fixing their tracker would edit the wrong row.

**How it was found.** Not by a user. The git history went straight from stubs to passing tests, so there was no bug to write up. On 2026-09-26 Claude ran an edge-case pass on purpose: blank and whitespace-only lines, a UTF-8 BOM, odd spacing and case in the status, dates right at the seven-day threshold, empty files, a missing or broken `review-log.json`. The blank line was the one case that gave a wrong answer.

**The cause.** `find_stale` worked out the line number as `row index + 2` (one for the header, one because rows count from zero). That assumes every row sits on the next physical line. `csv.DictReader` skips blank lines without saying so, so after a blank line the count drifts.

**The fix.** `cli.py` records `reader.line_num`, the reader's own physical line count, on each row as it is read, and `find_stale` uses it (`src/tracker_digest/stale.py:37`), falling back to the old count for rows that didn't come from a file.

**How the fix was verified.** A new test (`tests/test_cli.py::test_blank_line_does_not_shift_reported_problem_line`) writes a CSV with a blank line above a bad date. On the code before the fix (`c4ef7a8`) it fails with `line 2: Bad`. With the fix (`c9b682c`) it passes, and so does the rest of the suite: 20 passed, 0 failed.

## What AI wrote and what I verified

Kept honest as the project moves.

| Part | Who wrote it | How it was verified |
|---|---|---|
| Project layout, function signatures and docstrings | Claude (commit `b4d8f17`, stubs raising `NotImplementedError`) | Read the stubs against the tests before implementing |
| Unit tests (`tests/`) | Claude, from the rule I described | Ran them red against the stubs, then green after implementing: 19/19 pass as of 2026-09-23 |
| `find_stale`, `render`, `review` | Connor (commit `c529743`, no AI co-author on that commit) | All tests in `tests/test_stale.py`, `tests/test_digest.py`, `tests/test_review.py` pass |
| `cli.py` | Claude (thin wrapper) | `tests/test_cli.py::test_cli_end_to_end_with_sample` drives `main()` against `sample/leads.csv` |
| Blank-line bug fix and its test | Claude (commit `c9b682c`), found by a deliberate edge-case pass | The new test fails on `c4ef7a8` (`line 2` instead of `line 3`) and passes after the fix; full suite 20/20 |
| This README | Claude draft, reconciled against the code and test run | "Decisions" and "One tradeoff" match my project note of 2026-09-20, written before the code; they state intent, which the commit history can't prove |
