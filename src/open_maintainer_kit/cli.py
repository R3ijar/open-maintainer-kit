from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .engine import (
    MaintainerPlan,
    build_candidates,
    build_plan,
    build_release_checks,
    default_data_paths,
    render_candidates_markdown,
    render_plan_markdown,
    render_release_checks_markdown,
    write_plan_reports,
)
from .github_import import import_github_repo
from .io_utils import read_json, write_json_report, write_text_report
from .privacy import render_privacy_scan_markdown, scan_privacy
from .prompts import render_codex_prompt
from .workspace import init_workspace, validate_workspace


def main() -> None:
    parser = argparse.ArgumentParser(description="Open Maintainer Kit CLI.")
    parser.add_argument("--workspace", dest="global_workspace", default="", help="Repository workspace containing data/ and outbox/.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="Show current data file status.")
    add_workspace_argument(status)

    init = subparsers.add_parser("init", help="Create local data CSV files with expected headers.")
    add_workspace_argument(init)
    init.add_argument("--overwrite", action="store_true", help="Rewrite existing data CSV files.")

    validate = subparsers.add_parser("validate", help="Validate local CSV inputs and privacy-safe headers.")
    add_workspace_argument(validate)

    import_github = subparsers.add_parser("import-github", help="Import public GitHub repo signals into local CSVs using gh.")
    add_workspace_argument(import_github)
    import_github.add_argument("repo", help="GitHub repository in owner/name form.")
    import_github.add_argument("--limit", type=int, default=100, help="Maximum records to import per GitHub signal.")

    triage = subparsers.add_parser("triage", help="Write ranked maintainer triage candidates.")
    add_workspace_argument(triage)

    release_check = subparsers.add_parser("release-check", help="Write release-readiness checks.")
    add_workspace_argument(release_check)

    plan = subparsers.add_parser("plan", help="Choose one conservative maintainer action.")
    add_workspace_argument(plan)

    prompt = subparsers.add_parser("prompt", help="Write a Codex-ready prompt from the latest plan.")
    add_workspace_argument(prompt)
    prompt.add_argument("--plan-json", default="", help="Plan JSON. Defaults to outbox/plans/latest-plan.json.")

    privacy = subparsers.add_parser("privacy-scan", help="Scan local files for private-data leakage risks.")
    add_workspace_argument(privacy)

    args = parser.parse_args()
    workspace = Path(args.workspace or args.global_workspace or ".").resolve()

    if args.command == "status":
        run_status(workspace)
    elif args.command == "init":
        run_init(args, workspace)
    elif args.command == "validate":
        run_validate(workspace)
    elif args.command == "import-github":
        run_import_github(args, workspace)
    elif args.command == "triage":
        run_triage(workspace)
    elif args.command == "release-check":
        run_release_check(workspace)
    elif args.command == "plan":
        run_plan(workspace)
    elif args.command == "prompt":
        run_prompt(args, workspace)
    elif args.command == "privacy-scan":
        run_privacy_scan(workspace)


def add_workspace_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", default="", help="Repository workspace containing data/ and outbox/.")


def run_status(workspace: Path) -> None:
    paths = default_data_paths(workspace)
    payload = {
        "workspace": str(workspace),
        "data": {key: str(path) for key, path in paths.items()},
        "latest_plan": str(workspace / "outbox" / "plans" / "latest-plan.json"),
    }
    print(json.dumps(payload, indent=2))


def run_init(args: argparse.Namespace, workspace: Path) -> None:
    result = init_workspace(workspace, overwrite=args.overwrite)
    print(json.dumps(asdict(result), indent=2))


def run_validate(workspace: Path) -> None:
    result = validate_workspace(workspace)
    print(json.dumps(asdict(result), indent=2))
    if not result.ok:
        raise SystemExit(1)


def run_import_github(args: argparse.Namespace, workspace: Path) -> None:
    result = import_github_repo(args.repo, workspace, limit=args.limit)
    print(json.dumps(asdict(result), indent=2))


def run_triage(workspace: Path) -> None:
    candidates = build_candidates(default_data_paths(workspace))
    md_path = write_text_report(workspace / "outbox" / "triage" / "latest-triage.md", render_candidates_markdown(candidates))
    json_path = write_json_report(workspace / "outbox" / "triage" / "latest-triage.json", [asdict(candidate) for candidate in candidates])
    print(json.dumps({"candidates": len(candidates), "markdown": str(md_path), "json": str(json_path)}, indent=2))


def run_release_check(workspace: Path) -> None:
    paths = default_data_paths(workspace)
    checks = build_release_checks(paths["releases"])
    md_path = write_text_report(workspace / "outbox" / "release" / "latest-release-check.md", render_release_checks_markdown(checks))
    json_path = write_json_report(workspace / "outbox" / "release" / "latest-release-check.json", [asdict(check) for check in checks])
    print(json.dumps({"checks": len(checks), "markdown": str(md_path), "json": str(json_path)}, indent=2))


def run_plan(workspace: Path) -> None:
    plan = build_plan(default_data_paths(workspace))
    md_path, json_path = write_plan_reports(plan, workspace / "outbox" / "plans")
    print(json.dumps({"plan": asdict(plan), "markdown": str(md_path), "json": str(json_path)}, indent=2))


def run_prompt(args: argparse.Namespace, workspace: Path) -> None:
    plan_json = Path(args.plan_json) if args.plan_json else workspace / "outbox" / "plans" / "latest-plan.json"
    payload = read_json(plan_json)
    plan = MaintainerPlan(**payload)
    prompt = render_codex_prompt(plan)
    prompt_path = write_text_report(workspace / "outbox" / "prompts" / "latest-prompt.md", prompt)
    print(json.dumps({"prompt": str(prompt_path)}, indent=2))


def run_privacy_scan(workspace: Path) -> None:
    result = scan_privacy(workspace)
    md_path = write_text_report(workspace / "outbox" / "privacy-scan.md", render_privacy_scan_markdown(result))
    json_path = write_json_report(workspace / "outbox" / "privacy-scan.json", asdict(result))
    print(
        json.dumps(
            {
                "ok": result.ok,
                "checked_files": result.checked_files,
                "findings": len(result.findings),
                "markdown": str(md_path),
                "json": str(json_path),
            },
            indent=2,
        )
    )
    if not result.ok:
        raise SystemExit(1)
