# Milestones

## Milestone 1 — Share the heading vocabulary between parser and rule

- `openspec_graph/parse_semantics.py`: add `SPECKIT_REQUIREMENTS_HEADING =
  "Requirements"` and `SPECKIT_FUNCTIONAL_REQUIREMENTS_HEADING = "Functional
  Requirements"` beside the existing `SPECKIT_SUCCESS_CRITERIA_HEADING`
  (lines 51-54), carrying the same "so the two can't independently drift"
  comment that constant already has.
- `openspec_graph/parse_semantics.py`: add
  `speckit_requirements_heading(text) -> tuple[str, int] | None`. It scans
  `SECTION` and `SUBSECTION` matches, normalizes each title with the same
  `_TRAILING_ANNOTATION` strip `speckit_section_span` uses (extract or reuse
  it — do not write a second annotation stripper), and returns the normalized
  title plus its 1-based line for the first heading equal to either constant.
  Equality after normalization, never a prefix or substring test (R-SER-3).
- `openspec_graph/parse_speckit.py`: replace the two bare string literals at
  lines 35-36 (`"Requirements"`, `"Functional Requirements"`) with the new
  constants. No other change — the level-2/level-3 scoping R-SK-30/AC-SK-49
  established stays exactly as it is (R-SER-12).
- `tests/test_parse_speckit.py`: add
  `test_parse_speckit_output_is_unchanged_by_the_heading_constants` (the parse
  of every existing speckit fixture is identical before and after) and
  `test_parse_speckit_and_s005_share_one_heading_vocabulary` (no second copy of
  either heading literal exists outside `parse_semantics.py`).
- `tests/test_parse_semantics.py` (or whichever module covers
  `speckit_section_span` today): add
  `test_speckit_requirements_heading_matches_either_name_at_either_level` and
  `test_speckit_requirements_heading_rejects_a_non_functional_requirements_title`.

- **Gate:** `make test`

## Milestone 2 — S005

- `openspec_graph/rules_speckit.py`: add
  `_requirements_section_yields_nothing(spec, _p)`. Return early when
  `spec.requirements` is non-empty; otherwise call
  `speckit_requirements_heading(strip_waiver_comments(spec.raw))` and, on a
  match, yield one `CheckHit` carrying the heading's line. The `StackProfile`
  parameter stays unused (`_p`), matching every other rule in the module.
- The message names the section that was found, states that no `FR-` bullet was
  extracted from it, and names the canonical form so the author can compare —
  one message for all three firing shapes (DEC-SER-004).
- `openspec_graph/rules_speckit.py`: append
  `Rule("S005", WARN, ("speckit",), <summary>, _requirements_section_yields_nothing)`
  after S004 in `SPECKIT_RULES`. Do not reorder the existing entries. Update the
  module docstring from `S001-S004` to `S001-S005`.
- `tests/test_rules_speckit.py` — one fixture and one assertion per firing
  shape (R-SER-11):
  - `test_s005_fires_when_the_functional_requirements_heading_is_at_level_two`
  - `test_s005_fires_when_the_requirements_section_has_no_functional_subheading`
  - `test_s005_fires_on_a_prose_only_requirements_section`
  - `test_s005_fires_when_the_section_holds_only_non_fr_bullets`
- `tests/test_rules_speckit.py` — one per non-firing shape:
  - `test_s005_is_silent_when_no_requirements_shaped_heading_exists` (the
    user-story-only draft; the false positive item 4b deferred over)
  - `test_s005_is_silent_on_the_canonical_good_speckit_fixture`
  - `test_s005_does_not_match_a_non_functional_requirements_heading`
  - `test_s005_ignores_a_requirements_heading_inside_a_waiver_comment`
  - `test_s005_never_evaluates_against_a_harness_or_upstream_spec`
- `tests/test_rules_speckit.py` — shape and compatibility:
  - `test_s005_reports_the_heading_line`
  - `test_s005_fires_once_per_spec_not_once_per_heading`
  - `test_s005_is_warn_and_does_not_change_the_fail_on_error_exit_code`
  - `test_s005_and_g001_both_report_when_the_spec_is_also_criterion_less`
- Confirm steps 4a and 4b of `.claude/skills/planlint-add-rule/SKILL.md` do
  **not** apply, and record why in the check's docstring: the rule reads
  `len(spec.requirements)` and a heading title, never criterion or requirement
  prose, so there is no phrasing corpus to add under `tests/fixtures/phrasing/`
  and no floor to measure with `make matcher-accuracy` (DEC-SER-009); and it
  reads no `StackProfile` field, so there is no `tests/corpus/targets/` shape
  to add (DEC-SER-010).

- **Gate:** `make test`

## Milestone 3 — Registry, generated artifacts, and doc sync

Every location `.claude/skills/planlint-add-rule/SKILL.md` names, in its order.
Do not hand-pick from memory — run the two test modules at the end of this
milestone and let them name the rest. The counts below are the current values;
each goes from 26 to 27, and two of these files state it more than once.

- Regenerate the baseline: `planlint rules --json > tests/baseline_rules.json`.
  Never hand-edit it.
- Regenerate the distributable skill's rule catalog: `make skill-catalog`. The
  file under `skills/planlint-spec-governance/references/` is generated;
  `tests/test_skill_contract.py` fails on a stale one.
- `README.md`: add the S005 row to the rules table, in id order after S004.
  The row must read `| S005 | WARN | speckit | ... |` — `tests/test_rule_registry_docs.py`
  parses the id and severity columns and compares them against `rules.RULES`.
- `docs/architecture/c4.md`: three separate edits, and fixing one does not fix
  the others — the count and the family ranges are checked by different tests.
  - line 57: "26 deterministic rules" in the `rules.py` module-map table row.
  - line 133: the Mermaid node `rules_speckit.py<br/>S001-S004`.
  - line 140: the prose caption "`rules_speckit.py` covers S001-S004".
- `docs/agents-skills-harness.md` line 82: "The 26 rules".
- `docs/next-steps.md`: "the 26 rules" appears **twice** (lines 63 and 297) and
  the test asserts every occurrence. Also strike through item 4b / R6 and
  record what shipped and what did not — the `Success Criteria` half stays
  deliberately open (C-SER-2), and striking the item whole would overstate the
  fix.
- `docs/differentiation-roadmap.md`: "26 rules total" appears **twice**
  (lines 308 and 456).
- `openspec_graph/rules.py`: update the module docstring line for
  `rules_speckit` from `S001-S004` to `S001-S005`.
- `tests/test_rule_registry_docs.py`: no change expected — `_FAMILIES` already
  carries `("S", "rules_speckit")` and the README-table regex already accepts
  `S\d{3}`, both added by `add-speckit-dialect`. Confirm rather than assume.
- `tests/test_decomposition.py`: re-pin `_EXPECTED_HASHES["rules"]` and extend
  the comment above it with this change as the next re-pin reason.
  `["validate"]` and `["graph"]` must stay unchanged — the canonical fixture
  has no `specs/` directory, so no speckit rule fires against it. Confirm
  empirically; do not re-pin either on faith.
- Run `pytest tests/test_rule_registry_docs.py tests/test_skill_contract.py`
  and fix every location they report before moving on.

- **Gate:** `make test`

## Milestone 4 — Self-validation and the compatibility guarantee

- Run `make validate` against this repository. Every change package here is
  harness-dialect and carries a level-2 `Requirements` heading with zero `FR-`
  bullets, so a mis-scoped `dialects` tuple turns this gate red across the whole
  tree — the cheapest available proof of C-SER-5, and why AC-SER-8 cites
  `make validate` rather than a unit test alone.
- Re-run the `c60f894` reproduction end to end: the wrong-level file now reports
  one S005 warning and still exits 0 under the default `--fail-on ERROR`; the
  canonical file still reports nothing.
- Record the reproduction's before/after counts in the spec's Problem
  Statement, the way `fix-u003-mandatory-given` recorded its external-corpus
  numbers — a change justified by a measurement is closed by the same
  measurement.
- Replace each acceptance criterion's stage-only `_Verified by:_` citation with
  the `pytest -k <selector>` form naming the test that now exists.
  `tests/test_spec_test_citations.py` fails on a selector that resolves to
  nothing, so this step happens after the tests land, never before.
- Leave `**Status:** DRAFT` in the spec header. Promotion to APPROVED is a human
  decision after review, not an implementation step.

- **Gate:** `make pre-pr`
