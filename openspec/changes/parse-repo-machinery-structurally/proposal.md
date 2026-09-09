# Change: Parse Repo Machinery Structurally (CP-3)

## Why

`planlint` holds specs to the target repo's real machinery, but that machinery is
currently parsed with line regexes that produce two classes of false result:
the coverage floor can be read from the wrong TOML section (any `fail_under`,
not only `[tool.coverage.report]`), and `make <word>` in prose trips G004 even
when it is not a stage citation. Both make the gate less precise than the wedge
("fails when a spec cites a gate this repo does not have") demands.

**Evidence:** `openspec_graph/detect.py` reads `fail_under` via a regex over the
whole `pyproject.toml` (`_FAIL_UNDER`), with no section awareness;
`openspec_graph/parse.py:parse_spec` builds `make_refs` with
`MAKE_REF.findall(text)` over the entire spec body, so "make a decision" in a
Problem Statement becomes a cited target.

## What Changes

- New `openspec_graph/machinery.py` (stdlib-only): structural parsers for
  Makefile targets (`parse_makefile`) and the coverage floor
  (`parse_pyproject_fail_under`), returning plain data; `detect.py` constructs
  `ThresholdSource` from them.
- G004 scoping: `make_refs` is extracted only from execution contexts
  (`_Verified by:_` lines and the Validation Matrix Make Target column), not
  from prose. `MAKE_REF` / `parse._MAKE_REF` remain as compatibility exports.
- G003 drift semantics: a threshold literal that matches the detected floor is
  not a finding; a literal that differs (or any literal when no floor is
  detected) is. Rule and README wording updated from "no hard-coded thresholds"
  to drift detection.

## Non-Goals

- No new rules. G003 and G004 keep their IDs and severities.
- No TOML dependency. `machinery.py` is stdlib-only (Python 3.10+; `tomllib` is
  3.11+ and the repo supports 3.10).
- No INFO-level "matching floor" note in this change (scope creep); a matching
  literal is a silent non-finding.
- No change to the waiver syntax, config file, or `[tool.specgraph]` section.

## Affected Capabilities

- `repo-machinery`
