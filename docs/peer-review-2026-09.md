# Peer review — the rule surface behind the wedge

> Planning artifact, in the style of `docs/eval-corpus-plan.md`. Not
> implementation; nothing here authorizes an edit on its own. Every factual
> claim was reproduced against this tree at `c304a3d` in the session that
> wrote it, and carries a confidence tag: **[Certain]** reproduced directly,
> **[Likely]** a strong inference from evidence, **[Guessing]** judgement
> filling a gap.
>
> The subject is not the release. `docs/distribution-plan.md` §0 records that
> the engineering for 0.2.0 is green and §3 records what remains, and this
> review does not revisit either. The subject is the question those documents
> never ask: **when the gate says PASS, how much did it actually check?**

## Why this review exists

The README's first line is a promise:

> The CI gate that fails when a spec cites a gate this repo does not have.

`docs/differentiation-roadmap.md` stakes the whole product on it — "the only
tool you can point at a stranger's clone and say, with an exit code, whether
the plan is lying." Every planning document in this repository takes that
sentence as settled and argues about what to build next.

Nobody had measured it. This review did, by building target repositories and
running the shipped CLI against them. The promise holds in the case the
README demonstrates and fails open in four others, three of which are more
common than the demonstrated case.

**Fails open** is the load-bearing word. Each gap below produces `PASS`,
exit 0, zero findings — a green check mark on a spec that is lying. A
governance tool that fails closed is annoying. One that fails open is
worse than absent, because the green check is evidence of nothing while
looking like evidence of something.

---

## Findings

### F1 — `GNUmakefile` and lowercase `makefile` are invisible **[Certain]**

`detect._make_target_facts` looks for exactly one filename:

```python
makefile = root / "Makefile"
if not makefile.exists():
    return machinery.MakefileFacts((), False, False, 0)
```

GNU Make's documented search order is `GNUmakefile`, then `makefile`, then
`Makefile`. A repository using either of the first two — both legitimate,
and `GNUmakefile` takes *precedence* over `Makefile` where both exist —
reports `make targets 0 found`, which trips G004's empty-guard and disables
the rule.

Reproduced on one spec citing `make regression` against a makefile
declaring only `build`:

| Filename | `detect` | `validate --fail-on INFO` |
|---|---|---|
| `Makefile` | `1 found` | **ERROR G004**, exit 1 |
| `GNUmakefile` | `0 found` | **PASS**, exit 0 |
| `makefile` | `0 found` | **PASS**, exit 0 |

This is a detection defect, not a policy question: the repository has a
perfectly good makefile and a genuinely broken citation, and planlint
reports clean. `tests/corpus/targets/` holds 21 labelled shapes covering
BOM, CRLF, `define` blocks, include chains, hostile Makefiles and six TOML
floor forms — and every one of them names the file `Makefile`. The corpus
is thorough about a Makefile's *contents* and blind to its *name*.

Cost to fix: a filename tuple in one function, plus a corpus shape.
`.claude/skills/planlint-add-detect-shape/` already exists for the second
half. [Likely] under a day including the spec package.

### F2 — the vacuous-pass item names the wrong rule **[Certain]**

Three planning documents say the same thing:

> A target with no Makefile and no coverage floor currently passes
> G003/G004 vacuously.

— `docs/next-steps.md` item 1, `docs/differentiation-roadmap.md` "Status as
of 0.2.0" item 1, and the Action-contract deferral table.

**G003 does not fail open.** It has no empty-guard. With no coverage floor
detected anywhere, `_hard_coded_threshold` falls back to
`locator = "the governance policy"` and yields normally. Reproduced against
a repo with no Makefile and no `pyproject.toml`:

```
ERROR G003  hard-coded threshold; read it from the governance policy
            instead -- '- **THEN** ... branch coverage at least 97%'
exit=1
```

Only **G004** fails open, and it does so through one explicit line
(`rules_generic.py`):

```python
if not profile.make_targets:
    return
```

The coverage floor is irrelevant to it. The correct statement is: *a target
whose Makefile planlint does not find passes G004 vacuously.*

This matters because of what the mis-statement bought. Framed as
"G003/G004 + no coverage floor", the item reads as a broad rule-semantics
question spanning two rules and two kinds of machinery, and all three
documents defer it behind a `spec-drafter → spec-adversary` policy pass.
Framed correctly it is **one guard clause in one rule**, and the interesting
question is narrow enough to answer in a paragraph — see the rewritten
item R1.

### F3 — `GENERIC_STAGES` exempts the five most-cited stage names **[Certain]**

`rule_types.GENERIC_STAGES = {"ci", "test", "validate", "lint", "coverage"}`.
G004 skips any citation naming one of them. Against a Makefile declaring
only `build`:

| Spec cites | G004 findings |
|---|---|
| `make regression` | 1 |
| `make test` | **0** |
| `make ci` | **0** |
| `make lint` | **0** |
| `make coverage` | **0** |
| `make validate` | **0** |

So the README's example (`make regression`) is the case that works, and it
is [Likely] the least common citation in real specs.

Worse, the tool generates the exempt case itself. `planlint new` scaffolded
into a repository with **no Makefile at all** emits `make test` five times:

```
_Verified by:_ `pytest -k test_<selector>` · stage: `make test`
_Verified by:_ `make test`
| Focused gate | `make test` | AC-TC-1..2 pass |
```

The default scaffold produces citations that are structurally exempt from
the rule that is the product's headline claim, in a repository where the
rule is switched off anyway.

**This one is not obviously a bug.** The exemption has a real argument
behind it: a repo using tox, npm scripts or `just` may write "`make test`"
as generic shorthand, and flagging it would false-positive on prose. That
argument is sound and is why the rewritten plan proposes a WARN rather than
promoting these to ERROR. What is *not* defensible is that the exemption is
undocumented — it appears in no rule description, no README text, and no
planning document. An adopter reading the wedge sentence has no way to learn
that the five stages they are most likely to cite are never checked.

### F4 — SpecKit's wrong-level heading silently deletes requirements **[Certain]**

`docs/next-steps.md` item 4b describes this and is correct. It understates
it: the failure is not only a missing diagnostic, it is silent data loss
from the graph.

`parse_speckit` scopes the FR scan to an H3 `### Functional Requirements`
nested inside the H2 `## Requirements` span. A hand-edited spec that writes
`## Functional Requirements` at H2 yields nothing. Same file, one heading
level changed:

| Heading level | Graph nodes |
|---|---|
| `### Functional Requirements` (canonical) | `FR-001`, `FR-002`, `SC-001` |
| `## Functional Requirements` (hand-edited) | `SC-001` |

Both report `1 spec(s) checked · 0 error · 0 warn · 0 info`, `PASS`,
`broken_links: 0`. Two requirements leave the graph and every gate agrees
nothing is wrong. G001 does not catch it because `SC-001` survives, so the
spec is not requirement-less.

Item 4b's stated reason for deferral — false-positive risk against a
legitimately FR-less, user-story-only draft — is real and remains the right
caution. It also does not apply to the discriminating case: a
`Requirements`-shaped section that exists and yields zero FR bullets is
different from no section at all, and only the former needs to warn.

### F5 — `hard_coded()` reads bullets and table rows only **[Certain]**

`parse_semantics.hard_coded()` skips every line that does not start with
`-` or `|`:

```python
if not line.startswith("-") and not line.startswith("|"):
    continue
```

A threshold in a prose paragraph, a heading, or a `_Verified by:_` line is
invisible to G003. This is how the first attempt at reproducing F2 failed:
`_Verified by: \`make regression\`, coverage floor 97%_` produced no finding
because the line begins with `_`.

[Guessing] the scoping is deliberate — bullets and table rows are where
criteria live, and scanning prose would raise the false-positive rate that
`fix-prose-matcher-precision` spent a whole change package lowering. If so
it should be stated. Today it is an undocumented limit that reads as a
parser bug when you hit it.

### F6 — three planning claims have gone stale **[Certain]**

Each is a numeric or factual claim that no longer describes the tree. None
is load-bearing on its own; together they are the reason this review
re-measured rather than citing.

| Claim | Where | Now |
|---|---|---|
| `is_normative` is a bare substring test; "shallow clone" and "Marshalling" read as normative | `eval-corpus-plan.md`, tagged **[Certain]** | **Fixed.** `parse_model.is_normative` is word-bounded via `NORMATIVE_MODAL`, with a docstring naming those exact strings |
| E501 reports 100 violations: 33 in `openspec_graph/` + `tools/`, the rest in tests | `next-steps.md` item 18 | **122 violations**: 28 `openspec_graph`, 8 `tools`, 86 tests. The debt grew 22% while being tracked as a fixed number |
| Adding `--cov=tools` reports 88.3% line / 84.6% branch, "which fails the 90% floor" | `next-steps.md` item 19 | **91.41% line, 89.32% branch — both floors pass.** The stated blocker is gone |

Item 19's *diagnosis* survives its numbers and is worth keeping: the
shortfall is measurement, not absence. Four tools sit at literally 0%
(`check_coverage_floor`, `check_branch_coverage`, `diff_spec_graph`,
`render_mermaid`) while `tests/test_ci_hardening.py` demonstrably executes
them — via `subprocess.run([sys.executable, ...])`, which never sets
`COVERAGE_PROCESS_START`, so not one line is recorded. `tools/` as a whole
measures 66.5% line. The item is right about the mechanism and wrong that
the floor blocks it.

### F7 — witness mode cannot run where it matters **[Certain]**

`docs/differentiation-roadmap.md` stakes v2 on witness mode: "This is the
line competitors cannot cross without becoming CI infrastructure."

The witness store is `.planlint/witnesses`, and `.gitignore` line 52 is
`.planlint/`. A fresh CI checkout therefore has an empty store, so
`--require-witness` always fails W001 closed. The repository documents this
honestly — `CHANGELOG.md` calls it "a fresh-CI trap" and the composite
Action deliberately does not expose the flag.

Both facts are correct and neither is a defect. The gap is that no planning
document connects them: **the differentiating feature of v2 is currently
unusable in continuous integration, which is the only place its claim
means anything.** A witness proving `make regression` ran on a developer's
laptop, in a store that never leaves that laptop, is a weaker claim than
the `_Verified by:` citation it was built to replace.

[Guessing] the resolution is that witnesses must be a CI-produced artifact
that a later job consumes — the same upload/download shape the Action
contract already designed for pull-request comments — and not a local
store at all. That is a design pass nobody has scheduled, and v3 and v4
are sequenced ahead of it.

---

## Decisions

Written as **Thesis** (the current plans' position), **Counter-argument**
(the strongest case against it), **Rebuttal** (the position that survives
both).

### D1 — Does any of this block the tag?

**Thesis.** No. `docs/distribution-plan.md` is unambiguous that §3 is the
critical path and that everything else is hygiene which "should not delay"
it. These gaps have existed since before 0.1.0.

**Counter-argument.** The first adopter gets a gate that is silently weaker
than the sentence that sold it. F1 and F3 together mean a repository with a
lowercase `makefile`, or one whose specs cite `make test`, gets a green
check that checked nothing. Publishing that is the "half-product" the
distribution plan itself warns against, one level deeper than the warning
imagined.

**Rebuttal.** Neither, because the question is malformed. It assumes a
choice between shipping and fixing, and F2 is the reason there is no such
choice: the plans deferred these behind a policy pass they do not need. F1
is a filename tuple. F4 is a WARN. F6's E501 and coverage items are
bookkeeping. The only genuine policy question in the set is whether
`status` should say `indeterminate` when no machinery is found, and that
one can wait for 1.0 exactly as planned.

So: **tag 0.2.0 now, unchanged** — the tree is green and the publish is
external. Then land F1 and F3's documentation as 0.2.1, before promoting
the repository anywhere. The distinction that matters is not tag-versus-fix
but tag-versus-*promote*: a published package nobody has been pointed at yet
costs nothing to correct.

### D2 — Should `GENERIC_STAGES` be narrowed?

**Thesis.** Implied by the wedge sentence: if a spec cites `make test` and
the repo has no `test` target, the plan is lying and the gate should fail.

**Counter-argument.** It false-positives on every repository that does not
use Make. "Run `make test`" is idiomatic English for "run the test suite",
and a tox/npm/just repo writing it in prose is not lying about anything.
The exemption exists for a reason.

**Rebuttal.** Both are right about different repositories, and the profile
already knows which one it is looking at. When `make_targets` is
**non-empty** — the repo demonstrably uses Make — a citation of `make test`
against a Makefile with no `test` target is a real defect and should be a
**WARN** (not ERROR; the shorthand reading survives). When `make_targets` is
empty, the repo may not use Make at all and the citation carries no
information either way — which is F2's question, not this one.

This is strictly narrower than removing the exemption, and it costs nothing
in the tox case, because a tox repo has no Makefile and so never reaches the
check.

### D3 — What replaces "widen `indeterminate`"?

**Thesis.** `docs/next-steps.md` item 1: widening `indeterminate` to cover
"no machinery detected" is a rule-semantics question needing its own design
pass.

**Counter-argument.** `indeterminate` is an *Action output*. Changing it
tells a CI consumer something and leaves the CLI — which pre-commit,
`make validate` and every agent invocation use — saying `PASS` exactly as
before. It fixes the projection and not the thing being projected.

**Rebuttal.** The counter-argument is correct and is why this item should
be split rather than widened. Three separable pieces, in increasing cost:

1. **Find the Makefile** (F1). Not policy at all. Removes most real-world
   instances of the fail-open without touching rule semantics.
2. **Say when a rule could not run.** G004 skipping for want of a Makefile
   is information the CLI currently discards. An INFO finding — the severity
   that exists for exactly this and that `--fail-on INFO` already surfaces —
   makes a vacuous pass legible without changing any exit code. This is what
   the `discovery-warnings` Action output should have been projecting from
   all along, rather than computing independently.
3. **Change what `status` says.** Only now is this a policy question, and
   with 1 and 2 landed it is a much smaller one, because the honest signal
   already exists and the question is merely whether to escalate it.

---

## The rewritten remainder

Replaces `docs/next-steps.md` item 1 and `docs/differentiation-roadmap.md`
"Status as of 0.2.0" item 1. Everything else in both documents stands.

| Id | Work | Size | Order |
|---|---|---|---|
| **R1** | Find `GNUmakefile` and `makefile`; add the corpus shape (F1) | hours | before promoting |
| **R2** | Document `GENERIC_STAGES` in the rule description and README (F3) | hours | before promoting |
| **R3** | Document `hard_coded()`'s bullet/table scoping, or widen it (F5) | hours | before promoting |
| **R4** | INFO finding when a rule skips for want of machinery (D3.2) | days | 0.3 |
| **R5** | WARN on a generic-stage citation when Make *is* in use (D2) | days | 0.3 |
| **R6** | WARN when a `Requirements`-shaped section yields zero FRs (F4) | days | 0.3 |
| **R7** | Witness artifacts as a CI upload/download, not a local store (F7) | design pass | before v2 is claimed anywhere |
| **R8** | Widen `indeterminate` (D3.3) | policy | 1.0, as already planned |

R1–R3 are the ones this review would defend as pre-promotion: each is
hours, each closes a case where the gate says PASS on a lying spec, and
none needs a design pass. R4–R6 are ordinary change packages. R7 is the
one that should worry a reader of the roadmap, because v3 and v4 are
sequenced ahead of a v2 feature that does not yet work in CI.

Unchanged and not re-litigated here: the release sequence
(`distribution-plan.md` §3), CP-8's agent-threat corpus and H007, the
matcher-accuracy floors, and every non-goal — no authoring verb, no MCP
server, no rule-pack plugins before adoption.

## What this review did not check

- **The three dialects' parsers beyond the two cases above.** Upstream and
  harness parsing were exercised only incidentally.
- **SARIF and the Action against real GitHub code scanning.** The
  `action-contract` CI job covers the contract; nothing here uploaded a
  SARIF file to a live repository.
- **Whether F1's fail-open occurs in practice.** No survey was run of how
  many real repositories use `GNUmakefile` or lowercase `makefile`. The
  defect is [Certain]; its field frequency is [Guessing].
- **The eval suite's behaviour.** Counted, not run: 24 cases, 9 carrying at
  least one deterministic regex grader and 15 LLM-only, which matches
  `distribution-plan.md` §2 exactly.
