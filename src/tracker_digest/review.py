"""Human review step: nothing leaves the program until a person approves it.

Decisions are appended to a JSON log so every run can be audited afterwards.
"""


import json
from pathlib import Path


def review(items, decide, log_path):
    """Ask `decide(item) -> bool` about each item; return only the approved ones.

    Every decision (approved or rejected) is appended to the JSON list at
    `log_path` as {"item": str(item), "approved": bool}. The log file is created
    if missing and never truncated.
    """
    if not items:
        return []

    log_file = Path(log_path)
    entries = []
    if log_file.exists():
        try:
            content = log_file.read_text(encoding="utf-8").strip()
            if content:
                loaded = json.loads(content)
                if isinstance(loaded, list):
                    entries = loaded
        except Exception:
            entries = []

    kept = []
    for item in items:
        approved = bool(decide(item))
        item_val = item if isinstance(item, str) else str(item)
        entries.append({"item": item_val, "approved": approved})
        if approved:
            kept.append(item)

    log_file.parent.mkdir(parents=True, exist_ok=True)
    import tempfile
    with tempfile.NamedTemporaryFile("w", dir=str(log_file.parent), delete=False) as tf:
        json.dump(entries, tf, indent=2)
        temp_name = tf.name
    Path(temp_name).replace(log_file)
    return kept
