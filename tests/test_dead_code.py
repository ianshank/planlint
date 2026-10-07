"""``tools/dead_code.py``: unreferenced code under the coverage source trees.

``report-dead-code-and-spec-status`` (R-RDS-1 to R-RDS-7, R-RDS-19). The
script runs vulture once as a process over every tree ``[tool.coverage.run]
source`` declares, plus ``tests/`` as a user that is never reported, at
``[tool.specgraph] dead_code_min_confidence``; it reads vulture's stdout only,
applies ``tools/dead_code_whitelist.txt`` by name, and lists what is left and
every entry that suppressed nothing. Exit 0 nothing listed, 1 something
listed, 2 could not run.

Behaviour is asserted in-process against ``main(argv, run=...)`` with the
vulture runner injected where the test is about parsing, against roots
planted under ``tmp_path``; one test runs the installed vulture for real
(DEC-RDS-013). The ``python tools/dead_code.py`` path is covered by
``test_gate_script_is_runnable_as_a_script``. The guards on where vulture and
its confidence may be named read this repository's own files.
"""

from __future__ import annotations

import ast
import importlib.metadata
import importlib.util
import re
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from tests.support import captured_logger, load_tool, read_pyproject

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOL = "dead_code.py"
CONFIDENCE_KEY = "dead_code_min_confidence"

#: The scripts that must not carry the configured confidence as a literal.
CONFIDENCE_FREE_SCRIPTS = ("dead_code.py", "spec_status.py")

#: A planted confidence that is not vulture's own level, so a test can tell
#: the configured value from a default.
PLANTED_CONFIDENCE = 70

Runner = Callable[[Path, Sequence[str]], tuple[int, str, str]]

#: Loaded at collection, so the tools logger's stderr handler -- attached once,
#: on first import -- is bound to a stream that outlives every test, never to
#: one test's ``capsys`` stream, which is closed when that test ends.
_COMMON = load_tool("common_dead_code", "_common.py")


def _tool() -> ModuleType:
    return load_tool("dead_code", TOOL)


def _configured_confidence() -> int:
    value = _COMMON.read_pyproject_int(
        REPO_ROOT / "pyproject.toml", "[tool.specgraph]", CONFIDENCE_KEY
    )
    assert isinstance(value, int), f"[tool.specgraph] {CONFIDENCE_KEY} is not an integer"
    return value


def _plant(
    root: Path,
    *,
    source: Sequence[str] = ("pkg",),
    confidence: int | None = PLANTED_CONFIDENCE,
    whitelist: str | None = None,
    usage: bool = True,
) -> Path:
    """A planted root: a ``pyproject.toml``, each tree holding one module, a
    ``tests/`` tree when ``usage``, and a whitelist when one is given."""
    entries = ", ".join(f'"{tree}"' for tree in source)
    lines = ["[tool.coverage.run]", f"source = [{entries}]", "", "[tool.specgraph]"]
    if confidence is not None:
        lines.append(f"{CONFIDENCE_KEY} = {confidence}")
    (root / "pyproject.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for tree in source:
        (root / tree).mkdir(parents=True, exist_ok=True)
        (root / tree / "mod.py").write_text("def used() -> int:\n    return 1\n", encoding="utf-8")
    if usage:
        (root / "tests").mkdir(exist_ok=True)
        (root / "tests" / "test_mod.py").write_text("def test_x() -> None:\n    pass\n", encoding="utf-8")
    if whitelist is not None:
        (root / "tools").mkdir(exist_ok=True)
        (root / "tools" / "dead_code_whitelist.txt").write_text(whitelist, encoding="utf-8")
    return root


def _canned(
    stdout: str = "", *, code: int = 3, stderr: str = "", calls: list[list[str]] | None = None
) -> Runner:
    """An injected vulture runner returning canned output, recording each argv."""

    def run(root: Path, argv: Sequence[str]) -> tuple[int, str, str]:
        if calls is not None:
            calls.append(list(argv))
        return code, stdout, stderr

    return run


def _never(root: Path, argv: Sequence[str]) -> tuple[int, str, str]:
    raise AssertionError(f"vulture must not be started: {list(argv)}")


def _main(root: Path, run: Runner) -> int:
    return int(_tool().main([TOOL, "--root", str(root)], run=run))


# --- where vulture and its confidence may be named (R-RDS-1, R-RDS-2) --------

_REQUIREMENT_NAME = re.compile(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def _vulture_dependency_problems(pyproject: dict[str, Any]) -> list[str]:
    """Each way the parsed ``pyproject`` breaks DEC-RDS-001, named."""
    project = pyproject.get("project", {})
    problems: list[str] = []
    for requirement in project.get("dependencies", []):
        name = _REQUIREMENT_NAME.match(requirement)
        if name and name.group(1).lower() == "vulture":
            problems.append(f"vulture is a runtime dependency: {requirement!r}")
    dev = [
        requirement
        for requirement in project.get("optional-dependencies", {}).get("dev", [])
        if (name := _REQUIREMENT_NAME.match(requirement)) and name.group(1).lower() == "vulture"
    ]
    if len(dev) != 1:
        problems.append(f"the dev extra lists vulture {len(dev)} times, not once: {dev}")
    for requirement in dev:
        specifier = requirement.split(";", 1)[0]
        if ">=" not in specifier:
            problems.append(f"vulture has no lower bound: {requirement!r}")
        if "==" in specifier or "~=" in specifier:
            problems.append(f"vulture is pinned: {requirement!r}")
        if re.search(r"<(?!=)|<=", specifier):
            problems.append(f"vulture has an upper bound: {requirement!r}")
    return problems


@pytest.mark.integration
def test_vulture_is_a_floored_dev_extra_and_never_a_runtime_dependency() -> None:
    """R-RDS-1, DEC-RDS-001: the dev extra floors vulture, pins nothing and
    caps nothing, and the runtime dependency list does not carry it."""
    assert _vulture_dependency_problems(read_pyproject()) == []


@pytest.mark.unit
@pytest.mark.parametrize(
    ("dev", "dependencies", "expected"),
    [
        (["vulture==2.16"], [], "vulture is pinned"),
        (["vulture~=2.15"], [], "vulture is pinned"),
        (["vulture>=2.15,<3"], [], "vulture has an upper bound"),
        (["vulture"], [], "vulture has no lower bound"),
        (["vulture>=2.15"], ["vulture>=2.15"], "vulture is a runtime dependency"),
        ([], [], "lists vulture 0 times"),
    ],
)
def test_an_exact_vulture_pin_or_a_runtime_vulture_is_named(
    dev: list[str], dependencies: list[str], expected: str
) -> None:
    """R-RDS-19: the dev-extra guard names a planted pin, cap, bare entry,
    runtime entry and absence, and is quiet on the floored form."""
    clean = {"project": {"dependencies": [], "optional-dependencies": {"dev": ["vulture>=2.15"]}}}
    assert _vulture_dependency_problems(clean) == []
    planted = {"project": {"dependencies": dependencies, "optional-dependencies": {"dev": dev}}}
    found = _vulture_dependency_problems(planted)
    assert any(expected in item for item in found), found


_NAMES_VULTURE = re.compile(r"\bvulture\b", re.IGNORECASE)


def _lines_naming_vulture(label: str, text: str, *, recipe_lines_only: bool) -> list[str]:
    """``label:line`` for each line naming vulture; for a Makefile, recipe lines only."""
    return [
        f"{label}:{number}"
        for number, line in enumerate(text.splitlines(), 1)
        if (not recipe_lines_only or line.startswith("\t")) and _NAMES_VULTURE.search(line)
    ]


@pytest.mark.integration
def test_no_github_file_or_recipe_line_names_vulture() -> None:
    """R-RDS-1, C-RDS-3: the dev extra installs vulture and `tools/dead_code.py`
    runs it, so no workflow, Dependabot file or recipe line names it."""
    found: list[str] = []
    for path in sorted((REPO_ROOT / ".github").rglob("*")):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            found += _lines_naming_vulture(path.name, text, recipe_lines_only=False)
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    found += _lines_naming_vulture("Makefile", makefile, recipe_lines_only=True)
    assert found == []
    planted_workflow = "jobs:\n  lint:\n    steps:\n      - run: pip install vulture\n"
    assert _lines_naming_vulture("ci.yml", planted_workflow, recipe_lines_only=False) == ["ci.yml:4"]
    planted_recipe = "dead-code: ## Report vulture's list\n\tpython -m vulture tools\n"
    assert _lines_naming_vulture("Makefile", planted_recipe, recipe_lines_only=True) == [
        "Makefile:2"
    ]


def _integer_literals(source: str, value: int) -> list[int]:
    """The line of every integer constant in ``source`` equal to ``value``."""
    return [
        node.lineno
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant)
        and type(node.value) is int
        and node.value == value
    ]


@pytest.mark.integration
def test_the_confidence_lives_only_in_the_specgraph_table() -> None:
    """R-RDS-2, C-RDS-2: the confidence is an integer in `[tool.specgraph]`,
    there is no `[tool.vulture]` table for vulture to apply to the report's
    own run, and no report script carries the number."""
    confidence = _configured_confidence()
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert not re.search(r"^\[tool\.vulture[\].]", pyproject, re.MULTILINE)
    for script in CONFIDENCE_FREE_SCRIPTS:
        source = (REPO_ROOT / "tools" / script).read_text(encoding="utf-8")
        assert _integer_literals(source, confidence) == [], f"{script} carries {confidence}"
    assert _integer_literals(f"MIN_CONFIDENCE = {confidence}\n", confidence) == [1]


def _import_roots(path: Path) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            roots.add(node.module.split(".")[0])
    return roots


@pytest.mark.integration
def test_dead_code_imports_only_the_standard_library_and_common() -> None:
    """C-RDS-8, DEC-RDS-005: no vulture, no `openspec_graph`, no sibling but `_common`."""
    roots = _import_roots(REPO_ROOT / "tools" / TOOL)
    allowed = set(sys.stdlib_module_names) | {"__future__", "_common"}
    assert "_common" in roots
    assert roots - allowed == set()


# --- the run and its parsing (R-RDS-3, R-RDS-4) -------------------------------


@pytest.mark.integration
@pytest.mark.parametrize("usage", [True, False])
def test_the_confidence_is_read_from_the_specgraph_table_and_passed_to_vulture(
    tmp_path: Path, usage: bool
) -> None:
    """R-RDS-3: one process, `sys.executable -m vulture`, over every declared
    tree and `tests` when it exists, at the configured confidence."""
    root = _plant(tmp_path, source=("pkg", "tools"), usage=usage)
    calls: list[list[str]] = []
    assert _main(root, _canned(code=0, calls=calls)) == 0
    assert len(calls) == 1
    argv = calls[0]
    assert argv[:3] == [sys.executable, "-m", "vulture"]
    trees = ["pkg", "tools", "tests"] if usage else ["pkg", "tools"]
    assert argv[3:] == [*trees, "--min-confidence", str(PLANTED_CONFIDENCE)]
    assert "--whitelist" not in " ".join(argv)


@pytest.mark.integration
def test_findings_outside_the_reported_trees_are_dropped_and_tests_count_as_users(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """R-RDS-3, DEC-RDS-003: a finding under `tests/` is never listed."""
    root = _plant(tmp_path)
    stdout = (
        "tests/conftest.py:3: unused function '_fixture' (60% confidence)\n"
        "pkg/mod.py:7: unused function 'orphan' (60% confidence)\n"
        "pkgextra/mod.py:2: unused function 'sibling' (60% confidence)\n"
    )
    assert _main(root, _canned(stdout)) == 1
    out = capsys.readouterr().out
    assert "pkg/mod.py:7: unused function 'orphan' (60% confidence)" in out.splitlines()
    assert "_fixture" not in out and "sibling" not in out


@pytest.mark.integration
def test_a_whitelisted_name_is_suppressed_and_an_entry_suppressing_nothing_is_stale(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """R-RDS-4, R-RDS-6, DEC-RDS-004: applied by name after the run; an entry
    that hid nothing is listed, which alone makes the report non-empty."""
    whitelist = "# header\n\nwhitespace_split  # set for shlex to read\ngone  # once used\n"
    root = _plant(tmp_path, whitelist=whitelist)
    stdout = (
        "pkg/mod.py:4: unused attribute 'whitespace_split' (60% confidence)\n"
        "pkg/mod.py:9: unused attribute 'whitespace_split' (60% confidence)\n"
    )
    assert _main(root, _canned(stdout)) == 1
    out = capsys.readouterr().out
    assert "whitespace_split' (60%" not in out
    assert "stale whitelist entries:" in out
    stale = out.split("stale whitelist entries:", 1)[1]
    assert "gone" in stale and "whitespace_split" not in stale


@pytest.mark.integration
def test_unreachable_code_is_reported_and_never_whitelisted(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """R-RDS-4: a finding whose message names no symbol cannot be suppressed."""
    root = _plant(tmp_path, whitelist="return  # names the statement, not a symbol\n")
    stdout = (
        "pkg/mod.py:5: unreachable code after 'return' (100% confidence)\n"
        "pkg/mod.py:8: unsatisfiable 'if' condition (100% confidence)\n"
    )
    assert _main(root, _canned(stdout)) == 1
    out = capsys.readouterr().out.splitlines()
    assert "pkg/mod.py:5: unreachable code after 'return' (100% confidence)" in out
    assert "pkg/mod.py:8: unsatisfiable 'if' condition (100% confidence)" in out


@pytest.mark.integration
def test_windows_separators_in_vulture_output_name_the_same_tree(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """R-RDS-4: a backslash path is normalised before it is matched or listed."""
    root = _plant(tmp_path)
    stdout = (
        "pkg\\sub\\mod.py:3: unused function 'orphan' (60% confidence)\n"
        "tests\\test_mod.py:1: unused function 'test_x' (60% confidence)\n"
    )
    assert _main(root, _canned(stdout)) == 1
    out = capsys.readouterr().out
    assert "pkg/sub/mod.py:3: unused function 'orphan' (60% confidence)" in out.splitlines()
    assert "test_x" not in out


@pytest.mark.integration
def test_findings_are_sorted_by_path_then_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """R-RDS-4: listed in vulture's own form, sorted by path then line; a
    blank line on stdout is no finding and no error."""
    root = _plant(tmp_path, source=("pkg", "tools"))
    stdout = (
        "tools/a.py:2: unused function 'b' (60% confidence)\n\n"
        "pkg/mod.py:10: unused function 'c' (60% confidence)\n"
        "pkg/mod.py:9: unused function 'd' (60% confidence)\n"
    )
    assert _main(root, _canned(stdout)) == 1
    listed = [line for line in capsys.readouterr().out.splitlines() if "confidence)" in line]
    assert listed == [
        "pkg/mod.py:9: unused function 'd' (60% confidence)",
        "pkg/mod.py:10: unused function 'c' (60% confidence)",
        "tools/a.py:2: unused function 'b' (60% confidence)",
    ]


@pytest.mark.integration
def test_the_header_names_the_trees_the_confidence_the_version_and_the_entries(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """R-RDS-4: the first line says what was read, at what confidence, by which
    vulture, against how many whitelist entries."""
    whitelist = "alpha  # one\nbeta  # two\n"
    root = _plant(tmp_path, source=("pkg", "tools"), whitelist=whitelist)
    stdout = "pkg/mod.py:1: unused function 'alpha' (60% confidence)\n"
    stdout += "pkg/mod.py:2: unused function 'beta' (60% confidence)\n"
    assert _main(root, _canned(stdout)) == 0
    header = capsys.readouterr().out.splitlines()[0]
    assert "pkg, tools" in header
    assert f"confidence {PLANTED_CONFIDENCE}" in header
    assert f"vulture {importlib.metadata.version('vulture')}" in header
    assert "2 whitelist entries" in header


@pytest.mark.integration
def test_dead_code_exits_zero_when_nothing_is_listed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """R-RDS-5: no finding and no stale entry is exit 0 with a line saying so."""
    root = _plant(tmp_path)
    assert _main(root, _canned(code=0)) == 0
    out = capsys.readouterr().out
    assert "no unreferenced code and no stale whitelist entry" in out


@pytest.mark.integration
@pytest.mark.parametrize(
    ("code", "stdout", "stderr", "expected_exit"),
    [
        (0, "", "x.py:1: SyntaxWarning: invalid escape sequence '\\d'", 0),
        (
            3,
            "pkg/mod.py:7: unused function 'orphan' (60% confidence)\n",
            "x.py:1: SyntaxWarning: invalid escape sequence '\\d'",
            1,
        ),
        (1, "", "x.py:3: invalid syntax", 2),
    ],
    ids=["warning-beside-0", "warning-beside-3", "failure-exit-1"],
)
def test_vulture_stderr_is_logged_and_never_decides_the_exit(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
    code: int,
    stdout: str,
    stderr: str,
    expected_exit: int,
) -> None:
    """R-RDS-5, DEC-RDS-005: stderr goes to the DEBUG log; beside exit 0 or 3
    it decides nothing, and beside exit 1 it is carried in the exit-2 message."""
    root = _plant(tmp_path)
    with captured_logger(caplog, "planlint.tools"):
        assert _main(root, _canned(stdout, code=code, stderr=stderr)) == expected_exit
    assert stderr in caplog.text
    captured = capsys.readouterr()
    assert stderr not in captured.out
    printed = [line for line in captured.err.splitlines() if not line.startswith("DEBUG ")]
    if expected_exit == 2:
        assert any("vulture exited 1" in line and stderr in line for line in printed), printed
        return
    assert all(stderr not in line for line in printed), printed
    listed = [line for line in captured.out.splitlines() if "confidence)" in line]
    assert listed == [line for line in stdout.splitlines() if line]


Spoiler = Callable[[Path, pytest.MonkeyPatch], None]


def _undecodable_pyproject(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (root / "pyproject.toml").write_bytes(b"[tool.specgraph]\n\xff\n")


def _undecodable_whitelist(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (root / "tools" / "dead_code_whitelist.txt").write_bytes(b"alpha  # \xff\n")


def _unreadable_pyproject(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An injected `PermissionError`, as `tests/test_stage_citations.py` does:
    as root, a mode of 000 still reads."""
    original = Path.read_text

    def refuse(self: Path, *args: Any, **kwargs: Any) -> str:
        if self.name == "pyproject.toml":
            raise PermissionError(13, "Permission denied")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", refuse)


def _vulture_absent(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`find_spec` answers `None` for vulture alone, as on a runner without the
    dev extra."""
    original = importlib.util.find_spec

    def without_vulture(name: str, *args: Any, **kwargs: Any) -> Any:
        return None if name == "vulture" else original(name, *args, **kwargs)

    monkeypatch.setattr(importlib.util, "find_spec", without_vulture)


_CANNOT_RUN: dict[str, tuple[dict[str, Any], Runner, Spoiler | None, str]] = {
    "vulture-absent": ({}, _never, _vulture_absent, "vulture is not installed"),
    "confidence-absent": ({"confidence": None}, _never, None, CONFIDENCE_KEY),
    "no-source-tree": ({"source": ()}, _never, None, "source"),
    "vulture-exit-1": ({}, _canned(code=1, stderr="Error: bad"), None, "vulture exited 1"),
    "vulture-exit-2": ({}, _canned(code=2, stderr="usage: vulture"), None, "vulture exited 2"),
    "stdout-in-neither-shape": ({}, _canned("this is not a finding\n"), None, "neither shape"),
    "whitelist-line-without-reason": (
        {"whitelist": "commenters\n"}, _never, None, "dead_code_whitelist.txt"
    ),
    "undecodable-pyproject": ({}, _never, _undecodable_pyproject, "pyproject.toml"),
    "undecodable-whitelist": (
        {"whitelist": ""}, _never, _undecodable_whitelist, "dead_code_whitelist.txt"
    ),
    "unreadable-pyproject": ({}, _never, _unreadable_pyproject, "pyproject.toml"),
}


@pytest.mark.integration
@pytest.mark.parametrize("case", sorted(_CANNOT_RUN))
def test_dead_code_exits_two_when_it_cannot_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    case: str,
) -> None:
    """R-RDS-5, DEC-RDS-005: each precondition failure is exit 2 with its cause
    named and no traceback. An absent vulture is decided by `find_spec`
    before any process starts; a vulture that ran and failed carries its
    exit code."""
    plant, runner, spoil, expected = _CANNOT_RUN[case]
    root = _plant(tmp_path, **plant)
    if spoil is not None:
        spoil(root, monkeypatch)
    assert _main(root, runner) == 2
    err = capsys.readouterr().err
    assert "Traceback" not in err
    assert expected in err, err


@pytest.mark.integration
@pytest.mark.parametrize("shape", ["absent", "no-python"])
def test_a_declared_tree_that_is_absent_or_holds_no_python_exits_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], shape: str
) -> None:
    """R-RDS-5, DEC-RDS-005: vulture reads an empty tree as clean, so the
    script refuses one before any process starts, naming it."""
    root = _plant(tmp_path, source=("pkg", "lib"))
    (root / "lib" / "mod.py").unlink()
    if shape == "absent":
        (root / "lib").rmdir()
    else:
        (root / "lib" / "README.md").write_text("# no python here\n", encoding="utf-8")
    assert _main(root, _never) == 2
    err = capsys.readouterr().err
    assert "tree lib/" in err and "Traceback" not in err


# --- the whitelist binds something (R-RDS-7) ----------------------------------


@pytest.mark.integration
def test_every_dead_code_whitelist_entry_names_a_binding_in_a_reported_tree() -> None:
    """R-RDS-7, DEC-RDS-004: the deterministic half of staleness, by `ast` on
    the real tree with no vulture process -- an entry whose symbol was
    deleted or renamed fails here, whatever vulture's release."""
    tool = _tool()
    assert (REPO_ROOT / "tools" / "dead_code_whitelist.txt").is_file()
    assert tool.unbound_whitelist_entries(REPO_ROOT) == []


@pytest.mark.integration
def test_a_whitelist_entry_naming_no_binding_is_named(tmp_path: Path) -> None:
    """R-RDS-7, R-RDS-19: every binding form counts, and only an entry naming
    none of them is returned."""
    whitelist = "".join(
        f"{name}  # planted\n"
        for name in ("func", "Klass", "method", "local", "attr", "alias", "param", "ghost")
    )
    root = _plant(tmp_path, whitelist=whitelist)
    (root / "pkg" / "bindings.py").write_text(
        "import os.path as alias\n\n\n"
        "def func(param):\n    local = param\n    return local\n\n\n"
        "class Klass:\n    def method(self):\n        self.attr = alias\n",
        encoding="utf-8",
    )
    assert _tool().unbound_whitelist_entries(root) == ["ghost"]


# --- the installed vulture, for real (AC-RDS-6) -------------------------------


@pytest.mark.integration
def test_the_installed_vulture_reports_a_planted_unused_function(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """R-RDS-3, R-RDS-5, DEC-RDS-001: the real process, at the configured
    confidence, lists an unused function under a reported tree and exits 1;
    once a planted test calls it, the same tree exits 0. No skip: vulture is a
    dev extra, as hypothesis is (DEC-RDS-013)."""
    root = _plant(tmp_path, confidence=_configured_confidence(), usage=False)
    (root / "pkg" / "mod.py").write_text(
        "def planted_unused_function() -> int:\n    return 1\n", encoding="utf-8"
    )
    run = _tool().run_vulture
    assert _main(root, run) == 1
    assert "unused function 'planted_unused_function'" in capsys.readouterr().out
    (root / "tests").mkdir()
    (root / "tests" / "test_planted.py").write_text(
        "from pkg.mod import planted_unused_function\n\n\n"
        "def test_planted() -> None:\n    assert planted_unused_function() == 1\n",
        encoding="utf-8",
    )
    assert _main(root, run) == 0
    assert "no unreferenced code and no stale whitelist entry" in capsys.readouterr().out
