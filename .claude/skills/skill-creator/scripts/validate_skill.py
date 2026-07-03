#!/usr/bin/env python3
"""validate_skill — score one or more SKILL.md files against the rubric.

    validate_skill.py PATH [PATH ...] [options]

Options:
    --json              Emit machine-readable JSON instead of the text report.
    --expect-name NAME  Override the expected skill name (default: parent dir).
    --no-dir-check      Skip the "name matches directory" check.
    --min-score N       Score (0-100) required to pass (default: 80).
    --quiet             Only print skills that do not pass.

Exit code is 0 when every file passes, 1 otherwise — so it doubles as a CI gate
and as the command a PostToolUse hook runs on each SKILL.md write.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skill_lint import lint_file, DEFAULT_MIN_SCORE, SEVERITIES  # noqa: E402

MARK = {True: "✓", False: "✗"}          # ✓ / ✗
SEV_TAG = {"error": "ERROR", "warn": "warn", "info": "info"}


def render(result, quiet: bool) -> str:
    lines = []
    status = "PASS" if result.passed else "FAIL"
    head = f"{status}  score {result.score}/100  {result.skill or '(no name)'}  — {result.path}"
    lines.append(head)
    for c in result.checks:
        if c["passed"] and quiet:
            continue
        if c["passed"] and c["severity"] == "info":
            continue
        tag = SEV_TAG[c["severity"]]
        lines.append(f"  {MARK[c['passed']]} [{tag:<5}] {c['id']}")
        if not c["passed"]:
            lines.append(f"        ↳ {c['message']}")
    e, w, i = (result.counts[s] for s in SEVERITIES)
    lines.append(f"  → {e} error(s), {w} warning(s), {i} info")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Validate SKILL.md files against the skill-creator rubric.")
    ap.add_argument("paths", nargs="+", help="SKILL.md file(s) to validate")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--expect-name", default=None, help="expected skill name")
    ap.add_argument("--no-dir-check", action="store_true", help="skip name==dir check")
    ap.add_argument("--min-score", type=int, default=DEFAULT_MIN_SCORE)
    ap.add_argument("--quiet", action="store_true", help="only show non-passing checks")
    args = ap.parse_args(argv)

    results = []
    all_ok = True
    for path in args.paths:
        if not os.path.isfile(path):
            print(f"FAIL  missing file  — {path}", file=sys.stderr)
            all_ok = False
            continue
        r = lint_file(
            path,
            expected_name=args.expect_name,
            check_dir=not args.no_dir_check,
            min_score=args.min_score,
        )
        results.append(r)
        all_ok = all_ok and r.passed

    if args.json:
        print(json.dumps([r.as_dict() for r in results], indent=2))
    else:
        chunks = [render(r, args.quiet) for r in results
                  if not (args.quiet and r.passed)]
        print("\n\n".join(chunks) if chunks else "All skills pass.")

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
