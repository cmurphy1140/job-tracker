"""Turn approved digest items into a Gmail-draft-ready raw message.

Step 1 of milestone 3 (see docs/milestone-3-design.md): pure, standard-library
only, no network, no credentials. `build_message` returns the base64url
"raw" string the Gmail `users.drafts.create` call expects for its
`message.raw` field. Nothing here talks to Gmail.
"""
import base64
from email.message import EmailMessage

from .digest import render


def build_message(approved, today, subject: str | None = None) -> str:
    """Build an RFC 2822 email from the approved digest items.

    - Subject defaults to "Tracker digest for <today>".
    - Body is the same wording render() produces, using only the approved
      items (never anything the reviewer rejected, and no "Needs fixing"
      section since that's not something to email an employer about).
    - "To" is left blank for the user to fill in before sending the draft.

    Returns the base64url-encoded raw message, ready for the Gmail
    drafts.create `message.raw` field.
    """
    body = render(approved, [], today)

    msg = EmailMessage()
    msg["To"] = ""
    msg["Subject"] = subject or f"Tracker digest for {today}"
    msg.set_content(body)

    return base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
