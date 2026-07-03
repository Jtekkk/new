# Skill self-improvement loop

Claude improving its own tooling — a closed loop where Claude **builds** a
custom Claude Code skill, **runs** it, **measures** it with the skill's own
eval/benchmark mode, and **wires it into a hook** so it keeps every future skill
honest automatically.

```
        ┌────────────────────────────────────────────────────────┐
        │                                                        ▼
   ┌─────────┐      ┌────────┐      ┌───────────┐      ┌──────────────────┐
   │  BUILD  │ ───▶ │  RUN   │ ───▶ │  MEASURE  │ ───▶ │     AUTOMATE     │
   │ author  │      │scaffold│      │ benchmark │      │ PostToolUse hook │
   │  skill  │      │a skill │      │  + score  │      │ validates writes │
   └─────────┘      └────────┘      └───────────┘      └──────────────────┘
        ▲                                                        │
        └──────────────  feedback fixes the skill  ──────────────┘
```

The centerpiece is **`skill-creator`**, a project skill that scaffolds new
skills and scores any `SKILL.md` against a rubric. Because the loop is
self-referential, `skill-creator` is validated by its own rubric (it scores
100/100), and the hook re-runs that rubric on every `SKILL.md` write.

## The four steps

Run everything from the repo root. `SC=.claude/skills/skill-creator/scripts`.

### 1. Build

`skill-creator` is authored as a real skill at
`.claude/skills/skill-creator/`. Its rubric engine is
[`scripts/skill_lint.py`](.claude/skills/skill-creator/scripts/skill_lint.py);
the full rule table and rationale are in
[`references/authoring-guide.md`](.claude/skills/skill-creator/references/authoring-guide.md).

### 2. Run

Scaffold a new skill from the template:

```bash
python3 $SC/new_skill.py commit-helper \
  --description "Use when writing a git commit message …" --with-references
```

This produced [`.claude/skills/commit-helper/`](.claude/skills/commit-helper/),
an example skill. The scaffolder prints the new skill's starting score, then you
flesh out the body.

### 3. Measure

Score one skill, or benchmark them all (eval mode):

```bash
python3 $SC/validate_skill.py .claude/skills/commit-helper/SKILL.md
python3 $SC/benchmark.py --root .claude/skills --out evals/baseline-report.json
```

The committed [`evals/baseline-report.json`](evals/baseline-report.json) is the
current baseline: both skills score 100/100. The rubric produces a real spread —
a broken skill scores as low as 19 (see the fixtures) — so the number means
something.

### 4. Automate

[`.claude/settings.json`](.claude/settings.json) registers a `PostToolUse` hook
on `Write|Edit`:

```
Write/Edit a SKILL.md  ──▶  .claude/hooks/validate-skill.sh  ──▶  hook_entry.py
                                                                      │
                          error-severity failure ──▶ exit 2 (feedback to Claude)
                          warnings only / low score ──▶ exit 0 (advice, no block)
                          passes / not a SKILL.md ──▶ exit 0 (silent)
```

When Claude writes a skill that would not load, the hook feeds the specific
failures straight back so they get fixed in the same turn — that is the closing
edge of the loop.

## The rubric

The validator emits three severities and a weighted 0–100 score. A skill
**passes** with zero errors and a score ≥ 80. Errors *gate* (they break
loading); the score *grades* (activation and authoring quality).

| severity | examples | effect |
|----------|----------|--------|
| **error** | no frontmatter, missing/empty `name`/`description`, non-kebab `name`, `name` ≠ directory, description over 1024 chars, empty body | fails the skill |
| **warn** | thin description, no trigger phrase, first-person voice, generic name, no headings, leftover placeholders | lowers the score |
| **info** | over-long body, no workflow section | advisory only |

Full table with weights: `references/authoring-guide.md`.

## Layout

```
.claude/
  settings.json                     # step 4: PostToolUse hook registration
  hooks/validate-skill.sh           # hook wrapper → hook_entry.py
  skills/
    skill-creator/                  # step 1: the skill that builds/measures skills
      SKILL.md
      scripts/
        skill_lint.py               # rubric engine (stdlib only)
        validate_skill.py           # score one/many SKILL.md (the hook's command)
        benchmark.py                # eval mode: score all skills + aggregate
        new_skill.py                # scaffolder
        hook_entry.py               # PostToolUse decision logic
        test_validate.py            # tests for the rubric (the eval's own eval)
      assets/SKILL.template.md
      references/authoring-guide.md
      tests/fixtures/               # good→broken SKILL.md examples pinning the score range
    commit-helper/                  # step 2: example skill produced by running skill-creator
evals/baseline-report.json          # step 3: committed benchmark baseline
```

## Verify it yourself

```bash
python3 .claude/skills/skill-creator/scripts/test_validate.py   # rubric tests
python3 .claude/skills/skill-creator/scripts/benchmark.py --fail-under 90
```

## Notes

- All scripts are **stdlib-only Python 3** so the hook needs no install step.
- The hook activates automatically in any session started **after**
  `.claude/settings.json` exists (Claude Code's settings watcher only tracks
  directories that already had a settings file at session start). In the session
  that first creates it, open `/hooks` once or restart to load it live.
- Test fixtures under `tests/fixtures/` are intentionally broken and are skipped
  by the hook so editing them never blocks.
