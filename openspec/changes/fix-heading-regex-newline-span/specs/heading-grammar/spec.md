# Spec: Heading Grammar Newline Span (HNS)

> **Change:** `fix-heading-regex-newline-span`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

Every heading regex in `openspec_graph/parse_semantics.py` separates its
hashes from the heading's first token with `\s+`. Under `re.MULTILINE` the
anchors become line-aware but the class does not: `\s` includes `\n`, so a
line of bare hashes followed by a line that begins with the right keyword is
one heading whose title is the next line's text. A stray empty heading
manufactures a declaration, and every rule that reads declarations then
reports on it.

**Evidence:** `openspec_graph/parse_semantics.py:30-32` —

```python
REQUIREMENT = re.compile(
    r"^(#{2,4})\s+(?:Requirement|REQ\s*\d+)\s*[:—-]\s*(.+?)\s*$", re.MULTILINE | re.IGNORECASE
)
```

Reproduced at `6666444` through the CLI on an upstream-dialect target: a
delta file carrying the level-2 delta header, then a line holding only the
two characters `##`, then the prose line `Requirement: this is prose under
an empty heading, not a requirement`, then a real level-3 requirement with
two scenarios, one citing a real make target. `planlint validate --fail-on
INFO` reports `ERROR U002` at line 5 — `requirement 'REQ-1' (this is prose
under an empty heading, not a requirement...) has no Scenario` — plus
`WARN U004` at the same line (`uses no SHALL/MUST`) and `WARN U005`
(`requirements are at H2 (##), convention is H3`): `1 error · 2 warn`,
exit 1. Control: delete the bare `##` line and nothing else, and the same
file reports `0 error · 0 warn · 0 info`, `PASS`, exit 0. One empty heading
produced a false ERROR that blocks the gate and two false warnings, one of
them reporting drift at a heading level the author never used.

The same `\s+` sits in five more regexes in the same module — `SECTION`
(line 14), `SUBSECTION` (15), `DELTA_HEADER` (29), `SCENARIO` (33),
`USER_STORY_HEADING` (111) — and `SECTION` is the copy with the widest
reach: `section_span` and `speckit_section_span`
(`parse_semantics.py:485,533`) build every harness and SpecKit section span
from it, `ParsedSpec.sections` (`parse.py:167`) feeds H006's
required-sections check (`rules_harness.py:65-74`), and `hard_coded()` uses
it for its success-criteria exemption. A bare hash line before a prose line
reading `Problem Statement` would satisfy H006 for a spec that has no such
section. That is the fail-open direction, and nothing today would notice.

`docs/eval-corpus-plan.md:324-328` predicted this exact shape while the
requirement-count property was being written and rated it low priority
because "the generator never emits an empty heading". It is now reproduced
through the CLI with a false ERROR; it is a defect, not a note. The
`_bullet_decl` fix in `lint-empty-speckit-requirements` closed the same
regex class for the bullet grammar and established `[^\S\n]` as the idiom
(`parse_semantics.py:64-89`); the heading grammar was outside that fix's
scope and still carries the hole.

---

## Requirements

- R-HNS-1: In `openspec_graph/parse_semantics.py`, the whitespace between
  the leading hashes and the first token of a heading MUST be
  horizontal-only — the `[^\S\n]` class — in `SECTION`, `SUBSECTION`,
  `DELTA_HEADER`, `REQUIREMENT`, `SCENARIO` and `USER_STORY_HEADING`. It
  MUST NOT remain `\s+` in any of the six.
- R-HNS-2: A line consisting of hashes alone, with or without trailing
  horizontal whitespace, MUST match none of the six regexes, and the line
  after it MUST be read as ordinary prose. It MUST NOT yield a requirement,
  a scenario, a section, a subsection, a user story or a delta header,
  whatever the following line begins with.
- R-HNS-3: A heading whose keyword or title sits on the same line as its
  hashes MUST parse exactly as it does today: one or more spaces or tabs
  after the hashes, the colon, em-dash and hyphen separators, `REQ 12`-style
  numbering, and case-insensitive keywords where `re.IGNORECASE` is set
  today. Hash ranges, capture groups and flags MUST NOT change, and every
  rule that reads a real heading MUST behave as it does today.
- R-HNS-4: Heading-level drift MUST still be reported. A real level-2
  requirement heading MUST still produce U005's
  `requirements are at H2 (##), convention is H3`, a non-canonical scenario
  heading MUST still produce its U005 finding, and a real requirement with
  no scenario MUST still fail U002. `ParsedSpec.heading_drift` and
  `scenario_levels` MUST NOT change.
- R-HNS-5: The six regexes MUST share one definition of the
  horizontal-whitespace class — a module-level constant or a builder — and
  MUST NOT carry six hand-copied literals. A structural test MUST fail if
  any compiled pattern in the module anchored at `^#` places `\s` directly
  after its hash group.
- R-HNS-6: `tests/test_properties.py::_upstream_spec` MUST be extended to
  emit hashes-only lines (two to five hashes, optionally with trailing
  horizontal whitespace) followed by a keyword-shaped prose line, without
  incrementing the declared count. `derandomize=True` MUST stay and no new
  property function MAY be added.
- R-HNS-7: Each of the six regexes MUST have its own deterministic pair of
  assertions: a hashes-only line followed by a keyword-shaped prose line
  yields no match, and the same heading with the keyword on the same line
  still does. Every such test MUST fail at `6666444` before the regex change
  lands.
- R-HNS-8: Three dialect-level shapes MUST be pinned with their own
  fixtures: the CLI reproduction inverted (an upstream delta with a bare
  hash line before a prose `Requirement:` line validates clean and yields
  exactly one requirement); a SpecKit document with a bare hash line
  immediately before a success-criteria-shaped prose line acquires no
  section for it; a harness spec with a bare hash line before a prose line
  reading `Problem Statement` still reports H006 for the missing section.
- R-HNS-9: Behaviour preservation everywhere else MUST be measured, not
  assumed: `make matcher-accuracy` MUST be run and its per-pattern figures
  reported unchanged; `make validate` on this repository MUST report every
  package — 42 spec(s), the 41 at `6666444` plus this package's own — with
  `0 error · 0 warn · 0 info`; and all three `_EXPECTED_HASHES` entries in
  `tests/test_decomposition.py` MUST be byte-identical. None MAY be
  re-pinned by this change.
- R-HNS-10: `CHANGELOG.md` MUST gain an `Unreleased` / `Fixed` entry
  stating what was wrong, how it was reproduced, what the fix is and what it
  costs; `docs/eval-corpus-plan.md`'s Appendix C paragraph MUST gain a
  one-line note that the prediction was reproduced and fixed here, with the
  prediction itself left as written.
- C-HNS-1: This change MUST NOT alter `NEGATION_PATTERNS`,
  `NORMATIVE_MODAL` or any `*_pct` floor in `pyproject.toml`, and MUST NOT
  add a row under `tests/fixtures/phrasing/`.
- C-HNS-2: This change MUST NOT alter `GWT_SCENARIO`'s pattern or flags;
  `re.DOTALL` stays.
- C-HNS-3: This change MUST NOT add a rule or alter any rule's identifier,
  severity, dialect tuple or message. `tests/baseline_rules.json` and the
  generated skill catalog MUST be byte-identical.
- C-HNS-4: This change MUST NOT alter `is_upstream_marked`,
  `is_harness_marked` or `is_speckit_marked`.
- C-HNS-5: This change MUST NOT widen what counts as a heading. No line
  that fails to match any of the six regexes today MAY match after the
  change: setext underlines, hashes with no following whitespace, and hash
  runs outside each regex's existing range stay unmatched.
- C-HNS-6: This change MUST NOT create or edit
  `docs/peer-review-2026-10.md`.

---

## Decisions

- **DEC-HNS-001:** `[^\S\n]` rather than a literal space class or a second
  flag. `re.MULTILINE` changes only what `^` and `$` mean; `\s` is a
  character class and `\n` is a member of it, so under MULTILINE `^##\s+X`
  is still permitted to consume the line break between the hashes and `X`.
  No flag makes `\s` line-aware. `[^\S\n]` — "whitespace, but not a
  newline" — is the idiom `_bullet_decl`, `FR_DECL_LOOSE` and
  `_FENCED_BLOCK` already use in this module, so the fix reads as the
  module's own convention rather than a one-off. It keeps every other
  whitespace character `\s` accepts (tab, no-break space, form feed), so no
  heading that parses today stops parsing; and it excludes exactly the one
  character that defines a line boundary everywhere else in this module
  (`line_of`, every `re.MULTILINE` pattern). A literal space class would
  reject a tab after the hashes, which the current grammar accepts, and so
  would be a second defect in the other direction.
- **DEC-HNS-002:** one shared constant, `_HWS`, not a builder and not six
  literals. `_bullet_decl`'s docstring records the argument: "two copies,
  one fixed" has happened three times in this module, and a template makes
  the next fix structurally unable to land on one and miss another. The
  heading regexes are the fourth instance — the bullet fix landed while the
  headings a few lines above it kept the same `\s`. A builder was considered
  and rejected: the six patterns differ in hash range (`##`, `###`,
  `#{2,4}`, `#{3,5}`), in flags (three carry `re.IGNORECASE`) and in what
  they capture (a level group, a title, a story number, a delta verb), so a
  builder general enough for all six would be a second regex grammar to
  maintain, and a reader would have to expand it in their head to know what
  a pattern matches. A constant shares the one thing that was wrong and
  leaves each pattern legible on its own line. Its cost is that a constant
  cannot force itself to be used — a seventh heading regex written with
  `\s+` would compile — so R-HNS-5 pairs it with a structural test over the
  module's compiled patterns, which is the enforcement a template would
  have given for free.
- **DEC-HNS-003:** the whole family, `DELTA_HEADER` included, not
  `REQUIREMENT` alone. The reproduced defect is the upstream false ERROR,
  but `SECTION` is the more dangerous copy: it feeds `ParsedSpec.sections`,
  so a bare hash line before a prose line reading `Problem Statement`
  satisfies H006 for a harness spec that has no such section, and it feeds
  `section_span`, so the same construction before a prose line reading
  `Requirements` would make the harness parser read the following prose as
  the requirements span. `DELTA_HEADER` before a prose line beginning with
  the word `ADDED` and the word `Requirements` satisfies U001 for a delta
  that declared no operation. Those are fail-opens — a gate that passes when
  it should not — and this tool's stated purpose is to be the gate that does
  not. Fixing one copy and noting the other five would be exactly the event
  the module's own docstring warns against; fixing the family costs five
  more substitutions and leaves one idiom in the module.
- **DEC-HNS-004:** narrow, never widen; an empty heading is not an entry.
  The `_bullet_decl` fix chose `(.*?)` so an empty declaration became a
  recognised-but-empty requirement that S003 can report. The analogue here —
  treating a bare hash line as a heading with an empty title — was
  considered and rejected. A bullet carries an identifier that survives an
  empty body and is worth reporting on; a heading carries nothing but its
  title, so an empty one has no identity to attach a finding to and no rule
  reads it. CommonMark does admit an empty ATX heading, so in Markdown terms
  it is a heading; but in every dialect this tool reads, a heading is a
  declaration only when it carries a keyword or a title, and a bare line
  carries neither. The only hole was the gap between the hashes and the
  first token — `(.+?)` cannot cross a newline without `re.DOTALL`, and none
  of the six has it — so the fix changes exactly that gap. C-HNS-5 pins the
  direction: nothing matches after the change that did not match before.
- **DEC-HNS-005:** `GWT_SCENARIO` stays out. Its `re.DOTALL` is deliberate
  and documented in the comment block above it: the inner Given/When/Then
  spans must cross newlines to catch the one-clause-per-line SpecKit form,
  and a trailing lookahead rather than `\s*$` bounds the match. It is a
  prose-scrape over a numbered list item, not a heading regex, and it has
  no hashes for a bare line to consist of. Touching it here would be scope
  creep into a pattern whose newline behaviour is a feature.
- **DEC-HNS-006:** deterministic tests in a new flat module plus a
  generator extension, not one or the other. A deterministic test per regex
  names the pattern that regressed in its failure message, which is what a
  reader of a red CI log needs; the Hypothesis property covers the class for
  inputs nobody wrote down, which is what found the defect's shape in the
  first place (`docs/eval-corpus-plan.md:324-328`). The module is flat —
  `tests/test_heading_grammar.py`, never a `tests/` subdirectory — because
  `test_spec_test_citations.py` and `test_decomposition.py` glob
  `test_*.py` non-recursively and a subdirectory would silently orphan it
  from both gates (`tests/AGENTS.md`). It is a new module rather than more
  lines in `tests/test_graft_rules.py` because the subject is heading
  grammar across three dialects and `tests/AGENTS.md` splits by subject; the
  dialect-level shapes import `findings_for` from `tests/graft_support.py`
  the same way the graft modules do.
- **DEC-HNS-007:** the generator's new kind emits a keyword-shaped prose
  line on purpose, not random prose. `_prose` draws from a forty-character
  alphabet; the chance that a random draw begins `Requirement:` is
  negligible, so a bare line followed by random prose would exercise the
  generator's new branch without ever exercising the defect, and the
  property would pass at `6666444` — a test that cannot fail before the fix
  is not a test of the fix (`tests/AGENTS.md`). The new kind therefore
  writes the bare line and then a line of the form
  `<keyword><separator> <title>` with no hashes, drawn from the same keyword
  and separator sets the `req` kind uses, and increments `declared` by
  nothing. The bare line's hash count ranges two to five so every one of the
  six regexes' ranges is reached, and it optionally carries trailing spaces
  or a tab so the trailing-whitespace case of R-HNS-2 is covered.
  `_filler_title`'s existing filter is untouched: its job — a real filler
  heading must not start with a requirement keyword — is a different oracle
  concern. `derandomize=True` stays, per the module docstring: a gate that
  fails one run in fifty gets overridden and then deleted.
- **DEC-HNS-008:** `make matcher-accuracy` is run and reported even though
  no prose matcher changes. The hook in
  `.claude/hooks/nudge_rule_registry.sh` asks for it on any
  `parse_semantics.py` edit, and `docs/hooks.md` records why: a pattern
  change in that module is a change to a number. This change touches no
  pattern the matcher scores — `tools/matcher_accuracy.py` reads
  `Criterion.is_negative` and `Requirement.is_normative`, neither of which
  consults a heading regex — so the expected result is every figure
  unchanged and no `*_pct` floor in `pyproject.toml` moved. Running it costs
  seconds; it turns "no prose matcher is touched" from an assertion into a
  measurement, and if a figure does move, that is the finding.
- **DEC-HNS-009:** no new rule for "an empty heading was found", and no
  severity change anywhere. A bare hash line is a Markdown artifact — a
  template placeholder, a deleted title — not a claim the spec makes about
  the repository, and the rule families here read declarations: citations,
  identifiers, sections, scenarios. Reporting it would be a style lint
  outside the stated purpose of failing a build when a spec cites machinery
  the repository does not have. It would also carry the full registry-sync
  cost (`tests/baseline_rules.json`, the skill catalog, README's table,
  `c4.md`'s counts and ranges, `rules.py`'s docstring, a re-pinned `rules`
  hash) for a finding that changes no verdict. U005's severity and message
  are unchanged; after the fix it reports drift on real headings only, which
  is what it always claimed to do.
- **DEC-HNS-010:** the golden hashes are verified unchanged, never
  re-pinned. This repository's tree, its `tests/fixtures/` and its
  `tests/corpus/` carry no bare heading line (a grep for
  `^#{2,5}[[:space:]]*$` across all three is empty), so neither the parse of
  the canonical fixture nor `rules --json` has any reason to move. If one
  does, the change is not what this spec says it is, and the hash is the
  evidence; re-pinning would destroy it. Same clause the hook states for
  rules modules: if they moved, the change is not additive and that is the
  finding, not the hash.
- **DEC-HNS-011:** the plan's prediction is annotated, not rewritten, and
  the peer-review document is not touched. `docs/eval-corpus-plan.md` is a
  `*-plan.md` — written to be executed and retired (`docs/AGENTS.md`) — and
  its Appendix C paragraph is evidence that the defect was foreseen, rated
  low, and deferred on a stated reason ("the generator never emits an empty
  heading"). Rewriting that paragraph would erase the record that the rating
  was made and why it was wrong; a one-line note beside it preserves both.
  `docs/peer-review-2026-10.md` is being written alongside this package and
  will cite it by name; editing it from inside the package it reports on
  would make the package its own reviewer.

---

## Acceptance Criteria

- [ ] **AC-HNS-1 (non-success):** for each of `SECTION`, `SUBSECTION`,
  `DELTA_HEADER`, `REQUIREMENT`, `SCENARIO` and `USER_STORY_HEADING`, a line
  of hashes alone — plain, with trailing spaces, and with a trailing tab —
  followed by a line shaped like that regex's keyword and title yields no
  match; the following line is prose. (R-HNS-1, R-HNS-2, R-HNS-7)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-HNS-2:** for each of the six regexes, the same heading with its
  keyword on the same line as the hashes still matches, with one space,
  several spaces or a tab after the hashes, each separator the regex
  accepts, `REQ 12`-style numbering, and mixed case where `re.IGNORECASE` is
  set; the captured groups are unchanged. (R-HNS-3, R-HNS-7)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-HNS-3 (non-success):** the CLI reproduction, inverted — an
  upstream delta carrying the level-2 delta header, a bare hash line, a
  prose line beginning `Requirement:`, and one real level-3 requirement with
  two scenarios yields exactly one requirement, no U002, no U004 and no U005
  finding, and exits 0 under `--fail-on INFO`. (R-HNS-2, R-HNS-8)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-HNS-4 (non-success):** a real level-2 requirement heading, keyword
  on the same line, still parses and still reports U005 drift — the fix
  removes the phantom heading, never the drift report on a real one.
  (R-HNS-4)
  _Verified by:_ `pytest -k test_shallow_headings_are_parsed_and_reported_as_drift` · stage: `make test`

- [ ] **AC-HNS-5 (non-success):** a real requirement heading with no scenario
  still fails U002 at ERROR; the rule's true function is untouched.
  (R-HNS-4)
  _Verified by:_ `pytest -k test_u002_fires_on_a_requirement_with_no_scenario` · stage: `make test`

- [ ] **AC-HNS-6 (non-success):** a SpecKit document with a bare hash line
  immediately before a prose line reading `Success Criteria` acquires no
  section for it — `speckit_section_span` returns the empty span and no
  criterion is extracted from the prose below. (R-HNS-2, R-HNS-8)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-HNS-7 (non-success):** a harness spec with a bare hash line before
  a prose line reading `Problem Statement`, and no real Problem Statement
  heading, still reports H006 `missing required section: Problem Statement`;
  no phantom section satisfies the required-sections check. (R-HNS-2,
  R-HNS-8)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-HNS-8 (non-success):** H006 still fires on a harness spec whose
  required section is genuinely absent, unchanged by this change. (R-HNS-3)
  _Verified by:_ `pytest -k test_h006_fires_on_a_missing_required_section` · stage: `make test`

- [ ] **AC-HNS-9:** `_upstream_spec` emits bare hash lines followed by
  keyword-shaped prose, and the requirement-count property holds across its
  derandomized example set with the extended generator; at `6666444` the
  same generator finds a counterexample. (R-HNS-6)
  _Verified by:_ `pytest -k test_upstream_requirement_count_is_independent_of_heading_depth` · stage: `make test`

- [ ] **AC-HNS-10 (non-success):** the `validate`, `graph` and `rules` golden
  hashes in `tests/test_decomposition.py` are byte-identical before and
  after the change; none is re-pinned. (R-HNS-9, C-HNS-3)
  _Verified by:_ `pytest -k test_output_byte_identical` · stage: `make test`

- [ ] **AC-HNS-11 (non-success):** `make validate` against this repository
  reports every change package clean — `0 error · 0 warn · 0 info`, exit
  0 — with this package's own spec included in the count. (R-HNS-9)
  _Verified by:_ `make validate` · stage: `make validate`

- [ ] **AC-HNS-12 (non-success):** `make matcher-accuracy` reports the same
  per-pattern precision and recall for G002 and U004 before and after the
  change, and no `*_pct` floor in `pyproject.toml` and no row under
  `tests/fixtures/phrasing/` is touched. (R-HNS-9, C-HNS-1)
  _Verified by:_ `make matcher-accuracy` · stage: `make matcher-accuracy`

- [ ] **AC-HNS-13:** the six regexes resolve their horizontal-whitespace
  class from one shared definition, and a structural test fails if any
  compiled pattern in `parse_semantics.py` anchored at `^#` places `\s`
  directly after its hash group. (R-HNS-1, R-HNS-5)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-HNS-14 (non-success):** `GWT_SCENARIO`'s pattern and flags are
  unchanged — `re.DOTALL` is still set — and a Given/When/Then scenario
  spread across three lines still parses as one criterion. (C-HNS-2)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-HNS-15 (non-success):** no rule is added, re-severitied,
  re-scoped or re-worded — `tests/baseline_rules.json` matches `rules.RULES`
  without regeneration — and the three dialect classifiers are untouched.
  (C-HNS-3, C-HNS-4)
  _Verified by:_ `pytest -k test_rule_set_matches_baseline` · stage: `make test`

- [ ] **AC-HNS-16 (non-success):** nothing matches after the change that did
  not match before: a setext-underlined title, hashes with no following
  whitespace, and a hash run outside a regex's range are not headings to any
  of the six regexes. (C-HNS-5)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-HNS-17:** `CHANGELOG.md` carries the `Unreleased` / `Fixed` entry
  and `docs/eval-corpus-plan.md`'s Appendix C paragraph carries the one-line
  note with the prediction left as written; `docs/peer-review-2026-10.md`
  is neither created nor edited. No gate reads either entry's content, so
  this is confirmed by reading the diff; the stage proves the docs gate
  still passes with them in place. (R-HNS-10, C-HNS-6)
  _Verified by:_ `make pre-pr` · stage: `make pre-pr`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-HNS-1..10, AC-HNS-13..16 |
| Matcher | `make matcher-accuracy` | AC-HNS-12 — per-pattern figures unchanged, no floor moved |
| Self-check | `make validate` | AC-HNS-11 — this repository's packages, this one included, stay clean against the rules it describes |
| Full | `make pre-pr` | AC-HNS-17; full regression, lint, typecheck, security, docs, thresholds |
