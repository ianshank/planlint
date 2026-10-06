# Change: Fix Heading Regex Newline Span (HNS)

> **Status: proposed.** Found by the 2026-10 peer-review deep dive and
> reproduced through the CLI at `6666444`. Same regex class as the
> `_bullet_decl` fix in `lint-empty-speckit-requirements`: a `\s` allowed to
> span a newline, so one line's declaration swallows the next line's text.
> That fix covered the bullet grammar and argued for a shared template so
> the next fix could not land on one copy and miss another. The heading
> grammar sat outside its scope and still carries the hole.

## Why

Every heading regex in `openspec_graph/parse_semantics.py` separates its
hashes from the heading's first token with `\s+`. Under `re.MULTILINE` the
anchors `^` and `$` become line-aware, but `\s` does not: it is a character
class, and `\n` is a member of it. So a line consisting of two hashes and
nothing else, followed by a line that happens to begin `Requirement:`, is
read as one requirement heading whose title is the next line's text. A
stray empty heading manufactures a requirement, and every rule that reads
requirements then reports on it.

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

`docs/eval-corpus-plan.md:324-328` predicted this exact shape while the
requirement-count property was being written: "the upstream `REQUIREMENT`
regex's `\s+` after the heading hashes can span a newline, so a bare `##`
line followed by a plain-prose `Requirement: x` line would count as a
heading. The generator never emits an empty heading, so it did not fire. Low
priority; noted for the next parser change." It is now reproduced through
the CLI with a false ERROR. It is a defect, not a note.

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
satisfy H006 for a harness spec that has no such section. A bare `##` line
before a prose line beginning with the word `ADDED` and the word
`Requirements` would satisfy U001 for a delta that declared no operation.
Those are the fail-open direction — a gate that passes when it should not —
which is worse than the false ERROR that was reproduced, and nothing today
would notice either.

The dialect classifiers (`is_upstream_marked`, `is_harness_marked`,
`is_speckit_marked`, `parse_semantics.py:155-166`) are substring tests on
literal heading strings and are unaffected. `GWT_SCENARIO` is `re.DOTALL` by
design — the comment block above it records why — and is a prose-scrape over
a numbered list item, not a heading regex; it is out of scope.

This repository's own tree carries no bare heading line
(`grep -rnE '^#{2,5}[[:space:]]*$' openspec docs README.md tests` is empty),
so the `validate` and `graph` golden hashes in
`tests/test_decomposition.py::_EXPECTED_HASHES` are expected not to move.
Expected is not confirmed: the tasks verify it rather than assume it.

## What Changes

- **`openspec_graph/parse_semantics.py`** — one module-level constant for
  the horizontal-whitespace class, `_HWS = r"[^\S\n]"` ("whitespace but not
  a newline", the idiom `_bullet_decl` and `FR_DECL_LOOSE` already use), and
  the `\s+` between the hashes and the first token becomes `{_HWS}+` in all
  six heading regexes: `SECTION`, `SUBSECTION`, `DELTA_HEADER`,
  `REQUIREMENT`, `SCENARIO`, `USER_STORY_HEADING`. Nothing else in any of
  the six moves: the hash ranges, the keyword alternations, the separator
  classes, the `(.+?)\s*$` tails and the flags are untouched. The title
  capture cannot cross a newline today (no `re.DOTALL`), so the gap between
  the hashes and the keyword was the whole hole. A comment beside the
  constant records why `re.MULTILINE` alone is not enough and points at
  `_bullet_decl`'s docstring for the "two copies, one fixed" history this is
  the fourth instance of.
- **`tests/test_heading_grammar.py`** (new, flat — `tests/AGENTS.md`
  forbids subdirectories) — for each of the six regexes, a hashes-only line
  followed by a keyword-shaped prose line yields no match, and the same
  heading with the keyword on the same line still does, including tabs and
  runs of spaces after the hashes, the colon, em-dash and hyphen separators,
  `REQ 12`-style numbering and mixed case. Then the three dialect-level
  shapes: the CLI reproduction inverted (an upstream delta with a bare `##`
  line before a prose `Requirement:` line validates clean and still yields
  exactly one requirement); a SpecKit document with a bare `##` line
  immediately before a success-criteria-shaped prose line acquires no
  phantom section; a harness spec with a bare `##` line before a prose line
  reading `Problem Statement` still reports H006. Plus a structural guard
  that no compiled pattern in the module anchored at `^#` places `\s`
  directly after its hash group, so a seventh heading regex cannot
  reintroduce the hole. Every test must fail at `6666444` before the regex
  change lands.
- **`tests/test_properties.py`** — `_upstream_spec` gains a `bare` kind
  that emits a line of two to five hashes (optionally with trailing spaces
  or a tab) and then, deliberately, a keyword-shaped prose line such as
  `Requirement: <title>` or `Scenario: <title>`, incrementing `declared` by
  nothing. The existing requirement-count property then covers the class on
  every run; `derandomize=True` stays, and no new property function is
  added, so the suite's own settings contract is unchanged.
- **`tests/test_decomposition.py`** — no edit. All three `_EXPECTED_HASHES`
  entries (`validate`, `graph`, `rules`) must be confirmed byte-identical;
  if any moves, that is the finding and this change stops until it is
  explained.
- **`CHANGELOG.md`** — one `Unreleased` / `Fixed` entry in the house style:
  what was wrong, how it was reproduced, what the fix is, and what it
  costs — nothing, since a line of bare hashes is never a declaration in any
  dialect this tool reads.
- **`docs/eval-corpus-plan.md`** — the Appendix C paragraph that predicted
  the defect gets a one-line note: reproduced through the CLI and fixed in
  `fix-heading-regex-newline-span`. The prediction and its "low priority"
  rating are left as written; a plan records what was foreseen and how it
  was rated.
- **`docs/peer-review-2026-10.md`** — not created and not edited. The
  deep-dive document is being written alongside this package and will
  reference it by name; editing it from inside the package it reports on
  would be a circular edit.

## Non-Goals

- **No change to the prose matchers or any accuracy floor.**
  `NEGATION_PATTERNS` and `NORMATIVE_MODAL` are not touched, so no `*_pct`
  floor in `pyproject.toml` moves. `make matcher-accuracy` is still run and
  reported, because the hook asks for it on any `parse_semantics.py` edit
  and running it is cheaper than arguing the exemption.
- **No change to `GWT_SCENARIO`.** Its `re.DOTALL` is deliberate — the
  one-clause-per-line Given/When/Then form it exists to catch is documented
  above it — and it is a prose-scrape, not a heading regex.
- **No new rule and no severity change.** A bare heading is a Markdown
  artifact, not a claim the spec makes about the repository; reporting it
  would be a style lint outside the tool's stated purpose, and the registry
  baseline, the generated skill catalog and the rule table in README stay
  untouched.
- **No general Markdown parser and no heading-level normalisation.** The
  fix is one character class in six regexes; a tokenizer would be a
  different change with a different blast radius.
- **No change to the dialect classifiers.** `is_upstream_marked`,
  `is_harness_marked` and `is_speckit_marked` are substring tests and were
  never affected.
- **No widening of what counts as a heading.** Setext underlines, hashes
  with no following whitespace, and hash runs outside the existing ranges
  did not match before and do not match after. The fix narrows; it never
  adds.

## Affected Capabilities

- `heading-grammar`
