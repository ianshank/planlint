"""Guards for the shape of the CI workflows themselves (change package:
harden-ci-workflows).

Every guard here reads the files it judges and asserts a consistency
property, never a version string: a Dependabot bump must never have to edit a
test to pass it. Each guard collects every offender before asserting, so one
failure message lists them all with file, line and job (R-HCW-15). The
helpers take text or paths rather than reading the repository themselves, so
each guard is also run against a planted counter-example and shown red.
"""

from __future__ import annotations

import re
import textwrap
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pytest

from tests.support import load_tool, workflow_job_blocks

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
WORKFLOWS = sorted(WORKFLOWS_DIR.glob("*.yml"))
CI_YML = WORKFLOWS_DIR / "ci.yml"
RELEASE_YML = WORKFLOWS_DIR / "release.yml"
ACTION_YML = REPO_ROOT / ".github" / "actions" / "planlint" / "action.yml"
DOCKERFILE = REPO_ROOT / "Dockerfile"
DEPENDABOT = REPO_ROOT / ".github" / "dependabot.yml"
TEMPLATES = sorted((REPO_ROOT / "templates").glob("*.yml"))
README = REPO_ROOT / "README.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"
HOOKS_DOC = REPO_ROOT / "docs" / "hooks.md"

#: Every file whose third-party `uses:` refs must agree (R-HCW-1, R-HCW-2,
#: DEC-HCW-012): the workflows, the composite action, the adopter templates
#: and the README's copyable snippet.
ACTION_REF_SCAN: list[Path] = [*WORKFLOWS, ACTION_YML, *TEMPLATES, README]

#: This repository's own composite action, as adopters reference it. Its ref
#: is a commit SHA until the first public tag exists; that ref belongs to
#: tests/test_adopter_urls.py and docs/distribution-plan.md, not to this
#: module (C-HCW-3).
OWN_ACTION_PREFIX = "ianshank/planlint/"

TIMEOUT_SECTION = "[tool.specgraph]"
TIMEOUT_KEYS = ("ci_job_timeout_minutes_min", "ci_job_timeout_minutes_max")
PULL_REQUEST_TEST = "github.event_name == 'pull_request'"


# --- helpers: read, never assert ---------------------------------------------


def _rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.name


def _code_lines(text: str) -> list[tuple[int, str]]:
    """``(line number, line without its comment)`` for every line with content.

    The posture of ``_uncommented`` in test_agent_artifacts.py, keeping the
    line numbers so an offender can be named: a comment that merely mentions
    a token must satisfy nothing and trip nothing (R-HCW-15).
    """
    kept: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), 1):
        code = line.split("#", 1)[0].rstrip()
        if code.strip():
            kept.append((number, code))
    return kept


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def _top_level_block(text: str, key: str) -> dict[str, str] | None:
    """The ``k: v`` entries of a top-level ``key:`` mapping, or ``None``."""
    lines = _code_lines(text)
    for index, (_, code) in enumerate(lines):
        if code != f"{key}:":
            continue
        entries: dict[str, str] = {}
        for _, nested in lines[index + 1:]:
            if _indent(nested) == 0:
                break
            name, _, value = nested.strip().partition(":")
            entries[name.strip()] = value.strip()
        return entries
    return None


_USES = re.compile(r"^\s*-?\s*uses:\s*(\S+)")
_SHA = re.compile(r"^[0-9a-f]{40}$")


def _uses_refs(paths: Iterable[Path]) -> list[tuple[Path, int, str, str]]:
    """``(file, line, owner/repo, ref)`` for every third-party ``uses:``.

    Skips ``./`` local actions and this repository's own action. The action
    name is the first two path segments, so ``github/codeql-action/upload-sarif``
    is ``github/codeql-action`` -- one action, however many entry points.
    """
    refs: list[tuple[Path, int, str, str]] = []
    for path in paths:
        for number, code in _code_lines(path.read_text(encoding="utf-8")):
            match = _USES.match(code)
            if not match:
                continue
            target = match.group(1).strip("\"'")
            if target.startswith(("./", OWN_ACTION_PREFIX)):
                continue
            name, _, ref = target.partition("@")
            refs.append((path, number, "/".join(name.split("/")[:2]), ref))
    return refs


def _ref_disagreements(paths: Iterable[Path]) -> list[str]:
    by_action: dict[str, list[tuple[Path, int, str]]] = {}
    for path, number, action, ref in _uses_refs(paths):
        by_action.setdefault(action, []).append((path, number, ref))
    offenders = []
    for action, uses in sorted(by_action.items()):
        if len({ref for _, _, ref in uses}) > 1:
            where = ", ".join(f"{_rel(p)}:{n} @{ref}" for p, n, ref in uses)
            offenders.append(f"{action} is referenced on more than one ref: {where}")
    return offenders


def _sha_refs(paths: Iterable[Path]) -> list[str]:
    return [
        f"{_rel(path)}:{number} {action}@{ref}"
        for path, number, action, ref in _uses_refs(paths)
        if _SHA.match(ref)
    ]


def _job_permission_blocks(text: str) -> list[tuple[str, dict[str, str], bool]]:
    """``(job, entries, has a comment line above it in the job)`` per block."""
    found: list[tuple[str, dict[str, str], bool]] = []
    for job, body in workflow_job_blocks(text).items():
        raw = body.splitlines()
        for index, line in enumerate(raw):
            if line.split("#", 1)[0].rstrip() != "    permissions:":
                continue
            entries: dict[str, str] = {}
            for nested in raw[index + 1:]:
                code = nested.split("#", 1)[0].rstrip()
                if not code.strip():
                    continue
                if _indent(code) <= 4:
                    break
                name, _, value = code.strip().partition(":")
                entries[name.strip()] = value.strip()
            commented = any(previous.lstrip().startswith("#") for previous in raw[:index])
            found.append((job, entries, commented))
    return found


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


def _uncommented_permission_blocks(text: str, label: str) -> list[str]:
    return [
        f"{label}: job {job} has a permissions: block with no comment line above it in the job"
        for job, _, commented in _job_permission_blocks(text)
        if not commented
    ]


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


def _job_level_keys(body: str) -> dict[str, str]:
    """Keys at job indentation only, so a step-level key never counts."""
    keys: dict[str, str] = {}
    for _, code in _code_lines(body):
        if _indent(code) == 4:
            name, _, value = code.strip().partition(":")
            keys[name] = value.strip()
    return keys


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


_FROM = re.compile(r"^FROM\s+(\S+)")


def _dockerfile_from(text: str) -> tuple[int, str] | None:
    for number, code in _code_lines(text):
        match = _FROM.match(code)
        if match:
            return number, match.group(1)
    return None


def _dockerfile_tag_version(text: str) -> str | None:
    found = _dockerfile_from(text)
    if not found:
        return None
    match = re.match(r"^python:(\d+\.\d+)-slim(?:@|$)", found[1])
    return match.group(1) if match else None


def _dockerfile_offenders(text: str) -> list[str]:
    offenders = []
    found = _dockerfile_from(text)
    if found is None:
        offenders.append("Dockerfile: no FROM instruction")
    else:
        number, image = found
        if not re.search(r"@sha256:[0-9a-f]{64}$", image):
            offenders.append(f"Dockerfile:{number}: FROM is not digest-pinned: {image}")
        elif not re.match(r"^[^@:]+:[^@]+@sha256:", image):
            offenders.append(f"Dockerfile:{number}: FROM carries no tag before its digest: {image}")
    lines = _code_lines(text)
    installs = [n for n, c in lines if c.startswith("RUN ") and "pip install" in c]
    users = [(n, c.split()[1]) for n, c in lines if c.startswith("USER ")]
    if not users:
        offenders.append("Dockerfile: no USER instruction; the entrypoint runs as root")
    for number, user in users:
        if user == "root":
            offenders.append(f"Dockerfile:{number}: USER root")
        if installs and number < max(installs):
            offenders.append(f"Dockerfile:{number}: USER {user} precedes the install at line {max(installs)}")
    return offenders


def _dependabot_entries(text: str) -> set[tuple[str, str]]:
    """``(package-ecosystem, directory)`` pairs, in order of appearance."""
    entries: set[tuple[str, str]] = set()
    ecosystem: str | None = None
    for _, code in _code_lines(text):
        stripped = code.strip().lstrip("- ")
        name, _, value = stripped.partition(":")
        if name == "package-ecosystem":
            ecosystem = value.strip().strip("\"'")
        elif name == "directory" and ecosystem is not None:
            entries.add((ecosystem, value.strip().strip("\"'")))
            ecosystem = None
    return entries


def _docker_watch_offenders(dockerfile_text: str, dependabot_text: str) -> list[str]:
    found = _dockerfile_from(dockerfile_text)
    if not found or "@sha256:" not in found[1]:
        return []
    if ("docker", "/") in _dependabot_entries(dependabot_text):
        return []
    return [f"Dockerfile:{found[0]} is digest-pinned but .github/dependabot.yml has no docker entry for /"]


def _pyproject() -> dict[str, Any]:
    try:
        import tomllib as toml_reader
    except ModuleNotFoundError:  # pragma: no cover - 3.10 leg only
        import tomli as toml_reader  # type: ignore[import-not-found,no-redef]
    with PYPROJECT.open("rb") as handle:
        return toml_reader.load(handle)


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


def _ci_text() -> str:
    return CI_YML.read_text(encoding="utf-8")


# --- R-HCW-1 / R-HCW-2 / C-HCW-3: action refs agree, and none is a SHA ------


def test_every_reference_to_one_action_agrees_on_one_ref() -> None:
    """AC-HCW-1: one action, one ref, across the workflows, the composite
    action, the adopter templates and the README snippet."""
    assert _uses_refs(ACTION_REF_SCAN), "found no third-party uses: at all -- the scan is broken"
    offenders = _ref_disagreements(ACTION_REF_SCAN)
    assert not offenders, "\n".join(offenders)


def test_a_leftover_retired_major_is_reported_with_file_and_line(tmp_path: Path) -> None:
    """AC-HCW-2 (non-success): a template left on the old major while the
    workflow moved is named with both files and lines."""
    workflow = tmp_path / "ci.yml"
    template = tmp_path / "spec-gate.yml"
    workflow.write_text("jobs:\n  t:\n    steps:\n      - uses: actions/checkout@v7\n", encoding="utf-8")
    template.write_text(
        "jobs:\n  t:\n    steps:\n      # uses: actions/checkout@v1 (a comment must not count)\n"
        "      - uses: actions/checkout@v4\n",
        encoding="utf-8",
    )
    offenders = _ref_disagreements([workflow, template])
    assert len(offenders) == 1, offenders
    assert "ci.yml:4 @v7" in offenders[0] and "spec-gate.yml:5 @v4" in offenders[0], offenders


def test_no_third_party_action_ref_is_a_commit_sha() -> None:
    """AC-HCW-24: SHA pinning is a separate package; this repository's own
    action ref is exempt and policed by tests/test_adopter_urls.py."""
    assert not _sha_refs(ACTION_REF_SCAN), _sha_refs(ACTION_REF_SCAN)


def test_the_own_action_ref_is_exempt_from_the_sha_check(tmp_path: Path) -> None:
    planted = tmp_path / "t.yml"
    planted.write_text(
        f"jobs:\n  t:\n    steps:\n      - uses: {OWN_ACTION_PREFIX}.github/actions/planlint@{'a' * 40}\n"
        f"      - uses: ./.github/actions/planlint\n      - uses: actions/checkout@{'b' * 40}\n",
        encoding="utf-8",
    )
    assert _sha_refs([planted]) == [f"t.yml:6 actions/checkout@{'b' * 40}"]


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


# --- R-HCW-8 / R-HCW-9: one Python default per workflow, agreed everywhere --


def test_no_quoted_python_version_literal_outside_env_and_matrix() -> None:
    """AC-HCW-11: every single-version step reads env.PYTHON_DEFAULT."""
    offenders = []
    for workflow in WORKFLOWS:
        text = workflow.read_text(encoding="utf-8")
        assert _workflow_env(text, "PYTHON_DEFAULT"), f"{_rel(workflow)} declares no env.PYTHON_DEFAULT"
        offenders += [f'{_rel(workflow)}:{n} python-version: "{v}"' for n, v in _quoted_version_literals(text)]
    assert not offenders, "\n".join(offenders)


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


def test_the_default_python_is_a_hard_matrix_leg() -> None:
    """AC-HCW-13: the interpreter every single-version job runs on is one the
    matrix tests as a hard gate, not an advisory leg."""
    default = _workflow_env(_ci_text(), "PYTHON_DEFAULT")
    hard, experimental = _matrix_versions(_ci_text())
    assert default in hard, f"PYTHON_DEFAULT {default!r} is not a hard matrix leg; hard={sorted(hard)} experimental={sorted(experimental)}"


def test_a_disagreeing_default_is_named() -> None:
    assert _action_input_default('inputs:\n  python-version:\n    description: x\n    default: "3.11"\n', "python-version") == "3.11"
    assert _dockerfile_tag_version("FROM python:3.12-slim@sha256:" + "0" * 64 + "\n") == "3.12"
    assert _workflow_env('env:\n  PYTHON_DEFAULT: "3.13"\njobs:\n', "PYTHON_DEFAULT") == "3.13"


# --- R-HCW-10 / R-HCW-11: the experimental leg, the classifiers, the docs ---


def test_the_experimental_leg_is_an_expression_not_a_job_literal() -> None:
    """AC-HCW-14: an experimental leg rides `continue-on-error: ${{
    matrix.experimental || false }}`; a job-level literal would soften every
    leg at once."""
    assert not _experimental_leg_offenders(_ci_text()), "\n".join(_experimental_leg_offenders(_ci_text()))


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


def test_classifiers_equal_the_hard_matrix_legs() -> None:
    """AC-HCW-15: a classifier is a promise, so the set equals the hard legs
    -- no more (an untested promise) and no fewer (an unannounced support)."""
    hard, _ = _matrix_versions(_ci_text())
    classified = _classifier_versions(_pyproject()["project"]["classifiers"])
    assert classified == hard, (
        f"classifiers without a hard leg: {sorted(classified - hard)}; "
        f"hard legs without a classifier: {sorted(hard - classified)}"
    )


def test_hooks_test_row_names_the_matrix_bounds() -> None:
    """AC-HCW-15: docs/hooks.md's `test` row states the lowest and highest
    hard leg, read from the matrix rather than typed twice."""
    hard, _ = _matrix_versions(_ci_text())
    bounds = _hooks_test_row_bounds(HOOKS_DOC.read_text(encoding="utf-8"))
    assert bounds is not None, "docs/hooks.md has no `test` (low-high) row"
    expected = (min(hard, key=_version_key), max(hard, key=_version_key))
    assert bounds == expected, f"docs/hooks.md names {bounds}, the matrix's hard legs span {expected}"


def test_a_classifier_or_row_drift_is_named() -> None:
    """AC-HCW-16 (non-success)."""
    assert _classifier_versions(["Programming Language :: Python :: 3.12", "Programming Language :: Python :: 3"]) == {"3.12"}
    assert _hooks_test_row_bounds("| `test` (3.10\u20133.13) | push |") == ("3.10", "3.13")
    assert _hooks_test_row_bounds("| `test` | push |") is None


# --- R-HCW-13 / R-HCW-14: the Dockerfile and its update bot -----------------


def test_dockerfile_from_is_digest_pinned_with_the_tag_in_the_reference() -> None:
    """AC-HCW-18: the digest is the pin; the tag stays in the reference for
    readers and for Dependabot, which moves both together."""
    offenders = [o for o in _dockerfile_offenders(DOCKERFILE.read_text(encoding="utf-8")) if "FROM" in o]
    assert not offenders, "\n".join(offenders)


def test_dockerfile_switches_to_a_non_root_user_after_install() -> None:
    """AC-HCW-18: the CLI only reads the tree it is pointed at."""
    offenders = [o for o in _dockerfile_offenders(DOCKERFILE.read_text(encoding="utf-8")) if "USER" in o]
    assert not offenders, "\n".join(offenders)


def test_a_digest_pinned_base_is_watched_by_a_docker_dependabot_entry() -> None:
    """AC-HCW-18: an unwatched digest is a pin that only gets staler."""
    offenders = _docker_watch_offenders(
        DOCKERFILE.read_text(encoding="utf-8"), DEPENDABOT.read_text(encoding="utf-8")
    )
    assert not offenders, "\n".join(offenders)


@pytest.mark.parametrize(
    "label, dockerfile, expected",
    [
        ("tag only", "FROM python:3.12-slim\nRUN pip install .\nUSER app\n", "not digest-pinned"),
        ("no tag", f"FROM python@sha256:{'0' * 64}\nRUN pip install .\nUSER app\n", "no tag before its digest"),
        ("no user", f"FROM python:3.12-slim@sha256:{'0' * 64}\nRUN pip install .\n", "no USER instruction"),
        ("root", f"FROM python:3.12-slim@sha256:{'0' * 64}\nRUN pip install .\nUSER root\n", "USER root"),
        ("too early", f"FROM python:3.12-slim@sha256:{'0' * 64}\nUSER app\nRUN pip install .\n", "precedes the install"),
    ],
)
def test_a_weak_dockerfile_is_named(label: str, dockerfile: str, expected: str) -> None:
    """AC-HCW-19 (non-success)."""
    offenders = _dockerfile_offenders(dockerfile)
    assert any(expected in offender for offender in offenders), (label, offenders)


def test_an_unwatched_digest_is_named() -> None:
    dockerfile = f"FROM python:3.12-slim@sha256:{'0' * 64}\n"
    dependabot = 'version: 2\nupdates:\n  - package-ecosystem: "github-actions"\n    directory: "/"\n'
    assert _docker_watch_offenders(dockerfile, dependabot) == [
        "Dockerfile:1 is digest-pinned but .github/dependabot.yml has no docker entry for /"
    ]
    watched = dependabot + '  - package-ecosystem: "docker"\n    directory: "/"\n'
    assert _docker_watch_offenders(dockerfile, watched) == []


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
