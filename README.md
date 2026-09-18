# tracker-digest

A small command-line tool that reads a job-application tracker (CSV), finds applications that have gone quiet, and drafts a weekly digest. Nothing leaves the program until a person approves it, and every approval is logged.

Status: **in development.** The behaviour is specified by tests; the three core functions are not implemented yet.

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

## How it is tested

18 unit tests pin the behaviour: the seven-day boundary (exactly seven is stale, six is not), last contact resetting the clock, only `applied` rows counting, sort order, a configurable threshold, unreadable and missing dates, the digest's text contract, and the review log being appended across runs rather than overwritten.

## Milestones

1. [ ] `find_stale`, `render`, `review` pass their tests.
2. [ ] `cli` end to end on the sample file; add one integration test that drives `main()` with a fake `input`.
3. [ ] Gmail API: create a **draft** digest (never send). Credentials stay out of the repository.
4. [ ] A short debugging story in this README: one real bug, how it was found, how the fix was verified.

## What AI wrote and what I verified

Kept honest as the project moves.

| Part | Who wrote it | How it was verified |
|---|---|---|
| Project layout, function signatures and docstrings | Claude | |
| Unit tests (`tests/`) | Claude, from the rule I described | |
| `find_stale`, `render`, `review` | | |
| `cli.py` | Claude (thin wrapper) | |
| This README | Claude draft | |
