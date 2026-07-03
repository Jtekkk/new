# Commit Helper — reference

Detail behind `SKILL.md`. Read when you need to pick the right type or handle an
edge case.

## Types

| type | use it for |
|------|-----------|
| `feat` | a new user-facing feature |
| `fix` | a bug fix |
| `docs` | documentation only |
| `style` | formatting/whitespace, no behavior change |
| `refactor` | code change that neither fixes a bug nor adds a feature |
| `perf` | a change that improves performance |
| `test` | adding or correcting tests |
| `build` | build system or dependencies |
| `ci` | CI configuration and scripts |
| `chore` | maintenance that doesn't touch src or tests |
| `revert` | reverts a previous commit |

## Rules of thumb

- One logical change per commit; if the subject needs "and", consider splitting.
- Subject in the imperative, ≤ 50 chars, no trailing period, capitalized start.
- Body explains *why* and contrasts with previous behavior; wrap at ~72 chars.
- Breaking changes: add a `BREAKING CHANGE: <what and how to migrate>` footer,
  or append `!` after the type/scope (`feat(api)!: …`).
- Reference issues in the footer: `Refs: #123`, `Closes: #123`.

## Edge cases

- **Merge commits**: leave the default or use `chore: merge <branch>`.
- **Reverts**: `revert: <subject of reverted commit>` with the reverted SHA in
  the body.
- **Work in progress**: avoid committing `wip`; squash before sharing.
