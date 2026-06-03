from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .io_utils import read_csv_header, write_csv_rows

ISSUE_FIELDS = ["id", "title", "state", "labels", "created_at", "updated_at", "comments", "body_signal"]
PR_FIELDS = ["id", "title", "state", "is_draft", "checks_status", "review_status", "updated_at", "author_association"]
CI_FIELDS = ["id", "name", "status", "conclusion", "branch", "commit_sha", "created_at", "url"]
RELEASE_FIELDS = ["version", "date", "status", "notes_ready", "assets_ready", "changelog_ready"]
SECURITY_FIELDS = ["id", "severity", "status", "package", "summary", "created_at"]

DATA_FILES = {
    "issues.csv": ISSUE_FIELDS,
    "pull_requests.csv": PR_FIELDS,
    "ci_runs.csv": CI_FIELDS,
    "releases.csv": RELEASE_FIELDS,
    "security.csv": SECURITY_FIELDS,
}

PRIVATE_COLUMN_HINTS = {
    "email",
    "user",
    "username",
    "session",
    "ip",
    "payload",
    "token",
    "key",
    "secret",
    "phone",
    "customer",
    "address",
}


@dataclass(frozen=True)
class WorkspaceInitResult:
    created: list[str]
    skipped: list[str]


@dataclass(frozen=True)
class WorkspaceValidation:
    ok: bool
    checked: list[str]
    errors: list[str]


def init_workspace(workspace: Path, overwrite: bool = False) -> WorkspaceInitResult:
    created: list[str] = []
    skipped: list[str] = []
    data_dir = workspace / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    for filename, fields in DATA_FILES.items():
        path = data_dir / filename
        if path.exists() and not overwrite:
            skipped.append(str(path))
            continue
        write_csv_rows(path, fields, [])
        created.append(str(path))
    return WorkspaceInitResult(created=created, skipped=skipped)


def validate_workspace(workspace: Path) -> WorkspaceValidation:
    data_dir = workspace / "data"
    checked: list[str] = []
    errors: list[str] = []
    for filename, required in DATA_FILES.items():
        path = data_dir / filename
        if not path.exists():
            example_path = data_dir / filename.replace(".csv", ".example.csv")
            path = example_path if example_path.exists() else path
        if not path.exists():
            errors.append(f"{filename}: missing {path}")
            continue
        checked.append(str(path))
        header = read_csv_header(path)
        if not header:
            errors.append(f"{filename}: empty CSV or missing header at {path}")
            continue
        normalized = {field.strip().lstrip("\ufeff").lower() for field in header}
        private = sorted(normalized & PRIVATE_COLUMN_HINTS)
        if private:
            errors.append(f"{filename}: private-looking columns are not allowed: {', '.join(private)}")
        missing = sorted(set(required) - set(header))
        if missing:
            errors.append(f"{filename}: missing required columns: {', '.join(missing)}")
    return WorkspaceValidation(ok=not errors, checked=checked, errors=errors)
