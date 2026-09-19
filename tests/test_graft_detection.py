"""Stack detection: what `detect.profile` reads out of a repository.

The negative cases matter most: a detector that finds nothing reports a
clean profile, and every downstream rule then passes vacuously.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from openspec_graph import detect, dialect_card
from openspec_graph.cli import main
from openspec_graph.parse import parse_spec
from tests import support
from tests.graft_support import (
    _CAN_SYMLINK,
    CONTRACT,
    GOOD_HARNESS,
    GOOD_SPECKIT,
    GOOD_UPSTREAM,
    MAKEFILE,
    PYPROJECT,
    findings_for,
    rule_ids,
)
from tests.support import write_spec, write_speckit_spec


def test_supports_symlinks_returns_false_when_symlink_to_is_not_implemented(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Path.symlink_to() raises NotImplementedError, not OSError, when
    # os.symlink doesn't exist on this platform at all -- letting that
    # escape uncaught would crash the *importing* test module at collection
    # time (this file's and test_witness.py's own module-level
    # _CAN_SYMLINK probe above), the exact all-or-nothing failure this
    # capability probe exists to avoid.
    def _raise_not_implemented(self: Path, target: object, target_is_directory: bool = False) -> None:
        raise NotImplementedError("os.symlink() not available on this system")

    monkeypatch.setattr(Path, "symlink_to", _raise_not_implemented)
    assert support.supports_symlinks() is False

# --- detection -------------------------------------------------------------


def test_detect_reads_threshold_from_pyproject(repo: Path) -> None:
    prof = detect.profile(repo)
    assert prof.threshold is not None
    assert prof.threshold.value == 90
    assert "pyproject.toml" in prof.threshold.locator


def test_detect_prefers_governance_policy_over_pyproject(repo: Path) -> None:
    (repo / "governance-policy.json").write_text(json.dumps({"coverage": {"lines": 85}}))
    prof = detect.profile(repo)
    assert prof.threshold is not None
    assert prof.threshold.value == 85
    assert "governance-policy.json" in prof.threshold.locator


def test_detect_reads_threshold_from_coveragerc(repo: Path) -> None:
    (repo / "pyproject.toml").write_text('[project]\nname = "demo"\n')
    (repo / ".coveragerc").write_text("[report]\nfail_under = 88\n")
    prof = detect.profile(repo)
    assert prof.threshold is not None
    assert prof.threshold.value == 88
    assert ".coveragerc" in prof.threshold.locator


def test_detect_reads_threshold_from_setup_cfg(repo: Path) -> None:
    (repo / "pyproject.toml").write_text('[project]\nname = "demo"\n')
    (repo / "setup.cfg").write_text("[coverage:report]\nfail_under = 82\n")
    prof = detect.profile(repo)
    assert prof.threshold is not None
    assert prof.threshold.value == 82
    assert "setup.cfg" in prof.threshold.locator


def test_detect_governance_policy_locator_uses_forward_slashes_for_a_nested_path(
    repo: Path,
) -> None:
    # harness/shared/governance-policy.json is a genuinely multi-segment
    # relative path (unlike the root-level candidate every other governance
    # test here uses) -- the one _threshold() candidate that can actually
    # leak a native separator into ThresholdSource.locator on Windows.
    policy_dir = repo / "harness" / "shared"
    policy_dir.mkdir(parents=True)
    (policy_dir / "governance-policy.json").write_text(json.dumps({"coverage": {"lines": 85}}))
    prof = detect.profile(repo)
    assert prof.threshold is not None
    assert prof.threshold.locator == "harness/shared/governance-policy.json:coverage.lines"
    assert "\\" not in prof.threshold.locator


# --- detect.to_posix_relative (Defect A: Windows path separator leak) ------


def test_to_posix_relative_renders_a_path_under_root_with_forward_slashes() -> None:
    result = detect.to_posix_relative(Path("/repo/openspec/changes/c1/spec.md"), Path("/repo"))
    assert result == "openspec/changes/c1/spec.md"
    assert "\\" not in result


def test_to_posix_relative_falls_back_to_the_full_path_when_not_under_root() -> None:
    outside = Path("/elsewhere/not/under/root/spec.md")
    result = detect.to_posix_relative(outside, Path("/repo"))
    assert result == outside.as_posix()
    assert "\\" not in result


def test_to_posix_relative_falls_back_when_root_is_none() -> None:
    given = Path("openspec/changes/c1/spec.md")
    result = detect.to_posix_relative(given, None)
    assert result == given.as_posix()
    assert "\\" not in result


def test_detect_prefers_coveragerc_over_setup_cfg(repo: Path) -> None:
    (repo / "pyproject.toml").write_text('[project]\nname = "demo"\n')
    (repo / ".coveragerc").write_text("[report]\nfail_under = 88\n")
    (repo / "setup.cfg").write_text("[coverage:report]\nfail_under = 70\n")
    prof = detect.profile(repo)
    assert prof.threshold is not None
    assert prof.threshold.value == 88


def test_detect_still_prefers_pyproject_over_coveragerc(repo: Path) -> None:
    # repo fixture's pyproject.toml already sets fail_under = 90 -- confirms
    # the additive-only precedence: pyproject.toml keeps winning.
    (repo / ".coveragerc").write_text("[report]\nfail_under = 70\n")
    prof = detect.profile(repo)
    assert prof.threshold is not None
    assert prof.threshold.value == 90


def test_detect_ignores_malformed_governance_policy_json(repo: Path) -> None:
    (repo / "governance-policy.json").write_text("{not valid json")
    prof = detect.profile(repo)
    assert prof.threshold is not None
    assert prof.threshold.value == 90
    assert "pyproject.toml" in prof.threshold.locator


def test_detect_ignores_malformed_coveragerc(repo: Path) -> None:
    # No [section] header at all -- reliably raises configparser's
    # MissingSectionHeaderError, unlike text that might parse leniently.
    (repo / ".coveragerc").write_text("this is not valid ini content at all")
    prof = detect.profile(repo)
    assert prof.threshold is not None
    assert prof.threshold.value == 90
    assert "pyproject.toml" in prof.threshold.locator


def test_detect_finds_make_targets_and_ignores_phony(repo: Path) -> None:
    prof = detect.profile(repo)
    assert {"test", "regression", "ci", "help"} <= set(prof.make_targets)
    assert ".PHONY" not in prof.make_targets


def test_g004_stays_silent_when_the_target_repo_has_no_makefile_at_all(repo: Path) -> None:
    (repo / "Makefile").unlink()
    prof = detect.profile(repo)
    assert prof.make_targets == ()
    assert prof.make_target_confidence == "high"  # vacuous: nothing was seen to lower confidence
    body = GOOD_HARNESS.replace("make regression", "make nope")
    found = findings_for(repo, body)
    assert "G004" not in rule_ids(found)


def test_make_targets_json_shape_is_a_list_of_strings(repo: Path) -> None:
    # AC-MP-7: byte-identical shape (list[str], sorted), regardless of how
    # machinery.py computes the underlying values.
    payload = detect.profile(repo).as_dict()
    assert isinstance(payload["make_targets"], list)
    assert all(isinstance(t, str) for t in payload["make_targets"])
    assert payload["make_targets"] == sorted(payload["make_targets"])


def test_to_card_excludes_absolute_paths(repo: Path) -> None:
    write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    card = detect.profile(repo).to_card()
    assert "root" not in card
    assert "openspec_root" not in card
    assert card["has_openspec_root"] is True
    assert card["schema_version"] == dialect_card.SCHEMA_VERSION


def test_to_card_reports_no_openspec_root_when_absent(repo: Path) -> None:
    card = detect.profile(repo).to_card()
    assert card["has_openspec_root"] is False


def test_to_card_never_exposes_raw_speckit_root_path(repo: Path) -> None:
    # speckit_root is a Path | None exactly like openspec_root, so it gets
    # openspec_root's own to_card() treatment (a has_* boolean), never
    # adr_source's (already a relative string by the time it reaches
    # to_card()) -- confirms the byte-identical-across-checkout-paths
    # contract AC-DC-4/DEC-AD-009 established still holds for the new field.
    write_speckit_spec(repo, "001-demo-capability", GOOD_SPECKIT)
    card = detect.profile(repo).to_card()
    assert "speckit_root" not in card
    assert card["has_speckit_root"] is True
    assert card["feature_dirs"] == ["001-demo-capability"]


def test_to_card_reports_no_speckit_root_when_absent(repo: Path) -> None:
    card = detect.profile(repo).to_card()
    assert card["has_speckit_root"] is False
    assert card["feature_dirs"] == []


def test_to_card_excludes_witnesses_and_current_sha(repo: Path) -> None:
    # current_sha changes on every commit by design -- including it in the
    # portable snapshot would manufacture constant false `detect --diff`
    # drift (DEC-WM-014).
    card = detect.profile(repo).to_card()
    assert "witnesses" not in card
    assert "current_sha" not in card
    assert "witnesses" not in dialect_card._COMPARABLE_FIELDS
    assert "current_sha" not in dialect_card._COMPARABLE_FIELDS


def test_detect_format_json_emits_a_dialect_card_with_schema_version(
    repo: Path, capsys
) -> None:
    assert main(["--target", str(repo), "detect", "--format", "json"]) == 0
    card = json.loads(capsys.readouterr().out)
    assert card["schema_version"] == dialect_card.SCHEMA_VERSION
    assert "root" not in card


def test_detect_format_json_is_byte_identical_across_runs(repo: Path, capsys) -> None:
    main(["--target", str(repo), "detect", "--format", "json"])
    first = capsys.readouterr().out
    main(["--target", str(repo), "detect", "--format", "json"])
    second = capsys.readouterr().out
    assert first == second


def test_detect_format_json_card_is_identical_across_different_checkout_paths(
    tmp_path_factory, capsys
) -> None:
    # The strongest proof of the portability property AC-DC-1/2 need: the
    # same logical repo at two different absolute paths must yield a
    # byte-identical card end-to-end, not just at the to_card() unit level.
    def _build(root: Path) -> None:
        (root / "Makefile").write_text(MAKEFILE)
        (root / "pyproject.toml").write_text(PYPROJECT)
        write_spec(root, "c1", "cap1", GOOD_HARNESS)

    root_a = tmp_path_factory.mktemp("checkout_a")
    root_b = tmp_path_factory.mktemp("checkout_b_longer_name")
    _build(root_a)
    _build(root_b)

    main(["--target", str(root_a), "detect", "--format", "json"])
    card_a = capsys.readouterr().out
    main(["--target", str(root_b), "detect", "--format", "json"])
    card_b = capsys.readouterr().out
    assert card_a == card_b


def test_detect_json_flag_still_emits_full_profile_unchanged(repo: Path, capsys) -> None:
    assert main(["--target", str(repo), "detect", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert "root" in payload
    assert "schema_version" not in payload


def test_detect_format_json_takes_precedence_over_legacy_json_flag(repo: Path, capsys) -> None:
    # Passing both --json and --format json together is an edge case a
    # user could plausibly hit (habitually adding --json alongside the
    # newer --format flag). --format json wins: it's the more specific,
    # explicitly-requested output mode. Documented here so the precedence
    # is a tested contract, not an accident of check-ordering.
    assert main(["--target", str(repo), "detect", "--json", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert "schema_version" in payload, "the card (--format json) must win over the legacy --json shape"
    assert "root" not in payload


def test_detect_diff_exits_nonzero_and_lists_changed_fields_on_drift(
    repo: Path, tmp_path: Path, capsys
) -> None:
    main(["--target", str(repo), "detect", "--format", "json"])
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(capsys.readouterr().out)

    (repo / "Makefile").write_text(MAKEFILE + "new-target:\n\techo hi\n")
    result = main(["--target", str(repo), "detect", "--diff", str(baseline_path)])
    out = capsys.readouterr().out
    assert result == 1
    assert "make_targets" in out


def test_detect_diff_exits_zero_on_no_drift(repo: Path, tmp_path: Path, capsys) -> None:
    main(["--target", str(repo), "detect", "--format", "json"])
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(capsys.readouterr().out)

    result = main(["--target", str(repo), "detect", "--diff", str(baseline_path)])
    out = capsys.readouterr().out
    assert result == 0
    assert "PASS" in out


def test_detect_diff_with_missing_baseline_is_a_usage_error(repo: Path) -> None:
    result = main(["--target", str(repo), "detect", "--diff", "/nonexistent/baseline.json"])
    assert result == 2


def test_detect_diff_with_valid_json_non_object_baseline_is_a_usage_error(
    repo: Path, tmp_path: Path, capsys
) -> None:
    # A baseline file can be syntactically valid JSON (null, a list, a
    # number) while still not being a card at all. json.loads() succeeds
    # on all of these, so this must be checked explicitly -- without it,
    # dialect_card.diff_cards()'s .get() calls raise AttributeError,
    # which prints a traceback and exits 1, indistinguishable from "real
    # drift found" and violating the documented 0/1/2 exit contract.
    for bad_baseline in ("null", "[]", "42", '"just a string"'):
        baseline_path = tmp_path / "baseline.json"
        baseline_path.write_text(bad_baseline)
        result = main(["--target", str(repo), "detect", "--diff", str(baseline_path)])
        assert result == 2, f"baseline {bad_baseline!r} should be a usage error, got exit {result}"
        assert "expected a JSON object" in capsys.readouterr().err


def test_detect_never_writes_to_the_target_repo(repo: Path) -> None:
    # AC-DC-3 (non-success): detect.py's own module docstring already
    # promises read-only; this proves it holds across every detect output
    # mode, not just the default text one.
    write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    before = {p: p.stat().st_mtime_ns for p in repo.rglob("*") if p.is_file()}

    assert main(["--target", str(repo), "detect"]) == 0
    assert main(["--target", str(repo), "detect", "--json"]) == 0
    assert main(["--target", str(repo), "detect", "--format", "json"]) == 0

    after = {p: p.stat().st_mtime_ns for p in repo.rglob("*") if p.is_file()}
    assert set(before) == set(after), "detect must never create or delete a file in the target repo"
    assert before == after, "detect must never modify a file in the target repo"


def test_multi_target_makefile_line_resolves_both_targets_end_to_end(repo: Path) -> None:
    (repo / "Makefile").write_text(MAKEFILE + "lint typecheck: test\n\techo ok\n")
    prof = detect.profile(repo)
    assert {"lint", "typecheck"} <= set(prof.make_targets)
    assert prof.make_target_confidence == "high"


def test_define_block_does_not_leak_a_bogus_target_through_the_legacy_widening_fallback(
    repo: Path,
) -> None:
    # A define block lowers machinery.py's confidence, which triggers
    # detect.py's legacy-regex widening fallback -- that fallback has the
    # identical define/endef blindness machinery.py was fixed for, so
    # fixing machinery.py alone is not sufficient end-to-end.
    (repo / "Makefile").write_text(MAKEFILE + "\ndefine HELP_TEXT\nUsage: make test\nendef\n")
    prof = detect.profile(repo)
    assert "Usage" not in prof.make_targets
    assert prof.make_target_confidence == "low"


def test_unterminated_define_block_does_not_hang_detect_end_to_end(repo: Path) -> None:
    # The shared O(n) strip_define_blocks implementation must keep
    # detect.profile() fast even through the legacy-fallback path, not
    # just when calling machinery.parse_makefile directly.
    import time

    (repo / "Makefile").write_text(MAKEFILE + "\ndefine X\n" + ("body line\n" * 20000))
    start = time.monotonic()
    prof = detect.profile(repo)
    elapsed = time.monotonic() - start
    assert elapsed < 5.0, f"detect.profile() took {elapsed:.2f}s on an unterminated define block"
    assert prof.make_target_confidence == "low"


def test_cli_detect_reports_low_confidence_makefile_parse(repo: Path, capsys) -> None:
    (repo / "Makefile").write_text("include extra.mk\nbuild:\n\techo hi\n")
    assert main(["--target", str(repo), "detect"]) == 0
    assert "low confidence" in capsys.readouterr().out.lower()


def test_g004_still_fires_on_a_genuinely_absent_target_at_low_confidence(repo: Path) -> None:
    # AC-MP-4 (non-success): low confidence must never weaken the rule.
    (repo / "Makefile").write_text(MAKEFILE + "include extra.mk\n")
    body = GOOD_HARNESS.replace("make regression", "make totally-nonexistent")
    found = findings_for(repo, body)
    assert "G004" in rule_ids(found)


def test_detect_collects_invariant_ids(repo: Path) -> None:
    prof = detect.profile(repo)
    assert prof.invariant_ids == ("INV-1", "INV-2")


def test_invariant_source_name_uses_the_real_file_name_when_present(repo: Path) -> None:
    # Shared by G005 (rules_generic.py) and G006 (rules.py) so the two
    # can't independently drift on this fallback wording.
    prof = detect.profile(repo)
    assert prof.invariant_source_name == "CONTRACT.md"


def test_invariant_source_name_falls_back_when_no_source_is_declared(tmp_path: Path) -> None:
    # repo has no CONTRACT.md/HARNESS_SPEC.md/etc -- no invariant source at all.
    (tmp_path / "Makefile").write_text(MAKEFILE)
    prof = detect.profile(tmp_path)
    assert prof.invariant_source is None
    assert prof.invariant_source_name == "the contract"


def test_detect_collects_adr_ids(tmp_path: Path) -> None:
    (tmp_path / "Makefile").write_text(MAKEFILE)
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-use-postgres.md").write_text("# ADR-1: Use Postgres\n")
    (adr_dir / "0002-use-rest.md").write_text("# ADR-2: Use REST\n")
    prof = detect.profile(tmp_path)
    assert prof.adr_ids == ("ADR-1", "ADR-2")


def test_adr_source_name_uses_the_real_directory_name_when_present(tmp_path: Path) -> None:
    # Shared by G008 (rules_generic.py) and G009 (rules.py) so the two
    # can't independently drift on this fallback wording.
    (tmp_path / "Makefile").write_text(MAKEFILE)
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-use-postgres.md").write_text("# ADR-1: Use Postgres\n")
    prof = detect.profile(tmp_path)
    assert prof.adr_source_name == "docs/adr"


def test_adr_source_name_falls_back_when_no_source_is_declared(repo: Path) -> None:
    # repo fixture has no docs/adr/ or any other ADR source at all.
    prof = detect.profile(repo)
    assert prof.adr_source is None
    assert prof.adr_source_name == "the ADR log"


def test_as_dict_reports_a_multi_segment_invariant_source_with_forward_slashes(
    tmp_path: Path,
) -> None:
    # repo fixture's own CONTRACT.md is a single, root-level segment (no
    # separator character on either OS) -- nest it so this actually exercises
    # StackProfile.as_dict()'s invariant_source relativization.
    (tmp_path / "Makefile").write_text(MAKEFILE)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "CONTRACT.md").write_text(CONTRACT)
    payload = detect.profile(tmp_path).as_dict()
    assert payload["invariant_source"] == "docs/CONTRACT.md"
    assert "\\" not in payload["invariant_source"]


def test_adrs_discovered_from_a_directory_of_numbered_files(tmp_path: Path) -> None:
    (tmp_path / "Makefile").write_text(MAKEFILE)
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-use-postgres.md").write_text("# ADR-1: Use Postgres\n")
    (adr_dir / "0002-use-rest.md").write_text("# ADR-2: Use REST\n")
    source, ids = detect._adrs(tmp_path)
    assert source == adr_dir
    assert ids == ("ADR-1", "ADR-2")


def test_adrs_discovered_from_a_single_index_file(tmp_path: Path) -> None:
    (tmp_path / "Makefile").write_text(MAKEFILE)
    index = tmp_path / "docs" / "ADR.md"
    index.parent.mkdir(parents=True)
    index.write_text("# Decisions\n\n- ADR-1: Use Postgres\n- ADR-2: Use REST\n")
    source, ids = detect._adrs(tmp_path)
    assert source == index
    assert ids == ("ADR-1", "ADR-2")


def test_adr_ids_do_not_mismatch_on_zero_padded_filenames(tmp_path: Path) -> None:
    # A file's zero-padded name ("0007-...") must never be read as the id --
    # ids come from each file's own text content, never its filename. Here
    # the filename says "7" but the body cites ADR-3; only ADR-3 is real.
    (tmp_path / "Makefile").write_text(MAKEFILE)
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0007-use-grpc.md").write_text("# ADR-3: Use gRPC\n")
    _source, ids = detect._adrs(tmp_path)
    assert ids == ("ADR-3",)
    assert "ADR-7" not in ids


def test_adr_directory_declaration_ignores_a_later_reference_to_another_adr(tmp_path: Path) -> None:
    # A file's declared id is its own FIRST mention (its title); a later
    # "Supersedes ADR-99" reference elsewhere in its body must not be
    # promoted to a second declaration -- ADR-99 was never really declared
    # here, just cited (Copilot review finding on PR #13).
    (tmp_path / "Makefile").write_text(MAKEFILE)
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-use-postgres.md").write_text(
        "# ADR-1: Use Postgres\n\nSupersedes ADR-99, which is no longer a real decision.\n"
    )
    _source, ids = detect._adrs(tmp_path)
    assert ids == ("ADR-1",)
    assert "ADR-99" not in ids


def test_adr_directory_declaration_prefers_a_heading_over_an_earlier_preamble_reference(
    tmp_path: Path,
) -> None:
    # A "first mention anywhere" heuristic mis-declares this file as ADR-1:
    # its body opens with a reference to a related decision *before* its
    # own heading. The real declaration is on the heading line itself, so
    # that must win regardless of what precedes it (adversarial review
    # finding on PR #13 -- a residual gap in the original Copilot-review
    # fix, which only handled a reference placed *after* the heading).
    (tmp_path / "Makefile").write_text(MAKEFILE)
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0002-use-grpc.md").write_text(
        "Related: ADR-1 (superseded by this decision).\n\n# ADR-2: Use gRPC\n"
    )
    _source, ids = detect._adrs(tmp_path)
    assert ids == ("ADR-2",)
    assert "ADR-1" not in ids


def test_adr_directory_declaration_skips_a_heading_with_no_id_to_find_a_later_one(
    tmp_path: Path,
) -> None:
    # A heading that itself contains no ADR id ("# Overview") must not stop
    # the search -- the real declaring heading can come after it.
    (tmp_path / "Makefile").write_text(MAKEFILE)
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0004-use-kafka.md").write_text("# Overview\n\n# ADR-4: Use Kafka\n")
    _source, ids = detect._adrs(tmp_path)
    assert ids == ("ADR-4",)


@pytest.mark.skipif(not _CAN_SYMLINK, reason="platform/user lacks symlink-creation privilege")
def test_adr_directory_read_error_is_skipped_not_crashed(tmp_path: Path) -> None:
    # glob("*.md") lists directory entries by name pattern only -- it
    # doesn't check they're readable. A dangling symlink still matches and
    # previously made read_text() raise an uncaught FileNotFoundError,
    # crashing detect.profile() (and therefore every CLI verb) on any
    # target repo with a broken symlink under docs/adr/ (adversarial
    # review finding on PR #13). The broken entry must be skipped like any
    # other non-declaring file, leaving the real declarations intact.
    (tmp_path / "Makefile").write_text(MAKEFILE)
    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-use-postgres.md").write_text("# ADR-1: Use Postgres\n")
    (adr_dir / "0002-broken.md").symlink_to(adr_dir / "does-not-exist.md")
    source, ids = detect._adrs(tmp_path)
    assert source == adr_dir
    assert ids == ("ADR-1",)


def test_adr_directory_with_no_ids_falls_through_to_the_next_candidate(tmp_path: Path) -> None:
    (tmp_path / "Makefile").write_text(MAKEFILE)
    empty_adr_dir = tmp_path / "docs" / "adr"
    empty_adr_dir.mkdir(parents=True)
    (empty_adr_dir / "README.md").write_text("Nothing declared here yet.\n")
    index = tmp_path / "docs" / "ADR.md"
    index.write_text("# Decisions\n\n- ADR-1: Use Postgres\n")
    source, ids = detect._adrs(tmp_path)
    assert source == index
    assert ids == ("ADR-1",)


def test_adr_single_file_with_no_ids_falls_through_to_the_next_candidate(tmp_path: Path) -> None:
    (tmp_path / "Makefile").write_text(MAKEFILE)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "adr").write_text("Nothing declared here yet.\n")
    decisions = tmp_path / "docs" / "architecture" / "decisions"
    decisions.parent.mkdir(parents=True)
    decisions.write_text("# ADR-5: Use gRPC\n")
    source, ids = detect._adrs(tmp_path)
    assert source == decisions
    assert ids == ("ADR-5",)


def test_waiver_reason_text_is_not_scanned_as_a_citation(repo: Path) -> None:
    # A waiver's own reason text must not satisfy the citation it's waiving
    # -- naming "ADR-1"/"INV-77" in a reason must not add it to
    # adr_refs/invariant_refs and silently resolve the very orphan the
    # waiver exists to suppress (Copilot review finding on PR #13; the
    # identical bug already existed, unfixed, for INV_REF since CP-4).
    # INV-77 (not GOOD_HARNESS's own legitimately-cited INV-1) isolates the
    # waiver-comment-only citation from the fixture's real citations.
    body = GOOD_HARNESS.replace(
        "## Problem Statement",
        "<!-- specgraph:allow G009 ADR-1 and INV-77 are cited here only to "
        "prove the waiver's own reason text is never scanned as a citation "
        "-->\n\n## Problem Statement",
    )
    path = write_spec(repo, "demo-change", "demo-cap", body)
    spec = parse_spec(path, "harness")
    assert "ADR-1" not in spec.adr_refs
    assert "INV-77" not in spec.invariant_refs


def test_waiver_reason_text_is_not_scanned_as_a_stage_citation_harness(repo: Path) -> None:
    # The identical bug as test_waiver_reason_text_is_not_scanned_as_a_citation,
    # but for Criterion.verified_by specifically -- parse_spec()'s citation_text
    # fix only ever covered the spec-wide make_refs/invariant_refs/adr_refs
    # fields; VERIFIED_BY.search() still ran on raw text (found designing
    # CP-WM: this citation gates a build under --require-witness, not just a
    # cosmetic graph edge). VERIFIED_BY has no re.DOTALL, so the leak needs
    # the waiver comment on the same line as _Verified by:_.
    body = GOOD_HARNESS.replace(
        "_Verified by:_ `pytest -k test_attested_write` · stage: `make regression`",
        "_Verified by:_ `pytest -k test_attested_write` · stage: `make regression` "
        "<!-- specgraph:allow G004 mentions `make bogus` only to prove waiver "
        "text is never scanned as a citation -->",
    )
    path = write_spec(repo, "demo-change", "demo-cap", body)
    spec = parse_spec(path, "harness")
    crit = next(c for c in spec.criteria if c.ident == "AC-DMO-1")
    assert "bogus" not in crit.verified_by
    assert "regression" in crit.verified_by


def test_waiver_reason_text_is_not_scanned_as_a_stage_citation_upstream(repo: Path) -> None:
    # Same bug, upstream dialect: Criterion.verified_by is the *entire*
    # Scenario block, so a waiver comment anywhere within it leaks -- not
    # just on one line, unlike harness's narrower exposure. This is the
    # wider, gate-defeating half of the bug adversarial review found while
    # designing CP-WM.
    body = GOOD_UPSTREAM.replace(
        "- **THEN** an evidence id is recorded",
        "- **THEN** an evidence id is recorded\n\n"
        "<!-- specgraph:allow G004 mentions `make bogus` only to prove waiver "
        "text is never scanned as a citation -->",
    )
    path = write_spec(repo, "demo-change", "demo-cap", body)
    spec = parse_spec(path, "upstream")
    crit = next(c for c in spec.criteria if c.ident == "SCEN-1")
    assert "bogus" not in crit.verified_by
    assert "regression" in crit.verified_by


def test_dialect_detection_distinguishes_both_forms(repo: Path) -> None:
    harness = write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    upstream = write_spec(repo, "c2", "cap2", GOOD_UPSTREAM)
    assert detect.detect_dialect([harness]) == "harness"
    assert detect.detect_dialect([upstream]) == "upstream"
    assert detect.detect_dialect([harness, upstream]) == "mixed"


def test_dialect_unknown_when_no_specs() -> None:
    assert detect.detect_dialect([]) == "unknown"


