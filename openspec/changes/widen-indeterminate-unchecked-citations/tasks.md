# Tasks: widen-indeterminate-unchecked-citations

## Milestone 0 — Design

- This package: `proposal.md`, `specs/indeterminate-status/spec.md`,
  `tasks.md`. Records why the predicate is an unwaived G010 finding and never
  the dialect card (DEC-IND-001), why a reasoned waiver clears it
  (DEC-IND-002), why waived-ness becomes a `Finding` field rather than a
  prefix test (DEC-IND-004), why the rule id is a pinned module constant
  rather than a parameter (DEC-IND-005), and why the harness-dialect cost is
  accepted and stated rather than engineered away (DEC-IND-013).
- Re-confirm before implementing: `openspec_graph/rules.py` is still the only
  module constructing `Finding(...)` (three sites: `evaluate`, and the G006
  and G009 blocks of `evaluate_tree`); `openspec_graph/graph.py` still builds
  its own finding dict literal rather than calling `as_dict`; no file under
  `openspec/changes/*/specs/*/spec.md` uses an `IND` area code other than
  this one; `report.py` still has no intra-package import; H001 still
  requires a `make` stage on every harness criterion
  (`parse_model.Criterion.has_stage`, `rules_harness.py`), G010 still has no
  `GENERIC_STAGES` exemption, and `scaffold.pick_stage()` still returns
  `"test"` on an empty `make_targets`.
- Reproduce the measured facts the proposal cites against the current tree
  before touching code: a Makefile-less target with one citing spec is
  `PASS` / exit 0 / `status=pass` / `discovery-warnings=2`; a reasoned G010
  waiver is still INFO and still exit 1 at `--fail-on INFO`; a Makefile-less
  spec with no citation produces no G010; a harness spec whose citations are
  removed or replaced by a `tox` command is `ERROR H001`, `status=fail`.
- **Gate:** `make validate`

## Milestone 1 — Waived-ness in the envelope

- `openspec_graph/rule_types.py`: `Finding` gains `waived: bool = False`
  after `subject`; `as_dict()` emits `"waived": self.waived` after
  `"subject"`. Extend the comment above `FINDINGS_SCHEMA_VERSION` to name
  `waived` as the first additive key that exercised the "additive keys do not
  bump it" rule (R-IND-9, R-IND-10).
- `openspec_graph/rules.py`: `evaluate()` passes `waived=suppressed`;
  `evaluate_tree()` passes `waived=waived_invariant` in the G006 block and
  `waived=waived_adr` in the G009 block. Nothing else in either function
  changes — the severity downgrade and the `[waived] ` prefix stay exactly as
  they are (R-IND-9, C-IND-5).
- `tests/test_findings_envelope.py`: `test_a_waived_finding_carries_the_waived_flag`
  (a reasoned waiver of an ERROR rule yields `waived=True`, severity INFO, the
  prefix still present), `test_an_unwaived_finding_reports_waived_false`,
  `test_evaluate_tree_marks_a_waived_g006_and_g009_as_waived`,
  `test_finding_as_dict_emits_waived_as_a_boolean` (the value is `bool`, not a
  string, in both the rooted and the rootless rendering), and
  `test_the_findings_schema_version_is_still_one`. Together these are
  AC-IND-8's evidence; confirm `test_existing_keys_keep_their_spelling`
  passes unedited — it pins the top-level envelope keys, which do not change.
- `tests/test_decomposition.py`: run `test_output_byte_identical` before any
  edit to `_EXPECTED_HASHES`. `graph` and `rules` must be unchanged; if
  `validate` moved, the `_build_repo` fixture envelope carried a finding — add
  a comment line recording which finding and re-pin once. If it did not move,
  add nothing (DEC-IND-011, C-IND-6, AC-IND-15).
- `tests/test_sarif.py`: `test_sarif_carries_no_waived_property` — a waived
  finding's `as_dict()` through `to_sarif` yields a result whose `properties`
  carry only `subject`, and the SARIF byte-identity tests in
  `tests/test_report.py` pass unedited (C-IND-5, AC-IND-16).
- **Gate:** `make test`

## Milestone 2 — `report.py`: the predicate, the cause, the surfaces

- `openspec_graph/report.py`: module constants `UNCHECKED_CITATION_RULE =
  "G010"`, `CAUSE_NO_SPECS = "no-specs"`, `CAUSE_UNCHECKED_CITATIONS =
  "unchecked-citations"`, `CAUSES: tuple[str, ...]`, each added to `__all__`,
  with a comment beside the rule id saying why it is a literal here and which
  test pins it (DEC-IND-005, R-IND-13).
- `openspec_graph/report.py`: rewrite the module docstring's second paragraph
  (`report.py:6-8`), which says the module "never decides policy; `--fail-on`
  has already been applied by the run that wrote the envelope, and `blocking`
  records the result". After this change the module holds exactly two pieces
  of status policy — nothing checked, and nothing checkable — both derived
  from the envelope and neither from `--fail-on`; say that, and point at
  `status_of` and `indeterminate_cause`.
- `openspec_graph/report.py`: `FindingRecord` gains `waived: bool = False`;
  `_parse_finding` reads `raw.get("waived", False)`, returns it when it is a
  `bool`, and raises `EnvelopeError(f"{where}: 'waived' must be a boolean,
  got ...")` otherwise. `_REQUIRED_FINDING_KEYS` is unchanged — the key is
  optional on read (R-IND-11).
- `openspec_graph/report.py`: new `indeterminate_cause(envelope) -> str |
  None` — `None` when `blocking > 0`; `CAUSE_NO_SPECS` when
  `specs_checked == 0`; `CAUSE_UNCHECKED_CITATIONS` when any finding has
  `rule == UNCHECKED_CITATION_RULE and not waived`; else `None`. `status_of`
  becomes `STATUS_FAIL` on blocking, `STATUS_INDETERMINATE` when the cause is
  not `None`, `STATUS_PASS` otherwise, so the two are one predicate. Rewrite
  `status_of`'s docstring, which currently describes `indeterminate` as
  "there was nothing to check" (R-IND-1, R-IND-5, DEC-IND-007).
- `openspec_graph/report.py`: `to_outputs` adds
  `"indeterminate-cause": indeterminate_cause(envelope) or ""` immediately
  after `"status"`, in the unconditional block. The card block is untouched
  (R-IND-6, DEC-IND-006).
- `openspec_graph/report.py`: `to_step_summary` branches on the cause — the
  existing "No spec was checked ..." paragraph for `no-specs`; for
  `unchecked-citations`, a paragraph stating that the specs cite make stages
  and none could be checked because no make targets were detected, that a
  pass here would vouch for citations nobody verified, and naming the ways
  out with their dialect qualification: declare the make targets the specs
  cite; waive G010 with a reason in each spec that cites one; or, for an
  upstream or SpecKit spec, stop citing make stages. Then the sentence
  R-IND-16 requires, in so many words: a harness-dialect repository that
  does not use Make needs that one-line reasoned waiver in each spec, because
  H001 requires every criterion to name a stage. Keep the function free of
  timestamps and lookups (R-IND-7, R-IND-16).
- `openspec_graph/report.py`: leave `discovery_notes`, `parse_card`,
  `to_annotations` and `Envelope.raw_findings` untouched (C-IND-3, C-IND-5).
- `tests/test_report.py`: `test_an_unwaived_g010_makes_a_checked_run_indeterminate`
  (AC-IND-1), `test_a_blocking_finding_beside_g010_is_a_fail_not_indeterminate`
  (AC-IND-2), `test_a_waived_g010_leaves_a_checked_run_a_pass` asserting the
  finding is still counted (AC-IND-3),
  `test_a_card_with_no_machinery_does_not_relabel_a_g010_free_envelope`
  (AC-IND-4), `test_the_no_specs_cause_names_the_empty_tree` asserting the
  cause and the retained "No spec was checked" paragraph, and
  `test_both_causes_resolve_to_no_specs` (AC-IND-5, DEC-IND-007),
  `test_indeterminate_cause_is_always_an_output_and_empty_when_not_indeterminate`
  asserting the key, the empty value, single-line-ness, `status` within
  `STATUSES`, and that `make-targets` is still absent without a card
  (AC-IND-6), `test_step_summary_names_the_ways_out_of_unchecked_citations`
  asserting the three exits, the dialect qualification and the harness
  sentence (AC-IND-7), `test_an_envelope_without_the_waived_key_still_parses`
  and `test_a_non_boolean_waived_is_refused` plus a `"waived is a string"`
  entry in `MALFORMED` (AC-IND-9),
  `test_the_unchecked_citation_rule_is_the_registered_g010` importing
  `rules_generic` from the test side only (AC-IND-10).
- `tests/test_report.py`: `test_report_reads_no_waived_prefix` — parse
  `report.py` with `ast`, collect every `ast.Constant` whose value is a
  `str`, **excluding docstrings** (the first statement of the module body
  and of every `FunctionDef`/`AsyncFunctionDef`/`ClassDef` body when it is a
  bare string expression), and assert none contains `[waived]`. Comments are
  not in the AST, so the comment beside `UNCHECKED_CITATION_RULE` and any
  docstring prose about the prefix are permitted; a comparison against the
  prefix in code is not (R-IND-12, DEC-IND-004).
- `tests/test_report.py`: `_finding()` keeps omitting `waived`, so the
  existing malformed-envelope matrix doubles as the tolerant-parse evidence;
  confirm every existing test in the file passes unedited.
- **Gate:** `make test`

## Milestone 3 — Fixtures, the action, the contract tests, the hosted matrix

- `tests/fixtures/action/no-machinery/`: `pyproject.toml` with
  `[project] name = "demo"` and no `[tool.coverage.report]` table; no
  Makefile; `openspec/changes/add-thing/specs/thing/spec.md` copied from
  `passing/` so the only difference from `passing/` is the missing machinery.
  Verify with the real CLI before labelling: exit 0, exactly one finding,
  rule G010, severity INFO, no `[waived] ` prefix (DEC-IND-010).
- `tests/fixtures/action/no-machinery-waived/`: identical, plus
  `<!-- specgraph:allow G010 this target does not use Make; the stage is run
  by tox -->` at the top of the spec. Verify: exit 0, exactly one finding,
  G010, INFO, prefixed `[waived] `, `waived: true` in the envelope. This is
  the worked example of the exit a harness-dialect repository takes
  (DEC-IND-009, DEC-IND-013).
- `tests/fixtures/action/README.md`: two rows —
  `no-machinery/ | 0 | indeterminate | ...` naming the cause, and
  `no-machinery-waived/ | 0 | pass | ...` saying the waiver is the ledgered
  escape, that the finding stays in the envelope, and that this is the shape
  a harness-dialect repository without a Makefile adopts per spec. Rewrite
  the opening sentence so the table pins "one outcome of the action's status
  and, for `indeterminate`, its cause".
- `tests/test_report.py`: `FIXTURE_CONTRACT` gains
  `("no-machinery", 0, report.STATUS_INDETERMINATE, True)` and
  `("no-machinery-waived", 0, report.STATUS_PASS, True)`;
  `test_each_fixture_produces_the_status_its_label_promises` then covers
  both. Add `test_the_no_machinery_fixtures_project_their_cause` asserting
  `indeterminate-cause=unchecked-citations` for the first and an empty value
  for the second through `report --format github-outputs` (AC-IND-11).
- `.github/actions/planlint/action.yml`: `outputs:` gains
  `indeterminate-cause` (`value: ${{ steps.project.outputs.indeterminate-cause }}`,
  description naming both values and that it is empty otherwise); the
  `status` description says `indeterminate` means "nothing was checked, or
  the specs cite make stages none of which could be checked — see
  `indeterminate-cause`"; the `specs-checked` description drops "Zero is what
  makes a run indeterminate" in favour of "zero is one of the two causes of
  `indeterminate`" (R-IND-8).
- `.github/actions/planlint/action.yml`: the gate step gains
  `CAUSE: ${{ steps.project.outputs.indeterminate-cause }}` and its
  `indeterminate)` branch becomes a nested `case "${CAUSE:-}"`:
  `unchecked-citations)` prints a `::error title=planlint::` line saying the
  specs cite make stages and this run could check none of them, then the
  ways out with their dialect qualification (declare the targets; a reasoned
  `specgraph:allow G010` in each citing spec; for upstream/SpecKit specs,
  stop citing stages), then the sentence R-IND-16 requires — a
  harness-dialect repository without a Makefile needs that waiver in each
  spec, since H001 requires every criterion to name a stage — then
  `continue-on-error` as the workflow-side escape, then `exit 1`; `*)` prints
  the existing six lines verbatim. Keep `set +e -uo pipefail` (DEC-IND-008,
  R-IND-16, R-GA-7).
- `tests/test_action_contract.py`: `EXPECTED_OUTPUTS` gains
  `"indeterminate-cause"`; `EXPECTED_INPUTS` is untouched (C-IND-4).
  `ACTION_CONTRACT` gains
  `("tests/fixtures/action/no-machinery", "indeterminate", 1,
  "could check none of them")` and
  `("tests/fixtures/action/no-machinery-waived", "pass", 0,
  "no findings at or above")`; confirm the new phrase appears in neither the
  `fail` nor the `error` message, that `empty-tree`'s "gates nothing" does
  not appear in the new message, and add
  `test_the_unchecked_citations_gate_names_the_per_spec_waiver` asserting the
  harness sentence reaches the gate log (AC-IND-11, AC-IND-13).
- `.github/workflows/ci.yml`: two `include:` entries in the `action-contract`
  matrix — `fixture: no-machinery`, `target: tests/fixtures/action/no-machinery`,
  `outcome: failure`, `status: indeterminate`, `exit_code: "0"`; and
  `fixture: no-machinery-waived`, `target: tests/fixtures/action/no-machinery-waived`,
  `outcome: success`, `status: pass`, `exit_code: "0"`. Run
  `test_every_action_fixture_has_a_contract_leg` first and let it name the
  missing legs (AC-IND-12). No new job, so `docs/hooks.md`'s CI table does
  not change.
- `tests/test_graft_rules.py`: leave
  `test_g010_and_g011_waivers_keep_the_finding_visible` and
  `tests/test_e2e_corpus.py::test_a_waived_g010_still_fails_a_fail_on_info_run`
  unedited — they are the evidence for C-IND-1 and must keep passing as
  written (AC-IND-14).
- **Gate:** `make test`

## Milestone 4 — Record what changed, what it costs, and what it closes

Every planning document already names this package as *drafted* or
*planned* (the 2026-10 deep dive wrote those lines when it drafted the
package). The work here is the transition to *shipped*, against the text as
it stands, plus the surfaces that still describe the old status.

- `README.md:208-213`: the "related honesty gap" paragraph still says the
  Action reports the gap "through `discovery-warnings` and a warning
  annotation rather than relabelling the run `indeterminate`" and that
  "widening that status is a policy change". Rewrite: an unwaived G010 now
  makes the run `indeterminate` with cause `unchecked-citations`; a reasoned
  G010 waiver in the spec clears it; a missing coverage floor does not enter
  into it (G003 fires normally); and a harness-dialect repository that does
  not use Make needs that one-line waiver in each spec, because H001 requires
  every criterion to name a stage.
- `README.md:433`: the `indeterminate` row of the four-status table names
  both causes and the `indeterminate-cause` output.
- `skills/planlint-spec-governance/SKILL.md:184-189`: the "four results"
  paragraph keeps four results and adds that the third has two causes, each
  reported in `indeterminate-cause`, and what to do about each — including
  the per-spec waiver for a harness-dialect repository without a Makefile.
- `docs/next-steps.md:27-29`: "`widen-indeterminate-unchecked-citations` is
  the drafted package" → shipped, with the predicate in one clause.
  `docs/next-steps.md:156-160`: the "Widening `indeterminate`" bullet under
  item 5 — "plans `indeterminate` on an unwaived G010 instead, as ..." →
  struck through as shipped. `docs/next-steps.md:229`: the deferral-table
  row's "**Planned since:**" → "**Shipped:**", keeping the sentence that the
  status keys on an unwaived G010 and never on missing machinery alone.
- `docs/next-steps.md`: a new deferral-table row in the repo's style —
  **Deferred:** the scaffold emitting a reasoned G010 waiver (or no stage) on
  a Makefile-less target. **Reopen when:** the first harness-dialect adopter
  who does not use Make hits it; `planlint new` on such a target scaffolds a
  citation of `test` (`DEC-UMC-008`), so its output is `indeterminate` until
  the author adds the waiver. It changes `new`'s output and belongs in its
  own package (DEC-IND-013).
- `docs/peer-review-2026-09.md:349`: the R8 row's "**planned** —
  `widen-indeterminate-unchecked-citations`, drafted from
  `docs/peer-review-2026-10.md` D3 ..." → "**shipped** — ...", keeping the
  "keyed on an unwaived G010, never on missing machinery alone" clause.
  `docs/peer-review-2026-09.md:369-371`: narrow "G010 is effectively
  unwaivable" to "a waived G010 still counts at `--fail-on INFO`; it no
  longer makes the Action `indeterminate`".
- `docs/peer-review-2026-10.md:383` and `:386`: the R8 and N5 rows of the
  rewritten remainder — "drafted" → "shipped". D3's second paragraph already
  states the harness cost and the scaffold follow-up; leave it.
- `docs/differentiation-roadmap.md:602-605`: "`widen-indeterminate-unchecked-citations`
  is the drafted package" → shipped.
- `CHANGELOG.md` (`Unreleased`): one entry stating plainly — no CLI exit code
  changes; the envelope's findings gain a `waived` boolean at schema version
  1, defaulting to `false` on read so older envelopes still project; an
  Action consumer whose specs cite make stages against a target with no
  detected make targets will newly see `status=indeterminate`,
  `indeterminate-cause=unchecked-citations` and a red job; the ways out are a
  reasoned `specgraph:allow G010` waiver in the spec or `continue-on-error`
  on the step; in so many words, a harness-dialect repository without a
  Makefile needs that waiver in each spec that cites a stage, because H001
  requires every criterion to name one, and `planlint new`'s own output on a
  Makefile-less target is `indeterminate` until one is added; `DEC-GA-010`'s
  deferral is closed and `DEC-GA-005` stands. Narrow the existing
  "effectively unwaivable" sentence (`CHANGELOG.md:29-32`) to the CLI's
  `--fail-on INFO` rather than deleting it (R-IND-16).
- Re-read `llms.txt`, `docs/hooks.md`, `docs/architecture/c4.md` and
  `skills/planlint-spec-governance/references/exit-codes.md` for any
  description of `status` or of the envelope's finding keys; none mentions
  `indeterminate` today, so the expected outcome is that none needs an edit —
  confirm rather than assume.
- **Gate:** `make pre-pr`

## Milestone 5 — Re-point the stage-only criteria at the tests that now exist

- `specs/indeterminate-status/spec.md`: AC-IND-2, AC-IND-5, AC-IND-6 and
  AC-IND-8 cite the stage only, because at drafting time every existing test
  that could have been cited passes today and cannot fail on the new claim
  (`test_blocking_findings_are_a_fail` never sees a G010;
  `test_a_tree_with_nothing_to_check_is_indeterminate_not_pass` and
  `test_step_summary_names_the_indeterminate_case` never check a cause;
  `test_discovery_outputs_are_omitted_without_a_card` never sees
  `indeterminate-cause`; `test_existing_keys_keep_their_spelling` pins the
  envelope's keys, not the finding's). Once Milestones 1-3 have landed, add
  the `pytest -k` selector to each: AC-IND-2 →
  `test_a_blocking_finding_beside_g010_is_a_fail_not_indeterminate`;
  AC-IND-5 → `test_the_no_specs_cause_names_the_empty_tree` and
  `test_both_causes_resolve_to_no_specs`; AC-IND-6 →
  `test_indeterminate_cause_is_always_an_output_and_empty_when_not_indeterminate`;
  AC-IND-8 → `test_a_waived_finding_carries_the_waived_flag`,
  `test_evaluate_tree_marks_a_waived_g006_and_g009_as_waived` and
  `test_finding_as_dict_emits_waived_as_a_boolean`. Do the same for
  AC-IND-1, 3, 7, 9 and 11 with the tests Milestones 2 and 3 name, keeping
  the `· stage:` suffix.
- `specs/indeterminate-status/spec.md`: tick each `- [ ]` only after the
  cited test has been run and seen to pass; `tests/test_spec_test_citations.py`
  fails the suite on a selector that resolves to nothing, so run it before
  committing the re-pointed spec. The spec, not the proposal, is what must
  match what shipped.
- **Gate:** `make test`
