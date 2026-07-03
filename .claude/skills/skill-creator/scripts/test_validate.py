#!/usr/bin/env python3
"""test_validate — unit tests for the rubric engine (the eval's own eval).

Runs the validator over the fixtures in ../tests/fixtures and asserts each one's
pass/fail verdict and the specific checks it must flag. Pure stdlib; run with:

    python3 test_validate.py

Exit code 0 = all assertions hold, 1 = a regression in the rubric.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from skill_lint import lint_file, lint_text  # noqa: E402

FIXTURES = os.path.join(HERE, "..", "tests", "fixtures")

# Each case: fixture dir -> (should_pass, {check_id: expected_passed})
CASES = {
    "good-skill": (True, {
        "frontmatter_present": True,
        "name_matches_dir": True,
        "description_has_trigger": True,
        "no_placeholders": True,
    }),
    "missing-frontmatter": (False, {
        "frontmatter_present": False,
        "name_present": False,
        "description_present": False,
    }),
    "no-description": (False, {
        "name_present": True,
        "description_present": False,
    }),
    "name-mismatch": (False, {
        "name_present": True,
        "name_matches_dir": False,
    }),
    "vague-description": (True, {          # loads fine, but flagged
        "description_present": True,
        "description_min_length": False,
        "description_has_trigger": False,
    }),
}


def check_map(result):
    return {c["id"]: c["passed"] for c in result.checks}


def run() -> int:
    failures = []

    for fixture, (should_pass, expected) in CASES.items():
        path = os.path.join(FIXTURES, fixture, "SKILL.md")
        r = lint_file(path)
        cm = check_map(r)
        if r.passed != should_pass:
            failures.append(f"{fixture}: passed={r.passed}, expected {should_pass} "
                            f"(score {r.score})")
        for cid, want in expected.items():
            if cid not in cm:
                failures.append(f"{fixture}: check {cid!r} not emitted")
            elif cm[cid] != want:
                failures.append(f"{fixture}: check {cid} = {cm[cid]}, expected {want}")

    # Score-ordering invariant: good > vague > structurally broken.
    scores = {f: lint_file(os.path.join(FIXTURES, f, "SKILL.md")).score for f in CASES}
    if not (scores["good-skill"] > scores["vague-description"]
            > scores["missing-frontmatter"]):
        failures.append(f"score ordering violated: {scores}")

    # A perfect skill scores exactly 100.
    if scores["good-skill"] != 100:
        failures.append(f"good-skill should score 100, got {scores['good-skill']}")

    # Placeholder detection: ALL-CAPS <PLACEHOLDER> is flagged, but a lowercase
    # path/command template like `<name>` in prose is NOT (regression guard).
    base = ("---\nname: ph-test\ndescription: Use when the user needs a well "
            "formed skill for the placeholder regression check.\n---\n\n"
            "# Ph Test\n\n## Workflow\n\n1. Do the thing.\n")
    lowercase = lint_text(base + "\nSkills live at `.claude/skills/<name>/`.\n",
                          path="x/ph-test/SKILL.md")
    allcaps = lint_text(base + "\nReplace <PLACEHOLDER> before shipping.\n",
                        path="x/ph-test/SKILL.md")
    lc = {c["id"]: c["passed"] for c in lowercase.checks}
    ac = {c["id"]: c["passed"] for c in allcaps.checks}
    if not lc["no_placeholders"]:
        failures.append("no_placeholders false-positive on lowercase `<name>` template")
    if ac["no_placeholders"]:
        failures.append("no_placeholders missed an ALL-CAPS <PLACEHOLDER>")

    # CRLF line endings must parse identically to LF.
    with open(os.path.join(FIXTURES, "good-skill", "SKILL.md"), encoding="utf-8") as fh:
        lf = fh.read()
    crlf = lint_text(lf.replace("\n", "\r\n"),
                     path=os.path.join(FIXTURES, "good-skill", "SKILL.md"))
    if crlf.score != 100:
        failures.append(f"CRLF handling broken: score {crlf.score}")

    if failures:
        print("FAIL — rubric regressions:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print(f"ok — {len(CASES)} fixtures, scores: "
          + ", ".join(f"{k}={v}" for k, v in sorted(scores.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
