# Spec: Heading Grammar Newline Span (HNS)

> **Change:** `fix-heading-regex-newline-span`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

---

## Problem Statement

Every heading regex in `openspec_graph/parse_semantics.py` is written with
`\s` — between the hashes and the first token, on both sides of the
separator, inside `REQ\s*\d+`, after `User Story`, and in the trailing
`\s*$`. Under `re.MULTILINE` the anchors become line-aware but the class
does not: `\s` includes `\n`, so any of those spans may cross a line break.
A line of bare hashes followed by a line that begins with the right keyword
is one heading whose title is the next line's text; a `Requirement:` heading
with no title is one heading whose title is the next non-blank line — even
when that line is the next real requirement heading. A stray empty heading
manufactures a declaration, and an empty-titled one deletes the declaration
after it.

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

Adversarial review of this package's first draft prototyped the other spans
at `6666444` (`openspec_graph/` byte-unchanged since), each a single string
with `\n` written literally: `"### Requirement:\n\n### Requirement: Real
one\n"` parses as **one** requirement titled `Real one` — the second heading
is never emitted, a fail-open U002 cannot see; `"### Requirement:\nThe
system SHALL do X.\n"` takes the prose line as its title; a level-3
`Scenario:` heading with no title followed by a real one yields one
scenario, not two; the delta verb `ADDED` on one line and the word
`Requirements` on the next matches `DELTA_HEADER`; `"### Requirement\n:
Title"` matches with the separator borrowed from the next line. And under a
first-draft fix that made only the hash gap horizontal,
`"##  \nProblem Statement"` still matched `SECTION` with the title captured
as a single space, because `(.+?)` has no keyword in front of it and will
take a space as a title.

The same `\s` sits in five more regexes in the same module — `SECTION`
(line 14), `SUBSECTION` (15), `DELTA_HEADER` (29), `SCENARIO` (33),
`USER_STORY_HEADING` (111) — and `SECTION` is the copy with the widest
reach: `section_span` and `speckit_section_span`
(`parse_semantics.py:485,533`) build every harness and SpecKit section span
from it, `ParsedSpec.sections` (`parse.py:167`) feeds H006's
required-sections check (`rules_harness.py:65-74`), and `hard_coded()` uses
it for its success-criteria exemption. A bare hash line before a prose line
reading `Problem Statement` would satisfy H006 for a spec that has no such
section. That is the fail-open direction, and nothing today would notice.

`docs/eval-corpus-plan.md:324-331` predicted the bare-line shape while the
requirement-count property was being written, rated it low priority because
"the generator never emits an empty heading", and since `fa0a779` records
the CLI reproduction and names this package as the planned fix. The
`_bullet_decl` fix in `lint-empty-speckit-requirements` closed the same
regex class for the bullet grammar and established `[^\S\n]` as the idiom
and `(.*?)` as the answer to an empty declaration (`parse_semantics.py:
64-89`); the heading grammar was outside that fix's scope and still carries
the hole.

---

## Requirements

- R-HNS-1: In `openspec_graph/parse_semantics.py`, every `\s` in `SECTION`,
  `SUBSECTION`, `DELTA_HEADER`, `REQUIREMENT`, `SCENARIO` and
  `USER_STORY_HEADING` MUST become the shared horizontal-whitespace class
  `[^\S\n]` — the gap after the hashes, both sides of the separator, inside
  `REQ\s*\d+`, after `User Story`, and the trailing `\s*$`. The string `\s`
  MUST NOT remain anywhere in any of the six patterns' source.
- R-HNS-2: A line consisting of hashes alone, with or without trailing
  horizontal whitespace of any length, MUST match none of the six regexes,
  and the line after it MUST be read as ordinary prose. It MUST NOT yield a
  requirement, a scenario, a section, a subsection, a user story or a delta
  header, whatever the following line begins with. For `SECTION` and
  `SUBSECTION`, whose first token after the gap is the title itself, this
  requires the title capture to begin at a non-whitespace character; a
  horizontal class in the gap alone is not sufficient.
- R-HNS-3: A heading whose keyword and a non-empty title sit on the same
  line as its hashes MUST parse exactly as it does today: one or more spaces
  or tabs after the hashes, the colon, em-dash and hyphen separators,
  `REQ 12`-style numbering, and case-insensitive keywords where
  `re.IGNORECASE` is set today. Hash ranges, the number and order of capture
  groups, and flags MUST NOT change, and every rule that reads a real
  heading MUST behave as it does today. The match end MAY move back across
  the heading's trailing newline run — the old trailing `\s*$` consumed it,
  the horizontal class does not — so `Requirement.body` and the
  section-span bodies MAY gain a leading newline that no consumer reads;
  a test of this requirement MUST compare captured groups, not whole match
  spans or whole `Requirement` values.
- R-HNS-4: Heading-level drift MUST still be reported. A real level-2
  requirement heading MUST still produce U005's
  `requirements are at H2 (##), convention is H3`, a non-canonical scenario
  heading MUST still produce its U005 finding, and a real requirement with
  no scenario MUST still fail U002. `ParsedSpec.heading_drift` and
  `scenario_levels` MUST NOT change.
- R-HNS-5: The six regexes MUST share one definition of the
  horizontal-whitespace class — a module-level constant or a builder — and
  MUST NOT carry hand-copied literals. A structural test MUST select every
  compiled pattern in the module whose source satisfies
  `re.match(r"\^\(?#", pattern.pattern)`, MUST assert that selection is
  exactly the six, and MUST assert the string `\s` appears nowhere in their
  source. The check is case-sensitive: `\S` inside `[^\S\n]` and `(?=\S)`
  is not `\s`.
- R-HNS-6: `tests/test_properties.py::_upstream_spec` MUST be extended with
  two kinds: `bare`, which emits a hashes-only line (two to five hashes,
  optionally with trailing horizontal whitespace) followed by a
  requirement-keyword-shaped prose line and increments the declared count by
  nothing; and `empty_req`, which emits a requirement heading with keyword
  and separator but no title and increments it by one. `derandomize=True`
  MUST stay and no new property function MAY be added.
- R-HNS-7: Each of the six regexes MUST have its own deterministic pair of
  assertions: a hashes-only line followed by a keyword-shaped prose line
  yields no match, and the same heading with the keyword and a title on the
  same line still does. The negative half, the split-token cases of
  R-HNS-11 and R-HNS-12, and the three dialect-level shapes of R-HNS-8 MUST
  fail before the regex change lands; the same-line preservation half passes
  before and after, by design.
- R-HNS-8: Three dialect-level shapes MUST be pinned with their own
  fixtures: the CLI reproduction inverted (an upstream delta with a bare
  hash line before a prose `Requirement:` line validates clean and yields
  exactly one requirement); a SpecKit document with a bare hash line
  immediately before a success-criteria-shaped prose line acquires no
  section for it; a harness spec with a bare hash line before a prose line
  reading `Problem Statement` still reports H006 for the missing section.
- R-HNS-9: Behaviour preservation everywhere else MUST be measured, not
  assumed: `make matcher-accuracy` MUST be run and its per-pattern figures
  reported unchanged against the before-figures recorded in `tasks.md`;
  `make validate` on this repository MUST report every package present in
  the tree when this lands, this one included, at
  `0 error · 0 warn · 0 info`, exit 0; and all three `_EXPECTED_HASHES`
  entries in `tests/test_decomposition.py` MUST be byte-identical. None MAY
  be re-pinned by this change.
- R-HNS-10: `CHANGELOG.md` MUST gain an `Unreleased` / `Fixed` entry
  stating what was wrong, how it was reproduced, what the fix is and what it
  costs. In `docs/eval-corpus-plan.md` lines 324-331, which already record
  the prediction, the reproduction and "the fix is planned as
  `fix-heading-regex-newline-span`", the words "planned as" MUST become
  "fixed in" and nothing else in that paragraph MAY change.
- R-HNS-11: A keyworded heading whose title is empty — `Requirement:`,
  `REQ n:` or `Scenario:` followed by nothing or by trailing horizontal
  whitespace only — MUST be a recognised-but-empty entry with text `""` and
  MUST NOT consume the following line. An empty-titled requirement heading
  followed by a real requirement heading MUST yield two requirements, the
  first with empty text; an empty-titled scenario heading followed by a real
  one MUST yield two scenarios. The existing rules MUST report the empty
  entry on its own merits: U002 when no scenario follows it, U004 when its
  body carries no modal, U003 when its block carries no WHEN or THEN.
- R-HNS-12: Tokens split across lines MUST NOT assemble into a heading: the
  delta verb on one line and the word `Requirements` on the next MUST NOT be
  a delta header, and U001 MUST fire on a delta whose only header is split
  that way; a keyword on one line and its separator on the next MUST NOT
  match `REQUIREMENT` or `SCENARIO`; `REQ` with its number on the next line
  MUST NOT match; `User Story` with its number on the next line MUST NOT
  match.
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
- C-HNS-5: This change MUST NOT widen what counts as a heading line beyond
  the recognised-but-empty keyword heading of R-HNS-11. Setext underlines,
  hashes with no following whitespace, and hash runs outside each regex's
  existing range MUST stay unmatched, and no bare-hash line MAY become a
  heading of any kind.
- C-HNS-6: This change MUST NOT edit `docs/peer-review-2026-10.md`, which
  exists and cites this package by name.

---

## Decisions

- **DEC-HNS-001:** `[^\S\n]` rather than a literal space class or a second
  flag. `re.MULTILINE` changes only what `^` and `$` mean; `\s` is a
  character class and `\n` is a member of it, so under MULTILINE every
  `\s+` and `\s*` in a heading pattern is permitted to consume a line break.
  No flag makes `\s` line-aware. `[^\S\n]` — "whitespace, but not a
  newline" — is the idiom `_bullet_decl`, `FR_DECL_LOOSE` and
  `_FENCED_BLOCK` already use in this module, so the fix reads as the
  module's own convention rather than a one-off. It keeps every other
  whitespace character `\s` accepts (tab, no-break space, form feed), so no
  same-line heading that parses today stops parsing; and it excludes exactly
  the one character that defines a line boundary everywhere else in this
  module (`line_of`, every `re.MULTILINE` pattern). A literal space class
  would reject a tab after the hashes, which the current grammar accepts,
  and so would be a second defect in the other direction.
- **DEC-HNS-002:** one shared constant, `_HWS`, not a builder and not
  literals. `_bullet_decl`'s docstring records the argument: "two copies,
  one fixed" has happened three times in this module, and a template makes
  the next fix structurally unable to land on one and miss another. The
  heading regexes are the fourth instance — the bullet fix landed while the
  headings a few lines above it kept the same `\s` — and after adversarial
  review the constant is interpolated a dozen times across the six, which
  makes the case for sharing stronger, not weaker. A builder was considered
  and rejected: the six patterns differ in hash range (`##`, `###`,
  `#{2,4}`, `#{3,5}`), in flags (three carry `re.IGNORECASE`), in what they
  capture (a level group, a title, a story number, a delta verb) and now in
  shape (a lookahead in two, an optional title in two), so a builder general
  enough for all six would be a second regex grammar to maintain. A constant
  shares the one thing that was wrong and leaves each pattern legible on its
  own line. Its cost is that a constant cannot force itself to be used — a
  seventh heading regex written with `\s` would compile — so R-HNS-5 pairs
  it with a structural test over the module's compiled patterns, which is
  the enforcement a template would have given for free. The selection
  predicate is `re.match(r"\^\(?#", pattern.pattern)`, because two of the
  six begin `^(#` and a "begins with `^#`" test misses exactly the regex the
  defect was reproduced in; the assertion is that `\s` appears nowhere in
  the selected sources, which is simpler and stronger than checking the
  position after the hash group.
  The selector reaches the two shapes this module uses today, `^#` and
  `^(#`; a heading regex written another way would have to be added to
  it, so "exactly the six" is a statement about this module now, not
  about every heading regex forever.
- **DEC-HNS-003:** the whole family, `DELTA_HEADER` included, not
  `REQUIREMENT` alone. The reproduced defect is the upstream false ERROR,
  but `SECTION` is the more dangerous copy: it feeds `ParsedSpec.sections`,
  so a bare hash line before a prose line reading `Problem Statement`
  satisfies H006 for a harness spec that has no such section, and it feeds
  `section_span`, so the same construction before a prose line reading
  `Requirements` would make the harness parser read the following prose as
  the requirements span. `DELTA_HEADER` with its verb and the word
  `Requirements` on separate lines satisfies U001 for a delta that declared
  no operation. Those are fail-opens — a gate that passes when it should
  not — and this tool's stated purpose is to be the gate that does not.
  Fixing one copy and noting the other five would be exactly the event the
  module's own docstring warns against. `add-speckit-dialect`'s C-SK-8
  ("G002/G003's existing behavior for the harness and upstream dialects MUST
  be byte-unchanged by this change") and the `speckit_section_body`
  docstring that cites it (`parse_semantics.py:526-528`) do not bind here:
  C-SK-8 is a constraint on that change, not a standing invariant, and a
  bare-hash line was never a section in any dialect, so no behaviour a
  passing harness or upstream spec relies on moves — the golden hashes
  (R-HNS-9) are the measurement of that claim.
- **DEC-HNS-004:** a bare-hash line is never a heading; a keyworded heading
  with an empty title is a recognised-but-empty entry. The first draft of
  this package claimed the gap after the hashes was the whole hole, because
  `(.+?)` cannot cross a newline without `re.DOTALL`. That was false: the
  `\s*` on either side of the separator and the trailing `\s*$` cross
  newlines just as freely, so `Requirement:` with no title took the next
  line — a prose sentence, or the next real requirement heading, which then
  vanished from the document and from U002's view. That is the
  `_bullet_decl` defect exactly, and `_bullet_decl`'s resolution applies:
  every span becomes horizontal, and the title capture becomes `(.*?)` so an
  empty title is a recognised-but-empty entry rather than a swallow. The
  two cases are deliberately different. A line of bare hashes carries
  nothing — no keyword, no title, no identity to attach a finding to — and
  CommonMark's empty ATX heading is still not a declaration in any dialect
  this tool reads, so it matches none of the six. A `Requirement:` or
  `Scenario:` heading with no title carries its keyword; the author declared
  something and left it blank, which is a diagnosable state: U002 reports it
  when no scenario follows, U004 when its body has no modal, U003 when its
  block has no WHEN or THEN — the same way S003 reports an empty FR bullet.
  Recognising it costs nothing a passing spec relies on, because today that
  heading was counted either by stealing the next line or with a
  whitespace-only title, never on its own terms. C-HNS-5 pins the
  boundary: this is the one shape newly recognised, and nothing else matches
  after the change that did not match before.
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
  first place (`docs/eval-corpus-plan.md:324-331`). The module is flat —
  `tests/test_heading_grammar.py`, never a `tests/` subdirectory — because
  `test_spec_test_citations.py` and `test_decomposition.py` glob
  `test_*.py` non-recursively and a subdirectory would silently orphan it
  from both gates (`tests/AGENTS.md`). It is a new module rather than more
  lines in `tests/test_graft_rules.py` because the subject is heading
  grammar across three dialects and `tests/AGENTS.md` splits by subject; the
  dialect-level shapes import `findings_for` from `tests/graft_support.py`
  the same way the graft modules do.
- **DEC-HNS-007:** the generator's new kinds are shaped to the regex the
  property can see. The requirement-count property reads `parse_upstream`'s
  requirement tuple, so it exercises `REQUIREMENT` only — a `Scenario:`
  filler is inert for it, and `SECTION`, `SUBSECTION`, `DELTA_HEADER`,
  `USER_STORY_HEADING` are covered by the deterministic tests alone. The
  `bare` kind therefore writes the bare line and then a line of the form
  `<keyword><separator> <title>` with no hashes, drawn from the `req` kind's
  own keyword and separator sets (`Requirement`, `REQ 1`, `REQ7`, the colon,
  em-dash and hyphen), and increments `declared` by nothing; `_prose` draws
  from a forty-character alphabet and the chance that a random draw begins
  `Requirement:` is negligible, so random prose would exercise the branch
  without exercising the defect, and a test that cannot fail before the fix
  is not a test of the fix (`tests/AGENTS.md`). The `empty_req` kind writes
  a real requirement heading with keyword and separator and no title and
  increments `declared` by one: before the fix, when the next element is a
  requirement heading the parser counts one where two were declared, so the
  property fails; after the fix it counts two. The bare line's hash count
  ranges two to five so every regex's range is reached, and it optionally
  carries trailing spaces or a tab so R-HNS-2's trailing-whitespace case is
  covered. `_filler_title`'s existing filter is untouched: its job — a real
  filler heading must not start with a requirement keyword — is a different
  oracle concern. `derandomize=True` stays, per the module docstring: a gate
  that fails one run in fifty gets overridden and then deleted.
- **DEC-HNS-008:** `make matcher-accuracy` is run and reported even though
  no prose matcher changes — as the report it is, never as a stage a
  criterion cites: DEC-PM-011 (`fix-prose-matcher-precision`) makes it a
  report target composed into neither `ci` nor `pre-pr`, with
  `tests/test_matcher_accuracy.py` inside the test stage as the gate, and
  AC-HNS-12 cites that gate. The hook in
  `.claude/hooks/nudge_rule_registry.sh` asks for it on any
  `parse_semantics.py` edit, and `docs/hooks.md` records why: a pattern
  change in that module is a change to a number. This change touches no
  pattern the matcher scores — `tools/matcher_accuracy.py` reads
  `Criterion.is_negative` and `Requirement.is_normative`, neither of which
  consults a heading regex — so the expected result is every figure equal to
  the before-figures recorded in `tasks.md` and no `*_pct` floor in
  `pyproject.toml` moved. Running it costs seconds; it turns "no prose
  matcher is touched" from an assertion into a measurement, and if a figure
  does move, that is the finding.
- **DEC-HNS-009:** no new rule for "an empty heading was found", and no
  severity change anywhere. A bare hash line is a Markdown artifact — a
  template placeholder, a deleted title — not a claim the spec makes about
  the repository, and the rule families here read declarations: citations,
  identifiers, sections, scenarios. Reporting it would be a style lint
  outside the stated purpose of failing a build when a spec cites machinery
  the repository does not have. An empty-titled keyword heading, by
  contrast, is already reported by the rules that exist once it is parsed
  honestly (R-HNS-11), so it needs no new identifier either. A new rule
  would also carry the full registry-sync cost (`tests/baseline_rules.json`,
  the skill catalog, README's table, `c4.md`'s counts and ranges,
  `rules.py`'s docstring, a re-pinned `rules` hash) for a finding that
  changes no verdict. U005's severity and message are unchanged; after the
  fix it reports drift on real headings only, which is what it always
  claimed to do.
- **DEC-HNS-010:** the golden hashes are verified unchanged, never
  re-pinned. This repository's tree, its `tests/fixtures/` and its
  `tests/corpus/` carry no bare heading line and no empty-titled keyword
  heading (a grep for `^#{2,5}[[:space:]]*$` and a grep for a
  `Requirement`/`REQ n`/`Scenario` heading whose separator ends the line are
  both empty), so neither the parse of the canonical fixture nor
  `rules --json` has any reason to move. If one does, the change is not
  what this spec says it is, and the hash is the evidence; re-pinning would
  destroy it. Same clause the hook states for rules modules: if they moved,
  the change is not additive and that is the finding, not the hash.
- **DEC-HNS-011:** the plan's existing note is amended by two words, and
  the peer-review document is not touched. `docs/eval-corpus-plan.md` is a
  `*-plan.md` — written to be executed and retired (`docs/AGENTS.md`) — and
  its Appendix C paragraph is evidence that the defect was foreseen, rated
  low, deferred on a stated reason, and then reproduced; since `fa0a779` it
  already says so and names this package as the planned fix. The only
  honest edit once the fix lands is "planned as" to "fixed in". Rewriting
  the paragraph would erase the record that the rating was made and why it
  was wrong. `docs/peer-review-2026-10.md` exists and cites this package by
  name at lines 21, 355 and 366; editing it from inside the package it
  reports on would make the package its own reviewer.
- **DEC-HNS-012:** `(?=\S)` before `(.+?)` in `SECTION` and `SUBSECTION`,
  rather than `(\S.*?)`. Both make a title begin at a non-whitespace
  character, which is what closes the trailing-spaces hole: with only a
  horizontal class in the gap, `"##  \nProblem Statement"` still matched,
  with `[^\S\n]+` taking one space and `(.+?)` taking the other as the
  title. The lookahead is chosen because it leaves the capture group's own
  pattern byte-identical, so `section_span`, `speckit_section_span`,
  `ParsedSpec.sections` and every `m.group(1)` consumer read exactly the
  text they read today for every real heading (R-HNS-3); `(\S.*?)` would
  read the same text but by a different route, which is one more thing a
  reviewer has to prove equivalent. The keyworded four do not need it: a
  literal keyword follows their gap, and a space is not a keyword.
  One side effect is recorded so an implementer does not "fix" it: the old
  trailing `\s*$` greedily consumed the heading's newline run, so `m.end()`
  sat after it; `[^\S\n]*$` stops before it. `Requirement.body` and the
  `section_span`/`speckit_section_span`/`speckit_subsection_span` bodies
  therefore gain a leading newline (a heading on a file's last line goes from
  body `""` to `"\n"`). Verified across every markdown file in the tree: no
  finding, section name, text or line moves — loci are `origin + m.start()`,
  `is_normative` is whitespace-insensitive, and nothing tests a body for
  truthiness — so DEC-LH-006's offset contract holds. Groups are
  byte-identical; match spans are not, and R-HNS-3's test compares groups.

---

## Acceptance Criteria

- [ ] **AC-HNS-1 (non-success):** for each of `SECTION`, `SUBSECTION`,
  `DELTA_HEADER`, `REQUIREMENT`, `SCENARIO` and `USER_STORY_HEADING`, a line
  of hashes alone — plain, with two or more trailing spaces, and with a
  trailing tab — followed by a line shaped like that regex's keyword and
  title yields no match; the following line is prose. (R-HNS-1, R-HNS-2,
  R-HNS-7)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-HNS-2:** for each of the six regexes, the same heading with its
  keyword and a title on the same line as the hashes still matches, with one
  space, several spaces or a tab after the hashes, each separator the regex
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
  and title on the same line, still parses and still reports U005 drift —
  the fix removes the phantom heading, never the drift report on a real one.
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
  requirement-keyword-shaped prose and empty-titled requirement headings,
  and the requirement-count property holds across its derandomized example
  set with the extended generator; before the regex change lands, the same
  generator finds a counterexample. (R-HNS-6)
  _Verified by:_ `pytest -k test_upstream_requirement_count_is_independent_of_heading_depth` · stage: `make test`

- [ ] **AC-HNS-10 (non-success):** the `validate`, `graph` and `rules` golden
  hashes in `tests/test_decomposition.py` are byte-identical before and
  after the change; none is re-pinned. (R-HNS-9, C-HNS-3)
  _Verified by:_ `pytest -k test_output_byte_identical` · stage: `make test`

- [ ] **AC-HNS-11 (non-success):** `make validate` against this repository
  reports every change package present in the tree when this lands, this one
  included, at `0 error · 0 warn · 0 info`, exit 0. (R-HNS-9)
  _Verified by:_ `make validate` · stage: `make validate`

- [ ] **AC-HNS-12 (non-success):** `make matcher-accuracy` reports the same
  per-pattern precision and recall for G002 and U004 as the before-figures
  recorded in `tasks.md`, and no `*_pct` floor in `pyproject.toml` and no
  row under `tests/fixtures/phrasing/` is touched. The report target is the
  measurement; the gate that enforces the floors is
  `tests/test_matcher_accuracy.py` inside the test stage (DEC-PM-011).
  (R-HNS-9, C-HNS-1, DEC-HNS-008)
  _Verified by:_ `pytest -k test_matcher_accuracy` · stage: `make test`

- [ ] **AC-HNS-13:** the six regexes resolve their horizontal-whitespace
  class from one shared definition, and a structural test selects every
  compiled pattern in `parse_semantics.py` matching
  `re.match(r"\^\(?#", pattern.pattern)`, asserts that selection is exactly
  the six, and asserts the string `\s` appears nowhere in their source.
  (R-HNS-1, R-HNS-5)
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
  not match before, except the keyworded empty-titled heading R-HNS-11
  deliberately recognises: a setext-underlined title, hashes with no
  following whitespace, and a hash run outside a regex's range are not
  headings to any of the six regexes, and no bare-hash line is a heading of
  any kind. (C-HNS-5)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-HNS-17:** `CHANGELOG.md` carries the `Unreleased` / `Fixed` entry;
  `docs/eval-corpus-plan.md` lines 324-331 read "fixed in" where they read
  "planned as" and are otherwise unchanged; `docs/peer-review-2026-10.md`
  is not edited. No gate reads either entry's content, so this is confirmed
  by reading the diff; the stage proves the docs gate still passes with them
  in place. (R-HNS-10, C-HNS-6)
  _Verified by:_ `make pre-pr` · stage: `make pre-pr`

- [ ] **AC-HNS-18:** an empty-titled requirement heading followed by a real
  requirement heading yields two requirements, the first with text `""` and
  the second with its own title; an empty-titled scenario heading followed
  by a real one yields two scenarios. (R-HNS-11)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-HNS-19 (non-success):** the delta verb on one line and the word
  `Requirements` on the next is not a delta header, and U001 fires on an
  upstream delta whose only header is split that way — the honest outcome.
  (R-HNS-12)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-HNS-20 (non-success):** a keyword with its separator on the next
  line does not match `REQUIREMENT` or `SCENARIO`, `REQ` with its number on
  the next line does not match, and `User Story` with its number on the next
  line does not match. (R-HNS-12)
  _Verified by:_ `make test` · stage: `make test`

- [ ] **AC-HNS-21 (non-success):** an empty-titled requirement heading whose
  body carries no modal is reported by U004, one with no scenario after it
  is reported by U002, and an empty-titled scenario whose block carries no
  WHEN or THEN is reported by U003 — recognised-but-empty is diagnosable,
  never silent, as S003 reports an empty FR bullet. (R-HNS-11)
  _Verified by:_ `make test` · stage: `make test`

---

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-HNS-1..10, AC-HNS-13..16, AC-HNS-18..21 |
| Matcher | `make test` | AC-HNS-12 — `tests/test_matcher_accuracy.py` holds every floor; `make matcher-accuracy`, run by hand per the hook, reports per-pattern figures equal to the before-figures in `tasks.md` |
| Self-check | `make validate` | AC-HNS-11 — every package in the tree, this one included, stays clean against the rules it describes |
| Full | `make pre-pr` | AC-HNS-17; full regression, lint, typecheck, security, docs, thresholds |
