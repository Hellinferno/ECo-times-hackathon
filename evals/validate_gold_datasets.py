from __future__ import annotations

import json
from pathlib import Path
import sys

REQUIRED_KEYS = {
    "id",
    "task",
    "input",
    "context",
    "expected_output",
    "allowed_evidence",
    "reviewer_verdict",
    "failure_tags",
}


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            payload = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{line_number}: invalid JSON ({exc})")
            continue
        missing = REQUIRED_KEYS.difference(payload.keys())
        if missing:
            errors.append(f"{path}:{line_number}: missing keys {sorted(missing)}")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1] / "datasets"
    files = sorted(root.glob("**/gold.jsonl"))
    errors: list[str] = []
    for path in files:
        errors.extend(validate_file(path))
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Validated {len(files)} gold dataset files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
