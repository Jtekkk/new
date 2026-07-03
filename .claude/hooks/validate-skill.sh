#!/usr/bin/env bash
# PostToolUse hook: validate SKILL.md writes with skill-creator's rubric.
#
# Registered in .claude/settings.json for the Write and Edit tools. It delegates
# all logic to hook_entry.py (which reads the hook JSON from stdin). This wrapper
# never fails the tool call on its own account — a missing interpreter or script
# exits 0 so a broken hook can never block ordinary editing.
set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
ENTRY="$PROJECT_DIR/.claude/skills/skill-creator/scripts/hook_entry.py"

[ -f "$ENTRY" ] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

# exec so the hook payload on stdin passes straight through and hook_entry.py's
# exit code becomes this hook's exit code (0 ok / 2 blocking).
exec python3 "$ENTRY"
