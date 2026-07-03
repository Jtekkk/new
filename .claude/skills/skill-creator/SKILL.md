---
name: skill-creator
description: Use when creating, scaffolding, or improving a Claude Code skill, or when you want to measure skill quality. Provides a scaffolder, a rubric-based validator, and a benchmark mode, plus guidance for writing descriptions that reliably auto-activate.
---

# Skill Creator

Build, run, measure, and auto-check Claude Code skills. This skill is the engine
of a self-improvement loop: it scaffolds new skills, scores them against a
rubric, and — once its hook is installed — validates every `SKILL.md` the moment
it is written.

A skill is a directory under `.claude/skills/<name>/` containing a `SKILL.md`
with YAML frontmatter (`name`, `description`) and a Markdown body. The
`description` is the **only** text the model sees when deciding whether to
activate the skill, so most of the quality bar lives there.

## When to use

Use when the user asks to create, scaffold, generate, or improve a skill; when
you want to check whether a `SKILL.md` is well-formed and will auto-activate; or
when you want a scored benchmark across all skills in a repo.

## Workflow

Run these from the repository root. `SC=.claude/skills/skill-creator/scripts`.

1. **Build / scaffold** a new skill from the template:

   ```bash
   python3 $SC/new_skill.py my-skill \
     --description "Use when … (name concrete trigger conditions)"
   ```

   Add `--with-scripts` / `--with-references` for helper dirs. The scaffolder
   prints the new skill's starting score.

2. **Run / edit** it: fill in the body, replacing the scaffold's placeholder
   steps with real instructions and clearing its markers.

3. **Measure** a single skill against the rubric:

   ```bash
   python3 $SC/validate_skill.py .claude/skills/my-skill/SKILL.md
   ```

   Or benchmark every skill at once (eval mode):

   ```bash
   python3 $SC/benchmark.py --root .claude/skills --out evals/report.json
   ```

4. **Automate**: the `PostToolUse` hook in `.claude/settings.json` runs the
   validator on any `SKILL.md` write and feeds failures back so they get fixed
   in the same turn. See `references/authoring-guide.md` for how it is wired.

## Rubric at a glance

The validator emits three severities and a 0–100 weighted score. A skill
**passes** when it has zero errors and scores at least 80.

- **error** — breaks loading: missing frontmatter, missing/empty `name` or
  `description`, non-kebab-case `name`, `name` not matching its directory,
  description over the 1024-char cap, or an empty body.
- **warn** — hurts activation or quality: description too short, no trigger
  phrase, first-person voice, generic name, no headings, leftover placeholders.
- **info** — advisory: overly long body (use progressive disclosure), no
  workflow section.

The full rule list, weights, and rationale live in
`references/authoring-guide.md`. The rubric engine is `scripts/skill_lint.py`;
its own tests are `scripts/test_validate.py` (run them after changing the rubric).

## Writing a description that activates

- Lead with the situation, not the mechanism: "Use when the user wants X".
- Name concrete triggers — verbs and nouns the user is likely to say.
- Keep it under ~500 characters; move detail into the body.
- Write in third person about the situation, not "I will…".
