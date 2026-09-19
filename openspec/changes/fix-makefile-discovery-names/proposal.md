# Change: Fix Makefile Discovery by Name (`GNUmakefile`, `makefile`)

## Why

`detect._make_target_facts` looks for exactly one filename:

```python
makefile = root / "Makefile"
if not makefile.exists():
    return machinery.MakefileFacts((), False, False, 0)
```

GNU Make's documented search order is `GNUmakefile`, then `makefile`, then
`Makefile`, and it uses the **first** one that exists — so `GNUmakefile`
takes precedence over `Makefile` where both are present. A target
repository using either of the first two names reports `make targets 0
found`, which trips G004's empty-guard in `rules_generic.py`:

```python
if not profile.make_targets:
    return
```

The rule then evaluates nothing. This is a **fail-open**: a repository
with a perfectly good makefile and a genuinely broken citation gets a
green check, which is the exact scenario the README's headline sentence
("the CI gate that fails when a spec cites a gate this repo does not
have") promises to catch. A gate that fails closed is annoying; one that
fails open is worse than absent, because the green check is evidence of
nothing while looking like evidence of something.

**Evidence:** `docs/peer-review-2026-09.md` finding **F1** records the
defect at `[Certain]` confidence with a reproduction table, quoting the
same two code fragments above, and `docs/next-steps.md` item 1 carries it
forward as remediation **R1** ("Find `GNUmakefile` and `makefile`; add the
corpus shape (F1) — hours — before promoting"). Re-reproduced against this
tree at `c60f894` with one spec citing `` `make regression` `` against a
makefile declaring only `build`:

| Filename | `detect` | `validate --fail-on INFO` |
|---|---|---|
| `Makefile` | `1 found` | **ERROR G004**, exit 1 |
| `GNUmakefile` | `0 found` | **PASS**, exit 0 |
| `makefile` | `0 found` | **PASS**, exit 0 |

The labelled corpus does not catch it and structurally cannot:
`tests/corpus/targets/` holds 21 shapes covering BOM, CRLF, `define`
blocks, include chains, hostile Makefiles and six TOML floor forms — and
every one of them names the file `Makefile`. The corpus is thorough about
a Makefile's *contents* and blind to its *name*.

## What Changes

- `openspec_graph/detect.py`: new module-level
  `MAKEFILE_NAMES: tuple[str, ...] = ("GNUmakefile", "makefile", "Makefile")`,
  declared beside the three existing discovery lists (`MANIFESTS`,
  `INVARIANT_SOURCES`, `ADR_SOURCES`) and carrying the same kind of
  "most specific first" comment, recording that the order is GNU Make's
  own and that `GNUmakefile` **shadows** `Makefile` rather than adding to
  it. A named constant, never inline literals at the call site: this
  repository's own G003 and `tools/check_no_hardcoded_thresholds.py` exist
  to keep governance-relevant values out of the code that consumes them,
  and a discovery list is exactly that kind of value.
- `openspec_graph/detect.py`: `_make_target_facts` walks `MAKEFILE_NAMES`
  in order and uses the **first candidate `read_text_or_none` returns text
  for**, compared against `None` and never against falsiness. The
  `root / "Makefile"` literal and its separate `.exists()` pre-check are
  deleted — splitting "does it exist" from "can it be read" is the split
  that produced the `IsADirectoryError` crash `fix-detect-corpus-defects`
  closed (`DEC-TC-005`), and with three candidates it would additionally
  have to decide whether a directory named `GNUmakefile` ends the search.
  The resolved candidate and every skipped one are recorded at
  `logger.debug`, `detect.py`'s established "why did planlint not see my
  X?" diagnostic style.
- `tests/corpus/targets/gnumakefile-only/`,
  `tests/corpus/targets/lowercase-makefile-only/`,
  `tests/corpus/targets/gnumakefile-wins-over-makefile/`: three new shapes,
  each `repo/` plus a hand-written partial `expected.json` written from
  what a correct detector should emit, per
  `.claude/skills/planlint-add-detect-shape/SKILL.md`. Each gets its row in
  `tests/corpus/targets/README.md`'s shape table.
- `tests/test_detect_corpus.py`: three cases that cannot be committed as
  files, generated in the test beside the existing directory-named-`Makefile`
  and 20K-line cases — a directory named `GNUmakefile` shadowing a real
  `Makefile`, a zero-byte `GNUmakefile` shadowing a real `Makefile`, and
  `Makefile` + `makefile` present as two distinct files (a checkout that
  only exists on a case-sensitive filesystem).
- `tests/support.py`: `supports_case_sensitive_filenames()`, a capability
  probe in the style of the existing `supports_symlinks()` — a real
  `tempfile` probe, not a `sys.platform` check, so a case-sensitive volume
  on macOS still runs what it guards.
- `tests/test_detect_names.py` (new module): `MAKEFILE_NAMES`'s exact
  contents and order pinned against GNU Make's documented search order; an
  `ast`-based guard that `_make_target_facts`'s body holds no inline
  filename literal, in the style of `tests/test_decomposition.py`'s import
  guards.
- `tests/test_graft.py`: the end-to-end reproduction — a repository whose
  only makefile is `GNUmakefile`, with a spec citing a target it does not
  declare, now reports `ERROR G004` and exit 1 where it reported PASS and
  exit 0.
- `README.md` ledger, `CHANGELOG.md`, `docs/next-steps.md` item 1 and
  `docs/peer-review-2026-09.md`'s R1 row: record the defect and close R1.

## Non-Goals

- **No change to G004's empty-guard**, and no new finding, severity or
  status when a target has no machinery at all. That is the peer review's
  **R4** ("INFO finding when a rule skips for want of machinery") and
  **R8** ("widen `indeterminate`"), each its own change with its own
  policy argument. This change does not touch what G004 does when
  `make_targets` is empty; it stops the guard from being tripped by a
  makefile that is *there*. The two are independent: after this change a
  repository with genuinely no makefile still passes G004 vacuously,
  exactly as today, and `report.py`'s `discovery-warnings` note still says
  so.
- **Nothing about `GENERIC_STAGES`.** The peer review's F3/R2 — that five
  common stage names are exempt from G004 whether or not the target
  declares them — is a separate fail-open with a separate fix, and merging
  it here would make one change package answer two unrelated questions
  about the same rule.
- **Nothing about SpecKit parsing.** `detect.find_speckit_spec_files`,
  `parse_speckit.py` and the S00x rules are untouched.
- **No new rule.** The `RULES` tuple in `openspec_graph/rules.py` and the
  rules table in `README.md` are unchanged; nothing here is a spec-quality
  finding.
- **No new dialect-card field and no `schema_version` bump.** Recording
  *which* candidate resolved would churn every saved `detect --diff`
  baseline and, worse, make the card platform-dependent — see
  `DEC-MFD-005`. The name goes to `logger.debug` instead.
- **No configuration surface.** No `--makefile` flag, no `MAKEFILES`
  environment variable, no configurable discovery list. Configurable
  discovery lists are already deferred behind adoption in
  `docs/next-steps.md`, and GNU Make's own three names are not a matter of
  taste.
- **No change to `machinery.py`.** The defect is in *which file is handed
  to* the parser, not in how the parser reads text; `parse_makefile`,
  `strip_bom` and `strip_define_blocks` are untouched, and so is the
  low-confidence widening through `_legacy_make_targets`.
- **No `include`-following and no `MAKEFILE_LIST` resolution.** Both stay
  pinned limits, as the `include-chain` corpus shape already records.

## Affected Capabilities

- `makefile-discovery`
