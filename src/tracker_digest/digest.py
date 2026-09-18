"""Turn stale rows into a plain-text digest a person can read in a minute."""


def render(stale, problems, today) -> str:
    """Return the digest as text.

    Contract (see tests/test_digest.py):
      - first line: "Tracker digest for <YYYY-MM-DD>"
      - one line per stale row: "<company> | <title> | <N> days quiet | <url>"
      - if there are none: the line "Nothing is waiting on a reply."
      - if there are problems: a "Needs fixing" section listing line number and reason
    """
    raise NotImplementedError("Connor: implement me; tests/test_digest.py describes the behaviour")
