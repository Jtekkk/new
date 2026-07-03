# Skill authoring guide (skill-creator reference)

Depth behind `SKILL.md`. Read this when you need the exact rubric, the scoring
math, or the hook wiring.

## Anatomy of a skill

```
.claude/skills/<name>/
  SKILL.md            # required: frontmatter + Markdown body
  scripts/            # optional: runnable helpers the skill invokes
  references/         # optional: long-form detail (progressive disclosure)
  assets/             # optional: templates and static files
```

Frontmatter is minimal:

```yaml
---
name: <kebab-case, must equal the directory name, ≤ 64 chars>
description: <the only text the model sees when deciding to activate>
---
```

## The rubric

Each check has a severity and a weight. The score is a weighted percentage of
passed checks:

```
score = round(100 * sum(weight of passed checks) / sum(weight of all checks))
```

A skill **passes** when it has zero `error` failures **and** `score ≥ 80`
(configurable via `--min-score`). Note that a skill can score well and still
fail if it trips a single error (e.g. a name/directory mismatch) — errors gate,
the score grades.

| id | severity | weight | rule |
|----|----------|-------:|------|
| `frontmatter_present` | error | 5 | File opens with a `---` … `---` block. |
| `name_present` | error | 5 | Frontmatter has a non-empty `name`. |
| `description_present` | error | 5 | Frontmatter has a non-empty `description`. |
| `name_kebab_case` | error | 3 | `name` matches `^[a-z0-9]+(-[a-z0-9]+)*$`. |
| `name_length_ok` | error | 2 | `len(name) ≤ 64`. |
| `name_matches_dir` | error | 3 | `name` equals the parent directory name. |
| `description_within_hard_cap` | error | 3 | `len(description) ≤ 1024`. |
| `has_body` | error | 3 | Non-empty content after the frontmatter. |
| `description_min_length` | warn | 2 | `len(description) ≥ 40`. |
| `description_soft_cap` | warn | 1 | `len(description) ≤ 500`. |
| `description_has_trigger` | warn | 3 | Description names an activation cue ("Use when…", "when the user…", "whenever…", "for …ing"). |
| `description_third_person` | warn | 1 | Description does not start with "I"/"You". |
| `name_not_generic` | warn | 1 | `name` is not `skill`, `example`, `test`, … |
| `body_has_heading` | warn | 2 | Body has at least one Markdown heading. |
| `no_placeholders` | warn | 2 | No `TODO`/`FIXME`/`XXX`/`{{…}}`/`<PLACEHOLDER>` left. |
| `body_progressive_disclosure` | info | 1 | Body ≤ 400 lines (else move detail to `references/`). |
| `has_workflow_section` | info | 1 | Body has a Workflow/Usage/Steps section. |

Total weight = 43, so a flawless skill scores exactly 100. Thresholds live as
named constants at the top of `scripts/skill_lint.py`; change them there and the
tests in `scripts/test_validate.py` will tell you what moved.

## Why description quality is weighted so heavily

The harness matches a user's request against every skill's `description` alone —
it does not read the body until the skill is already selected. A description
that only says *what* the skill is ("A commit helper.") gives the model nothing
to match against. One that says *when* to use it ("Use when writing a git commit
message…") reliably fires. That is why `description_has_trigger` and
`description_min_length` are the highest-signal warn checks.

## The automation hook

`.claude/hooks/validate-skill.sh` is registered as a `PostToolUse` hook for the
`Write` and `Edit` tools in `.claude/settings.json`. On every write it:

1. Reads the hook JSON from stdin and extracts the edited file path
   (`.tool_input.file_path`).
2. Exits `0` immediately unless that path ends in `SKILL.md`.
3. Runs `validate_skill.py` on the file.
4. If there are **error**-severity failures, it prints them to stderr and exits
   `2`. For a `PostToolUse` hook, exit code 2 feeds stderr back to the model as
   feedback, so the broken skill gets fixed in the same turn.
5. Warnings alone print to stderr as advice but exit `0` (non-blocking) — the
   loop nudges without nagging.

This is the closing move of the loop: after skill-creator builds a skill, the
hook keeps *every future edit* honest automatically.

### Hook exit-code reference (PostToolUse)

| exit | meaning |
|-----:|---------|
| 0 | success; stdout goes to the transcript |
| 2 | blocking; **stderr is fed back to the model** to act on |
| other | non-blocking error; stderr shown to the user |

## Extending the rubric

Add a check inside `lint_text()` in `skill_lint.py` with a stable `id`, a
severity, and a weight, then add a fixture under `tests/fixtures/<case>/SKILL.md`
and an assertion in `test_validate.py`. Keep the engine stdlib-only so the hook
never needs an install step.
