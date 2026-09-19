"""Confirm the enterprise documentation set exists and is linked from README
(AC-EH-8). A missing or unlinked doc fails the gate — docs that aren't
discoverable from README are effectively absent for a new contributor.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import read_text, repo_root

REPO_ROOT = repo_root()

REQUIRED_DOCS = [
    "CHANGELOG.md",
    "docs/architecture/c4.md",
    "docs/aqa.md",
    "docs/hooks.md",
    "docs/agents-skills-harness.md",
    "docs/next-steps.md",
    # The distributable Agent Skill's own entry point. Listed here so "the
    # README links it" is a gate rather than a hope (R-SD-11): the skill is
    # the product surface an agent reads first, and an unlinked one is
    # undiscoverable from the repo's front page.
    "skills/planlint-spec-governance/SKILL.md",
    # The repo-root entry point an agent loads without being asked. Same
    # argument as the skill above, one step earlier: it is read before anyone
    # decides to read anything else, so an unlinked copy is a file no human
    # reviews and every agent obeys.
    "AGENTS.md",
    # The disclosure route and the threat model. A security policy nobody can
    # find from the front page is a policy in name only, and GitHub surfaces
    # this file to reporters before they read anything else here.
    "SECURITY.md",
]


def check(root: Path | None = None) -> list[str]:
    """Report every required doc that is absent or unlinked under ``root``.

    ``root=None`` rather than ``root=REPO_ROOT`` so the default is read at
    call time, not bound at definition time. With the default bound at def
    time this function could only ever be run against the directory the
    module was imported from, which is why its own gate logic had no test
    that could point it at a fixture tree.
    """
    root = REPO_ROOT if root is None else root
    problems: list[str] = []
    readme_text = read_text(root / "README.md")
    for doc in REQUIRED_DOCS:
        if not (root / doc).exists():
            problems.append(f"MISSING: {doc}")
        elif doc not in readme_text:
            problems.append(f"UNLINKED: {doc} not referenced in README.md")
    return problems


def main(argv: list[str], root: Path | None = None) -> int:
    problems = check(root)
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1
    print("docs-check: all required docs present and linked from README")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
