# Tasks: report-unchecked-make-citations

## Milestone 0 — Design

- This package: `proposal.md`, `specs/unchecked-make-citations/spec.md`,
  `tasks.md`. Records why the two signals must be two **new rule ids** rather
  than new behaviour on G004 (DEC-UMC-001: `rule_types.Rule` carries one
  `severity` and `rules.evaluate()` reads it off the rule, never off the
  `CheckHit`), and why G004's guard clause and `GENERIC_STAGES` both survive
  untouched (DEC-UMC-004, DEC-UMC-006).
- Confirm before implementing that `openspec_graph/rules_generic.py` still ends
  at G009 and nothing else has claimed `G010`/`G011`.
- **Gate:** `make validate`

## Milestone 1 — G010: say when the cited-stage check could not run

- `openspec_graph/rules_generic.py`: new `_unchecked_make_citations(spec,
  profile)` — returns nothing unless `spec.make_refs` is non-empty **and**
  `profile.make_targets` is empty; otherwise yields exactly one message naming
  how many citations went unchecked and why (R-UMC-1, R-UMC-2, DEC-UMC-003).
  Register it as `Rule("G010", INFO, ("*",), ...)` in `GENERIC_RULES`, and add
  `INFO` to the module's `rule_types` import.
- `openspec_graph/rules_generic.py`: leave `_unknown_make_target` (G004)
  byte-identical. Add a one-line comment beside its `if not
  profile.make_targets: return` guard pointing at G010, so the early return
  reads as a delegation rather than as an omission (R-UMC-6).
- `tests/test_graft.py`: a fixture with no Makefile and a spec carrying a
  citation asserts exactly one G010 (AC-UMC-1); the same repo with a spec
  carrying no citation asserts no G010 (AC-UMC-2); a Makefile-less run asserts
  G010 present and G004 absent (AC-UMC-6).
- `tests/test_graft.py`: confirm
  `test_g004_stays_silent_when_the_target_repo_has_no_makefile_at_all` passes
  **unedited**. If it does not, the implementation changed G004's semantics and
  is wrong — do not adjust the test (AC-UMC-7, DEC-UMC-006).
- **Gate:** `make test`

## Milestone 2 — G011: check generic stages where Make is demonstrably in use

- `openspec_graph/rules_generic.py`: new `_unknown_generic_stage(spec,
  profile)` — returns nothing when `profile.make_targets` is empty; otherwise
  yields one message per citation naming a `GENERIC_STAGES` member absent from
  `profile.make_targets` (R-UMC-3, R-UMC-4, DEC-UMC-003). Register it as
  `Rule("G011", WARN, ("*",), ...)`.
- `openspec_graph/rule_types.py`: extend the comment above `GENERIC_STAGES`
  ("Make targets a spec may cite without them existing yet in the Makefile") to
  name G011 and state the condition under which the exemption stops applying
  (R-UMC-8, AC-UMC-14).
- `tests/test_graft.py`: a Makefile declaring one non-generic target plus a
  spec citing the stage `test` asserts one G011 and zero `ERROR` findings
  (AC-UMC-3); the same spec against a Makefile-less repo asserts G010 and no
  G011 (AC-UMC-4); a citation naming a target that is neither present nor
  generic asserts exactly one G004 and no G011 (AC-UMC-6).
- `tests/test_graft.py`: waiver coverage for both ids — a `specgraph:allow
  G010`/`specgraph:allow G011` comment with a reason downgrades to `INFO` with
  the `[waived]` prefix, and neither id sits in `rules._NON_WAIVABLE`
  (AC-UMC-12).
- `tests/test_report.py` (or the Action-contract test beside it): for a
  Makefile-less target whose specs carry citations, the `discovery-warnings`
  output keeps its existing value and the same envelope carries the G010
  finding (AC-UMC-13).
- **Gate:** `make test`

## Milestone 3 — Registry sync (the full `planlint-add-rule` checklist)

Two new ids mean every location `tests/test_rule_registry_docs.py` and
`tests/test_skill_contract.py` guard has to move together. Run those two test
files and fix what they report rather than editing from memory — the list is
longer than intuition suggests, and this repo added that guard after the same
drift recurred three times.

- `tests/baseline_rules.json`: regenerate with `planlint rules --json >
  tests/baseline_rules.json` (`test_rule_set_matches_baseline`,
  `test_rule_registry_baseline_is_unchanged`).
- `skills/planlint-spec-governance/references/rule-catalog.md`: regenerate with
  `make skill-catalog`. Generated artifact — never hand-edited
  (`test_rule_catalog_is_fresh`, `test_rule_catalog_lists_every_registered_rule`).
- `tests/test_rule_registry_docs.py`: widen
  `test_readme_rules_table_matches_rules_exactly`'s `(ERROR|WARN)` alternation
  to `(ERROR|WARN|INFO)`. **This sync point is not in
  `.claude/skills/planlint-add-rule/SKILL.md`.** G010 is the first
  INFO-severity entry in `RULES`, so the guard cannot see its README row today
  and fails with a "missing/extra" diff that names no cause (DEC-UMC-002).
- `README.md`: two rows in the rules table (`| G010 | INFO | any | ... |`,
  `| G011 | WARN | any | ... |`); add an `INFO` clause to the "ERROR blocks the
  gate; WARN degrades review quality" sentence above it, since the table now
  has a severity that sentence does not describe.
- `openspec_graph/rules.py`: module docstring — `rules_generic` covers
  `G001-G011` (`test_rules_py_docstring_family_ranges_match_rules`).
- `docs/architecture/c4.md`: the `rules.py` row's deterministic-rule count
  (26 → 28) **and** the module map's `rules_generic.py` range `G001-G009` →
  `G001-G011`, plus the caption sentence below it that restates every family's
  range (`test_total_rule_count_matches_every_prose_claim`,
  `test_c4_module_map_family_ranges_match_rules`).
- `docs/agents-skills-harness.md`: "The 26 rules" → 28.
- `docs/next-steps.md`: both "the 26 rules" claims → 28.
- `docs/differentiation-roadmap.md`: both "26 rules total" claims → 28.
- **Gate:** `make test`

## Milestone 4 — Record what changed and what it costs

- `openspec_graph/report.py`: rewrite `discovery_notes()`'s docstring. It
  currently records the CLI's silence as the correct behaviour for both rules;
  after this change only the coverage-floor half is still unreported by the
  rule engine. Leave the computed value and the Action's `discovery-warnings`
  output alone (DEC-UMC-007, C-UMC-5).
- `README.md`: the "no Makefile and no coverage floor is a related honesty gap"
  paragraph stops saying the Action is the only surface that reports it, and
  names G010/G011.
- `CHANGELOG.md` (`Unreleased`): state plainly that no `--fail-on ERROR` run
  changes verdict, and that a `--fail-on WARN` or `--fail-on INFO` run over a
  repository with no Makefile — or one citing a generic stage it does not have
  — will newly report findings. An adopter should read that here rather than
  discover it in CI (C-UMC-1).
- `docs/peer-review-2026-09.md`: mark R4 and R5 as landed by this package, and
  note that R2 (document `GENERIC_STAGES`) is absorbed by G011 rather than
  still outstanding.
- `docs/next-steps.md`: the item that defers "say when a rule could not run"
  now points at G010; the `indeterminate`-widening item (R8/D3.3) stays open
  and records that its prerequisite has landed.
- **Gate:** `make pre-pr`
