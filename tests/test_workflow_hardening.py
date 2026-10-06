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
ACTION_YMLS = sorted((REPO_ROOT / ".github" / "actions").glob("*/action.yml"))
DOCKERFILE = REPO_ROOT / "Dockerfile"
DEPENDABOT = REPO_ROOT / ".github" / "dependabot.yml"
TEMPLATES = sorted((REPO_ROOT / "templates").glob("*.yml"))
README = REPO_ROOT / "README.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"
HOOKS_DOC = REPO_ROOT / "docs" / "hooks.md"

#: Every file whose third-party `uses:` refs must agree (R-HCW-1, R-HCW-2,
#: DEC-HCW-012): the workflows, the composite action, the adopter templates
#: and the README's copyable snippet.
ACTION_REF_SCAN: list[Path] = [*WORKFLOWS, *ACTION_YMLS, *TEMPLATES, README]

#: Where a pin has to be carried by hand: Dependabot reads neither the
#: adopter template (nor its byte copy under the skill) nor the README, so a
#: bump under `.github/` leaves them behind until someone copies the pin.
HAND_CARRY = (
    "`templates/spec-gate.yml`, its copy under `skills/planlint-spec-governance/assets/` "
    "and `README.md` are not watched by Dependabot; carry the SHA and its `# vX.Y.Z` "
    "comment there by hand."
)

#: This repository's own composite action, as adopters reference it. Its ref
#: is a commit SHA until the first public tag exists; that ref belongs to
#: tests/test_adopter_urls.py and docs/distribution-plan.md, not to this
#: module (C-HCW-3).
OWN_ACTION_PREFIX = "ianshank/planlint/"

TIMEOUT_SECTION = "[tool.specgraph]"
TIMEOUT_KEYS = ("ci_job_timeout_minutes_min", "ci_job_timeout_minutes_max")
FLOOR_TABLE = "action_major_floors"

#: The CLI verbs that write into the target tree (`planlint --help`: init
#: writes a conventions snapshot, new scaffolds a package, witness records a
#: run). A non-root image cannot write into a host-owned bind mount, so the
#: Dockerfile's header must hand the reader the `--user` override for these.
WRITING_VERBS = ("init", "new", "witness")
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
_PIN_COMMENT = re.compile(r"^v\d+\.\d+\.\d+$")


def _uses_refs(paths: Iterable[Path]) -> list[tuple[Path, int, str, str, str | None]]:
    """``(file, line, owner/repo, ref, comment)`` for every third-party ``uses:``.

    Read from the raw line rather than ``_code_lines``, on purpose: a pin is
    ``@<sha> # v7.0.1`` and the trailing comment is the only place its
    release lives, so this one reader keeps the comment -- as stripped text,
    or ``None`` when the line has no ``#`` -- and applies no pattern to it;
    the callers classify. A line whose code half is blank is a whole-line
    comment and yields nothing, which is the posture every other guard takes
    from ``_code_lines``. Skips ``./`` local actions and this repository's
    own action. The action name is the first two path segments, so
    ``github/codeql-action/upload-sarif`` is ``github/codeql-action`` -- one
    action, however many entry points.
    """
    refs: list[tuple[Path, int, str, str, str | None]] = []
    for path in paths:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            code, hash_sign, comment = line.partition("#")
            if not code.strip():
                continue
            match = _USES.match(code)
            if not match:
                continue
            target = match.group(1).strip("\"'")
            if target.startswith(("./", OWN_ACTION_PREFIX)):
                continue
            name, _, ref = target.partition("@")
            action = "/".join(name.split("/")[:2])
            refs.append((path, number, action, ref, comment.strip() if hash_sign else None))
    return refs


def _pin_offenders(paths: Iterable[Path]) -> list[str]:
    """Every third-party ``uses:`` that is not ``@<40-hex> # vMAJOR.MINOR.PATCH``.

    Three shapes, each named so the fix is obvious: a tag or branch ref is
    not pinned at all; a SHA with no comment is pinned but no reader can tell
    which release it is; a SHA whose comment is not a release tag is a hand
    edit that drifted (Dependabot writes exactly ``# vX.Y.Z``).
    """
    offenders = []
    for path, number, action, ref, comment in _uses_refs(paths):
        where = f"{_rel(path)}:{number} {action}@{ref}"
        if not _SHA.match(ref):
            offenders.append(f"{where} is not a commit SHA")
        elif comment is None:
            offenders.append(f"{where} has no `# vX.Y.Z` release-tag comment")
        elif not _PIN_COMMENT.match(comment):
            offenders.append(
                f"{where} # {comment} is not a release tag; expected `# vMAJOR.MINOR.PATCH`"
            )
    return offenders


def _ref_disagreements(paths: Iterable[Path]) -> list[str]:
    """One action, one ``(ref, comment)`` pair across the scan set.

    The pair, not the ref alone: two copies on one SHA with different
    comments disagree about which release that SHA is, and the comment is
    what Dependabot classifies the update from.
    """
    by_action: dict[str, list[tuple[Path, int, str, str | None]]] = {}
    for path, number, action, ref, comment in _uses_refs(paths):
        by_action.setdefault(action, []).append((path, number, ref, comment))
    offenders = []
    for action, uses in sorted(by_action.items()):
        if len({(ref, comment) for _, _, ref, comment in uses}) > 1:
            where = ", ".join(f"{_rel(p)}:{n} @{ref} # {c}" for p, n, ref, c in uses)
            offenders.append(f"{action} is referenced on more than one ref: {where}. {HAND_CARRY}")
    return offenders


_MAJOR = re.compile(r"^v(\d+)(?:\.\d+)*$")


def _major(ref: str) -> int | None:
    """``v7`` or ``v7.0.1`` -> 7; a branch or SHA ref has no major."""
    match = _MAJOR.match(ref)
    return int(match.group(1)) if match else None


def _action_major_floors(config: dict[str, Any] | None = None) -> dict[str, int]:
    table = (config or _pyproject())["tool"]["specgraph"].get(FLOOR_TABLE)
    assert table, f"pyproject.toml declares no [tool.specgraph.{FLOOR_TABLE}]; the floor guard cannot run"
    return {name: int(floor) for name, floor in table.items()}


def _floor_offenders(paths: Iterable[Path], floors: dict[str, int]) -> list[str]:
    """Refs below their action's floor, and major-tagged actions with no floor.

    The agreement guard sees only disagreement: every copy of an action
    sliding back to a retired major together is still one ref. The floor is
    the independent invariant that catches that, and an action the table
    forgot is a hole in it, so it is reported too. For a SHA pin the major
    is read from the release tag in its comment; a branch ref, a bare SHA or
    an unparseable comment has no major and is the shape guard's to name.
    """
    offenders = []
    for path, number, action, ref, comment in _uses_refs(paths):
        pinned = bool(_SHA.match(ref))
        major = _major(comment or "") if pinned else _major(ref)
        if major is None:
            continue
        shown = f"{action}@{ref} # {comment}" if pinned else f"{action}@{ref}"
        floor = floors.get(action)
        if floor is None:
            offenders.append(
                f"{_rel(path)}:{number} {shown} has no floor in [tool.specgraph.{FLOOR_TABLE}]"
            )
        elif major < floor:
            offenders.append(f"{_rel(path)}:{number} {shown} is below its floor v{floor}")
    return offenders


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


def _user_override_offenders(text: str) -> list[str]:
    """A non-root image must tell the reader how to run the writing verbs."""
    if not any(code.startswith("USER ") for _, code in _code_lines(text)):
        return []
    comments = "\n".join(line for line in text.splitlines() if line.lstrip().startswith("#"))
    offenders = []
    if "--user" not in comments or "id -u" not in comments:
        offenders.append(
            'Dockerfile: non-root USER, but the header documents no `--user "$(id -u):$(id -g)"` override'
        )
    offenders += [
        f"Dockerfile: the header does not name `{verb}` as a verb that writes into the mounted tree"
        for verb in WRITING_VERBS
        if not re.search(rf"`{verb}`", comments)
    ]
    return offenders


def _dependabot_entries(text: str) -> set[tuple[str, str]]:
    """``(package-ecosystem, directory)`` pairs, one per watched directory.

    Reads the singular ``directory:`` and the plural ``directories:`` -- as
    a flow list (``["/", "/x"]``) or a block list (one ``- "/x"`` line each)
    -- because one entry with ``directories:`` is how a bump of every copy
    under ``.github/`` arrives as one grouped pull request.
    """
    entries: set[tuple[str, str]] = set()
    ecosystem: str | None = None
    in_block_list = False
    for _, code in _code_lines(text):
        stripped = code.strip()
        if in_block_list:
            if stripped.startswith("- ") and ":" not in stripped and ecosystem is not None:
                entries.add((ecosystem, stripped[2:].strip().strip("\"'")))
                continue
            in_block_list = False
            ecosystem = None
        name, _, value = stripped.lstrip("- ").partition(":")
        value = value.strip()
        if name == "package-ecosystem":
            ecosystem = value.strip("\"'")
        elif name == "directory" and ecosystem is not None:
            entries.add((ecosystem, value.strip("\"'")))
            ecosystem = None
        elif name == "directories" and ecosystem is not None:
            if value.startswith("["):
                for item in value.strip("[]").split(","):
                    if item.strip():
                        entries.add((ecosystem, item.strip().strip("\"'")))
                ecosystem = None
            else:
                in_block_list = True
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


# --- R-HCW-1 / R-HCW-2 / R-ASP-1: action refs agree, and every one is a pinned SHA


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
    new, old = "a" * 40, "b" * 40
    workflow.write_text(
        f"jobs:\n  t:\n    steps:\n      - uses: actions/checkout@{new} # v7.0.1\n", encoding="utf-8"
    )
    template.write_text(
        "jobs:\n  t:\n    steps:\n      # uses: actions/checkout@v1 (a comment must not count)\n"
        f"      - uses: actions/checkout@{old} # v4.2.2\n",
        encoding="utf-8",
    )
    offenders = _ref_disagreements([workflow, template])
    assert len(offenders) == 1, offenders
    assert f"ci.yml:4 @{new} # v7.0.1" in offenders[0], offenders
    assert f"spec-gate.yml:5 @{old} # v4.2.2" in offenders[0], offenders
    assert offenders[0].endswith(HAND_CARRY), offenders


def test_every_third_party_action_meets_its_major_floor() -> None:
    """AC-HCW-28: the agreement guard cannot see every copy regressing
    together; the per-action floor in pyproject.toml can (R-HCW-17)."""
    offenders = _floor_offenders(ACTION_REF_SCAN, _action_major_floors())
    assert not offenders, "\n".join(offenders)


def test_a_uniformly_retired_major_is_named_with_file_and_line(tmp_path: Path) -> None:
    """AC-HCW-29 (non-success): two files agreeing on one retired pin pass
    the agreement guard and fail the floor guard, each named with the
    release tag the floor was read from (R-ASP-4)."""
    paths = [tmp_path / "ci.yml", tmp_path / "spec-gate.yml"]
    sha = "a" * 40
    for path in paths:
        path.write_text(
            f"jobs:\n  t:\n    steps:\n      - uses: actions/checkout@{sha} # v4.2.2\n", encoding="utf-8"
        )
    assert _ref_disagreements(paths) == []
    assert _floor_offenders(paths, {"actions/checkout": 7}) == [
        f"ci.yml:4 actions/checkout@{sha} # v4.2.2 is below its floor v7",
        f"spec-gate.yml:4 actions/checkout@{sha} # v4.2.2 is below its floor v7",
    ]


def test_an_action_without_a_floor_is_named(tmp_path: Path) -> None:
    """AC-HCW-29 (non-success): a table that forgot an action is a hole;
    a branch ref has no major and is the shape guard's business, not the
    floor's."""
    planted = tmp_path / "t.yml"
    sha = "a" * 40
    planted.write_text(
        f"jobs:\n  t:\n    steps:\n      - uses: some/action@{sha} # v2.0.0\n"
        "      - uses: pypa/gh-action-pypi-publish@release/v1\n",
        encoding="utf-8",
    )
    assert _floor_offenders([planted], {"actions/checkout": 7}) == [
        f"t.yml:4 some/action@{sha} # v2.0.0 has no floor in [tool.specgraph.{FLOOR_TABLE}]"
    ]
    assert _major("v7") == 7 and _major("v7.0.1") == 7 and _major("v3.38.2") == 3
    assert _major("release/v1") is None and _major("a" * 40) is None


def test_every_third_party_action_is_pinned_to_a_commit_sha_with_its_release_tag() -> None:
    """AC-ASP-1: every third-party `uses:` in the scan set is a 40-hex commit
    with its release tag in a trailing comment (R-ASP-1)."""
    assert _uses_refs(ACTION_REF_SCAN), "found no third-party uses: at all -- the scan is broken"
    offenders = _pin_offenders(ACTION_REF_SCAN)
    assert not offenders, "\n".join(offenders)


def test_a_sha_pin_without_its_release_tag_comment_is_named(tmp_path: Path) -> None:
    """AC-ASP-2 (non-success): a bare SHA is pinned but unreadable; it is
    named beside a commented one that is not."""
    planted = tmp_path / "t.yml"
    planted.write_text(
        f"jobs:\n  t:\n    steps:\n      - uses: actions/checkout@{'a' * 40} # v7.0.1\n"
        f"      - uses: actions/setup-python@{'b' * 40}\n",
        encoding="utf-8",
    )
    assert _pin_offenders([planted]) == [
        f"t.yml:5 actions/setup-python@{'b' * 40} has no `# vX.Y.Z` release-tag comment"
    ]


def test_the_own_action_ref_is_exempt_from_the_sha_check(tmp_path: Path) -> None:
    """This repository's own action ref (a bare SHA until the first tag,
    policed by tests/test_adopter_urls.py) and a `./` local action are not
    the third-party guards' business; the third-party bare SHA beside them is."""
    planted = tmp_path / "t.yml"
    planted.write_text(
        f"jobs:\n  t:\n    steps:\n      - uses: {OWN_ACTION_PREFIX}.github/actions/planlint@{'a' * 40}\n"
        f"      - uses: ./.github/actions/planlint\n      - uses: actions/checkout@{'b' * 40}\n",
        encoding="utf-8",
    )
    assert _pin_offenders([planted]) == [
        f"t.yml:6 actions/checkout@{'b' * 40} has no `# vX.Y.Z` release-tag comment"
    ]


def test_an_unpinned_ref_is_named_with_file_and_line(tmp_path: Path) -> None:
    """AC-ASP-2 (non-success): a tag, a branch, and two malformed comments
    are each named; a whole-line `# uses:` comment is not."""
    planted = tmp_path / "t.yml"
    sha = "c" * 40
    planted.write_text(
        textwrap.dedent(
            f"""\
            jobs:
              t:
                steps:
                  # uses: actions/checkout@v1 is a comment, not a ref
                  - uses: actions/checkout@v7
                  - uses: pypa/gh-action-pypi-publish@release/v1
                  - uses: actions/upload-artifact@{sha} # v7
                  - uses: actions/download-artifact@{sha} # 7.0.1
            """
        ),
        encoding="utf-8",
    )
    assert _pin_offenders([planted]) == [
        "t.yml:5 actions/checkout@v7 is not a commit SHA",
        "t.yml:6 pypa/gh-action-pypi-publish@release/v1 is not a commit SHA",
        (
            f"t.yml:7 actions/upload-artifact@{sha} # v7 is not a release tag; "
            "expected `# vMAJOR.MINOR.PATCH`"
        ),
        (
            f"t.yml:8 actions/download-artifact@{sha} # 7.0.1 is not a release tag; "
            "expected `# vMAJOR.MINOR.PATCH`"
        ),
    ]


def test_the_version_comment_is_read_from_the_raw_line(tmp_path: Path) -> None:
    """AC-ASP-2: the reader keeps the comment `_code_lines` strips (R-ASP-6)."""
    planted = tmp_path / "t.yml"
    planted.write_text(
        f"jobs:\n  t:\n    steps:\n      - uses: actions/checkout@{'a' * 40} # v7.0.1\n", encoding="utf-8"
    )
    [(_, _, action, ref, comment)] = _uses_refs([planted])
    assert (action, ref, comment) == ("actions/checkout", "a" * 40, "v7.0.1")
    assert all("#" not in code for _, code in _code_lines(planted.read_text(encoding="utf-8")))


def test_a_comment_disagreement_behind_one_sha_is_named(tmp_path: Path) -> None:
    """AC-ASP-6 (non-success): one SHA, two release-tag comments -- the pair
    disagrees even though the ref agrees (R-ASP-5)."""
    sha = "a" * 40
    first, second = tmp_path / "ci.yml", tmp_path / "release.yml"
    first.write_text(f"jobs:\n  t:\n    steps:\n      - uses: actions/checkout@{sha} # v7.0.1\n", encoding="utf-8")
    second.write_text(f"jobs:\n  t:\n    steps:\n      - uses: actions/checkout@{sha} # v7.0.0\n", encoding="utf-8")
    offenders = _ref_disagreements([first, second])
    assert len(offenders) == 1, offenders
    assert f"ci.yml:4 @{sha} # v7.0.1" in offenders[0] and f"release.yml:4 @{sha} # v7.0.0" in offenders[0]


def test_a_version_comment_below_the_floor_is_named(tmp_path: Path) -> None:
    """AC-ASP-4 (non-success): the floor reads the comment, and names it."""
    planted = tmp_path / "t.yml"
    sha = "a" * 40
    planted.write_text(f"jobs:\n  t:\n    steps:\n      - uses: actions/checkout@{sha} # v4.2.2\n", encoding="utf-8")
    assert _floor_offenders([planted], {"actions/checkout": 7}) == [
        f"t.yml:4 actions/checkout@{sha} # v4.2.2 is below its floor v7"
    ]


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


def test_dockerfile_documents_the_user_override_for_writing_verbs() -> None:
    """AC-HCW-18: the CLI is not wholly read-only -- `init`, `new` and
    `witness` write into the target -- and a non-root image cannot write into
    a host-owned bind mount, so the header hands the reader the override."""
    offenders = _user_override_offenders(DOCKERFILE.read_text(encoding="utf-8"))
    assert not offenders, "\n".join(offenders)


def test_a_non_root_dockerfile_without_the_override_is_named() -> None:
    """AC-HCW-19 (non-success)."""
    silent = "# Run: docker run --rm planlint validate\nFROM python:3.12-slim\nUSER app\n"
    offenders = _user_override_offenders(silent)
    assert offenders and "--user" in offenders[0], offenders
    assert len(offenders) == 1 + len(WRITING_VERBS), offenders
    assert _user_override_offenders("FROM python:3.12-slim\n") == []


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


def test_a_plural_directories_entry_is_read_as_one_pair_per_directory() -> None:
    """AC-ASP-17: one `github-actions` entry with `directories:` is read as
    one pair per directory, in flow and in block form (R-ASP-11)."""
    expected = {("github-actions", "/"), ("github-actions", "/.github/actions/planlint"), ("docker", "/")}
    flow = (
        'version: 2\nupdates:\n  - package-ecosystem: "github-actions"\n'
        '    directories: ["/", "/.github/actions/planlint"]\n'
        '  - package-ecosystem: "docker"\n    directory: "/"\n'
    )
    block = (
        'version: 2\nupdates:\n  - package-ecosystem: "github-actions"\n    directories:\n'
        '      - "/"\n      - "/.github/actions/planlint"\n    schedule:\n      interval: "weekly"\n'
        '  - package-ecosystem: "docker"\n    directory: "/"\n'
    )
    assert _dependabot_entries(flow) == expected
    assert _dependabot_entries(block) == expected


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
