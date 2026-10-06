# Tasks: widen-indeterminate-unchecked-citations

## Milestone 0 — Design

- This package: `proposal.md`, `specs/indeterminate-status/spec.md`,
  `tasks.md`. Records why the predicate is an unwaived G010 finding and never
  the dialect card (DEC-IND-001), why a reasoned waiver clears it
  (DEC-IND-002), why waived-ness becomes a `Finding` field rather than a
  prefix test (DEC-IND-004), and why the rule id is a pinned module constant
  rather than a parameter (DEC-IND-005).
- Re-confirm before implementing: `openspec_graph/rules.py` is still the only
  module constructing `Finding(...)` (three sites: `evaluate`, and the G006
  and G009 blocks of `evaluate_tree`); `openspec_graph/graph.py` still builds
  its own finding dict literal rather than calling `as_dict`; no file under
  `openspec/changes/*/specs/*/spec.md` uses an `IND` area code other than
  this one; `report.py` still has no intra-package import.
- Reproduce the three measured facts the proposal cites against the current
  tree before touching code: a Makefile-less target with one citing spec is
  `PASS` / exit 0 / `status=pass`; a reasoned G010 waiver is still INFO and
  still exit 1 at `--fail-on INFO`; a Makefile-less spec with no citation
  produces no G010.
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
  `test_the_findings_schema_version_is_still_one`. Confirm
  `test_existing_keys_keep_their_spelling` passes unedited — it pins the
  top-level envelope keys, which do not change (AC-IND-8).
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
  pass here would vouch for citations nobody verified, and naming the three
  ways out: declare the make targets the specs cite, waive G010 with a reason
  in the spec if the repository does not use Make, or stop citing make
  stages. Keep the function free of timestamps and lookups (R-IND-7).
- `openspec_graph/report.py`: leave `discovery_notes`, `parse_card`,
  `to_annotations` and `Envelope.raw_findings` untouched (C-IND-3, C-IND-5).
- `tests/test_report.py`: `test_an_unwaived_g010_makes_a_checked_run_indeterminate`
  (AC-IND-1), `test_a_blocking_finding_beside_g010_is_a_fail_not_indeterminate`
  (AC-IND-2), `test_a_waived_g010_leaves_a_checked_run_a_pass` asserting the
  finding is still counted (AC-IND-3),
  `test_a_card_with_no_machinery_does_not_relabel_a_g010_free_envelope`
  (AC-IND-4), `test_the_no_specs_cause_names_the_empty_tree` and
  `test_both_causes_resolve_to_no_specs` (AC-IND-5, DEC-IND-007),
  `test_indeterminate_cause_is_always_an_output_and_empty_when_not_indeterminate`
  (AC-IND-6), `test_step_summary_names_the_three_ways_out_of_unchecked_citations`
  (AC-IND-7), `test_an_envelope_without_the_waived_key_still_parses` and
  `test_a_non_boolean_waived_is_refused` plus a `"waived is a string"` entry
  in `MALFORMED` (AC-IND-9), `test_the_unchecked_citation_rule_is_the_registered_g010`
  importing `rules_generic` from the test side only (AC-IND-10), and
  `test_report_reads_no_waived_prefix` — an AST or text scan of `report.py`
  for the literal `[waived]` (R-IND-12).
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
  G010, INFO, prefixed `[waived] `, `waived: true` in the envelope
  (DEC-IND-009).
- `tests/fixtures/action/README.md`: two rows —
  `no-machinery/ | 0 | indeterminate | ...` naming the cause, and
  `no-machinery-waived/ | 0 | pass | ...` saying the waiver is the ledgered
  escape and the finding stays in the envelope. Rewrite the opening sentence
  so the table pins "one outcome of the action's status and, for
  `indeterminate`, its cause".
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
  three ways out and `continue-on-error`, then `exit 1`; `*)` prints the
  existing six lines verbatim. Keep `set +e -uo pipefail` (DEC-IND-008,
  R-GA-7).
- `tests/test_action_contract.py`: `EXPECTED_OUTPUTS` gains
  `"indeterminate-cause"`; `EXPECTED_INPUTS` is untouched (C-IND-4).
  `ACTION_CONTRACT` gains
  `("tests/fixtures/action/no-machinery", "indeterminate", 1,
  "could check none of them")` and
  `("tests/fixtures/action/no-machinery-waived", "pass", 0,
  "no findings at or above")`; confirm the new phrase appears in neither the
  `fail` nor the `error` message, and that `empty-tree`'s "gates nothing"
  does not appear in the new message (AC-IND-11, AC-IND-13).
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

- `README.md`: the "related honesty gap" paragraph stops saying the Action
  reports the gap "rather than relabelling the run `indeterminate`" and that
  "widening that status is a policy change"; it now says an unwaived G010
  makes the run `indeterminate`, a reasoned waiver clears it, and a missing
  coverage floor does not enter into it. The `indeterminate` row of the
  four-status table names both causes and the `indeterminate-cause` output.
- `skills/planlint-spec-governance/SKILL.md`: the "four results" paragraph
  keeps four results and adds that the third has two causes, each reported
  in `indeterminate-cause`, and what to do about each.
- `docs/next-steps.md`: item 1's last sentence stops saying widening
  `indeterminate` "stays a 1.0 policy question" and points here; the
  "Widening `indeterminate`" bullet under item 5 is struck through with the
  package name; the deferral-table row records that the design pass happened,
  that the predicate is the finding and not the card, and that `DEC-GA-005`
  still holds.
- `docs/peer-review-2026-09.md`: the R8 row becomes **shipped** —
  `widen-indeterminate-unchecked-citations`, with a note that the predicate
  is the unwaived G010 finding rather than "no machinery found"; the
  limitations note narrows "G010 is effectively unwaivable" to "a waived G010
  still counts at `--fail-on INFO`; it no longer makes the Action
  `indeterminate`".
- `docs/differentiation-roadmap.md`: "Status as of 0.2.0" item 1's last
  sentence stops saying widening `indeterminate` "remains a 1.0 policy
  question".
- `CHANGELOG.md` (`Unreleased`): one entry stating plainly — no CLI exit code
  changes; the envelope's findings gain a `waived` boolean at schema version
  1; an Action consumer whose specs cite make stages against a target with no
  detected make targets will newly see `status=indeterminate`,
  `indeterminate-cause=unchecked-citations` and a red job; the two ways out
  are a reasoned `specgraph:allow G010` waiver in the spec or
  `continue-on-error` on the step; `DEC-GA-010`'s deferral is closed and
  `DEC-GA-005` stands. Narrow the existing "effectively unwaivable" sentence
  in the G010 entry rather than deleting it.
- Re-read `llms.txt`, `docs/hooks.md`, `docs/architecture/c4.md` and
  `skills/planlint-spec-governance/references/exit-codes.md` for any
  description of `status` or of the envelope's finding keys; none mentions
  `indeterminate` today, so the expected outcome is that none needs an edit —
  confirm rather than assume.
- **Gate:** `make pre-pr`
