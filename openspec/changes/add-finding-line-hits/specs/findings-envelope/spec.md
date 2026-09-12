# Spec: Findings Envelope

> **Change:** `add-finding-line-hits`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

Every finding `evaluate()` emits has `Finding.line == 0`, so SARIF omits
`region` and GitHub annotations omit `line=` for the entire run. The
projections are already honest about a missing locus; the check contract is
what never supplies one.

**Evidence:** `openspec_graph/rules.py:85-93` constructs each `Finding`
from `rule.check`'s `Iterable[str]` without passing `line=`.
`Rule.check` is typed `Callable[[ParsedSpec, StackProfile], Iterable[str]]`
(`rule_types.py:99`). G007 already embeds `waiver.line` in its message
(`rules_generic.py:86-92`) while the `Finding` stays at line 0.
`Criterion.line` and `Waiver.line` are already 1-based;
`Requirement` has no `line` field (`parse_model.py:64-69`).
`parse_harness.py:55` sets harness `Criterion.line` via
`text.find(block[:60])`, which returns the first occurrence of that prefix
in the whole document. `sarif.py:92-99` and `report.py:424-430` omit
region/`line=` when `line < 1` and never clamp `0` to `1`, pinned by
`test_a_line_of_zero_emits_no_region` and
`test_a_line_of_zero_emits_no_line_property`. `docs/next-steps.md` item 2
is this change.

`FINDINGS_SCHEMA_VERSION` stays `1`: `Finding.as_dict()` already emits
`line` (`rule_types.py:81`). Filling a 1-based value where a check has a
real locus is a value change of an existing key, which `DEC-FE-010` does
not treat as a schema bump. The package version stays `0.2.0`.

---

## Requirements

- R-LH-1: `openspec_graph/rule_types.py` MUST declare a frozen dataclass
  `CheckHit` with fields `message: str` and `line: int = 0` — the same
  default as `Finding.line`. `CheckHit` MUST be added to that module's
  `__all__`.
- R-LH-2: The same module MUST declare a type alias
  `CheckResult = str | CheckHit` and a helper
  `as_check_hit(item: CheckResult) -> CheckHit`. A bare `str` MUST become
  `CheckHit(message=item, line=0)`. A `CheckHit` MUST be returned
  unchanged, including a non-positive `line`.
- R-LH-3: `Rule.check` MUST be typed
  `Callable[[ParsedSpec, StackProfile], Iterable[CheckResult]]`. A check
  that yields a bare `str` MUST remain valid and MUST continue to mean
  "no locus" (`line` 0).
- R-LH-4: `openspec_graph/rules.py` MUST re-export `CheckHit`,
  `CheckResult`, and `as_check_hit` through its facade `__all__`, so
  callers reach them as `rules.CheckHit` the way they reach `Finding`
  (R-DG-1). `cli.py` MUST NOT gain a direct `rule_types` import for these
  names.
- R-LH-5: `evaluate()` MUST coerce every item `rule.check` yields through
  `as_check_hit`. It MUST copy `hit.line` onto the constructed `Finding`
  when `hit.line >= 1`, and MUST store `0` otherwise. It MUST NOT clamp
  `0` or a negative value to `1`.
- R-LH-6: `evaluate()` MUST log through
  `logging.getLogger("planlint.rules")`, a child of `planlint`, and MUST
  NOT attach an extra handler. At DEBUG the record MUST name the rule id
  and either the attached 1-based line or the token `unset`. The logger
  MUST NOT emit finding message bodies at INFO, and MUST emit no records
  at the default WARNING level.
- R-LH-7: `evaluate_tree()` MUST continue to construct G006 and G009
  findings without passing `line=`, so those findings keep `Finding.line
  == 0`.
- R-LH-8: `FINDINGS_SCHEMA_VERSION` MUST remain `1`. The package version
  MUST remain `0.2.0`. The `line` key on `Finding.as_dict()` MUST keep its
  spelling and meaning.
- R-LH-9: `Requirement` MUST gain `line: int = 0` as its last dataclass
  field (after `body`), so existing positional construction of earlier
  fields does not silently rebind.
- R-LH-10: `parse_semantics.py` MUST provide
  `section_span(text, name) -> tuple[int, str]` returning the body's start
  offset in `text` and the body string. `section_body` MUST become
  `return section_span(...)[1]` and MUST keep returning `str`. A missing
  section MUST yield offset `0` and body `""`.
- R-LH-11: The harness, upstream, and speckit parsers MUST set
  `Requirement.line` via `line_of(full_text, absolute_match_start)` where
  `absolute_match_start` is the start of the declaration in the full
  document — span origin plus `match.start()` for a match taken against a
  section body, or `match.start()` when the match is already against the
  full text. SpecKit FR bullets MUST use the nested Functional
  Requirements span origin, not `text.find` of a bullet prefix.
- R-LH-12: Harness `Criterion.line` MUST be the line of the AC bullet,
  computed as the Acceptance Criteria `section_span` origin plus
  `match.start()`. It MUST NOT use `text.find(block[:60])` or any other
  first-occurrence search of a prefix. SpecKit Success Criteria bullets
  MUST likewise use the Success Criteria span origin plus `match.start()`
  rather than `text.find(m.group(0))`. SpecKit GWT scenarios MUST keep
  `story.start() + scen.start()`.
- R-LH-13: `ParsedSpec.orphan_requirements` MUST remain a
  `tuple[str, ...]` of requirement idents. H003 MUST look up
  `Requirement.line` by ident from `spec.requirements`. The property's
  signature MUST NOT change.
- R-LH-14: These checks MUST yield `CheckHit` (message strings
  **unchanged**) with the locus named: G007 (`waiver.line`); H001, H002,
  H004 (`crit.line`); H003 (`Requirement.line` looked up by ident); U002,
  U004 (`req.line`); U003 (`crit.line`); S001
  (`NEEDS_CLARIFICATION.finditer` + `line_of` on length-preserving
  waiver-stripped text); S002 both halves (the duplicate requirement's or
  criterion's `.line`); S003 (`req.line`); S004 (`crit.line`); W001, W002
  (`crit.line`).
- R-LH-15: These checks MUST keep yielding a bare `str` (so `Finding.line`
  stays `0`): G001, G002, G003, G004, G005, G008, G006, G009, H005, H006,
  U001, U005.
- C-LH-1: This change MUST NOT increment `FINDINGS_SCHEMA_VERSION`.
- C-LH-2: This change MUST NOT clamp a non-positive line to `1` in
  `evaluate()`, in `sarif.to_sarif`, or in `report.to_annotations`.
- C-LH-3: This change MUST NOT attribute G003, G004, G005, or G008 by
  searching the document for the first occurrence of the cited
  threshold, make target, invariant id, or ADR id.
- C-LH-4: Migrated rules MUST keep their current finding message strings
  byte-for-byte, including G007's embedded `at line {waiver.line}` text.
- C-LH-5: This change MUST NOT bump `openspec_graph.__version__`.
- C-LH-6: This change MUST NOT add a field to `Rule` other than the
  `check` callable's return type, MUST NOT add a rule or rule family, and
  MUST NOT introduce a plugin mechanism.

---

## Decisions

- **DEC-LH-001:** a frozen `CheckHit` dataclass rather than a `(message,
  line)` tuple or a second `check_with_line` method. A named type is what
  `as_check_hit` can total over, and what a migrated check can construct
  without a comment explaining tuple order. A second method would leave
  two check contracts to drift — the failure mode `to_posix_relative` was
  created to end (`DEC-PS-003`). The default `line=0` matches `Finding`,
  so an unmigrated `CheckHit(message=...)` and a bare `str` mean the same
  thing.
- **DEC-LH-002:** a bare `str` remains a valid `CheckResult`. Forcing every
  check to construct `CheckHit` in this change would be a mechanical rewrite
  of G001–G005/G008/H005/H006/U001/U005, none of which have a locus to
  attach. Yielding `str` continues to mean "unset", and `as_check_hit` is
  the one coercion so `evaluate()` does not grow an `isinstance` ladder.
- **DEC-LH-003:** `evaluate()` stores `0` for any `hit.line < 1` and never
  clamps to `1`. SARIF's `startLine` minimum is 1; clamping would put a
  wrong annotation on the first line of a real file, which
  `sarif.py:92-96` and `report.py:424-428` already refuse to do. This
  change fills the field; it does not reopen that refusal.
- **DEC-LH-004:** `FINDINGS_SCHEMA_VERSION` stays `1`, following
  `DEC-FE-010`. That decision started the constant at `1` and reserved
  bumps for a breaking change to the envelope or to a finding's own keys.
  `line` is already a key. A consumer that ignored the field when it was
  always `0` still sees the same key; a consumer that wants a region now
  has one when the value is `>= 1`. Coupling the schema version to the
  package version is what `tool_version` exists to avoid, and the package
  version is not bumping either (`C-LH-5`).
- **DEC-LH-005:** the logger is `logging.getLogger("planlint.rules")`, a
  child of the `planlint` logger `log.configure()` already owns. Detect
  and parse use the same child-name pattern (`planlint.detect`,
  `planlint.parse`). The child MUST NOT add a handler: `configure()`
  attaches one handler to `planlint` with `propagate = False` on the
  parent, so a child with default `NOTSET` and `propagate = True` reaches
  that handler once. A second handler on the child would duplicate every
  DEBUG line. DEBUG records the rule id and the line or `unset` so a
  contributor can see which checks attached a locus without dumping
  finding text into CI logs. Message bodies stay off INFO and off the
  default WARNING run; `test_evaluate_is_silent_at_default_warning` pins
  the quiet default.
- **DEC-LH-006:** `section_span` is additive; `section_body` becomes a
  one-line wrapper returning the string. Changing `section_body`'s return
  type to a tuple would break every caller that concatenates, indexes, or
  `finditer`s the body (`parse_harness.py`, `hard_coded`, SpecKit helpers
  that exist specifically because they are *not* `section_body`). The
  offset is the start of the body (end of the heading match), which is
  the origin `match.start()` from a body-scoped `finditer` is relative
  to.
- **DEC-LH-007:** harness `Criterion.line` is the AC bullet's line, from
  span origin plus `match.start()`, not `text.find(block[:60])`. The
  prefix search is a documented false locus: a duplicate leading sixty
  characters anywhere earlier in the document — another AC, a quoted
  example in the Problem Statement — wins. Criteria already had a `line`
  field; this decision makes the number true rather than introducing the
  field.
- **DEC-LH-008:** `orphan_requirements` stays a tuple of idents. H003 and
  U002 share the property (`parse_model.py:130-134`); widening it to
  `Requirement` objects would be a signature break for every caller that
  treats the values as strings (`set(spec.orphan_requirements)` in
  `rules_upstream.py:23`). H003 looks up `Requirement.line` by ident
  instead. U002 already iterates `spec.requirements` and can read
  `req.line` directly.
- **DEC-LH-009:** only checks that already hold a real 1-based locus
  migrate to `CheckHit`. Document-level checks (G001, G002, H005, H006,
  U001, U005) and cross-tree checks (G006, G009) have no single line that
  would be true. Citation checks (G003, G004, G005, G008) have a string,
  not a span; attaching a line is `DEC-LH-010`. Leaving those as `str`
  keeps `Finding.line == 0` by construction rather than by a `CheckHit`
  whose `line=0` a future editor might "helpfully" fill in.
- **DEC-LH-010:** G003–G005/G008 MUST NOT grow a first-match search for
  the cited token. `parse_harness.py:55` is the existence proof that
  first-match is a false locus; doing it for a make-target name or a
  threshold substring would annotate the wrong copy more often than the
  right one, and a wrong `startLine` on a pull-request diff is the
  failure `DEC-LH-003` exists to prevent. Honest absence stays omitted.
- **DEC-LH-011:** `Requirement.line` is appended after `body`, not
  inserted between existing fields. `ParsedSpec` already records the
  reason (`parse_model.py:99-104`): a new field ahead of an existing one
  shifts every later positional index. `Requirement` is publicly
  exported from `parse.py`; the same discipline applies.
- **DEC-LH-012:** `evaluate_tree()` does not grow a line. G006/G009 point
  at an invariant or ADR id that is absent from every living spec; the
  declaring source is already in `path=`, and there is no single line in
  that source this change is willing to guess. Same honest-absence
  stance as `DEC-LH-009`.
- **DEC-LH-013:** SpecKit FR/SC line numbers use the nested-span origin
  plus `match.start()`, not `text.find` of the bullet. `parse_speckit.py:58`
  currently uses `text.find(m.group(0))` for Success Criteria — the same
  first-match class as `parse_harness.py:55`. Implementation MAY add
  `speckit_section_span` / `speckit_subsection_span` next to the existing
  body helpers if that is the cleanest way to recover the origin; those
  helpers are not a new public product surface. SpecKit GWT already uses
  `story.start() + scen.start()` (`parse_speckit.py:88`) and keeps it.
- **DEC-LH-014:** migrated message strings are unchanged. G007's message
  already names `waiver.line`; putting the same number on `Finding.line`
  is additive. Rewording messages in the same change would mix a locus
  fix with a copy edit, and every test that pins a message would move for
  a reason unrelated to lines.

---

## Acceptance Criteria

- [ ] **AC-LH-1:** `as_check_hit("bare")` returns a `CheckHit` whose
  `message` is `"bare"` and whose `line` is `0`; `as_check_hit` on an
  existing `CheckHit` returns it unchanged; both names import from
  `openspec_graph.rules` (and from `rule_types`). A `Rule.check` that
  yields a bare `str` is still accepted. (R-LH-1, R-LH-2, R-LH-3, R-LH-4,
  C-LH-6, DEC-LH-001, DEC-LH-002)
  _Verified by:_ `pytest -k test_as_check_hit_coerces_a_string_to_line_zero` · stage: `make test`

- [ ] **AC-LH-2:** `evaluate()` over a check that yields
  `CheckHit(message=..., line=N)` with `N >= 1` produces a `Finding`
  whose `line` is `N` and whose `message` is the hit's message.
  (R-LH-5, DEC-LH-003)
  _Verified by:_ `pytest -k test_evaluate_copies_checkhit_line_onto_finding` · stage: `make test`

- [ ] **AC-LH-3 (non-success):** `evaluate()` over a `CheckHit` whose
  `line` is `0`, and over a `CheckHit` whose `line` is negative, stores
  `Finding.line == 0` — never `1`. A bare `str` from an unmigrated check
  likewise stores `0`. (R-LH-5, C-LH-2, DEC-LH-003)
  _Verified by:_ `pytest -k "test_evaluate_stores_zero_for_nonpositive_checkhit_line or test_evaluate_does_not_clamp_zero_to_one"` · stage: `make test`

- [ ] **AC-LH-4:** With the `planlint.rules` logger at DEBUG, `evaluate()`
  emits a record that names the rule id and the attached line or `unset`,
  and the record does not contain the finding message body.
  (R-LH-6, DEC-LH-005)
  _Verified by:_ `pytest -k test_evaluate_debug_log_names_rule_and_line_not_message` · stage: `make test`

- [ ] **AC-LH-5 (non-success):** At the default WARNING level, `evaluate()`
  emits no log records on `planlint.rules` (and no finding message on
  INFO). A quiet default run stays quiet. (R-LH-6, DEC-LH-005)
  _Verified by:_ `pytest -k test_evaluate_is_silent_at_default_warning` · stage: `make test`

- [ ] **AC-LH-6:** A harness R-/C- bullet, an upstream `### Requirement:`
  heading, and a SpecKit `FR-` bullet each produce `Requirement.line`
  equal to the 1-based line of that declaration in the full document, not
  `0` and not a line from a duplicate copy of the same prefix elsewhere.
  (R-LH-9, R-LH-11, DEC-LH-011, DEC-LH-013)
  _Verified by:_ `pytest -k test_requirement_line_is_one_based_in_harness_upstream_and_speckit` · stage: `make test`

- [ ] **AC-LH-7:** In a harness document where `text.find(block[:60])`
  for the second AC actually diverges from that bullet's line — either
  because the Problem Statement quotes that AC's `block[:60]`, or
  because two ACs share an ident so the first sixty characters collide —
  the second criterion's `.line` is the line of the second AC bullet,
  not the earlier copy. Distinct ids with only a shared description do
  not reproduce the old false locus (the ident sits inside `block[:60]`).
  (R-LH-10, R-LH-12, DEC-LH-007)
  _Verified by:_ `pytest -k test_harness_criterion_line_is_the_ac_bullet_not_a_duplicate_prefix` · stage: `make test`

- [ ] **AC-LH-8 (non-success):** `section_body(text, name)` still returns
  only the span text — a `str`, not a `(offset, body)` tuple — equal to
  `section_span(text, name)[1]`. Callers that never asked for an offset
  do not start receiving one. (R-LH-10, DEC-LH-006)
  _Verified by:_ `pytest -k test_section_body_still_returns_only_the_span_text` · stage: `make test`

- [ ] **AC-LH-9:** A reason-less waiver produces a G007 finding whose
  `line` equals `waiver.line` and whose message is the pre-change string
  (still containing `at line {waiver.line}`). (R-LH-14, C-LH-4,
  DEC-LH-014)
  _Verified by:_ `pytest -k test_g007_finding_line_equals_waiver_line` · stage: `make test`

- [ ] **AC-LH-10:** An H001 finding for a criterion missing its
  Verified-by citation, or whose citation names no make stage, has
  `Finding.line` equal to that criterion's `.line`. (R-LH-14)
  _Verified by:_ `pytest -k test_h001_finding_line_is_the_criterion_line` · stage: `make test`

- [ ] **AC-LH-11:** A U003 finding for a scenario missing WHEN or THEN
  has `Finding.line` equal to that scenario's `Criterion.line`.
  (R-LH-14)
  _Verified by:_ `pytest -k test_u003_finding_line_is_the_scenario_line` · stage: `make test`

- [ ] **AC-LH-12:** An S001 finding for an unresolved
  `[NEEDS CLARIFICATION]` marker has `Finding.line` equal to
  `line_of` of that marker's match start on the waiver-stripped
  document. (R-LH-14, DEC-LH-013)
  _Verified by:_ `pytest -k test_s001_finding_line_is_the_clarification_marker` · stage: `make test`

- [ ] **AC-LH-13:** An H003 finding for an orphan requirement has
  `Finding.line` equal to that requirement's `.line`, looked up by ident
  from `orphan_requirements` without changing that property's return
  type. (R-LH-9, R-LH-13, R-LH-14, DEC-LH-008)
  _Verified by:_ `pytest -k test_h003_finding_line_is_the_orphan_requirement_line` · stage: `make test`

- [ ] **AC-LH-14:** A W001 finding (evaluated through `evaluate(...,
  rule_set=RULES)` or the equivalent `--require-witness` path) has
  `Finding.line` equal to the citing criterion's `.line`. (R-LH-14)
  _Verified by:_ `pytest -k test_w001_finding_line_is_the_criterion_line` · stage: `make test`

- [ ] **AC-LH-15:** A migrated ERROR whose `Finding.line` is `>= 1`
  round-trips through `Finding.as_dict` into `sarif.to_sarif` as
  `region.startLine` equal to that line, and a GitHub annotation for the
  same finding carries `line=` with that value. (R-LH-5, R-LH-14,
  DEC-LH-003)
  _Verified by:_ `pytest -k "test_migrated_error_round_trips_to_sarif_start_line or test_a_real_line_emits_a_start_line or test_a_real_line_emits_a_line_property"` · stage: `make test`

- [ ] **AC-LH-16 (non-success):** A `Finding` with `line == 0` — including
  a `CheckHit(line=0)`, an unmigrated check, `evaluate_tree()`'s G006/G009,
  and the citation rules G003–G005/G008 — still omits SARIF `region` and
  still omits the GitHub `line=` property. No first-match search is
  introduced for those citation rules. (R-LH-7, R-LH-15, C-LH-2, C-LH-3,
  DEC-LH-003, DEC-LH-009, DEC-LH-010, DEC-LH-012)
  _Verified by:_ `pytest -k "test_a_line_of_zero_emits_no_region or test_a_line_of_zero_emits_no_line_property"` · stage: `make test`

- [ ] **AC-LH-17 (non-success):** `FINDINGS_SCHEMA_VERSION` is still `1`,
  `validate --json` still carries the same envelope keys, and
  `openspec_graph.__version__` is still the current `0.2.0` value this
  change is forbidden to bump. Filling `line` does not announce a new
  schema. (R-LH-8, C-LH-1, C-LH-5, DEC-LH-004)
  _Verified by:_ `pytest -k "test_envelope_carries_a_schema_version or test_existing_keys_keep_their_spelling or test_cli_version_flag_reports_the_package_version"` · stage: `make test`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-LH-1..17 |
| Core | `make ci` | AC-LH-1..17, plus lint and this repo's own `planlint validate` |
| Types | `make typecheck` | `CheckHit` / `CheckResult` / `Rule.check` annotations accepted |
| Full | `make pre-pr` | full regression, lint, typecheck, security, docs, no-hardcoded-thresholds |
