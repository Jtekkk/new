---
name: commit-helper
description: Use when writing a git commit message or when the user asks to commit, so the message follows Conventional Commits — type(scope): subject — with an imperative subject under 50 characters and a wrapped body.
---

# Commit Helper

Write clear, consistent git commit messages in the Conventional Commits format.
Use this whenever you are about to commit, or when the user asks for a commit
message, so history stays scannable and machine-parseable.

## When to use

Use when the user asks to commit changes, asks for a commit message, or when you
are about to run `git commit` yourself and want the message to follow the
project's convention.

## Format

```
type(scope): subject

body (optional, wrapped at ~72 chars, explains the why)

footer (optional: BREAKING CHANGE:, Refs: #123)
```

- **type** — one of: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`,
  `test`, `build`, `ci`, `chore`, `revert`. See `references/guide.md` for when
  each applies.
- **scope** — optional area of the codebase, e.g. `feat(parser):`.
- **subject** — imperative mood ("add", not "added"/"adds"), no trailing
  period, ≤ 50 characters.
- **body** — optional; explain *why*, not *what*. Wrap at ~72 characters.

## Workflow

1. Inspect what changed: `git diff --staged` (or `git status`).
2. Pick the single `type` that best describes the change; add a `scope` if one
   area dominates.
3. Write an imperative subject ≤ 50 chars that completes the sentence
   "If applied, this commit will …".
4. If the change needs justification, add a blank line and a wrapped body.
5. Note breaking changes in a `BREAKING CHANGE:` footer.
6. Commit, e.g. `git commit -m "fix(auth): reject expired tokens on refresh"`.

## Examples

- `feat(export): add CSV download for reports`
- `fix(api): guard against null user in session lookup`
- `docs: clarify hook exit-code semantics in README`
- `refactor: extract rubric engine into skill_lint module`

Avoid vague subjects like `fix bug`, `update code`, or `changes`. The full type
reference and edge cases live in `references/guide.md`.
