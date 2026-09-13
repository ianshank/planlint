"""Finding line hits: CheckHit, parser loci, migrated rules, projections.

Change package: ``add-finding-line-hits``. A linter that never fails is a
decoration — each named acceptance criterion here has a fixture that would
have produced the wrong line (or none) before this change.
"""

from __future__ import annotations

import dataclasses
import logging
import textwrap
from pathlib import Path

import pytest

from openspec_graph import detect, report, rules, sarif
from openspec_graph.parse import ParsedSpec, parse_spec
from openspec_graph.parse_harness import parse_harness
from openspec_graph.parse_semantics import (
    AC,
    line_of,
    parse_waivers,
    section_body,
    section_span,
)
from openspec_graph.parse_speckit import parse_speckit
from openspec_graph.parse_upstream import parse_upstream
from openspec_graph.rule_types import (
    ERROR,
    FINDINGS_SCHEMA_VERSION,
    CheckHit,
    as_check_hit,
)
from tests.support import write_spec, write_speckit_spec

MAKEFILE = textwrap.dedent(
    """\
    .PHONY: test regression
    test:
    \tpytest
    regression:
    \tpytest tests/regression
    """
)

HARNESS = textwrap.dedent(
    """\
    # Spec: Demo Capability

    > **Status:** DRAFT

    ## Problem Statement

    **Evidence:** `demo/mod.py::run` writes without attestation.

    ## Requirements

    - R-DMO-1: The system MUST attest every write.
    - C-DMO-1: The change MUST NOT weaken INV-1.

    ## Acceptance Criteria

    - [ ] **AC-DMO-1:** An attested write records an evidence id. (R-DMO-1)
      _Verified by:_ `pytest -k test_attested_write` · stage: `make regression`

    - [ ] **AC-DMO-2 (non-success):** An unattested write is denied and the
      error names INV-1. (C-DMO-1)
      _Verified by:_ `pytest -k test_unattested_denied` · stage: `make regression`

    ## Validation Matrix

    | Stage | Make Target | Pass Criteria |
    |---|---|---|
    | Focused | `make regression` | AC-DMO-1..2 |
    """
)

UPSTREAM = textwrap.dedent(
    """\
    # Spec delta — Demo capability

    ## ADDED Requirements

    ### Requirement: the writer SHALL attest every write

    Prose obligation.

    #### Scenario: attested writes record an evidence id

    - **GIVEN** an attested writer
    - **WHEN** `make regression` runs the suite
    - **THEN** an evidence id is recorded

    #### Scenario: an unattested write is caught before merge

    - **GIVEN** a writer with no attestation
    - **WHEN** the suite runs
    - **THEN** the check fails and names the offending file
    """
)

SPECKIT = textwrap.dedent(
    """\
    # Feature Specification: Demo Capability

    **Feature Branch**: `001-demo-capability`
    **Status**: Draft

    ## User Scenarios & Testing

    ### User Story 1 - Reject unattested writes (Priority: P1)

    **Acceptance Scenarios**:

    1. **Given** an unattested write, **When** validation runs, **Then** the write is rejected.

    ## Requirements *(mandatory)*

    ### Functional Requirements

    - **FR-001**: The system MUST attest every write.

    ## Success Criteria *(mandatory)*

    - **SC-001**: Every write is attested before acknowledgment.
    """
)


def _line_containing(text: str, needle: str) -> int:
    for index, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return index
    raise AssertionError(f"{needle!r} not in document")


def _blank_spec(path: Path) -> ParsedSpec:
    return ParsedSpec(
        path=path,
        dialect="harness",
        sections=(),
        status=None,
        requirements=(),
        criteria=(),
        make_refs=(),
        invariant_refs=(),
        hard_coded_thresholds=(),
        delta_headers=(),
    )


def _evaluate_one(tmp_path: Path, check, dialects: tuple[str, ...] = ("*",)):
    spec = _blank_spec(tmp_path / "spec.md")
    prof = detect.profile(tmp_path)
    rule = rules.Rule("T001", ERROR, dialects, "test locus", check)
    return rules.evaluate(spec, prof, (rule,))


def test_as_check_hit_coerces_a_string_to_line_zero() -> None:
    hit = as_check_hit("bare")
    assert hit.message == "bare"
    assert hit.line == 0
    original = CheckHit(message="kept", line=9)
    assert as_check_hit(original) is original
    assert rules.CheckHit is CheckHit
    from openspec_graph import rule_types

    assert rule_types.as_check_hit is as_check_hit


def test_evaluate_copies_checkhit_line_onto_finding(tmp_path: Path) -> None:
    def check(_spec: ParsedSpec, _profile: object):
        yield CheckHit("boom", line=12)

    found = _evaluate_one(tmp_path, check)
    assert len(found) == 1
    assert found[0].line == 12
    assert found[0].message == "boom"


def test_evaluate_stores_zero_for_nonpositive_checkhit_line(tmp_path: Path) -> None:
    def check(_spec: ParsedSpec, _profile: object):
        yield CheckHit("neg", line=-3)
        yield CheckHit("zero", line=0)
        yield "bare-str"

    found = _evaluate_one(tmp_path, check)
    assert [item.line for item in found] == [0, 0, 0]


def test_evaluate_does_not_clamp_zero_to_one(tmp_path: Path) -> None:
    def check(_spec: ParsedSpec, _profile: object):
        yield CheckHit("unset", line=0)

    found = _evaluate_one(tmp_path, check)
    assert found[0].line == 0


def test_evaluate_debug_log_names_rule_and_line_not_message(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    marker = "finding-body-must-not-be-logged"

    def check(_spec: ParsedSpec, _profile: object):
        yield CheckHit(marker, line=12)

    logger = logging.getLogger("planlint.rules")
    logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.DEBUG, logger="planlint.rules"):
            _evaluate_one(tmp_path, check)
    finally:
        logger.removeHandler(caplog.handler)
    messages = [record.getMessage() for record in caplog.records]
    assert messages
    assert any("T001" in msg and "12" in msg for msg in messages)
    assert all(marker not in msg for msg in messages)


def test_evaluate_is_silent_at_default_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    def check(_spec: ParsedSpec, _profile: object):
        yield CheckHit("quiet-default", line=4)

    logger = logging.getLogger("planlint.rules")
    logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.WARNING, logger="planlint.rules"):
            _evaluate_one(tmp_path, check)
    finally:
        logger.removeHandler(caplog.handler)
    assert caplog.records == []


def test_requirement_line_is_one_based_in_harness_upstream_and_speckit() -> None:
    reqs, _ = parse_harness(HARNESS)
    harness_req = next(req for req in reqs if req.ident == "R-DMO-1")
    assert harness_req.line == _line_containing(HARNESS, "- R-DMO-1:")

    ureqs, _ = parse_upstream(UPSTREAM)
    heading = "### Requirement: the writer SHALL attest every write"
    assert ureqs[0].line == _line_containing(UPSTREAM, heading)

    sreqs, _ = parse_speckit(SPECKIT)
    fr = next(req for req in sreqs if req.ident == "FR-001")
    assert fr.line == _line_containing(SPECKIT, "- **FR-001**:")


def test_harness_criterion_line_is_the_ac_bullet_not_a_duplicate_prefix() -> None:
    # Distinct ids with a shared description do not collide: the ident sits
    # inside block[:60]. Quote the second AC's block[:60] in Problem Statement
    # so text.find would hit the quote (spec-adversary finding on AC-LH-7).
    second_open = (
        "- [ ] **AC-DUP-2:** Shared prefix text that is definitely longer "
        "than sixty characters in this block."
    )
    text = textwrap.dedent(
        f"""\
        # Spec: Duplicate prefix

        > **Status:** DRAFT

        ## Problem Statement

        Quoted earlier: `{second_open}`

        ## Requirements

        - R-DUP-1: The system MUST attest every write.

        ## Acceptance Criteria

        - [ ] **AC-DUP-1:** First unique criterion. (R-DUP-1)
          _Verified by:_ `pytest -k test_a` · stage: `make test`

        {second_open} (R-DUP-1)
          _Verified by:_ `pytest -k test_b` · stage: `make test`

        ## Validation Matrix

        | Stage | Make Target | Pass Criteria |
        |---|---|---|
        | Focused | `make test` | AC-DUP-1..2 |
        """
    )
    _reqs, criteria = parse_harness(text)
    second = next(crit for crit in criteria if crit.ident == "AC-DUP-2")
    expected = [
        index
        for index, line in enumerate(text.splitlines(), 1)
        if "**AC-DUP-2:**" in line
    ][-1]
    # The quote in Problem Statement is an earlier copy of the same needle;
    # the criterion line must be the later AC bullet.
    quote_line = next(
        index
        for index, line in enumerate(text.splitlines(), 1)
        if "Quoted earlier" in line
    )
    assert quote_line < expected
    assert second.line == expected

    _origin, body = section_span(text, "Acceptance Criteria")
    matches = list(AC.finditer(body))
    second_match = matches[1]
    stop = len(body) if len(matches) < 3 else matches[2].start()
    block = body[second_match.start() : stop]
    old_line = line_of(text, text.find(block[:60]))
    assert old_line == quote_line
    assert second.line != old_line


def test_section_body_still_returns_only_the_span_text() -> None:
    origin, body = section_span(HARNESS, "Requirements")
    result = section_body(HARNESS, "Requirements")
    assert isinstance(result, str)
    assert result == body
    assert not isinstance(result, tuple)
    assert origin >= 1
    assert section_body(HARNESS, "No Such Section") == ""
    assert section_span(HARNESS, "No Such Section") == (0, "")


def test_g007_finding_line_equals_waiver_line(tmp_path: Path) -> None:
    (tmp_path / "Makefile").write_text(MAKEFILE, encoding="utf-8")
    body = HARNESS.replace(
        "## Problem Statement",
        "<!-- specgraph:allow G007 -->\n\n## Problem Statement",
    )
    path = write_spec(tmp_path, "demo-change", "demo-capability", body)
    found = [item for item in rules.evaluate(parse_spec(path, "harness"), detect.profile(tmp_path)) if item.rule == "G007"]
    waiver = parse_waivers(body)[0]
    assert found
    assert found[0].line == waiver.line
    assert found[0].message == (
        f"waiver of {waiver.rule} at line {waiver.line} has no reason; "
        "a waiver is a claim that must justify itself"
    )


def test_h001_finding_line_is_the_criterion_line(tmp_path: Path) -> None:
    (tmp_path / "Makefile").write_text(MAKEFILE, encoding="utf-8")
    body = HARNESS.replace(
        "  _Verified by:_ `pytest -k test_attested_write` · stage: `make regression`\n",
        "",
    )
    path = write_spec(tmp_path, "demo-change", "demo-capability", body)
    spec = parse_spec(path, "harness")
    crit = next(item for item in spec.criteria if item.ident == "AC-DMO-1")
    found = [item for item in rules.evaluate(spec, detect.profile(tmp_path)) if item.rule == "H001"]
    assert found
    assert found[0].line == crit.line
    assert found[0].line == _line_containing(body, "**AC-DMO-1:**")


def test_u003_finding_line_is_the_scenario_line(tmp_path: Path) -> None:
    (tmp_path / "Makefile").write_text(MAKEFILE, encoding="utf-8")
    body = UPSTREAM.replace("- **THEN** an evidence id is recorded", "- it works")
    path = write_spec(tmp_path, "demo-change", "demo-capability", body)
    spec = parse_spec(path, "upstream")
    crit = next(item for item in spec.criteria if item.ident == "SCEN-1")
    found = [item for item in rules.evaluate(spec, detect.profile(tmp_path)) if item.rule == "U003"]
    assert found
    assert found[0].line == crit.line
    assert found[0].line == _line_containing(body, "#### Scenario: attested writes")


def test_s001_finding_line_is_the_clarification_marker(tmp_path: Path) -> None:
    marker = "[NEEDS CLARIFICATION: within what time bound?]"
    body = SPECKIT.replace(
        "The system MUST attest every write.",
        f"The system MUST attest every write {marker}",
    )
    path = write_speckit_spec(tmp_path, "001-demo-capability", body)
    spec = parse_spec(path, "speckit")
    found = [item for item in rules.evaluate(spec, detect.profile(tmp_path)) if item.rule == "S001"]
    assert found
    assert found[0].line == _line_containing(body, marker)


def test_h003_finding_line_is_the_orphan_requirement_line(tmp_path: Path) -> None:
    (tmp_path / "Makefile").write_text(MAKEFILE, encoding="utf-8")
    body = HARNESS.replace(
        "- C-DMO-1: The change MUST NOT weaken INV-1.",
        "- C-DMO-1: The change MUST NOT weaken INV-1.\n- R-DMO-9: MUST also do an untested thing.",
    )
    path = write_spec(tmp_path, "demo-change", "demo-capability", body)
    spec = parse_spec(path, "harness")
    assert "R-DMO-9" in spec.orphan_requirements
    req = next(item for item in spec.requirements if item.ident == "R-DMO-9")
    found = [item for item in rules.evaluate(spec, detect.profile(tmp_path)) if item.rule == "H003"]
    assert found
    assert found[0].line == req.line
    assert found[0].line == _line_containing(body, "- R-DMO-9:")


def test_w001_finding_line_is_the_criterion_line(tmp_path: Path) -> None:
    (tmp_path / "Makefile").write_text(MAKEFILE, encoding="utf-8")
    path = write_spec(tmp_path, "demo-change", "demo-capability", HARNESS)
    spec = parse_spec(path, "harness")
    prof = dataclasses.replace(detect.profile(tmp_path), witnesses=(), current_sha=None)
    found = [item for item in rules.evaluate(spec, prof, rules.RULES) if item.rule == "W001"]
    assert found
    by_ident = {crit.ident: crit.line for crit in spec.criteria}
    assert found[0].line == by_ident[spec.criteria[0].ident]
    assert all(item.line >= 1 for item in found)


def test_migrated_error_round_trips_to_sarif_start_line(tmp_path: Path) -> None:
    (tmp_path / "Makefile").write_text(MAKEFILE, encoding="utf-8")
    body = HARNESS.replace(
        "  _Verified by:_ `pytest -k test_attested_write` · stage: `make regression`\n",
        "",
    )
    path = write_spec(tmp_path, "demo-change", "demo-capability", body)
    spec = parse_spec(path, "harness")
    found = next(
        item for item in rules.evaluate(spec, detect.profile(tmp_path)) if item.rule == "H001"
    )
    assert found.line >= 1
    payload = sarif.to_sarif(
        [found.as_dict(tmp_path)],
        rules.rule_table(),
        tool_version="0.2.0",
    )
    physical = payload["runs"][0]["results"][0]["locations"][0]["physicalLocation"]
    assert physical["region"]["startLine"] == found.line
    envelope = report.parse_envelope(
        {
            "schema_version": FINDINGS_SCHEMA_VERSION,
            "tool_version": "0.2.0",
            "target": str(tmp_path),
            "specs_checked": 1,
            "findings": [found.as_dict(tmp_path)],
            "blocking": 1,
        },
        schema_version=FINDINGS_SCHEMA_VERSION,
    )
    annotation = report.to_annotations(envelope)[0]
    assert f"line={found.line}" in annotation
