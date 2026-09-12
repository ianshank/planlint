# Milestones

## Milestone 1 — `CheckHit`, coercion, and `evaluate()` line copy

- `openspec_graph/rule_types.py`: add frozen `CheckHit(message: str, line:
  int = 0)`, type alias `CheckResult = str | CheckHit`, helper
  `as_check_hit(item: CheckResult) -> CheckHit` (bare `str` →
  `CheckHit(message=item, line=0)`; `CheckHit` returned unchanged). Change
  `Rule.check` to `Callable[[ParsedSpec, StackProfile],
  Iterable[CheckResult]]`. Add the new names to `__all__`.
- `openspec_graph/rules.py`: re-export `CheckHit`, `CheckResult`,
  `as_check_hit` on the facade `__all__` (R-DG-1). `evaluate()` coerces
  every yielded item through `as_check_hit`, copies `hit.line` onto
  `Finding` only when `>= 1`, stores `0` otherwise, never clamps to `1`.
  `evaluate_tree()` still omits `line=` for G006/G009.
- `openspec_graph/rules.py`: `logger = logging.getLogger("planlint.rules")`
  with no extra handler. DEBUG records the rule id and the attached line
  or `unset`; finding message bodies are not logged at INFO; default
  WARNING is silent.
- `tests/test_finding_line_hits.py` (new):
  `test_as_check_hit_coerces_a_string_to_line_zero`,
  `test_evaluate_copies_checkhit_line_onto_finding`,
  `test_evaluate_stores_zero_for_nonpositive_checkhit_line`,
  `test_evaluate_does_not_clamp_zero_to_one`,
  `test_evaluate_debug_log_names_rule_and_line_not_message`,
  `test_evaluate_is_silent_at_default_warning`.
- **Gate:** `make test`

## Milestone 2 — Parser line attribution

- `openspec_graph/parse_model.py`: `Requirement.line: int = 0` as the last
  field, after `body`.
- `openspec_graph/parse_semantics.py`: add `section_span(text, name) ->
  tuple[int, str]` (body start offset, body). `section_body` becomes
  `return section_span(...)[1]`. Missing section → `(0, "")`.
- `openspec_graph/parse_harness.py`: set `Requirement.line` via
  `line_of(full_text, span_origin + match.start())`. Replace
  `text.find(block[:60])` on criteria with the Acceptance Criteria span
  origin plus `match.start()`.
- `openspec_graph/parse_upstream.py`: set `Requirement.line` via
  `line_of(text, m.start())` (matches are already against the full text).
  Scenario `Criterion.line` is already `line_of(text, match.start())` —
  leave it.
- `openspec_graph/parse_speckit.py`: set `Requirement.line` from the
  nested Functional Requirements span origin plus `match.start()`. Set
  Success Criteria `Criterion.line` the same way (drop
  `text.find(m.group(0))`). Keep GWT at `story.start() + scen.start()`.
  Add `speckit_section_span` / `speckit_subsection_span` only if they are
  the cleanest way to recover those origins (`DEC-LH-013`).
- `tests/test_finding_line_hits.py`:
  `test_requirement_line_is_one_based_in_harness_upstream_and_speckit`,
  `test_harness_criterion_line_is_the_ac_bullet_not_a_duplicate_prefix`,
  `test_section_body_still_returns_only_the_span_text`.
- **Gate:** `make test`

## Milestone 3 — Migrate checks that hold a real locus

- `openspec_graph/rules_generic.py`: G007 yields `CheckHit` with
  `waiver.line`. Message string unchanged.
- `openspec_graph/rules_harness.py`: H001, H002, H004 yield `CheckHit`
  with `crit.line`. H003 looks up `Requirement.line` by ident from
  `spec.orphan_requirements` (property stays a tuple of idents).
- `openspec_graph/rules_upstream.py`: U003 uses `crit.line`; U002 and
  U004 use `req.line`.
- `openspec_graph/rules_speckit.py`: S001 uses
  `NEEDS_CLARIFICATION.finditer` + `line_of` on length-preserving
  waiver-stripped text; S002 both halves use the duplicate item's
  `.line`; S003 uses `req.line`; S004 uses `crit.line`.
- `openspec_graph/rules_witness.py`: W001 and W002 yield `CheckHit` with
  `crit.line`.
- Leave as bare `str` (honest `line=0`): G001, G002, G003, G004, G005,
  G008, G006, G009, H005, H006, U001, U005. Do not add a first-match
  search for G003–G005/G008.
- `tests/test_finding_line_hits.py`:
  `test_g007_finding_line_equals_waiver_line`,
  `test_h001_finding_line_is_the_criterion_line`,
  `test_u003_finding_line_is_the_scenario_line`,
  `test_s001_finding_line_is_the_clarification_marker`,
  `test_h003_finding_line_is_the_orphan_requirement_line`,
  `test_w001_finding_line_is_the_criterion_line`.
- **Gate:** `make test`

## Milestone 4 — Projection round-trip, comments, golden hashes

- `tests/test_finding_line_hits.py`:
  `test_migrated_error_round_trips_to_sarif_start_line` (a migrated ERROR
  with `line >= 1` serializes through `Finding.as_dict` into
  `sarif.to_sarif` `region.startLine`). Existing
  `tests/test_sarif.py::test_a_line_of_zero_emits_no_region` and
  `tests/test_report.py::test_a_line_of_zero_emits_no_line_property`
  remain; do not clamp. Do not add
  `test_failing_action_fixture_annotations_include_line`: the failing
  fixture's ERROR is G004 (unknown make target), which stays at line 0.
- `openspec_graph/sarif.py` / `openspec_graph/report.py`: update the
  comments that say no rule currently sets a line, so they describe the
  omit-when-`< 1` rule rather than a now-false "every finding is 0".
  Do not change the omit/clamp behaviour.
- `tests/test_decomposition.py`: confirm empirically whether
  `_EXPECTED_HASHES["validate"]` moves (only if the golden fixture's
  findings gain non-zero lines). Re-pin that hash only then, with a
  comment naming this change. `["graph"]` and `["rules"]` MUST NOT move.
- **Gate:** `make test`

## Milestone 5 — Action inputs `change` and `dialect`

- `.github/actions/planlint/action.yml`: add inputs `change` and
  `dialect`, `required: false`, default `""`. Scan-step env grows
  `INPUT_CHANGE` and `INPUT_DIALECT`. Build the `validate` argv as an
  array; append `--change` / `--dialect` only when non-empty. Do not
  pass `--dialect auto` when empty. Do not add `extra-args`. Do not pass
  `--require-witness`.
- `tests/test_action_contract.py`: add `change` and `dialect` to
  `EXPECTED_INPUTS` and to `ActionRun` defaults (`""`). Update
  `test_the_action_runs_validate_once_and_projects_the_rest` and
  `test_the_step_extractor_sees_the_whole_action` so they still assert
  a single `validate` run against the array form. Add
  `test_action_inputs_include_change_and_dialect`,
  `test_empty_change_and_dialect_inputs_omit_cli_flags`,
  `test_nonempty_change_input_passes_change_flag`,
  `test_nonempty_dialect_input_passes_dialect_flag`,
  `test_action_does_not_pass_require_witness`.
- Templates (`templates/spec-gate.yml` and the skill twin) stay
  byte-identical and need not start passing the new inputs.
- **Gate:** `make test`

## Milestone 6 — Docs and full gate

- `CHANGELOG.md`: record finding line hits and the two Action inputs
  without a version bump — under `[0.2.0]` while that tag is still
  unpushed (matching PR #25), or under `[Unreleased]` if the tag exists
  by then. State that `FINDINGS_SCHEMA_VERSION` stays `1` because `line`
  already existed (`DEC-FE-010` / `DEC-LH-004`), and that this
  supersedes `R-GA-3`'s closed input list in part.
- `docs/next-steps.md`: mark items 2 (finding line numbers) and 3
  (named Action inputs for `--change` / `--dialect`) as shipped by this
  change. Leave item 1 (vacuous-pass policy), plugins, CP-8, and
  Marketplace/`v1` deferred.
- Confirm `openspec_graph.__version__` is still `0.2.0` and
  `FINDINGS_SCHEMA_VERSION` is still `1`.
- **Gate:** `make pre-pr`
