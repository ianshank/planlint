"""Report code under the coverage source trees that nothing references (vulture).

Usage::

    python tools/dead_code.py                     # this repository
    python tools/dead_code.py --root /path/to/checkout

It is a **report, not a gate** (``DEC-PM-011``, guardrail 7): composed into
neither ``ci`` nor ``pre-pr``, and made a gate only by a package of its own
after a quarter of an empty report. Its exit contract is planlint's own
(``report-dead-code-and-spec-status``, R-RDS-5, DEC-RDS-006): **0** when
nothing is listed, with a line saying so; **1** when an unreferenced symbol
or a stale whitelist entry is listed; **2** when it cannot run, with the
cause named and never a traceback.

What it reads. The reported trees are ``[tool.coverage.run] source``, this
repository's one declaration of the trees it measures. ``tests/`` is read as
a *user* of the code and never reported, because the reflection plan's
"Unreferenced symbols" count is repository-wide; reporting it would also list
pytest fixtures, which pytest injects by name (DEC-RDS-003). The confidence is
``[tool.specgraph] dead_code_min_confidence``, passed to vulture on the
command line. There is no ``[tool.vulture]`` table, and there must not be:
vulture reads one from its working directory, which is the root here, and
its keys would act on the run that has to see every finding (DEC-RDS-002).

The whitelist, ``tools/dead_code_whitelist.txt``, holds one ``name  # reason``
per line, for a reported name that code vulture does not read uses -- the
shlex lexer attributes ``_common`` sets for the standard library, at landing.
It is never passed to vulture. It is applied by name after one run made
without it, which is what vulture's own whitelist does (a whitelisted name
counts as used), so the one run shows both what an entry hides and which entry
hides nothing. Staleness is caught in two halves (DEC-RDS-004): an entry that
names no binding in a reported tree is found by
:func:`unbound_whitelist_entries`, with ``ast`` and no vulture, in a test in
``make test``; an entry that is bound but suppresses no finding is listed by
this report. So ``make test``'s verdict never changes with a vulture release,
and no stale entry survives a run of the report.

Why a process. ``tools/`` takes no third-party import (``tools/AGENTS.md``),
so vulture runs as ``sys.executable -m vulture`` -- the vulture installed
beside the interpreter running this script -- and its absence is decided by
``importlib.util.find_spec`` before any process starts, so no import-error
text reaches stderr (DEC-RDS-005). Its exit 3, "dead code found", becomes
this report's 1; its 1 and 2 become this report's 2.

Why stderr is a log. Vulture writes findings to stdout and complaints to
stderr, and ``ast.parse``, which it parses with, writes a ``SyntaxWarning``
for an invalid escape to stderr and still succeeds. So stdout is the report
and stderr goes to the DEBUG log (``PLANLINT_LOG_LEVEL=DEBUG`` shows it): it
decides nothing beside exit 0 or 3, and reaches the message only when the exit
code says vulture could not run.

Why an empty tree is not clean. Vulture over a directory with no ``.py``
file prints nothing and exits 0, which would read as "nothing to report" for
a tree never read, and over an absent path it exits 1 with its own message.
So each declared tree is checked before the process starts.
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import importlib.metadata
import importlib.util
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
    SCOPED_FLOOR_SECTION,
    ReportError,
    coverage_sources,
    logger,
    read_pyproject_int,
    repo_root,
)

CONFIDENCE_KEY = "dead_code_min_confidence"

#: Trees read as users of the code and never reported (DEC-RDS-003).
USAGE_ONLY = ("tests",)

WHITELIST = Path("tools") / "dead_code_whitelist.txt"

PYPROJECT = "pyproject.toml"

#: Vulture's exit codes: 0 clean, 3 dead code found (from 2.9, DEC-RDS-001).
VULTURE_CLEAN = 0
VULTURE_FOUND = 3

#: One line of vulture's stdout: ``path:line: message (N% confidence)``, with
#: the size suffix ``--sort-by-size`` would add tolerated.
_FINDING = re.compile(
    r"^(?P<path>.+?):(?P<line>\d+): (?P<message>.+) "
    r"\((?P<confidence>\d+)% confidence(?:, \d+ lines?)?\)$"
)

#: The one message shape that names a symbol; every other message -- an
#: unreachable block, an unsatisfiable condition -- names none.
_UNUSED_SYMBOL = re.compile(r"^unused (?P<kind>\w+) '(?P<name>[^']+)'$")

#: A whitelist line: an identifier, whitespace, ``#``, and a reason.
_WHITELIST_LINE = re.compile(r"^(?P<name>\S+)\s+#\s*(?P<reason>\S.*)$")

Runner = Callable[[Path, Sequence[str]], tuple[int, str, str]]


@dataclasses.dataclass(frozen=True)
class Finding:
    """One line of vulture's report; ``name`` is set only for ``unused <kind> '<name>'``."""

    path: str
    line: int
    message: str
    confidence: int
    name: str | None

    def render(self) -> str:
        """Vulture's own line form, with the path's separators normalised."""
        return f"{self.path}:{self.line}: {self.message} ({self.confidence}% confidence)"


def parse_line(text: str) -> Finding | None:
    """A finding from one stdout line, or ``None`` when it has neither shape."""
    match = _FINDING.match(text)
    if match is None:
        return None
    symbol = _UNUSED_SYMBOL.match(match.group("message"))
    return Finding(
        path=match.group("path").replace("\\", "/"),
        line=int(match.group("line")),
        message=match.group("message"),
        confidence=int(match.group("confidence")),
        name=symbol.group("name") if symbol else None,
    )


def read_config(root: Path) -> tuple[int, list[str]]:
    """``(confidence, reported trees)`` from ``root``'s ``pyproject.toml``.

    ``_common``'s readers raise ``OSError`` and ``UnicodeDecodeError``
    unchanged, which the gates sharing them rely on, so this script turns
    them into its own exit 2, naming the file.
    """
    pyproject = root / PYPROJECT
    try:
        confidence = read_pyproject_int(pyproject, SCOPED_FLOOR_SECTION, CONFIDENCE_KEY)
        trees = coverage_sources(pyproject)
    except (OSError, UnicodeDecodeError) as exc:
        raise ReportError(f"cannot read {pyproject}: {exc}") from exc
    if confidence is None:
        raise ReportError(f"{pyproject}: {SCOPED_FLOOR_SECTION} {CONFIDENCE_KEY} is absent")
    if not trees:
        raise ReportError(f"{pyproject}: [tool.coverage.run] source declares no tree to report")
    logger.debug("dead-code: confidence %d over %s, from %s", confidence, trees, pyproject)
    return confidence, trees


def check_trees(root: Path, trees: Sequence[str]) -> None:
    """Refuse a declared tree that is absent or holds no ``.py`` file, which
    vulture would read as clean."""
    for tree in trees:
        path = root / tree
        if not path.is_dir():
            raise ReportError(f"declared tree {tree}/ is not a directory under {root}")
        if next(path.rglob("*.py"), None) is None:
            raise ReportError(
                f"declared tree {tree}/ holds no .py file; vulture would read it as clean"
            )


def read_whitelist(path: Path) -> dict[str, str]:
    """``{name: reason}``; an absent file is an empty whitelist."""
    if not path.exists():
        logger.debug("dead-code: no whitelist at %s", path)
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ReportError(f"cannot read {path}: {exc}") from exc
    entries: dict[str, str] = {}
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = _WHITELIST_LINE.match(stripped)
        if match is None or not match.group("name").isidentifier():
            raise ReportError(
                f"{path}:{number}: malformed whitelist line {line!r}; "
                "expected an identifier, whitespace, '#' and a reason"
            )
        entries[match.group("name")] = match.group("reason")
    logger.debug("dead-code: %d whitelist entries from %s", len(entries), path)
    return entries


def _bound_names(tree: ast.AST) -> set[str]:
    """Every name a module binds: a function, class or method; an assignment
    target, a name or an attribute's name; an import alias; a parameter."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
            names.add(node.attr)
        elif isinstance(node, ast.alias):
            names.add(node.asname or node.name.split(".")[0])
        elif isinstance(node, ast.arg):
            names.add(node.arg)
    return names


def unbound_whitelist_entries(root: Path) -> list[str]:
    """Every whitelist entry that no reported tree binds, sorted -- the
    deterministic half of staleness, read with ``ast`` and without vulture
    (R-RDS-7)."""
    _, trees = read_config(root)
    entries = read_whitelist(root / WHITELIST)
    bound: set[str] = set()
    for tree in trees:
        for path in sorted((root / tree).rglob("*.py")):
            bound |= _bound_names(ast.parse(path.read_text(encoding="utf-8"), str(path)))
    unbound = sorted(set(entries) - bound)
    logger.debug("dead-code: %d of %d whitelist entries unbound", len(unbound), len(entries))
    return unbound


def vulture_argv(root: Path, trees: Sequence[str], confidence: int) -> list[str]:
    """The one vulture command: the reported trees, ``tests`` when present, at
    ``confidence``, and no whitelist."""
    usage = [tree for tree in USAGE_ONLY if (root / tree).is_dir()]
    return [sys.executable, "-m", "vulture", *trees, *usage, "--min-confidence", str(confidence)]


def run_vulture(root: Path, argv: Sequence[str]) -> tuple[int, str, str]:
    """Run ``argv`` from ``root``; ``(exit code, stdout, stderr)``."""
    result = subprocess.run(
        list(argv), cwd=root, capture_output=True, text=True, check=False
    )
    return result.returncode, result.stdout, result.stderr


def vulture_version() -> str:
    """The installed vulture's version, from its metadata, without importing it."""
    try:
        return importlib.metadata.version("vulture")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def build_report(
    stdout: str, trees: Sequence[str], whitelist: dict[str, str]
) -> tuple[list[Finding], list[str]]:
    """``(listed findings, stale whitelist entries)`` from vulture's stdout alone.

    A finding outside every reported tree -- under ``tests/`` -- is dropped; a
    finding whose name is a whitelist entry is suppressed; a finding that
    names no symbol is never suppressed.
    """
    listed: list[Finding] = []
    used: set[str] = set()
    for raw in stdout.splitlines():
        if not raw.strip():
            continue
        finding = parse_line(raw)
        if finding is None:
            raise ReportError(f"vulture printed a line in neither shape: {raw!r}")
        if not any(finding.path == tree or finding.path.startswith(f"{tree}/") for tree in trees):
            logger.debug("dead-code: not a reported tree, dropped: %s", finding.render())
            continue
        if finding.name is not None and finding.name in whitelist:
            logger.debug("dead-code: whitelisted, suppressed: %s", finding.render())
            used.add(finding.name)
            continue
        listed.append(finding)
    listed.sort(key=lambda item: (item.path, item.line, item.message))
    stale = sorted(set(whitelist) - used)
    return listed, stale


def _plural(count: int, singular: str, plural: str) -> str:
    return f"{count} {singular if count == 1 else plural}"


def report(root: Path, run: Runner) -> int:
    """Print the report for ``root``; the exit code, or ``ReportError``."""
    confidence, trees = read_config(root)
    check_trees(root, trees)
    whitelist = read_whitelist(root / WHITELIST)
    if importlib.util.find_spec("vulture") is None:
        raise ReportError(
            'vulture is not installed; install the dev extra (pip install -e ".[dev]")'
        )
    argv = vulture_argv(root, trees, confidence)
    logger.debug("dead-code: running %s from %s", argv, root)
    code, stdout, stderr = run(root, argv)
    if stderr.strip():
        logger.debug("dead-code: vulture stderr (exit %d): %s", code, stderr.strip())
    if code not in (VULTURE_CLEAN, VULTURE_FOUND):
        detail = stderr.strip() or "(nothing on stderr)"
        raise ReportError(f"vulture exited {code}: {detail}")
    listed, stale = build_report(stdout, trees, whitelist)
    usage = [tree for tree in USAGE_ONLY if (root / tree).is_dir()]
    users = f"; {', '.join(f'{tree}/' for tree in usage)} read as a user" if usage else ""
    print(
        f"dead-code: {', '.join(trees)} at confidence {confidence} "
        f"(vulture {vulture_version()}{users}); "
        f"{_plural(len(whitelist), 'whitelist entry', 'whitelist entries')} read"
    )
    for finding in listed:
        print(finding.render())
    if stale:
        print("stale whitelist entries:")
        for name in stale:
            print(f"  {name}  # {whitelist[name]}")
    if not listed and not stale:
        print("nothing to report: no unreferenced code and no stale whitelist entry")
        return 0
    print(
        f"{_plural(len(listed), 'unreferenced symbol', 'unreferenced symbols')}; "
        f"{_plural(len(stale), 'stale whitelist entry', 'stale whitelist entries')}"
    )
    return 1


def main(argv: Sequence[str], run: Runner = run_vulture) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "--root", default=None, help="repository to report on (default: this repository)"
    )
    args = parser.parse_args(list(argv[1:]))
    root = (Path(args.root) if args.root is not None else repo_root()).resolve()
    if not root.is_dir():
        print(f"ERROR not a directory: {root}", file=sys.stderr)
        return 2
    try:
        return report(root, run)
    except ReportError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
