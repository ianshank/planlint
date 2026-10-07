"""The workflows' posture: least privilege, bounded timeouts, concurrency, the guard's silence, attestations.

Moved from ``tests/test_workflow_hardening.py`` by ``shape-the-test-suite`` (R-TSS-2):
``harden-ci-workflows`` R-HCW-4 to R-HCW-7 and C-HCW-2, and the attestations guard of
``prepare-release-0-3-0`` R-REL-10 (DEC-REL-011, DEC-TSS-016).
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

import pytest

from tests.support import load_tool, workflow_job_blocks
from tests.workflow_support import (
    PULL_REQUEST_TEST,
    PYPROJECT,
    RELEASE_YML,
    TIMEOUT_KEYS,
    TIMEOUT_SECTION,
    WORKFLOWS,
    _ci_text,
    _code_lines,
    _job_permission_blocks,
    _rel,
    _top_level_block,
    _uncommented_permission_blocks,
)


def _write_permissions(text: str) -> list[str]:
    offenders = [
        f"line {number}: {code.strip()}"
        for number, code in _code_lines(text)
        if re.match(r"^\s*permissions:\s*write-all\s*$", code)
    ]
    top = _top_level_block(text, "permissions") or {}
    offenders += [f"top-level {k}: {v}" for k, v in top.items() if "write" in v]
    for job, entries, _ in _job_permission_blocks(text):
        offenders += [f"job {job}: {k}: {v}" for k, v in entries.items() if "write" in v]
    return offenders

def _timeout_range(pyproject: Path = PYPROJECT) -> tuple[int, int]:
    """The configured ``[min, max]``; a missing key is a failure, never a skip."""
    common = load_tool("_common", "_common.py")
    values = []
    for key in TIMEOUT_KEYS:
        value = common.read_pyproject_int(pyproject, TIMEOUT_SECTION, key)
        assert value is not None, (
            f"{pyproject}: {TIMEOUT_SECTION} has no `{key}`; the timeout guard cannot run"
        )
        values.append(value)
    low, high = values
    assert low < high, f"{TIMEOUT_KEYS[0]} {low} is not below {TIMEOUT_KEYS[1]} {high}"
    return low, high

_TIMEOUT = re.compile(r"^    timeout-minutes:\s*(\S+)\s*$")

def _timeout_offenders(text: str, label: str, low: int, high: int) -> list[str]:
    offenders = []
    for job, body in workflow_job_blocks(text).items():
        found = next((m.group(1) for _, c in _code_lines(body) if (m := _TIMEOUT.match(c))), None)
        if found is None:
            offenders.append(f"{label}: job {job} has no timeout-minutes")
        elif not found.isdigit():
            offenders.append(f"{label}: job {job} timeout-minutes is not a literal: {found}")
        elif not low <= int(found) <= high:
            offenders.append(f"{label}: job {job} timeout-minutes {found} is outside {low}..{high}")
    return offenders

def _concurrency_offenders(text: str) -> list[str]:
    block = _top_level_block(text, "concurrency")
    if block is None:
        return ["no top-level concurrency: block"]
    offenders = []
    group = block.get("group", "")
    for token in ("github.workflow", PULL_REQUEST_TEST, "github.ref", "github.sha"):
        if token not in group:
            offenders.append(f"concurrency.group lacks `{token}`: {group!r}")
    cancel = block.get("cancel-in-progress", "")
    if cancel.lower() in ("", "true", "false"):
        offenders.append(f"cancel-in-progress is a literal, not the pull-request expression: {cancel!r}")
    elif PULL_REQUEST_TEST not in cancel:
        offenders.append(f"cancel-in-progress does not switch on the event: {cancel!r}")
    return offenders

# --- R-HCW-4 / R-HCW-5: least privilege, stated and commented ---------------


def test_ci_declares_read_only_permissions_at_the_top() -> None:
    """AC-HCW-4: the default for every job is `contents: read` and nothing
    else; a job widens only in its own block."""
    assert _top_level_block(_ci_text(), "permissions") == {"contents": "read"}

def test_no_write_permission_anywhere_in_ci() -> None:
    """AC-HCW-4: no `write` under any permissions: block in ci.yml."""
    assert not _write_permissions(_ci_text()), _write_permissions(_ci_text())

def test_every_job_level_permissions_block_carries_a_comment() -> None:
    """AC-HCW-5: a widening (or a narrowing) names its reason, in a comment
    somewhere above it inside the same job."""
    offenders = []
    for workflow in WORKFLOWS:
        offenders += _uncommented_permission_blocks(workflow.read_text(encoding="utf-8"), _rel(workflow))
    assert not offenders, "\n".join(offenders)

def test_security_reads_pull_requests_and_posts_no_comments() -> None:
    """AC-HCW-6: gitleaks-action's commit listing needs `pull-requests: read`;
    comments are off so no write permission is ever needed."""
    blocks = {job: entries for job, entries, _ in _job_permission_blocks(_ci_text())}
    assert blocks.get("security") == {"contents": "read", "pull-requests": "read"}, blocks.get("security")
    security = workflow_job_blocks(_ci_text())["security"]
    assert re.search(r'^\s*GITLEAKS_ENABLE_COMMENTS:\s*"false"\s*$', security, re.MULTILINE), security

@pytest.mark.parametrize(
    "label, body, expected",
    [
        (
            "no top-level block",
            "name: CI\non: push\njobs:\n  t:\n    runs-on: ubuntu-latest\n",
            None,
        ),
        (
            "a write under a job",
            (
                "name: CI\npermissions:\n  contents: read\njobs:\n  t:\n    # why\n    permissions:\n"
                "      pull-requests: write\n    runs-on: ubuntu-latest\n"
            ),
            "job t: pull-requests: write",
        ),
        (
            "write-all scalar",
            "name: CI\npermissions: write-all\njobs:\n  t:\n    runs-on: ubuntu-latest\n",
            "permissions: write-all",
        ),
    ],
)
def test_a_permissive_workflow_is_named(label: str, body: str, expected: str | None) -> None:
    """AC-HCW-5 (non-success): the three ways to be too permissive."""
    if expected is None:
        assert _top_level_block(body, "permissions") is None, label
    else:
        offenders = _write_permissions(body)
        assert offenders and expected in offenders[0], (label, offenders)

def test_an_uncommented_job_permissions_block_is_named() -> None:
    body = "jobs:\n  quiet:\n    runs-on: ubuntu-latest\n    permissions:\n      contents: read\n"
    offenders = _uncommented_permission_blocks(body, "planted.yml")
    assert offenders == ["planted.yml: job quiet has a permissions: block with no comment line above it in the job"]

# --- R-HCW-6: every job has a bounded timeout -------------------------------


def test_every_job_in_every_workflow_has_a_timeout_inside_the_range() -> None:
    """AC-HCW-8: a hung step costs minutes, not GitHub's six-hour default."""
    low, high = _timeout_range()
    offenders = []
    for workflow in WORKFLOWS:
        offenders += _timeout_offenders(workflow.read_text(encoding="utf-8"), _rel(workflow), low, high)
    assert not offenders, "\n".join(offenders)

def test_a_job_without_a_timeout_is_named() -> None:
    body = "jobs:\n  fast:\n    runs-on: ubuntu-latest\n    timeout-minutes: 10\n  slow:\n    runs-on: ubuntu-latest\n"
    assert _timeout_offenders(body, "planted.yml", 5, 45) == ["planted.yml: job slow has no timeout-minutes"]

def test_a_timeout_above_the_ceiling_is_named() -> None:
    body = "jobs:\n  typo:\n    runs-on: ubuntu-latest\n    timeout-minutes: 300\n"
    assert _timeout_offenders(body, "planted.yml", 5, 45) == [
        "planted.yml: job typo timeout-minutes 300 is outside 5..45"
    ]

def test_a_missing_timeout_range_key_fails_rather_than_skips(tmp_path: Path) -> None:
    """AC-HCW-9: a pyproject without the range is a misconfiguration, so the
    guard fails loudly instead of passing vacuously."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.specgraph]\nci_job_timeout_minutes_min = 5\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="ci_job_timeout_minutes_max"):
        _timeout_range(pyproject)

# --- R-HCW-7: concurrency that never cancels a push to main -----------------


def test_ci_concurrency_never_cancels_a_push() -> None:
    """AC-HCW-10: pull requests group by ref and cancel in progress; every
    other event groups by SHA, so a `main` run is neither cancelled nor left
    pending to be superseded."""
    assert not _concurrency_offenders(_ci_text()), "\n".join(_concurrency_offenders(_ci_text()))

@pytest.mark.parametrize(
    "label, block, expected",
    [
        (
            "literal true",
            "concurrency:\n  group: ${{ github.workflow }}-${{ github.event_name == 'pull_request' && github.ref || github.sha }}\n  cancel-in-progress: true\n",
            "cancel-in-progress is a literal",
        ),
        (
            "ref alone",
            "concurrency:\n  group: ${{ github.workflow }}-${{ github.ref }}\n  cancel-in-progress: ${{ github.event_name == 'pull_request' }}\n",
            "lacks `github.sha`",
        ),
        ("absent", "name: CI\n", "no top-level concurrency: block"),
    ],
)
def test_a_cancelling_or_missing_concurrency_group_is_named(label: str, block: str, expected: str) -> None:
    """AC-HCW-10 (non-success)."""
    offenders = _concurrency_offenders(f"name: CI\n{block}jobs:\n  t:\n    runs-on: ubuntu-latest\n")
    assert any(expected in offender for offender in offenders), (label, offenders)

def test_release_has_no_concurrency_group() -> None:
    """AC-HCW-10: a tag is its own ref and must never be cancelled."""
    assert _top_level_block(RELEASE_YML.read_text(encoding="utf-8"), "concurrency") is None

# --- C-HCW-2: the thresholds guard is quiet on every new line ---------------


def test_threshold_guard_stays_quiet_on_timeouts_env_and_concurrency(tmp_path: Path) -> None:
    """AC-HCW-27: nothing this package adds to a workflow registers with
    tools/check_no_hardcoded_thresholds.py, and a real floor still does."""
    guard = load_tool("thresholds_quiet", "check_no_hardcoded_thresholds.py")
    planted = tmp_path / "ci.yml"
    planted.write_text(
        textwrap.dedent(
            """\
            name: CI
            on: push
            permissions:
              contents: read
            concurrency:
              group: ${{ github.workflow }}-${{ github.event_name == 'pull_request' && github.ref || github.sha }}
              cancel-in-progress: ${{ github.event_name == 'pull_request' }}
            env:
              PYTHON_DEFAULT: "3.12"
            jobs:
              test:
                runs-on: ubuntu-latest
                timeout-minutes: 15
                continue-on-error: ${{ matrix.experimental || false }}
                steps:
                  - run: make test
            """
        ),
        encoding="utf-8",
    )
    assert guard.check_workflow(planted) == []
    planted.write_text(planted.read_text(encoding="utf-8") + "      - run: pytest --cov-fail-under=90\n", encoding="utf-8")
    assert guard.check_workflow(planted), "a planted coverage floor went unreported"

def test_threshold_guard_stays_quiet_on_a_sha_pinned_uses_line(tmp_path: Path) -> None:
    """AC-ASP-16: a `uses: owner/repo@<sha> # vX.Y.Z` line registers nothing
    with tools/check_no_hardcoded_thresholds.py, and a real floor still does."""
    guard = load_tool("thresholds_quiet_sha", "check_no_hardcoded_thresholds.py")
    planted = tmp_path / "ci.yml"
    planted.write_text(
        f"jobs:\n  t:\n    steps:\n      - uses: actions/checkout@{'a' * 40} # v7.0.1\n"
        "      - run: make test\n",
        encoding="utf-8",
    )
    assert guard.check_workflow(planted) == []
    planted.write_text(
        planted.read_text(encoding="utf-8") + "      - run: pytest --cov-fail-under=90\n", encoding="utf-8"
    )
    assert guard.check_workflow(planted), "a planted coverage floor went unreported"

# --- the publish step's attestations input (prepare-release-0-3-0, R-REL-10) --


def _publisher_step_declares(release_text: str, key: str, value: str) -> bool:
    """Whether the publish job's pypa/gh-action-pypi-publish step has ``key: value`` under ``with:``.

    Read from the comment-stripped job block, so a comment that merely mentions
    the input satisfies nothing, and by indentation, so the input has to be a
    direct child of the step's ``with:`` mapping: a same-named key beside
    ``with:`` is one GitHub ignores and this guard must not credit. Says
    nothing about the step's ``uses:`` ref, which is the pin guards' to hold
    (DEC-REL-011).
    """
    jobs = workflow_job_blocks(release_text)
    publish = jobs.get("publish", "")
    code = "\n".join(line for _, line in _code_lines(publish))
    steps = re.split(r"^(?=\s*-\s+(?:uses|name):)", code, flags=re.MULTILINE)
    publisher = [step for step in steps if "pypa/gh-action-pypi-publish" in step]
    if len(publisher) != 1:
        return False
    lines = publisher[0].splitlines()
    with_at = [i for i, line in enumerate(lines) if re.fullmatch(r"\s*with:\s*", line)]
    if len(with_at) != 1:
        return False
    with_indent = len(lines[with_at[0]]) - len(lines[with_at[0]].lstrip())
    wanted = re.compile(rf"\s*{re.escape(key)}:\s*{re.escape(value)}\s*")
    for line in lines[with_at[0] + 1 :]:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= with_indent:
            break  # the with: mapping ended; a later sibling key is not an input
        if wanted.fullmatch(line):
            return True
    return False

def test_publish_declares_attestations_explicitly() -> None:
    """`attestations: true` is written on the publish step, not inherited from a version's default.

    The default has been `true` since v1.11.0 of the action; a SHA pin is a
    version, and a re-pin can land on one where it is not. The explicit input
    survives the pin and states the dependency (R-REL-10, DEC-REL-006).
    """
    text = RELEASE_YML.read_text(encoding="utf-8")
    assert _publisher_step_declares(text, "attestations", "true"), (
        "release.yml's publish step must declare `attestations: true` under `with:`"
    )
    # A step that only mentions the input in a comment, or carries it under
    # another step, does not count.
    planted = text.replace("          attestations: true", "          # attestations: true")
    assert not _publisher_step_declares(planted, "attestations", "true"), (
        "a commented-out input must not satisfy the guard"
    )
    # The key beside `with:` rather than under it: GitHub ignores it, and so
    # must the guard, even though a `with:` block is present on the step.
    sibling = text.replace(
        "        with:\n          attestations: true",
        "        attestations: true\n        with:\n          verbose: true",
    )
    assert "        attestations: true\n        with:" in sibling, "the planted shape was not applied"
    assert not _publisher_step_declares(sibling, "attestations", "true"), (
        "an input beside with: instead of under it must not satisfy the guard"
    )
