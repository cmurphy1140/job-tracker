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


def write_keychain_secret(service: str, secret: str, account: str | None = None, runner=subprocess.run) -> None:
    """Write (or overwrite) one generic-password item in the macOS Keychain.

    `-U` tells `security` to update the item in place if it already exists,
    so re-running `auth` overwrites an expired refresh token instead of
    failing on a duplicate item. `runner` is injected the same way
    `read_keychain_secret` injects it, so no test ever shells out for real
    or logs the secret it stores.
    """
    args = ["security", "add-generic-password", "-s", service, "-w", secret, "-U"]
    if account:
        args.extend(["-a", account])

    result = runner(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise KeychainError(
            f"Could not write Keychain item {service!r} (exit code {result.returncode})."
        )


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


def run_installed_app_flow(client_secret_json: str, scopes) -> str:
    """Run the real one-time installed-app OAuth flow, return the refresh token.

    Lazy-imports google_auth_oauthlib so this module (and its tests) never
    require it installed. Opens a browser via InstalledAppFlow.run_local_server
    per docs/milestone-3-design.md step 6 — only ever called from real usage
    (`cli.py`'s `auth` command), never from a test.
    """
    import json

    from google_auth_oauthlib.flow import InstalledAppFlow

    config = json.loads(client_secret_json)
    flow = InstalledAppFlow.from_client_config(config, scopes)
    credentials = flow.run_local_server(port=0)
    return credentials.refresh_token


def authorize(client_secret_json: str, flow_runner=run_installed_app_flow, write_secret=write_keychain_secret) -> None:
    """Run the one-time sign-in and store both secrets in the Keychain.

    `flow_runner(client_secret_json, SCOPES) -> refresh_token` is
    `run_installed_app_flow` in real use, and a fake in tests, so the OAuth
    flow (browser, local server, network) never runs during the test suite.
    Stores the client secret JSON itself under CLIENT_SECRET_SERVICE and the
    resulting refresh token under REFRESH_TOKEN_SERVICE, overwriting any
    expired one from a previous consent.
    """
    refresh_token = flow_runner(client_secret_json, SCOPES)
    write_secret(CLIENT_SECRET_SERVICE, client_secret_json)
    write_secret(REFRESH_TOKEN_SERVICE, refresh_token)


def create_draft(client, raw_message: str) -> dict:
    """Create a Gmail draft holding `raw_message`. Never sends it.

    `client` is whatever build_gmail_client() (or a fake) returns; only
    `.users().drafts().create(userId=..., body=...).execute()` is used, so a
    fake test double only needs to implement that much of the real API.
    """
    body = {"message": {"raw": raw_message}}
    return client.users().drafts().create(userId="me", body=body).execute()
