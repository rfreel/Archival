from __future__ import annotations

import unittest

from consumer import UnsafeIdentifier, canonicalize_external_keys, normalize_identifier


class NovelInputTests(unittest.TestCase):
    def test_compatibility_and_casefold_inputs(self) -> None:
        self.assertEqual(normalize_identifier("  KELVIN  "), "kelvin")
        self.assertEqual(normalize_identifier("Straße"), "strasse")
        self.assertEqual(normalize_identifier("INV①"), "inv1")

    def test_downstream_deduplication_task(self) -> None:
        result = canonicalize_external_keys(
            ["KELVIN", " kelvin ", "Straße", "STRASSE", "INV①"]
        )
        self.assertEqual(result, ["kelvin", "strasse", "inv1"])

    def test_invisible_format_character_is_rejected(self) -> None:
        with self.assertRaises(UnsafeIdentifier):
            normalize_identifier("account\u200dadmin")


if __name__ == "__main__":
    unittest.main()
