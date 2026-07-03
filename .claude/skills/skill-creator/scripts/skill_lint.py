"""skill_lint — the rubric engine behind skill-creator's eval/benchmark mode.

Parses a Claude Code ``SKILL.md`` file and scores it against a rubric that
covers two things that actually matter for a skill:

1. **Structural validity** (error-severity): will the harness be able to load
   this skill at all? Missing frontmatter, a missing/malformed ``name`` or
   ``description``, or a ``name`` that does not match its directory all break
   loading.
2. **Auto-activation & authoring quality** (warn/info): the ``description`` is
   the *only* text the model sees when deciding whether to fire a skill, so the
   rubric rewards descriptions that name concrete trigger conditions and
   penalises vague or placeholder-laden ones.

The module is intentionally **stdlib-only** so it can run inside a git hook on
any machine without an install step. It is imported by ``validate_skill.py``,
``benchmark.py``, ``new_skill.py`` and ``test_validate.py``.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field, asdict
from typing import Optional

# ---------------------------------------------------------------------------
# Tunable thresholds (kept as module constants so tests and docs can cite them)
# ---------------------------------------------------------------------------
DESC_HARD_MAX = 1024      # Claude Code hard-caps the description at 1024 chars.
DESC_SOFT_MAX = 500       # Above this it gets unwieldy; warn, don't fail.
DESC_MIN = 40             # Below this it can't carry real trigger conditions.
NAME_MAX = 64             # Directory / name length ceiling.
BODY_LONG_LINES = 400     # Past this, suggest progressive disclosure.
DEFAULT_MIN_SCORE = 80    # A skill "passes" the benchmark at or above this.

KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HEADING_RE = re.compile(r"^#{1,6}\s+\S", re.M)

# An activation cue: the phrasings that make a description reliably fire.
# The "for <gerund>" arm is a curated verb list rather than a bare `for \w+ing`
# so it does not fire on incidental words like "for anything" or "for string
# parsing" (which would inflate the highest-weighted quality check).
TRIGGER_RE = re.compile(
    r"\buse (?:this|it)?\s*(?:skill\s+)?(?:when|to|for)\b"
    r"|\bwhen (?:the user|you|working|running|building|creating|writing|"
    r"editing|configuring|debugging|reviewing|generating|setting up|asked)\b"
    r"|\bwhenever\b"
    r"|\bfor (?:creating|building|writing|generating|configuring|scaffolding|"
    r"validating|formatting|managing|running|testing|deploying|migrating|"
    r"refactoring|converting|parsing|editing|updating|checking|handling|"
    r"processing|summarizing|extracting|searching|reviewing|analyzing|"
    r"debugging|setting up|working with)\b",
    re.I,
)
FIRST_PERSON_RE = re.compile(r"^\s*(?:i |i'|you |your )", re.I)
# Scaffold leftovers. TODO/FIXME/XXX are matched case-SENSITIVE (uppercase) so
# ordinary prose ("the todo list") is not flagged; only literal scaffold markers
# are. {{…}} and the ALL-CAPS <PLACEHOLDER> form (below) round it out.
PLACEHOLDER_RE = re.compile(
    r"\{\{.*?\}\}|\bTODO\b|\bFIXME\b|\bXXX\b|REPLACE_ME|your-skill-name")
# Angle-bracket placeholders must be ALL-CAPS (e.g. <PLACEHOLDER>, <YOUR NAME>)
# so ordinary lowercase path/command templates like `<name>` or `<branch>` in
# documentation are not falsely flagged. Case-sensitive on purpose.
ANGLE_PLACEHOLDER_RE = re.compile(r"<[A-Z][A-Z_ ]{2,}>")
WORKFLOW_RE = re.compile(
    r"^#{1,6}\s+.*\b(workflow|steps?|usage|how to use|instructions|process)\b",
    re.I | re.M,
)
GENERIC_NAMES = {"skill", "my-skill", "new-skill", "example", "test", "untitled", "sample"}

SEVERITIES = ("error", "warn", "info")

# Fenced code blocks (``` … ``` or ~~~ … ~~~). Stripped before the heading /
# workflow checks so a `# comment` inside a shell block is not mistaken for a
# Markdown heading. Non-greedy + DOTALL spans from the opening fence to the next
# matching fence line.
_FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,}).*?^[ \t]*\1[^\n]*$\n?", re.S | re.M)


def strip_code_fences(text: str) -> str:
    return _FENCE_RE.sub("", text)


@dataclass
class Check:
    id: str
    severity: str
    passed: bool
    weight: float
    message: str

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Result:
    path: str
    skill: Optional[str]
    score: int
    passed: bool
    counts: dict
    checks: list = field(default_factory=list)

    def as_dict(self) -> dict:
        d = asdict(self)
        d["checks"] = [c for c in d["checks"]]
        return d

    def failures(self, severity: Optional[str] = None) -> list:
        return [
            c
            for c in self.checks
            if not c["passed"] and (severity is None or c["severity"] == severity)
        ]


# ---------------------------------------------------------------------------
# Frontmatter parsing (minimal, forgiving, dependency-free)
# ---------------------------------------------------------------------------
def split_frontmatter(text: str):
    """Return ``(frontmatter_block, body)`` or ``(None, text)`` if absent.

    Accepts ``\r\n``/``\r`` line endings and a trailing-whitespace fence.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.startswith("---"):
        return None, text
    m = re.match(r"^---[ \t]*\n(.*?)\n---[ \t]*(?:\n|$)", text, re.S)
    if not m:
        return None, text
    return m.group(1), text[m.end():]


def parse_frontmatter(block: str) -> dict:
    """Parse simple ``key: value`` YAML frontmatter without a YAML dependency.

    Handles surrounding quotes and skips whole-line ``#`` comments. Trailing
    inline comments are intentionally NOT stripped — ``#`` appears legitimately
    in descriptions (``Refs: #123``, ``C# tips``), so removing it would corrupt
    the value. Multi-line/folded scalars are out of scope (skills use
    single-line name/description) and are reported by the rubric as missing.
    """
    data: dict = {}
    for line in block.split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if len(val) >= 2 and val[0] in "\"'" and val[-1] == val[0]:
            val = val[1:-1]
        data[key] = val
    return data


# ---------------------------------------------------------------------------
# The rubric
# ---------------------------------------------------------------------------
def lint_text(text: str, path: str = "<memory>", expected_name: Optional[str] = None,
              check_dir: bool = True, min_score: int = DEFAULT_MIN_SCORE) -> Result:
    """Run the full rubric over the raw text of a SKILL.md and score it."""
    checks: list[Check] = []

    def add(cid, severity, passed, weight, message):
        checks.append(Check(cid, severity, bool(passed), weight, message))

    block, body = split_frontmatter(text)
    fm = parse_frontmatter(block) if block is not None else {}
    name = (fm.get("name") or "").strip()
    desc = (fm.get("description") or "").strip()

    # Which directory name should `name` equal? Only derive one when the path
    # actually carries a directory component — otherwise an in-memory/sentinel
    # path ("<memory>") would spuriously compare against the current directory.
    if expected_name is None and check_dir and os.path.dirname(path):
        expected_name = os.path.basename(os.path.dirname(os.path.abspath(path)))

    # ---- structural (error severity) ------------------------------------
    add("frontmatter_present", "error", block is not None, 5,
        "SKILL.md must open with a `---` YAML frontmatter block.")
    add("name_present", "error", bool(name), 5,
        "Frontmatter must define a non-empty `name`.")
    add("description_present", "error", bool(desc), 5,
        "Frontmatter must define a non-empty `description` (the model's only "
        "activation signal).")
    add("name_kebab_case", "error", bool(name) and bool(KEBAB_RE.match(name)), 3,
        "`name` must be kebab-case: lowercase letters, digits and single hyphens.")
    add("name_length_ok", "error", bool(name) and len(name) <= NAME_MAX, 2,
        f"`name` must be at most {NAME_MAX} characters.")
    if check_dir and expected_name:
        add("name_matches_dir", "error", name == expected_name, 3,
            f"`name` ({name!r}) must equal the skill directory name "
            f"({expected_name!r}).")
    # Cap checks only fire when a description exists; emptiness is owned by
    # `description_present`, so these don't pile a bogus "too long" message on a
    # missing description.
    add("description_within_hard_cap", "error",
        (not desc) or len(desc) <= DESC_HARD_MAX, 3,
        f"`description` must be at most {DESC_HARD_MAX} characters "
        "(Claude Code hard limit).")
    add("has_body", "error", bool(body.strip()), 3,
        "SKILL.md must have instructional body content after the frontmatter.")

    # ---- quality (warn severity) ----------------------------------------
    add("description_min_length", "warn", bool(desc) and len(desc) >= DESC_MIN, 2,
        f"`description` should be at least {DESC_MIN} chars so it can state when "
        "to use the skill.")
    add("description_soft_cap", "warn", (not desc) or len(desc) <= DESC_SOFT_MAX, 1,
        f"`description` is long (>{DESC_SOFT_MAX} chars); tighten it or move "
        "detail into the body.")
    add("description_has_trigger", "warn",
        bool(desc) and bool(TRIGGER_RE.search(desc)), 3,
        "`description` should name a trigger condition (e.g. \"Use when…\", "
        "\"when the user…\") so the skill auto-activates.")
    add("description_third_person", "warn",
        (not desc) or not FIRST_PERSON_RE.match(desc), 1,
        "`description` reads better in third person describing the situation, "
        "not \"I\"/\"You\".")
    add("name_not_generic", "warn", bool(name) and name not in GENERIC_NAMES, 1,
        "`name` is generic; pick something specific to what the skill does.")
    body_no_code = strip_code_fences(body)
    add("body_has_heading", "warn", bool(HEADING_RE.search(body_no_code)), 2,
        "Body should use Markdown headings to structure the instructions.")
    add("no_placeholders", "warn",
        not (PLACEHOLDER_RE.search(text) or ANGLE_PLACEHOLDER_RE.search(text)), 2,
        "Remove scaffold placeholders (TODO, {{…}}, <PLACEHOLDER>, …) before "
        "shipping the skill.")

    # ---- advisory (info severity) ---------------------------------------
    body_lines = body.count("\n") + 1 if body.strip() else 0
    add("body_progressive_disclosure", "info", body_lines <= BODY_LONG_LINES, 1,
        f"SKILL.md body is long ({body_lines} lines); consider moving detail "
        "into references/ for progressive disclosure.")
    add("has_workflow_section", "info", bool(WORKFLOW_RE.search(body_no_code)), 1,
        "Consider a Workflow/Usage/Steps section so the model has an explicit "
        "procedure to follow.")

    total_w = sum(c.weight for c in checks)
    got_w = sum(c.weight for c in checks if c.passed)
    score = int(round(100 * got_w / total_w)) if total_w else 0

    counts = {sev: sum(1 for c in checks if c.severity == sev and not c.passed)
              for sev in SEVERITIES}
    passed = counts["error"] == 0 and score >= min_score

    return Result(
        path=path,
        skill=name or None,
        score=score,
        passed=passed,
        counts=counts,
        checks=[c.as_dict() for c in checks],
    )


def lint_file(path: str, expected_name: Optional[str] = None,
              check_dir: bool = True, min_score: int = DEFAULT_MIN_SCORE) -> Result:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    return lint_text(text, path=path, expected_name=expected_name,
                     check_dir=check_dir, min_score=min_score)
