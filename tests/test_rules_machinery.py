"""CP-3: G003 drift semantics and G004 scoped make-target detection.

G003 fires only on drift — a threshold literal that differs from the detected
coverage floor, or any literal when no floor is detected. A literal matching the
floor is agreement, not a violation.

G004 fires only on make targets cited in execution contexts (verified-by lines
and the Validation Matrix), not on prose like "make a decision".
"""

from __future__ import annotations

import json
from pathlib import Path

from tests.support import run_cli, write_spec

MAKEFILE = "test:\n\tpytest\n"
PYPROJECT_FLOOR_85 = "[tool.coverage.report]\nfail_under = 85\n"
PYPROJECT_NO_FLOOR = "[tool.ruff]\nline-length = 100\n"


def _spec(threshold_text: str, verified_by: str, prose: str = "") -> str:
    return f"""\
# Spec: Demo

> **Status:** DRAFT

## Problem Statement

{prose}

## Requirements

- R-DMO-1: The system MUST meet the floor.

## Acceptance Criteria

- [ ] **AC-DMO-1 (non-success):** Coverage is {threshold_text}, else the gate
  refuses the build. (R-DMO-1)
  _Verified by:_ `{verified_by}` · stage: `make test`

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-DMO-1 |
"""


def _findings(repo: Path, spec: str, pyproject: str = PYPROJECT_FLOOR_85) -> list[str]:
    (repo / "pyproject.toml").write_text(pyproject)
    (repo / "Makefile").write_text(MAKEFILE)
    write_spec(repo, "c1", "cap", spec)
    result = run_cli(repo, "validate", "--json")
    payload = json.loads(result.stdout)
    return [f["rule"] for f in payload["findings"]]


# --- G003 drift semantics ----------------------------------------------------


def test_g003_matching_floor_not_a_violation(tmp_path: Path) -> None:
    """A threshold literal matching the detected floor is not a finding."""
    findings = _findings(
        tmp_path, _spec(threshold_text="85%", verified_by="pytest -k t")
    )
    assert "G003" not in findings


def test_g003_differing_floor_is_a_violation(tmp_path: Path) -> None:
    """A threshold literal that differs from the floor drifts -> G003."""
    findings = _findings(
        tmp_path, _spec(threshold_text="90%", verified_by="pytest -k t")
    )
    assert "G003" in findings


def test_g003_no_floor_literal_still_fires(tmp_path: Path) -> None:
    """With no detected floor, any threshold literal is unbound -> G003."""
    findings = _findings(
        tmp_path,
        _spec(threshold_text="90%", verified_by="pytest -k t"),
        pyproject=PYPROJECT_NO_FLOOR,
    )
    assert "G003" in findings


# --- G004 scoped make-target detection --------------------------------------


def test_g004_prose_make_does_not_fire(tmp_path: Path) -> None:
    """`make a` in prose must not trip G004."""
    findings = _findings(
        tmp_path,
        _spec(
            threshold_text="85%",
            verified_by="pytest -k t",
            prose="We must make a decision about the floor before merging.",
        ),
    )
    assert "G004" not in findings


def test_g004_verified_by_missing_target_fires(tmp_path: Path) -> None:
    """`make nope` on a verified-by line cites a target that does not exist."""
    findings = _findings(
        tmp_path,
        _spec(threshold_text="85%", verified_by="make nope"),
    )
    assert "G004" in findings


def test_g004_validation_matrix_missing_target_fires(tmp_path: Path) -> None:
    """`make nope` in the Validation Matrix Make Target column is a citation."""
    spec = _spec(threshold_text="85%", verified_by="pytest -k t").replace(
        "| Focused | `make test` |", "| Focused | `make nope` |"
    )
    findings = _findings(tmp_path, spec)
    assert "G004" in findings


# --- G004 scoped: upstream-dialect Scenario steps ----------------------------


def _upstream_spec(when_line: str) -> str:
    return f"""\
# Spec delta — Demo capability

## ADDED Requirements

### Requirement: the writer SHALL run the suite

The writer runs the gate.

#### Scenario: the suite runs

- **GIVEN** a writer
- **WHEN** {when_line}
- **THEN** an evidence id is recorded

#### Scenario: a bad write is caught

- **GIVEN** a writer with no attestation
- **WHEN** the suite runs
- **THEN** the check fails
"""


def test_g004_scenario_backticked_missing_target_fires(tmp_path: Path) -> None:
    """A backticked `make nope` in a Scenario step cites a missing target."""
    findings = _findings(tmp_path, _upstream_spec("`make nope` runs the suite"))
    assert "G004" in findings


def test_g004_scenario_prose_no_backtick_does_not_fire(tmp_path: Path) -> None:
    """Bare prose 'make a decision' in a Scenario is not a citation."""
    findings = _findings(
        tmp_path, _upstream_spec("we make a decision before running the suite")
    )
    assert "G004" not in findings
