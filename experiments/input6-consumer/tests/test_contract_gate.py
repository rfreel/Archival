from __future__ import annotations

import json
import unittest
from pathlib import Path

from consumer import UnsafeIdentifier, normalize_identifier
from fetch_dependency import assert_admissible, load_lock


ROOT = Path(__file__).resolve().parents[1]


class ContractGateTests(unittest.TestCase):
    def test_pinned_contract_identity(self) -> None:
        lock = load_lock()
        contract = json.loads(
            (ROOT / "vendor" / "contract-v1.0.0.json").read_text(encoding="utf-8")
        )
        self.assertEqual(contract["contract_id"], lock["contract_id"])
        self.assertEqual(contract["version"], lock["contract_version"])
        self.assertEqual(contract["status"], "active")

    def test_all_contract_examples_and_rejections(self) -> None:
        contract = json.loads(
            (ROOT / "vendor" / "contract-v1.0.0.json").read_text(encoding="utf-8")
        )
        for example in contract["examples"]:
            self.assertEqual(
                normalize_identifier(example["input"]), example["output"]
            )
        for example in contract["rejections"]:
            raw = example["input_escape"].encode("utf-8").decode("unicode_escape")
            with self.assertRaises(UnsafeIdentifier):
                normalize_identifier(raw)

    def test_revoked_commit_is_blocked_before_fetch(self) -> None:
        lock = load_lock()
        lock["revoked_commits"] = [lock["producer_commit"]]
        with self.assertRaisesRegex(RuntimeError, "revoked"):
            assert_admissible(lock)


if __name__ == "__main__":
    unittest.main()
