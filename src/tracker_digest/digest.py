"""Turn stale rows into a plain-text digest a person can read in a minute."""


def render(stale, problems, today) -> str:
    """Return the digest as text.

    Contract (see tests/test_digest.py):
      - first line: "Tracker digest for <YYYY-MM-DD>"
      - one line per stale row: "<company> | <title> | <N> days quiet | <url>"
      - if there are none: the line "Nothing is waiting on a reply."
      - if there are problems: a "Needs fixing" section listing line number and reason
    """
    lines = [f"Tracker digest for {today}"]
    if not stale:
        lines.append("Nothing is waiting on a reply.")
    else:
        for s in stale:
            lines.append(f"{s.company} | {s.title} | {s.days_quiet} days quiet | {s.url}")

    if problems:
        lines.extend(["", "Needs fixing:"])
        for p in problems:
            lines.append(f"  line {p.line}: {p.company} - {p.reason}")

    return "\n".join(lines)
