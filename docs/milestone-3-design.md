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

## Sources

- [Gmail API: users.drafts.create](https://developers.google.com/gmail/api/reference/rest/v1/users.drafts/create)
- [Gmail API: OAuth scopes](https://developers.google.com/gmail/api/auth/scopes)
- [Google Identity: OAuth 2.0 for native/installed apps](https://developers.google.com/identity/protocols/oauth2/native-app)
