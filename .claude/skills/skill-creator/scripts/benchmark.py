#!/usr/bin/env python3
"""benchmark — skill-creator's eval/benchmark mode.

Discovers every ``*/SKILL.md`` under a skills root, scores each against the
rubric, and reports an aggregate: mean score, pass rate, and the weakest skill.
This is how you *measure* the tooling after building or changing a skill.

    benchmark.py [--root .claude/skills] [--out evals/report.json]
                 [--min-score 80] [--json] [--fail-under N]

Exit code is 0 when every discovered skill passes (and, if given, the mean is at
or above ``--fail-under``), 1 otherwise — so it can gate CI too.

The JSON report is written with sorted keys and no timestamp so re-running on an
unchanged tree yields a byte-identical file (clean diffs, reviewable in git).
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skill_lint import lint_file, DEFAULT_MIN_SCORE  # noqa: E402

REPORT_SCHEMA_VERSION = 1


def discover(root: str) -> list:
    hits = glob.glob(os.path.join(root, "*", "SKILL.md"))
    # A skill can also nest one level deeper (namespaced); include those too.
    hits += glob.glob(os.path.join(root, "*", "*", "SKILL.md"))
    return sorted(set(os.path.normpath(p) for p in hits))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Benchmark every skill under a root.")
    ap.add_argument("--root", default=".claude/skills")
    ap.add_argument("--out", default=None, help="write JSON report to this path")
    ap.add_argument("--min-score", type=int, default=DEFAULT_MIN_SCORE)
    ap.add_argument("--fail-under", type=int, default=None,
                    help="also fail if the mean score is below this")
    ap.add_argument("--json", action="store_true", help="print JSON to stdout")
    args = ap.parse_args(argv)

    paths = discover(args.root)
    if not paths:
        print(f"No SKILL.md found under {args.root!r}", file=sys.stderr)
        return 1

    rows = []
    for p in paths:
        r = lint_file(p, min_score=args.min_score)
        rows.append(r)

    rows.sort(key=lambda r: (r.passed, r.score, r.skill or ""))
    scores = [r.score for r in rows]
    mean = round(sum(scores) / len(scores), 1)
    n_pass = sum(1 for r in rows if r.passed)

    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "root": args.root,
        "min_score": args.min_score,
        "summary": {
            "skills": len(rows),
            "passing": n_pass,
            "failing": len(rows) - n_pass,
            "mean_score": mean,
            "min_score_seen": min(scores),
            "max_score_seen": max(scores),
        },
        "skills": [
            {
                "skill": r.skill,
                "path": r.path,
                "score": r.score,
                "passed": r.passed,
                "errors": r.counts["error"],
                "warnings": r.counts["warn"],
                "infos": r.counts["info"],
            }
            for r in rows
        ],
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"skill-creator benchmark — {len(rows)} skill(s) under {args.root}\n")
        print(f"  {'SKILL':<24} {'SCORE':>5}  {'E':>2} {'W':>2} {'I':>2}  RESULT")
        print(f"  {'-'*24} {'-'*5}  {'-'*2} {'-'*2} {'-'*2}  {'-'*6}")
        for r in rows:
            print(f"  {(r.skill or '(no name)'):<24} {r.score:>5}  "
                  f"{r.counts['error']:>2} {r.counts['warn']:>2} "
                  f"{r.counts['info']:>2}  {'PASS' if r.passed else 'FAIL'}")
        s = report["summary"]
        print(f"\n  mean {s['mean_score']}  ·  {s['passing']}/{s['skills']} passing"
              f"  ·  range {s['min_score_seen']}–{s['max_score_seen']}")

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, sort_keys=True)
            fh.write("\n")
        if not args.json:
            print(f"\n  report → {args.out}")

    ok = n_pass == len(rows)
    if args.fail_under is not None:
        ok = ok and mean >= args.fail_under
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
