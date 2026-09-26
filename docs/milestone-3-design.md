# Milestone 3 design: Gmail draft creation

Goal: turn an approved digest into a Gmail **draft** (never sent). No code yet — this is the plan.

## Scope: the smallest one that can create drafts

Gmail API scopes that permit `users.drafts.create`, per the [Drafts: create reference](https://developers.google.com/gmail/api/reference/rest/v1/users.drafts/create):

- `https://mail.google.com/` (full mailbox — too broad)
- `https://www.googleapis.com/auth/gmail.modify` (read + compose + send, minus permanent delete — too broad)
- `https://www.googleapis.com/auth/gmail.compose`

**Use `gmail.compose`.** Per the [scopes reference](https://developers.google.com/gmail/api/auth/scopes), it grants "Manage drafts and send emails" but *not* reading existing messages, labels, or settings. That matches this tool's shape: it only ever writes a draft, it never reads the mailbox. It is broader than the narrowest possible ("create drafts only" isn't a scope Google offers — `gmail.compose` also covers sending, which this tool will just never call).

## Where the client secret and token live

Both stay **outside the repository**, per Google's [OAuth 2.0 for native/installed apps](https://developers.google.com/identity/protocols/oauth2/native-app):

- **Client secret** (from the Cloud Console OAuth client, "Desktop app" type): stored in the **macOS Keychain**, one item, read with the `security` CLI (`security find-generic-password -s tracker-digest-gmail -w`), the same pattern already used for the TypeSafe API key. Never written to a file in the repo or its parent folders.
- **Refresh token** (obtained once via the installed-app / loopback flow, `http://127.0.0.1:<port>`): also a Keychain item, separate service name (e.g. `tracker-digest-gmail-token`). Google's guidance is to store it "in a secure, long-lived location accessible between invocations" — Keychain satisfies that without adding a token file to `.gitignore` and hoping nobody `git add -f`'s it.
- `.gitignore` already excludes credential-shaped files as a second line of defense, but Keychain means there's no file to accidentally commit in the first place.
- The OAuth client secret is technically optional for installed apps per Google's own doc, but Google's Cloud Console still issues one for "Desktop app" clients, so we store and send it; no PKCE-without-secret shortcut needed for a CLI tool run by one person.

## Standard library vs. `google-api-python-client`

**This is the one place the "no dependencies" rule bends, and it should bend.**

- Doing OAuth token exchange and a signed HTTPS POST by hand with `urllib` is possible (the token endpoint and `users.drafts.create` are plain REST/JSON), but reimplementing token refresh, expiry handling, and the library's retry/backoff means maintaining a small OAuth client ourselves — exactly the kind of code most likely to have a subtle security bug (token leakage, wrong scope requested, silent refresh failure).
- `google-api-python-client` + `google-auth-oauthlib` is the combination Google's own quickstart and reference samples use for this exact flow. It is well-maintained, and the *tradeoff* is explicit: we accept one dependency family (plus `google-auth`) in exchange for not hand-rolling OAuth.
- Recommendation: add `google-api-python-client`, `google-auth-httplib2`, and `google-auth-oauthlib` as the **only** third-party dependencies, scoped to a new `tracker_digest/gmail.py` module, and update the README's "No dependencies" claim to "no dependencies for the core tool; Milestone 3's Gmail integration adds three Google-maintained libraries." Keep `find_stale`/`render`/`review`/`cli` dependency-free as they are now — only the new Gmail module imports Google's libraries, so the existing 20 tests keep running with zero installs.

## How `review-log.json` and human review connect to draft creation

No new review mechanism — reuse what exists:

1. `cli.main()` already calls `review(stale, ask, args.log)`, which asks per-item and returns only the **approved** items, appending every decision (approved or rejected) to `review-log.json` (`src/tracker_digest/review.py`).
2. Milestone 3 adds one step *after* that: `render(approved, problems, today)` builds the digest text exactly as today, and a new `gmail.create_draft(text, to, subject)` wraps it as a MIME message and calls `users.drafts.create`.
3. **Nothing reaches Gmail that wasn't already approved.** The draft body is built only from the `approved` list `review()` returned — rejected items never appear in it, and `review-log.json` remains the audit trail proving which items a human said yes to before the draft existed.
4. `create_draft` is called at most once per run, only when `approved` is non-empty, and only creates a draft (`drafts.create`, not `messages.send`) — so even a bug can't send email, only leave an extra draft in Gmail.

## Test plan (never calls the real API)

All tests use a fake/mock Gmail client — no network, no real credentials, no real Google account touched.

1. **Unit: MIME construction.** Given a digest string, sender, and recipient, `gmail.build_message(...)` returns a base64url-encoded RFC 2822 message. Assert on decoding it back (headers, body) — no API call involved.
2. **Unit: `create_draft` with a fake client.** Inject a stub object in place of the real `googleapiclient` service (e.g. a `FakeDraftsResource` recording `.create(userId=..., body=...)` calls and returning a canned `{"id": "..."}`). Assert it's called exactly once, with `userId="me"` and the expected `message.raw` payload.
3. **Unit: no-op on empty approval.** `approved == []` → `create_draft` (or the CLI step that calls it) is never invoked. Assert the fake client records zero calls.
4. **Unit: credential loading is mocked.** A fake "Keychain reader" function is injected wherever `security find-generic-password` would be shelled out to; test that a missing credential raises a clear error rather than the code silently trying to hit the network.
5. **Integration-style: CLI end to end with a fake Gmail service.** Extend `test_cli.py`'s existing `main()`-driving pattern: inject the fake drafts client the same way the test already fakes `input()`, run against `sample/leads.csv`, and assert the fake recorded exactly one `create` call whose body matches `render()`'s output for the approved rows.
6. **Never-network guard.** No test imports `googleapiclient.discovery.build` against real credentials; any test touching the Gmail module only exercises code paths that accept an injected client, so there is no code path in the test suite capable of reaching `gmail.googleapis.com`.

All new tests join the existing suite and must keep `PYTHONPATH=src python3 -m unittest discover -s tests` fully green with no network access required.

## Step 3 setup, researched

This is what Connor needs to do by hand in his Google account, and what it means for how this tool behaves afterward. Cited to Google's current docs; nothing here is from third-party blog posts.

### 1. Create the Cloud project and enable the Gmail API

1. Go to the [Google Cloud console](https://console.cloud.google.com/) and create a new project (or pick an existing personal one) from the project picker.
2. Go to **Menu > APIs & Services > Library**, search "Gmail API," open it, and click **Enable**. Per Google's guide, "you can turn on one or more APIs in a single Google Cloud project" ([Enable Google Workspace APIs](https://developers.google.com/workspace/guides/enable-apis)).

### 2. Configure the OAuth consent screen

Since 2024 this lives under **APIs & Services > Google Auth Platform**, split into **Branding**, **Audience**, and **Clients** tabs ([Configure the OAuth consent screen and choose scopes](https://developers.google.com/workspace/guides/configure-oauth-consent)).

1. **Branding**: enter an app name and a support email, then Next.
2. **Audience**: choose the user type.
   - **External** — required unless the Google account belongs to a Google Workspace organization. This is the right choice for a personal Gmail account.
   - **Internal** — only available "for apps used only internally by your Google Workspace organization" ([same doc](https://developers.google.com/workspace/guides/configure-oauth-consent)); not applicable here.
3. Leave the publishing status as **Testing** (the default for a new app) — no submission needed for personal use.
4. **Add Connor as a test user**: on the Audience tab, add his own Google account email under test users and save. Google's docs are explicit: "If you selected External for user type, add test users by clicking Audience and entering your email address and any other authorized test users, then click Save" ([Manage App Audience](https://support.google.com/cloud/answer/15549945?hl=en)). Without this, his own account can't complete the consent flow at all — Testing status blocks any account not on that list.

### 3. Create the Desktop app OAuth client

1. **APIs & Services > Google Auth Platform > Clients > Create Client**.
2. **Application type > Desktop app**.
3. Give it a name (console-only label, e.g. "tracker-digest").
4. Click **Create**. ([Create access credentials](https://developers.google.com/workspace/guides/create-credentials))

The console shows a client ID and client secret — both go straight into the Keychain, per the existing plan above, never into a file.

### 4. Is `gmail.compose` sensitive or restricted?

**Restricted**, not merely sensitive. Google's [Gmail API OAuth scopes reference](https://developers.google.com/workspace/gmail/api/auth/scopes) lists `gmail.compose` ("Manage drafts and send emails") in its restricted-scope table. Restricted scopes "provide wide access to Google user data and require restricted-scope OAuth App verification," and apps that access restricted-scope data from or through a third-party server must also pass an annual third-party security assessment (CASA) ([Restricted scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification)).

**What this means for this tool**: none of that verification or CASA burden applies as long as the app stays in **Testing** status with Connor as the only test user. Verification and the security assessment are only required to move an app to a "In production," publicly-verified state for other users — not to use a restricted scope yourself, on your own data, in Testing. This tool never needs to leave Testing.

### 5. Refresh token lifetime in Testing status

**Seven days.** Per Google's own docs: "Authorizations by a test user will expire seven days from the time of consent. If your OAuth client requests offline access and receives a refresh token, that token will also expire" ([Manage App Audience](https://support.google.com/cloud/answer/15549945?hl=en); consistent with [OAuth app state overview](https://developers.google.com/identity/protocols/oauth2/production-readiness/overview)). The only exemption is for apps requesting solely `openid`/`email`/`profile` scopes — `gmail.compose` doesn't qualify.

**What this means for the tool**: the refresh token stored in the Keychain will go stale about once a week. `build_gmail_client` will start getting `invalid_grant` from the token endpoint 7 days after the last consent. There are two ways to live with this while staying in Testing (moving to "In production" requires Google's verification + CASA for a restricted scope, which is disproportionate for a single-user personal tool):
- **Re-consent every ~7 days**: rerun the one-time flow below whenever a run fails with `invalid_grant`, and overwrite the Keychain token. Simplest, matches the tool's low run frequency.
- Accept this as a known limitation and surface a clear error (already partly done — `KeychainError` — but `invalid_grant` from Google's token endpoint is a separate failure mode worth catching explicitly in `gmail.py` and pointing at re-consent, as a small follow-up, not part of this doc's step 3).

### 6. The one-time consent flow this tool will run

Not yet built (that's the actual step 3 work), but the shape Google's library expects for a Desktop-app client is the "installed app" / loopback flow ([OAuth 2.0 for native/installed apps](https://developers.google.com/identity/protocols/oauth2/native-app), already cited above):

1. The tool runs `google_auth_oauthlib.flow.InstalledAppFlow.from_client_config(...).run_local_server(port=0)` with `SCOPES` (`gmail.compose`) and the client ID/secret pulled from the Keychain.
2. That opens Connor's browser to Google's consent screen, showing the "app isn't verified" warning (expected — the app is in Testing) plus a continue-anyway path since he's a listed test user.
3. He signs in and approves; Google redirects to `http://127.0.0.1:<port>`, which the library's local server catches.
4. The library exchanges the auth code for an access token + refresh token; the code writes the refresh token to the Keychain (`tracker-digest-gmail-token`), overwriting any expired one.
5. Every later run just reads the refresh token from the Keychain and lets `google-auth` mint short-lived access tokens from it — no browser involved — until the 7-day expiry forces step 1–4 again.

## Sources

- [Gmail API: users.drafts.create](https://developers.google.com/gmail/api/reference/rest/v1/users.drafts/create)
- [Gmail API: OAuth scopes](https://developers.google.com/workspace/gmail/api/auth/scopes)
- [Google Identity: OAuth 2.0 for native/installed apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Enable Google Workspace APIs](https://developers.google.com/workspace/guides/enable-apis)
- [Configure the OAuth consent screen and choose scopes](https://developers.google.com/workspace/guides/configure-oauth-consent)
- [Create access credentials](https://developers.google.com/workspace/guides/create-credentials)
- [Manage App Audience (test users, 7-day refresh token expiry, 100 test user limit)](https://support.google.com/cloud/answer/15549945?hl=en)
- [OAuth app state overview (Testing vs. production)](https://developers.google.com/identity/protocols/oauth2/production-readiness/overview)
- [Restricted scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification)
