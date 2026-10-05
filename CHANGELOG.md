# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-04

First tagged release. Standard library only; Python 3.10 or newer.

### Added

- `tracker-digest` console command (`tracker-digest sample/leads.csv --today 2026-09-18`);
  a bare CSV path runs the `review` subcommand.
- `find_stale`: finds `applied` rows that have heard nothing for seven days (configurable
  with `--days`), counting from the last contact or, failing that, the application date.
- Bad rows (unreadable or missing dates) are reported under "Needs fixing" with their
  physical line number, blank lines included, instead of being dropped.
- `review`: asks about every stale item before anything is printed and appends each
  decision to `review-log.json` so a run can be audited afterwards.
- `render`: the plain-text weekly digest.
- `auth` and `draft` subcommands that create a Gmail **draft** (never send) from the
  approved items, with credentials kept in the macOS Keychain. Optional dependencies via
  `pip install "tracker-digest[gmail]"` (mirrors `requirements-gmail.txt`).
- Packaging (`pyproject.toml`, `__version__`), a demo transcript page
  (`docs/demo/tracker-digest-demo.html`) and this changelog.
- 33 unit tests, run in CI on Python 3.10, 3.12 and 3.14.

### Known limitations

- The Gmail draft path has only ever been exercised against fake Gmail clients in the test
  suite. It has not been run against a live Gmail account.
- Not published on PyPI; install from the Git tag (see the README).

[0.1.0]: https://github.com/cmurphy1140/tracker-digest/releases/tag/v0.1.0
