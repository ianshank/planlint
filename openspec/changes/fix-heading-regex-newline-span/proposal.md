# Change: Fix Heading Regex Newline Span (HNS)

> **Status: proposed.** Found by the 2026-10 peer-review deep dive
> (`docs/peer-review-2026-10.md`, N1) and reproduced through the CLI at
> `6666444`. Same regex class as the `_bullet_decl` fix in
> `lint-empty-speckit-requirements`: a `\s` allowed to span a newline, so one
> line's declaration swallows the next line's text. That fix covered the
> bullet grammar and argued for a shared template so the next fix could not
> land on one copy and miss another. The heading grammar sat outside its
> scope and still carries the hole — in every `\s` of six regexes, not only
> the one after the hashes. Revised once after adversarial review; the
> closing section records what changed.

## Why

Every heading regex in `openspec_graph/parse_semantics.py` is written with
`\s`: between the hashes and the first token, on both sides of the
separator, inside `REQ\s*\d+`, after `User Story`, and in the trailing
`\s*$`. Under `re.MULTILINE` the anchors `^` and `$` become line-aware, but
`\s` does not: it is a character class, and `\n` is a member of it. So a
line consisting of two hashes and nothing else, followed by a line that
happens to begin `Requirement:`, is read as one requirement heading whose
title is the next line's text; and a `Requirement:` heading with no title is
read as one requirement whose title is whatever the next non-blank line
says — including the next real requirement heading, which then never exists.
A stray empty heading manufactures a declaration, and an empty-titled one
deletes the declaration after it.

**Evidence:** `openspec_graph/parse_semantics.py:30-32` is the upstream
requirement grammar —

```python
REQUIREMENT = re.compile(
    r"^(#{2,4})\s+(?:Requirement|REQ\s*\d+)\s*[:—-]\s*(.+?)\s*$", re.MULTILINE | re.IGNORECASE
)
```

Reproduced at `6666444` on an upstream-dialect target: a delta file carrying
the level-2 delta header, then a line holding only the two characters `##`,
then the prose line `Requirement: this is prose under an empty heading, not
a requirement`, then a real level-3 requirement heading with two scenarios,
one of which cites a real make target. `planlint validate --fail-on INFO`
reports:

| Finding | Message |
|---|---|
| `ERROR U002`, line 5 | `requirement 'REQ-1' (this is prose under an empty heading, not a requirement...) has no Scenario` |
| `WARN U004`, line 5 | `requirement '...' uses no SHALL/MUST` |
| `WARN U005` | `requirements are at H2 (##), convention is H3` |

`1 error · 2 warn`, exit 1. Control: delete the bare `##` line and nothing
else, and the same file reports `0 error · 0 warn · 0 info`, `PASS`, exit 0.
One empty heading produced a false ERROR that blocks the gate, a false
non-normative warning, and a false heading-drift warning — U005 reported
drift at a level the author never wrote a requirement at, because the
"requirement" is the bare `##` line itself.

**The hole is every `\s`, not the first one.** Adversarial review of this
package's first draft prototyped the other spans at `6666444`
(`openspec_graph/` is byte-unchanged since). Each row is one string with
`\n` written literally:

| Input | Result at `6666444` |
|---|---|
| `"### Requirement:\n\n### Requirement: Real one\n"` | **one** requirement, titled `Real one`; the second heading is never emitted — a fail-open U002 cannot see |
| `"### Requirement:\nThe system SHALL do X.\n"` | one requirement whose title is the prose line |
| `"### Scenario:\n\n### Scenario: Real\n"` | one scenario, not two |
| the delta verb `ADDED` on the header line, the word `Requirements` alone on the next | matches `DELTA_HEADER`; U001 is satisfied by a header nobody wrote |
| `"### Requirement\n: Title"` | matches; the separator came from the next line |
| `"##  \nProblem Statement"`, under a first-draft fix of the hash gap alone | still matches `SECTION`, title captured as a single space |

The last row is why the fix is not one character class in one position:
`SECTION` and `SUBSECTION` have no keyword after the gap, so `(.+?)` will
capture a trailing space as the title unless the title is required to begin
at a non-whitespace character. This is exactly the `_bullet_decl` defect
on the heading grammar, and the same cure applies: every span becomes
horizontal-only, and a keyworded heading with an empty title becomes a
recognised-but-empty entry rather than a line that swallows its successor.

`docs/eval-corpus-plan.md:324-331` predicted the bare-line shape while the
requirement-count property was being written ("the generator never emits an
empty heading, so it did not fire. Low priority") and, since `fa0a779`,
already records the CLI reproduction and names this package as the planned
fix. The paragraph's one remaining edit is "planned as" to "fixed in".

**The hole is a family, not one regex.** The same construction appears in
five more patterns in the same module, and several of them feed rules that
fail open rather than closed:

| Regex | Line | Consumers |
|---|---|---|
| `SECTION` | 14 | `section_span` (the harness `Requirements` and `Acceptance Criteria` spans, `parse_harness.py:20,31`); `speckit_section_span` (`parse_speckit.py:35,57`); `ParsedSpec.sections` (`parse.py:167`) and therefore H006's required-sections check (`rules_harness.py:65-74`); `hard_coded()`'s success-criteria exemption; the user-story block bound (`parse_speckit.py:76`) |
| `SUBSECTION` | 15 | `speckit_subsection_span` (`parse_speckit.py:36`) |
| `DELTA_HEADER` | 29 | `ParsedSpec.delta_headers` (`parse.py:174`) and therefore U001 |
| `REQUIREMENT` | 30-32 | `parse_upstream.py:12`; the dialect fallback at `parse.py:151` |
| `SCENARIO` | 33 | `parse_upstream.py:31`; `scenario_levels` (`parse_semantics.py:710-711`) and therefore U005's scenario half |
| `USER_STORY_HEADING` | 111 | `parse_speckit.py:75` |

A bare `##` line before a prose line reading `Problem Statement` would
satisfy H006 for a harness spec that has no such section. A split delta
header satisfies U001 for a delta that declared no operation. Those are the
fail-open direction — a gate that passes when it should not — which is worse
than the false ERROR that was reproduced, and nothing today would notice
either.

The dialect classifiers (`is_upstream_marked`, `is_harness_marked`,
`is_speckit_marked`, `parse_semantics.py:155-166`) are substring tests on
literal heading strings and are unaffected. `GWT_SCENARIO` is `re.DOTALL` by
design — the comment block above it records why — and is a prose-scrape over
a numbered list item, not a heading regex; it is out of scope.

This repository's own tree carries no bare heading line and no empty-titled
keyword heading (`grep -rnE '^#{2,5}[[:space:]]*$'` and a grep for a
`Requirement`/`REQ n`/`Scenario` heading whose separator ends the line are
both empty across `openspec`, `docs`, `README.md` and `tests`), so the
`validate`, `graph` and `rules` golden hashes in
`tests/test_decomposition.py::_EXPECTED_HASHES` are expected not to move.
Expected is not confirmed: the tasks verify it rather than assume it.

## What Changes

- **`openspec_graph/parse_semantics.py`** — one module-level constant for
  the horizontal-whitespace class, `_HWS = r"[^\S\n]"` ("whitespace but not
  a newline", the idiom `_bullet_decl` and `FR_DECL_LOOSE` already use), and
  **every** `\s` in the six heading regexes — `SECTION`, `SUBSECTION`,
  `DELTA_HEADER`, `REQUIREMENT`, `SCENARIO`, `USER_STORY_HEADING` — becomes
  that class: the gap after the hashes, both sides of the separator, inside
  `REQ\s*\d+`, after `User Story`, and the trailing `\s*$`. Two further
  edits close the shapes a horizontal class alone leaves open: in
  `REQUIREMENT` and `SCENARIO` the title capture `(.+?)` becomes `(.*?)`, so
  a keyworded heading with no title is a recognised-but-empty entry with
  text `""` instead of a line that swallows its successor (mirroring
  `_bullet_decl`'s `(.*?)`); in `SECTION` and `SUBSECTION` a `(?=\S)`
  lookahead precedes `(.+?)`, so a title must begin at a non-whitespace
  character and a bare line with two trailing spaces is not a section. Hash
  ranges, the keyword alternations, the separator classes, the number and
  order of capture groups, and the flags are untouched. A comment beside the
  constant records why `re.MULTILINE` alone is not enough and points at
  `_bullet_decl`'s docstring for the "two copies, one fixed" history this is
  the fourth instance of.
- **`tests/test_heading_grammar.py`** (new, flat — `tests/AGENTS.md`
  forbids subdirectories) — for each of the six regexes, a hashes-only line
  (plain, trailing spaces, trailing tab) followed by a keyword-shaped prose
  line yields no match, and the same heading with the keyword and a title on
  the same line still does, including tabs and runs of spaces after the
  hashes, the colon, em-dash and hyphen separators, `REQ 12`-style numbering
  and mixed case. Then the split-token shapes: an empty-titled requirement
  heading followed by a real one yields two requirements, the first with
  empty text (and the scenario analogue two scenarios); a delta header split
  across two lines is not a delta header and U001 fires; a separator, a
  `REQ` number or a `User Story` number on the next line does not match.
  Then the three dialect-level shapes: the CLI reproduction inverted (an
  upstream delta with a bare `##` line before a prose `Requirement:` line
  validates clean and still yields exactly one requirement); a SpecKit
  document with a bare `##` line immediately before a success-criteria-shaped
  prose line acquires no phantom section; a harness spec with a bare `##`
  line before a prose line reading `Problem Statement` still reports H006.
  Plus a structural guard: select every compiled pattern in the module with
  `re.match(r"\^\(?#", pattern.pattern)` — exactly the six — and assert the
  string `\s` appears nowhere in their source. The negative cases, the
  split-token cases and the three dialect-level tests must fail before the
  regex change lands; the same-line preservation cases pass before and after,
  by design.
- **`tests/test_properties.py`** — `_upstream_spec` gains two kinds. `bare`
  emits a line of two to five hashes (optionally with trailing spaces or a
  tab) and then, deliberately, a requirement-keyword-shaped prose line such
  as `Requirement: <title>` or `REQ 1: <title>`, drawn from the `req` kind's
  own keyword and separator sets, incrementing `declared` by nothing.
  `empty_req` emits a real requirement heading with the keyword and
  separator but no title, incrementing `declared` by one. The existing
  requirement-count property then covers both classes on every run — it
  exercises `REQUIREMENT` only, which is the regex the defect was reproduced
  in; `derandomize=True` stays, and no new property function is added, so the
  suite's own settings contract is unchanged.
- **`tests/test_decomposition.py`** — no edit. All three `_EXPECTED_HASHES`
  entries (`validate`, `graph`, `rules`) must be confirmed byte-identical;
  if any moves, that is the finding and this change stops until it is
  explained.
- **`CHANGELOG.md`** — one `Unreleased` / `Fixed` entry in the house style:
  what was wrong, how it was reproduced, what the fix is, and what it
  costs — nothing a passing spec relies on, since a line of bare hashes was
  never a declaration in any dialect this tool reads and an empty-titled
  keyword heading was only ever counted by stealing the next line.
- **`docs/eval-corpus-plan.md`** — lines 324-331 already carry the
  prediction, the CLI reproduction and the sentence "the fix is planned as
  `fix-heading-regex-newline-span`, across all six heading regexes"
  (`fa0a779`). The only edit is "planned as" to "fixed in". The prediction
  and its "low priority" rating are left as written; a plan records what
  was foreseen and how it was rated.
- **`docs/peer-review-2026-10.md`** — exists and already cites this package
  by name (lines 21, 355, 366). It is not edited from inside this package:
  it is the document that reports on the change, not a file of it.

## Non-Goals

- **No change to the prose matchers or any accuracy floor.**
  `NEGATION_PATTERNS` and `NORMATIVE_MODAL` are not touched, so no `*_pct`
  floor in `pyproject.toml` moves. `make matcher-accuracy` is still run and
  reported against the before-figures recorded in `tasks.md`, because the
  hook asks for it on any `parse_semantics.py` edit and running it is
  cheaper than arguing the exemption.
- **No change to `GWT_SCENARIO`.** Its `re.DOTALL` is deliberate — the
  one-clause-per-line Given/When/Then form it exists to catch is documented
  above it — and it is a prose-scrape, not a heading regex.
- **No new rule and no severity change.** A bare heading is a Markdown
  artifact, not a claim the spec makes about the repository; an empty-titled
  keyword heading is already reported by the rules that exist (U002 when no
  scenario follows, U004 when its body is not normative, U003 when its block
  has no WHEN/THEN), so no new identifier is needed, and the registry
  baseline, the generated skill catalog and the rule table in README stay
  untouched.
- **No general Markdown parser and no heading-level normalisation.** The
  fix is one character class, one lookahead and one quantifier in six
  regexes; a tokenizer would be a different change with a different blast
  radius.
- **No change to the dialect classifiers.** `is_upstream_marked`,
  `is_harness_marked` and `is_speckit_marked` are substring tests and were
  never affected.
- **No widening of what counts as a heading line beyond the one deliberate
  addition.** Setext underlines, hashes with no following whitespace, and
  hash runs outside the existing ranges did not match before and do not
  match after. The one shape newly recognised is the keyworded heading with
  an empty title, which today is either swallowed into the next line or
  unmatched at end of file; it is recognised so that it can be reported
  rather than so that it can pass.
- **No change to what text the heading regexes scan.** They read raw, not
  waiver-stripped, text, so a `Requirement:` heading written inside a
  multi-line waiver reason is still counted as a requirement. That is
  pre-existing and on record (DEC-SER-006 in
  `lint-empty-speckit-requirements`); this change neither fixes nor worsens
  it.

## Affected Capabilities

- `heading-grammar`

---

## Revision after adversarial review

The first draft fixed the gap after the hashes and claimed that gap was the
whole hole. `spec-adversary` showed it was not, with prototypes at
`6666444`; the design changed and the spec was rewritten to match, not
annotated.

- **Superseded: "the gap between the hashes and the keyword was the whole
  hole."** Every `\s` in the six regexes spans a newline — both sides of the
  separator, inside `REQ\s*\d+`, after `User Story`, the trailing `\s*$`. An
  empty-titled `Requirement:` heading consumed the next real requirement
  heading, so the document lost a requirement and U002 could not see it;
  the delta verb and the word `Requirements` on separate lines satisfied
  U001. Shipped instead: every `\s` becomes the shared horizontal class, and
  the keyworded title captures become `(.*?)` so an empty title is a
  recognised-but-empty entry — the `_bullet_decl` resolution, applied to the
  heading grammar (R-HNS-1, R-HNS-11, R-HNS-12, DEC-HNS-004).
- **Superseded: a horizontal class alone for `SECTION`/`SUBSECTION`.** With
  no keyword after the gap, `(.+?)` captured a trailing space as the title,
  so a bare `##` line with two trailing spaces was still a section. Shipped
  instead: a `(?=\S)` lookahead before the title capture, which keeps the
  capture groups byte-identical (DEC-HNS-012).
- **Corrected: the structural guard's predicate.** "Source begins with
  `^#`" missed `REQUIREMENT` and `SCENARIO`, whose source begins `^(#`. The
  guard now selects with `re.match(r"\^\(?#", ...)` and asserts `\s` appears
  nowhere in the six patterns' source (R-HNS-5).
- **Corrected: three stale statements.** `docs/eval-corpus-plan.md` already
  carries the reproduction note; `docs/peer-review-2026-10.md` already
  exists; and a hard-coded spec count in the self-check line was already
  wrong by the time it was written. The fail-first requirement is scoped to
  the cases that can fail before the fix, and the property's filler is
  described as exercising `REQUIREMENT` only.
