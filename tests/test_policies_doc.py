"""`docs/policies.md` is the one place the working policies are written.

`write-down-policies` (plan W8.3). The document carries its own index, and
the agent-facing files carry one-sentence pointers into it, so the property
worth holding is between parts of the tree rather than against a copy kept
here: every level-two heading is indexed and every index anchor is a heading;
every `policies.md#<anchor>` link in a pointer file lands on a heading and
resolves from its own directory; every `make <stage>` the document cites is
a target this repository declares. The module reads the document rather than
a list of expected headings -- a list here would be the second copy
`tests/test_rule_registry_docs.py` exists to prevent -- and collects every
offender before asserting, so one run names every defect.
"""

from __future__ import annotations

import re
from pathlib import Path

from openspec_graph import detect
from openspec_graph.parse_semantics import MAKE_REF
from tests import support

REPO_ROOT = Path(__file__).resolve().parent.parent
POLICIES = REPO_ROOT / "docs" / "policies.md"
# The files that must each carry at least one pointer into the document.
POINTER_FILES = (
    REPO_ROOT / "openspec" / "AGENTS.md",
    REPO_ROOT / "docs" / "AGENTS.md",
    REPO_ROOT / "docs" / "agents-skills-harness.md",
)
# The files whose `policies.md#<anchor>` links are checked when present.
LINKING_FILES = (*POINTER_FILES, REPO_ROOT / "llms.txt", REPO_ROOT / "README.md")
# A heading in this form has an anchor that is the heading lowercased with
# spaces as hyphens and nothing else -- the only shape `_anchor` is correct
# for, which is why every heading is held to it.
HEADING_FORM = re.compile(r"^[A-Za-z0-9 -]+$")
_HEADING = re.compile(r"^## (.+?)\s*$")
_INDEX_ANCHOR = re.compile(r"\]\(#([^)\s]+)\)")
_POLICY_LINK = re.compile(r"\]\(([^)\s#]*policies\.md)#([^)\s]+)\)")
_FENCE = "```"


def _anchor(heading: str) -> str:
    return heading.lower().replace(" ", "-")


def _headings(text: str) -> list[str]:
    """Every `## ` heading outside a fenced code block, in document order."""
    found: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.startswith(_FENCE):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = _HEADING.match(line)
        if match:
            found.append(match.group(1))
    return found


def _index_anchors(text: str) -> list[str]:
    """Every `](#anchor)` before the first level-two heading."""
    head = text
    for line in text.splitlines(keepends=True):
        if _HEADING.match(line):
            head = text[: text.index(line)]
            break
    return _INDEX_ANCHOR.findall(head)


def _policy_links(text: str) -> list[tuple[str, str]]:
    """Every markdown link whose path ends in `policies.md` and has a fragment."""
    return _POLICY_LINK.findall(text)


def _index_offenders(text: str) -> list[str]:
    """Name every way the document's index and headings disagree.

    Shared by the real-tree test and the planted tests, so a planted defect
    exercises the collection and the message the real test would print.
    """
    headings = _headings(text)
    anchors = _index_anchors(text)
    offenders: list[str] = []
    if not headings:
        offenders.append("no level-two heading")
    if not anchors:
        offenders.append("no index entry")
    offenders += [
        f"heading not plain words: {h}" for h in headings if not HEADING_FORM.match(h)
    ]
    seen: set[str] = set()
    for heading in headings:
        if heading in seen:
            offenders.append(f"heading repeated: {heading}")
        seen.add(heading)
    heading_anchors = {_anchor(h) for h in headings}
    offenders += [
        f"index anchor with no heading: #{a}" for a in anchors if a not in heading_anchors
    ]
    offenders += [f"heading not indexed: {h}" for h in headings if _anchor(h) not in anchors]
    return offenders


def _pointer_offenders(pointer_text: str, policies_text: str) -> list[str]:
    """Name every `policies.md#<fragment>` in a pointer file that lands on no heading."""
    known = {_anchor(h) for h in _headings(policies_text)}
    return [
        f"#{fragment}" for _, fragment in _policy_links(pointer_text) if fragment not in known
    ]


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


# --- the real tree -----------------------------------------------------------


def test_policies_doc_is_registered_in_the_docs_gate_and_named_in_the_readme_and_llms() -> None:
    """Three registrations, one of which nothing else guards.

    `REQUIRED_DOCS` membership is what makes the docs gate hold the README
    link; the `llms.txt` line has no gate of its own, so it is held here.
    """
    check_docs = support.load_tool("check_docs", "check_docs.py")
    missing: list[str] = []
    if "docs/policies.md" not in check_docs.REQUIRED_DOCS:
        missing.append("tools/check_docs.py REQUIRED_DOCS")
    for name in ("README.md", "llms.txt"):
        if "docs/policies.md" not in (REPO_ROOT / name).read_text(encoding="utf-8"):
            missing.append(name)
    assert not missing, f"docs/policies.md is not registered in: {missing}"


def test_every_policy_heading_is_indexed_and_every_index_anchor_resolves() -> None:
    text = POLICIES.read_text(encoding="utf-8")
    offenders = [f"{_rel(POLICIES)}: {o}" for o in _index_offenders(text)]
    assert not offenders, "\n".join(offenders)


def test_every_policy_pointer_resolves_to_a_heading_and_each_pointer_file_has_one() -> None:
    policies_text = POLICIES.read_text(encoding="utf-8")
    offenders: list[str] = []
    for path in LINKING_FILES:
        text = path.read_text(encoding="utf-8")
        offenders += [f"{_rel(path)}: {o}" for o in _pointer_offenders(text, policies_text)]
        for link_path, fragment in _policy_links(text):
            if (path.parent / link_path).resolve() != POLICIES.resolve():
                offenders.append(
                    f"{_rel(path)}: {link_path}#{fragment} does not resolve to {_rel(POLICIES)}"
                )
    for path in POINTER_FILES:
        if not _policy_links(path.read_text(encoding="utf-8")):
            offenders.append(f"{_rel(path)}: carries no policies.md#<anchor> link")
    assert not offenders, "\n".join(offenders)


def test_every_make_citation_in_the_policy_doc_names_a_real_target() -> None:
    """G004's own matcher and target set, pointed at the policy document."""
    targets = set(detect.profile(REPO_ROOT).make_targets)
    assert targets, (
        "detect found no make targets in this repository, so this guard would "
        "pass vacuously -- the detector, not the citations, is what broke"
    )
    cited = sorted(set(MAKE_REF.findall(POLICIES.read_text(encoding="utf-8"))))
    missing = [stage for stage in cited if stage not in targets]
    assert not missing, (
        f"{_rel(POLICIES)} cites `make <stage>` targets this repository does not "
        f"declare: {missing}"
    )


# --- planted defects ---------------------------------------------------------

_PLANTED = (
    "# Policies\n\nIntro.\n\n- [Alpha](#alpha) — one\n- [Beta](#beta) — two\n\n"
    "## Alpha\n\n## Beta\n"
)


def test_a_dead_index_anchor_is_named() -> None:
    planted = _PLANTED.replace(
        "- [Beta](#beta) — two\n", "- [Beta](#beta) — two\n- [Gamma](#gamma) — three\n"
    )
    offenders = _index_offenders(planted)
    assert offenders == ["index anchor with no heading: #gamma"], offenders


def test_an_unindexed_policy_heading_is_named() -> None:
    planted = _PLANTED + "\n## Gamma\n"
    offenders = _index_offenders(planted)
    assert offenders == ["heading not indexed: Gamma"], offenders


def test_an_empty_policy_document_is_an_offender_not_a_pass() -> None:
    offenders = _index_offenders("# Policies\n\nNothing here.\n")
    assert "no level-two heading" in offenders and "no index entry" in offenders, offenders
    # A fenced example heading is not a heading, and a non-plain or repeated
    # heading is named rather than slugged into a collision.
    fenced = "- [Alpha](#alpha) — one\n\n```\n## Not A Heading\n```\n\n## Alpha\n"
    assert _index_offenders(fenced) == []
    odd = "- [Alpha](#alpha) — one\n\n## Alpha\n\n## Alpha\n\n## Beta: two\n"
    offenders = _index_offenders(odd)
    assert "heading not plain words: Beta: two" in offenders, offenders
    assert "heading repeated: Alpha" in offenders, offenders


def test_a_pointer_to_a_missing_fragment_is_named() -> None:
    pointer = (
        "See [the count rule](../docs/policies.md#no-such-heading) "
        "and [this](../docs/policies.md#alpha).\n"
    )
    offenders = _pointer_offenders(pointer, _PLANTED)
    assert offenders == ["#no-such-heading"], offenders
    assert _pointer_offenders("no links here\n", _PLANTED) == []
