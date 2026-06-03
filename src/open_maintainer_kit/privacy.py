from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

PRIVATE_PATTERNS = [
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[^'\"\s]+", re.IGNORECASE),
]

SKIP_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "outbox", "dist", "build"}
TEXT_EXTENSIONS = {".md", ".txt", ".toml", ".py", ".csv", ".yml", ".yaml", ".json"}


@dataclass(frozen=True)
class PrivacyFinding:
    path: str
    line: int
    pattern: str


@dataclass(frozen=True)
class PrivacyScan:
    ok: bool
    checked_files: int
    findings: list[PrivacyFinding]


def scan_privacy(workspace: Path) -> PrivacyScan:
    findings: list[PrivacyFinding] = []
    checked = 0
    for path in workspace.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        checked += 1
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            for pattern in PRIVATE_PATTERNS:
                if pattern.search(line):
                    findings.append(PrivacyFinding(path=str(path), line=line_number, pattern=pattern.pattern))
    return PrivacyScan(ok=not findings, checked_files=checked, findings=findings)


def render_privacy_scan_markdown(scan: PrivacyScan) -> str:
    lines = ["# Privacy Scan", "", f"- OK: {'yes' if scan.ok else 'no'}", f"- Checked files: {scan.checked_files}", f"- Findings: {len(scan.findings)}", ""]
    if scan.findings:
        lines.append("## Findings")
        lines.append("")
        lines.extend(f"- {finding.path}:{finding.line} matched `{finding.pattern}`" for finding in scan.findings)
        lines.append("")
    return "\n".join(lines)
