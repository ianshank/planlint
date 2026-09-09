# Spec: Repo Machinery Parsing

> **Change:** `parse-repo-machinery-structurally`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

`planlint` holds specs to the target repo's real machinery, but that machinery is
parsed with line regexes that produce false results: the coverage floor can be
read from the wrong TOML section, and `make <word>` in prose trips G004 even when
it is not a stage citation.

**Evidence:** `openspec_graph/detect.py` reads `fail_under` via a regex over the
whole `pyproject.toml` with no section awareness; `parse.py:parse_spec` builds
`make_refs` with `MAKE_REF.findall(text)` over the entire spec body, so prose
like "make a decision" becomes a cited target.

---

## Requirements

- R-PM-1: The system MUST parse Makefile targets structurally — recognizing
  multi-target rules, `.PHONY` members, and double-colon rules, while ignoring
  recipe lines and variable assignments.
- R-PM-2: The system MUST read the coverage floor from the correct TOML section
  (`[tool.coverage.report]`), ignoring `fail_under` in any other section.
- R-PM-3: G003 MUST fire only on threshold drift — a literal that differs from
  the detected floor, or any literal when no floor is detected. A literal
  matching the detected floor is not a finding.
- R-PM-4: G004 MUST inspect make-target citations only in execution contexts
  (`_Verified by:_` lines, the Validation Matrix Make Target column, and
  backticked code spans in upstream-dialect Scenario steps), not in prose.
- C-PM-1: `machinery.py` MUST be stdlib-only (no third-party imports), so the
  import-boundary and stdlib-only guards stay green.
- C-PM-2: Coverage for the change MUST meet the floor declared in
  `pyproject.toml:[tool.coverage.report].fail_under`. No literal threshold may
  appear in this spec or its tests.

---

## Acceptance Criteria

- [ ] **AC-PM-1:** `parse_makefile` returns multi-target rule names, `.PHONY`
  members, and double-colon targets; it ignores recipe lines and variable
  assignments. (R-PM-1)
  _Verified by:_ `pytest -k test_parse_makefile` · stage: `make test`

- [ ] **AC-PM-2:** `parse_pyproject_fail_under` reads `fail_under` only from
  `[tool.coverage.report]` and ignores the same key in other sections. (R-PM-2)
  _Verified by:_ `pytest -k test_parse_pyproject_fail_under` · stage: `make test`

- [ ] **AC-PM-3 (non-success):** A threshold literal matching the detected floor
  does NOT fire G003; a literal that differs, or any literal when no floor is
  detected, DOES fire G003. (R-PM-3)
  _Verified by:_ `pytest -k test_g003` · stage: `make test`

- [ ] **AC-PM-4 (non-success):** `make nope` in prose (Problem Statement) does NOT
  fire G004; `make nope` on a verified-by line, in a Validation Matrix cell, or
  as a backticked code span in a Scenario step DOES fire G004. Bare prose in a
  Scenario (`we make a decision`) does NOT fire. (R-PM-4)
  _Verified by:_ `pytest -k test_g004` · stage: `make test`

- [ ] **AC-PM-5:** `machinery.py` imports only from the standard library
  (`sys.stdlib_module_names`), preserving the stdlib-only guard. (C-PM-1)
  _Verified by:_ `pytest -k test_new_modules_stdlib_only` · stage: `make test`

- [ ] **AC-PM-6:** Coverage for the change meets the floor declared in
  `pyproject.toml:[tool.coverage.report].fail_under`. No literal threshold is
  named in this spec or its tests. (C-PM-2)
  _Verified by:_ `make test` · stage: `make test`

## Invariants Touched

- INV-PM-1: detection is structural, not regex-fragile — preserved, proven by
  AC-PM-1 and AC-PM-2.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-PM-1..6 |
