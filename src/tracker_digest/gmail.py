"""Create a Gmail draft from a raw message. Never sends anything.

Step 2 of milestone 3 (see docs/milestone-3-design.md): the code here is
built to be driven by an injected client and an injected Keychain runner, so
tests never touch the network, the real Keychain, or a Google account.
`build_gmail_client` is the only function that imports Google's libraries,
and it only does so when actually called (lazy import), so the existing
suite stays green with nothing installed.
"""
import subprocess

CLIENT_SECRET_SERVICE = "tracker-digest-gmail"
REFRESH_TOKEN_SERVICE = "tracker-digest-gmail-token"
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]


class KeychainError(Exception):
    """Raised when a Keychain item is missing or unreadable."""


def read_keychain_secret(service: str, account: str | None = None, runner=subprocess.run) -> str:
    """Read one generic-password item from the macOS Keychain.

    `runner` defaults to subprocess.run but is injected in tests so no test
    ever shells out to the real `security` CLI. Raises KeychainError with a
    clear message instead of letting a missing item look like a network
    problem later on.
    """
    args = ["security", "find-generic-password", "-s", service, "-w"]
    if account:
        args.extend(["-a", account])

    result = runner(args, capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        raise KeychainError(
            f"Keychain item {service!r} not found or unreadable "
            f"(exit code {result.returncode}). Add it with "
            f"`security add-generic-password -s {service} -a <account> -w <secret>`."
        )
    return result.stdout.strip()


def read_client_secret(runner=subprocess.run) -> str:
    """Read the OAuth client secret stored under CLIENT_SECRET_SERVICE."""
    return read_keychain_secret(CLIENT_SECRET_SERVICE, runner=runner)


def read_refresh_token(runner=subprocess.run) -> str:
    """Read the OAuth refresh token stored under REFRESH_TOKEN_SERVICE."""
    return read_keychain_secret(REFRESH_TOKEN_SERVICE, runner=runner)


def build_gmail_client(runner=subprocess.run):
    """Build a real Gmail API client, credentials pulled from the Keychain.

    Imports google-auth and googleapiclient lazily so importing this module
    (and running its tests) never requires those packages to be installed.
    Only called from real usage, never from a test.
    """
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    client_secret = read_client_secret(runner=runner)
    refresh_token = read_refresh_token(runner=runner)

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_secret=client_secret,
        scopes=SCOPES,
        token_uri="https://oauth2.googleapis.com/token",
    )
    return build("gmail", "v1", credentials=credentials)


def create_draft(client, raw_message: str) -> dict:
    """Create a Gmail draft holding `raw_message`. Never sends it.

    `client` is whatever build_gmail_client() (or a fake) returns; only
    `.users().drafts().create(userId=..., body=...).execute()` is used, so a
    fake test double only needs to implement that much of the real API.
    """
    body = {"message": {"raw": raw_message}}
    return client.users().drafts().create(userId="me", body=body).execute()
