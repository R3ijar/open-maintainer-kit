# Dogfooding Plan

Open Maintainer Kit should be dogfooded on Open Growth Loop before larger releases.

## First Dogfood Target

Repository:

```text
https://github.com/R3ijar/open-growth-loop
```

## Local Export Plan

For v0.1, use manual or exported CSVs:

- issues
- pull requests
- CI runs
- planned releases
- public or sanitized security notes

## Success Criteria

- `omk validate` passes on the Open Growth Loop workspace.
- `omk triage` produces a useful queue.
- `omk plan` selects a sensible repo-health action.
- `omk prompt` produces a task that can be used by Codex without exposing private data.
- Any confusing rule becomes a small issue or patch in Open Maintainer Kit.

## 2026-06-02 Snapshot

The first dogfood snapshot lives at `examples/open-growth-loop-current`.

Public Open Growth Loop state at capture time:

- open issues: 0
- open pull requests: 0
- latest main CI run: success
- GitHub releases: 0

Expected OMK result: `wait_for_signal`.

This is a valid result. A maintainer tool should not invent urgent work when public repo-health signals are clean.
