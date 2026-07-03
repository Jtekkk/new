#!/usr/bin/env python3
"""new_skill — scaffold a new Claude Code skill from the skill-creator template.

    new_skill.py NAME --description "Use when …" [options]

Options:
    --root DIR          Skills root (default: .claude/skills).
    --title TITLE       H1 title for the body (default: derived from NAME).
    --with-scripts      Also create a scripts/ dir with a runnable stub.
    --with-references   Also create references/ for progressive disclosure.
    --force             Overwrite an existing SKILL.md.

After writing, the new skill is immediately validated so you get its starting
score right away — the first turn of the build → run → measure loop.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skill_lint import lint_file, KEBAB_RE  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "SKILL.template.md")

SCRIPT_STUB = '''#!/usr/bin/env python3
"""Helper for the {name} skill."""


def main() -> int:
    print("TODO: implement {name} helper")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

REFERENCE_STUB = """# {title} — reference

Move long-form detail here so SKILL.md stays lean (progressive disclosure).
The model reads SKILL.md first and only opens this file when it needs depth.
"""


def title_from_name(name: str) -> str:
    return " ".join(w.capitalize() for w in name.split("-"))


def render_template(name: str, description: str, title: str) -> str:
    with open(TEMPLATE, "r", encoding="utf-8") as fh:
        tpl = fh.read()
    return (
        tpl.replace("{{NAME}}", name)
        .replace("{{DESCRIPTION}}", description)
        .replace("{{TITLE}}", title)
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Scaffold a new Claude Code skill.")
    ap.add_argument("name", help="skill name (kebab-case)")
    ap.add_argument("--description", required=True,
                    help="frontmatter description — name concrete trigger conditions")
    ap.add_argument("--root", default=".claude/skills")
    ap.add_argument("--title", default=None)
    ap.add_argument("--with-scripts", action="store_true")
    ap.add_argument("--with-references", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)

    name = args.name.strip()
    if not KEBAB_RE.match(name):
        print(f"error: {name!r} is not kebab-case (a-z, 0-9, single hyphens).",
              file=sys.stderr)
        return 2

    title = args.title or title_from_name(name)
    skill_dir = os.path.join(args.root, name)
    skill_md = os.path.join(skill_dir, "SKILL.md")

    if os.path.exists(skill_md) and not args.force:
        print(f"error: {skill_md} already exists (use --force to overwrite).",
              file=sys.stderr)
        return 2

    os.makedirs(skill_dir, exist_ok=True)
    with open(skill_md, "w", encoding="utf-8") as fh:
        fh.write(render_template(name, args.description, title))
    created = [skill_md]

    if args.with_scripts:
        sdir = os.path.join(skill_dir, "scripts")
        os.makedirs(sdir, exist_ok=True)
        stub = os.path.join(sdir, "run.py")
        with open(stub, "w", encoding="utf-8") as fh:
            fh.write(SCRIPT_STUB.format(name=name))
        os.chmod(stub, 0o755)
        created.append(stub)

    if args.with_references:
        rdir = os.path.join(skill_dir, "references")
        os.makedirs(rdir, exist_ok=True)
        ref = os.path.join(rdir, "guide.md")
        with open(ref, "w", encoding="utf-8") as fh:
            fh.write(REFERENCE_STUB.format(title=title))
        created.append(ref)

    print("Scaffolded skill:")
    for p in created:
        print(f"  + {p}")

    result = lint_file(skill_md)
    print(f"\nStarting score: {result.score}/100 "
          f"({result.counts['error']} error, {result.counts['warn']} warn) — "
          f"{'PASS' if result.passed else 'needs work'}")
    print("Next: flesh out the body, then re-check with")
    print(f"  python3 {os.path.relpath(os.path.join(HERE, 'validate_skill.py'))} {skill_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
