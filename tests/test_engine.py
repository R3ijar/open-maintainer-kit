from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_maintainer_kit.engine import build_candidates, build_plan, build_release_checks, default_data_paths


def write_minimal_workspace(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    (data / "issues.csv").write_text("id,title,state,labels,created_at,updated_at,comments,body_signal\n", encoding="utf-8")
    (data / "pull_requests.csv").write_text(
        "id,title,state,is_draft,checks_status,review_status,updated_at,author_association\n",
        encoding="utf-8",
    )
    (data / "ci_runs.csv").write_text("id,name,status,conclusion,branch,commit_sha,created_at,url\n", encoding="utf-8")
    (data / "releases.csv").write_text("version,date,status,notes_ready,assets_ready,changelog_ready\n", encoding="utf-8")
    (data / "security.csv").write_text("id,severity,status,package,summary,created_at\n", encoding="utf-8")


class EngineTests(unittest.TestCase):
    def test_security_beats_ci_and_prs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_workspace(root)
            (root / "data" / "security.csv").write_text(
                "id,severity,status,package,summary,created_at\n"
                "SEC-1,high,open,lib,Update dependency,2026-06-01\n",
                encoding="utf-8",
            )
            (root / "data" / "ci_runs.csv").write_text(
                "id,name,status,conclusion,branch,commit_sha,created_at,url\n"
                "1,tests,completed,failure,main,abc,2026-06-01,https://example.org/run\n",
                encoding="utf-8",
            )

            plan = build_plan(default_data_paths(root))

        self.assertEqual(plan.action_type, "review_security")

    def test_main_branch_ci_is_selected_before_pr_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_workspace(root)
            (root / "data" / "ci_runs.csv").write_text(
                "id,name,status,conclusion,branch,commit_sha,created_at,url\n"
                "1,tests,completed,failure,main,abc,2026-06-01,https://example.org/run\n",
                encoding="utf-8",
            )
            (root / "data" / "pull_requests.csv").write_text(
                "id,title,state,is_draft,checks_status,review_status,updated_at,author_association\n"
                "2,Improve docs,open,false,success,none,2026-06-01,contributor\n",
                encoding="utf-8",
            )

            candidates = build_candidates(default_data_paths(root))

        self.assertEqual(candidates[0].action_type, "fix_ci_failure")
        self.assertTrue(any(candidate.action_type == "review_pr" for candidate in candidates))

    def test_reproducible_issue_beats_release_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_workspace(root)
            (root / "data" / "issues.csv").write_text(
                "id,title,state,labels,created_at,updated_at,comments,body_signal\n"
                "3,Crash on startup,open,bug,2026-06-01,2026-06-01,4,repro\n",
                encoding="utf-8",
            )
            (root / "data" / "releases.csv").write_text(
                "version,date,status,notes_ready,assets_ready,changelog_ready\n"
                "0.1.1,2026-06-05,planned,true,false,true\n",
                encoding="utf-8",
            )

            plan = build_plan(default_data_paths(root))

        self.assertEqual(plan.action_type, "triage_issue")

    def test_release_check_reports_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            release = root / "releases.csv"
            release.write_text(
                "version,date,status,notes_ready,assets_ready,changelog_ready\n"
                "0.1.1,2026-06-05,planned,true,false,true\n",
                encoding="utf-8",
            )

            checks = build_release_checks(release)

        self.assertFalse(checks[0].ready)
        self.assertEqual(checks[0].gaps, ["release assets are not ready"])

    def test_waits_when_no_signal_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_workspace(root)

            plan = build_plan(default_data_paths(root))

        self.assertEqual(plan.action_type, "wait_for_signal")


if __name__ == "__main__":
    unittest.main()
