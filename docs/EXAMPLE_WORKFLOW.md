# Example Workflow

This walkthrough uses the sample CSVs in `data/`.

## 1. Validate

```bash
python -m open_maintainer_kit --workspace . validate
```

Expected shape:

```json
{
  "ok": true,
  "errors": []
}
```

## 2. Build The Triage Queue

```bash
python -m open_maintainer_kit --workspace . triage
```

The sample data includes a failing main-branch CI run, an open PR, a reproducible issue, and one planned release gap.

## 3. Choose One Plan

```bash
python -m open_maintainer_kit --workspace . plan
```

With the bundled sample data, the planner chooses the main-branch CI failure first:

```json
{
  "action_type": "fix_ci_failure",
  "target": "python-tests"
}
```

## 4. Generate A Prompt

```bash
python -m open_maintainer_kit --workspace . prompt
```

This writes `outbox/prompts/latest-prompt.md`, which can be handed to Codex for one focused repo-maintenance task.

## 5. Check Release Readiness

```bash
python -m open_maintainer_kit --workspace . release-check
```

The sample `0.1.1` release is not ready because release assets are missing.

## What This Avoids

Open Maintainer Kit avoids:

- sending repository data to a hosted service
- needing GitHub credentials for the core workflow
- letting routine backlog work hide security or CI blockers
- asking a coding assistant to solve vague maintenance goals
