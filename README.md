# Open Maintainer Kit

[![CI](https://github.com/R3ijar/open-maintainer-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/R3ijar/open-maintainer-kit/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](pyproject.toml)

Local-first CLI for open-source maintainers who want one conservative repo-maintenance action at a time.

Open Maintainer Kit turns local issue, pull request, CI, release, and security CSVs into a ranked triage queue, one daily maintainer plan, release-readiness checks, and a Codex-ready prompt.

```text
local repo exports -> triage queue -> one maintainer plan -> focused prompt
```

It is designed to complement [Open Growth Loop](https://github.com/R3ijar/open-growth-loop): Open Growth Loop helps decide which docs/content growth action to take next; Open Maintainer Kit helps decide which repository health task to handle next.

## Why Maintainers Use It

| Maintainer problem | What Open Maintainer Kit does |
| --- | --- |
| Issues, PRs, CI runs, and release notes compete for attention. | Ranks the strongest maintainer candidates in one queue. |
| Security or broken CI can be buried under routine backlog work. | Prioritizes high-risk security items and main-branch CI failures first. |
| PRs wait without a clear review decision. | Surfaces open non-draft PRs that need maintainer review. |
| Release readiness lives in memory or chat. | Checks release notes, assets, and changelog readiness from a local CSV. |
| Coding assistants need narrow, evidence-backed tasks. | Writes a focused prompt from the selected maintainer plan. |

## 60-Second Quickstart

From a local checkout on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m open_maintainer_kit --workspace . validate
python -m open_maintainer_kit --workspace . triage
python -m open_maintainer_kit --workspace . plan
python -m open_maintainer_kit --workspace . prompt
```

On macOS/Linux, activate the environment with `. .venv/bin/activate` before running the install and CLI commands.

Example plan:

```json
{
  "action_type": "fix_ci_failure",
  "target": "python-tests",
  "confidence": "high",
  "reason": "Main-branch CI failures block releases and lower contributor confidence."
}
```

## Commands

- `omk init` creates local `data/` files with the expected headers.
- `omk validate` checks CSV inputs and rejects private-looking columns.
- `omk triage` writes ranked maintainer candidates.
- `omk release-check` writes release-readiness checks.
- `omk plan` chooses one conservative maintainer action.
- `omk prompt` writes a Codex-ready prompt for the selected action.
- `omk privacy-scan` scans local text files for private-data leakage risks.

## Inputs And Outputs

Open Maintainer Kit reads:

- `issues.csv`
- `pull_requests.csv`
- `ci_runs.csv`
- `releases.csv`
- `security.csv`

It writes reviewable Markdown/JSON files under `outbox/`:

- `outbox/triage/latest-triage.md`
- `outbox/release/latest-release-check.md`
- `outbox/plans/latest-plan.md`
- `outbox/prompts/latest-prompt.md`
- `outbox/privacy-scan.md`

It does not call the GitHub API, require credentials, mutate issues, post comments, publish releases, or upload repository data.

## Decision Rules

The planner prioritizes:

1. Open high or critical security items.
2. Failing main-branch CI runs.
3. Open non-draft pull requests needing review.
4. Reproducible bug reports.
5. Release-readiness gaps.
6. Waiting for stronger signal.

These rules are deliberately conservative. The tool should reduce maintainer thrash, not automate judgment away.

## Privacy Boundary

The CSV schemas use aggregate or public repository metadata only. Validation rejects private-looking columns such as email, user, session, IP, token, key, secret, customer, and address.

Open Maintainer Kit is safe to run locally on public exports or hand-maintained CSVs. Keep raw payloads, credentials, private vulnerability detail, and non-public user data out of the input files.

## Full Command Flow

Initialize data files:

```bash
omk init --workspace .
```

Validate inputs:

```bash
omk validate --workspace .
```

Write the triage queue:

```bash
omk triage --workspace .
```

Check release readiness:

```bash
omk release-check --workspace .
```

Choose one maintainer action:

```bash
omk plan --workspace .
```

Generate a focused prompt:

```bash
omk prompt --workspace .
```

Scan before sharing a workspace:

```bash
omk privacy-scan --workspace .
```

Run tests:

```bash
python -m unittest discover -s tests
```

## Project Status

This is an early public MVP. It is intended for small CSV-driven maintainer workflows and dogfooding on Open Growth Loop before expanding into optional issue export or GitHub integration.

## License

Apache-2.0.
