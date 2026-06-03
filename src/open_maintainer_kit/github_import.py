from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .io_utils import write_csv_rows
from .workspace import CI_FIELDS, ISSUE_FIELDS, PR_FIELDS, RELEASE_FIELDS, SECURITY_FIELDS

Runner = Callable[[list[str]], str]


@dataclass(frozen=True)
class GitHubImportResult:
    repo: str
    workspace: str
    counts: dict[str, int]
    files: dict[str, str]


def import_github_repo(repo: str, workspace: Path, limit: int = 100, runner: Runner | None = None) -> GitHubImportResult:
    if "/" not in repo or repo.count("/") != 1:
        raise ValueError("repo must use owner/name format, for example R3ijar/open-growth-loop")
    if limit < 1:
        raise ValueError("limit must be at least 1")

    run = runner or run_gh
    data_dir = workspace / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    issues = _issue_rows(
        _gh_json(
            run,
            [
                "issue",
                "list",
                "--repo",
                repo,
                "--state",
                "open",
                "--limit",
                str(limit),
                "--json",
                "number,title,state,labels,createdAt,updatedAt,comments",
            ],
        )
    )
    pull_requests = _pull_request_rows(
        _gh_json(
            run,
            [
                "pr",
                "list",
                "--repo",
                repo,
                "--state",
                "open",
                "--limit",
                str(limit),
                "--json",
                "number,title,state,isDraft,statusCheckRollup,reviewDecision,updatedAt",
            ],
        )
    )
    ci_runs = _ci_rows(
        _gh_json(
            run,
            [
                "run",
                "list",
                "--repo",
                repo,
                "--limit",
                str(limit),
                "--json",
                "databaseId,workflowName,status,conclusion,headBranch,headSha,createdAt,url",
            ],
        )
    )
    releases = _release_rows(
        _gh_json(
            run,
            [
                "release",
                "list",
                "--repo",
                repo,
                "--limit",
                str(limit),
                "--json",
                "tagName,createdAt,isDraft,isLatest,isPrerelease,publishedAt,name",
            ],
        )
    )
    security: list[dict[str, object]] = []

    outputs = {
        "issues": data_dir / "issues.csv",
        "pull_requests": data_dir / "pull_requests.csv",
        "ci_runs": data_dir / "ci_runs.csv",
        "releases": data_dir / "releases.csv",
        "security": data_dir / "security.csv",
    }
    write_csv_rows(outputs["issues"], ISSUE_FIELDS, issues)
    write_csv_rows(outputs["pull_requests"], PR_FIELDS, pull_requests)
    write_csv_rows(outputs["ci_runs"], CI_FIELDS, ci_runs)
    write_csv_rows(outputs["releases"], RELEASE_FIELDS, releases)
    write_csv_rows(outputs["security"], SECURITY_FIELDS, security)

    return GitHubImportResult(
        repo=repo,
        workspace=str(workspace),
        counts={
            "issues": len(issues),
            "pull_requests": len(pull_requests),
            "ci_runs": len(ci_runs),
            "releases": len(releases),
            "security": len(security),
        },
        files={key: str(path) for key, path in outputs.items()},
    )


def run_gh(args: list[str]) -> str:
    gh = _find_gh()
    if not gh:
        raise RuntimeError(
            "GitHub CLI was not found. Install it from https://cli.github.com/ or use winget install --id GitHub.cli"
        )
    completed = subprocess.run([gh, *args], capture_output=True, check=False, text=True)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(f"gh {' '.join(args)} failed: {detail}")
    return completed.stdout


def _find_gh() -> str:
    gh = shutil.which("gh")
    if gh:
        return gh
    for path in [Path("C:/Program Files/GitHub CLI/gh.exe")]:
        if path.exists():
            return str(path)
    return ""


def _gh_json(run: Runner, args: list[str]) -> list[dict[str, object]]:
    payload = json.loads(run(args) or "[]")
    if not isinstance(payload, list):
        raise RuntimeError(f"gh {' '.join(args)} returned a non-list JSON payload")
    return [item for item in payload if isinstance(item, dict)]


def _issue_rows(items: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in items:
        labels = _label_names(item.get("labels"))
        rows.append(
            {
                "id": item.get("number", ""),
                "title": item.get("title", ""),
                "state": _normalize(item.get("state")),
                "labels": labels,
                "created_at": item.get("createdAt", ""),
                "updated_at": item.get("updatedAt", ""),
                "comments": _count_comments(item.get("comments")),
                "body_signal": _body_signal(labels),
            }
        )
    return rows


def _pull_request_rows(items: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in items:
        rows.append(
            {
                "id": item.get("number", ""),
                "title": item.get("title", ""),
                "state": _normalize(item.get("state")),
                "is_draft": str(bool(item.get("isDraft"))).lower(),
                "checks_status": _checks_status(item.get("statusCheckRollup")),
                "review_status": _review_status(item.get("reviewDecision")),
                "updated_at": item.get("updatedAt", ""),
                "author_association": "",
            }
        )
    return rows


def _ci_rows(items: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in items:
        rows.append(
            {
                "id": item.get("databaseId", ""),
                "name": item.get("workflowName", ""),
                "status": _normalize(item.get("status")),
                "conclusion": _normalize(item.get("conclusion")),
                "branch": item.get("headBranch", ""),
                "commit_sha": item.get("headSha", ""),
                "created_at": item.get("createdAt", ""),
                "url": item.get("url", ""),
            }
        )
    return rows


def _release_rows(items: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in items:
        is_draft = bool(item.get("isDraft"))
        is_prerelease = bool(item.get("isPrerelease"))
        published = bool(item.get("publishedAt")) and not is_draft
        status = "draft" if is_draft else "prerelease" if is_prerelease else "published"
        rows.append(
            {
                "version": item.get("tagName", ""),
                "date": item.get("publishedAt") or item.get("createdAt", ""),
                "status": status,
                "notes_ready": str(published).lower(),
                "assets_ready": str(published).lower(),
                "changelog_ready": str(published).lower(),
            }
        )
    return rows


def _label_names(value: object) -> str:
    if not isinstance(value, list):
        return ""
    names: list[str] = []
    for item in value:
        if isinstance(item, dict):
            name = item.get("name", "")
        else:
            name = item
        if str(name).strip():
            names.append(str(name).strip())
    return ";".join(names)


def _count_comments(value: object) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict) and "totalCount" in value:
        return _safe_int(value.get("totalCount"))
    return _safe_int(value)


def _checks_status(value: object) -> str:
    if not isinstance(value, list) or not value:
        return "unknown"
    states = {_normalize(item.get("status")) for item in value if isinstance(item, dict)}
    conclusions = {_normalize(item.get("conclusion")) for item in value if isinstance(item, dict)}
    combined = states | conclusions
    if combined & {"failure", "failed", "timed_out", "cancelled", "action_required", "startup_failure"}:
        return "failure"
    if combined & {"pending", "queued", "requested", "waiting", "in_progress", "expected", ""}:
        return "pending"
    if combined <= {"", "success", "completed", "neutral", "skipped"}:
        return "success"
    return "unknown"


def _review_status(value: object) -> str:
    normalized = _normalize(value)
    return {
        "approved": "approved",
        "changes_requested": "changes_requested",
        "review_required": "none",
        "": "none",
    }.get(normalized, normalized or "none")


def _body_signal(labels: str) -> str:
    normalized = {_normalize(label) for label in labels.split(";") if label.strip()}
    if normalized & {"bug", "repro", "reproduction", "reproducible", "minimal_repro"}:
        return "repro"
    if normalized & {"needs_info", "needs_reproduction", "question"}:
        return "missing_info"
    return ""


def _normalize(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def _safe_int(value: object) -> int:
    try:
        return int(str(value or "0").strip())
    except ValueError:
        return 0
