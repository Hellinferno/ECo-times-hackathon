# Shared Gold Datasets

Each `gold.jsonl` row should include:

- `id`
- `task`
- `input`
- `context`
- `expected_output`
- `allowed_evidence`
- `reviewer_verdict`
- `failure_tags`

Use human-reviewed traces as the source of truth. Synthetic examples can extend coverage, but they should not replace reviewed examples for release gates.
