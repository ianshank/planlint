"""Scaffolding, the CLI contract, the waivers verb, and real-repo regressions.

Grouped because they exercise the command surface rather than a rule: what
`planlint` writes, what it prints, and what it exits.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

from openspec_graph import detect, rules, scaffold
from openspec_graph.cli import main
from openspec_graph.parse import parse_spec
from tests.graft_support import (
    CONTRACT,
    GOOD_HARNESS,
    GOOD_UPSTREAM,
    MAKEFILE,
    findings_for,
    rule_ids,
)
from tests.support import write_spec

# --- scaffolding -----------------------------------------------------------


def test_scaffold_uses_a_stage_that_exists_in_the_target(repo: Path) -> None:
    prof = detect.profile(repo)
    plans = scaffold.plan_change(prof, "add-thing", "thing-capability", "harness")
    spec = next(p for p in plans if p.path.name == "spec.md")
    assert "make regression" in spec.content
    assert "make test-governance" not in spec.content


def test_scaffolded_spec_passes_its_own_validator(repo: Path) -> None:
    prof = detect.profile(repo)
    for dialect in ("harness", "upstream"):
        plans = scaffold.plan_change(prof, f"add-{dialect}", "demo-capability", dialect)
        scaffold.apply(plans)
    prof = detect.profile(repo)
    errors = []
    for path in detect.find_spec_files(repo / "openspec"):
        errors += [
            f for f in rules.evaluate(parse_spec(path, "auto"), prof) if f.severity == "ERROR"
        ]
    assert errors == [], [f.render() for f in errors]


def test_scaffold_references_the_detected_threshold_locator(repo: Path) -> None:
    prof = detect.profile(repo)
    plans = scaffold.plan_change(prof, "add-thing", "thing-capability", "harness")
    spec = next(p for p in plans if p.path.name == "spec.md")
    assert "pyproject.toml" in spec.content


def test_apply_is_idempotent_and_refuses_to_clobber(repo: Path) -> None:
    prof = detect.profile(repo)
    plans = scaffold.plan_change(prof, "add-thing", "thing-capability", "harness")
    first = scaffold.apply(plans)
    assert len(first) == 3
    spec = next(p for p in plans if p.path.name == "spec.md").path
    spec.write_text("EDITED BY HAND")
    replanned = scaffold.plan_change(prof, "add-thing", "thing-capability", "harness")
    assert scaffold.apply(replanned) == []
    assert spec.read_text() == "EDITED BY HAND"
    assert len(scaffold.apply(replanned, force=True)) == 3


def test_init_pins_detected_conventions(repo: Path) -> None:
    prof = detect.profile(repo)
    scaffold.apply(scaffold.plan_init(prof))
    config = json.loads((repo / "openspec" / "specgraph.json").read_text())
    assert config["focused_stage"] == "regression"
    assert "pyproject.toml" in config["threshold_locator"]
    assert config["invariant_source"] == "CONTRACT.md"


def test_plan_init_persists_a_forward_slash_invariant_source_to_disk(tmp_path: Path) -> None:
    # Highest-severity Defect A site: plan_init()'s invariant_source is
    # written into TWO persisted files (specgraph.json, project.md) via
    # scaffold.apply()'s write_text() -- a Windows-run `planlint init` would
    # otherwise bake a wrong-separator path into files a user might commit,
    # not just print one. The repo fixture's own CONTRACT.md is a single,
    # root-level segment with no separator character on either OS, so it
    # can't exercise this bug regardless of platform -- nest it instead.
    (tmp_path / "Makefile").write_text(MAKEFILE)
    (tmp_path / "harness").mkdir()
    (tmp_path / "harness" / "CONTRACT.md").write_text(CONTRACT)
    prof = detect.profile(tmp_path)
    assert prof.invariant_source == tmp_path / "harness" / "CONTRACT.md"  # sanity

    scaffold.apply(scaffold.plan_init(prof))

    config = json.loads((tmp_path / "openspec" / "specgraph.json").read_text())
    assert config["invariant_source"] == "harness/CONTRACT.md"
    assert "\\" not in config["invariant_source"]

    project_md = (tmp_path / "openspec" / "project.md").read_text()
    assert "Invariant source: `harness/CONTRACT.md`" in project_md
    assert "\\" not in project_md


# --- CLI contract ----------------------------------------------------------


def test_cli_validate_exits_nonzero_on_a_bad_spec(repo: Path, capsys) -> None:
    write_spec(repo, "bad-change", "bad-cap", GOOD_HARNESS.replace("make regression", "make nope"))
    assert main(["--target", str(repo), "validate"]) == 1
    assert "G004" in capsys.readouterr().out


def test_cli_validate_exits_zero_on_a_clean_spec(repo: Path) -> None:
    write_spec(repo, "ok-change", "ok-cap", GOOD_HARNESS)
    assert main(["--target", str(repo), "validate"]) == 0


def test_cli_validate_text_finding_order_is_consistent_across_host_os(
    repo: Path, capsys
) -> None:
    # "\\" sorts after digits/uppercase letters while "/" sorts before them,
    # so a native str(path) sort key renders these two sibling change dirs in
    # OPPOSITE relative order on Windows vs. POSIX for the identical repo:
    # "add-thing" is shorter, so its next character after the common prefix
    # is the path separator ("/" or "\\"); "add-thing2"'s is the digit "2".
    # "/" (0x2F) < "2" (0x32) < "\\" (0x5C) -- posix puts add-thing first,
    # native-Windows puts add-thing2 first. detect.to_posix_relative in the
    # sort key (not str(f.path)) is what makes this consistent everywhere.
    write_spec(repo, "add-thing", "cap", GOOD_HARNESS.replace("make regression", "make nope"))
    write_spec(repo, "add-thing2", "cap", GOOD_HARNESS.replace("make regression", "make nope"))
    assert main(["--target", str(repo), "validate"]) == 1
    out = capsys.readouterr().out
    assert "add-thing/" in out and "add-thing2/" in out
    assert out.index("changes/add-thing/") < out.index("changes/add-thing2/")


def test_cli_validate_fail_on_warn_is_stricter(repo: Path) -> None:
    write_spec(repo, "warn-change", "warn-cap", GOOD_HARNESS.replace("INV-1", "INV-77"))
    assert main(["--target", str(repo), "validate"]) == 0
    assert main(["--target", str(repo), "validate", "--fail-on", "WARN"]) == 1


def test_cli_detect_json_is_machine_readable(repo: Path, capsys) -> None:
    assert main(["--target", str(repo), "detect", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["threshold"]["value"] == 90


def test_cli_dry_run_writes_nothing(repo: Path) -> None:
    assert main(["--target", str(repo), "new", "x", "--capability", "y", "--dry-run"]) == 0
    assert not (repo / "openspec" / "changes" / "x").exists()


def test_cli_init_dry_run_prints_forward_slash_paths(repo: Path, capsys) -> None:
    assert main(["--target", str(repo), "init", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "openspec/specgraph.json" in out
    assert "openspec/project.md" in out
    assert "\\" not in out


def test_cli_new_dry_run_prints_forward_slash_paths(repo: Path, capsys) -> None:
    assert (
        main(
            ["--target", str(repo), "new", "add-thing", "--capability", "thing-cap", "--dry-run"]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "openspec/changes/add-thing/specs/thing-cap/spec.md" in out
    assert "\\" not in out


# --- regressions found by running against real repositories ----------------
# Each of these encodes a false positive or misleading message that the first
# version of the rule engine produced against ianshank/Mouse-Droid-AGI.


def test_g002_accepts_a_negation_phrased_as_absence(repo: Path) -> None:
    """'opens no egress channel' is a non-success scenario. G002 must not fire.

    Regression: the original phrase-list detector missed it and reported a
    false positive against openspec/changes/mouse-droid-cloud-egress-default-off.
    """
    body = textwrap.dedent(
        """\
        # Spec delta — Cloud egress

        ## ADDED Requirements

        ### Requirement: egress SHALL default to off

        Prose.

        #### Scenario: a partial GCP block opens no egress channel

        - **GIVEN** a partially configured GCP block
        - **WHEN** `make regression` runs
        - **THEN** the resolver opens no egress channel
        """
    )
    assert "G002" not in rule_ids(findings_for(repo, body, "upstream"))


def test_g002_accepts_mutates_neither(repo: Path) -> None:
    body = GOOD_UPSTREAM.replace(
        "- **THEN** the check fails and names the offending file",
        "- **THEN** it mutates neither the remote nor the local tag list",
    ).replace("caught before merge", "reported in dry-run")
    assert "G002" not in rule_ids(findings_for(repo, body, "upstream"))


def test_g002_still_fires_on_a_genuinely_happy_only_upstream_spec(repo: Path) -> None:
    body = textwrap.dedent(
        """\
        # Spec delta — Happy path only

        ## ADDED Requirements

        ### Requirement: the exporter SHALL emit a metric

        Prose.

        #### Scenario: the metric appears

        - **GIVEN** a running exporter
        - **WHEN** `make regression` runs
        - **THEN** the metric appears in the registry
        """
    )
    assert "G002" in rule_ids(findings_for(repo, body, "upstream"))


def test_shallow_headings_are_parsed_and_reported_as_drift(repo: Path) -> None:
    """`## Requirement:` / `### Scenario:` must parse, then trip U005.

    Regression: openspec/changes/mouse-droid-deploy-repin uses H2/H3 while its
    nine sibling packages use H3/H4. The first version reported 'no criteria
    found', which blamed the author for a parser limitation.
    """
    body = GOOD_UPSTREAM.replace("### Requirement:", "## Requirement:").replace(
        "#### Scenario:", "### Scenario:"
    )
    found = findings_for(repo, body, "upstream")
    ids = rule_ids(found)
    assert "G001" not in ids, "criteria must be recognized at non-canonical depths"
    assert "U005" in ids
    assert any("H2" in f.message or "H3" in f.message for f in found)


def test_numbered_req_headings_are_recognized_as_requirements(repo: Path) -> None:
    """`## REQ 1: ...` is a third in-repo form; report it accurately."""
    body = textwrap.dedent(
        """\
        # Specification: NemoClaw Integration

        ## REQ 1: Live Memory Query

        The bridge SHALL answer a live memory query.

        ## REQ 2: Transport-Identical Gating

        Gating SHALL be identical across transports.
        """
    )
    found = findings_for(repo, body, "upstream")
    assert "G001" in rule_ids(found)
    assert any("no Scenario or acceptance" in f.message for f in found)
    assert "U002" in rule_ids(found), "each REQ should be reported as scenario-less"


def test_waiver_downgrades_a_finding_to_info_and_stays_visible(repo: Path) -> None:
    body = GOOD_HARNESS.replace(
        "## Problem Statement",
        "<!-- specgraph:allow G003 this spec's subject IS the 85% hook floor -->\n\n## Problem Statement",
    ).replace(
        "An attested write records an evidence id.",
        "The documented hook floor stays pinned at 85%.",
    )
    found = findings_for(repo, body, "harness")
    g003 = [f for f in found if f.rule == "G003"]
    assert g003, "the waived rule must still appear in the report"
    assert all(f.severity == "INFO" for f in g003)
    assert all("[waived]" in f.message for f in g003)


def test_waiver_does_not_leak_to_other_rules(repo: Path) -> None:
    body = GOOD_HARNESS.replace(
        "## Problem Statement", "<!-- specgraph:allow G003 -->\n\n## Problem Statement"
    ).replace("make regression", "make nope")
    found = findings_for(repo, body, "harness")
    assert any(f.rule == "G004" and f.severity == "ERROR" for f in found)


def test_cli_validate_passes_when_the_only_error_is_waived(repo: Path) -> None:
    # Reason required (CP-4/G007): a reason-less waiver would now also trip
    # G007, so this fixture must carry one to keep testing what it always
    # meant to test -- a *justified* waiver passing.
    body = GOOD_HARNESS.replace(
        "## Problem Statement",
        "<!-- specgraph:allow G003 95% is this spec's own coverage floor -->\n\n## Problem Statement",
    ).replace("An attested write records an evidence id.", "Coverage is at least 95%.")
    write_spec(repo, "waived-change", "waived-cap", body)
    assert main(["--target", str(repo), "validate"]) == 0


def test_cli_validate_fails_when_a_waiver_has_no_reason(repo: Path) -> None:
    body = GOOD_HARNESS.replace(
        "## Problem Statement", "<!-- specgraph:allow G003 -->\n\n## Problem Statement"
    ).replace("An attested write records an evidence id.", "Coverage is at least 95%.")
    write_spec(repo, "waived-change", "waived-cap", body)
    assert main(["--target", str(repo), "validate"]) == 1


def test_unreasoned_waiver_downgrades_the_named_rule_and_also_fires_g007(repo: Path) -> None:
    body = GOOD_HARNESS.replace(
        "## Problem Statement", "<!-- specgraph:allow G003 -->\n\n## Problem Statement"
    ).replace("An attested write records an evidence id.", "Coverage is at least 95%.")
    found = findings_for(repo, body, "harness")
    g003 = [f for f in found if f.rule == "G003"]
    g007 = [f for f in found if f.rule == "G007"]
    assert g003 and all(f.severity == "INFO" and "[waived]" in f.message for f in g003)
    assert g007 and all(f.severity == "ERROR" for f in g007)
    assert any("G003" in f.message for f in g007)


def test_reasoned_waiver_does_not_trip_g007(repo: Path) -> None:
    body = GOOD_HARNESS.replace(
        "## Problem Statement",
        "<!-- specgraph:allow G003 this spec's subject IS the 95% coverage floor -->"
        "\n\n## Problem Statement",
    ).replace("An attested write records an evidence id.", "Coverage is at least 95%.")
    assert "G007" not in rule_ids(findings_for(repo, body, "harness"))


def test_g007_fires_regardless_of_dialect(repo: Path) -> None:
    body = GOOD_UPSTREAM.replace(
        "## ADDED Requirements", "<!-- specgraph:allow G002 -->\n\n## ADDED Requirements"
    )
    assert "G007" in rule_ids(findings_for(repo, body, "upstream"))


def test_g007_is_not_suppressible_by_waiving_itself_without_a_reason(repo: Path) -> None:
    body = GOOD_HARNESS.replace(
        "## Problem Statement", "<!-- specgraph:allow G007 -->\n\n## Problem Statement"
    )
    g007 = [f for f in findings_for(repo, body, "harness") if f.rule == "G007"]
    assert g007 and all(f.severity == "ERROR" for f in g007)


def test_multi_rule_waiver_with_no_reason_fires_one_g007_per_waived_rule(repo: Path) -> None:
    # A single comment naming N rules expands to N Waiver records (one per
    # rule, all sharing that comment's reason/line) -- so an unreasoned
    # multi-rule waiver produces one independent G007 finding per name, not
    # one finding for the whole comment.
    body = GOOD_HARNESS.replace(
        "## Problem Statement", "<!-- specgraph:allow G003,G004 -->\n\n## Problem Statement"
    ).replace("An attested write records an evidence id.", "Coverage is at least 95%.")
    g007 = [f for f in findings_for(repo, body, "harness") if f.rule == "G007"]
    assert len(g007) == 2
    messages = " ".join(f.message for f in g007)
    assert "G003" in messages and "G004" in messages


def test_suppressions_unchanged_behavior_after_waiver_refactor() -> None:
    from openspec_graph.parse_semantics import suppressions

    text = "<!-- specgraph:allow G003, G004 because reasons -->"
    assert suppressions(text) == {"G003", "G004"}


# --- waivers CLI verb (AC-WL-1) ---------------------------------------------


def test_cli_waivers_json_lists_reason_file_line_and_change(repo: Path, capsys) -> None:
    body = GOOD_HARNESS.replace(
        "## Problem Statement",
        "<!-- specgraph:allow G003 95% is this spec's own coverage floor -->\n\n## Problem Statement",
    ).replace("An attested write records an evidence id.", "Coverage is at least 95%.")
    write_spec(repo, "waived-change", "waived-cap", body)
    exit_code = main(["--target", str(repo), "waivers", "--format", "json"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload) == 1
    entry = payload[0]
    assert entry["rule"] == "G003"
    assert entry["reason"] == "95% is this spec's own coverage floor"
    assert entry["change"] == "waived-change"
    assert "waived-change" in entry["path"]
    assert entry["line"] > 0


def test_cli_waivers_json_is_empty_list_with_no_waivers(repo: Path, capsys) -> None:
    write_spec(repo, "clean-change", "clean-cap", GOOD_HARNESS)
    exit_code = main(["--target", str(repo), "waivers", "--format", "json"])
    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == []


def test_cli_waivers_exits_2_with_no_openspec_tree(repo: Path, capsys) -> None:
    # repo fixture has Makefile/pyproject/CONTRACT.md but no openspec/ tree.
    exit_code = main(["--target", str(repo), "waivers"])
    assert exit_code == 2
    assert "openspec/" in capsys.readouterr().err


def test_cli_waivers_text_output_lists_a_waiver(repo: Path, capsys) -> None:
    body = GOOD_HARNESS.replace(
        "## Problem Statement",
        "<!-- specgraph:allow G003 95% is this spec's own coverage floor -->\n\n## Problem Statement",
    ).replace("An attested write records an evidence id.", "Coverage is at least 95%.")
    write_spec(repo, "waived-change", "waived-cap", body)
    exit_code = main(["--target", str(repo), "waivers"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "G003" in out
    assert "waived-change" in out
    assert "95% is this spec's own coverage floor" in out


def test_cli_waivers_text_output_says_none_found_when_empty(repo: Path, capsys) -> None:
    write_spec(repo, "clean-change", "clean-cap", GOOD_HARNESS)
    exit_code = main(["--target", str(repo), "waivers"])
    assert exit_code == 0
    assert "no waivers found" in capsys.readouterr().out


