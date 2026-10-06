# Spec: Indeterminate Status

> **Change:** `widen-indeterminate-unchecked-citations`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

The Action's `status` says `pass` for a run whose specs cite `make` stages
against a target where none of those citations could be checked. The CLI now
reports that run honestly — G010 records, per spec, that the cited-stage check
could not run — but `report.status_of` reads only `blocking` and
`specs_checked`, so the one surface a consuming workflow branches on relays
the run as green. The two existing escalations are both wrong-shaped:
`fail-on: INFO` fails every justified waiver in the tree alongside the
unchecked citations, and a waiver of G010 changes nothing but a message
prefix. The policy question `DEC-GA-010` deferred is now small, because the
honest signal exists and the only decision left is whether the Action
escalates it. `docs/peer-review-2026-10.md` D3 ("What should `indeterminate`
mean?") makes that decision and names its cost; this spec is the package that
row files.

**Evidence:** `openspec_graph/report.py::status_of` (`report.py:339-357`) is
three lines: `fail` on `blocking > 0`, `indeterminate` on
`specs_checked == 0`, `pass` otherwise. Reproduced against this tree
(`docs/peer-review-2026-10.md` N5): a target with no Makefile and no coverage
floor whose one spec cites a make stage prints `INFO  G010 ... 1 distinct
`make` stage(s) not checked: no make targets were detected in the target
repo, so G004 could not run`, then `1 spec(s) checked · 0 error · 2 warn ·
1 info` and `PASS`, exit 0; `report --format github-outputs` over that
envelope with the target's card prints `status=pass`, `infos=1`,
`make-targets=0`, `discovery-warnings=2`. With
`<!-- specgraph:allow G010 reason -->` in the spec the finding becomes
`INFO  G010 ... [waived] ...`, still INFO, still exit 1 at `--fail-on INFO` —
pinned by `tests/test_e2e_corpus.py::test_a_waived_g010_still_fails_a_fail_on_info_run`
and recorded in `CHANGELOG.md` as "G010 is effectively unwaivable".
`rule_types.Finding.as_dict` (`rule_types.py:93-100`) emits six keys and
none of them says whether a finding was waived; the `[waived] ` prefix that
`rules.evaluate` (`rules.py:119`) and `rules.evaluate_tree` (`rules.py:151`,
`rules.py:164`) prepend is the only trace. The discriminating case holds: a
Makefile-less target whose specs cite no make stage produces no G010
(`tests/test_graft_rules.py::test_g010_is_silent_when_the_spec_cites_no_make_target`;
`peer-review-2026-10.md` Appendix H), which is why `report.discovery_notes()`
(`report.py:379-408`, card-shaped, fires with or without a citation) is the
wrong input. A missing coverage floor is irrelevant:
`rules_generic._hard_coded_threshold` (`rules_generic.py:45`) has no empty
guard and falls back to `locator = "the governance policy"`.

The cost, measured rather than assumed: `parse_model.Criterion.has_stage`
(`parse_model.py:55-56`) is a `MAKE_REF` match and H001 (ERROR,
`rules_harness.py:21-25`) fires on every harness criterion that names no
`make` stage; harness is the fallback dialect (`parse.py:133`); G010
(`rules_generic.py:97-113`) has no `GENERIC_STAGES` exemption; a waiver is
scoped to its spec file (`rules.py:103`); and `scaffold.pick_stage()`
(`scaffold.py:61`) returns `"test"` on a Makefile-less target. A harness spec
with its citations removed or replaced by a `tox` command is `ERROR H001 ×2`,
`status=fail`; with a citation of `test` alone it is `INFO G010`, which this
change makes `indeterminate`. So a harness-dialect repository that does not
use Make cannot take the "stop citing make stages" exit; its exit is one
reasoned G010 waiver per spec, or `continue-on-error`.

---

## Requirements

### The predicate

- R-IND-1: `report.status_of` MUST return `indeterminate` when the envelope's
  `blocking` is zero and at least one finding has `rule` equal to the
  unchecked-citation rule (G010) and `waived` equal to `False`. `fail` on
  `blocking > 0` MUST take precedence over every other status, and
  `specs_checked == 0` MUST continue to yield `indeterminate` exactly as it
  does today.
- R-IND-2: The predicate MUST be keyed on findings in the envelope and MUST
  NOT read the dialect card. An envelope carrying no such finding MUST keep
  its current status whatever the card says about make targets or the
  coverage floor, and `status_of`'s signature MUST NOT gain a card parameter.
- R-IND-3: A G010 finding whose `waived` is `True` MUST NOT contribute to
  `indeterminate`. The finding itself MUST remain in the envelope, counted in
  `findings` and `infos`, with its `[waived] ` prefix.
- R-IND-4: `status` MUST remain exactly one of the four values R-GA-5
  defines. This change MUST NOT add a fifth status.

### The cause

- R-IND-5: `report` MUST expose `indeterminate_cause(envelope) -> str | None`
  returning `None` when the status is not `indeterminate`, `no-specs` when
  `specs_checked == 0`, and `unchecked-citations` otherwise. `status_of` and
  `indeterminate_cause` MUST be one predicate: `status_of` returns
  `indeterminate` if and only if `indeterminate_cause` returns a value.
  The cause strings MUST be module constants listed in a `CAUSES` tuple.
- R-IND-6: `to_outputs` MUST emit `indeterminate-cause` for every envelope:
  the cause string when the status is `indeterminate`, the empty string
  otherwise. It MUST NOT be omitted, because it is always measured. The
  discovery outputs MUST keep their omitted-without-a-card behaviour and
  their values.
- R-IND-7: `to_step_summary` MUST print a cause-specific paragraph when the
  status is `indeterminate`: the existing "No spec was checked ..." text for
  `no-specs`, and for `unchecked-citations` a paragraph that states the specs
  cite make stages none of which could be checked and names the ways out —
  declare the make targets the specs cite; waive G010 with a reason in each
  spec that cites one; or, for an upstream or SpecKit spec only, stop citing
  make stages. The paragraph MUST NOT present the third exit as available to
  a harness-dialect spec, whose criteria H001 requires to name a stage. The
  two paragraphs MUST be distinct.
- R-IND-8: The Action MUST declare an `indeterminate-cause` output projected
  from the `project` step, and its gate step's `indeterminate` branch MUST
  print a message distinct per cause. The `unchecked-citations` message MUST
  name the ways out of R-IND-7 with the same dialect qualification, and
  `continue-on-error`. An empty or unrecognised cause MUST fall to the
  existing `no-specs` message, so a CLI installed through the `version:`
  input from a release that emits no cause produces the pre-change message.
  Every property R-GA-6 states MUST still hold.

### Waived-ness in the envelope

- R-IND-9: `rule_types.Finding` MUST gain `waived: bool = False`.
  `rules.evaluate` and `rules.evaluate_tree` MUST set it `True` exactly at
  the sites where they already downgrade a finding to INFO and prefix its
  message with `[waived] `, and nowhere else. Severity, message and prefix
  MUST be unchanged.
- R-IND-10: `Finding.as_dict` MUST emit `"waived"` as a JSON boolean. The six
  existing finding keys and the six top-level envelope keys MUST keep their
  spellings and meanings, and `FINDINGS_SCHEMA_VERSION` MUST stay `1`.
- R-IND-11: `report.parse_envelope` MUST accept a finding that lacks `waived`
  and read it as `False`, so an envelope written by an older build still
  projects. It MUST refuse, with `EnvelopeError`, a `waived` that is present
  and not a boolean.
- R-IND-12: `report.py` MUST NOT derive waived-ness from the `[waived] `
  message prefix or from any other message text. That property MUST be
  checked by an AST scan of the module's string constants in code —
  docstrings excluded, comments not being in the AST — so that prose about
  the prefix in a comment or docstring is permitted and a comparison against
  it is not.

### Where the rule id lives

- R-IND-13: The unchecked-citation rule id MUST live in `report.py` as a
  module constant `UNCHECKED_CITATION_RULE`, not as an import. A test MUST
  pin it to the `rules_generic.GENERIC_RULES` entry whose check is
  `_unchecked_make_citations` and whose severity is INFO. `report.py` MUST
  keep its zero-intra-package-import posture, checked mechanically.

### The stated cost

- R-IND-16: The `CHANGELOG.md` entry, the gate step's `unchecked-citations`
  message and the step summary's `unchecked-citations` paragraph MUST each
  say, in so many words, that a harness-dialect repository without a Makefile
  needs a reasoned G010 waiver in each spec that cites a stage (or
  `continue-on-error` on the step), and the changelog entry MUST add that
  `planlint new`'s own output on a Makefile-less target is `indeterminate`
  until one is added. None of the three MAY describe the third exit of
  R-IND-7 without its dialect qualification.

### Fixtures and verification

- R-IND-14: Two labelled fixtures MUST be added under `tests/fixtures/action/`:
  `no-machinery/` — one change package whose spec cites a make stage, no
  Makefile, a `pyproject.toml` declaring no coverage floor — labelled
  `indeterminate`, `validate` exit 0, cause `unchecked-citations`; and
  `no-machinery-waived/` — the same with a reasoned `specgraph:allow G010`
  waiver in the spec — labelled `pass`, exit 0. Each MUST have a row in
  `tests/fixtures/action/README.md`, in `tests/test_report.py`'s
  `FIXTURE_CONTRACT`, in `tests/test_action_contract.py`'s `ACTION_CONTRACT`,
  and a leg in `.github/workflows/ci.yml`'s `action-contract` matrix.
- R-IND-15: Unit tests in `tests/test_report.py` MUST cover, on constructed
  envelopes: an unwaived G010 is `indeterminate`; a waived G010 is `pass`; a
  G010 beside a blocking finding is `fail`; `specs_checked == 0` has cause
  `no-specs`; a finding without the `waived` key parses; and an envelope with
  no G010 finding stays `pass` with and without a card reporting zero make
  targets.

### Constraints

- C-IND-1: This change MUST NOT alter any `validate` exit code or `blocking`
  count for any input. INFO never blocks; `rules.py`'s severity contract
  stands.
- C-IND-2: This change MUST NOT alter G010's, G011's, G004's or H001's id,
  severity, message, dialect set or finding shape; MUST NOT add a
  `GENERIC_STAGES` exemption to G010; MUST NOT touch `RULES`; and MUST leave
  `tests/baseline_rules.json` and the generated rule catalog unchanged.
- C-IND-3: `report.discovery_notes()` and the Action's `discovery-warnings`
  output MUST keep their current derivation and values (`DEC-UMC-007`).
- C-IND-4: The Action MUST gain no input. `EXPECTED_INPUTS` in
  `tests/test_action_contract.py` MUST be unchanged (`DEC-GA-005`).
- C-IND-5: `Finding.render` and the `[waived] ` prefix MUST be unchanged, and
  the SARIF projection MUST be byte-identical before and after for the same
  tree — `waived` MUST NOT appear as a SARIF property.
- C-IND-6: `_EXPECTED_HASHES["graph"]` and `_EXPECTED_HASHES["rules"]` MUST
  NOT move. `_EXPECTED_HASHES["validate"]` MUST move only if the hashed
  fixture envelope carries at least one finding; the implementation MUST
  verify this by running the test rather than assume either outcome.
- C-IND-7: `README.md`, `SKILL.md`, `docs/next-steps.md`,
  `docs/peer-review-2026-09.md`, `docs/peer-review-2026-10.md`,
  `docs/differentiation-roadmap.md`, the Action's `outputs:` block and
  `CHANGELOG.md` MUST move in the same change — each against its current
  text, where the package is already named as drafted or planned — and
  `make docs-check` MUST stay green.
- C-IND-8: The presence or absence of a coverage floor MUST have no bearing
  on `status` or on the cause.
- C-IND-9: The predicate MUST NOT be narrowed by dialect, by stage name or by
  any property of the target to reduce the harness-dialect cost; the cost is
  paid by the per-spec waiver, and `scaffold.pick_stage()` MUST NOT change in
  this package.

---

## Decisions

- **DEC-IND-001:** the predicate is an **unwaived G010 finding**, never the
  dialect card. The question the status answers is "did this run check what
  the specs claim", and G010 is the one signal keyed on that: it fires only
  when a spec carries a `make` citation and `profile.make_targets` is empty.
  The card-shaped predicate the 2026-09 review's D3 rejected — "no Makefile
  and no coverage floor" — and the deferral table's reopen trigger of the
  same shape, which `docs/peer-review-2026-10.md` D3 rejected again, relabel
  a tox, npm or `just` repository whose specs never mention Make and which
  has nothing unchecked; `discovery_notes()` has the same shape and fires on
  a citation-free target, which the revision of `DEC-UMC-007` recorded as the
  reason it must not drive status. R6/S005 taught the same lesson from the
  other direction: the shipped predicate keys on data loss (FR bullets
  present, none extracted), not on a heading.
  On `DEC-GA-010`, stated plainly: G010 is unchanged by this package, so this
  is **not** "policy in the rules". The defensible reading is the one
  `DEC-GA-004`/`DEC-GA-005` already established — `specs_checked == 0 →
  indeterminate` is projection-side status policy derived from one fact in
  the envelope, and this is the same shape with one more fact from the same
  envelope. `DEC-GA-010`'s deferral is closed on those terms, and
  `DEC-GA-005` is left intact: there is still no input to make a false green
  available; the waiver and `continue-on-error` remain the only escapes.
  Two prior decisions are engaged by name rather than passed over.
  `DEC-UMC-004` argued that a tox repository writing a generic stage "is not
  lying" and that G011's narrowing "costs nothing in the tox case"; both are
  statements about rule severity, both stay true (G010 is INFO, the CLI exits
  0, `rule_types.py:39-47` still documents the exemption), and neither is
  about what the Action's `status` says about a run that checked no citation
  — which is all that moves here. `DEC-UMC-008` kept `pick_stage()` emitting
  `test` on a Makefile-less target; this package does not reopen it
  (C-IND-9) and records the consequence in DEC-IND-013.
- **DEC-IND-002:** a **reasoned waiver clears it**. The waiver is the
  ledgered escape this project built: it lives in the spec, `planlint
  waivers` lists it, G007 refuses it without a reason, and it stays visible
  as an INFO finding. Giving it an effect on `status` is what gives G010's
  waiver the effect `CHANGELOG.md` says it lacks — at the Action layer, which
  `docs/peer-review-2026-10.md` N5 identifies as the one surface that can
  distinguish "unchecked" from "unchecked, and the author said why". At the
  CLI the limitation is narrowed, not removed: a waived G010 still counts at
  `--fail-on INFO` (C-IND-1), because dropping waived INFO findings is an
  engine change for every rule and is still not done here.
- **DEC-IND-003:** **not `fail-on: INFO`, not a fifth status.** `fail-on`
  cannot separate "unchecked citation" from "justified waiver" because
  `rules.evaluate` makes both INFO; a consumer who reaches for it to catch
  the first fails on every instance of the second. A fifth status such as
  `unchecked` would be a new value in R-GA-5's closed set, which a consuming
  workflow's `case` has never seen; `indeterminate` already means "this run
  proves nothing about the repository", which is exactly what an unchecked
  run proves. The distinction consumers need is carried by an additive
  output, which R-GA-4 permits inside a major version.
- **DEC-IND-004:** waived-ness becomes a **`Finding` field and an envelope
  key**, and the rejected alternative is `status_of` testing
  `message.startswith("[waived] ")`. The prefix is a display contract — it is
  what `Finding.render` shows and what several suites assert — and a status
  policy keyed on it would flip gate verdicts the day someone rewords it, or
  the day a rule's own message begins with that string. The field is the
  fact; the prefix is its rendering; `report.py` reads the fact (R-IND-12),
  and the guard that proves it scans string constants in code only, because
  this very decision mentions the prefix in prose and a comment beside the
  constant is expected to. The key is additive, so `FINDINGS_SCHEMA_VERSION`
  stays `1` by the rule `rule_types.py:35-36` already states ("additive keys
  do not bump it"), and `test_an_unknown_finding_key_is_tolerated` already
  pins that a richer envelope is accepted. `parse_envelope` defaults an
  absent `waived` to `False` so an artifact produced by an older build still
  projects, and refuses a present non-boolean for the same reason
  `_require_int` refuses a `bool` as a count: a producer bug is worth
  reporting, not silently reading.
- **DEC-IND-005:** the rule id is a **module constant pinned by a test**,
  not a parameter of `status_of`. `report.py` passes `schema_version` in
  because that number's *value* is owned by `rule_types` and changes; a rule
  id is a stable public identifier that already appears in the README table,
  the baseline JSON and every SARIF rule descriptor, and `report.py` already
  names `G004` and `G003` as literals in `discovery_notes`. The new thing is
  only that this literal is load-bearing, so a test pins
  `report.UNCHECKED_CITATION_RULE` to the registered G010 — its check is
  `_unchecked_make_citations`, its severity INFO — and fails if either side
  moves. The parameter alternative was rejected because `status_of` is called
  from `to_outputs` and `to_step_summary` as well as directly, so the id would
  have to thread through three signatures and every existing test call for a
  value that has one correct answer. `test_report_has_no_intra_package_imports`
  and `test_module_is_importable_without_the_rest_of_the_package` both keep
  passing.
- **DEC-IND-006:** `indeterminate-cause` is **always present and empty when
  not indeterminate**. `to_outputs` has two conventions: a key is *omitted*
  when the fact behind it was not measured (the discovery outputs without a
  card), and *empty* when it was measured and found to be none
  (`coverage-floor` with a card and no floor). The cause is derived from the
  envelope alone, so it is always measured; the empty string is the honest
  "none" and lets a workflow test it without first testing for presence. It
  sits in the unconditional block beside `status`, not in the card block.
- **DEC-IND-007:** `no-specs` **wins when both causes hold**. In a real
  envelope they cannot: G010 is a per-spec finding, so `specs_checked == 0`
  implies no G010. A constructed envelope can carry both, and
  `indeterminate_cause` must be total over whatever `parse_envelope` admits,
  so the order is stated rather than left to implementation: nothing checked
  is the stronger statement and matches `status_of`'s existing clause order.
- **DEC-IND-008:** the gate's **default branch is the `no-specs` text**. The
  Action installs the CLI from its own checkout by default, so cause and gate
  move together; with `version:` set to a release that predates this change,
  `report --format github-outputs` emits no cause and `status` is
  `indeterminate` only for the empty-tree case. Falling through to the
  existing message makes that configuration produce the pre-change output
  byte for byte, and the new message appears only when the CLI says
  `unchecked-citations`. `ACTION_CONTRACT`'s phrase for `empty-tree`
  ("gates nothing") is kept, and the new row's phrase must be a string that
  appears in neither of the other two red messages.
- **DEC-IND-009:** **two fixtures, not one.** `no-machinery/` pins the new
  verdict; `no-machinery-waived/` is the only thing that proves the escape
  works end to end — through `validate`, the envelope, `report` and the gate
  — and it pins that a waived G010 is still *in* the envelope (`findings=1`,
  `infos=1`, message prefixed `[waived] `): the waiver clears the status, not
  the record. A unit test on a constructed envelope cannot show that the
  engine actually sets the field, and a contract fixture nobody can turn
  green has not demonstrated the policy's own exit. Both fixtures are
  harness-dialect, so the waived one is also the worked example of the exit
  DEC-IND-013 says a harness repository must take.
- **DEC-IND-010:** `no-machinery/` deliberately has **no coverage floor
  either**. Its card then yields two discovery notes while its status is
  driven by one finding, which demonstrates F2 in the fixture itself: the
  floor's absence contributes nothing to the verdict (C-IND-8), and
  `discovery-warnings` keeps counting card-shaped notes unchanged (C-IND-3).
  `no-machinery-waived/` has the same card and lands on `pass`, which is the
  proof that the card is not the input.
- **DEC-IND-011:** the golden hash is **verified, not assumed**.
  `_EXPECTED_HASHES["graph"]` cannot move: `graph.py:181` and `graph.py:219`
  build their own finding dict literal and never call `as_dict`.
  `_EXPECTED_HASHES["rules"]` cannot move: the registry is untouched
  (C-IND-2). `_EXPECTED_HASHES["validate"]` is the hash of `validate --json`
  over the repository `_build_repo` assembles from `tests/fixtures/Makefile`,
  `tests/fixtures/pyproject.toml`, `good_harness.md` and `good_upstream.md`;
  it moves if and only if that envelope's `findings` list is non-empty. Both
  fixture specs cite the one stage that Makefile declares, and the comment
  block above the hashes records that `validate` stayed byte-identical across
  three rule additions, so the list is expected to be empty — but the
  expectation is confirmed by running `test_output_byte_identical`, and if
  it is wrong the hash is re-pinned once with the reason added to that
  comment block, as `DEC-FE-008` requires.
- **DEC-IND-012:** **no CLI change.** The CLI's `PASS` on this shape stays,
  because the CLI already has its honest signal (G010, R4) and its own
  escalation (`--fail-on INFO`), and because "INFO never blocks" is the
  severity contract every adopter's pre-commit hook relies on. The Action is
  the surface where a green check is *evidence* to a reviewer, which is why
  D3.3 located the policy question there and why this change stops there.
- **DEC-IND-013:** the **harness-dialect cost is accepted and stated**, not
  engineered away. H001 (ERROR) requires every harness criterion to name a
  `make` stage, harness is the fallback dialect, and G010 has no
  `GENERIC_STAGES` exemption, so a harness-dialect repository that does not
  use Make is forced to write a citation, always gets G010, and under this
  change is `indeterminate` on every spec until each spec file carries its
  own reasoned waiver — one line per spec, each a ledgered statement visible
  in `planlint waivers` that the citation is shorthand — or the workflow
  uses `continue-on-error`. `planlint new` on such a target scaffolds a
  citation of `test` (`DEC-UMC-008`), so the scaffold's own output is
  `indeterminate` until the author adds that line. The alternatives were
  rejected by name: exempting `GENERIC_STAGES` from G010 reopens the vacuous
  pass G010 was written to report; narrowing the predicate by dialect makes
  the status depend on which parser ran rather than on what went unchecked;
  changing the scaffold changes `new`'s output and is a different package.
  A green check over citations nobody could check is the thing this review
  series exists to remove, so the cost is paid in the open: the changelog,
  the gate message and the step summary each say it (R-IND-16), and the
  scaffold question is filed in `docs/next-steps.md`'s deferral table with
  its reopen trigger — the first harness-dialect adopter who does not use
  Make.

---

## Acceptance Criteria

- [ ] **AC-IND-1:** A constructed envelope with `blocking == 0`,
  `specs_checked >= 1` and one unwaived G010 finding has status
  `indeterminate` and cause `unchecked-citations`. (R-IND-1, R-IND-5,
  R-IND-15, DEC-IND-001)
  _Verified by:_ stage: `make test`

- [ ] **AC-IND-2 (non-success):** A blocking finding beside a G010 finding is
  `fail`, never `indeterminate`, and the cause is `None` — blocking wins.
  (R-IND-1, R-IND-15)
  _Verified by:_ stage: `make test`

- [ ] **AC-IND-3:** The same envelope with the G010 finding's `waived` set to
  `True` is `pass` with cause `None`, and the finding is still present in
  `findings`, counted in `infos`, with its `[waived] ` prefix. (R-IND-3,
  R-IND-15, DEC-IND-002)
  _Verified by:_ stage: `make test`

- [ ] **AC-IND-4 (non-success):** The tox shape is never relabelled: a
  checked envelope with no G010 finding is `pass` both without a card and
  with a card reporting zero make targets and no coverage floor, and a
  Makefile-less spec that cites no make stage produces no G010 at all.
  (R-IND-2, R-IND-15, C-IND-8, DEC-IND-001, DEC-IND-010)
  _Verified by:_ `pytest -k "test_a_checked_clean_tree_is_a_pass or test_g010_is_silent_when_the_spec_cites_no_make_target"` · stage: `make test`

- [ ] **AC-IND-5:** An envelope with `specs_checked == 0` is still
  `indeterminate`, its cause is `no-specs`, and the step summary still
  carries the "No spec was checked" paragraph. (R-IND-1, R-IND-5, R-IND-7,
  R-IND-15, DEC-IND-007)
  _Verified by:_ stage: `make test`

- [ ] **AC-IND-6:** `to_outputs` carries `indeterminate-cause` for every
  envelope — the cause when indeterminate, the empty string otherwise — as a
  single-line value; `status` is one of the four known values; and the
  discovery outputs are still omitted entirely without a card. (R-IND-4,
  R-IND-6, DEC-IND-006)
  _Verified by:_ stage: `make test`

- [ ] **AC-IND-7:** For the `unchecked-citations` cause the step summary
  names the ways out — declaring the make targets, waiving G010 with a
  reason in each citing spec, or (for upstream and SpecKit specs only) not
  citing make stages — says in so many words that a harness-dialect
  repository without a Makefile needs that waiver in each spec, and is not
  the `no-specs` paragraph. (R-IND-7, R-IND-16, DEC-IND-013)
  _Verified by:_ stage: `make test`

- [ ] **AC-IND-8:** `rules.evaluate` sets `waived=True` on a suppressed
  finding and `False` otherwise; `rules.evaluate_tree` does the same for a
  waived G006 and G009; `Finding.as_dict` emits `waived` as a boolean; the
  six top-level envelope keys keep their spelling; `FINDINGS_SCHEMA_VERSION`
  is still `1`. (R-IND-9, R-IND-10, DEC-IND-004)
  _Verified by:_ stage: `make test`

- [ ] **AC-IND-9 (non-success):** An envelope whose findings carry no
  `waived` key parses with `waived == False` and projects normally; one whose
  `waived` is a string or an integer is refused with `EnvelopeError`, and the
  `report` verb exits 2 with an empty stdout on it, never 1. No string
  constant in `report.py`'s code — docstrings excluded — contains
  `[waived]`. (R-IND-11, R-IND-12, R-IND-15)
  _Verified by:_ stage: `make test`

- [ ] **AC-IND-10:** `report.py` imports no module of this package, and
  `report.UNCHECKED_CITATION_RULE` names the `GENERIC_RULES` entry whose
  check is `_unchecked_make_citations` and whose severity is INFO.
  (R-IND-13, DEC-IND-005)
  _Verified by:_ `pytest -k test_report_has_no_intra_package_imports` · stage: `make test`

- [ ] **AC-IND-11:** Through the real CLI, `no-machinery/` exits 0 with one
  finding (G010, INFO, unwaived) and projects `status=indeterminate`,
  `indeterminate-cause=unchecked-citations`; `no-machinery-waived/` exits 0
  with one finding (G010, INFO, `[waived] `) and projects `status=pass`,
  `indeterminate-cause=`. Through the action's extracted steps, the first
  fails the gate with a message containing a phrase absent from both other
  red messages and naming the per-spec waiver a harness repository needs,
  and the second passes it. (R-IND-8, R-IND-14, R-IND-16, DEC-IND-008,
  DEC-IND-009)
  _Verified by:_ stage: `make test`

- [ ] **AC-IND-12:** Every fixture directory under `tests/fixtures/action/`
  has a matching `action-contract` leg, the two new ones included.
  (R-IND-14)
  _Verified by:_ `pytest -k test_every_action_fixture_has_a_contract_leg` · stage: `make test`

- [ ] **AC-IND-13:** The action declares `indeterminate-cause` among its
  outputs and declares exactly the inputs it declares today — no
  `allow-indeterminate`, no new input of any name. (R-IND-8, C-IND-4)
  _Verified by:_ `pytest -k test_the_action_declares_exactly_the_v1_inputs` · stage: `make test`

- [ ] **AC-IND-14 (non-success):** No CLI exit code moves: a Makefile-less
  target whose spec cites a make stage still exits 0 at `--fail-on ERROR`
  and `--fail-on WARN` and 1 at `--fail-on INFO`, and a reasoned G010 waiver
  still exits 1 at `--fail-on INFO`. (C-IND-1, DEC-IND-002, DEC-IND-012)
  _Verified by:_ `pytest -k "test_g010_reaches_the_cli_without_changing_a_fail_on_error_verdict or test_a_waived_g010_still_fails_a_fail_on_info_run"` · stage: `make test`

- [ ] **AC-IND-15 (non-success):** The rule registry matches the committed
  baseline — G010 in particular still has no `GENERIC_STAGES` exemption and
  `pick_stage()` is unchanged — `_EXPECTED_HASHES["graph"]` and `["rules"]`
  are unchanged, and `["validate"]` is either unchanged or re-pinned once
  with its reason recorded, decided by running the test. (C-IND-2, C-IND-6,
  C-IND-9, DEC-IND-011, DEC-IND-013)
  _Verified by:_ `pytest -k "test_rule_set_matches_baseline or test_output_byte_identical"` · stage: `make test`

- [ ] **AC-IND-16:** `report --format sarif` is still byte-identical to
  `validate --format sarif` on a tree with findings and on a clean one, no
  SARIF result carries a `waived` property, and `Finding.render` output is
  unchanged. (C-IND-5)
  _Verified by:_ `pytest -k "test_report_sarif_is_byte_identical_to_validate_sarif or test_report_sarif_matches_on_a_clean_tree_too"` · stage: `make test`

- [ ] **AC-IND-17:** `discovery_notes` still emits one note per missing kind
  of machinery, and `no-machinery/`'s card yields two of them while its
  envelope carries exactly one G010 — the card-shaped count and the
  finding-shaped verdict agree without one deriving from the other.
  (C-IND-3, DEC-IND-010)
  _Verified by:_ `pytest -k "test_a_target_with_no_make_targets_is_flagged or test_a_target_with_no_coverage_floor_is_flagged"` · stage: `make test`

- [ ] **AC-IND-18:** Every planning-record mention of this package reads
  *shipped* rather than *drafted* or *planned*; the README's honesty-gap
  paragraph and status table, SKILL.md's four-results paragraph, the
  Action's `outputs:` block and `CHANGELOG.md` describe the widened status
  and its two causes; the changelog says in so many words that a
  harness-dialect repository without a Makefile needs a reasoned G010 waiver
  in each spec and that the scaffold's output on a Makefile-less target is
  `indeterminate` until one is added; the deferral table carries the
  scaffold item with its reopen trigger; and the docs gate passes.
  (C-IND-7, R-IND-16, DEC-IND-013)
  _Verified by:_ `pytest -k test_docs_check_passes` · stage: `make docs-check`

- [ ] **AC-IND-19:** The hosted `action-contract` job is green on the pull
  request that lands this change, with seven legs — the five existing
  fixtures plus `no-machinery` (outcome `failure`, status `indeterminate`,
  exit code `0`) and `no-machinery-waived` (outcome `success`, status
  `pass`, exit code `0`) — each reporting its labelled result under a
  read-only token with no secret. (R-IND-14)
  _Verified by:_ the `action-contract` job's own assertion steps on the pull request · stage: `make ci` must also be green on the same commit

- [ ] **AC-IND-20:** The full gate is green with the widened status — lint,
  type-check, security, docs, threshold discipline and the whole suite.
  (C-IND-7)
  _Verified by:_ `make pre-pr` · stage: `make pre-pr`

---

## Non-Success Criteria (what this change rejects)

- An implementation that keys `status` on the dialect card — `make-targets`,
  `coverage-floor` or `discovery_notes()` — is rejected: it relabels the tox
  shape (DEC-IND-001, AC-IND-4).
- An implementation that narrows the predicate by dialect or stage name, adds
  a `GENERIC_STAGES` exemption to G010, or changes `pick_stage()` to soften
  the harness-dialect cost is rejected: the cost is paid by the per-spec
  waiver and stated in the open (C-IND-9, DEC-IND-013, AC-IND-15).
- An implementation whose changelog entry, gate message or step summary
  offers "stop citing make stages" to a harness-dialect repository, or omits
  the per-spec waiver sentence, is rejected (R-IND-16, AC-IND-7, AC-IND-11,
  AC-IND-18).
- An implementation that tests `message.startswith("[waived] ")` in
  `report.py` is rejected: it couples a gate verdict to a display string
  (DEC-IND-004, AC-IND-9).
- An implementation that adds an Action input, a fifth status value, or a
  `FINDINGS_SCHEMA_VERSION` bump is rejected (DEC-IND-003, C-IND-4,
  AC-IND-6, AC-IND-13).
- An implementation that changes any `validate` exit code, any rule's
  severity or message, or `discovery-warnings`' value is rejected (C-IND-1,
  C-IND-2, C-IND-3, AC-IND-14, AC-IND-15, AC-IND-17).
- An implementation that re-pins `_EXPECTED_HASHES["validate"]` without first
  observing it move, or that lands one fixture without the other, is rejected
  (DEC-IND-009, DEC-IND-011, AC-IND-11, AC-IND-15).

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-IND-1..17 |
| Self-check | `make validate` | this repo's own packages, this one included, stay clean at `--fail-on ERROR` |
| Docs | `make docs-check` | AC-IND-18 |
| Core | `make ci` | AC-IND-1..18, plus lint and this repo's own `planlint validate` |
| Hosted | `action-contract` job in `.github/workflows/ci.yml` | AC-IND-19 |
| Full | `make pre-pr` | AC-IND-20 — full regression, lint, typecheck, security, docs, threshold discipline |
