# Spec: Makefile discovery by name

> **Change:** `fix-makefile-discovery-names`
> **Version:** 1.0.0-draft
> **Authors:** maintainer · reviewer
> **Status:** DRAFT

## Problem Statement

`detect._make_target_facts` resolves a target repository's makefile by
probing exactly one filename, `Makefile`, and returns empty
`MakefileFacts` when that probe misses. GNU Make's documented search order
is `GNUmakefile`, then `makefile`, then `Makefile`, and it uses the first
one that exists — so `GNUmakefile` takes precedence over `Makefile` where
both are present. A repository using either of the first two names reports
no make targets at all, which trips G004's empty-guard
(`if not profile.make_targets: return` in `rules_generic.py`) and switches
the rule off for the whole run.

The direction of the failure is what makes it urgent. This is a
**fail-open**: the repository has a real makefile and a genuinely broken
citation, and `validate` returns exit 0 with zero findings. It is the
exact scenario the README's headline sentence promises to catch, and a
green check that is evidence of nothing is worse than no check at all.

**Evidence:** `docs/peer-review-2026-09.md` finding **F1** records it at
`[Certain]` confidence, with the same one-filename probe quoted from the
live source and a reproduction table; `docs/next-steps.md` item 1 carries
it forward as remediation **R1**, sized in hours and marked "before
promoting". Re-reproduced against this tree at `c60f894` with a single
spec citing a stage the makefile does not declare: named `Makefile` the
run reports `1 found` and `ERROR G004`, exit 1; renamed `GNUmakefile` or
`makefile`, byte-for-byte identical otherwise, the same run reports
`0 found` and PASS, exit 0.

No existing gate can see this. `tests/corpus/targets/` holds 21 labelled
shapes covering BOM, CRLF, `define` blocks, include chains, hostile
Makefiles and six TOML floor forms, and every one of them names the file
`Makefile` — the corpus is thorough about a Makefile's *contents* and
blind to its *name*.

## Requirements

- R-MFD-1 **(revised)**: `detect._make_target_facts` MUST resolve the target
  repository's makefile in GNU Make's documented search order —
  `GNUmakefile`, then `makefile`, then `Makefile` — stopping at the first
  candidate that **exists**, so a repository using either of the first two
  names is detected exactly as one using the third.

  The original said "the first candidate it can read", which contradicted the
  revised R-MFD-6: taken together they required both falling through past an
  unreadable candidate and not falling through, for the same case. **R-MFD-6
  governs what happens to a candidate that exists and cannot be read**; this
  requirement governs only the search order. Presence ends the search;
  readability decides whether targets are reported or none are.
- R-MFD-2: Resolution MUST stop at the first usable candidate. A
  lower-precedence candidate's targets MUST NOT be unioned into, nor
  substituted for, the resolved candidate's. `GNUmakefile` shadowing
  `Makefile` is the whole point of the order, and a union would also make
  the result depend on whether the host filesystem can hold two of the
  names at once.
- R-MFD-3: "Usable" MUST mean that the shared read helper returned text,
  compared against `None` and never against falsiness. A zero-byte
  `GNUmakefile` is a makefile that declares no targets, not an absent one,
  and MUST shadow a later candidate exactly as a populated one does.
- R-MFD-4: The candidate names MUST live in one named module-level
  constant, `MAKEFILE_NAMES: tuple[str, ...]`, declared beside the
  existing discovery lists it is a sibling of. No filename literal MUST
  appear at the call site, and no second copy of the list MUST exist
  anywhere in the package.
- R-MFD-5: Resolution MUST inherit the host filesystem's case semantics
  exactly as GNU Make's own probe does. It MUST NOT case-fold, MUST NOT
  normalise a candidate name, and MUST NOT list the repository root
  looking for a case-variant spelling of its own accord.
- R-MFD-6 **(revised — the original is superseded)**: A candidate that exists
  but cannot be read — a directory, a FIFO, a dangling symlink, a permission
  denial — MUST end the search and MUST yield no targets. It MUST NOT raise
  and MUST NOT block.

  The original required the opposite ("treated as absent, and resolution MUST
  continue to the next candidate"). Reproduced against real `make`: with a
  directory named `GNUmakefile` beside a valid `Makefile`, invoking make on
  any target prints "GNUmakefile: Is a directory. Stop." and runs nothing, so
  continuing would report the shadowed file's targets and green-light a
  citation that cannot run — the fail-open this package exists to close. GNU
  Make skips a candidate that does not *exist*; it never skips one that exists
  and cannot be opened. The resulting silence is covered by G010
  (`report-unchecked-make-citations`), which reports the citations as
  unchecked.
- R-MFD-7: The resolved candidate's *name* MUST NOT reach the dialect
  card, any verb's stdout, or any sort key. `dialect_card.SCHEMA_VERSION`
  MUST be unchanged by this spec, and the byte-identical CLI-output guard
  MUST pass without its pinned hashes being edited.
- R-MFD-8: Every new name shape MUST carry a hand-written partial expected
  card and a row in the corpus README, per
  `.claude/skills/planlint-add-detect-shape/SKILL.md`. A shape that cannot
  survive a checkout as committed files MUST be generated inside the test
  instead, beside the cases already generated there for the same reason.
- C-MFD-1: A repository whose makefile is named `Makefile` MUST detect
  identically to today. Every one of the existing corpus shapes MUST still
  match its label unchanged, and this repository's own detection MUST be
  unchanged. Backwards compatibility is not negotiable here.
- C-MFD-2: A repository with no makefile under any of the three names MUST
  still report no targets, and G004 MUST still stay silent for it. This
  change MUST NOT manufacture a target, a finding, a severity or a status
  out of an absent makefile — that question belongs to a different change.
- C-MFD-3: The diagnostic naming which candidate resolved and which were
  skipped MUST go to `logger.debug`, reaching a reader only via stderr
  under `--verbose` / `PLANLINT_LOG_LEVEL`. It MUST NOT be printed on
  stdout, so JSON output stays parseable and the byte-stable contract is
  untouched.

## Decisions

- **DEC-MFD-001:** the constant lives in `detect.py`, not `machinery.py`.
  `machinery.py`'s own docstring declares it a pure Makefile-*text* parser
  with "no I/O of its own"; *where to look for a file* is discovery, not
  parsing. `detect.py` already holds three sibling discovery lists —
  `MANIFESTS`, `INVARIANT_SOURCES` and `ADR_SOURCES` — each a module-level
  tuple with a "most specific first" comment, which is precisely the shape
  and precisely the justification this fourth one needs. It stays out of
  `__all__` for the same reason its three siblings are: that list is the
  re-export surface for names that moved between modules during the
  decomposition, not an inventory of every module constant.
- **DEC-MFD-002:** a stat probe per candidate, not a directory listing.
  A listing matched case-exactly would find `Makefile` at the third
  candidate on a case-insensitive filesystem where a probe finds it at the
  second — but both read the same bytes, and since no candidate *name* is
  reported anywhere (R-MFD-7) the two are observationally identical. A
  listing would also cost a full `scandir` of a stranger's repository root
  on every `detect`/`validate`/`graph` call, for a distinction nothing can
  observe. GNU Make itself probes, so probing additionally means planlint
  and `make -n` agree about which file is in force on whatever filesystem
  the user is actually standing on — the comparison a confused adopter
  will make first.
- **DEC-MFD-003:** the first *readable* candidate wins, not the first
  *existing* one. Splitting "does it exist" from "can it be read" is
  exactly the split that produced the `IsADirectoryError` crash
  `fix-detect-corpus-defects` closed (`DEC-TC-005`), and with three
  candidates instead of one it would have to answer a new question:
  does a directory named `GNUmakefile` end the search? It does not — an
  unreadable candidate is absent, and absent candidates are skipped, which
  is the convention `_invariants`/`_adrs`/`read_text_or_none` already
  established package-wide. This does diverge from GNU Make, which would
  abort on such a repository. The divergence is safe in the only direction
  that matters: GNU Make aborting means no targets at all, so falling
  through can never *add* a false G004 against a valid repository; it only
  stops a junk `GNUmakefile` from silently ungating a repository whose real
  `Makefile` is right there. Neither posture is fail-closed for input that
  malformed, and consistency with the established convention won.
- **DEC-MFD-004:** the empty-file case is decided against `None`, not
  truthiness. The read helper returns `""` for a zero-byte file, so
  `if not text:` would send an empty `GNUmakefile` on to `Makefile` and
  report targets GNU Make would not see in that repository — turning a
  citation that genuinely cannot run into a PASS. That is the same
  fail-open this change exists to close, re-introduced one line further
  down, and it is the single most likely way for an implementation of
  R-MFD-1 to be quietly wrong. Hence its own requirement (R-MFD-3) and its
  own criterion.
- **DEC-MFD-005:** no dialect-card field for the resolved name. Recording
  it would bump `dialect_card.SCHEMA_VERSION` and report drift on every
  saved `detect --diff` baseline of an unchanged repository — the churn
  `DEC-TC-003` already refused for a different reason. Worse, it would
  make the card **platform-dependent**: on a case-insensitive filesystem a
  repository whose file is named `Makefile` resolves at the `makefile`
  candidate, so the identical tree would emit a different card on macOS
  than on Linux, breaking the byte-identical contract this project runs a
  Windows CI leg to defend. The name is a diagnostic, and diagnostics go
  to `logger.debug` (C-MFD-3) — the same call `fix-symlinked-spec-dir-double-count`
  made for which alias lost.
- **DEC-MFD-006:** the case-colliding shape is generated in the test, not
  committed. `Makefile` and `makefile` are the same path on a
  case-insensitive filesystem, so a committed fixture carrying both would
  either collide at checkout or leave a permanently dirty working tree for
  every macOS and Windows contributor — the same class of reason the
  directory-named-`Makefile` and large-Makefile cases are generated rather
  than committed. `GNUmakefile` and `Makefile` differ by more than case and
  coexist everywhere, so precedence itself stays a real, committed,
  labelled corpus shape. The generated case is guarded by a
  `supports_case_sensitive_filenames()` capability probe in
  `tests/support.py`, written in the style of the existing
  `supports_symlinks()`: a real filesystem probe rather than a
  `sys.platform` check, so a case-sensitive volume mounted on macOS still
  runs it.
- **DEC-MFD-007:** every expectation is hand-written before the fix runs,
  per `DEC-TC-007` and the add-detect-shape skill. A card copied from the
  detector asserts only that the code equals itself, and this defect is
  precisely one the current detector reports confidently and wrongly — it
  says `0 found` about a repository that has a makefile. The three new
  `expected.json` files state what a correct detector should emit and are
  expected to fail on first run.
- **DEC-MFD-008:** this change deliberately leaves G004 fail-open for a
  target with genuinely no makefile (C-MFD-2). Widening the guard, or
  emitting an INFO when a rule skips for want of machinery, is the peer
  review's R4/R8 and carries a policy argument this change does not make.
  Keeping the two separate means this one can be reviewed purely as a
  detection correction, with a corpus that decides it, rather than as a
  rule-semantics proposal that needs a different kind of agreement.

## Acceptance Criteria

- [ ] **AC-MFD-1:** a repository whose only makefile is named
  `GNUmakefile` reports that file's targets in the dialect card, not an
  empty list. (R-MFD-1, R-MFD-8)
  _Verified by:_ `pytest -k test_detected_card_matches_the_labelled_expectation` · stage: `make test`

- [ ] **AC-MFD-2:** a repository whose only makefile is named lowercase
  `makefile` reports that file's targets in the dialect card. (R-MFD-1,
  R-MFD-8)
  _Verified by:_ `pytest -k test_detected_card_matches_the_labelled_expectation` · stage: `make test`

- [ ] **AC-MFD-3 (non-success):** in a repository holding both
  `GNUmakefile` and `Makefile`, only `GNUmakefile`'s targets are reported
  — a target declared solely in the shadowed `Makefile` does **not**
  appear in the card, and the two files' targets are never unioned.
  (R-MFD-2)
  _Verified by:_ `pytest -k test_detected_card_matches_the_labelled_expectation` · stage: `make test`

- [ ] **AC-MFD-4:** end-to-end, the reproduction inverts: a repository
  whose only makefile is `GNUmakefile`, carrying a spec that cites a stage
  that makefile does not declare, reports `ERROR G004` and exit 1 where it
  previously reported PASS and exit 0. (R-MFD-1)
  _Verified by:_ stage: `make test`

- [ ] **AC-MFD-5:** `MAKEFILE_NAMES` holds exactly GNU Make's three
  documented names in its documented order, and `_make_target_facts`'s own
  body contains no string literal equal to any of them — the call site
  reads the constant and nothing else. (R-MFD-4)
  _Verified by:_ stage: `make test`

- [ ] **AC-MFD-6 (non-success):** a zero-byte `GNUmakefile` beside a
  populated `Makefile` reports **no** targets — the empty higher-precedence
  file shadows the lower one exactly as a populated one would, and the
  usability test is against `None`, never against an empty string being
  falsy. (R-MFD-3)
  _Verified by:_ stage: `make test`

- [x] **AC-MFD-7 (revised):** a directory named `GNUmakefile` beside a real
  `Makefile` reports **no** targets, with no traceback and no change of exit
  code — the shadowed `Makefile`'s targets MUST NOT be reported, because
  `make` itself would run none of them. (R-MFD-6)
  _Verified by:_ `pytest -k test_an_unreadable_candidate_is_terminal_not_a_fall_through` · stage: `make test`

- [ ] **AC-MFD-8 (non-success):** a repository carrying none of the three
  names still reports no targets and still draws no G004 — this change
  manufactures no target and no finding out of an absent makefile, and the
  vacuous-pass question stays where it was. (C-MFD-2, DEC-MFD-008)
  _Verified by:_ `pytest -k test_g004_stays_silent_when_the_target_repo_has_no_makefile_at_all` · stage: `make test`

- [ ] **AC-MFD-9:** every pre-existing corpus shape still matches its
  hand-written label unchanged, and a repository with a conventional
  `Makefile` still reports its targets and still filters `.PHONY`.
  (C-MFD-1)
  _Verified by:_ `pytest -k "test_detected_card_matches_the_labelled_expectation or test_detect_finds_make_targets_and_ignores_phony"` · stage: `make test`

- [ ] **AC-MFD-10 (non-success):** resolution does not diverge by
  filesystem. A `Makefile`-only repository produces the identical card
  whether the host filesystem is case-sensitive or not, even though the
  candidate that matched differs; and where two files differing only by
  case can exist at once, exactly one of them is read, never both and
  never a union. (R-MFD-5, R-MFD-2, DEC-MFD-006)
  _Verified by:_ stage: `make test`

- [ ] **AC-MFD-11:** the resolved filename reaches no persisted or printed
  surface — the dialect card's schema version is unchanged, and the
  byte-identical CLI-output guard passes against its pre-existing pinned
  hashes without edits. (R-MFD-7, C-MFD-3)
  _Verified by:_ `pytest -k "test_corpus_pins_the_card_schema_version or test_output_byte_identical"` · stage: `make test`

- [ ] **AC-MFD-12:** every new shape is described in the corpus README's
  shape table, and every shape's card is byte-identical across two
  interpreters started with different hash seeds. (R-MFD-8)
  _Verified by:_ `pytest -k "test_every_shape_is_documented or test_detection_is_byte_stable_across_hash_seeds"` · stage: `make test`

## Invariants Touched

None — this repo declares no invariant source; no `INV-n` is cited by this
spec.

## Validation Matrix

| Stage | Make Target | Pass Criteria |
|---|---|---|
| Focused | `make test` | AC-MFD-1..12 |
| Self-check | `make validate` | this repo's own change packages validate clean with the corrected detector, and its own `Makefile` still resolves |
| Full | `make pre-pr` | full regression, lint, typecheck, security, docs, thresholds |
