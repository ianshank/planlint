"""Small shared helpers for the ``tools/`` gate scripts.

These scripts are intentionally dependency-free (stdlib only) so they run in a
bare CI runner. Anything repeated across them lives here so a fix to repo-root
discovery or text reading is made once.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

# Debug logging for the gate scripts, under the CLI's own "planlint" logger
# namespace so one env var covers both.
#
# The env var must be read *here*. `logging.getLogger` inherits nothing from
# openspec_graph.log: that module reads PLANLINT_LOG_LEVEL only inside its own
# configure(), which no tool calls, and tools stay stdlib-only so they cannot
# import it anyway (a gate script must run in a bare CI runner where planlint
# may not be installed). Attaching the name without reading the variable was
# tried first and silently dropped every record while the comment claimed
# otherwise -- so the level is resolved and a handler attached below.
_ENV_VARS = ("PLANLINT_LOG_LEVEL", "SPECGRAPH_LOG_LEVEL")  # legacy name second
logger = logging.getLogger("planlint.tools")


def _configure_from_env() -> None:
    """Set the tools logger's level from the environment, once.

    Idempotent and handler-safe: re-importing this module (tests load these
    scripts by path more than once) must not stack duplicate handlers.
    Records go to stderr, never stdout, because a gate script's stdout is
    parsed by CI and by ``make``.
    """
    raw = ""
    for name in _ENV_VARS:
        raw = os.environ.get(name, "")
        if raw:
            break
    named = logging.getLevelName(raw.upper())
    logger.setLevel(named if isinstance(named, int) else logging.WARNING)
    if not logger.handlers:
        handler = logging.StreamHandler()  # stderr
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
    logger.propagate = False


_configure_from_env()

# tools/ sits one level below the repo root.
REPO_ROOT = Path(__file__).resolve().parent.parent


# GNU Make's search order, duplicated here on purpose.
#
# `openspec_graph.detect.MAKEFILE_NAMES` is the same tuple, and this module
# deliberately does not import it: `tools/` is stdlib-only and runs before the
# package is installed (pre-commit, a fresh checkout), so a package import
# would make the gates depend on the thing they gate. The duplication is
# pinned by a test asserting the two tuples are equal, so a drift is a failure
# rather than a silent divergence -- which is how the single-name lookup this
# replaces survived in both places at once.
MAKEFILE_NAMES = ("GNUmakefile", "makefile", "Makefile")


def resolve_makefile(root: Path) -> Path | None:
    """The makefile GNU Make would read under ``root``, or ``None``.

    Matched against the directory LISTING rather than by probing
    ``(root / name).is_file()`` per candidate, for two reasons the Windows CI
    leg found the hard way:

    1. On a case-insensitive filesystem, probing `makefile` succeeds against a
       file written `Makefile`, and the returned path then carries the
       *candidate's* spelling rather than the real one. `detect` can shrug that
       off -- its dialect card carries targets, never the filename -- but this
       function's result is a scanned path that a caller reports on, so the
       wrong spelling is user-visible. The listing gives the true name.
    2. Presence, not readability, is what ends the search. `make` stops at the
       first name that EXISTS, even if it cannot open it, so a directory named
       `GNUmakefile` must not let a lower-precedence `Makefile` be scanned --
       that would report on a file `make` would never read. Readability is the
       caller's problem, which is why ``check_makefile`` tolerates a path it
       cannot open rather than this function silently skipping it.
    """
    try:
        present = {entry.name for entry in root.iterdir()}
    except OSError:
        return None
    for name in MAKEFILE_NAMES:
        if name in present:
            return root / name
    return None


def repo_root() -> Path:
    """Return the repository root (the parent of the ``tools/`` directory)."""
    return REPO_ROOT


def read_text(path: Path) -> str:
    """Read a file as UTF-8, returning ``\"\"`` if it is missing.

    Centralizes the ``encoding=\"utf-8\"`` convention used by every gate script
    so encoding is never left to the platform default.
    """
    return path.read_text(encoding="utf-8") if path.exists() else ""


def read_json(path: Path) -> dict[str, Any]:
    """Parse a JSON file whose top level is an object, fully typed.

    Read directly rather than through :func:`read_text`, on purpose: that
    helper's missing-file ``""`` would turn an absent artifact into a
    ``JSONDecodeError`` with no path in it, where the consumers of this
    function -- ``diff_spec_graph`` and ``render_mermaid``, which read a
    saved ``planlint graph --format json`` -- need a missing file to stay the
    ``FileNotFoundError`` it is. A document whose top level is not an object
    (a list, a string, ``null``) is refused here with the path in the
    message; every caller indexes the result by key, and letting it through
    would surface later as a ``TypeError`` that names nothing.

    One DEBUG record names the file and its size, so a run under
    ``PLANLINT_LOG_LEVEL=DEBUG`` shows which artifact was read before the
    verdict is printed.
    """
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(
            f"{path}: expected a JSON object at the top level, got {type(data).__name__}"
        )
    logger.debug(
        "read_json: %s (%d bytes, %d top-level keys)",
        path, len(text.encode("utf-8")), len(data),
    )
    return data


def read_pyproject_int(pyproject: Path, section: str, key: str) -> int | None:
    """Read one integer key out of one ``pyproject.toml`` table, stdlib only.

    Hand-rolled rather than via ``tomllib`` because these gate scripts run
    before anything is installed and on the 3.10 leg of the matrix, where the
    stdlib parser does not exist. Section-aware on purpose: a bare search for
    the key would match the same name under any other table.

    The path is an argument rather than :func:`repo_root`, deliberately. The
    coverage gates read the ``pyproject.toml`` of whichever tree they are
    pointed at, so they can be exercised against a synthetic one (see
    ``tests/test_ci_hardening.py``, which writes a floor of 95 into a temp
    directory and asserts the gate honours it). Anchoring at this repository's
    own root would make the gate untestable and would silently ignore the
    config of the tree actually being measured.

    Returns ``None`` when the file, the table, or the key is absent. Callers
    treat that as a misconfiguration and fail loudly; it is never a skip.
    """
    if not pyproject.exists():
        return None
    in_section = False
    pattern = re.compile(rf"{re.escape(key)}\s*=\s*(\d+)")
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_section = stripped == section
            continue
        if not in_section:
            continue
        match = pattern.match(stripped)
        if match:
            return int(match.group(1))
    return None


def write_or_check(path: Path, expected: str, *, write: bool, label: str) -> int:
    """Regenerate ``path`` from ``expected``, or verify it already matches.

    The shared half of every generated-artifact tool here (the rule catalog,
    the plugin manifests): a ``--write`` mode that is the single writer, and a
    ``--check`` mode CI runs to prove the committed file was regenerated. The
    two modes must agree byte-for-byte or the check is theater, which is why
    they read from one ``expected`` string rather than each formatting its own.

    Returns a process exit code: 0 for written or fresh, 1 for stale/missing.
    ``label`` names the make target that regenerates the file, so the failure
    message tells the reader what to run instead of only what is wrong.
    """
    # Display path: repo-relative when the target is inside the repo, absolute
    # otherwise. relative_to() raises on any path outside REPO_ROOT, which a
    # test redirecting the target into a temp directory legitimately does --
    # a generator helper must not require its output to live in this repo.
    try:
        rel = path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        rel = str(path)
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        changed = read_text(path) != expected
        path.write_text(expected, encoding="utf-8")
        logger.debug("write_or_check: wrote %s (changed=%s)", rel, changed)
        print(f"wrote {rel}" if changed else f"unchanged {rel}")
        return 0

    actual = read_text(path)
    if not actual:
        logger.debug("write_or_check: %s missing or empty", rel)
        print(f"STALE: {rel} is missing or empty; run `{label}`", file=sys.stderr)
        return 1
    if actual != expected:
        logger.debug(
            "write_or_check: %s differs (%d bytes on disk, %d expected)",
            rel, len(actual), len(expected),
        )
        print(f"STALE: {rel} does not match its generator; run `{label}`", file=sys.stderr)
        return 1
    logger.debug("write_or_check: %s is fresh", rel)
    return 0


#: Where a scoped floor lives, given ``--scope NAME``: ``[tool.specgraph]``
#: key ``NAME_line_fail_under`` / ``NAME_branch_fail_under``. Derived rather
#: than listed so adding a second measured tree is a config line, not a code
#: change -- and kept in one place so the two checkers cannot disagree.
SCOPED_FLOOR_SECTION = "[tool.specgraph]"


def scoped_floor_key(scope: str, kind: str) -> str:
    """``("tools", "line") -> "tools_line_fail_under"``."""
    return f"{scope}_{kind}_fail_under"


#: Where the unscoped floors live, by kind. The FIRST entry of
#: ``[tool.coverage.run] source`` is the tree these have always gated, so a
#: scoped read of that tree with no scoped key of its own falls back here;
#: every later entry needs its own ``<scope>_<kind>_fail_under`` key. One
#: mapping, read by both checkers, so they cannot disagree about either kind
#: (measure-coverage-once, R-MCO-3, DEC-MCO-002).
UNSCOPED_FLOOR_LOCATORS: dict[str, tuple[str, str]] = {
    "line": ("[tool.coverage.report]", "fail_under"),
    "branch": (SCOPED_FLOOR_SECTION, "branch_fail_under"),
}
COVERAGE_RUN_SECTION = "[tool.coverage.run]"
_SOURCE_ARRAY = re.compile(r"^source\s*=\s*\[(.*)$", re.S)
_SOURCE_ENTRY = re.compile(r"""["']([^"']+)["']""")


def normalize_scope(name: str) -> str:
    """``"./tools/"`` -> ``"tools"``: the one spelling ``--scope`` and ``source`` compare in."""
    name = name.strip().replace("\\", "/")
    if name.startswith("./"):
        name = name[2:]
    return name.rstrip("/")


def coverage_sources(pyproject: Path) -> list[str]:
    """The entries of ``[tool.coverage.run] source``, in order, normalized.

    Hand-rolled on the same table-tracking loop as :func:`read_pyproject_int`
    and for the same reason: these gate scripts run on the 3.10 leg, where
    ``tomllib`` does not exist. Accepts exactly the shape this repository
    writes -- the literal ``[tool.coverage.run]`` header and a
    ``source = [...]`` array, on one line or several -- and strips a leading
    ``./`` and a trailing ``/`` from each entry so it compares equal to a
    ``--scope`` name. The dotted ``[tool.coverage]`` / ``run.source`` form and
    the separate ``source_pkgs`` key are not read: a tree declared that way
    finds no entry here and surfaces as the checkers' exit-2 message naming
    both places a floor could have lived, never as a silent pass
    (DEC-MCO-003). An absent file, table or key is ``[]``.
    """
    if not pyproject.exists():
        return []
    in_section = False
    array_text: str | None = None
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]") and array_text is None:
            in_section = stripped == COVERAGE_RUN_SECTION
            continue
        if not in_section:
            continue
        if array_text is None:
            match = _SOURCE_ARRAY.match(stripped)
            if match:
                array_text = match.group(1)
        else:
            array_text += "\n" + stripped
        if array_text is not None and "]" in array_text:
            break
    if array_text is None:
        return []
    body = array_text.split("]", 1)[0]
    return [normalize_scope(entry) for entry in _SOURCE_ENTRY.findall(body)]


def scoped_floor(pyproject: Path, scope: str, kind: str) -> int | None:
    """The ``kind`` (``"line"`` or ``"branch"``) floor for one measured tree.

    ``scope`` is normalised first -- ``"tools"``, ``"tools/"`` and ``"./tools"``
    are one tree -- and the scoped key is built from the normalised name
    (``tools_line_fail_under``, never ``tools/_line_fail_under``), so no
    spelling can slip past a stricter scoped floor onto the unscoped one.
    Then, in this order (R-MCO-3): the tree's own ``[tool.specgraph]
    <scope>_<kind>_fail_under`` key; else, when ``scope`` is the FIRST entry of
    ``[tool.coverage.run] source``, the unscoped locator in
    :data:`UNSCOPED_FLOOR_LOCATORS`; else ``None``, which the caller turns into
    exit 2 naming both places. Only the first entry falls back, for D2's two
    reasons: its floors have lived in the unscoped locators since the gate
    existed (``planlint detect`` reports that locator, and the threshold guard
    anchors on it), and a scoped twin of them would be two places for one
    number -- which is why :func:`duplicate_scoped_floor_keys` forbids one on
    this repository's own ``pyproject.toml``. Every later entry keeps
    R-GTC-11 as written: no key, no gate, exit 2.
    """
    scope = normalize_scope(scope)
    own = read_pyproject_int(pyproject, SCOPED_FLOOR_SECTION, scoped_floor_key(scope, kind))
    if own is not None:
        return own
    if scope in coverage_sources(pyproject)[:1]:
        section, key = UNSCOPED_FLOOR_LOCATORS[kind]
        logger.debug(
            "scoped_floor: %s is the first coverage source; reading %s %s", scope, section, key
        )
        return read_pyproject_int(pyproject, section, key)
    return None


def missing_floor_message(pyproject: Path, scope: str, kind: str) -> str:
    """Both places a scoped floor could have lived, for the checkers' exit-2 line.

    Names the scoped key as :func:`scoped_floor` looked it up -- built from the
    normalised scope -- so the reader is sent to a key that can exist.
    """
    scope = normalize_scope(scope)
    section, key = UNSCOPED_FLOOR_LOCATORS[kind]
    where = f"{SCOPED_FLOOR_SECTION} {scoped_floor_key(scope, kind)}"
    sources = coverage_sources(pyproject)
    first = sources[0] if sources else None
    if first is not None and scope == first:
        return f"{where}, and {section} {key} -- the first source entry's floor -- is absent too"
    return (
        f"{where}; the unscoped {key} applies only to the first {COVERAGE_RUN_SECTION} source "
        f"entry ({first if first is not None else 'none declared'})"
    )


def duplicate_scoped_floor_keys(pyproject: Path) -> list[str]:
    """Scoped floor keys that duplicate the first source entry's unscoped floors.

    The first entry's floors are the unscoped locators; a
    ``<first>_<kind>_fail_under`` beside them is two places for one threshold,
    the drift ``make thresholds`` exists to prevent (R-MCO-5). Returns the
    offending keys, in kind order, or ``[]``.
    """
    sources = coverage_sources(pyproject)
    if not sources:
        return []
    first = sources[0]
    return [
        scoped_floor_key(first, kind)
        for kind in UNSCOPED_FLOOR_LOCATORS
        if read_pyproject_int(pyproject, SCOPED_FLOOR_SECTION, scoped_floor_key(first, kind)) is not None
    ]


def coverage_totals(
    cov_path: Path, covered_key: str, total_key: str, scope: str | None = None
) -> tuple[int, int]:
    """Sum one coverage.json counter pair, optionally over one subtree only.

    ``scope=None`` reads the report's own ``totals``, which is every measured
    source. A ``scope`` instead sums the per-file summaries under that
    directory, so one test run can gate two trees against two floors without
    either number being diluted by the other -- the package and its own gate
    scripts have genuinely different coverage, and a combined figure hides
    both.

    Separator-normalized before matching: coverage.py writes the paths as the
    platform spells them, so a backslash-separated ``tools`` path on Windows
    would never match a ``tools/`` prefix. Returns ``(0, 0)`` for a scope that matches
    nothing, which every caller already treats as a misconfiguration and
    fails loudly on, rather than as a vacuous pass.
    """
    data = json.loads(cov_path.read_text(encoding="utf-8"))
    if scope is None:
        totals = data.get("totals", {})
        return int(totals.get(covered_key, 0)), int(totals.get(total_key, 0))

    prefix = scope.replace("\\", "/").rstrip("/") + "/"
    covered = total = 0
    for raw_path, entry in data.get("files", {}).items():
        if not raw_path.replace("\\", "/").startswith(prefix):
            continue
        summary = entry.get("summary", {})
        covered += int(summary.get(covered_key, 0))
        total += int(summary.get(total_key, 0))
    return covered, total


def parse_coverage_argv(argv: list[str]) -> tuple[Path, str | None]:
    """``(coverage.json path, scope)`` from a gate script's argv.

    Hand-rolled rather than argparse to match the hand-rolled scripts in this
    directory -- the five that index ``argv`` directly, two of which call
    this -- and because the accepted shape is exactly two optional things.
    The other scripts here are argparse-based; see ``tools/AGENTS.md`` for
    the grouping. ``--scope`` may be given as
    ``--scope NAME`` or ``--scope=NAME``.
    """
    cov_path = Path("coverage.json")
    scope: str | None = None
    rest = list(argv[1:])
    positional: list[str] = []
    while rest:
        arg = rest.pop(0)
        if arg.startswith("--scope="):
            scope = arg.split("=", 1)[1]
        elif arg == "--scope":
            if not rest:
                raise ValueError("--scope requires a directory name")
            scope = rest.pop(0)
        else:
            positional.append(arg)
    if positional:
        cov_path = Path(positional[0])
    if scope is not None and not scope.strip():
        raise ValueError("--scope requires a directory name")
    return cov_path, scope
