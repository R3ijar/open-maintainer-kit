from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .io_utils import parse_bool, parse_int, read_csv_rows, write_json_report, write_text_report


@dataclass(frozen=True)
class Candidate:
    action_type: str
    target: str
    title: str
    reason: str
    priority: int
    score: float
    confidence: str
    source: str
    next_steps: list[str]
    evidence: dict[str, object]
    blocked_by: list[str]


@dataclass(frozen=True)
class MaintainerPlan:
    action_type: str
    target: str
    title: str
    reason: str
    confidence: str
    next_steps: list[str]
    evidence: dict[str, object]


@dataclass(frozen=True)
class ReleaseCheck:
    version: str
    status: str
    ready: bool
    gaps: list[str]


def default_data_paths(workspace: Path) -> dict[str, Path]:
    data = workspace / "data"
    return {
        "issues": _first_existing(data / "issues.csv", data / "issues.example.csv"),
        "pull_requests": _first_existing(data / "pull_requests.csv", data / "pull_requests.example.csv"),
        "ci_runs": _first_existing(data / "ci_runs.csv", data / "ci_runs.example.csv"),
        "releases": _first_existing(data / "releases.csv", data / "releases.example.csv"),
        "security": _first_existing(data / "security.csv", data / "security.example.csv"),
    }


def build_candidates(paths: dict[str, Path]) -> list[Candidate]:
    issues = read_csv_rows(paths["issues"])
    pull_requests = read_csv_rows(paths["pull_requests"])
    ci_runs = read_csv_rows(paths["ci_runs"])
    releases = read_csv_rows(paths["releases"])
    security = read_csv_rows(paths["security"])
    candidates: list[Candidate] = []
    candidates.extend(_security_candidates(security))
    candidates.extend(_ci_candidates(ci_runs))
    candidates.extend(_pull_request_candidates(pull_requests))
    candidates.extend(_issue_candidates(issues))
    candidates.extend(_release_candidates(releases))
    return sort_candidates(candidates)


def sort_candidates(candidates: list[Candidate]) -> list[Candidate]:
    return sorted(candidates, key=lambda item: (bool(item.blocked_by), item.priority, -item.score, item.target))


def build_plan(paths: dict[str, Path]) -> MaintainerPlan:
    candidates = build_candidates(paths)
    if not candidates:
        return MaintainerPlan(
            action_type="wait_for_signal",
            target="",
            title="Wait for a stronger maintainer signal",
            reason="No open security item, broken main CI run, ready PR, reproducible issue, or release-readiness gap was found.",
            confidence="high",
            next_steps=[
                "Refresh local exports or CSVs.",
                "Keep issue and PR labels current.",
                "Run release-check before cutting the next release.",
            ],
            evidence={
                "decision": {
                    "selected_rule": "wait_for_signal",
                    "alternatives": [],
                }
            },
        )
    selected = candidates[0]
    return MaintainerPlan(
        action_type=selected.action_type,
        target=selected.target,
        title=selected.title,
        reason=selected.reason,
        confidence=selected.confidence,
        next_steps=list(selected.next_steps),
        evidence={
            **selected.evidence,
            "decision": {
                "selected_rule": selected.source,
                "alternatives": [candidate_brief(item) for item in candidates[1:6]],
            },
        },
    )


def build_release_checks(releases_path: Path) -> list[ReleaseCheck]:
    checks: list[ReleaseCheck] = []
    for row in read_csv_rows(releases_path):
        gaps: list[str] = []
        if not parse_bool(row.get("notes_ready")):
            gaps.append("release notes are not ready")
        if not parse_bool(row.get("assets_ready")):
            gaps.append("release assets are not ready")
        if not parse_bool(row.get("changelog_ready")):
            gaps.append("changelog is not ready")
        checks.append(
            ReleaseCheck(
                version=row.get("version", ""),
                status=_normalize(row.get("status")),
                ready=not gaps,
                gaps=gaps,
            )
        )
    return checks


def write_plan_reports(plan: MaintainerPlan, out_dir: Path) -> tuple[Path, Path]:
    md_path = out_dir / "latest-plan.md"
    json_path = out_dir / "latest-plan.json"
    write_text_report(md_path, render_plan_markdown(plan))
    write_json_report(json_path, asdict(plan))
    return md_path, json_path


def render_candidates_markdown(candidates: list[Candidate]) -> str:
    lines = ["# Maintainer Triage Queue", ""]
    if not candidates:
        lines.append("No candidates met the current rules.")
        return "\n".join(lines) + "\n"
    for index, candidate in enumerate(candidates, start=1):
        lines.extend(
            [
                f"## {index}. {candidate.title}",
                "",
                f"- Action: {candidate.action_type}",
                f"- Target: {candidate.target or 'none'}",
                f"- Source: {candidate.source}",
                f"- Priority: {candidate.priority}",
                f"- Score: {candidate.score:.3f}",
                f"- Confidence: {candidate.confidence}",
                f"- Reason: {candidate.reason}",
                "",
            ]
        )
        if candidate.blocked_by:
            lines.append("Blocked by:")
            lines.extend(f"- {item}" for item in candidate.blocked_by)
            lines.append("")
    return "\n".join(lines)


def render_plan_markdown(plan: MaintainerPlan) -> str:
    lines = [
        "# Maintainer Plan",
        "",
        f"**Action:** {plan.action_type}",
        f"**Target:** {plan.target or 'none'}",
        f"**Confidence:** {plan.confidence}",
        "",
        f"## {plan.title}",
        "",
        plan.reason,
        "",
        "## Next Steps",
        "",
    ]
    lines.extend(f"- {step}" for step in plan.next_steps)
    lines.extend(["", "## Evidence", "", "```json"])
    import json

    lines.append(json.dumps(plan.evidence, indent=2, sort_keys=True))
    lines.extend(["```", ""])
    return "\n".join(lines)


def render_release_checks_markdown(checks: list[ReleaseCheck]) -> str:
    lines = ["# Release Readiness", ""]
    if not checks:
        lines.append("No release rows found.")
        return "\n".join(lines) + "\n"
    for check in checks:
        lines.extend(
            [
                f"## {check.version or 'unknown'}",
                "",
                f"- Status: {check.status or 'unknown'}",
                f"- Ready: {'yes' if check.ready else 'no'}",
            ]
        )
        if check.gaps:
            lines.append("- Gaps:")
            lines.extend(f"  - {gap}" for gap in check.gaps)
        lines.append("")
    return "\n".join(lines)


def candidate_brief(candidate: Candidate) -> dict[str, object]:
    return {
        "action_type": candidate.action_type,
        "target": candidate.target,
        "source": candidate.source,
        "priority": candidate.priority,
        "score": round(candidate.score, 3),
        "reason": candidate.reason,
    }


def _security_candidates(rows: list[dict[str, str]]) -> list[Candidate]:
    candidates: list[Candidate] = []
    severity_score = {"critical": 100, "high": 80, "medium": 45, "low": 15}
    for row in rows:
        severity = _normalize(row.get("severity"))
        status = _normalize(row.get("status"))
        if status in {"closed", "resolved", "ignored", "accepted_risk"}:
            continue
        if severity not in {"critical", "high"}:
            continue
        target = row.get("id") or row.get("package") or row.get("summary", "")
        candidates.append(
            Candidate(
                action_type="review_security",
                target=target,
                title=f"Review {severity} security item {target}",
                reason="Open high-severity security work should be reviewed before routine maintenance.",
                priority=10,
                score=severity_score[severity],
                confidence="high",
                source="security",
                next_steps=[
                    "Confirm whether the advisory or dependency item still applies.",
                    "Identify the smallest safe fix, mitigation, or disclosure note.",
                    "Avoid publishing sensitive exploit details in generated prompts.",
                ],
                evidence=dict(row),
                blocked_by=[],
            )
        )
    return candidates


def _ci_candidates(rows: list[dict[str, str]]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for row in rows:
        branch = _normalize(row.get("branch"))
        conclusion = _normalize(row.get("conclusion"))
        status = _normalize(row.get("status"))
        if branch not in {"main", "master"}:
            continue
        if status not in {"completed", "failure", "failed"} and conclusion not in {"failure", "failed", "timed_out", "cancelled"}:
            continue
        if conclusion in {"success", "neutral", "skipped"}:
            continue
        target = row.get("name") or row.get("id") or row.get("commit_sha", "")
        candidates.append(
            Candidate(
                action_type="fix_ci_failure",
                target=target,
                title=f"Fix failing main-branch CI: {target}",
                reason="Main-branch CI failures block releases and lower contributor confidence.",
                priority=20,
                score=70,
                confidence="high",
                source="ci_runs",
                next_steps=[
                    "Open the latest failing workflow log or exported failure note.",
                    "Reproduce the smallest failing command locally.",
                    "Patch the issue and rerun the relevant local tests before pushing.",
                ],
                evidence=dict(row),
                blocked_by=[],
            )
        )
    return candidates


def _pull_request_candidates(rows: list[dict[str, str]]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for row in rows:
        state = _normalize(row.get("state"))
        if state != "open" or parse_bool(row.get("is_draft")):
            continue
        review_status = _normalize(row.get("review_status"))
        checks_status = _normalize(row.get("checks_status"))
        if review_status in {"approved", "merged", "closed"}:
            continue
        blocked_by: list[str] = []
        priority = 30
        score = 50
        if checks_status in {"failure", "failed", "cancelled", "timed_out"}:
            blocked_by.append("PR checks are failing; review should start with the failure.")
            priority = 35
            score = 30
        target = row.get("id") or row.get("title", "")
        candidates.append(
            Candidate(
                action_type="review_pr",
                target=target,
                title=f"Review pull request {target}",
                reason="Open non-draft pull requests should get maintainer attention before new backlog work.",
                priority=priority,
                score=score + parse_int(row.get("comments"), 0),
                confidence="medium",
                source="pull_requests",
                next_steps=[
                    "Read the PR summary and changed files.",
                    "Check whether tests or CI evidence support the change.",
                    "Leave a clear review: approve, request changes, or ask a specific question.",
                ],
                evidence=dict(row),
                blocked_by=blocked_by,
            )
        )
    return candidates


def _issue_candidates(rows: list[dict[str, str]]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for row in rows:
        if _normalize(row.get("state")) != "open":
            continue
        labels = _labels(row.get("labels", ""))
        body_signal = _normalize(row.get("body_signal"))
        if "bug" not in labels and "reproducible" not in labels and body_signal not in {"repro", "reproduction", "minimal_repro"}:
            continue
        target = row.get("id") or row.get("title", "")
        score = 35 + parse_int(row.get("comments"), 0)
        candidates.append(
            Candidate(
                action_type="triage_issue",
                target=target,
                title=f"Triage reproducible issue {target}",
                reason="Reproducible bug reports are actionable maintainer work.",
                priority=40,
                score=score,
                confidence="medium",
                source="issues",
                next_steps=[
                    "Confirm the reproduction steps and expected behavior.",
                    "Label the issue with the smallest affected area.",
                    "Decide whether to fix, ask for missing information, or close with rationale.",
                ],
                evidence=dict(row),
                blocked_by=[],
            )
        )
    return candidates


def _release_candidates(rows: list[dict[str, str]]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for check in build_release_checks_from_rows(rows):
        if check.ready or check.status in {"shipped", "published", "released"}:
            continue
        candidates.append(
            Candidate(
                action_type="prepare_release",
                target=check.version,
                title=f"Close release-readiness gaps for {check.version}",
                reason="A planned release has missing notes, assets, or changelog evidence.",
                priority=50,
                score=20 + len(check.gaps) * 10,
                confidence="medium",
                source="releases",
                next_steps=[
                    "Update release notes from merged changes only.",
                    "Confirm release artifacts are present or intentionally not needed.",
                    "Verify the changelog before publishing the release.",
                ],
                evidence={"version": check.version, "status": check.status, "gaps": check.gaps},
                blocked_by=[],
            )
        )
    return candidates


def build_release_checks_from_rows(rows: list[dict[str, str]]) -> list[ReleaseCheck]:
    checks: list[ReleaseCheck] = []
    for row in rows:
        gaps: list[str] = []
        if not parse_bool(row.get("notes_ready")):
            gaps.append("release notes are not ready")
        if not parse_bool(row.get("assets_ready")):
            gaps.append("release assets are not ready")
        if not parse_bool(row.get("changelog_ready")):
            gaps.append("changelog is not ready")
        checks.append(
            ReleaseCheck(
                version=row.get("version", ""),
                status=_normalize(row.get("status")),
                ready=not gaps,
                gaps=gaps,
            )
        )
    return checks


def _normalize(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def _labels(value: str) -> set[str]:
    return {_normalize(label) for label in value.replace(";", ",").split(",") if label.strip()}


def _first_existing(primary: Path, fallback: Path) -> Path:
    return primary if primary.exists() else fallback
