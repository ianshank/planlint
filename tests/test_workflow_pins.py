"""Every action reference pinned, agreed, at or above its major floor; the Dockerfile and its update bot.

Moved from ``tests/test_workflow_hardening.py`` and ``tests/test_ci_workflow.py`` by
``shape-the-test-suite`` (R-TSS-2): ``harden-ci-workflows`` R-HCW-1, R-HCW-2, R-HCW-13,
R-HCW-14 and ``pin-actions-by-sha`` R-ASP-1, R-ASP-8, R-ASP-11 -- both Dependabot readers
R-ASP-11 names live here (DEC-TSS-016).
"""

from __future__ import annotations

import re
import textwrap
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pytest

from tests.workflow_support import (
    ACTION_YMLS,
    DEPENDABOT,
    DOCKERFILE,
    FLOOR_TABLE,
    HAND_CARRY,
    OWN_ACTION_PREFIX,
    README,
    TEMPLATES,
    WORKFLOWS,
    WRITING_VERBS,
    _code_lines,
    _dockerfile_from,
    _pyproject,
    _rel,
)

#: Every file whose third-party `uses:` refs must agree (R-HCW-1, R-HCW-2,
#: DEC-HCW-012): the workflows, the composite action, the adopter templates
#: and the README's copyable snippet.
ACTION_REF_SCAN: list[Path] = [*WORKFLOWS, *ACTION_YMLS, *TEMPLATES, README]

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


REPO_ROOT = Path(__file__).resolve().parent.parent

def _dependabot_directories() -> set[str]:
    """Every directory dependabot.yml watches, as text.

    Reads the singular `directory:` and the plural `directories:` -- flow
    list or block list -- because one entry with `directories:` is how a
    bump of every copy under `.github/` arrives as one grouped pull request
    (pin-actions-by-sha R-ASP-11). Parsed with `re` rather than PyYAML for the
    same reason every other config assertion here is: the package declares
    zero dependencies and the test suite does not get to import one the
    product cannot.
    """
    text = DEPENDABOT.read_text(encoding="utf-8")
    found = set(re.findall(r'^\s*directory:\s*"([^"]+)"', text, re.MULTILINE))
    for flow in re.findall(r"^\s*directories:\s*\[([^\]]*)\]", text, re.MULTILINE):
        found |= {item.strip().strip("\"'") for item in flow.split(",") if item.strip()}
    for block in re.findall(r'^\s*directories:\s*\n((?:\s+-\s*"[^"]+"\s*\n)+)', text, re.MULTILINE):
        found |= set(re.findall(r'"([^"]+)"', block))
    return found

def test_dependabot_config_exists_and_watches_github_actions() -> None:
    assert DEPENDABOT.is_file(), "no .github/dependabot.yml; action pins would go stale silently"
    text = DEPENDABOT.read_text(encoding="utf-8")
    assert 'package-ecosystem: "github-actions"' in text

def test_every_composite_action_directory_is_watched_by_dependabot() -> None:
    """A nested composite action is invisible to the root entry.

    Dependabot's github-actions ecosystem discovers workflow files under the
    `/` entry, but an `action.yml` in a subdirectory needs that subdirectory
    declared explicitly. Adding a second composite action without a matching
    entry would leave its pins unwatched, and nothing else in this suite would
    notice -- which is exactly how the floating tags this config exists to
    manage got there in the first place.
    """
    watched = _dependabot_directories()
    assert "/" in watched, watched

    for action_yml in sorted((REPO_ROOT / ".github" / "actions").glob("*/action.yml")):
        rel = "/" + str(action_yml.parent.relative_to(REPO_ROOT)).replace("\\", "/")
        assert rel in watched, (
            f"{rel} holds a composite action but is not a dependabot `directory:` entry; "
            f"its third-party pins would never be updated. Watched: {sorted(watched)}"
        )

def test_dependabot_does_not_add_a_pip_ecosystem() -> None:
    """Non-success: the dev extras are unpinned on purpose.

    `[project] dependencies` is empty and guarded, and
    `tools/check_no_hardcoded_thresholds.py` fails the build on a reintroduced
    `ruff==`/`mypy==`/`pytest==` pin. A pip ecosystem entry would open pull
    requests arguing with that decision every release, so its absence is a
    decision worth pinning rather than an omission.
    """
    text = DEPENDABOT.read_text(encoding="utf-8")
    assert 'package-ecosystem: "pip"' not in text
