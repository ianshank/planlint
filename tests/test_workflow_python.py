"""One Python default per workflow, the experimental leg, the classifiers and the docs row.

Moved from ``tests/test_workflow_hardening.py`` by ``shape-the-test-suite`` (R-TSS-2):
``harden-ci-workflows`` R-HCW-8 to R-HCW-11.
"""

from __future__ import annotations

import re
import textwrap
from collections.abc import Iterable

import pytest

from tests.support import read_pyproject, workflow_job_blocks
from tests.workflow_support import (
    ACTION_YML,
    DOCKERFILE,
    HOOKS_DOC,
    WORKFLOWS,
    _ci_text,
    _code_lines,
    _dockerfile_from,
    _indent,
    _job_level_keys,
    _rel,
    _top_level_block,
)


def _version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))

_PY_LITERAL = re.compile(r"^\s*-?\s*python-version:\s*[\"'](\d+\.\d+)[\"']\s*$")

def _quoted_version_literals(text: str) -> list[tuple[int, str]]:
    """``(line, value)`` for every single quoted ``python-version:`` literal
    outside ``strategy.matrix`` -- the list and its ``include:`` entries."""
    found: list[tuple[int, str]] = []
    matrix_indent: int | None = None
    for number, code in _code_lines(text):
        indent = _indent(code)
        if matrix_indent is not None and indent <= matrix_indent:
            matrix_indent = None
        if code.strip() == "matrix:":
            matrix_indent = indent
            continue
        if matrix_indent is not None:
            continue
        match = _PY_LITERAL.match(code)
        if match:
            found.append((number, match.group(1)))
    return found

def _matrix_versions(ci_text: str) -> tuple[set[str], set[str]]:
    """``(hard, experimental)`` Python versions of the ``test`` matrix."""
    test = workflow_job_blocks(ci_text).get("test", "")
    hard: set[str] = set()
    experimental: set[str] = set()
    listed = re.search(r"^\s*python-version:\s*\[([^\]]*)\]", test, re.MULTILINE)
    if listed:
        hard |= set(re.findall(r"[\"'](\d+\.\d+)[\"']", listed.group(1)))
    lines = _code_lines(test)
    include_indent: int | None = None
    entry: dict[str, str] | None = None

    def close() -> None:
        if entry and "python-version" in entry:
            target = experimental if entry.get("experimental") == "true" else hard
            target.add(entry["python-version"].strip("\"'"))

    for _, code in lines:
        indent = _indent(code)
        if include_indent is not None and indent <= include_indent:
            close()
            entry = None
            include_indent = None
        if code.strip() == "include:":
            include_indent = indent
            continue
        if include_indent is None:
            continue
        stripped = code.strip()
        if stripped.startswith("- "):
            close()
            entry = {}
            stripped = stripped[2:]
        if entry is not None:
            name, _, value = stripped.partition(":")
            entry[name.strip()] = value.strip()
    close()
    return hard, experimental

def _experimental_leg_offenders(ci_text: str) -> list[str]:
    keys = _job_level_keys(workflow_job_blocks(ci_text).get("test", ""))
    flag = keys.get("continue-on-error")
    _, experimental = _matrix_versions(ci_text)
    offenders = []
    if flag is not None and flag.lower() in ("true", "false"):
        offenders.append(f"test: job-level continue-on-error is the literal `{flag}`; it softens every leg")
    if experimental and (flag is None or "matrix.experimental" not in flag):
        offenders.append(
            f"test: experimental leg(s) {sorted(experimental)} without a job-level "
            "continue-on-error on matrix.experimental"
        )
    if not experimental and flag is not None:
        offenders.append("test: continue-on-error is set but no leg is experimental; remove it")
    return offenders

def _workflow_env(text: str, key: str) -> str | None:
    env = _top_level_block(text, "env")
    if env is None or key not in env:
        return None
    return env[key].strip("\"'")

def _action_input_default(text: str, name: str) -> str | None:
    lines = _code_lines(text)
    for index, (_, code) in enumerate(lines):
        if code.strip() != f"{name}:" or _indent(code) != 2:
            continue
        for _, nested in lines[index + 1:]:
            if _indent(nested) <= 2:
                break
            key, _, value = nested.strip().partition(":")
            if key.strip() == "default":
                return value.strip().strip("\"'")
    return None

def _dockerfile_tag_version(text: str) -> str | None:
    found = _dockerfile_from(text)
    if not found:
        return None
    match = re.match(r"^python:(\d+\.\d+)-slim(?:@|$)", found[1])
    return match.group(1) if match else None

def _classifier_versions(classifiers: Iterable[str]) -> set[str]:
    return {
        m.group(1)
        for c in classifiers
        if (m := re.fullmatch(r"Programming Language :: Python :: (\d+\.\d+)", c))
    }

def _hooks_test_row_bounds(hooks_text: str) -> tuple[str, str] | None:
    # The row writes its range with an en dash; a hyphen is accepted too.
    dashes = "\u2013-"
    pattern = rf"^\|\s*`test`\s*\((\d+\.\d+)\s*[{dashes}]\s*(\d+\.\d+)\)"
    match = re.search(pattern, hooks_text, re.MULTILINE)
    return (match.group(1), match.group(2)) if match else None

# --- R-HCW-8 / R-HCW-9: one Python default per workflow, agreed everywhere --


@pytest.mark.integration
def test_no_quoted_python_version_literal_outside_env_and_matrix() -> None:
    """AC-HCW-11: every single-version step reads env.PYTHON_DEFAULT."""
    offenders = []
    for workflow in WORKFLOWS:
        text = workflow.read_text(encoding="utf-8")
        assert _workflow_env(text, "PYTHON_DEFAULT"), f"{_rel(workflow)} declares no env.PYTHON_DEFAULT"
        offenders += [f'{_rel(workflow)}:{n} python-version: "{v}"' for n, v in _quoted_version_literals(text)]
    assert not offenders, "\n".join(offenders)

@pytest.mark.unit
def test_a_pasted_python_literal_is_named_with_file_and_line() -> None:
    """AC-HCW-12 (non-success): the pasted literal is reported; the matrix
    list, the include: leg and a comment are not."""
    body = textwrap.dedent(
        """\
        jobs:
          test:
            strategy:
              matrix:
                python-version: ["3.10", "3.11"]
                include:
                  - python-version: "3.14"
                    experimental: true
            steps:
              # python-version: "3.12" used to be here
              - uses: actions/setup-python@v7
                with:
                  python-version: "3.12"
        """
    )
    assert _quoted_version_literals(body) == [(13, "3.12")]

@pytest.mark.integration
def test_the_default_python_agrees_across_workflows_action_and_dockerfile() -> None:
    """AC-HCW-13: the two env values, the action's input default and the
    Dockerfile tag are one version."""
    sources: dict[str, str | None] = {}
    for workflow in WORKFLOWS:
        sources[f"{_rel(workflow)} env.PYTHON_DEFAULT"] = _workflow_env(
            workflow.read_text(encoding="utf-8"), "PYTHON_DEFAULT"
        )
    sources[f"{_rel(ACTION_YML)} inputs.python-version.default"] = _action_input_default(
        ACTION_YML.read_text(encoding="utf-8"), "python-version"
    )
    sources["Dockerfile FROM tag"] = _dockerfile_tag_version(DOCKERFILE.read_text(encoding="utf-8"))
    missing = [name for name, value in sources.items() if value is None]
    assert not missing, f"no Python default found in: {missing}"
    assert len(set(sources.values())) == 1, "\n".join(f"{k}: {v}" for k, v in sources.items())

@pytest.mark.integration
def test_the_default_python_is_a_hard_matrix_leg() -> None:
    """AC-HCW-13: the interpreter every single-version job runs on is one the
    matrix tests as a hard gate, not an advisory leg."""
    default = _workflow_env(_ci_text(), "PYTHON_DEFAULT")
    hard, experimental = _matrix_versions(_ci_text())
    assert default in hard, f"PYTHON_DEFAULT {default!r} is not a hard matrix leg; hard={sorted(hard)} experimental={sorted(experimental)}"

@pytest.mark.unit
def test_a_disagreeing_default_is_named() -> None:
    assert _action_input_default('inputs:\n  python-version:\n    description: x\n    default: "3.11"\n', "python-version") == "3.11"
    assert _dockerfile_tag_version("FROM python:3.12-slim@sha256:" + "0" * 64 + "\n") == "3.12"
    assert _workflow_env('env:\n  PYTHON_DEFAULT: "3.13"\njobs:\n', "PYTHON_DEFAULT") == "3.13"

# --- R-HCW-10 / R-HCW-11: the experimental leg, the classifiers, the docs ---


@pytest.mark.integration
def test_the_experimental_leg_is_an_expression_not_a_job_literal() -> None:
    """AC-HCW-14: an experimental leg rides `continue-on-error: ${{
    matrix.experimental || false }}`; a job-level literal would soften every
    leg at once."""
    assert not _experimental_leg_offenders(_ci_text()), "\n".join(_experimental_leg_offenders(_ci_text()))

@pytest.mark.unit
def test_a_job_literal_continue_on_error_is_named() -> None:
    body = textwrap.dedent(
        """\
        jobs:
          test:
            runs-on: ubuntu-latest
            continue-on-error: true
            strategy:
              matrix:
                python-version: ["3.12"]
            steps:
              - continue-on-error: true
                run: true
        """
    )
    offenders = _experimental_leg_offenders(body)
    assert "test: job-level continue-on-error is the literal `true`; it softens every leg" in offenders, offenders

@pytest.mark.unit
def test_matrix_versions_split_hard_from_experimental() -> None:
    body = textwrap.dedent(
        """\
        jobs:
          test:
            strategy:
              matrix:
                python-version: ["3.10", "3.13"]
                include:
                  - python-version: "3.14"
                    experimental: true
                  - python-version: "3.9"
            steps: []
        """
    )
    assert _matrix_versions(body) == ({"3.10", "3.13", "3.9"}, {"3.14"})

@pytest.mark.integration
def test_classifiers_equal_the_hard_matrix_legs() -> None:
    """AC-HCW-15: a classifier is a promise, so the set equals the hard legs
    -- no more (an untested promise) and no fewer (an unannounced support)."""
    hard, _ = _matrix_versions(_ci_text())
    classified = _classifier_versions(read_pyproject()["project"]["classifiers"])
    assert classified == hard, (
        f"classifiers without a hard leg: {sorted(classified - hard)}; "
        f"hard legs without a classifier: {sorted(hard - classified)}"
    )

@pytest.mark.integration
def test_hooks_test_row_names_the_matrix_bounds() -> None:
    """AC-HCW-15: docs/hooks.md's `test` row states the lowest and highest
    hard leg, read from the matrix rather than typed twice."""
    hard, _ = _matrix_versions(_ci_text())
    bounds = _hooks_test_row_bounds(HOOKS_DOC.read_text(encoding="utf-8"))
    assert bounds is not None, "docs/hooks.md has no `test` (low-high) row"
    expected = (min(hard, key=_version_key), max(hard, key=_version_key))
    assert bounds == expected, f"docs/hooks.md names {bounds}, the matrix's hard legs span {expected}"

@pytest.mark.unit
def test_a_classifier_or_row_drift_is_named() -> None:
    """AC-HCW-16 (non-success)."""
    assert _classifier_versions(["Programming Language :: Python :: 3.12", "Programming Language :: Python :: 3"]) == {"3.12"}
    assert _hooks_test_row_bounds("| `test` (3.10\u20133.13) | push |") == ("3.10", "3.13")
    assert _hooks_test_row_bounds("| `test` | push |") is None
