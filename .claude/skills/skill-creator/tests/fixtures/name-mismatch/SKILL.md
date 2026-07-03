---
name: totally-different-name
description: Use when testing that the validator catches a frontmatter name that does not match the skill's directory, which breaks discovery.
---

# Name Mismatch

The frontmatter `name` here is `totally-different-name`, but the directory is
`name-mismatch`. Claude Code keys skills by directory, so a mismatch is an
error-severity failure.

## Workflow

1. Compare name to directory.
2. Fail the rubric.
