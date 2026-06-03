from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_maintainer_kit.privacy import scan_privacy


class PrivacyTests(unittest.TestCase):
    def test_scan_detects_email_addresses(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            address = "person" + "@" + "example.org"
            (root / "README.md").write_text(f"Contact {address}\n", encoding="utf-8")

            result = scan_privacy(root)

        self.assertFalse(result.ok)
        self.assertEqual(len(result.findings), 1)


if __name__ == "__main__":
    unittest.main()
