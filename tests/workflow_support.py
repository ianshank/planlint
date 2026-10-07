"""Readers shared by the workflow test modules -- read, never assert.

The pattern of ``tests/graft_support.py``: a module pytest does not collect,
holding the helpers more than one collected module uses, so that no collected
module imports another (``shape-the-test-suite`` R-TSS-2, ``harden-ci-workflows``
DEC-HCW-009). Moved from ``tests/test_workflow_hardening.py``, every docstring kept.
Readers used by one module only live in that module.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from tests.support import workflow_job_blocks

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

    The posture of ``_uncommented`` in test_release_surface.py, keeping the
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

def _uncommented_permission_blocks(text: str, label: str) -> list[str]:
    return [
        f"{label}: job {job} has a permissions: block with no comment line above it in the job"
        for job, _, commented in _job_permission_blocks(text)
        if not commented
    ]

def _job_level_keys(body: str) -> dict[str, str]:
    """Keys at job indentation only, so a step-level key never counts."""
    keys: dict[str, str] = {}
    for _, code in _code_lines(body):
        if _indent(code) == 4:
            name, _, value = code.strip().partition(":")
            keys[name] = value.strip()
    return keys

_FROM = re.compile(r"^FROM\s+(\S+)")

def _dockerfile_from(text: str) -> tuple[int, str] | None:
    for number, code in _code_lines(text):
        match = _FROM.match(code)
        if match:
            return number, match.group(1)
    return None

def _pyproject() -> dict[str, Any]:
    try:
        import tomllib as toml_reader
    except ModuleNotFoundError:  # pragma: no cover - 3.10 leg only
        import tomli as toml_reader  # type: ignore[import-not-found,no-redef]
    with PYPROJECT.open("rb") as handle:
        return toml_reader.load(handle)

def _ci_text() -> str:
    return CI_YML.read_text(encoding="utf-8")
