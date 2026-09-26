import unittest

from tracker_digest.gmail import (
    KeychainError,
    create_draft,
    read_keychain_secret,
)


class FakeDraftsResource:
    def __init__(self):
        self.calls = []

    def create(self, userId, body):
        self.calls.append({"userId": userId, "body": body})
        return _FakeRequest({"id": "draft-1"})


class _FakeRequest:
    def __init__(self, result):
        self._result = result

    def execute(self):
        return self._result


class FakeUsersResource:
    def __init__(self, drafts):
        self._drafts = drafts

    def drafts(self):
        return self._drafts


class FakeGmailClient:
    """Stands in for the object googleapiclient.discovery.build() returns."""

    def __init__(self):
        self.drafts_resource = FakeDraftsResource()

    def users(self):
        return FakeUsersResource(self.drafts_resource)


class TestCreateDraft(unittest.TestCase):
    def test_creates_exactly_one_draft_with_the_raw_message(self):
        client = FakeGmailClient()
        result = create_draft(client, "b64url-raw-message")

        self.assertEqual(len(client.drafts_resource.calls), 1)
        call = client.drafts_resource.calls[0]
        self.assertEqual(call["userId"], "me")
        self.assertEqual(call["body"], {"message": {"raw": "b64url-raw-message"}})
        self.assertEqual(result, {"id": "draft-1"})


class TestReadKeychainSecret(unittest.TestCase):
    def test_returns_the_secret_the_runner_prints(self):
        def fake_runner(args, **kwargs):
            self.assertIn("find-generic-password", args)
            self.assertIn("tracker-digest-gmail", args)
            return _FakeCompleted(stdout="the-secret\n", returncode=0)

        secret = read_keychain_secret("tracker-digest-gmail", runner=fake_runner)
        self.assertEqual(secret, "the-secret")

    def test_missing_item_raises_a_clear_error(self):
        def fake_runner(args, **kwargs):
            return _FakeCompleted(stdout="", returncode=44)

        with self.assertRaises(KeychainError):
            read_keychain_secret("tracker-digest-gmail-token", runner=fake_runner)


class _FakeCompleted:
    def __init__(self, stdout, returncode):
        self.stdout = stdout
        self.returncode = returncode


if __name__ == "__main__":
    unittest.main()
