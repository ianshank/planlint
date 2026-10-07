"""Planted inputs for the static-check ratchets: each helper red, then quiet.

``ratchet-test-types-and-docstrings`` R-TDR-11: every helper in
``tests/ratchet_support.py`` that ``tests/test_static_ratchets.py`` runs on the
tree is shown here naming its planted violation, and staying quiet on the
matching well-formed shape, so a guard green on the tree is not green by
accident. Moved out of that module by DEC-TDR-012, its line budget.

Planted comment text lives in one-line strings with ``\\n`` escapes: no line of
this module begins with mypy's inline-configuration prefix, no planted comment
is a real one, and the names and conditions the guards refuse appear here only
inside strings -- so this module passes the guards it plants for.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Collection, Mapping
from pathlib import Path
from typing import Any

import pytest

from tests.ratchet_support import (
    ALLOWED_VERSION_CHECK,
    MYPY_FIXED,
    MYPY_FLOOR,
    MYPY_TREES,
    TESTS_ENTRY,
    TYPECHECK_RECIPE,
    ceiling_problems,
    derive_config,
    derived_problems,
    dev_extra_problems,
    hidden_code,
    listed_codes,
    load_mypy_config,
    mypy_config_problems,
    mypy_errors,
    override_problems,
    platform_only,
    read_comments,
    run_environment,
    stub_problems,
    waiver_problems,
)

_MODULES = ("tests.support", "tests.test_graph")
_BASE: dict[str, Any] = {"strict": True, "warn_unreachable": True}
_GOOD_TABLE: dict[str, Any] = {"files": list(MYPY_TREES), "mypy_path": "tools", **MYPY_FIXED}
_X = "tests/test_x.py"
_NOTE = json.dumps({"file": "tests/a.py", "line": 1, "code": "attr-defined", "severity": "note"})
_WINDOWS = json.dumps({"file": "tests\\a.py", "line": 2, "code": "index", "severity": "error"})
_CODELESS = json.dumps({"file": "tests/a.py", "line": 3, "code": None, "severity": "error"})
_ERROR = {"file": "tests/a.py", "line": 2, "code": "index"}


def _toml(table: Mapping[str, Any]) -> str:
    lines = ["[tool.mypy]", *(f"{k} = {json.dumps(v)}" for k, v in table.items() if k != "overrides")]
    for entry in table.get("overrides", []):
        lines += ["[[tool.mypy.overrides]]", *(f"{k} = {json.dumps(v)}" for k, v in entry.items())]
    return "\n".join(lines) + "\n"


def _overrides(tmp_path: Path, *entries: dict[str, Any], listed: Collection[str] = ()) -> list[str]:
    config = tmp_path / "pyproject.toml"
    config.write_text(_toml({**_BASE, "overrides": list(entries)}), encoding="utf-8")
    return override_problems(*load_mypy_config(config), _MODULES, listed)


def _derived(tmp_path: Path, *entries: dict[str, Any], drop: str = "", add: str = "") -> list[str]:
    table = {**_BASE, "overrides": list(entries)}
    (tmp_path / "pyproject.toml").write_text(_toml(table), encoding="utf-8")
    (tmp_path / "derived.ini").write_text(derive_config(table).replace(drop, "") + add, encoding="utf-8")
    source, _ = load_mypy_config(tmp_path / "pyproject.toml")
    derived, stderr = load_mypy_config(tmp_path / "derived.ini")
    return [stderr] * bool(stderr) + derived_problems(derived, source, _MODULES)


def _counted(stdout: str, stderr: str = "", returncode: int = 1) -> list[str]:
    errors, problems = mypy_errors(stdout, stderr, returncode)
    return [f"counted {error['code']} in {error['file']}" for error in errors] + problems


def _waivers(text: str, *recorded: tuple[str, str, str], listed: Collection[str] = ("no-untyped-def",)) -> list[str]:
    ignores, problems = read_comments(_X, text)
    return problems + waiver_problems(ignores, recorded, listed)


_TESTS = {"module": TESTS_ENTRY, "disable_error_code": ["index"]}
_SKIP = {"follow_imports": "skip"}
_PLANTED: dict[str, tuple[Callable[[Path], list[str]], str | None]] = {
    # (case) -> (planted input -> what the helper names, a substring it must name or None for quiet)
    "stale-code": (lambda _: ceiling_problems(["index"], {"index": 2}, {}), "stale"),
    "unlisted-code": (lambda _: ceiling_problems([], {}, {"index": 1}), "index occurs 1 times"),
    "above-ceiling": (lambda _: ceiling_problems(["index"], {"index": 1}, {"index": 2}), "above its ceiling of 1"),
    "below-ceiling": (lambda _: ceiling_problems(["index"], {"index": 3}, {"index": 2}), "lower index from 3 to 2"),
    "listed-without-ceiling": (lambda _: ceiling_problems(["index"], {}), "without a ceiling"),
    "ceiling-without-code": (lambda _: ceiling_problems([], {"index": 1}), "does not list"),
    "ceiling-exact": (lambda _: ceiling_problems(["index"], {"index": 2}, {"index": 2}), None),
    "recipe-without-config": (lambda _: mypy_config_problems(["python -m mypy"], _GOOD_TABLE), "names no configuration"),
    "recipe-with-path": (lambda _: mypy_config_problems([f"{TYPECHECK_RECIPE} tests"], _GOOD_TABLE), "passes paths"),
    "table-with-exclude": (lambda _: mypy_config_problems([TYPECHECK_RECIPE], {**_GOOD_TABLE, "exclude": "x"}), "sets exclude"),
    "wider-mypy-path": (lambda _: mypy_config_problems([TYPECHECK_RECIPE], {**_GOOD_TABLE, "mypy_path": ["tools", "tests"]}), "mypy_path"),
    "recipe-and-table": (lambda _: mypy_config_problems([TYPECHECK_RECIPE], {**_GOOD_TABLE, "mypy_path": ["tools"]}), None),
    "second-option": (lambda _: listed_codes([{**_TESTS, "ignore_errors": True}])[1], "beside disable_error_code"),
    "empty-list": (lambda _: listed_codes([{**_TESTS, "disable_error_code": []}])[1], "lists no code"),
    "two-entries": (lambda _: listed_codes([_TESTS, _TESTS])[1], "2 overrides"),
    "unlistable-code": (lambda _: listed_codes([{**_TESTS, "disable_error_code": ["misc"]}])[1], "misc is not"),
    "tests-entry": (lambda _: listed_codes([{**_TESTS, "module": [TESTS_ENTRY]}])[1], None),
    "slash-spelling": (lambda t: _overrides(t, {"module": "tests/test_graph", "disable_error_code": ["index"]}), "tests.test_graph: disables"),
    "comma-spelling": (lambda t: _overrides(t, {**_TESTS, "module": "openspec_graph.cli,tests.test_graph"}), "tests.test_graph: disables"),
    "list-spelling": (lambda t: _overrides(t, {**_TESTS, "module": ["openspec_graph.cli", "tests.test_graph"]}), "tests.test_graph: disables"),
    "mid-glob": (lambda t: _overrides(t, {**_TESTS, "module": "tests.*.test_graph"}), "tests.test_graph: disables"),
    "follow-imports": (lambda t: _overrides(t, {"module": "tests.test_graph", **_SKIP}), "tests.test_graph: follow_imports"),
    "relaxed-strict": (lambda t: _overrides(t, {"module": "tests.test_graph", "disallow_untyped_defs": False}), "disallow_untyped_defs"),
    "bare-star": (lambda t: _overrides(t, {**_TESTS, "module": "*"}), None),
    "package-follow-imports": (lambda t: _overrides(t, {"module": "openspec_graph.*", **_SKIP}), None),
    "listed-override": (lambda t: _overrides(t, _TESTS, listed=["index"]), None),
    "repeat-passes-the-comparison": (lambda t: _overrides(t, _TESTS, {**_TESTS, "module": "tests.test_graph"}, listed=["index"]), None),
    "derived-drops-an-option": (lambda t: _derived(t, _TESTS, drop="warn_unreachable = True\n"), "derived warn_unreachable"),
    "derived-keeps-tests-entry": (lambda t: _derived(t, _TESTS, add="[mypy-tests.*]\ndisable_error_code = index\n"), "derived, tests.test_graph"),
    "derived-keeps-a-repeat": (lambda t: _derived(t, _TESTS, {**_TESTS, "module": "tests.test_graph"}), "derived, tests.test_graph"),
    "derived": (lambda t: _derived(t, _TESTS, {"module": "tomli", "ignore_missing_imports": True}), None),
    "mypypath-dropped": (lambda _: sorted(set(run_environment({"MYPYPATH": "s", "COVERAGE_FILE": "c", "P": "p"})) - {"P"}), None),
    "note-not-counted": (lambda _: _counted(_NOTE + "\n"), None),
    "windows-error-counted": (lambda _: _counted(_WINDOWS + "\n"), "counted index in tests/a.py"),
    "non-json-line": (lambda _: _counted("Success: no issues found\n"), "not a JSON object"),
    "error-without-code": (lambda _: _counted(_CODELESS + "\n"), "without a code"),
    "nonempty-stderr": (lambda _: _counted("\n", stderr="Traceback"), "stderr"),
    "exit-two": (lambda _: _counted("\n", returncode=2), "exited 2"),
    "clean-run": (lambda _: _counted("\n", returncode=0), None),
    "platform-only": (lambda _: platform_only({"linux": [_ERROR], "win32": []}), "platform-only (linux)"),
    "platforms-agree": (lambda _: platform_only({"linux": [_ERROR], "win32": [_ERROR]}), None),
    "unrecorded-ignore": (lambda _: _waivers("def f(x):  # type: ignore[no-untyped-def, unused-ignore]\n"), "unrecorded waiver"),
    "waiver-gone": (lambda _: _waivers("x = 1\n", (_X, "index", "x = 1")), "no longer in the tree"),
    "two-codes": (lambda _: _waivers("x = 1  # type: ignore[index, arg-type, unused-ignore]\n"), "2 codes"),
    "unused-beside-enforced": (lambda _: _waivers("x = 1  # type: ignore[index, unused-ignore]\n", (_X, "index", "x = 1")), "does not list"),
    "listed-without-unused": (lambda _: _waivers("x = 1  # type: ignore[no-untyped-def]\n"), "needs unused-ignore"),
    "bare-ignore": (lambda _: _waivers("x = 1  # type: ignore\n", (_X, "", "x = 1")), "0 codes"),
    "moved-comment": (lambda _: _waivers("x = 1\ny = 2  # type: ignore[index]\n", (_X, "index", "x = 1")), "no longer in the tree"),
    "no-spaces-read": (lambda _: _waivers("x = 1  #type:ignore[index]\n"), "unrecorded waiver"),
    "enforced-waiver": (lambda _: _waivers("x = 1  # type: ignore[index]\n", (_X, "index", "x = 1")), None),
    "listed-waiver": (lambda _: _waivers("x = 1  # type: ignore[no-untyped-def, unused-ignore]\n", (_X, "no-untyped-def", "x = 1")), None),
    "mypy-comment": (lambda _: _waivers('x = 1\n# mypy: disable-error-code="no-untyped-def"\n'), "configures mypy"),
    "mypy-line-in-a-string": (lambda _: _waivers('"""Doc.\n# mypy: disable-error-code=x\n"""\n'), "reads as configuration"),
    "stub-in-package": (lambda _: stub_problems(["openspec_graph/graph.py", "openspec_graph/graph.pyi"]), "graph.pyi"),
    "stub-in-tests": (lambda _: stub_problems(["tests/support.pyi"]), "tests/support.pyi"),
    "no-type-check": (lambda _: hidden_code(_X, "from typing import no_type_check\n"), "no_type_check"),
    "type-checking": (lambda _: hidden_code(_X, "from typing import TYPE_CHECKING\n"), "TYPE_CHECKING"),
    "mypy-name": (lambda _: hidden_code(_X, "MYPY = False\nif not MYPY:\n    pass\n"), "MYPY"),
    "new-version": (lambda _: hidden_code(_X, "import sys\nif sys.version_info >= (3, 11):\n    pass\n"), "branch test"),
    "old-version": (lambda _: hidden_code(_X, "import sys\nif sys.version_info < (3, 10):\n    pass\n"), "branch test"),
    "platform": (lambda _: hidden_code(_X, "import sys\nif sys.platform == 'darwin':\n    pass\n"), "branch test"),
    "match-guard": (lambda _: hidden_code(_X, "import sys\nmatch 1:\n    case 1 if sys.platform == 'x':\n        pass\n"), "branch test"),
    "module-assert": (lambda _: hidden_code(_X, "import sys\nassert sys.platform == 'darwin'\n"), "branch test"),
    "second-check-at-the-site": (lambda _: hidden_code(ALLOWED_VERSION_CHECK[0], f"import sys\ndef {ALLOWED_VERSION_CHECK[1]}():\n    if sys.version_info >= (3, 11):\n        pass\n    assert sys.platform\n"), "branch test in read_pyproject"),
    "allowed-site": (lambda _: hidden_code(ALLOWED_VERSION_CHECK[0], f"import sys\ndef {ALLOWED_VERSION_CHECK[1]}():\n    if sys.version_info >= (3, 11):\n        pass\n"), None),
    "skipif-argument": (lambda _: hidden_code(_X, "import sys, pytest\n@pytest.mark.skipif(sys.platform == 'win32', reason='x')\ndef test_x():\n    pass\n"), None),
    "bare-mypy": (lambda _: dev_extra_problems(["mypy"]), "not floored exactly"),
    "pinned-mypy": (lambda _: dev_extra_problems(["mypy==1.11.0"]), "pins a version"),
    "lower-floor": (lambda _: dev_extra_problems(["mypy>=1.10"]), "not floored exactly"),
    "compatible-release": (lambda _: dev_extra_problems(["mypy~=1.11"]), "not floored exactly"),
    "pinned-tool": (lambda _: dev_extra_problems([f"mypy{MYPY_FLOOR}", "ruff==0.4.2"]), "pins a version"),
    "no-mypy": (lambda _: dev_extra_problems(["ruff"]), "0 dev-extra entries"),
    "floored-with-marker": (lambda _: dev_extra_problems([f"mypy{MYPY_FLOOR}", 'tomli; python_version == "3.10"']), None),
}


@pytest.mark.unit
@pytest.mark.parametrize("case", sorted(_PLANTED))
def test_a_planted_ratchet_violation_is_named(case: str, tmp_path: Path) -> None:
    """R-TDR-11 / AC-TDR-9: each helper names its planted violation and stays quiet
    on the well-formed shape, so a guard green on the tree is not green by accident."""
    plant, named = _PLANTED[case]
    problems = plant(tmp_path)
    if named is None:
        assert problems == [], problems
    else:
        assert any(named in problem for problem in problems), problems
