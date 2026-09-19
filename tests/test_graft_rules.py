"""One violating fixture per rule, plus the clean baselines they contrast with.

The important tests are the negative ones: a linter that never fails is a
decoration. Each rule gets a fixture that violates it and an assertion that
the rule fires on exactly that violation.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

from openspec_graph import detect, rules
from openspec_graph.cli import main
from openspec_graph.parse import parse_spec
from tests.graft_support import (
    GOOD_HARNESS,
    GOOD_UPSTREAM,
    findings_for,
    rule_ids,
    tree_findings_for,
)
from tests.support import write_spec

# --- clean baselines -------------------------------------------------------


def test_good_harness_spec_has_no_errors(repo: Path) -> None:
    found = findings_for(repo, GOOD_HARNESS)
    assert [f for f in found if f.severity == "ERROR"] == []


def test_good_upstream_spec_has_no_errors(repo: Path) -> None:
    found = findings_for(repo, GOOD_UPSTREAM)
    assert [f for f in found if f.severity == "ERROR"] == []


# --- negative cases, one per rule -----------------------------------------


def test_g001_fires_when_no_criteria(repo: Path) -> None:
    body = "# Spec: Empty\n\n## Requirements\n\n- R-DMO-1: MUST do a thing.\n"
    assert "G001" in rule_ids(findings_for(repo, body, "harness"))


def test_g001_fires_when_neither_requirements_nor_criteria_are_recognized(repo: Path) -> None:
    # Distinct from test_g001_fires_when_no_criteria: that fixture has
    # requirements but no criteria (rules_generic.py's `if` branch); this one
    # has neither (the `else` branch), which was previously untested.
    body = "# Spec: Empty\n\nJust prose; no requirements or acceptance criteria at all.\n"
    found = findings_for(repo, body, "harness")
    matching = [f for f in found if f.rule == "G001"]
    assert matching, "G001 must fire when nothing is recognized"
    assert any("no requirements and no verifiable criteria" in f.message for f in matching), (
        "must hit the 'neither' branch's message, not the 'requirements but no criteria' branch"
    )


def test_harness_dialect_falls_back_to_upstream_when_the_text_is_actually_upstream(
    repo: Path,
) -> None:
    # A repo classified "harness" but this one file is written in upstream
    # form -- _parse_harness finds nothing, but the text matches the
    # upstream REQUIREMENT pattern, so parse_spec must re-parse it as
    # upstream rather than reporting a false G001 "no criteria" finding.
    # This is the per-file misclassification safety net for mixed repos.
    path = write_spec(repo, "demo-change", "demo-capability", GOOD_UPSTREAM)
    parsed = parse_spec(path, "harness")
    assert parsed.dialect == "upstream"
    assert parsed.requirements and parsed.criteria

    found = findings_for(repo, GOOD_UPSTREAM, "harness")
    assert "G001" not in rule_ids(found), "the upstream-form criteria must be recognized, not missed"


def test_g002_fires_when_every_criterion_is_a_happy_path(repo: Path) -> None:
    body = GOOD_HARNESS.replace(
        "**AC-DMO-2 (non-success):** An unattested write is denied and the\n  error names INV-1.",
        "**AC-DMO-2:** A second attested write also records an id.",
    )
    found = rule_ids(findings_for(repo, body))
    assert "G002" in found, "spec with no failure path must be rejected"


def test_g003_fires_on_hard_coded_threshold(repo: Path) -> None:
    # 95%, not the repo fixture's real floor of 90 -- this line has exactly
    # one threshold-shaped number, and it does NOT match, so it stays a
    # genuine violation after the value-comparison suppression lands.
    body = GOOD_HARNESS.replace(
        "An attested write records an evidence id.",
        "Line coverage is at least 95% for the new module.",
    )
    assert "G003" in rule_ids(findings_for(repo, body))


def test_g003_suppresses_a_bare_number_that_matches_the_real_threshold(repo: Path) -> None:
    # The repo fixture's real floor is 90 -- a single, unambiguous, matching
    # number needs no locator name to be excused.
    body = GOOD_HARNESS.replace(
        "An attested write records an evidence id.",
        "Line coverage is at least 90% for the new module.",
    )
    assert "G003" not in rule_ids(findings_for(repo, body))


def test_g003_still_fires_on_the_non_matching_number_in_a_same_line_collision(repo: Path) -> None:
    # Two threshold-shaped numbers on one line, only one matching the real
    # floor -- must never suppress on a coincidental match to unrelated text.
    body = GOOD_HARNESS.replace(
        "An attested write records an evidence id.",
        "Coverage moved from 80% to 90% after the refactor.",
    )
    assert "G003" in rule_ids(findings_for(repo, body))


def test_g003_allows_a_threshold_read_from_the_policy_locator(repo: Path) -> None:
    body = GOOD_HARNESS.replace(
        "An attested write records an evidence id.",
        "Coverage meets the floor in `pyproject.toml` (currently 90%).",
    )
    assert "G003" not in rule_ids(findings_for(repo, body))


def test_g003_allows_a_threshold_read_from_coveragerc(repo: Path) -> None:
    (repo / "pyproject.toml").write_text('[project]\nname = "demo"\n')
    (repo / ".coveragerc").write_text("[report]\nfail_under = 90\n")
    body = GOOD_HARNESS.replace(
        "An attested write records an evidence id.",
        "Coverage meets the floor in `.coveragerc` (currently 90%).",
    )
    assert "G003" not in rule_ids(findings_for(repo, body))


def test_g004_fires_on_a_make_target_the_target_repo_lacks(repo: Path) -> None:
    body = GOOD_HARNESS.replace("make regression", "make test-governance")
    found = findings_for(repo, body)
    assert "G004" in rule_ids(found)
    assert any("test-governance" in f.message for f in found)


def test_g004_does_not_fire_on_a_bare_english_use_of_make(repo: Path) -> None:
    # Lowercase "make sure"/"make progress" in ordinary prose, with no
    # backtick-fencing, must not be treated as a stage citation.
    body = GOOD_HARNESS.replace(
        "An attested write records an evidence id.",
        "Reviewers make sure every write is attested, so the team can make progress.",
    )
    assert "G004" not in rule_ids(findings_for(repo, body))


def test_g005_fires_on_an_undeclared_invariant(repo: Path) -> None:
    body = GOOD_HARNESS.replace("INV-1", "INV-99")
    found = findings_for(repo, body)
    assert "G005" in rule_ids(found)
    assert any("INV-99" in f.message for f in found)


def test_g006_fires_for_a_declared_invariant_no_spec_cites(repo: Path) -> None:
    # repo's own CONTRACT.md declares INV-1 and INV-2; GOOD_HARNESS only
    # cites INV-1, so INV-2 is a real, pre-existing orphan in this fixture.
    found = tree_findings_for(repo, [("demo-change", "demo-cap", GOOD_HARNESS)])
    g006 = [f for f in found if f.rule == "G006"]
    assert g006 and all(f.severity == "WARN" for f in g006)
    assert any(f.subject == "INV-2" for f in g006)
    assert any("INV-2" in f.message and "CONTRACT.md" in f.message for f in g006)


def test_g006_does_not_fire_once_cited_anywhere_in_the_tree(repo: Path) -> None:
    other = GOOD_HARNESS.replace("INV-1", "INV-2").replace("AC-DMO", "AC-DM2").replace("R-DMO", "R-DM2")
    found = tree_findings_for(
        repo,
        [("c1", "cap1", GOOD_HARNESS), ("c2", "cap2", other)],
    )
    assert "G006" not in rule_ids(found)


def test_g006_is_downgraded_to_info_when_waived_anywhere_in_the_tree(repo: Path) -> None:
    # Reason text deliberately avoids the INV-n pattern itself -- invariant_refs
    # scans the whole raw text unconditionally, so naming the invariant here
    # would make the waiver comment itself count as a citation and resolve
    # the orphan before the waiver-downgrade path is even exercised.
    body = GOOD_HARNESS.replace(
        "## Problem Statement",
        "<!-- specgraph:allow G006 the second contract invariant is a future "
        "gate, not yet wired into any spec -->\n\n## Problem Statement",
    )
    found = tree_findings_for(repo, [("demo-change", "demo-cap", body)])
    g006 = [f for f in found if f.rule == "G006"]
    assert g006 and all(f.severity == "INFO" and "[waived]" in f.message for f in g006)


def test_g006_is_skipped_under_change_scoping(repo: Path, capsys) -> None:
    # other-change alone cites INV-2; a naive --change-filtered evaluate_tree()
    # would falsely call INV-2 orphaned since that citation sits outside the
    # filtered view. Confirms it's skipped outright instead (DEC-WL-003).
    write_spec(repo, "demo-change", "demo-cap", GOOD_HARNESS)
    other = GOOD_HARNESS.replace("INV-1", "INV-2").replace("AC-DMO", "AC-DM2").replace("R-DMO", "R-DM2")
    write_spec(repo, "other-change", "other-cap", other)
    exit_code = main(["--target", str(repo), "validate", "--change", "demo-change"])
    out = capsys.readouterr()
    assert exit_code == 0
    assert "G006" not in out.out
    assert "G006 skipped" in out.err


def test_g008_fires_on_an_undeclared_adr(repo: Path) -> None:
    (repo / "docs" / "adr").mkdir(parents=True)
    (repo / "docs" / "adr" / "0001-use-postgres.md").write_text("# ADR-1: Use Postgres\n")
    body = GOOD_HARNESS.replace(
        "**Evidence:** `demo/mod.py::run` writes without attestation.",
        "**Evidence:** `demo/mod.py::run` writes without attestation. See ADR-99.",
    )
    found = findings_for(repo, body)
    assert "G008" in rule_ids(found)
    assert any("ADR-99" in f.message for f in found)


def test_g009_fires_for_a_declared_adr_no_spec_cites(repo: Path) -> None:
    (repo / "docs" / "adr").mkdir(parents=True)
    (repo / "docs" / "adr" / "0001-use-postgres.md").write_text("# ADR-1: Use Postgres\n")
    (repo / "docs" / "adr" / "0002-use-rest.md").write_text("# ADR-2: Use REST\n")
    body = GOOD_HARNESS.replace(
        "**Evidence:** `demo/mod.py::run` writes without attestation.",
        "**Evidence:** `demo/mod.py::run` writes without attestation. See ADR-1.",
    )
    found = tree_findings_for(repo, [("demo-change", "demo-cap", body)])
    g009 = [f for f in found if f.rule == "G009"]
    assert g009 and all(f.severity == "WARN" for f in g009)
    assert any(f.subject == "ADR-2" for f in g009)
    assert any("ADR-2" in f.message and "docs/adr" in f.message for f in g009)


def test_g009_does_not_fire_once_cited_anywhere_in_the_tree(repo: Path) -> None:
    (repo / "docs" / "adr").mkdir(parents=True)
    (repo / "docs" / "adr" / "0001-use-postgres.md").write_text("# ADR-1: Use Postgres\n")
    body1 = GOOD_HARNESS.replace(
        "**Evidence:** `demo/mod.py::run` writes without attestation.",
        "**Evidence:** `demo/mod.py::run` writes without attestation. See ADR-1.",
    )
    other = GOOD_HARNESS.replace("AC-DMO", "AC-DM2").replace("R-DMO", "R-DM2")
    found = tree_findings_for(
        repo,
        [("c1", "cap1", body1), ("c2", "cap2", other)],
    )
    assert "G009" not in rule_ids(found)


def test_g009_is_downgraded_to_info_when_waived_anywhere_in_the_tree(repo: Path) -> None:
    # Reason text deliberately avoids the ADR-n pattern itself -- adr_refs
    # scans the whole raw text unconditionally, so naming the ADR here
    # would make the waiver comment itself count as a citation and resolve
    # the orphan before the waiver-downgrade path is even exercised.
    (repo / "docs" / "adr").mkdir(parents=True)
    (repo / "docs" / "adr" / "0001-use-postgres.md").write_text("# ADR-1: Use Postgres\n")
    body = GOOD_HARNESS.replace(
        "## Problem Statement",
        "<!-- specgraph:allow G009 the decision predates this spec tree, not "
        "yet cited anywhere -->\n\n## Problem Statement",
    )
    found = tree_findings_for(repo, [("demo-change", "demo-cap", body)])
    g009 = [f for f in found if f.rule == "G009"]
    assert g009 and all(f.severity == "INFO" and "[waived]" in f.message for f in g009)


def test_g009_is_skipped_under_change_scoping(repo: Path, capsys) -> None:
    (repo / "docs" / "adr").mkdir(parents=True)
    (repo / "docs" / "adr" / "0001-use-postgres.md").write_text("# ADR-1: Use Postgres\n")
    write_spec(repo, "demo-change", "demo-cap", GOOD_HARNESS)
    exit_code = main(["--target", str(repo), "validate", "--change", "demo-change"])
    out = capsys.readouterr()
    assert exit_code == 0
    assert "G009" not in out.out
    assert "G009 skipped" in out.err


def test_no_openapi_or_event_schema_idents_are_reserved() -> None:
    # C-AD-2: this change explicitly reserves no rule ident for the
    # deferred OpenAPI/event-schema citation-checking work (DEC-AD-007) --
    # mirrors DEC-MP-003's own precedent for not pre-reserving an id for
    # unbuilt work.
    idents = {r.ident for r in rules.RULES}
    assert not any(i.startswith(("OPENAPI", "EVENT")) for i in idents), idents


def test_h001_fires_when_an_ac_has_no_verification(repo: Path) -> None:
    body = GOOD_HARNESS.replace(
        "  _Verified by:_ `pytest -k test_attested_write` · stage: `make regression`\n",
        "",
    )
    assert "H001" in rule_ids(findings_for(repo, body, "harness"))


def test_h001_fires_when_verification_names_no_stage(repo: Path) -> None:
    body = GOOD_HARNESS.replace(
        "`pytest -k test_attested_write` · stage: `make regression`",
        "`pytest -k test_attested_write`",
    )
    found = findings_for(repo, body, "harness")
    assert "H001" in rule_ids(found)


def test_h002_fires_when_an_ac_traces_to_no_requirement(repo: Path) -> None:
    body = GOOD_HARNESS.replace(
        "**AC-DMO-1:** An attested write records an evidence id. (R-DMO-1)",
        "**AC-DMO-1:** An attested write records an evidence id.",
    )
    found = findings_for(repo, body, "harness")
    assert "H002" in rule_ids(found)
    assert any("AC-DMO-1" in f.message and "traces to no" in f.message for f in found)


def test_h002_does_not_fire_when_the_spec_declares_no_requirements_at_all(repo: Path) -> None:
    # _ac_missing_requirement's own guard: `if not spec.requirements: return`
    # -- G001 is the rule that names "no requirements at all," not H002.
    body = textwrap.dedent(
        """\
        # Spec: Demo Capability

        > **Status:** DRAFT

        ## Problem Statement

        **Evidence:** `demo/mod.py::run` writes without attestation.

        ## Acceptance Criteria

        - [ ] **AC-DMO-1:** An attested write records an evidence id.
          _Verified by:_ `pytest -k test_attested_write` · stage: `make regression`

        - [ ] **AC-DMO-2 (non-success):** An unattested write is denied.
          _Verified by:_ `pytest -k test_unattested_denied` · stage: `make regression`

        ## Validation Matrix

        | Stage | Make Target | Pass Criteria |
        |---|---|---|
        | Focused | `make regression` | AC-DMO-1..2 |
        """
    )
    assert "H002" not in rule_ids(findings_for(repo, body, "harness"))


def test_h003_fires_on_an_orphan_requirement(repo: Path) -> None:
    body = GOOD_HARNESS.replace(
        "- C-DMO-1: The change MUST NOT weaken INV-1.",
        "- C-DMO-1: The change MUST NOT weaken INV-1.\n- R-DMO-9: MUST also do an untested thing.",
    )
    found = findings_for(repo, body, "harness")
    assert "H003" in rule_ids(found)
    assert any("R-DMO-9" in f.message for f in found)


def test_h004_fires_on_duplicate_criterion_ids(repo: Path) -> None:
    body = GOOD_HARNESS.replace("**AC-DMO-2 (non-success):**", "**AC-DMO-1 (non-success):**")
    assert "H004" in rule_ids(findings_for(repo, body, "harness"))


def test_h005_fires_when_a_blocking_question_survives_draft(repo: Path) -> None:
    body = GOOD_HARNESS.replace("**Status:** DRAFT", "**Status:** APPROVED")
    body += "\n## Open Questions\n\n> **DEC-DMO-001 (BLOCKING):** unresolved.\n"
    assert "H005" in rule_ids(findings_for(repo, body, "harness"))


def test_h006_fires_on_a_missing_required_section(repo: Path) -> None:
    body = GOOD_HARNESS.replace("## Validation Matrix", "## Notes")
    assert "H006" in rule_ids(findings_for(repo, body, "harness"))


def test_u001_fires_without_a_delta_header(repo: Path) -> None:
    body = GOOD_UPSTREAM.replace("## ADDED Requirements", "## Requirements")
    assert "U001" in rule_ids(findings_for(repo, body, "upstream"))


def test_u002_fires_on_a_requirement_with_no_scenario(repo: Path) -> None:
    body = GOOD_UPSTREAM + "\n### Requirement: the reader SHALL verify ids\n\nProse.\n"
    found = findings_for(repo, body, "upstream")
    assert "U002" in rule_ids(found)


def test_u003_fires_on_a_scenario_missing_then(repo: Path) -> None:
    body = GOOD_UPSTREAM.replace("- **THEN** an evidence id is recorded", "- it works")
    assert "U003" in rule_ids(findings_for(repo, body, "upstream"))


# --- U003: GIVEN is optional (fix-u003-mandatory-given) --------------------
#
# Every negative body below is a single targeted `.replace()` mutation of
# GOOD_UPSTREAM, so the passing and failing fixtures cannot drift (AC-UG-5).

_GIVEN_LINE = "- **GIVEN** an attested writer\n"
_WHEN_LINE = "- **WHEN** `make regression` runs the suite"
_THEN_LINE = "- **THEN** an evidence id is recorded"

NO_GIVEN_UPSTREAM = GOOD_UPSTREAM.replace(_GIVEN_LINE, "")
MISSING_WHEN_UPSTREAM = GOOD_UPSTREAM.replace(_WHEN_LINE, "- the suite runs")
MISSING_THEN_UPSTREAM = GOOD_UPSTREAM.replace(_THEN_LINE, "- it works")


def test_u003_accepts_a_scenario_without_given(repo: Path) -> None:
    """AC-UG-1: WHEN + THEN with no GIVEN is executable and must not fire.

    Regression for a 100% false-positive rate: run against an external
    upstream-dialect corpus, U003 reported 66 of 68 scenarios, and every one
    of them carried WHEN and THEN while omitting only GIVEN.
    """
    assert "GIVEN" not in NO_GIVEN_UPSTREAM.split("#### Scenario:")[1]
    assert "U003" not in rule_ids(findings_for(repo, NO_GIVEN_UPSTREAM, "upstream"))


def test_u003_still_fires_when_when_is_absent(repo: Path) -> None:
    """AC-UG-2: a scenario with no stimulus is still not executable."""
    assert "U003" in rule_ids(findings_for(repo, MISSING_WHEN_UPSTREAM, "upstream"))


def test_u003_still_fires_when_then_is_absent(repo: Path) -> None:
    """AC-UG-3: a scenario that asserts no outcome is still not executable."""
    assert "U003" in rule_ids(findings_for(repo, MISSING_THEN_UPSTREAM, "upstream"))


def test_u003_accepts_a_full_gwt_scenario(repo: Path) -> None:
    """AC-UG-4: the previously accepted three-clause shape is not lost."""
    assert "U003" not in rule_ids(findings_for(repo, GOOD_UPSTREAM, "upstream"))


def test_u003_negative_fixtures_are_mutations_of_the_positive() -> None:
    """AC-UG-5: each failing fixture differs from the passing one by one clause."""
    for mutated, removed in (
        (NO_GIVEN_UPSTREAM, _GIVEN_LINE.strip()),
        (MISSING_WHEN_UPSTREAM, _WHEN_LINE),
        (MISSING_THEN_UPSTREAM, _THEN_LINE),
    ):
        assert mutated != GOOD_UPSTREAM, "mutation must actually change the fixture"
        assert removed in GOOD_UPSTREAM, "the clause must exist in the source fixture"
        assert removed not in mutated, "the mutation must remove exactly that clause"


def test_u003_summary_does_not_require_given() -> None:
    """AC-UG-6: the rule must stop advertising a check it no longer makes."""
    u003 = next(r for r in rules.RULES if r.ident == "U003")
    assert "GIVEN" not in u003.summary.upper()


def test_u002_unchanged_by_the_u003_fix(repo: Path) -> None:
    """AC-UG-7: a requirement with no scenario at all still fires U002."""
    body = NO_GIVEN_UPSTREAM + "\n### Requirement: the reader SHALL verify ids\n\nProse.\n"
    assert "U002" in rule_ids(findings_for(repo, body, "upstream"))


def test_rule_registry_baseline_is_unchanged() -> None:
    """AC-UG-8: no rule id added, no finding emitted for an omitted GIVEN."""

    baseline = json.loads(
        (Path(__file__).resolve().parent / "baseline_rules.json").read_text(encoding="utf-8")
    )
    assert {r["id"] for r in baseline} == {r.ident for r in rules.RULES}
    assert len(baseline) == len(rules.RULES)


def test_u004_fires_on_a_non_normative_requirement(repo: Path) -> None:
    body = GOOD_UPSTREAM.replace(
        "### Requirement: the writer SHALL attest every write",
        "### Requirement: the writer attests writes",
    )
    assert "U004" in rule_ids(findings_for(repo, body, "upstream"))


def test_u004_does_not_fire_when_the_modal_verb_is_only_in_the_body(repo: Path) -> None:
    # Regression: Requirement.text used to be populated from the heading match
    # alone, so a heading with no SHALL/MUST but a normative body still
    # false-fired U004 -- the common real-world authoring style.
    body = GOOD_UPSTREAM.replace(
        "### Requirement: the writer SHALL attest every write",
        "### Requirement: the writer attests every write",
    ).replace(
        "Prose obligation.",
        "The writer SHALL record an evidence id for every write.",
    )
    assert "U004" not in rule_ids(findings_for(repo, body, "upstream"))



# --- G010 / G011: what the make-citation check actually checked -------------
#
# G004 alone was silent in two directions at once (docs/peer-review-2026-09.md
# F2 and F3): it returned early when no makefile was found, and it exempted the
# five GENERIC_STAGES unconditionally. Both silences produced PASS with zero
# findings on a spec citing a stage that does not exist.


def test_g010_reports_citations_it_could_not_check(repo: Path) -> None:
    (repo / "Makefile").unlink()
    found = findings_for(repo, GOOD_HARNESS.replace("make regression", "make nope"))
    g010 = [f for f in found if f.rule == "G010"]
    assert len(g010) == 1, found
    assert g010[0].severity == "INFO"
    assert "not checked" in g010[0].message


def test_g010_is_silent_when_the_spec_cites_no_make_target(repo: Path) -> None:
    """Non-success: it reports an unrun check, never a missing makefile.

    A spec with nothing to check has nothing unchecked, so a Makefile-less
    repo full of make-free specs stays completely quiet.
    """
    (repo / "Makefile").unlink()
    body = GOOD_HARNESS.replace("`make regression`", "the regression suite")
    assert "G010" not in rule_ids(findings_for(repo, body))


def test_g010_fires_once_per_spec_not_once_per_citation(repo: Path) -> None:
    """The fact reported is a property of the run, not of each citation."""
    (repo / "Makefile").unlink()
    body = GOOD_HARNESS.replace("make regression", "make nope") + (
        "\n\n_Also verified by:_ `make alpha`, `make beta`, `make gamma`\n"
    )
    assert len([f for f in findings_for(repo, body) if f.rule == "G010"]) == 1


def test_g010_does_not_change_a_fail_on_error_verdict(repo: Path) -> None:
    """Non-success: INFO exists so no currently-passing repo starts failing."""
    (repo / "Makefile").unlink()
    found = findings_for(repo, GOOD_HARNESS.replace("make regression", "make nope"))
    assert [f for f in found if f.rule == "G010" and f.severity == "ERROR"] == []
    assert not [f for f in found if f.severity == "ERROR"], found


def test_g011_warns_on_a_generic_stage_the_makefile_lacks(repo: Path) -> None:
    """`make coverage` against a Makefile that declares no `coverage` target.

    G004 exempts it as a conventional name; the repo demonstrably uses Make,
    so the citation still may not run and that is worth a WARN.
    """
    found = findings_for(repo, GOOD_HARNESS.replace("make regression", "make coverage"))
    g011 = [f for f in found if f.rule == "G011"]
    assert len(g011) == 1, found
    assert g011[0].severity == "WARN"
    assert not [f for f in found if f.severity == "ERROR"], found


def test_g011_is_silent_for_a_generic_stage_that_does_exist(repo: Path) -> None:
    """Non-success: the fixture Makefile declares `test`, so nothing is wrong."""
    found = findings_for(repo, GOOD_HARNESS.replace("make regression", "make test"))
    assert "G011" not in rule_ids(found)


def test_g011_does_not_run_where_the_repo_has_no_makefile(repo: Path) -> None:
    """Non-success: the tox/npm/just case the GENERIC_STAGES exemption exists for.

    With no makefile the repo has not shown it uses Make at all, so a generic
    stage carries no information and only G010 speaks.
    """
    (repo / "Makefile").unlink()
    ids = rule_ids(findings_for(repo, GOOD_HARNESS.replace("make regression", "make coverage")))
    assert "G011" not in ids
    assert "G010" in ids


def test_no_citation_is_reported_by_two_of_the_three_rules(repo: Path) -> None:
    """Non-success: G004/G010/G011 partition the cases, never overlap."""
    # Non-generic, absent, Makefile present -> G004 only.
    ids = rule_ids(findings_for(repo, GOOD_HARNESS.replace("make regression", "make nope")))
    assert "G004" in ids and "G010" not in ids and "G011" not in ids

    # Generic, absent, Makefile present -> G011 only.
    ids = rule_ids(findings_for(repo, GOOD_HARNESS.replace("make regression", "make coverage")))
    assert "G011" in ids and "G004" not in ids and "G010" not in ids

    # Makefile absent -> G010 only.
    (repo / "Makefile").unlink()
    ids = rule_ids(findings_for(repo, GOOD_HARNESS.replace("make regression", "make nope")))
    assert "G010" in ids and "G004" not in ids and "G011" not in ids


def test_a_gnumakefile_only_repo_fails_a_bad_citation_end_to_end(repo: Path) -> None:
    """AC-MFD-4: the inversion the whole makefile-discovery change exists for.

    Before it, this repository reported PASS with zero findings. The corpus
    shapes pin detection; this pins the verdict a user actually sees.
    """
    (repo / "Makefile").rename(repo / "GNUmakefile")
    found = findings_for(repo, GOOD_HARNESS.replace("make regression", "make nope"))
    assert "G004" in rule_ids(found)
    assert [f for f in found if f.rule == "G004" and f.severity == "ERROR"]


def test_an_unreadable_makefile_reports_nothing_and_says_so(repo: Path) -> None:
    """GNU Make aborts here, so no citation runs -- and G010 must say so.

    The pair is the point: reporting the shadowed file's targets would be a
    lie, and reporting nothing without a diagnostic would be the silence this
    work set out to remove.
    """
    (repo / "Makefile").rename(repo / "Makefile.bak")
    (repo / "GNUmakefile").mkdir()
    (repo / "Makefile").write_text("build:\n\t@echo b\n", encoding="utf-8")
    found = findings_for(repo, GOOD_HARNESS.replace("make regression", "make build"))
    assert detect.profile(repo).make_targets == ()
    assert "G004" not in rule_ids(found)
    assert "G010" in rule_ids(found)


def test_g010_and_g011_waivers_keep_the_finding_visible(repo: Path) -> None:
    """Waiving an already-INFO rule downgrades nothing; it only marks it.

    `rules.evaluate()` is `severity=INFO if suppressed else rule.severity`, so a
    waived G010 keeps INFO and keeps appearing -- `--fail-on INFO` still counts
    it. G010 is therefore effectively unwaivable, which is a real limitation
    recorded in the change package rather than a property to assert away.
    G011 is WARN, so its waiver does what a waiver normally does.
    """
    waiver = "<!-- specgraph:allow G010,G011 reason: this target does not use Make -->\n"

    (repo / "Makefile").unlink()
    found = findings_for(repo, waiver + GOOD_HARNESS.replace("make regression", "make nope"))
    g010 = [f for f in found if f.rule == "G010"]
    assert len(g010) == 1, found
    assert g010[0].severity == "INFO"
    assert g010[0].message.startswith("[waived]"), g010[0].message


def test_a_waived_g011_is_downgraded_to_info(repo: Path) -> None:
    waiver = "<!-- specgraph:allow G011 reason: shorthand, this repo runs tox -->\n"
    found = findings_for(repo, waiver + GOOD_HARNESS.replace("make regression", "make coverage"))
    g011 = [f for f in found if f.rule == "G011"]
    assert len(g011) == 1, found
    assert g011[0].severity == "INFO", "a waived WARN drops to INFO"
    assert g011[0].message.startswith("[waived]")


def test_an_empty_bodied_fr_bullet_does_not_consume_the_next_one(repo: Path) -> None:
    """Regression: `\\s*(.+?)` spanned newlines, so `- **FR-001**:` took the
    FOLLOWING bullet as its body and that bullet left the graph entirely.

    Reproduced at the *correct* heading level, so it was never an S005 story --
    a malformed bullet silently deleted a well-formed sibling.
    """
    from openspec_graph.parse_semantics import FR_DECL

    doc = "- **FR-001**:\n- **FR-002**: real body here\n"
    found = [(m.group(1), m.group(2)) for m in FR_DECL.finditer(doc)]
    assert found == [("FR-001", ""), ("FR-002", "real body here")], found

    # And it must not reach across a blank line into an unrelated heading.
    m = FR_DECL.search("- **FR-001**:\n\n## Success Criteria\n")
    assert m is not None and m.group(2) == "", m and m.group(2)


def test_a_waiver_whose_reason_spans_lines_actually_suppresses(repo: Path) -> None:
    """A multi-line waiver used to be silently inert, for every rule.

    `SUPPRESS` had no `re.DOTALL`, so `(.*?)` could not cross a newline: the
    comment suppressed nothing, appeared in `planlint waivers` as nothing, and
    raised no G007. The author got back the finding they believed they had
    waived, with no signal the comment did nothing — the one answer a
    governance tool must not give.
    """
    waiver = "<!-- specgraph:allow G004\nreason: this target lands in the next PR\n-->\n"
    found = findings_for(repo, waiver + GOOD_HARNESS.replace("make regression", "make nope"))
    g004 = [f for f in found if f.rule == "G004"]
    assert len(g004) == 1, found
    assert g004[0].severity == "INFO", "a waived ERROR drops to INFO"
    assert g004[0].message.startswith("[waived]")


def test_a_multiline_waiver_does_not_shift_later_finding_lines(repo: Path) -> None:
    """Non-success: `re.DOTALL` must not cost the 1-based locus contract.

    The old fill was `" " * len(span)`, which contains no newlines — blanking a
    three-line waiver that way would merge those lines and move every later
    finding up by two, silently. The fill preserves newlines (DEC-LH /
    R-LH-14), so the only change is that the waiver now works.
    """
    body = GOOD_HARNESS.replace("make regression", "make nope")
    single = findings_for(repo, "<!-- specgraph:allow G001 reason: x -->\n" + body)
    multi = findings_for(repo, "<!-- specgraph:allow G001\nreason: x\n-->\n" + body)

    def loci(found: list[rules.Finding]) -> dict[str, int]:
        return {f.rule: f.line for f in found if f.line}

    # The multi-line form occupies two extra lines, so every later locus moves
    # by exactly two — no more, which a merging fill would not manage.
    for rule, line in loci(single).items():
        assert loci(multi).get(rule) == line + 2, (rule, line, loci(multi))
