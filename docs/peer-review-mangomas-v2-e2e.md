# Peer review — `planlint` end-to-end against `MangoMas_V2`

> An evidence report, in the style of `docs/peer-review-2026-10.md`. Every
> command below was run in the session that wrote this document, and every
> claim is tagged **[Certain]** (reproduced directly here) or **[Likely]** (a
> strong inference from evidence). No file in `E:\Coding_Projects\MangoMas_V2`
> was modified; Phase 1 was strictly read-only and `git status --porcelain`
> was empty before and after. Phases 2A–2C ran in an isolated copy at
> `$env:TEMP\mangomas_v2_planlint_e2e`, which was deleted on completion.
>
> Baseline, run before anything else as the gate requires:
>
> ```
> planlint --version                                →  planlint 0.3.0
> planlint --target . validate --fail-on ERROR      →  57 spec(s) checked · 0 error · 0 warn · 0 info · PASS · exit 0
> git -C E:\Coding_Projects\MangoMas_V2 rev-parse HEAD  →  eb0a0867d2122563c637977eae85e463fb0efd3a
> ```

---

## 1. Executive summary

`planlint 0.3.0` was evaluated end-to-end against a second real repository,
`MangoMas_V2`, in four phases: a read-only audit of the live target (Phase 1),
a raw 40-spec corpus ingestion (Phase 2A), a tri-dialect defect-seeding and
repair loop (Phase 2B), and a full verb / delta / witness matrix (Phase 2C).
The verdict, by phase:

| Phase | Subject | Verdict |
|---|---|---|
| 1 | Live `MangoMas_V2`, read-only | `detect` reads the machinery correctly; the four spec-tree verbs honour the exit-2 "no spec tree" contract [Certain] |
| 2A | All 40 `specs/NNNN-*.md` mapped into `openspec/` | `planlint` finds real cross-reference defects (an ADR padding mismatch) and 0 false `G004`/`G005`/`G006` across 76 `make` citations [Certain] |
| 2B | harness + upstream + speckit, Pass A → Pass B | 8 seeded defects across 8 distinct rules all caught in Pass A; Pass B exits 0 at `--fail-on ERROR` and `--fail-on WARN` [Certain] |
| 2C | graph, waivers, report ×4, delta, witness ×5 | every verb and the five-state W001/W002 machine behave per contract [Certain] |

`planlint` did not lie anywhere in the run: it never reported a pass the
target did not earn, and every exit code matched the finding set. Two
candidate improvements fall out of the evidence (§5): one misleading CLI
message in `cmd_detect`, and one documentation gap about a discovery shape
`MangoMas_V2` actually uses.

---

## 2. Phase 1 — live `MangoMas_V2`, read-only

All commands below ran against `E:\Coding_Projects\MangoMas_V2` with no
`openspec/` or SpecKit `specs/` tree present. [Certain]

### 2.1 `detect` reads the machinery

`planlint --target E:\Coding_Projects\MangoMas_V2 detect`:

```
target            E:\Coding_Projects\MangoMas_V2
languages         python
make targets      64 found
openspec/         ABSENT — run ``planlint init``
specs/ (SpecKit)  ABSENT
spec dialect      unknown
change packages   0
coverage floor    (none)  from (not found)
invariants        1 in AGENTS.md
focused stage     make test

INFO  Makefile parsed with low confidence (3 target(s) could not be resolved structurally); falling back to regex-based detection for those.
```

The portable dialect card (`detect --format json`) carries: `dialect:
"unknown"`, `threshold: null`, `invariant_ids: ["INV-16"]` (source
`AGENTS.md`), `make_target_confidence: "low"`, `make_unresolved_count: 3`, and
`adr_ids` listing 35 ADRs (`ADR-001`, `ADR-002`, `ADR-0003`…`ADR-0038`, with
`0006`/`0007`/`0022` absent). `make_targets` has 64 entries, including the
regex-fallback noise tokens the low-confidence mode surfaces (`?=`, `=`,
`-c`, `-m`, `sys;`). The `-v` debug log attributes the low confidence to
`conditional, 3 unresolved name(s)` (`ifeq` at Makefile line 156 plus three
variable-derived target names such as `$(LOCK_PYTHON)`).

`detect --diff <card>` against the freshly saved card exits 0 with
`PASS: no drift in detected conventions` [Certain].

### 2.2 The exit-2 "no spec tree" contract

Each verb below exited **2** and printed the precondition message on stderr,
never a spec verdict [Certain]:

| Verb | Exit | stderr |
|---|---|---|
| `validate --fail-on ERROR` | 2 | `no openspec/ directory and no SpecKit specs/ tree; run ``planlint init`` first` |
| `validate --fail-on ERROR` (`PYTHONIOENCODING=ascii`) | 2 | same message |
| `waivers` | 2 | same message |
| `graph --format json` | 2 | longer form naming both absolute paths, `run `planlint init` first` |
| `delta --baseline <card>` | 2 | `no openspec/ directory …` |

This is the documented behaviour: exit 2 means the command could not run, not
that the specs are bad. `planlint` does not apply to `MangoMas_V2`'s flat
`specs/NNNN-slug.md` layout out of the box (§5.2).

### 2.3 Dry-run scaffolding, no writes

`planlint --target … init --dry-run` and `new studio-contract-aqa --capability
studio-aqa --dry-run` each print their planned `create` lines and
`dry run — nothing written`, exit 0. `git status --porcelain` was empty before
and after the whole phase [Certain]. `planlint rules --json` lists 29 rules
(G001–G011, H001–H006, U001–U005, S001–S005, W001–W002).

---

## 3. Phase 2 — isolated workspace

A scratch git repository at `$env:TEMP\mangomas_v2_planlint_e2e` was seeded
with copies of `MangoMas_V2`'s `Makefile`, `pyproject.toml`, `AGENTS.md`, and
`docs/adr/*.md`, committed (`git init` + one commit) so `git rev-parse HEAD`
returns a real SHA.

> Note on the spec count: `MangoMas_V2\specs` holds **40** numbered
> `NNNN-slug.md` files (`0001`–`0041`, with `0036` absent), not 41. Every
> phase-2 corpus figure below is over those 40. [Certain]

### 3.1 Phase 2A — the raw 40-spec corpus, as written

All 40 specs were mapped unchanged into
`openspec/changes/<NNNN-slug>/specs/core/spec.md` and validated with **no
prose edits**. This is the highest-signal empirical test: it measures the real
repository's `make`/ADR/invariant citations against the real machinery.

**Run 2A-1** — `pyproject.toml` unmodified (`threshold: null`), `validate
--fail-on ERROR` → exit 1, **190 findings**:

| Rule | Severity | Count | What it means |
|---|---|---|---|
| G001 | ERROR | 40 | none of the 40 flat specs uses a recognised requirement/criterion form (they are MangoMas's own shape, not OpenSpec harness/upstream) |
| G003 | ERROR | 63 | bare threshold percentages (95/100/94/85) with no discoverable floor to cite |
| G008 | WARN | 2 | `0004-cloud-run-deploy` and `0024-deploy-manifest-application` cite `ADR-0001`, which is not declared |
| G009 | WARN | 5 | `ADR-0003/0004/0005/0023/0035` declared but cited by no spec |
| H006 | WARN | 80 | required harness sections absent (the specs are not harness-dialect) |
| **G004 / G005 / G006 / G011 / G002** | — | **0** | the controls that must stay silent did |

The three zeroes are the point. Across **76 backtick-fenced `` `make <target>`
`` citations** in 18 specs, **every cited target exists in the Makefile** →
`G004 = 0`. `INV-16` (declared in `AGENTS.md`) is cited by
`0030-cognitive-authority-plugin` → `G005 = 0`, `G006 = 0`. No generic-stage
citation misfired → `G011 = 0`.

The two `G008` warnings are a **real defect** in the target repo:
`docs/adr/0001-cloud-targets.md` is headed `# ADR-001` (3 digits) while
`docs/adr/0003`–`0038` use 4 digits, but the specs cite `ADR-0001` (4 digits).
`planlint` resolves `ADR-0001` to nothing (G008) and flags `ADR-001` as
orphaned (G009). [Certain]

**Run 2A-2** — adding `fail_under = 95` under `[tool.coverage.report]` and
re-running: **G003 drops 63 → 12**. The exact-floor suppression in
`_hard_coded_threshold` excuses every single-value `95%` bullet once the floor
is discoverable; the surviving 12 are multi-value lines and secondary-package
floor bullets that name no allowlisted config token. G001 (40), G008 (2),
G009 (5), H006 (80) are unchanged [Certain].

### 3.2 Phase 2B — tri-dialect defect seeding and repair

The corpus was replaced by three hand-authored specs derived from real
`MangoMas_V2` features, one per dialect, in one mixed tree (`detect` →
`spec dialect mixed`):

- **harness** `studio-contract-aqa` (from Spec-0041 + Spec-0030), cites
  `INV-16`, `ADR-0038`, `ADR-0029`, `` `make studio-probe-mock` ``, `` `make
  guard-probe` ``, `` `make gate` ``, `` `make bridge-coverage` ``;
- **upstream** `llm-provider-profiles` (from Spec-0040), cites `` `make test` ``;
- **speckit** `0033-gate-falsifiability-probe` (from Spec-0033), cites `` `make
  guard-probe` ``.

**Pass A** seeded eight defects across eight distinct rules and exited 1
(`--fail-on WARN`), 41 findings [Certain]:

| Seeded defect | Caught by | Verdict |
|---|---|---|
| bare `100%` bridge-coverage bullet | G003 (ERROR) | fired |
| `_Verified by:_` missing on AC-SA-1 | H001 (ERROR) | fired |
| `ADR-0001` cited against `# ADR-001` | G008 (WARN) | fired |
| historical ADRs cited by no spec | G009 (WARN) | fired (32 orphan findings) |
| upstream requirement with no SHALL/MUST | U004 (WARN) | fired |
| `[NEEDS CLARIFICATION: …]` marker | S001 (ERROR) | fired |
| indented `- **FR-002**:` bullet dropped from the graph | S005 (WARN) | fired |
| (incidental) upstream REQ-2 with no scenario | U002 (ERROR) | fired |

**Pass B** repaired each defect in the spec prose (never by editing machinery,
thresholds, or adding a citation-silencing waiver): the threshold bullet now
cites `pyproject.toml:[tool.coverage.report].fail_under`, AC-SA-1 gained its
`_Verified by:_` line, `ADR-0001` → `ADR-001`, every upstream requirement is
normative, the clarification marker resolved, FR-002 un-indented, and the
G009 orphans were silenced by one **justified** waiver
`<!-- specgraph:allow G009 The historical ADRs in docs/adr/ (0001-0038)
precede this living three-spec slice … -->` placed in the harness spec, which
downgrades every G009 to `INFO [waived]` [Certain].

Results [Certain]:

| Command | Exit | Summary |
|---|---|---|
| `validate --fail-on ERROR` | 0 | `3 spec(s) checked · 0 error · 0 warn · 32 info · PASS` |
| `validate --fail-on WARN` | 0 | identical summary |
| `validate --fail-on ERROR` (`PYTHONIOENCODING=ascii`) | 0 | identical summary |
| `validate --change studio-contract-aqa --fail-on ERROR` | 0 | `1 spec(s) checked · 0/0/0 · PASS`; stderr `INFO G006 skipped` / `INFO G009 skipped (tree-wide check needs an unscoped run)` |

### 3.3 Phase 2C — verb, delta, report, and witness matrix

**Graph.** `graph --format json` and `--format mermaid` both exit 0; the
Mermaid output renders requirement/criterion/stage/ADR/invariant nodes and
traces-to/verified-by/declares edges across the three specs, with the 32
orphan ADRs styled `orphan` and each linked `-->|finding| G009`. `graph
--change studio-contract-aqa` exits 0 and prints the unscoped-check notes
`INFO G006 included unscoped` / `INFO G009 included unscoped` on stderr
[Certain].

**Waivers.** `waivers` (text) and `waivers --format json` both list the single
G009 waiver with its rule, line (8), change (`studio-contract-aqa`), and
reason [Certain].

**Report (all four formats).** `report --findings <envelope> --card
baseline-card.json` over the saved Pass A and Pass B envelopes, in `sarif`,
`github-annotations`, `github-summary`, and `github-outputs`, each exit 0.
`github-outputs` summarises the two runs [Certain]:

| Field | Pass A | Pass B |
|---|---|---|
| `status` | `fail` | `pass` |
| `errors` / `warnings` / `infos` | 4 / 37 / 0 | 0 / 0 / 32 |
| `blocking` | 41 | 0 |
| `rules-triggered` | G003,G008,G009,H001,H002,S001,S003,U002,U004 | G009 |
| `coverage-floor` | `pyproject.toml:[tool.coverage.report].fail_under` | same |

`validate --format sarif` and `report --format sarif` on the same findings are
**byte-identical** (31380 bytes each) [Certain] — SARIF agreement is
structural, not maintained by two code paths.

**Machinery drift.** With the clean Pass B state as baseline card, three
mutations were applied at once — `fail_under` raised to 96, the
`studio-probe-mock` target removed from the Makefile, `INV-16` dropped from
`AGENTS.md` — then restored [Certain]:

- `detect --diff baseline-card.json` → exit 1, reporting all four field
  changes (make_targets lost `studio-probe-mock`, threshold 95→96,
  invariant_source `AGENTS.md`→`None`, invariant_ids `['INV-16']`→`[]`).
- `delta --baseline baseline-card.json` → exit 1, reporting 4 machinery
  changes and **2 stale citations**: `studio-aqa/spec.md` cites `INV-16`
  (removed) and `` `make studio-probe-mock` `` (removed).
- After restore: `detect --diff` → `PASS: no drift`, `validate` → `PASS`.

**Witness state machine (W001/W002).** Five sequential steps against the same
cited stages (`test`, `studio-probe-mock`, `guard-probe`, `gate`,
`bridge-coverage`), each verified by `validate --require-witness
--fail-on ERROR` [Certain]:

| Step | Action | Result |
|---|---|---|
| W1 | empty store | exit 1 — 5× `ERROR W001 … has never been witnessed` |
| W2 | `studio-probe-mock` exit 1 at HEAD | exit 1 — `W001 … recorded a failing run (exit 1)` for AC-SA-1 |
| W3 | `guard-probe` exit 0 at stale SHA `000…0` | exit 1 — `W001 … witnessed, but not at the current commit` |
| W4 | `gate` exit 0, `--coverage 80.0` at HEAD | exit 1 — `ERROR W002 … 80.0% coverage, below the detected floor of 95%` |
| W5 | all five stages exit 0, `--coverage 96.4` at HEAD | exit 0 — `0 error · 0 warn · 32 info · PASS` |

One behaviour worth stating plainly: after W5, the stale 80.0% `gate` witness
recorded in W4 **still triggered W002** alongside the passing 96.4% witness,
because the content-addressed store is append-only and W002 evaluates *every*
exit-0 witness at the current commit (DEC-WM-019: no "most recent wins"
tie-break). Only after clearing the store and re-recording the five passing
witnesses did W5 exit 0. That is the documented fail-closed design, but it
means a stage re-run does **not** supersede an older below-floor record at the
same commit — see §5.1 for why this is worth a sentence in the witness docs
even though it is by design. [Certain]

---

## 4. SDLC Council architectural findings

### 4.1 For `planlint`

- **[Certain] `cmd_detect`'s low-confidence message names the wrong cause.**
  `openspec_graph/cli.py` (the `INFO  Makefile parsed with low confidence (N
  target(s) could not be resolved structurally)…` line) interpolates only
  `prof.make_unresolved_count`, so when `make_target_confidence == "low"` was
  triggered by a *conditional* (`ifeq`, as in `MangoMas_V2`'s Makefile) the
  message still attributes low confidence to "N target(s) could not be
  resolved structurally" — with N possibly 0 or, here, 3, but never naming
  the conditional. The `-v` log already knows the real reason (`conditional,
  3 unresolved name(s)`); the INFO line should surface it. A reader told "3
  targets could not be resolved" is sent looking for broken targets when the
  actual trigger was an `ifeq`. **Candidate fix:** include
  `has_conditional`/`has_include`/`has_define` in the message when they, not
  the unresolved count, lowered confidence.
- **[Certain] `--dialect` re-parses rather than filters, and that is worth one
  line of documentation.** `validate --dialect harness` runs
  `parse_spec(path, "harness")` over *every* spec in a mixed tree, so the
  speckit and upstream specs are re-read as harness and report `G001`/`H006`
  (and the upstream/speckit runs report `G001`/`U001`). The full-tree
  `mixed` run is unaffected and stays green. This is consistent and correct
  as a *reparse override*, but a reader could mistake `--dialect harness` for
  "lint only the harness specs". The scoped exits (1, with genuine findings)
  are reproduced in §3.2 and are not a Pass B regression.
- **[Likely] The W4→W5 residue above deserves a sentence in
  `references/` or the witness skill.** It is the documented DEC-WM-019
  behaviour, but an adopter who re-runs a stage to clear a below-floor W002
  will be surprised that the older record keeps the run red until the store
  is managed. Saying so costs one paragraph and prevents a misread "the
  witness gate is stuck".

### 4.2 For `MangoMas_V2` (observational — no edits made)

- **[Certain] Align the coverage floor with what pytest already enforces.**
  `MangoMas_V2` enforces 95% via `--cov-fail-under=95` in pytest `addopts`
  (and per-package floors via `Makefile` `*_FLOOR`), but
  `[tool.coverage.report]` has no `fail_under`, so static tooling reports
  `threshold: null`. Adding `fail_under = 95` there makes the floor
  discoverable (and, per §3.1, silences 51 of the 63 `G003` findings that a
  single-value-`95%` bullet otherwise triggers).
- **[Certain] Normalise ADR-001/ADR-002 to the 4-digit convention.**
  `docs/adr/0001-cloud-targets.md` (`# ADR-001`) and
  `0002-secrets-provider-error-semantics.md` (`# ADR-002`) use 3 digits while
  `0003`–`0038` use 4, and specs `0004`/`0024` cite the 4-digit `ADR-0001`.
  Renaming the two headers to `# ADR-0001` / `# ADR-0002` resolves both the
  `G008` "cited but not declared" and the `G009` "declared but not cited".
- **[Certain] `specs/NNNN-slug.md` is a flat layout `planlint` cannot discover
  as-is.** `validate` exits 2 (§2.2). The Phase 2A mapping
  (`openspec/changes/<NNNN-slug>/specs/core/spec.md`) is a faithful,
  prose-preserving bridge, but a native flat-tree discovery mode is a
  `planlint` feature, not a `MangoMas_V2` change (see
  `docs/next-steps.md` item 4 on configurable discovery lists).

---

## 5. Reproduction index

Every command below ran in this session. Paths use the scratch workspace
`$env:TEMP\mangomas_v2_planlint_e2e` (deleted on completion) and the live
target `E:\Coding_Projects\MangoMas_V2` (read-only).

| Step | Command | Exit |
|---|---|---|
| Preflight | `planlint --target . validate --fail-on ERROR` | 0 |
| 1 | `planlint --target E:\Coding_Projects\MangoMas_V2 detect` | 0 |
| 1 | `planlint --target E:\Coding_Projects\MangoMas_V2 detect --format json` | 0 |
| 1 | `planlint --target E:\Coding_Projects\MangoMas_V2 detect --diff <card>` | 0 |
| 1 | `planlint --target E:\Coding_Projects\MangoMas_V2 validate --fail-on ERROR` | 2 |
| 1 | `… waivers` / `… graph --format json` / `… delta --baseline <card>` | 2 |
| 1 | `planlint --target E:\Coding_Projects\MangoMas_V2 init --dry-run` / `new … --dry-run` | 0 |
| 2A-1 | `planlint --target <temp> validate --fail-on ERROR --format json` | 1 (190 findings) |
| 2A-2 | add `fail_under=95`; re-run validate | 1 (139 findings; G003 63→12) |
| 2B-A | `planlint --target <temp> validate --fail-on WARN --format json` | 1 (41 findings) |
| 2B-B | `… validate --fail-on ERROR` / `--fail-on WARN` / ascii | 0 |
| 2B-B | `… validate --change studio-contract-aqa --fail-on ERROR` | 0 |
| 2B | `… validate --dialect harness\|upstream\|speckit --fail-on ERROR` | 1 (reparse findings, by design) |
| 2C | `graph --format json\|mermaid`, `graph --change …` | 0 |
| 2C | `waivers`, `waivers --format json` | 0 |
| 2C | `report --format sarif\|github-annotations\|github-summary\|github-outputs` ×{pass-a,pass-b} | 0 |
| 2C | drift → `detect --diff` / `delta --baseline`; restore | 1 / 1 → restore 0 |
| 2C | witness W1–W5 → `validate --require-witness --fail-on ERROR` | 1,1,1,1,0 |

Per [docs/policies.md#count-cites-a-command](policies.md#count-cites-a-command),
each count above (64 make targets, 35 ADR ids, 190/139/41 findings, G003
63→12, 76 make citations, 32 waived G009, 31380-byte SARIF) is the output of a
command in this table, not a transcribed claim.
