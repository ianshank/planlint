"""Structural parsers for target-repository machinery.

Two things only: Makefile target names and the pyproject coverage floor. Both
are parsed structurally — not with line regexes over the whole file — so the
coverage floor is read from the correct TOML section and Makefile targets are
recognized without recipe or variable-assignment noise.

Stdlib-only (Python 3.10+). This module imports nothing from ``detect``,
``rules``, ``parse``, ``cli``, or ``graph``; callers construct dataclasses from
the plain data returned here.
"""

from __future__ import annotations

import re

__all__ = ["parse_makefile", "parse_pyproject_fail_under"]

# A variable-assignment line: `NAME := value`, `NAME = value`, `NAME ?= value`,
# `NAME += value`. Detected before rule parsing so a colon in an assignment is
# never mistaken for a rule separator.
_VAR_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\s*(?:\?=|:=|\+=|=)")

# A TOML table header: `[tool.coverage.report]`. Captures the section path.
_SECTION = re.compile(r"^\[([^\]]+)\]\s*$")

# A bare `fail_under = 90` line, possibly with trailing whitespace / a comment.
_FAIL_UNDER = re.compile(r"^fail_under\s*=\s*(\d+)")


def parse_makefile(text: str) -> tuple[str, ...]:
    """Return the sorted, unique set of invokable make target names.

    Recognizes multi-target rules (``a b c: prereq``), ``.PHONY`` members (even
    without their own rule), and double-colon rules (``target::``). Ignores
    recipe lines (tab-prefixed), variable assignments, comments, and pattern /
    automatic-variable targets (``%.o:``, ``$(TARGET):``) which are not invokable
    by name.
    """
    targets: set[str] = set()
    for raw_line in text.splitlines():
        if not raw_line or raw_line.lstrip().startswith("#"):
            continue
        # Recipe lines are commands, not target definitions.
        if raw_line.startswith("\t"):
            continue
        stripped = raw_line.strip()
        # Variable assignments are not targets. Match the stripped line so
        # leading whitespace does not defeat detection (`  NAME := value`).
        if _VAR_ASSIGN.match(stripped):
            continue
        colon = stripped.find(":")
        if colon <= 0:
            continue
        targets_part = stripped[:colon].strip()
        # Pattern / automatic-variable targets are not invokable by name.
        if not targets_part or "$" in targets_part or targets_part.startswith("%"):
            continue
        prereqs = stripped[colon + 1 :].lstrip(":").strip()
        for name in targets_part.split():
            if not name or "$" in name or name.startswith("%"):
                continue
            if name == ".PHONY":
                # .PHONY members are invokable targets even without their own rule.
                # Strip an inline comment first so `# helpers` is not added.
                phony_prereqs = prereqs.split("#", 1)[0]
                for member in phony_prereqs.split():
                    if member:
                        targets.add(member)
                continue
            if name.startswith("."):
                # Other special targets (.SUFFIXES, .DEFAULT_GOAL, .PRECIOUS, ...)
                # are not invokable and neither are their prereqs.
                continue
            targets.add(name)
    return tuple(sorted(targets))


def parse_pyproject_fail_under(text: str) -> int | None:
    """Return the coverage line floor from ``[tool.coverage.report].fail_under``.

    Walks the TOML section-aware (as INI-style table headers), reading
    ``fail_under`` only when the current section is exactly
    ``[tool.coverage.report]``. Returns ``None`` if the section or key is absent,
    or if ``fail_under`` appears only in a different section. The first value in
    the correct section wins.
    """
    current: str | None = None
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        header = _SECTION.match(stripped)
        if header:
            current = header.group(1).strip()
            continue
        if current == "tool.coverage.report":
            match = _FAIL_UNDER.match(stripped)
            if match:
                return int(match.group(1))
    return None
