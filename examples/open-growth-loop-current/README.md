# Open Growth Loop Dogfood Snapshot

This example is a public metadata snapshot from `R3ijar/open-growth-loop`, captured with `omk import-github` on 2026-06-03.

Observed public state:

- open issues: 0
- open pull requests: 0
- imported CI runs: 21
- latest main CI run: success
- GitHub releases: 0

Expected result:

```json
{
  "action_type": "wait_for_signal"
}
```

That is intentional. Open Maintainer Kit should not invent maintenance work when the strongest public repo-health signals are clean.

Run it:

```bash
python -m open_maintainer_kit --workspace examples/open-growth-loop-current import-github R3ijar/open-growth-loop
python -m open_maintainer_kit --workspace examples/open-growth-loop-current validate
python -m open_maintainer_kit --workspace examples/open-growth-loop-current triage
python -m open_maintainer_kit --workspace examples/open-growth-loop-current plan
```
