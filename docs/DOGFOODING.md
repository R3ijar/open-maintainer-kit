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
