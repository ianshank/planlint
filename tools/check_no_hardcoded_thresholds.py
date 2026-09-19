"""Fail if a numeric threshold, tool version, or pinned path is hard-coded in
the Makefile or any CI workflow YAML (AC-EH-6, rule G003 / C-CH-2).

Thresholds must live in ``pyproject.toml`` and be read by scripts at run time.
This guard catches a regression where someone re-introduces a bare number into
the Makefile (e.g. ``--cov-fail-under=90``) or pins a tool version in the
workflow instead of the dev extras.

Allowed: comments, the Makefile's own ``$(MAKE)`` recursion, and the literal
``0``/``1`` exit codes. Flagged: any other integer appearing on a command line
in the Makefile, or a ``fail-under``/``fail_under``/``--cov-fail-under`` literal
in any workflow.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import repo_root, resolve_makefile

REPO_ROOT = repo_root()

# A comment is the only whole-line exemption: none of it executes.
_COMMENT_LINE = re.compile(r"^\s*#")

# Everything else is removed as a TOKEN before scanning, not used to veto the
# whole line. The previous version vetoed any line containing `$(`, `@\w`, or
# the word "make" -- and `@`-prefixed and `$(VAR)`-using recipes are the
# dominant Makefile idiom, so the guard's real coverage was close to inverted
# from its claim. Measured against the old `_is_allowed`:
#
#   python -m pytest --cov-fail-under=90     FLAGGED
#   @pytest --cov-fail-under=90              ALLOWED   <- the `@\w` veto
#   $(PY) -m pytest --cov-fail-under=90      ALLOWED   <- the `$(` veto
#   make-believe --floor 85                  ALLOWED   <- `\bmake\b`, at the hyphen
#
# A `$(...)` span is genuinely not a literal (its value comes from elsewhere),
# and a leading `@` is recipe-echo syntax carrying no number -- so both are
# stripped and whatever remains is scanned. The `make` rule is dropped
# outright: `$(MAKE)` is already covered by the span strip, and a bare "make"
# never justified ignoring a number on the rest of the line.
_MAKE_EXPANSION = re.compile(r"\$\([^()]*(?:\([^()]*\)[^()]*)*\)")
_RECIPE_ECHO_PREFIX = re.compile(r"^\s*@")

# A numeric literal on a recipe/CI command line that is NOT an exit code 0/1.
_THRESHOLD_TOKEN = re.compile(r"(?<![\w.-])(\d{2,})(?![\w.])")


def _is_allowed(line: str) -> bool:
    """Whether the whole line is exempt. Only a comment ever is."""
    return bool(_COMMENT_LINE.match(line))


def scannable(line: str) -> str:
    """The part of a recipe line a hard-coded number could hide in.

    Strips `$(...)` expansions (nested one level, which covers `$(shell $(PY)
    ...)`) and a leading `@`, then returns the rest. Exposed rather than
    private so a test can assert on the reduction directly.
    """
    return _MAKE_EXPANSION.sub(" ", _RECIPE_ECHO_PREFIX.sub("", line))


def check_makefile(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.is_file():
        # Present but not a regular file -- a directory carrying the name, a
        # dangling symlink. `resolve_makefile` stops here deliberately (make
        # does too), so there is nothing to scan and nothing lower-precedence
        # to fall back to.
        return findings
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return findings
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith(".PHONY"):
            continue
        if _is_allowed(line):
            continue
        for match in _THRESHOLD_TOKEN.finditer(scannable(line)):
            value = match.group(1)
            findings.append(f"{path}:{lineno}: hard-coded numeric literal '{value}' in: {stripped}")
    return findings


def check_workflow(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.exists():
        return findings
    text = path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), 1):
        # A coverage floor pinned in the workflow instead of pyproject.
        if re.search(r"(--cov-fail-under|fail[-_]under)\s*[:=]\s*\d", line):
            findings.append(f"{path}:{lineno}: coverage floor pinned in workflow, not pyproject: {line.strip()}")
        # A python-version pin is allowed (matrix), but a tool version pin is not.
        if re.search(r"ruff==\d|mypy==\d|pytest==\d", line):
            findings.append(f"{path}:{lineno}: tool version pinned in workflow, use dev extras: {line.strip()}")
    return findings


def targets(root: Path | None = None) -> list[Path]:
    """Every file this guard scans.

    A named function, not an inline list inside ``main``, so a test can assert
    on the *selection* rather than re-deriving it. That distinction is the
    whole bug this function exists to prevent: the guard previously named
    ``ci.yml`` literally, so any workflow added later escaped it while the
    guard still printed PASS -- and a test that re-globbed the directory
    itself would have passed against the broken version too (R-SD-10).

    Both YAML spellings are included: GitHub Actions accepts ``.yml`` and
    ``.yaml``, and a guard that covers only one is the same bug one rename
    away. Sorted for a stable report order across filesystems.

    ``root`` defaults through ``None`` so ``REPO_ROOT`` is read at call time
    rather than bound into the signature at definition time -- otherwise this
    guard could only ever be run against its own checkout, and its failing
    path (the one that matters) would have no test that could build a
    violating tree to point it at.
    """
    root = REPO_ROOT if root is None else root
    workflows_dir = root / ".github" / "workflows"
    workflows = sorted(workflows_dir.glob("*.yml")) + sorted(workflows_dir.glob("*.yaml"))
    # By GNU Make's search order, not the literal name `Makefile`. This guard
    # had the same single-name bug `fix-makefile-discovery-names` fixed in
    # detect.py: a repo (or an adopter copying this script) using `GNUmakefile`
    # or `makefile` got a silent PASS, because the missing path returned [].
    makefile = resolve_makefile(root)
    return ([makefile] if makefile else []) + workflows


def main(argv: list[str], root: Path | None = None) -> int:
    root = REPO_ROOT if root is None else root
    findings: list[str] = []
    makefile = resolve_makefile(root)
    for target in targets(root):
        # Dispatch on which list the path came from, never on its basename: a
        # makefile named `GNUmakefile` would otherwise be routed to the
        # workflow checker, which scans for entirely different shapes.
        is_makefile = makefile is not None and target == makefile
        findings.extend(check_makefile(target) if is_makefile else check_workflow(target))

    if findings:
        for message in findings:
            print(f"FAIL: {message}")
        return 1
    print("PASS: no hard-coded thresholds in Makefile or workflow YAML")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
