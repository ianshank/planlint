# Peer review deep dive — what the 2026-09 review closed, and plans for what it left open

> Planning artifact, in the style of `docs/peer-review-2026-09.md`. Not
> implementation; nothing here authorizes an edit on its own. Every factual
> claim was reproduced against this tree at `6666444` in the session that
> wrote it, and carries a confidence tag: **[Certain]** reproduced directly,
> **[Likely]** a strong inference from evidence, **[Guessing]** judgement
> filling a gap.
>
> The subject is the previous review itself. It measured the gate, found four
> fail-opens, and six of its eight remediation items shipped. A review whose
> remediation has landed is a claim like any other, so this one asks two
> questions it could not: **did R1–R6 close the cases as measured, not as
> described**, and **what do R7 and R8 need in order to stop being a "design
> pass" and a "policy question"** — the two labels the 2026-09 review itself
> showed can hide hours of work behind months of deferral (its F2).
>
> The output is three OpenSpec change packages, drafted at `Status: DRAFT`
> and reviewed by `spec-adversary`, none implemented:
> `add-witness-ci-artifacts` (R7), `widen-indeterminate-unchecked-citations`
> (R8), and `fix-heading-regex-newline-span` (a defect this deep dive found).
> The rewritten remainder at the bottom replaces the R7/R8 rows of the
> 2026-09 table; everything else in that document stands.
>
> A second pass, after the packages were drafted, reviewed the branch as a
> whole: the harness that drafted them, and the code's shape. Its findings are
> N7 and N8; the harness defects are fixed on this branch with tests, and the
> code-shape debt is measured and dispositioned rather than bundled in.

## Why this review exists

`docs/peer-review-2026-09.md` ends with a table that says R1–R6 "landed
together, through three OpenSpec change packages and three review rounds".
That sentence is true and is also exactly the kind of sentence the review was
written to distrust: a planning document asserting that the tree has a
property. So the first job here was to re-run every one of its reproductions
against HEAD rather than cite the table.

The second job is the remainder. R7 (witness mode cannot run in CI) was left
as "design pass — before v2 is claimed anywhere" and R8 (widen
`indeterminate`) as "policy — 1.0, as already planned". Both deferrals are
reasonable and both are the shape of deferral that F2 caught: an item whose
size is unknown is filed under the largest plausible label. Measured, R7 is a
path override, a recorder, a tightened rule, and a CI job; R8 is one
predicate in one pure function plus two fixtures. Neither needs a design pass
that a change package is not.

The baseline, run before anything else and reported as the gate requires:

```
planlint --target . validate --fail-on ERROR   →  41 spec(s) checked · 0 error · 0 warn · 0 info · PASS · exit 0
planlint --target . detect                     →  make targets 20 found · coverage floor 90 from pyproject.toml
planlint rules                                 →  29 rules, G001–G011 · H001–H006 · U001–U005 · S001–S005 · W001–W002
```

---

## Findings

### The 2026-09 findings, re-measured at HEAD

Each row re-runs the original reproduction. "Closed" means the exact case
that used to say `PASS` now produces a finding; "documented" means the
behaviour is unchanged and the limit is now written where a reader meets it.

| 2026-09 | Then | Now, at `6666444` | Verdict |
|---|---|---|---|
| **F1** `GNUmakefile` / `makefile` invisible | `0 found`, PASS on a broken citation | All three names: `make targets 1 found`; a spec citing a stage the file does not declare gets `ERROR G004`, exit 1 | **Closed** [Certain] |
| **F2** G003 does not fail open | correct as stated | No Makefile, no floor: `ERROR G003 … read it from the governance policy instead`, exit 1. Unchanged and correct | **Stands** [Certain] |
| **F3** `GENERIC_STAGES` exempt | five generic stages, zero findings against a `build`-only Makefile | Same Makefile: each generic stage → `WARN G011`; `make regression` → `ERROR G004`. No Makefile: each → `INFO G010`. The exemption is now stated in `rule_types.py`, the README table, and the rule catalog | **Closed** [Certain] |
| **F4** SpecKit H2 heading deletes requirements | `SC-001` alone, PASS, `broken_links: 0` | Same file: `WARN S005 … declares FR-001 but no FR- requirement reached the graph`. The graph still holds `SC-001` alone — the loss is diagnosed, not repaired, which is the right split | **Closed as WARN** [Certain] |
| **F5** `hard_coded()` reads bullets and table rows only | undocumented | `parse_semantics.hard_coded` docstring: "**Scope: bullets and table rows only** … a deliberate limit, not an oversight", with the cost stated | **Documented** [Certain] |
| **F6** three stale planning claims | 122 E501; item 19's "fails the floor"; `is_normative` substring | `is_normative` word-bounded and documented. Item 19 is closed by `gate-tools-coverage`: `make coverage-tools` is a gate with its own floors (re-run below). E501: see N6 | **Two of three closed** [Certain] |
| **F7** witness mode cannot run in CI | store gitignored, fresh checkout fails W001 | Unchanged: a fresh `git clone` fails `--require-witness` with `ERROR W001 … has never been witnessed` on every criterion. See N3, N4 | **Open — R7** [Certain] |

Two of the three limitations the 2026-09 table recorded "rather than closed"
were re-checked. A SpecKit document with a wrong-level requirements heading
*and* no success-criteria section is not discovered as SpecKit at all, so
`validate` exits 2 with `no openspec/ directory and no SpecKit specs/ tree`
— loud, as recorded [Certain]. A waived G010 still prints `INFO G010 …
[waived] …` and still exits 1 at `--fail-on INFO` [Certain]; see N5 for why
that matters more than it did. The third, AC-MFD-10's cross-host
case-sensitivity invariant, was not re-checked and stays as recorded.

One thing the previous review promised R4 would deliver was checked
separately: INFO findings are printed at the default `--fail-on ERROR`, so
G010 is legible to every CLI caller without changing the threshold [Certain].
The vacuous pass is no longer silent anywhere the CLI runs.

### N1 — a bare heading line fabricates a requirement, and a false ERROR **[Certain]**

`docs/eval-corpus-plan.md` Appendix C noted, as an aside while writing a
property test: "the upstream `REQUIREMENT` regex's `\s+` after the heading
hashes can span a newline, so a bare `##` line followed by a plain-prose
`Requirement: x` line would count as a heading. The generator never emits an
empty heading, so it did not fire. Low priority."

It fires. An upstream delta with a bare `##` line followed by the prose line
`Requirement: this is prose under an empty heading, not a requirement`, then
one real level-3 requirement with two scenarios:

```
ERROR U002  …spec.md:5: requirement 'REQ-1' (this is prose under an empty heading, not a requirement...) has no Scenario
WARN  U004  …spec.md:5: requirement '…' uses no SHALL/MUST; it is not normative
WARN  U005  …spec.md: requirements are at H2 (##), convention is H3 (### Requirement:)
1 spec(s) checked · 1 error · 2 warn · 0 info — exit 1
```

Delete the bare `##` line and the same file is `0 error · 0 warn · 0 info`,
`PASS`, exit 0. A stray empty heading manufactures a requirement, an ERROR
that blocks the gate, and a heading-drift warning about a heading that does
not exist.

The cause is `^(#{2,4})\s+(?:Requirement|…)` under `re.MULTILINE`: `\s` is
not line-aware, so the gap after the hashes crosses the newline. This is the
same defect class `lint-empty-speckit-requirements` fixed in `_bullet_decl`
("`\s*` matches newlines, so `.+?` reached past a blank line to the next
non-blank one"), and that fix's own docstring argues for a template so "the
next fix is structurally unable to land on one and miss the other". The
heading regexes were not in that template. Six of them share the
construction: `SECTION`, `SUBSECTION`, `REQUIREMENT`, `SCENARIO`,
`USER_STORY_HEADING`, `DELTA_HEADER`. `SECTION` is the one with reach: it
feeds `section_span`, and through it H006's required-section check, the
harness Acceptance Criteria span, both SpecKit spans, and `hard_coded()`'s
exemptions.

Field frequency is [Guessing] low — a bare `##` is a typo or an abandoned
heading. The cost of the fix is one character class in six patterns plus the
tests, and the failure mode is a false ERROR, which is the one planlint is
least allowed to produce. This repository's own tree contains no bare heading
line, so the `validate` and `graph` golden hashes should not move.

### N2 — eleven stages are cited as verification; six of them no pull-request job runs by name **[Certain]**

Witness mode exists to answer "did the cited stage run". Before designing how
it reaches CI, this review asked what it would say about this repository.
Two counts matter, and the first draft of this finding conflated them. G004
reads `ParsedSpec.make_refs`: every backticked `` `make <x>` `` anywhere in a
spec. W001 reads `Criterion.verified_by`: the `_Verified by:_` line of each
criterion and nothing else (`rules_witness._stage_citations`). A stage named
in a requirement or a decision is G004's business; only a stage named on a
verification line is a claim witness mode would ever check. Both, over the
41 specs at `6666444`, through the package's own parser:

| Stage | Specs mentioning it anywhere (G004) | Specs citing it on a verification line (W001) | Run by a pull-request job, via `make`? |
|---|---|---|---|
| `test` | 38 | 38 | yes — four matrix legs |
| `pre-pr` | 36 | 5 | **no** — only `release.yml`, on a tag |
| `validate` | 11 | 6 | **no** — `self-validate` runs `planlint … validate` bare, not `make validate` |
| `ci` | 11 | 4 | **no** — its three components run as separate jobs |
| `docs-check` | 9 | 9 | yes |
| `typecheck` | 5 | 3 | yes |
| `lint` | 4 | 2 | yes |
| `thresholds` | 2 | 1 | **no** — `security` runs the script bare |
| `security` | 1 | 1 | **no** — `security` runs the gitleaks action, not `make security` |
| `wheel-check` | 1 | 1 | **no** — `packaging` runs `python -m build` and the checker bare |
| `coverage-tools` | 1 | 1 | yes |
| `matcher-accuracy` | 2 | 0 | not run by any workflow; never on a verification line |
| `e2e-live` | 1 | 0 | yes; never on a verification line |
| `skill-catalog` | 1 | 0 | a writer target; named in a requirement, never on a verification line |

Eleven distinct stages reach a verification line; five of them run by name on
every pull request and six do not. Every one of the fourteen names is a real
Makefile target, so `validate` passes — G004 asks whether the target exists,
not whether anything runs it. The two aggregates are the sharp case: `make
pre-pr` is *mentioned* in 36 specs but *cited as verification* in five, and
those five would each fail W001 because no pull-request job runs it; the
release workflow does, on a tag. `docs/hooks.md` says the CI jobs use "the
same targets CI uses" as the pre-commit hooks; for three jobs that is true of
the command and not of the name.

None of this is a defect in the tool. It is the first measurement of what
`--require-witness` would report against the repository that ships it, and
the answer is that it would fail on day one — on the aggregate citations and
on the three bare-command jobs. That is the product working. It also means
R7's dogfood step cannot be "turn the flag on": it has to align three CI
steps to their make targets and run the aggregates somewhere a pull request
can see. Nothing in the specs needs to change — the three names that never
reach a verification line are not claims witness mode makes.

The table is regenerated, not transcribed: `make stage-citations` prints it
for the current tree, and `python tools/stage_citations.py --root <a checkout
of 6666444> --workflow ci.yml` reproduces every row above, including the six
stages in its last line.

### N3 — W001 lets a failing matrix leg be out-voted by a passing one **[Certain]**

`rules_witness._missing_witness` passes a citation when *any* witness at the
current sha recorded `exit_code == 0`:

```python
if any(w.exit_code == 0 for w in at_commit):
    continue
```

`DEC-WM-019` chose the opposite semantic for W002 — "one bad run among
several retries for the same commit still blocks, rather than being silently
out-voted by a luckier one" — and did not apply it to W001. In a single-job
pipeline the difference never shows. In CI it is the common case: this
repository runs `make test` on four interpreters with `fail-fast: false`, and
under R7 each leg records a `test` witness at the same sha. One failing leg
and three passing ones is a passing W001. The CI job is red, so nothing is
lost today; but the witness gate's whole claim is that it does not need the
CI job's colour to know. R7 tightens W001 to "at least one passing and none
failing", which is strictly more fail-closed and changes nothing for a store
with only passing records.

### N4 — the witness store is portable; the trap is a path, not a format **[Certain]**

The 2026-09 review's F7 said the resolution was [Guessing] "witnesses must be
a CI-produced artifact that a later job consumes … and not a local store at
all". Measured, the store is already the right artifact:

- A record is `{"coverage":95.0,"exit_code":0,"recorded_at":"…","schema_version":1,"sha":"<40 hex>","stage":"test"}`
  — no path, no hostname, content-addressed by filename.
- Copying `.planlint/witnesses/` from the recording checkout into a fresh
  clone turns `FAIL — 2 finding(s) at or above ERROR` into `PASS` with no
  other change. A second commit in the clone turns it back into
  `W001 … witnessed, but not at the current commit`, which is the freshness
  check doing its job.
- Two stores merge by directory union: filenames are content hashes, so
  identical records collide harmlessly and different ones never collide.
- `DEC-WM-011` already says recording and validating may happen in different
  jobs "using the CI system's own artifact-passing mechanism".

What does not exist is any way to tell `validate` or `witness` where the
store is. `load_witnesses(root)` and `write_witness(root, …)` hard-code
`root / ".planlint/witnesses"`, and `detect.profile(root)` has no override.
That one missing parameter is why the composite Action cannot expose the
flag: R-GA-8 forbids the action writing into the workspace, the
`action-contract` job asserts `git diff --quiet` after every run, and a
downloaded artifact has nowhere else to go. The "design pass" R7 was filed
under is a `--witness-dir` option, a recorder action that uploads the
directory, and a gate that downloads it under `$RUNNER_TEMP`.

### N5 — a G010 waiver changes nothing, and `--fail-on INFO` cannot be the escalation **[Certain]**

Three facts, each reproduced on a target with no Makefile whose one spec
cites a make stage:

1. `validate --fail-on ERROR` prints `INFO G010 … G004 could not run`,
   `PASS`, exit 0. Projected through `report --format github-outputs` with
   the target's dialect card, the envelope reads `status=pass`, `infos=1`,
   `make-targets=0`, `discovery-warnings=2` (one note each for the missing
   make targets and the missing floor) — a green check whose only caveats
   are two warning annotations.
2. `<!-- specgraph:allow G010 reason -->` yields `INFO G010 … [waived] …`:
   same severity, same count, exit 1 at `--fail-on INFO`. The CHANGELOG
   records this as "G010 is effectively unwaivable".
3. A consumer who sets `fail-on: INFO` to catch (1) also fails on every
   justified waiver in the tree, because `rules.evaluate` downgrades every
   waived finding of every rule to INFO.

So the three ways an adopter could today turn "my citations went unchecked"
into a red build are: none (default), too much (`INFO`), or nothing (a
waiver). The envelope's finding dict carries `rule, severity, message, path,
line, subject` and no `waived` field; the only trace of a waiver is the
`[waived] ` message prefix. R8 is where a waiver of G010 can acquire the
effect the CHANGELOG says it lacks, because the Action's `status` is the one
surface that can distinguish "unchecked" from "unchecked, and the author said
why".

### N6 — the planning record, re-measured **[Certain]**

| Claim | Where | Now |
|---|---|---|
| E501: 122 violations (28 package, 8 tools, 86 tests) | `next-steps.md` item 18, re-measured at `c304a3d` | **121**: 29 package, 5 tools, 87 tests — three fewer in `tools/`, one more in each of the other two since `c304a3d`. The rewrap item stands, and the number has now been re-counted three times (100, 122, 121) without being done |
| `tools/` measures 66.5% line; four scripts at 0%; the fix is a sibling helper for in-process invocation | `next-steps.md` item 19 | **Closed** by `gate-tools-coverage`: `make coverage-tools` is a hard gate with `[tool.specgraph] tools_line_fail_under` / `tools_branch_fail_under`. Re-run here: see Appendix A |
| v2 (witness mode) sequenced ahead of v3 and v4 "which is the wrong order" | `differentiation-roadmap.md` v2 note | Still the recorded order. R7 now has a package; the roadmap's note should point at it rather than at the gap |
| `v0.2.0` is the release that carries `report`, G010, G011, S005 | CHANGELOG `Unreleased`, distribution plan §3 | Still unreleased: `origin` carries `v0.1.0` only. Every contract change below ships in 0.2.0 or later; none needs a version bump of its own |

### N7 — the harness that drafted these packages had five defects **[Certain]**

The three packages were drafted by the `spec-drafter` subagent and reviewed by
`spec-adversary`, with the PostToolUse hook in `.claude/hooks/` nudging after
every write. Watching that harness run surfaced defects in it, each now fixed
on this branch with a test that fails without the fix:

| Defect | How it showed | Fix |
|---|---|---|
| The hook carried two `case` arms with the identical `spec.md` pattern; bash takes the first, so the second — the dialect-sniffing warning `docs/hooks.md` documents — had never fired | Fed the hook a `spec.md` path: the first arm's text came back, the documented warning did not | One merged arm naming every trap; a test that fails on any duplicated alternative |
| `spec-drafter` had no shell, while the hook told it to run the gate | All three drafters reported "gate not run"; the parent's run found one H001 and two H003 in the R7 draft | `Bash` for read-only checks only; the gate and the citation test are now part of its "before finishing" |
| The verification marker quoted inside an acceptance criterion's prose became that criterion's verification line (`VERIFIED_BY.search` takes the first) | The R7 draft's H001: a criterion that cited a stage was reported as citing none | Documented as the fourth trap in `openspec/AGENTS.md`, the drafter, the hook, and the new `planlint-change-package` skill |
| `tests/test_agent_skill_docs.py` matched make targets with `[a-z-]`, so `e2e-live`, or a typo of it, was skipped rather than checked | Found writing the stage tool's own regression test, which tripped over the same regex | The stage grammar `MAKE_REF` uses, plus a test that a digit-bearing typo is caught |
| The witness loader dropped a bad record, and the sha lookup folded four failures to `None`, both silently | A W001 "never witnessed" against a store that visibly holds files could not say why | DEBUG lines naming each dropped file and its cause, and which of the four sha failures occurred; the default run stays silent and the verdict is unchanged; the git timeout became a named constant |

The N2 measurement itself was a scratch script, which `docs/AGENTS.md` says
a number in this directory should not be. It is now
`tools/stage_citations.py` behind `make stage-citations`: a report, not a
gate, in the shape `DEC-PM-011` gives `make matcher-accuracy`.

### N8 — code shape at HEAD, measured **[Certain]**

The second pass also measured the package and `tools/` for the debt a review
is expected to name. Every row is a command's output, run at this branch's
head; none of it is a regression this branch introduced.

| Measure | Result | Disposition |
|---|---|---|
| Largest module | `cli.py`, 1029 lines; `build_parser` 148 lines, `cmd_validate` 119 | Deferred to its own change package, as `decompose-god-files` was; not bundled into a planning PR |
| Functions over 60 lines | 15 of 253 | Same package; most are parsers or dispatchers whose length is their case list |
| ruff C901, complexity above 10 | 6: `parse_makefile` 15, `cmd_validate` 14, `build_delta` 14, `cmd_report` 12, `find_threshold` 12, `scoped_fail_under` 11 | C901 is not selected; turning it on now adds a backlog, not a gate. Recorded beside the decomposition |
| ruff E501 | 121 lines | `next-steps.md` item 18: its own change |
| ruff BLE, B006, B008, SIM, RET, PIE, UP | 0 | Clean |
| ruff T201 / PERF401 / PTH105–108 | 121 / 12 / 2 | Not defects: a CLI prints by design; the list loops are readable as written; `os.replace` is the atomic write `DEC-WM-012` requires |
| Modules with a logger | 8 of 29 package modules | The two silent paths witness mode depends on now log (N7); the rest are pure projections that do no I/O |
| Hard-coded values | One magic number, the git timeout | Named (N7). `make thresholds` passes: no threshold in the Makefile or a workflow |
| NumPy | Not a dependency | `[project] dependencies = []` stays empty, as `docs/aqa.md` records |
| Dependabot | Two `github-actions` entries: the workflow root, and the one composite action directory on disk, `.github/actions/planlint` | R7's recorder directory does not exist yet; its package adds the third entry when it lands (AC-WCA-32) |
| Coverage | package 99.2% line / 97.6% branch; `tools/` 95.7% / 92.8%; floors 90 / 80 | Holding, with the new tool and its tests included |

---

## Decisions

Written as **Thesis** (the current plans' position), **Counter-argument**
(the strongest case against it), **Rebuttal** (the position that survives
both).

### D1 — Does R7 need a design pass, or a flag?

**Thesis.** `peer-review-2026-09.md` F7: the resolution is that witnesses
"must be a CI-produced artifact that a later job consumes … and not a local
store at all. That is a design pass nobody has scheduled."

**Counter-argument.** Nothing is needed. `DEC-WM-011` already names
`upload-artifact`/`download-artifact` as the wiring; N4 shows a copied
directory passes; an adopter can do the whole thing today in one job (run the
stage, record, validate) with zero code changes. The "trap" is a
documentation problem.

**Rebuttal.** The counter-argument is right about the format and wrong about
the path. The single-job shape works and should be shown — it is the
cheapest honest answer and the template never shows it. But the composite
Action is the surface the wedge is sold on, and it cannot do even the
single-job shape: it may not write into the workspace (R-GA-8), the
`action-contract` job proves it does not, and the store lives nowhere else.
What R7 needs is therefore not a redesign of witnesses but a `--witness-dir`
on `validate` and `witness`, a recorder action that writes under
`$RUNNER_TEMP` and uploads, and a gate that downloads under `$RUNNER_TEMP`
and passes the path — so the action keeps the property the contract holds it
to. Along the way N3's `any` becomes "one passing, none failing", because a
matrix is the first thing CI will do with it. That is a change package, not a
design pass, and `add-witness-ci-artifacts` is it.

### D2 — Should witness mode be proven on this repository before it is offered?

**Thesis.** Implied by the roadmap: v2 is "the line competitors cannot cross
without becoming CI infrastructure"; the Action should gain the flag and the
README should say so.

**Counter-argument.** N2: turned on here, the gate fails on its first run —
six of the eleven stages on a verification line are run by no pull-request
job under that name: `pre-pr` (the verification of five specs), `ci` (four),
and four more — `validate`, `thresholds`, `security`, `wheel-check` — run
bare or not at all. Dogfooding would hold the package hostage to this
repository's own CI shape, which is not what an adopter buys.

**Rebuttal.** The first-run failure is not a reason to skip the dogfood; it
is the dogfood's result. Each W001 it raises is a citation the repository
cannot back: either CI runs the stage by that name, or the spec stops saying
it does. SKILL.md already forbids the third option — recording a witness by
hand — and `evals/fabricate-witness` tests that an agent refuses it. So the
package aligns the three bare-command jobs to `make validate`, `make
thresholds` and `make wheel-check` (same commands, now by the name the specs
cite), adds one job that runs the two aggregates on pull requests (the
release workflow already runs `make pre-pr`; this moves the same gate
earlier), and only then adds the final `witness-gate` job. The exit
criterion is that gate
passing on `main`. A v2 claimed anywhere before that is the same sentence
the 2026-09 review refused to let the README keep.

### D3 — What should `indeterminate` mean?

**Thesis.** R-GA-5: `indeterminate` is "zero specs checked", and `DEC-GA-010`
deferred anything wider as policy.

**Counter-argument.** The deferral table's own reopen trigger: widen it to
"no machinery detected" (no Makefile, no coverage floor), so a repository
that cannot be checked is red rather than green.

**Rebuttal.** Both are wrong about the same thing, in opposite directions.
The thesis leaves the measured case — one spec, one `make` citation, no
Makefile — as a green check with a warning annotation. The counter-argument
reds a tox repository whose specs never mention Make and whose thresholds
G003 checks perfectly well (F2). The discriminating predicate is the one R6
learned on S005: key on what was lost, not on what the document or the
repository looks like. A run is `indeterminate` when it found no spec, **or
when it reported an unwaived G010** — the specs made `make` claims and the
run could check none of them. A reasoned G010 waiver clears it, which is both
the ledgered escape (`planlint waivers` lists it) and the effect N5 says the
waiver currently lacks. The CLI exit code does not move: INFO never blocks,
and `status` is a projection the Action owns (`DEC-GA-004`). Two fixtures
pin the two sides, the gate message names the cause, and `DEC-GA-005`'s
refusal of an `allow-indeterminate` knob stands — the waiver and
`continue-on-error` remain the only ways out. That is
`widen-indeterminate-unchecked-citations`.

The adversarial review of that package named the cost, and it belongs
here. In the harness dialect, H001 (ERROR) requires every acceptance
criterion to cite a `make` stage, so "stop citing Make" is an exit only
for the upstream and SpecKit dialects; a harness-dialect repository that
does not use Make is forced to write `make <x>`, always gets G010, and
under this change is `indeterminate` on every spec until each carries a
reasoned waiver — one line per spec, each a ledgered statement that the
citation is shorthand. `planlint new` on a Makefile-less target scaffolds
`make test` (DEC-UMC-008), so the scaffold's own output is `indeterminate`
until the author adds that line. The decision stands with the cost stated
rather than hidden: a green check over citations nobody could check is the
thing this whole review series exists to remove, DEC-UMC-004's "not lying"
argument is about the rule's severity and is untouched, and the scaffold
question is recorded as a follow-up with a reopen trigger rather than
folded in.

### D4 — Is N1 a note or a fix?

**Thesis.** `eval-corpus-plan.md` Appendix C: low priority, noted for the
next parser change; the generator never emits an empty heading.

**Counter-argument.** It produces a false ERROR that blocks a gate, from a
one-character typo, in the dialect the first foreign adopter uses. A linter
that fails a build on a heading that does not exist has the exact defect it
sells itself as catching.

**Rebuttal.** Fix it, and fix the family. The counter-argument wins on
severity, and the `_bullet_decl` precedent decides the shape: six regexes
share the construction, one shared horizontal-whitespace class, tests per
regex plus the Hypothesis generator extended to emit bare headings so the
property holds forever. No prose matcher moves, so no accuracy floor moves.
Hours, not days; it goes first because it is the only item here with a false
ERROR behind it. That is `fix-heading-regex-newline-span`.

---

## The rewritten remainder

Replaces the R7 and R8 rows of `docs/peer-review-2026-09.md`'s table.
Everything else there stands.

| Id | Work | Size | Plan |
|---|---|---|---|
| **N1** | A bare heading line is never a heading: `[^\S\n]+` in six `parse_semantics` regexes, tests per regex, generator extended (D4) | hours | `openspec/changes/fix-heading-regex-newline-span/` — drafted, reviewed twice, revised, gate-green |
| **R8** | `indeterminate` also when an unwaived G010 was reported; `indeterminate-cause` output; `waived` in the envelope's finding dict; two fixtures (D3) | days | `openspec/changes/widen-indeterminate-unchecked-citations/` — drafted, reviewed, revised, gate-green |
| **R7** | `--witness-dir` on `validate` and `witness`; W001 "one passing, none failing" (N3); `require-witness`/`witness-dir` action inputs; a recorder action; a two-job template; the dogfood ladder (N2) (D1, D2) | days, plus CI runs to prove it | `openspec/changes/add-witness-ci-artifacts/` — drafted, reviewed, revised, gate-green |
| **N2** | Three CI steps run their gate bare and two aggregates never run on a pull request, so six verification-line stages have no witness | inside R7 | the dogfood milestone of `add-witness-ci-artifacts` |
| **N5** | A G010 waiver has no effect | inside R8 | the waiver clears the widened `indeterminate` |
| 18 | E501 rewrap, 121 lines | hours | its own change, as item 18 already says; the number should not be re-counted a fourth time |
| **N7** | Harness defects: a dead hook arm, a drafter without a shell, the quoted-marker trap, a digit-blind guard, two silent paths | hours | **fixed on this branch**, each with a test that fails without it |
| **N8a** | Decompose `cli.py` (1029 lines; parser builder 148; `cmd_validate` complexity 14) | days | its own change package, in the shape of `decompose-god-files` |
| **N8b** | Six functions above ruff's complexity limit | per function | alongside N8a, case by case; C901 stays unselected until then |
| L1 | S005 cannot see a wrong-level spec that also lacks success criteria | recorded | exits 2, loud; not planned |
| L2 | AC-MFD-10 is a cross-host invariant no single CI leg verifies | recorded | not re-checked; not planned |

**Order.** N1, then R8, then R7. N1 is hours and removes a false ERROR. R8
is a contract change confined to `report.py`, `rule_types.py`, the action's
gate step and two fixtures, all testable offline. R7 is the only one that
needs a hosted run to prove, and its first `witness-gate` run on this
repository is expected to fail on exactly the citations N2 lists — that
failure is part of the plan, and the package says so.

**Each, in order:** `spec-adversary` on the draft before code;
`planlint --target . validate --fail-on ERROR` after every edit under
`openspec/`, with the exit code reported; `make pre-pr` before the pull
request. None of the three bumps the package version — `v0.2.0` is still
untagged on `origin`, so 0.2.0 is the release that carries whichever of
them lands first.

Unchanged and not re-litigated here: the release sequence
(`distribution-plan.md` §3), CP-8 and H007, the matcher-accuracy floors, the
`extra-args` refusal, and every non-goal — no authoring verb, no MCP server,
no rule-pack plugins before adoption, no agent that records a witness.

## What this review did not check

- **GitHub Actions' sha behaviour across jobs.** R7 relies on every job in
  one run that uses the default `actions/checkout` seeing the same
  `GITHUB_SHA` and `git rev-parse HEAD` (on `pull_request`, the merge
  commit), and on `download-artifact@v4`'s `merge-multiple` producing a
  directory union. Both are [Likely] from the actions' documentation; neither
  was run here. The package's first hosted run is where they get checked.
- **SARIF against live code scanning, and the eval suite.** Unchanged from
  the 2026-09 list: `action-contract` covers the contract; nothing uploaded a
  SARIF file to a live repository, and `claude plugin eval` still cannot run
  from this account.
- **Field frequency of N1.** A bare `##` line is a typo; how often it occurs
  in real spec trees is [Guessing]. The fix is justified by the false ERROR,
  not by frequency.
- **The drafted YAML.** Three change packages describe workflow and action
  changes. None of that YAML has been executed; the packages are plans, and
  the `action-contract` job is where their fixtures will run.
- **AC-MFD-10.** Not re-checked; the `test-windows` leg exercises a
  case-insensitive filesystem but no leg exercises both at once.
- **Whether the drafter's new shell is used as instructed.** `spec-drafter`
  now carries `Bash` for read-only checks; nothing mechanically stops it
  writing outside its package. The parent still runs the gate, and the hook
  still nudges.

## Appendix — reproductions

All probes ran in scratch directories against `6666444`, with no repository
file modified until this document and the three packages were written. Each
is reproducible from the description.

### A. Gates

| Command | Result |
|---|---|
| `planlint --target . validate --fail-on ERROR` | 41 specs, 0/0/0, PASS, exit 0 |
| `planlint --target . detect` | dialect `harness`, 40 change packages, 20 make targets, floor 90 from `pyproject.toml:[tool.coverage.report].fail_under` |
| `python -m pytest tests/ -q` | 1412 tests collected at `6666444`, all passing; 1493 on this branch after the three Copilot review rounds, all passing |
| `python -m ruff check … --select E501` | 121: `openspec_graph` 29, `tools` 5, `tests` 87 |
| `make coverage-tools` | `tools/` line 95.2% (657/690) against floor 90, branch 92.3% (229/248) against floor 80, exit 0 — item 19 closed, as measured not as read |

### B. F1 — three makefile names

One spec citing a stage the file does not declare, against a makefile
declaring only `build`, under each of `Makefile`, `GNUmakefile`, `makefile`:
`detect` reports `make targets 1 found` and `validate --fail-on INFO`
reports `1 error · 2 warn` (the error is G004; the warnings are H006 for the
deliberately minimal fixture) for all three.

### C. F3 — generic stages

Same `build`-only makefile; one spec citing one stage each. With the
makefile: `regression` → `G004/ERROR`; `test`, `ci`, `lint`, `coverage`,
`validate` → `G011/WARN`. Without any makefile: all six → `G010/INFO`.

### D. F4 — SpecKit heading level

One SpecKit feature with two FR bullets and one SC bullet. Level-3
functional-requirements heading: graph nodes `FR-001`, `FR-002`, `SC-001`,
PASS. Level-2: `WARN S005 … declares FR-001 but no FR- requirement reached
the graph`, graph nodes `SC-001` alone.

### E. F7 / N4 — the witness round trip

In a scratch git repository with a `test` target and a spec citing it:
`validate --require-witness` fails W001 twice ("never witnessed"); after
`planlint witness --stage test --exit 0 --coverage 95 --sha <HEAD>` it
passes; a fresh `git clone` fails W001 twice again; copying
`.planlint/witnesses/` into the clone makes it pass; one further commit in
the clone yields `W001 … witnessed, but not at the current commit`.

### F. N1 — the bare heading

See the finding for the exact output. The dialect detected was `upstream`;
the real requirement's two scenarios each resolved; the phantom `REQ-1` is
reported at line 5, the bare `##` line.

### G. N2 — cited stages

`python tools/stage_citations.py --root <checkout of 6666444> --workflow
ci.yml`. The tool parses each spec with `openspec_graph.parse.parse_spec`;
"mentioned" counts specs whose `ParsedSpec.make_refs` holds the stage,
"verified" counts specs with a criterion whose `Criterion.verified_by` cites
it, and a workflow is credited only for a direct `make <stage>` invocation.
41 specs at that commit, every one citing at least one stage on a
verification line. The first version of this appendix measured only the
first column, with a scratch script; the R7 drafter caught the conflation.

### H. N5 — G010 and its waiver

No Makefile, no floor, one spec citing a make stage: `INFO G010`, `PASS`,
exit 0 at `--fail-on ERROR`; exit 1 at `--fail-on INFO`. With a reasoned
`specgraph:allow G010` comment: `INFO G010 … [waived] …`, still exit 1 at
`--fail-on INFO`. The same repository with the citation removed: no G010
(G003, H001 and H006 fire on the minimal fixture instead), so the
discriminating predicate in D3 is reachable from the envelope alone.
