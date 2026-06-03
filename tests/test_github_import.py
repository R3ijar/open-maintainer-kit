from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from open_maintainer_kit.engine import build_plan, default_data_paths
from open_maintainer_kit.github_import import import_github_repo
from open_maintainer_kit.io_utils import read_csv_rows
from open_maintainer_kit.workspace import validate_workspace


class GitHubImportTests(unittest.TestCase):
    def test_import_writes_schema_safe_csvs(self) -> None:
        def runner(args: list[str]) -> str:
            command = args[:2]
            if command == ["issue", "list"]:
                return json.dumps(
                    [
                        {
                            "number": 12,
                            "title": "Crash on startup",
                            "state": "OPEN",
                            "labels": [{"name": "bug"}],
                            "createdAt": "2026-06-01T00:00:00Z",
                            "updatedAt": "2026-06-02T00:00:00Z",
                            "comments": [{"body": "not imported"}],
                        }
                    ]
                )
            if command == ["pr", "list"]:
                return json.dumps(
                    [
                        {
                            "number": 21,
                            "title": "Improve docs",
                            "state": "OPEN",
                            "isDraft": False,
                            "statusCheckRollup": [
                                {"status": "COMPLETED", "conclusion": "SUCCESS"},
                            ],
                            "reviewDecision": "REVIEW_REQUIRED",
                            "updatedAt": "2026-06-02T00:00:00Z",
                        }
                    ]
                )
            if command == ["run", "list"]:
                return json.dumps(
                    [
                        {
                            "databaseId": 31,
                            "workflowName": "CI",
                            "status": "COMPLETED",
                            "conclusion": "FAILURE",
                            "headBranch": "main",
                            "headSha": "abc1234",
                            "createdAt": "2026-06-02T00:00:00Z",
                            "url": "https://example.org/run",
                        }
                    ]
                )
            if command == ["release", "list"]:
                return json.dumps(
                    [
                        {
                            "tagName": "v0.1.0",
                            "createdAt": "2026-06-02T00:00:00Z",
                            "publishedAt": "2026-06-02T00:10:00Z",
                            "isDraft": False,
                            "isPrerelease": False,
                            "isLatest": True,
                            "name": "v0.1.0",
                        }
                    ]
                )
            raise AssertionError(f"unexpected gh command: {args}")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = import_github_repo("owner/repo", root, limit=5, runner=runner)
            validation = validate_workspace(root)
            plan = build_plan(default_data_paths(root))
            issues = read_csv_rows(root / "data" / "issues.csv")
            prs = read_csv_rows(root / "data" / "pull_requests.csv")
            runs = read_csv_rows(root / "data" / "ci_runs.csv")

        self.assertEqual(result.counts["issues"], 1)
        self.assertTrue(validation.ok, validation.errors)
        self.assertEqual(issues[0]["body_signal"], "repro")
        self.assertEqual(prs[0]["review_status"], "none")
        self.assertEqual(runs[0]["conclusion"], "failure")
        self.assertEqual(plan.action_type, "fix_ci_failure")

    def test_rejects_invalid_repo_locator(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                import_github_repo("not-a-repo", Path(temp_dir), runner=lambda args: "[]")


if __name__ == "__main__":
    unittest.main()
