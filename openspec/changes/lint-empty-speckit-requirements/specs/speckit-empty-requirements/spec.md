# Spec: SpecKit Empty Requirements Section (SER)

> **Change:** `lint-empty-speckit-requirements`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

`parse_speckit()` extracts functional requirements from a level-3
`Functional Requirements` heading nested inside the level-2 `Requirements`
span. When a hand-edited spec promotes that heading one level — writing
`## Functional Requirements` — neither lookup resolves, `FR_DECL` iterates an
empty string, and the document contributes zero requirement nodes to the
dependency graph. Nothing reports it.

**Evidence:** the mechanism is two lines,
`openspec_graph/parse_speckit.py:35-36`:

```python
req_origin, req_section = speckit_section_span(text, "Requirements")
sub_origin, req_body = speckit_subsection_span(req_section, "Functional Requirements")
```

`speckit_section_span` (`parse_semantics.py:478-488`) compares an
annotation-stripped level-2 title for exact equality, so
`## Functional Requirements` is not `Requirements`;
`speckit_subsection_span` (`parse_semantics.py:508-517`) returns `(0, "")`
when the named level-3 heading is absent from the span handed to it. Both
returns are empty strings, and an empty string is indistinguishable from a
section that was legitimately never written.

Reproduced at `c60f894` — one file, one heading level changed. The canonical
level-3 form yields graph nodes `FR-001`, `FR-002`, `SC-001`; the level-2 form
yields `SC-001` alone. Both runs print `1 spec(s) checked · 0 error · 0 warn ·
0 info`, `PASS`, and `broken_links: 0`.

No existing rule can catch it. G001's check returns early whenever
`spec.criteria` is non-empty (`rules_generic.py:20-22`), and the surviving
`SC-001` keeps it non-empty — the spec is not requirement-*less*, it is
requirement-*losing*. S002 and S003 both iterate `spec.requirements`, which is
the empty tuple, so each has nothing to report. The failure is not a gap in any
one rule's logic; it is that every rule which could have noticed reads the
parsed model, and the parsed model is where the loss already happened.

This was deferred once, deliberately (`docs/next-steps.md` item 4b / R6,
`docs/peer-review-2026-09.md` F4), because the obvious rule — "a speckit spec
with zero requirements" — would fire on every legitimately FR-less,
user-story-only draft, which is a supported state in SpecKit's own authoring
workflow. That caution stands. It does not reach the discriminating case: a
`Requirements`-shaped section that **exists** and yields zero `FR-` bullets is
a different state from no such section at all, and only the former has made a
claim the parser could not honour.

---

## Requirements

- R-SER-1: `rules_speckit.py` MUST add exactly one new rule, **S005** — the
  next free identifier in the `S` family, whose current members are S001-S004
  (`rules_speckit.py:65-70`) — at WARN severity, with
  `dialects=("speckit",)`, appended after S004 so `SPECKIT_RULES` stays
  append-ordered.
- R-SER-2: S005 MUST emit exactly one finding for a speckit-dialect spec in
  which a `Requirements`-shaped heading is present **and** `spec.requirements`
  is empty. It MUST NOT emit one finding per missing bullet, per candidate
  heading, or per section: the condition is a property of the document, and
  one finding per document is what an author can act on.
- R-SER-3: a `Requirements`-shaped heading MUST be defined as the first
  level-2 or level-3 heading whose title, after the same trailing-annotation
  normalization `speckit_section_span` already applies, is case-insensitively
  **equal** to `Requirements` or to `Functional Requirements`. The comparison
  MUST be equality after normalization, never a prefix, substring, or
  contains test — a heading titled `Non-Functional Requirements` or
  `Requirements Traceability` MUST NOT count.
- R-SER-4: S005 MUST NOT emit any finding for a speckit-dialect spec that
  carries no `Requirements`-shaped heading at all, whatever else it contains.
  This is the deferral condition from item 4b, pinned as behaviour rather than
  left to a reviewer's memory.
- R-SER-5: S005 MUST NOT emit any finding when `spec.requirements` is
  non-empty, regardless of how many headings match R-SER-3.
- R-SER-6: S005 MUST fire, with its single unchanged message, when the
  `Requirements`-shaped section exists and contains only prose, and when it
  contains only bullets that are not `FR-`-shaped (a
  `- **NFR-001**: ...` sibling, say — a shape `FR_DECL` deliberately refuses,
  `parse_semantics.py:45-49`). These MUST NOT be split into distinct
  severities, messages, or rule identifiers.
- R-SER-7: the two heading names `parse_speckit.py` looks up as bare string
  literals today MUST become shared constants in `parse_semantics.py`
  (`SPECKIT_REQUIREMENTS_HEADING`, `SPECKIT_FUNCTIONAL_REQUIREMENTS_HEADING`),
  beside the existing `SPECKIT_SUCCESS_CRITERIA_HEADING`, and both
  `parse_speckit.py`'s lookups and S005's heading scan MUST read them. S005
  MUST NOT carry its own copy of either name.
- R-SER-8: S005's heading scan MUST run over
  `strip_waiver_comments(spec.raw)`, not `spec.raw`, and the finding MUST be a
  `CheckHit` carrying the matched heading's own 1-based line, so the
  annotation lands on the heading the author has to fix.
- R-SER-9: S005 MUST be WARN. A spec whose only finding is S005 MUST still
  exit 0 under `validate`'s default `--fail-on ERROR`, so no existing consumer
  of this tool changes behaviour on upgrade.
- R-SER-10: every location that states the rule inventory MUST be updated in
  the same change: `tests/baseline_rules.json` (regenerated, not hand-edited),
  the distributable skill's rule catalog (via `make skill-catalog`, likewise
  generated), README's rules table, `docs/architecture/c4.md`'s total rule
  count **and** its per-family range claims in both the module map and its
  caption, `docs/agents-skills-harness.md`, `docs/next-steps.md`,
  `docs/differentiation-roadmap.md`, and `rules.py`'s own module docstring.
  `tests/test_decomposition.py::_EXPECTED_HASHES["rules"]` MUST be re-pinned;
  `["validate"]` and `["graph"]` MUST stay unchanged.
- R-SER-11: each firing shape and each non-firing shape named in this spec
  MUST have its own deterministic fixture and its own assertion. A single
  fixture proving the rule *can* fire proves nothing about the discrimination
  this rule exists for.
- R-SER-12: `parse_speckit()`'s heading scoping MUST NOT change. The level-2
  span, the nested level-3 span, and their exact-title lookups stay exactly as
  R-SK-30/AC-SK-49 left them; this change adds a diagnostic beside the parser,
  never a looser parse.
- C-SER-1: no existing rule's identifier, severity, dialect tuple, or message
  MAY change, and no configuration key, CLI flag, or environment variable MAY
  be added to tune, disable, or re-severity S005.
- C-SER-2: no analogous rule for an empty `Success Criteria` section MAY ship
  in this change.
- C-SER-3: S005 MUST NOT be suppressed when G001 also fires on the same spec,
  and G001's own behaviour MUST NOT change.
- C-SER-4: S005's check MUST NOT read `Requirement.text`, `Requirement.body`,
  `Criterion.text`, or `Criterion.note`, and this change MUST NOT add a row to
  `tests/fixtures/phrasing/`, a floor key to `tools/matcher_accuracy.py`, or a
  repository shape to `tests/corpus/targets/`.
- C-SER-5: S005's `dialects` tuple MUST be `("speckit",)` and MUST NOT be
  `("*",)` or include `harness`/`upstream`.

---

## Decisions

- **DEC-SER-001:** the discriminator is the *presence of the section*, not the
  *absence of requirements*. These are two different predicates and only one of
  them is safe. "Zero requirements" fires on every user-story-only draft, which
  is a supported authoring state and exactly the false positive item 4b
  refused to ship. "A section that exists and yielded nothing" fires only on a
  document that opened a requirements section and got nothing out of it —
  either because the heading is at the wrong level, or because what is inside
  it is not in the form the parser reads. In both cases the author has already
  declared an intent the machine could not honour, and saying so is a report
  about the document rather than a guess about the author.
- **DEC-SER-002:** both `Requirements` and `Functional Requirements` count, and
  both count at level 2 as well as level 3. The reproduced defect presents in
  two shapes, and either name on its own catches only one of them. Promote the
  level-3 heading while the level-2 `Requirements` heading survives, and the
  only heading left in the document is named `Requirements` — a
  `Functional Requirements`-only match misses it. Collapse the pair into one
  level-2 `Functional Requirements` heading, and the name `Requirements` never
  appears at all — a `Requirements`-only match misses that one instead.
  Accepting either name at either level covers both shapes without the rule
  having to model which edit the author made, which it has no way to know.
- **DEC-SER-003:** the match is equality after annotation-stripping, never a
  substring test. A `contains` test would read `Non-Functional Requirements` as
  a requirements section and fire on a spec that legitimately declares only
  non-functional requirements — reintroducing a false positive of the same
  family this rule is designed around, and one `FR_DECL` already went out of
  its way to avoid at the bullet level (`parse_semantics.py:45-49`, anchored so
  `- **NFR-001**:` cannot match). Normalization is reused from
  `speckit_section_span` rather than reimplemented, so the rule and the parser
  cannot disagree about whether `## Requirements *(mandatory)*` is
  `Requirements`.
- **DEC-SER-004:** a prose-only section and a section of non-`FR-`-shaped
  bullets get the same finding, not two. All three states — wrong level, prose
  only, wrong bullet shape — are the same observable fact from the parser's
  side: a section exists and produced no requirement. Splitting them would
  require classifying what *is* in the section, which means judging bullet
  shapes and prose, which is the class of check step 4a of
  `.claude/skills/planlint-add-rule/SKILL.md` requires a measured phrasing
  corpus for. One state, one message, and the message names the canonical form
  so the author can compare their section against it. A message enriched with
  "n bullets found, none matching `- **FR-nnn**: `" is deliberately deferred,
  not rejected: it is a strictly better message and a strictly worse rule to
  ship without a corpus behind it.
- **DEC-SER-005:** the finding carries the heading's line, not line 0 and not
  the first line of the file. `add-finding-line-hits` made `CheckHit`'s locus
  available precisely so a finding can point at the token a reader has to
  change, and the heading is the whole defect here. `strip_waiver_comments` is
  length-preserving, so a line computed over the stripped text is the raw
  document's line — the same property `_unresolved_clarification` already
  relies on (`rules_speckit.py:15-28`).
- **DEC-SER-006:** the scan runs over waiver-stripped text. This follows S001's
  established precedent, and it is also the conservative direction: stripping
  can only *remove* a candidate heading, never invent one, so it can only make
  S005 quieter. The parser itself does not strip waivers before its own
  requirement scan, so the two could in principle disagree about a heading
  written inside a waiver comment; that asymmetry is pre-existing, it fails in
  the silent direction for this rule, and fixing the parser's waiver handling
  is not in this change's scope.
- **DEC-SER-007:** the heading names become shared constants rather than a
  second pair of literals in `rules_speckit.py`. This is the exact failure mode
  `SPECKIT_SUCCESS_CRITERIA_HEADING`'s own comment already records
  (`parse_semantics.py:51-54`) — "shared … so the two can't independently
  drift." If the parser's vocabulary ever changes and the rule's copy does not,
  S005 goes blind in precisely the situation it exists to cover, and nothing
  would fail. A shared constant makes that impossible rather than unlikely.
- **DEC-SER-008:** no cross-rule suppression with G001, in either direction.
  `Rule.check` is typed `Callable[[ParsedSpec, StackProfile],
  Iterable[CheckResult]]` (`rule_types.py:122-131`), so a rule structurally
  cannot see another rule's findings; suppression would require inventing a
  mechanism this engine has never had. It would also suppress the better
  message: G001's requirement-less branch names the harness and upstream
  authoring forms by hand (`rules_generic.py:29-33`) and says nothing a SpecKit
  author can act on, while S005 points at their own heading.
- **DEC-SER-009:** step 4a of the add-rule checklist does not apply, confirmed
  rather than assumed. The rule's entire input is `len(spec.requirements)` and
  a match of `SECTION`/`SUBSECTION` — regexes over `^##` and `^###` — followed
  by a string equality against two constants. No requirement or criterion text
  is examined, which is what makes it a structural check rather than a prose
  one. `tools/matcher_accuracy.py`'s `FLOOR_KEYS` covers `G002` and `U004`
  only, and it scores `Criterion.is_negative` and `Requirement.is_normative` —
  neither of which S005 calls. There is no phrasing judgement here to measure,
  and reporting a precision figure for a heading-level comparison would
  describe nothing.
- **DEC-SER-010:** step 4b of the add-rule checklist does not apply either.
  S005's check ignores its `StackProfile` parameter entirely, as every other
  rule in `rules_speckit.py` does (`_p`), so it depends on nothing `detect`
  reads from a target repository and needs no `tests/corpus/targets/` shape.
- **DEC-SER-011:** WARN, and WARN is a contract rather than a starting point.
  ERROR would change the exit code of every consumer running the default
  `--fail-on ERROR` against a spec this rule newly notices, on the strength of
  a discrimination that has been designed but not yet measured against a
  collected corpus of real SpecKit documents — the same bar that holds S004 at
  WARN (DEC-SK-019). Promotion, if it is ever justified, is a separate change
  with its own evidence, not a follow-up milestone in this one.
- **DEC-SER-012:** the parser is not loosened to accept the wrong-level
  heading. Accepting it would re-open AC-SK-49's over-matching bug and would
  silently rewrite the author's document structure in the tool's head. A tool
  that reports "your heading is at a level I do not read" is auditable; a tool
  that quietly reads it anyway is the thing this repository exists to argue
  against.
- **DEC-SER-013:** a `Success Criteria` analogue is excluded rather than
  bundled. The sibling defect is real and is named in the same item 4b, but its
  discrimination is not a mirror of this one: criteria have a second,
  independent source in the User Story acceptance scenarios that synthesize
  `US<n>-AS<m>` entries, so "the section exists and yielded nothing" does not
  mean the same thing there. Shipping it as an assumed symmetry would be
  exactly the rushed addition item 4b declined.

---

## Acceptance Criteria

- [ ] **AC-SER-1:** a speckit spec whose requirements heading sits at level 2
  (`## Functional Requirements`) instead of the canonical nested level-3
  heading produces exactly one S005 finding, at WARN. (R-SER-1, R-SER-2)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-SER-2:** a speckit spec carrying a level-2 `Requirements` heading
  with no level-3 `Functional Requirements` heading beneath it produces one
  S005 finding. (R-SER-2, R-SER-3)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-SER-3:** a speckit spec whose `Requirements`-shaped section contains
  only prose — no bullets of any shape — produces one S005 finding. (R-SER-6)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-SER-4:** a speckit spec whose `Requirements`-shaped section contains
  only non-`FR-`-shaped bullets (a `- **NFR-001**: ...` list) produces one S005
  finding, with the same message as AC-SER-1 and AC-SER-3 — not a distinct
  message, severity, or rule id. (R-SER-6)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-SER-5 (non-success):** a legitimately FR-less, user-story-only
  speckit draft — no `Requirements`-shaped heading anywhere in the document —
  produces no S005 finding at any severity. This is the false positive item 4b
  deferred this rule over, pinned as behaviour. (R-SER-4)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-SER-6 (non-success):** the canonical `good_speckit.md` fixture,
  whose requirements parse correctly today, produces no S005 finding, and its
  extracted requirements and criteria are unchanged by this package.
  (R-SER-5, R-SER-12)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-SER-7 (non-success):** a speckit spec whose only requirements-like
  heading is titled `Non-Functional Requirements` (or `Requirements
  Traceability`) produces no S005 finding — the title comparison is equality
  after annotation-stripping, not a substring test. (R-SER-3)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-SER-8 (non-success):** S005 is never evaluated against a harness- or
  upstream-dialect spec, and this repository's own change packages still
  validate clean — every harness spec in this tree, including this one, carries
  a level-2 `Requirements` heading and zero `FR-` bullets, so a rule scoped
  `("*",)` would fire on all of them. (C-SER-5, R-SER-1)
  _Verified by:_ `make validate` · stage: `make validate`

- [ ] **AC-SER-9:** the S005 finding's `line` is the 1-based line of the
  matched heading in the raw document, not 0 and not the first line of the
  file. (R-SER-8)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-SER-10 (non-success):** a `Requirements`-shaped heading that appears
  only inside a waiver comment does not make S005 fire; the scan sees
  waiver-stripped text. (R-SER-8)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-SER-11 (non-success):** a speckit spec whose only finding is S005
  exits 0 under the default `--fail-on ERROR`, and non-zero only under
  `--fail-on WARN` — the backwards-compatibility guarantee, asserted on the
  exit code rather than on the severity constant alone. (R-SER-9)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-SER-12:** `parse_speckit.py` and S005 resolve their heading names
  from the same `parse_semantics.py` constants, with no second copy of either
  literal in `rules_speckit.py`, and `parse_speckit()`'s output over every
  existing speckit fixture is unchanged by the constant extraction.
  (R-SER-7, R-SER-12)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-SER-13:** README's rules table, `docs/architecture/c4.md`'s rule
  count and both of its per-family range claims,
  `docs/agents-skills-harness.md`, `docs/next-steps.md`,
  `docs/differentiation-roadmap.md`, and `rules.py`'s module docstring all
  match `rules.RULES` with S005 present. (R-SER-10)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-SER-14 (non-success):** `tests/baseline_rules.json` and the
  distributable skill's rule catalog are both regenerated rather than
  hand-edited, and a stale copy of either fails; the `rules` golden hash is
  re-pinned while the `validate` and `graph` hashes stay unchanged, confirmed
  empirically against the canonical fixture, which has no `specs/` directory.
  (R-SER-10)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-SER-15 (non-success):** a speckit spec that is both
  criterion-less and carries an empty `Requirements`-shaped section reports
  G001 and S005 together; neither rule suppresses the other and G001's message
  is unchanged. (C-SER-3)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-SER-16 (non-success):** no existing rule's identifier, severity,
  dialect tuple, or message changed, and no configuration key, CLI flag, or
  environment variable was added to tune or disable S005 — a waiver remains the
  only supported way to silence it. (C-SER-1)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-SER-17 (non-success):** `planlint rules --json` lists exactly
  S001-S005 for the speckit family; no `Success Criteria` analogue shipped in
  this change. (C-SER-2)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-SER-18 (non-success):** S005's check reads no prose field, and this
  change adds no row under `tests/fixtures/phrasing/`, no floor key to
  `tools/matcher_accuracy.py`, and no repository shape under
  `tests/corpus/targets/`. (C-SER-4)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-SER-19:** every firing shape (AC-SER-1 through AC-SER-4) and every
  non-firing shape (AC-SER-5 through AC-SER-8, AC-SER-10) has its own named
  fixture and its own assertion, so no shape is covered only by another's
  fixture. (R-SER-11)
  _Verified by:_ `make test` · stage: `make test`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-SER-1..7, AC-SER-9..19 |
| Self-check | `make validate` | AC-SER-8 — this repository's own harness packages stay clean, and this package validates against the rules it describes |
| Full | `make pre-pr` | full regression, lint, typecheck, security, docs, thresholds |
