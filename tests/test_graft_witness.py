"""Witness mode (CP-WM): the data model, rules W001/W002, and the CLI verb."""

from __future__ import annotations

import dataclasses
import json
import logging
import subprocess
import textwrap
from pathlib import Path

import pytest

from openspec_graph import detect, rules, witness
from openspec_graph.cli import build_parser, main
from openspec_graph.parse import parse_spec
from tests.graft_support import (
    GOOD_HARNESS,
    GOOD_UPSTREAM,
)
from tests.support import run_cli, write_spec

# --- witness mode data model (CP-WM) ----------------------------------------


def _git_init_and_commit(repo: Path) -> None:
    for args in (
        ["git", "init", "-q"],
        ["git", "config", "user.email", "test@example.com"],
        ["git", "config", "user.name", "Test"],
        ["git", "add", "-A"],
        ["git", "commit", "-q", "-m", "init"],
    ):
        subprocess.run(args, cwd=repo, check=True)


@pytest.mark.unit
def test_stack_profile_construction_still_works_without_witness_fields(repo: Path) -> None:
    # New StackProfile fields must be additive (C-WM-1) -- a caller building
    # a StackProfile without knowing about witnesses/current_sha (every
    # field predating CP-WM) still gets sane defaults.
    prof = detect.StackProfile(
        root=repo,
        languages=(),
        make_targets=(),
        openspec_root=None,
        change_dirs=(),
        dialect="harness",
        threshold=None,
        invariant_source=None,
        invariant_ids=(),
        has_project_md=False,
    )
    assert prof.witnesses == ()
    assert prof.current_sha is None


@pytest.mark.unit
def test_stack_profile_construction_still_works_without_speckit_fields(repo: Path) -> None:
    # New StackProfile fields must be additive (R-SK-1) -- a caller building
    # a StackProfile without knowing about speckit_root/feature_dirs (every
    # field predating this change) still gets sane defaults.
    prof = detect.StackProfile(
        root=repo,
        languages=(),
        make_targets=(),
        openspec_root=None,
        change_dirs=(),
        dialect="harness",
        threshold=None,
        invariant_source=None,
        invariant_ids=(),
        has_project_md=False,
    )
    assert prof.speckit_root is None
    assert prof.feature_dirs == ()


@pytest.mark.unit
def test_current_sha_returns_none_outside_a_git_repo(repo: Path) -> None:
    assert detect._current_sha(repo) is None


@pytest.mark.e2e
def test_current_sha_reads_head_inside_a_real_git_repo(repo: Path) -> None:
    _git_init_and_commit(repo)
    sha = detect._current_sha(repo)
    real = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()
    assert sha == real
    assert sha is not None and len(sha) == 40


@pytest.mark.e2e
def test_current_sha_is_not_invoked_when_no_witnesses_are_present(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # detect.profile() runs on every detect/validate/graph call -- computing
    # the current sha is meaningless with zero witnesses to compare against,
    # so it must be skipped entirely, not just discarded (DEC-WM-008).
    calls: list[object] = []
    original_run = subprocess.run

    def spy(*args: object, **kwargs: object) -> object:
        calls.append(args)
        return original_run(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(detect.subprocess, "run", spy)
    prof = detect.profile(repo)
    assert calls == []
    assert prof.current_sha is None


@pytest.mark.unit
def test_profile_witnesses_field_reads_the_planlint_witnesses_directory(repo: Path) -> None:
    w = witness.Witness(
        schema_version=witness.WITNESS_SCHEMA_VERSION,
        stage="test",
        exit_code=0,
        coverage=97.0,
        sha="a" * 40,
        recorded_at="2026-01-01T00:00:00Z",
    )
    witness.write_witness(repo, w)
    assert detect.profile(repo).witnesses == (w,)


@pytest.mark.e2e
def test_profile_current_sha_is_populated_once_a_witness_exists_in_a_git_repo(repo: Path) -> None:
    _git_init_and_commit(repo)
    witness.write_witness(
        repo,
        witness.Witness(
            schema_version=witness.WITNESS_SCHEMA_VERSION,
            stage="test",
            exit_code=0,
            coverage=None,
            sha="a" * 40,
            recorded_at="2026-01-01T00:00:00Z",
        ),
    )
    prof = detect.profile(repo)
    assert prof.current_sha is not None
    assert len(prof.current_sha) == 40


# --- witness mode rules W001/W002 (CP-WM) -----------------------------------

CURRENT_SHA = "a" * 40
OTHER_SHA = "b" * 40


def _profile_with(repo: Path, *, witnesses: tuple = (), current_sha: str | None = CURRENT_SHA) -> detect.StackProfile:
    return dataclasses.replace(detect.profile(repo), witnesses=witnesses, current_sha=current_sha)


def _witness(**overrides: object) -> witness.Witness:
    fields: dict[str, object] = {
        "schema_version": witness.WITNESS_SCHEMA_VERSION,
        "stage": "regression",
        "exit_code": 0,
        "coverage": None,
        "sha": CURRENT_SHA,
        "recorded_at": "2026-01-01T00:00:00Z",
    }
    fields.update(overrides)
    return witness.Witness(**fields)  # type: ignore[arg-type]


@pytest.mark.unit
def test_w001_fires_when_a_cited_stage_has_no_matching_witness(repo: Path) -> None:
    path = write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    prof = _profile_with(repo, witnesses=())
    found = rules.evaluate(parse_spec(path, "harness"), prof, rules.RULES)
    assert any(f.rule == "W001" for f in found)


@pytest.mark.unit
def test_w001_reports_never_witnessed_not_a_sha_failure_when_the_store_is_empty(
    repo: Path,
) -> None:
    # Copilot review finding on PR #14: detect.profile()'s real wiring sets
    # current_sha=None whenever witnesses is empty (DEC-WM-008's lazy skip)
    # -- so the common "nobody has run `witness` yet" case must not read as
    # "sha could not be determined" (a misdiagnosis suggesting a git
    # problem). Mirrors the real StackProfile relationship exactly, unlike
    # test_w001_fires_for_every_citation_when_current_sha_is_none below,
    # which deliberately tests the other case: witnesses exist but sha
    # detection itself failed.
    path = write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    prof = _profile_with(repo, witnesses=(), current_sha=None)
    found = rules.evaluate(parse_spec(path, "harness"), prof, rules.RULES)
    w001 = [f for f in found if f.rule == "W001"]
    assert w001 and "never been witnessed" in w001[0].message
    assert not any("could not be determined" in f.message for f in w001)


@pytest.mark.unit
def test_w001_fires_when_the_witness_sha_does_not_match_current_sha(repo: Path) -> None:
    path = write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    prof = _profile_with(repo, witnesses=(_witness(sha=OTHER_SHA),))
    found = rules.evaluate(parse_spec(path, "harness"), prof, rules.RULES)
    w001 = [f for f in found if f.rule == "W001"]
    assert w001 and "not at the current commit" in w001[0].message


@pytest.mark.unit
def test_w001_fires_when_the_matching_witness_recorded_a_nonzero_exit_code(repo: Path) -> None:
    path = write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    prof = _profile_with(repo, witnesses=(_witness(exit_code=1),))
    found = rules.evaluate(parse_spec(path, "harness"), prof, rules.RULES)
    w001 = [f for f in found if f.rule == "W001"]
    assert w001 and "failing run" in w001[0].message


@pytest.mark.unit
def test_w001_fires_for_every_citation_when_current_sha_is_none(repo: Path) -> None:
    path = write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    prof = _profile_with(repo, witnesses=(_witness(),), current_sha=None)
    found = rules.evaluate(parse_spec(path, "harness"), prof, rules.RULES)
    w001 = [f for f in found if f.rule == "W001"]
    assert w001 and "could not be determined" in w001[0].message


@pytest.mark.unit
def test_w001_does_not_fire_when_a_fresh_passing_witness_exists(repo: Path) -> None:
    path = write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    prof = _profile_with(repo, witnesses=(_witness(),))
    found = rules.evaluate(parse_spec(path, "harness"), prof, rules.RULES)
    assert not any(f.rule == "W001" for f in found)


@pytest.mark.unit
def test_w002_fires_when_witness_coverage_is_below_the_detected_floor(repo: Path) -> None:
    path = write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    prof = _profile_with(repo, witnesses=(_witness(coverage=50.0),))
    assert prof.threshold is not None and prof.threshold.value == 90
    found = rules.evaluate(parse_spec(path, "harness"), prof, rules.RULES)
    assert any(f.rule == "W002" for f in found)


@pytest.mark.unit
def test_w002_does_not_fire_when_witness_coverage_meets_the_floor(repo: Path) -> None:
    path = write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    prof = _profile_with(repo, witnesses=(_witness(coverage=95.0),))
    found = rules.evaluate(parse_spec(path, "harness"), prof, rules.RULES)
    assert not any(f.rule == "W002" for f in found)


@pytest.mark.unit
def test_w002_does_not_fire_when_the_witness_has_no_recorded_coverage(repo: Path) -> None:
    path = write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    prof = _profile_with(repo, witnesses=(_witness(coverage=None),))
    found = rules.evaluate(parse_spec(path, "harness"), prof, rules.RULES)
    assert not any(f.rule == "W002" for f in found)


@pytest.mark.unit
def test_w002_does_not_fire_when_there_is_no_detected_coverage_floor(repo: Path) -> None:
    path = write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    prof = dataclasses.replace(_profile_with(repo, witnesses=(_witness(coverage=1.0),)), threshold=None)
    found = rules.evaluate(parse_spec(path, "harness"), prof, rules.RULES)
    assert not any(f.rule == "W002" for f in found)


@pytest.mark.unit
def test_w002_does_not_evaluate_a_witness_that_already_fails_w001(repo: Path) -> None:
    # A failing (nonzero exit) witness with low coverage must not ALSO
    # produce a W002 finding -- that's W001's own finding to make (DEC-WM-012).
    path = write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    prof = _profile_with(repo, witnesses=(_witness(exit_code=1, coverage=1.0),))
    found = rules.evaluate(parse_spec(path, "harness"), prof, rules.RULES)
    assert not any(f.rule == "W002" for f in found)
    assert any(f.rule == "W001" for f in found)


@pytest.mark.unit
def test_witness_rules_apply_to_both_dialects(repo: Path) -> None:
    path = write_spec(repo, "c1", "cap1", GOOD_UPSTREAM)
    prof = _profile_with(repo, witnesses=())
    found = rules.evaluate(parse_spec(path, "upstream"), prof, rules.RULES)
    assert any(f.rule == "W001" for f in found)


@pytest.mark.unit
def test_w001_fires_independently_for_each_stage_cited_in_one_upstream_scenario(repo: Path) -> None:
    # DEC-WM-016: a scenario mentioning more than one backtick-fenced stage
    # requires a witness for every citation -- no heuristic picks "the real
    # one."
    body = textwrap.dedent(
        """\
        # Spec delta — Demo capability

        ## ADDED Requirements

        ### Requirement: the writer SHALL attest every write

        Prose obligation.

        #### Scenario: attested writes record an evidence id

        - **GIVEN** `make build` has succeeded
        - **WHEN** `make regression` runs the suite
        - **THEN** an evidence id is recorded
        """
    )
    path = write_spec(repo, "c1", "cap1", body)
    prof = _profile_with(repo, witnesses=())
    found = rules.evaluate(parse_spec(path, "upstream"), prof, rules.RULES)
    messages = " ".join(f.message for f in found if f.rule == "W001")
    assert "`build`" in messages
    assert "`regression`" in messages


@pytest.mark.unit
def test_w001_reports_never_witnessed_for_a_stage_the_non_empty_store_lacks(repo: Path) -> None:
    # The store isn't empty (so the top-level "nothing has ever been
    # witnessed" short-circuit doesn't apply) and current_sha is known, but
    # none of the recorded witnesses are for this specific stage -- must
    # still fall through to the same "never been witnessed" message, not
    # the "not at the current commit" one (that's for a witness that
    # exists for this stage but at a stale sha, a different case).
    body = textwrap.dedent(
        """\
        # Spec delta — Demo capability

        ## ADDED Requirements

        ### Requirement: the writer SHALL attest every write

        Prose obligation.

        #### Scenario: attested writes record an evidence id

        - **GIVEN** `make build` has succeeded
        - **WHEN** `make regression` runs the suite
        - **THEN** an evidence id is recorded
        """
    )
    path = write_spec(repo, "c1", "cap1", body)
    prof = _profile_with(repo, witnesses=(_witness(stage="build"),))
    found = rules.evaluate(parse_spec(path, "upstream"), prof, rules.RULES)
    w001 = {f.message for f in found if f.rule == "W001"}
    assert not any("`build`" in m for m in w001)
    assert any("`regression`" in m and "never been witnessed" in m for m in w001)


@pytest.mark.unit
def test_w001_waiver_suppresses_the_finding_and_downgrades_to_info(repo: Path) -> None:
    body = GOOD_HARNESS.replace(
        "## Problem Statement",
        "<!-- specgraph:allow W001 CI witness upload not wired up yet -->\n\n## Problem Statement",
    )
    path = write_spec(repo, "c1", "cap1", body)
    prof = _profile_with(repo, witnesses=())
    found = rules.evaluate(parse_spec(path, "harness"), prof, rules.RULES)
    w001 = [f for f in found if f.rule == "W001"]
    assert w001
    assert all(f.severity == "INFO" for f in w001)
    assert all(f.message.startswith("[waived]") for f in w001)


@pytest.mark.unit
def test_w001_waiver_is_inert_when_require_witness_is_not_passed(repo: Path) -> None:
    # A W001/W002 waiver has nothing to suppress on a run that never
    # evaluates the rules at all (DEC-WM-015) -- not a bug, just inert.
    body = GOOD_HARNESS.replace(
        "## Problem Statement",
        "<!-- specgraph:allow W001 CI witness upload not wired up yet -->\n\n## Problem Statement",
    )
    path = write_spec(repo, "c1", "cap1", body)
    prof = _profile_with(repo, witnesses=())
    found = rules.evaluate(parse_spec(path, "harness"), prof)  # default rule_set = NON_WITNESS_RULES
    assert not any(f.rule == "W001" for f in found)


# --- witness mode CLI: `witness` verb + `validate --require-witness` -------


@pytest.mark.unit
def test_cli_witness_stage_flag_does_not_collide_with_global_target(repo: Path) -> None:
    args = build_parser().parse_args(
        ["--target", str(repo), "witness", "--stage", "test", "--exit", "0", "--sha", "a" * 40]
    )
    assert args.target == str(repo)
    assert args.stage == "test"


@pytest.mark.unit
def test_cli_witness_rejects_a_target_that_is_not_a_directory(tmp_path: Path, capsys) -> None:
    # cmd_witness resolves --target itself rather than going through
    # _profile() (which would run the whole detection pipeline for no
    # benefit here) -- its own "not a directory" guard needs its own test.
    missing = tmp_path / "does-not-exist"
    exit_code = main(["--target", str(missing), "witness", "--stage", "test", "--exit", "0", "--sha", "a" * 40])
    assert exit_code == 2
    assert "not a directory" in capsys.readouterr().err.lower()


@pytest.mark.unit
def test_cli_witness_verb_rejects_an_abbreviated_sha(repo: Path, capsys) -> None:
    exit_code = main(["--target", str(repo), "witness", "--stage", "test", "--exit", "0", "--sha", "abc1234"])
    assert exit_code == 2
    assert "40-character" in capsys.readouterr().err


@pytest.mark.unit
def test_cli_witness_verb_rejects_an_out_of_range_coverage_value(repo: Path, capsys) -> None:
    exit_code = main(
        ["--target", str(repo), "witness", "--stage", "test", "--exit", "0", "--coverage", "150", "--sha", "a" * 40]
    )
    assert exit_code == 2
    assert "coverage" in capsys.readouterr().err.lower()


@pytest.mark.unit
def test_cli_witness_verb_rejects_a_non_finite_coverage_value(repo: Path, capsys) -> None:
    exit_code = main(
        ["--target", str(repo), "witness", "--stage", "test", "--exit", "0", "--coverage", "nan", "--sha", "a" * 40]
    )
    assert exit_code == 2
    assert "coverage" in capsys.readouterr().err.lower()


@pytest.mark.unit
def test_cli_witness_records_a_zero_coverage_value_distinctly_from_none(repo: Path) -> None:
    exit_code = main(
        ["--target", str(repo), "witness", "--stage", "test", "--exit", "0", "--coverage", "0", "--sha", "a" * 40]
    )
    assert exit_code == 0
    recorded = witness.load_witnesses(repo)
    assert len(recorded) == 1
    assert recorded[0].coverage == 0.0


@pytest.mark.unit
def test_cli_witness_prints_a_forward_slash_path(repo: Path, capsys) -> None:
    exit_code = main(
        ["--target", str(repo), "witness", "--stage", "test", "--exit", "0", "--sha", "a" * 40]
    )
    assert exit_code == 0
    out = capsys.readouterr().out
    assert out.startswith("witness recorded: .planlint/witnesses/")
    assert "\\" not in out


@pytest.mark.unit
def test_cli_witness_rejects_a_malformed_stage(repo: Path, capsys) -> None:
    exit_code = main(["--target", str(repo), "witness", "--stage", "Not Valid", "--exit", "0", "--sha", "a" * 40])
    assert exit_code == 2
    assert "stage" in capsys.readouterr().err.lower()


@pytest.mark.unit
def test_cli_witness_reports_a_clean_error_when_the_witness_directory_is_unwritable(
    repo: Path, capsys
) -> None:
    # A file sitting where the witness directory needs to be created is a
    # portable way to force write_witness() to fail regardless of whether
    # tests run as root (permission bits alone are unreliable there) -- the
    # resulting OSError must produce a clean exit-2 message, not a traceback.
    (repo / ".planlint").write_text("not a directory")
    exit_code = main(["--target", str(repo), "witness", "--stage", "test", "--exit", "0", "--sha", "a" * 40])
    assert exit_code == 2
    assert "cannot write" in capsys.readouterr().err.lower()


@pytest.mark.unit
def test_validate_without_require_witness_never_evaluates_w001(repo: Path, capsys) -> None:
    write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    exit_code = main(["--target", str(repo), "validate", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert not any(f["rule"] == "W001" for f in out["findings"])


@pytest.mark.unit
def test_validate_without_require_witness_prints_no_witness_related_stderr(repo: Path, capsys) -> None:
    # Copilot review finding on PR #14: the default (flag-absent) path is
    # every existing caller's own behavior, unmodified by this change --
    # printing new INFO noise on it, forever, would contradict that and
    # could break a downstream consumer expecting clean stderr on success.
    # Unlike the --change-scoped skip messages below (a real, narrowed-scope
    # caveat worth flagging every time), there is nothing to flag here.
    write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    main(["--target", str(repo), "validate"])
    assert "witness" not in capsys.readouterr().err.lower()


@pytest.mark.unit
def test_validate_require_witness_fails_closed_on_a_repo_with_no_witness_store(repo: Path) -> None:
    # AC-WM-9, literal: zero witnesses must never read as "passed".
    write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    assert main(["--target", str(repo), "validate", "--require-witness"]) == 1


@pytest.mark.e2e
def test_validate_require_witness_passes_once_a_matching_fresh_witness_is_recorded(
    repo: Path, capsys
) -> None:
    write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    _git_init_and_commit(repo)
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()
    record_exit = main(
        [
            "--target", str(repo), "witness",
            "--stage", "regression", "--exit", "0", "--coverage", "95", "--sha", sha,
        ]
    )
    assert record_exit == 0
    capsys.readouterr()
    assert main(["--target", str(repo), "validate", "--require-witness"]) == 0




# --- debug logging: why the current sha is unknown ----------------------------
#
# Every failure of the one `git rev-parse HEAD` call folds to ``None``, which
# W001 reports as "the current commit sha could not be determined". The verdict
# stays one case; the log line says which of four it was.


def _capture_detect(caplog: pytest.LogCaptureFixture) -> logging.Logger:
    target = logging.getLogger("planlint.detect")
    target.addHandler(caplog.handler)
    caplog.set_level(logging.DEBUG, logger="planlint.detect")
    return target


@pytest.mark.unit
@pytest.mark.parametrize(
    ("label", "outcome", "expected"),
    [
        ("git-missing", FileNotFoundError(2, "No such file"), "could not run git (FileNotFoundError)"),
        ("timeout", subprocess.TimeoutExpired(cmd="git", timeout=detect.GIT_TIMEOUT_SECONDS), "exceeded"),
        ("not-a-repo", subprocess.CompletedProcess(["git"], 128, "", "fatal"), "exited 128"),
        ("garbage", subprocess.CompletedProcess(["git"], 0, "not-a-sha\n", ""), "unexpected git output"),
    ],
)
def test_each_unknown_sha_cause_is_logged_and_still_returns_none(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    label: str,
    outcome: object,
    expected: str,
) -> None:
    def fake_run(*_args: object, **kwargs: object) -> object:
        assert kwargs.get("timeout") == detect.GIT_TIMEOUT_SECONDS
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    monkeypatch.setattr(detect.subprocess, "run", fake_run)
    target = _capture_detect(caplog)
    try:
        assert detect._current_sha(repo) is None, label
    finally:
        target.removeHandler(caplog.handler)
    assert any(expected in r.getMessage() for r in caplog.records), [r.getMessage() for r in caplog.records]


@pytest.mark.e2e
def test_a_resolved_sha_is_logged(repo: Path, caplog: pytest.LogCaptureFixture) -> None:
    _git_init_and_commit(repo)
    target = _capture_detect(caplog)
    try:
        sha = detect._current_sha(repo)
    finally:
        target.removeHandler(caplog.handler)
    assert sha is not None
    assert any(r.getMessage() == f"current sha: {sha}" for r in caplog.records)


@pytest.mark.e2e
def test_verbose_validate_names_a_dropped_witness_on_stderr_and_keeps_stdout_clean(repo: Path) -> None:
    """Integration: the reason reaches an operator through ``--verbose``, on
    stderr only; the verdict is the same fail-closed W001 as without it, and
    the machine-readable stdout carries no log line."""
    write_spec(repo, "c1", "cap1", GOOD_HARNESS)
    _git_init_and_commit(repo)
    store = repo / witness.WITNESS_DIR_NAME
    store.mkdir(parents=True)
    bad = b'{"schema_version": 99}'
    name = f"{witness.compute_hash(bad)}.json"
    (store / name).write_bytes(bad)

    quiet = run_cli(repo, "validate", "--require-witness", "--format", "json")
    loud = run_cli(repo, "-v", "validate", "--require-witness", "--format", "json")

    assert loud.returncode == quiet.returncode == 1
    assert json.loads(loud.stdout)["findings"] == json.loads(quiet.stdout)["findings"]
    assert any(f["rule"] == "W001" for f in json.loads(loud.stdout)["findings"])
    assert f"skipping {name}: schema_version 99 is not" in loud.stderr
    assert "skipping" not in quiet.stderr
