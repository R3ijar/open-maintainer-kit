# Data Schemas

Open Maintainer Kit uses plain CSV files so maintainers can inspect and version their workflow.

## Issues

Default path: `data/issues.csv`

```text
id,title,state,labels,created_at,updated_at,comments,body_signal
```

Use `body_signal` for non-private summary labels such as `repro`, `missing_info`, or `minimal_repro`.

## Pull Requests

Default path: `data/pull_requests.csv`

```text
id,title,state,is_draft,checks_status,review_status,updated_at,author_association
```

Useful values:

- `checks_status`: `success`, `failure`, `pending`
- `review_status`: `none`, `changes_requested`, `approved`

## CI Runs

Default path: `data/ci_runs.csv`

```text
id,name,status,conclusion,branch,commit_sha,created_at,url
```

Main-branch failures are treated as high-priority maintainer work.

## Releases

Default path: `data/releases.csv`

```text
version,date,status,notes_ready,assets_ready,changelog_ready
```

`release-check` reports gaps before a release is published.

## Security

Default path: `data/security.csv`

```text
id,severity,status,package,summary,created_at
```

Use public or sanitized summaries only. Do not place exploit payloads, private reports, secrets, or non-public user data in this file.
