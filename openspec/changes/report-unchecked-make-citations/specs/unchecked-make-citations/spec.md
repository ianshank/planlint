# Spec: Unchecked `make` Citations

> **Change:** `report-unchecked-make-citations`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

G004 ("cited make targets exist") stays silent in two situations and records
nothing about either, so `validate` reports the same `PASS` whether it checked
every citation or checked none of them.

First, `rules_generic._unknown_make_target` returns early when
`profile.make_targets` is empty. A target repository whose Makefile `detect`
did not find therefore passes G004 vacuously, and the CLI prints `PASS` with
zero findings even at `--fail-on INFO`. `report.discovery_notes()` computes
that same fact independently for the composite Action's `discovery-warnings`
output, so the information exists — it simply never reaches the surface that
pre-commit, `make validate` and every agent invocation read.

Second, the same function skips any citation naming a member of
`rule_types.GENERIC_STAGES`, which is the set of the five stage names a real
spec is most likely to cite. The exemption is defensible for a repository that
does not use Make at all, and indefensible for one that demonstrably does.

**Evidence:** reproduced at `c60f894` and tabulated in
`docs/peer-review-2026-09.md` F2/F3/D2/D3.2. Against a Makefile declaring one
target named `build`, a citation naming `regression` yields 1 G004 finding,
while citations naming `test`, `ci`, `lint`, `coverage` and `validate` each
yield 0. `scaffold.pick_stage()` returns `"test"` for an empty
`profile.make_targets`, so `planlint new` emits the exempt citation five times
into a repository where the rule is switched off anyway. The guard clause
itself is two lines in `openspec_graph/rules_generic.py`; the exemption is one
`set` literal in `openspec_graph/rule_types.py` and one `and` clause beside it.

---

## Requirements

- R-UMC-1: When a spec carries at least one `make` citation and
  `profile.make_targets` is empty, the rule engine MUST emit an `INFO` finding
  under a rule id of its own, stating that the cited-stage check could not be
  run because no Makefile was found in the target.
- R-UMC-2: That finding MUST NOT be emitted for a spec carrying no `make`
  citation. The rule reports a check that could not run, not the absence of a
  Makefile.
- R-UMC-3: When `profile.make_targets` is non-empty and a citation names a
  `GENERIC_STAGES` member that is absent from `profile.make_targets`, the rule
  engine MUST emit a `WARN` finding under a rule id of its own. It MUST NOT be
  `ERROR`.
- R-UMC-4: That `WARN` MUST NOT be emitted when `profile.make_targets` is
  empty. R-UMC-1's `INFO` covers that case, and a repository with no Makefile
  may not use Make at all.
- R-UMC-5: G004, the new `INFO` rule and the new `WARN` rule MUST partition the
  cases they cover: no single citation may produce a finding from more than one
  of the three in a single run.
- R-UMC-6: G004's behaviour MUST NOT change. Its empty-`make_targets` guard,
  its `GENERIC_STAGES` exemption, its id, severity, dialect set and message all
  stay exactly as they are.
- R-UMC-7: Both new rules MUST be suppressible through the existing
  `specgraph:allow` waiver mechanism, downgrading to `INFO` with a `[waived]`
  prefix in the usual way, and MUST NOT be added to `rules._NON_WAIVABLE`.
- R-UMC-8: `GENERIC_STAGES` MUST carry an in-source note naming the rule that
  now checks it. An exemption that appears in no rule description, no README
  row and no planning document is the documentation half of this defect.
- C-UMC-1: No repository that passes `validate --fail-on ERROR` before this
  change may fail after it. `--fail-on WARN` and `--fail-on INFO` runs MAY
  newly fail; that is the point of the change and MUST be stated in the
  changelog entry rather than discovered by an adopter.
- C-UMC-2: `tests/test_graft.py`'s existing
  `test_g004_stays_silent_when_the_target_repo_has_no_makefile_at_all` MUST
  continue to pass **unmodified**. It asserts `"G004" not in rule_ids(found)`,
  not that the run produced no findings at all, so a differently-identified
  `INFO` finding on the same fixture is compatible with it by construction.
- C-UMC-3: This repository's own change packages MUST still validate clean at
  `--fail-on ERROR` and MUST acquire zero findings from the new `WARN` rule —
  every generic stage cited by a spec under `openspec/changes/*/specs/*/spec.md`
  is a real target in this repository's Makefile.
- C-UMC-4: Every artifact `tests/test_rule_registry_docs.py` and
  `tests/test_skill_contract.py` guard MUST be updated in the same change:
  `tests/baseline_rules.json`, the generated rule catalog, the README rules
  table, `docs/architecture/c4.md`'s rule count and per-family ranges,
  `docs/agents-skills-harness.md`, `docs/next-steps.md`,
  `docs/differentiation-roadmap.md`, and `rules.py`'s own module docstring.
- C-UMC-5: The composite Action's `discovery-warnings` output MUST keep its
  current value and derivation, and MUST NOT contradict the new finding: for a
  Makefile-less target whose specs carry `make` citations, the same run MUST
  both count the no-Makefile discovery note and carry the new `INFO` finding.

---

## Decisions

- **DEC-UMC-001:** Two **new rule ids**, `G010` (INFO) and `G011` (WARN) — not
  new behaviour on G004. This is forced by the engine's own types, not chosen
  for taste. `rule_types.Rule` is a frozen dataclass with a single
  `severity: str`; `CheckHit` carries only `message` and `line`; and
  `rules.evaluate()` builds every `Finding` with
  `severity=INFO if suppressed else rule.severity`, reading the severity off
  the *rule* and never off the hit. One `Rule` therefore emits exactly one
  severity for every hit it produces. G004 is `ERROR`, so an `INFO` signal and
  a `WARN` signal can be neither G004 nor each other: three severities force
  three ids. The alternative — widening `CheckHit` with a per-hit severity
  override — was rejected: it changes the engine's core type to serve two
  findings, makes every rule's declared severity advisory, and breaks the
  contract that one rule id maps to one severity, which is exactly what
  `rules --json`, `tests/baseline_rules.json` and the README table all encode.
  Separate ids also give each signal its own waiver id and its own table row,
  so an adopter can suppress one without suppressing the other.
- **DEC-UMC-002:** G010 is `INFO`, not `WARN`. `rules.py`'s own severity
  contract defines `INFO` as "observation, never blocks", which is precisely
  what "this check could not run" is. `--fail-on INFO` already surfaces it and
  the default `--fail-on ERROR` is unaffected, so no existing caller's exit
  code moves (C-UMC-1). Note that G010 is the **first** INFO-severity entry in
  `RULES`: every `INFO` finding produced today is a downgraded waiver, from
  `evaluate()` or `evaluate_tree()`. That is why
  `test_readme_rules_table_matches_rules_exactly`'s `(ERROR|WARN)` alternation
  has to widen in this change — an INFO row is invisible to it today, and it
  would fail with a "missing/extra" diff that names no cause. This sync point
  is **not** in `.claude/skills/planlint-add-rule/SKILL.md`'s checklist; step 5
  of that checklist ("let the test tell you") is what surfaces it.
- **DEC-UMC-003:** G010 emits **one finding per spec**; G011 emits **one
  finding per offending citation**. The fact G010 reports is a property of the
  target repository — no Makefile was found — so N identical lines for N
  citations would be noise and the count belongs in the message instead. Each
  G011 finding names a different stage and each is separately fixable, which is
  the shape G004 already has.
- **DEC-UMC-004:** `GENERIC_STAGES` is **not** deleted and G004's exemption is
  **not** narrowed. "Run `make test`" is idiomatic English for "run the test
  suite", and a tox/npm/`just` repository writing it in prose is not lying
  about anything. That argument holds exactly when the repository does not
  demonstrably use Make, and `profile.make_targets` already distinguishes the
  two. Conditioning G011 on a non-empty `make_targets` is strictly narrower
  than removing the exemption and costs nothing in the tox case, because such a
  repository has no Makefile and never reaches the check.
- **DEC-UMC-005:** G011 is `WARN`, not `ERROR`. Even a repository that uses
  Make can write a stage name as shorthand in a sentence that was never meant
  as a citation, so the shorthand reading survives and the document is degraded
  rather than false — this repo's stated `WARN` contract. It also keeps
  C-UMC-1 true by construction rather than by audit.
- **DEC-UMC-006:** G004 keeps its guard clause rather than being rewritten to
  delegate to the new rules. The early return is the behaviour
  `test_g004_stays_silent_when_the_target_repo_has_no_makefile_at_all` pins,
  and that test asserts only that G004 specifically did not fire — so G010
  firing on the same fixture is compatible with it and the test must not need
  editing. Treat that as a design check: an implementation that requires
  editing that test has changed G004's semantics and is the wrong
  implementation.
- **DEC-UMC-007:** `report.discovery_notes()` and the Action's
  `discovery-warnings` output keep computing their own answer in this package,
  even though G010 is the signal they should eventually project. The function
  also covers the coverage-floor case, which has no corresponding rule id and
  would need one before it could be derived from findings; re-deriving half of
  the output from the envelope and leaving the other half computed would give
  the Action two inconsistent derivations rather than one. What does change is
  the docstring, which currently records the CLI's silence as the correct
  behaviour for both rules. C-UMC-5 pins the two against contradicting each
  other in the meantime.
- **DEC-UMC-008:** `planlint new` is not changed. `scaffold.pick_stage()`
  returning `"test"` for a Makefile-less target is what makes a freshly
  scaffolded package immediately legible, and after this change that package's
  own G010 finding says plainly that the citation was not checked. Reporting
  the truth about what the scaffold emits is a different question from changing
  what it emits, and only the first is in scope here.
- **DEC-UMC-009:** No new detection corpus shape is added. Per
  `.claude/skills/planlint-add-detect-shape/`, a rule that depends on something
  `detect` reads needs a labelled repository shape — and the shape these two
  rules need already exists:
  `tests/corpus/targets/node-vitest-no-makefile/expected.json` pins
  `"make_targets": []` for a real, non-Make repository. Both rules read
  `profile.make_targets` and `spec.make_refs`, so what they need beyond that is
  rule-level fixtures, not detection fixtures.
- **DEC-UMC-010:** No phrasing corpus rows are added and `make matcher-accuracy`
  is not a gate for this change. Step 4a of the add-rule checklist applies to a
  rule that reads prose; both new rules are set-membership tests over
  `profile.make_targets` and the citations `MAKE_REF` already extracted, with no
  regex over criterion or requirement text. There is no false-positive rate to
  measure that is not already `MAKE_REF`'s.

---

## Acceptance Criteria

- [ ] **AC-UMC-1:** A target repository with no Makefile, whose spec carries at
  least one `make` citation, produces exactly one G010 `INFO` finding for that
  spec, whose message names the count of citations it could not check.
  (R-UMC-1, DEC-UMC-003)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-UMC-2 (non-success):** A target repository with no Makefile, whose
  spec carries **no** `make` citation, produces no G010 finding — the rule
  reports an unrun check, never a missing Makefile. (R-UMC-2)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-UMC-3:** Against a Makefile declaring exactly one target that is not
  a generic stage, a spec citing the stage `test` produces exactly one G011
  `WARN` finding and zero `ERROR` findings. (R-UMC-3, DEC-UMC-005)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-UMC-4 (non-success):** That same spec, against a repository with no
  Makefile at all, produces G010 and **no** G011 — the generic-stage check does
  not run where the repository has not shown it uses Make. (R-UMC-4,
  DEC-UMC-004)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-UMC-5:** G004 is unchanged: every one of its existing tests passes
  without edit, including the low-confidence fallback case and the
  bare-English-"make" precision case. (R-UMC-6)
  _Verified by:_ `pytest -k "test_g004_fires_on_a_make_target_the_target_repo_lacks or test_g004_still_fires_on_a_genuinely_absent_target_at_low_confidence or test_g004_does_not_fire_on_a_bare_english_use_of_make"` · stage: `make test`

- [ ] **AC-UMC-6 (non-success):** No single citation produces findings from
  more than one of G004/G010/G011 in one run — a citation naming a target that
  is neither in the Makefile nor a generic stage yields exactly one G004 and no
  G011, and a Makefile-less run yields G010 and no G004. (R-UMC-5)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-UMC-7:** `test_g004_stays_silent_when_the_target_repo_has_no_makefile_at_all`
  passes byte-identical to its state before this change, with G010 now firing
  on the same fixture. (C-UMC-2, DEC-UMC-006)
  _Verified by:_ `pytest -k test_g004_stays_silent_when_the_target_repo_has_no_makefile_at_all` · stage: `make test`

- [ ] **AC-UMC-8 (non-success):** No repository that passes at `--fail-on ERROR`
  today fails after this change: the registry reports the two new ids at `INFO`
  and `WARN` respectively, neither at `ERROR`, and the regenerated baseline says
  the same. (C-UMC-1)
  _Verified by:_ `pytest -k "test_rule_set_matches_baseline or test_rule_registry_baseline_is_unchanged"` · stage: `make test`

- [ ] **AC-UMC-9:** This repository's own change packages validate clean at
  `--fail-on ERROR` with zero findings from the new `WARN` rule — every generic
  stage any spec here cites is a real target in this repository's Makefile.
  (C-UMC-3)
  _Verified by:_ `make validate` · stage: `make validate`

- [ ] **AC-UMC-10:** Both new rules appear in the committed baseline, in the
  generated skill rule catalog, and in the README rules table, with severities
  that match the registry — including the INFO row the table's guard cannot
  currently see. (C-UMC-4, DEC-UMC-002)
  _Verified by:_ `pytest -k "test_readme_rules_table_matches_rules_exactly or test_rule_catalog_lists_every_registered_rule or test_rule_catalog_is_fresh"` · stage: `make test`

- [ ] **AC-UMC-11:** Every rule-count and per-family-range claim in the docs and
  in `rules.py`'s own module docstring agrees with `rules.RULES`, with the
  generic family reading `G001-G011`. (C-UMC-4)
  _Verified by:_ `pytest -k "test_total_rule_count_matches_every_prose_claim or test_rules_py_docstring_family_ranges_match_rules or test_c4_module_map_family_ranges_match_rules"` · stage: `make test`

- [ ] **AC-UMC-12:** A `specgraph:allow` waiver naming either new rule, with a
  reason, downgrades that finding to `INFO` with a `[waived]` prefix rather
  than dropping it; neither id is in `_NON_WAIVABLE`. (R-UMC-7)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-UMC-13:** For a Makefile-less target whose specs carry `make`
  citations, the Action-facing outputs keep their existing `discovery-warnings`
  value and the same envelope carries the G010 finding — the two statements of
  the same fact agree. (C-UMC-5, DEC-UMC-007)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-UMC-14:** `GENERIC_STAGES` carries an in-source note naming the rule
  that checks it, so the exemption is no longer documented nowhere. (R-UMC-8)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-UMC-15:** The full gate is green with both rules registered — lint,
  type-check, security, docs, threshold discipline and the whole suite.
  (C-UMC-4)
  _Verified by:_ `make pre-pr` · stage: `make pre-pr`

---

## Non-Success Criteria (what this change rejects)

- An implementation that deletes or narrows `GENERIC_STAGES`, or that removes
  G004's empty-`make_targets` guard, is rejected — it breaks the tox/npm/`just`
  case the exemption exists for (DEC-UMC-004, AC-UMC-5).
- An implementation that edits
  `test_g004_stays_silent_when_the_target_repo_has_no_makefile_at_all` to make
  the new findings fit is rejected. That test is the backwards-compatibility
  evidence, not an obstacle (DEC-UMC-006, AC-UMC-7).
- An implementation that emits either new signal at `ERROR`, or that reaches
  two severities from one `Rule` by widening `CheckHit`, is rejected
  (DEC-UMC-001, DEC-UMC-002, DEC-UMC-005, AC-UMC-8).
- An implementation that lands the rules without the full registry-sync
  checklist is rejected; a rule the README and the generated catalog do not
  know about is the exact drift class `tests/test_rule_registry_docs.py` was
  added for (C-UMC-4, AC-UMC-10, AC-UMC-11).

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-UMC-1..8, AC-UMC-10..14 |
| Self-check | `make validate` | AC-UMC-9 — this repo's own packages stay clean at `--fail-on ERROR` under both new rules |
| Full | `make pre-pr` | AC-UMC-15 — full regression, lint, typecheck, security, docs, threshold discipline |
