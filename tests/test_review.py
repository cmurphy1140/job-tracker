import json
import tempfile
import unittest
from pathlib import Path

from tracker_digest.review import review


class Review(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.log = Path(self.dir.name) / "review-log.json"

    def tearDown(self):
        self.dir.cleanup()

    def test_only_approved_items_come_back(self):
        kept = review(["a", "b", "c"], lambda item: item != "b", self.log)
        self.assertEqual(kept, ["a", "c"])

    def test_every_decision_is_logged(self):
        review(["a", "b"], lambda item: item == "a", self.log)
        self.assertEqual(json.loads(self.log.read_text()),
                         [{"item": "a", "approved": True}, {"item": "b", "approved": False}])

    def test_log_is_appended_across_runs(self):
        review(["a"], lambda _: True, self.log)
        review(["b"], lambda _: False, self.log)
        self.assertEqual(len(json.loads(self.log.read_text())), 2)

    def test_nothing_to_review_writes_nothing_and_returns_empty(self):
        self.assertEqual(review([], lambda _: True, self.log), [])


if __name__ == "__main__":
    unittest.main()
