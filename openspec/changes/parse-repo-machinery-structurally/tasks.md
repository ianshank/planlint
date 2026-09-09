# Milestones

## Milestone 1 — Structural machinery parsers  [DONE]

- Add `openspec_graph/machinery.py` (stdlib-only): `parse_makefile(text)` — a
  structural tokenizer recognizing multi-target rules (`a b c: prereq`),
  `.PHONY` members, and double-colon rules, while ignoring recipe (tab-prefixed)
  lines and variable assignments (`:=`/`=`/`?=`/`+=`); and
  `parse_pyproject_fail_under(text)` — a section-aware walker that reads
  `fail_under` only from `[tool.coverage.report]`.
- `detect.py` constructs `ThresholdSource` and `make_targets` from
  `machinery.py` instead of the line regexes.

- **Gate:** `make test` green on the new `test_machinery.py`; stdlib-only guard
  stays green.

## Milestone 2 — G004 scoping + G003 drift semantics  [DONE]

- `parse.py:parse_spec` builds `make_refs` from execution contexts only
  (`_Verified by:_` lines + Validation Matrix Make Target column), not the whole
  spec body. `MAKE_REF` / `parse._MAKE_REF` remain as compatibility exports.
- `rules_generic._hard_coded_threshold` fires only on drift (literal differs from
  detected floor, or any literal when no floor is detected).
- README + rule-table wording for G003 updated to drift detection.

- **Gate:** `make pre-pr` green; self-validate clean; byte-identical baseline
  preserved or legitimately regenerated with a recorded diff.
