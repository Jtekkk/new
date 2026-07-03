#!/usr/bin/env python3
"""PostToolUse hook entry — auto-validate a written SKILL.md.

Reads the hook JSON from stdin. If the edited file is a `SKILL.md` (and not a
test fixture), it runs the rubric and:

- **error-severity failures** → prints them to stderr and exits 2, which is the
  blocking code for a PostToolUse hook: stderr is fed back to Claude so the
  broken skill gets fixed in the same turn.
- **warnings / sub-threshold score, no errors** → prints advice to stdout and
  exits 0 (non-blocking). The loop nudges without nagging.
- **anything it can't handle** (bad JSON, missing file, non-SKILL.md) → exits 0
  silently, so the hook can never get in the way of ordinary editing.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skill_lint import lint_file  # noqa: E402


def read_payload() -> dict:
    try:
        data = json.load(sys.stdin)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def target_path(data: dict):
    """Return the path to validate, or None if this write should be ignored.

    Ignored when: the payload is malformed, the file is not literally named
    ``SKILL.md`` (so ``docs/WRITING-A-SKILL.md`` and friends are untouched), or
    the file lives under a ``tests/fixtures`` tree (intentionally-broken
    examples). Everything here is defensive so the hook never trips on an
    unexpected payload shape.
    """
    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    fp = tool_input.get("file_path") or tool_input.get("filePath")
    if not isinstance(fp, str) or not fp:
        return None
    norm = fp.replace("\\", "/")
    if os.path.basename(norm) != "SKILL.md":
        return None
    if "/tests/fixtures/" in norm:
        return None
    if not os.path.isfile(fp):
        return None
    return fp


def failing_lines(result) -> list:
    out = []
    for c in result.checks:
        if not c["passed"]:
            out.append(f"  [{c['severity']}] {c['id']}: {c['message']}")
    return out


def main() -> int:
    fp = target_path(read_payload())
    if fp is None:
        return 0

    result = lint_file(fp)
    if result.passed:
        return 0

    errors = [c for c in result.checks if not c["passed"] and c["severity"] == "error"]
    header = (f"skill-creator: {fp} scored {result.score}/100 and did not pass "
              f"its rubric.")
    body = "\n".join(failing_lines(result))

    if errors:
        print(header, file=sys.stderr)
        print(body, file=sys.stderr)
        print("Fix the error-severity items above so the skill loads correctly.",
              file=sys.stderr)
        return 2   # blocking: fed back to Claude

    # No errors — only warnings or a sub-threshold score. Advise, don't block.
    print(header)
    print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
