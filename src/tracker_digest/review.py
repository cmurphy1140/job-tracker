"""Human review step: nothing leaves the program until a person approves it.

Decisions are appended to a JSON log so every run can be audited afterwards.
"""


def review(items, decide, log_path):
    """Ask `decide(item) -> bool` about each item; return only the approved ones.

    Every decision (approved or rejected) is appended to the JSON list at
    `log_path` as {"item": str(item), "approved": bool}. The log file is created
    if missing and never truncated.
    """
    raise NotImplementedError("Connor: implement me; tests/test_review.py describes the behaviour")
