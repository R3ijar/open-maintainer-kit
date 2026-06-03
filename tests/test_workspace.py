from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_maintainer_kit.workspace import init_workspace, validate_workspace


class WorkspaceTests(unittest.TestCase):
    def test_init_creates_default_data_files_without_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = init_workspace(root)
            issues = root / "data" / "issues.csv"
            issues.write_text("custom\n", encoding="utf-8")

            second = init_workspace(root)
            text = issues.read_text(encoding="utf-8")

        self.assertEqual(len(result.created), 5)
        self.assertEqual(len(second.created), 0)
        self.assertEqual(len(second.skipped), 5)
        self.assertEqual(text, "custom\n")

    def test_validate_accepts_initialized_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            init_workspace(root)

            result = validate_workspace(root)

        self.assertTrue(result.ok, result.errors)
        self.assertEqual(len(result.checked), 5)

    def test_validate_rejects_private_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            init_workspace(root)
            address = "person" + "@" + "example.org"
            (root / "data" / "issues.csv").write_text(
                "id,title,state,labels,created_at,updated_at,comments,body_signal,email\n"
                f"1,Problem,open,bug,2026-06-01,2026-06-01,0,repro,{address}\n",
                encoding="utf-8",
            )

            result = validate_workspace(root)

        self.assertFalse(result.ok)
        self.assertTrue(any("private-looking columns" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
