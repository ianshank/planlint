"""Tests for the speckit rule family S001-S005, and the mandatory G002/G003
fix (add-speckit-dialect, Milestone 4).

"A linter that never fails is a decoration" -- each rule gets a fixture that
violates it and an assertion the rule fires on exactly that violation
(the philosophy stated in tests/test_graft_rules.py, mirrored here).
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from openspec_graph import detect, parse_model, rules
from openspec_graph.parse import parse_spec
from tests.support import write_speckit_spec

GOOD_SPECKIT = textwrap.dedent(
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


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return tmp_path


def findings_for(repo: Path, body: str) -> list[rules.Finding]:
    path = write_speckit_spec(repo, "001-demo-capability", body)
    prof = detect.profile(repo)
    return rules.evaluate(parse_spec(path, "speckit"), prof)


def rule_ids(findings: list[rules.Finding]) -> set[str]:
    return {f.rule for f in findings}


# --- S001: unresolved [NEEDS CLARIFICATION] marker --------------------------


def test_s001_fires_on_unresolved_needs_clarification(repo: Path) -> None:
    body = GOOD_SPECKIT.replace(
        "The system MUST attest every write.",
        "The system MUST attest every write [NEEDS CLARIFICATION: within what time bound?].",
    )
    assert "S001" in rule_ids(findings_for(repo, body))


def test_s001_does_not_fire_on_a_clean_spec(repo: Path) -> None:
    assert "S001" not in rule_ids(findings_for(repo, GOOD_SPECKIT))


def test_s001_does_not_fire_when_the_marker_is_only_inside_a_waiver_reason(repo: Path) -> None:
    # A waiver's own free-text reason quoting the literal marker while
    # explaining why S001 is being waived must not itself count as an
    # unresolved marker (R-SK-16) -- the same bug class already fixed once
    # for ADR_REF/MAKE_REF (parse.py's citation_text), now closed here too.
    body = GOOD_SPECKIT + (
        "\n<!-- specgraph:allow S001 previously had a [NEEDS CLARIFICATION] "
        "marker here, now resolved -->\n"
    )
    assert "S001" not in rule_ids(findings_for(repo, body))


# --- S002: duplicate FR-/SC- identifier --------------------------------------


def test_s002_fires_on_duplicate_fr_or_sc_id(repo: Path) -> None:
    body = GOOD_SPECKIT.replace(
        "- **FR-001**: The system MUST attest every write.",
        "- **FR-001**: The system MUST attest every write.\n"
        "- **FR-001**: A duplicate requirement id.",
    )
    assert "S002" in rule_ids(findings_for(repo, body))


def test_s002_fires_on_duplicate_criterion_id(repo: Path) -> None:
    body = GOOD_SPECKIT.replace(
        "- **SC-001**: Every write is attested before acknowledgment.",
        "- **SC-001**: Every write is attested before acknowledgment.\n"
        "- **SC-001**: A duplicate criterion id.",
    )
    assert "S002" in rule_ids(findings_for(repo, body))


def test_s002_does_not_fire_without_duplicates(repo: Path) -> None:
    assert "S002" not in rule_ids(findings_for(repo, GOOD_SPECKIT))


# --- S003: requirement with no SHALL/MUST -----------------------------------


def test_s003_fires_on_a_non_normative_requirement(repo: Path) -> None:
    body = GOOD_SPECKIT.replace(
        "- **FR-001**: The system MUST attest every write.",
        "- **FR-001**: The system attests every write.",
    )
    assert "S003" in rule_ids(findings_for(repo, body))


def test_s003_does_not_fire_on_a_normative_requirement(repo: Path) -> None:
    assert "S003" not in rule_ids(findings_for(repo, GOOD_SPECKIT))


# --- S004: scenario missing WHEN/THEN, WARN not ERROR -----------------------


def _minimal_speckit_spec(**overrides: object) -> parse_model.ParsedSpec:
    defaults: dict[str, object] = {
        "path": Path("spec.md"),
        "dialect": "speckit",
        "sections": (),
        "status": None,
        "requirements": (),
        "criteria": (),
        "make_refs": (),
        "invariant_refs": (),
        "hard_coded_thresholds": (),
        "delta_headers": (),
    }
    defaults.update(overrides)
    return parse_model.ParsedSpec(**defaults)  # type: ignore[arg-type]


def test_s004_fires_at_warn_not_error(repo: Path) -> None:
    # Unit-test S004's check function directly against a hand-built
    # ParsedSpec, the same direct-construction pattern tests/test_ledger.py
    # already uses -- independent of whatever real parsing does or doesn't
    # produce, so this stays a pure check-function test.
    spec = _minimal_speckit_spec(
        criteria=(
            parse_model.Criterion(
                ident="US1-AS1",
                text="an incomplete scenario",
                note="Given a precondition, something happens eventually.",
            ),
        ),
    )
    prof = detect.profile(repo)
    findings = [f for f in rules.evaluate(spec, prof) if f.rule == "S004"]
    assert len(findings) == 1
    assert findings[0].severity == "WARN"


def test_s004_fires_through_real_parsing_on_a_malformed_scenario(repo: Path) -> None:
    # Post-review hardening: GWT_SCENARIO originally required the literal
    # Given/When/Then keywords to match at all, so parse_speckit() could
    # never actually produce a Criterion for a malformed scenario missing
    # WHEN/THEN -- S004 was only reachable via the hand-built ParsedSpec
    # above, never through real parsing. GWT_SCENARIO now matches any
    # numbered item in a User Story block; completeness is decided
    # downstream by scenario_has_gwt(), so a genuinely malformed real
    # scenario is captured and now actually reaches S004.
    body = GOOD_SPECKIT.replace(
        "1. **Given** an unattested write, **When** validation runs, **Then** the write is rejected.",
        "1. **Given** an unattested write, something happens eventually but no outcome is stated.",
    )
    findings = [f for f in findings_for(repo, body) if f.rule == "S004"]
    assert len(findings) == 1
    assert findings[0].severity == "WARN"


def test_s004_does_not_fire_on_success_criteria_with_no_note(repo: Path) -> None:
    # An SC-00N Success Criterion never carries a `note` -- must not be
    # reported as "missing WHEN/THEN", a claim it never made.
    spec = _minimal_speckit_spec(
        criteria=(parse_model.Criterion(ident="SC-001", text="a measurable outcome"),),
    )
    prof = detect.profile(repo)
    assert "S004" not in {f.rule for f in rules.evaluate(spec, prof)}


# --- Mandatory fix: G002/G003 scoped away from speckit false positives -----


def test_g002_does_not_fire_on_a_positive_only_speckit_spec(repo: Path) -> None:
    # GOOD_SPECKIT's only negative-phrased criterion is the GWT scenario
    # ("...the write is rejected"); a purely positive-phrased spec must not
    # trip G002 now that it's scoped to harness/upstream only (R-SK-18).
    body = GOOD_SPECKIT.replace(
        "1. **Given** an unattested write, **When** validation runs, **Then** the write is rejected.",
        "1. **Given** an attested write, **When** validation runs, **Then** the write succeeds.",
    )
    assert "G002" not in rule_ids(findings_for(repo, body))


def test_g003_does_not_fire_on_a_success_criteria_percentage(repo: Path) -> None:
    body = GOOD_SPECKIT.replace(
        "- **SC-001**: Every write is attested before acknowledgment.",
        "- **SC-001**: 95% of new users complete onboarding in under 5 minutes.",
    )
    assert "G003" not in rule_ids(findings_for(repo, body))


def test_g003_does_not_fire_with_the_canonical_annotated_heading(repo: Path) -> None:
    # The real github/spec-kit template writes "## Success Criteria
    # *(mandatory)*", not the bare heading -- reproduces the gap an
    # exact-title section lookup would have here and proves the fix.
    body = GOOD_SPECKIT.replace(
        "## Success Criteria\n\n- **SC-001**: Every write is attested before acknowledgment.",
        "## Success Criteria *(mandatory)*\n\n"
        "- **SC-001**: 95% of new users complete onboarding in under 5 minutes.",
    )
    assert "G003" not in rule_ids(findings_for(repo, body))


def test_g003_still_fires_on_a_speckit_threshold_outside_success_criteria(repo: Path) -> None:
    # The exemption is scoped to the Success Criteria section body only --
    # a bare percentage anywhere else in a speckit spec is still a real
    # hard-coded-threshold violation.
    body = GOOD_SPECKIT.replace(
        "- **FR-001**: The system MUST attest every write.",
        "- **FR-001**: The system MUST attest 95% of writes.",
    )
    assert "G003" in rule_ids(findings_for(repo, body))


def test_g003_hard_coded_threshold_scan_unaffected_when_no_success_criteria_heading(
    repo: Path,
) -> None:
    # dialect == "speckit" but section_body() finds no "Success Criteria"
    # heading at all -- the blanking branch must be a no-op, not a crash,
    # and the full text is still scanned as normal.
    body = GOOD_SPECKIT.replace(
        "\n## Success Criteria *(mandatory)*\n\n"
        "- **SC-001**: Every write is attested before acknowledgment.\n",
        "\n",
    ).replace(
        "- **FR-001**: The system MUST attest every write.",
        "- **FR-001**: The system MUST attest 95% of writes.",
    )
    assert "## Success Criteria" not in body
    assert "G003" in rule_ids(findings_for(repo, body))


def test_g002_g003_byte_unchanged_for_harness_and_upstream_fixtures(repo: Path) -> None:
    # C-SK-8/AC-SK-35: existing dialects' G002/G003 behavior must be
    # byte-unchanged by this change -- both golden "good" fixtures still
    # pass cleanly (G002 stays wired for harness/upstream; G003's speckit
    # exemption is a no-op for dialects without a Success Criteria heading).
    fixtures = Path(__file__).resolve().parent / "fixtures"
    for name, dialect in (("good_harness.md", "harness"), ("good_upstream.md", "upstream")):
        text = (fixtures / name).read_text(encoding="utf-8")
        path = repo / f"{dialect}-spec.md"
        path.write_text(text, encoding="utf-8")
        prof = detect.profile(repo)
        found = rule_ids(rules.evaluate(parse_spec(path, dialect), prof))
        assert "G002" not in found
        assert "G003" not in found


# --- C-SK-4/AC-SK-38 (non-success): no "orphaned requirement" speckit rule -


def test_rules_py_registers_speckit_rules_additively() -> None:
    # R-SK-17: NON_WITNESS_RULES = GENERIC + HARNESS + UPSTREAM + SPECKIT --
    # a pure append. Confirms G/H/U weren't disturbed (interleaved, reordered,
    # or replaced) by the addition, not just that S001-S004 exist somewhere.
    from openspec_graph.rules_generic import GENERIC_RULES
    from openspec_graph.rules_harness import HARNESS_RULES
    from openspec_graph.rules_speckit import SPECKIT_RULES
    from openspec_graph.rules_upstream import UPSTREAM_RULES

    assert rules.NON_WITNESS_RULES == GENERIC_RULES + HARNESS_RULES + UPSTREAM_RULES + SPECKIT_RULES
    assert rules.NON_WITNESS_RULES[-len(SPECKIT_RULES) :] == SPECKIT_RULES


def test_no_orphan_requirement_rule_exists_for_speckit() -> None:
    """C-SK-4: no *orphaned-requirement* rule may be added for speckit.

    The second assertion is the load-bearing one and is unchanged. The set
    below is a proxy that grew with `lint-empty-speckit-requirements`, which
    added S005.

    AC-SK-38 wrote "lists exactly S001-S004 as the new speckit family", which
    was a true description of what *that* change added. It is not a standing
    bar on the family ever growing -- read that way it would freeze the
    dialect permanently, which C-SK-4, the actual constraint, does not say.
    S005 flags a Requirements section that yielded no requirement; it is an
    empty-section rule, not an orphan-requirement rule, so C-SK-4 holds
    intact. See DEC-SER in the change package for the full argument.
    """
    speckit_idents = {r.ident for r in rules.RULES if "speckit" in r.dialects}
    assert speckit_idents == {"S001", "S002", "S003", "S004", "S005"}
    for r in rules.RULES:
        if r.ident.startswith("S"):
            assert "orphan" not in r.summary.lower()


# --- C-SK-9/AC-SK-39 (non-success): scaffold.py untouched -------------------


def test_scaffold_still_only_offers_harness_and_upstream() -> None:
    from openspec_graph import scaffold_templates

    assert hasattr(scaffold_templates, "spec_harness")
    assert hasattr(scaffold_templates, "spec_upstream")
    assert not hasattr(scaffold_templates, "spec_speckit")


# --- S005: a Requirements section that yielded nothing ----------------------
#
# docs/peer-review-2026-09.md F4. `parse_speckit` scopes the FR scan to a
# level-3 heading nested in the level-2 `Requirements` span; a hand-edited spec
# writing it one level up loses every requirement from the graph while validate
# reports 0/0/0 PASS and broken_links 0.

_WRONG_LEVEL = textwrap.dedent(
    """\
    # Feature Specification: Demo

    ## Requirements *(mandatory)*

    ## Functional Requirements

    - **FR-001**: The system MUST do the thing.
    - **FR-002**: The system MUST reject a bad input.

    ## Success Criteria *(mandatory)*

    - **SC-001**: The thing completes in under a second.
    """
)

_USER_STORY_ONLY = textwrap.dedent(
    """\
    # Feature Specification: Demo

    ## User Scenarios *(mandatory)*

    - As a user I want the thing so that it helps.

    ## Success Criteria *(mandatory)*

    - **SC-001**: The thing completes in under a second.
    """
)


def test_s005_fires_when_a_requirements_section_yields_nothing(repo: Path) -> None:
    found = [f for f in findings_for(repo, _WRONG_LEVEL) if f.rule == "S005"]
    assert len(found) == 1, found
    assert found[0].severity == "WARN"
    # The exact line, not merely a positive one: the contract is that the locus
    # is the FIRST DROPPED BULLET -- the token the author has to move. A
    # regression reporting the heading, or line 1, would satisfy `> 0`.
    expected = next(
        i for i, ln in enumerate(_WRONG_LEVEL.splitlines(), 1)
        if ln.startswith("- **FR-001**")
    )
    assert found[0].line == expected, (found[0].line, expected)


def test_s005_is_silent_on_the_canonical_nesting(repo: Path) -> None:
    """Non-success: the shape SpecKit's own template produces must stay quiet."""
    body = _WRONG_LEVEL.replace("## Functional Requirements", "### Functional Requirements")
    assert "S005" not in {f.rule for f in findings_for(repo, body)}


def test_s005_is_silent_on_a_user_story_only_draft(repo: Path) -> None:
    """Non-success: THE false positive docs/next-steps.md item 4b refused.

    A draft that never declares a Requirements section has not lost anything;
    the discrimination is "declared and yielded nothing", not "yielded
    nothing".
    """
    assert "S005" not in {f.rule for f in findings_for(repo, _USER_STORY_ONLY)}


def test_s005_does_not_match_non_functional_requirements(repo: Path) -> None:
    """Non-success: equality, never containment.

    `Non-Functional Requirements` declares something else and promises no FR
    bullets; matching it by substring would fire on a correct document.
    """
    body = _USER_STORY_ONLY.replace(
        "## User Scenarios *(mandatory)*", "## Non-Functional Requirements"
    )
    assert "S005" not in {f.rule for f in findings_for(repo, body)}


def test_s005_is_silent_on_a_requirements_section_with_no_bullets(repo: Path) -> None:
    """Non-success: the predicate is data loss, not document shape.

    A section that declares no FR- bullet has not lost one. An earlier draft
    keyed on the heading and fired here; the adversarial review showed the same
    predicate also fires on a legitimately NFR-only spec under SpecKit's own
    mandatory `## Requirements` wrapper, which is the false positive
    docs/next-steps.md item 4b refused. Keying on dropped bullets removes both.
    """
    body = textwrap.dedent(
        """\
        # Feature Specification: Demo

        ## Requirements *(mandatory)*

        We will decide the requirements once the design settles.

        ## Success Criteria *(mandatory)*

        - **SC-001**: The thing completes in under a second.
        """
    )
    assert "S005" not in {f.rule for f in findings_for(repo, body)}


def test_s005_is_silent_on_a_non_functional_only_spec(repo: Path) -> None:
    """Non-success: THE false positive the adversarial review reproduced.

    SpecKit's template makes the `## Requirements` H2 wrapper mandatory, so a
    heading-based predicate swallows every document whose requirements are
    non-functional and tells its author things were "dropped" when none existed.
    """
    body = textwrap.dedent(
        """\
        # Feature Specification: Demo

        ## Requirements *(mandatory)*

        ### Non-Functional Requirements

        - The system responds within one second under nominal load.

        ## Success Criteria *(mandatory)*

        - **SC-001**: The thing completes in under a second.
        """
    )
    assert "S005" not in {f.rule for f in findings_for(repo, body)}


def test_s005_fires_on_fr_bullets_under_a_differently_titled_subheading(repo: Path) -> None:
    """A shape a heading-based predicate misses entirely.

    `### Core Requirements` holding FR- bullets is refused by the parser
    (AC-SK-49) and is exactly as lost as the wrong-level case.
    """
    body = textwrap.dedent(
        """\
        # Feature Specification: Demo

        ## Requirements *(mandatory)*

        ### Core Requirements

        - **FR-001**: The system MUST do the thing.

        ## Success Criteria *(mandatory)*

        - **SC-001**: The thing completes in under a second.
        """
    )
    assert "S005" in {f.rule for f in findings_for(repo, body)}


def test_s005_ignores_fr_bullets_inside_a_multiline_comment(repo: Path) -> None:
    """Non-success: a comment's own text is not the document's content.

    `strip_waiver_comments` alone is not enough here. `SUPPRESS` has no
    `re.DOTALL`, so a MULTI-LINE waiver comment is never matched and its reason
    text survives into the scanned document -- reproduced by the adversarial
    review, where the waiver both failed to register and tripped the rule it
    was trying to waive. That is the third recurrence of the class
    `strip_waiver_comments`'s own docstring records, so S005 blanks every HTML
    comment rather than only the well-formed waivers.
    """
    body = textwrap.dedent(
        """\
        # Feature Specification: Demo

        <!-- specgraph:allow S005
        - **FR-001**: quoted inside this waiver's reason text
        -->

        ## Success Criteria *(mandatory)*

        - **SC-001**: The thing completes in under a second.
        """
    )
    assert "S005" not in {f.rule for f in findings_for(repo, body)}


def test_blank_html_comments_preserves_length_and_line_numbers() -> None:
    """The locus contract (DEC-LH / R-LH-14) survives blanking.

    Blanking newlines would merge lines and shift every subsequent finding's
    line by an amount nobody can see.
    """
    from openspec_graph.parse_semantics import blank_html_comments

    raw = "a\n<!-- one\ntwo -->\nb\n"
    out = blank_html_comments(raw)
    assert len(out) == len(raw)
    assert out.count("\n") == raw.count("\n")
    assert out.splitlines()[0] == "a"
    assert out.splitlines()[3] == "b"
    assert "one" not in out and "two" not in out


def test_s005_never_evaluates_for_the_harness_dialect(repo: Path) -> None:
    """Non-success: this repo's own harness specs all carry `## Requirements`
    and zero FR- bullets. A dialect leak would light up its entire tree."""
    from openspec_graph.rules import RULES

    s005 = next(r for r in RULES if r.ident == "S005")
    assert not s005.applies("harness")
    assert not s005.applies("upstream")
    assert s005.applies("speckit")


def test_s005_is_silent_on_fr_bullets_inside_a_fenced_code_block(repo: Path) -> None:
    """Non-success: a fenced block illustrates, it does not declare.

    S005 scans the raw document deliberately -- the whole point is to see
    bullets the parser's scoped span missed -- which meant a spec DOCUMENTING
    the canonical requirement form was told its requirements had been dropped.
    SpecKit authors and this repository's own change packages write that block
    constantly.
    """
    body = textwrap.dedent(
        """\
        # Feature Specification: Demo

        ## Overview

        The canonical form looks like this:

        ```markdown
        ### Functional Requirements

        - **FR-001**: The system MUST do the thing.
        ```

        ## Success Criteria *(mandatory)*

        - **SC-001**: The thing completes in under a second.
        """
    )
    assert "S005" not in {f.rule for f in findings_for(repo, body)}


def test_s005_fires_on_indented_fr_bullets_the_parser_drops(repo: Path) -> None:
    """The failure mode S005 exists for, previously invisible by construction.

    `FR_DECL` anchors the hyphen at column 0, so a sub-item under a grouping
    line is dropped silently. Detecting that loss with the same pattern that
    caused it cannot work -- the probe and the parser shared the blind spot.
    `FR_DECL_LOOSE` allows leading whitespace and differs in nothing else, so
    the probe is a strict superset of the grammar it audits.
    """
    body = textwrap.dedent(
        """\
        # Feature Specification: Demo

        ## Requirements *(mandatory)*

        ### Functional Requirements

        - Group A:
          - **FR-001**: The system MUST do the thing.

        ## Success Criteria *(mandatory)*

        - **SC-001**: The thing completes in under a second.
        """
    )
    found = [f for f in findings_for(repo, body) if f.rule == "S005"]
    assert len(found) == 1, found


def test_blank_fenced_code_preserves_length_and_lines() -> None:
    """The locus contract again: a finding after a block must name its real line."""
    from openspec_graph.parse_semantics import blank_fenced_code

    raw = "a\n```py\nx = 1\n```\nb\n"
    out = blank_fenced_code(raw)
    assert len(out) == len(raw)
    assert out.count("\n") == raw.count("\n")
    assert out.splitlines()[0] == "a"
    assert out.splitlines()[4] == "b"
    assert "x = 1" not in out


def test_blank_fenced_code_handles_an_unterminated_fence() -> None:
    """An unterminated fence runs to end of document, as a reader sees it."""
    from openspec_graph.parse_semantics import blank_fenced_code

    out = blank_fenced_code("a\n```\n- **FR-001**: x\n")
    assert "FR-001" not in out
