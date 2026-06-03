# Contributing

Thanks for considering a contribution.

Open Maintainer Kit is early. The most useful contributions are:

- bug reports with small reproducible examples
- sample CSV shapes from public repository workflows
- conservative triage-rule improvements
- documentation fixes
- tests for edge cases

## Development

```bash
python -m venv .venv
.\.venv\Scripts\python -m pip install -e .
python -m unittest discover -s tests
```

On macOS/Linux, activate with `. .venv/bin/activate`.

## Privacy

Do not include secrets, private payloads, private vulnerability details, raw user data, or non-public repository exports in issues, tests, examples, or pull requests.
