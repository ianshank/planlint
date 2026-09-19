"""Shared constants and helpers for the `test_graft_*` modules.

Split out of `tests/test_graft.py`, which had grown to 2321 lines covering six
unrelated subjects. Not named `test_*`, so pytest does not collect it as a test
module. The importing modules name what they use, so each file's dependency on
this one is visible rather than ambient.

`tests/support.py` stays the home for helpers shared across the *whole* suite;
this holds the ones shared by the graft family only, which is the distinction
that file's own note draws. The `repo` fixture that is built from these
constants lives in `tests/conftest.py` -- see the reason there.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from openspec_graph import detect, rules
from openspec_graph.parse import parse_spec
from tests import support
from tests.support import write_spec

# at all -- probed once, at this module's import time, not assumed from
# sys.platform, so a Windows box that does have one of those enabled still
# runs this test.
_CAN_SYMLINK = support.supports_symlinks()



MAKEFILE = textwrap.dedent(
    """\
    .PHONY: help test regression ci
    help: ## show help
    \t@echo hi
    test: ## run tests
    \tpytest
    regression: ## regression tier
    \tpytest tests/regression
    ci: test regression ## full
    \t@echo ok
    """
)

PYPROJECT = textwrap.dedent(
    """\
    [project]
    name = "demo"

    [tool.coverage.report]
    fail_under = 90
    """
)

CONTRACT = "# Contract\n\n- INV-1 no unattested writes\n- INV-2 gates are ordered\n"

GOOD_HARNESS = textwrap.dedent(
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

    ## Invariants Touched

    - INV-1: preserved, proven by AC-DMO-2.

    ## Validation Matrix

    | Stage | Make Target | Pass Criteria |
    |---|---|---|
    | Focused | `make regression` | AC-DMO-1..2 |
    """
)

GOOD_UPSTREAM = textwrap.dedent(
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

GOOD_SPECKIT = textwrap.dedent(
    """\
    # Feature Specification: Demo Capability

    **Feature Branch**: `001-demo-capability`
    **Created**: 2026-01-01
    **Status**: Draft

    ## User Scenarios & Testing

    ### User Story 1 - Attest every write (Priority: P1)

    A user's write is attested so it can be verified later.

    **Why this priority**: Core guarantee the feature exists for.

    **Acceptance Scenarios**:

    1. **Given** an attested writer, **When** a write occurs, **Then** an evidence id is recorded.

    ## Requirements *(mandatory)*

    ### Functional Requirements

    - **FR-001**: The system MUST attest every write.
    - **FR-002**: The system MUST record an evidence id for every attested write.

    ## Success Criteria *(mandatory)*

    - **SC-001**: 95% of writes are attested within 1 second.
    """
)


def findings_for(repo: Path, body: str, dialect: str = "auto") -> list[rules.Finding]:
    path = write_spec(repo, "demo-change", "demo-capability", body)
    prof = detect.profile(repo)
    return rules.evaluate(parse_spec(path, dialect), prof)


def rule_ids(found: list[rules.Finding]) -> set[str]:
    return {f.rule for f in found}


def tree_findings_for(repo: Path, bodies: list[tuple[str, str, str]], dialect: str = "auto") -> list[rules.Finding]:
    """bodies: (change, capability, body) tuples, each written as its own spec."""
    specs = [parse_spec(write_spec(repo, change, capability, body), dialect) for change, capability, body in bodies]
    return rules.evaluate_tree(specs, detect.profile(repo))


