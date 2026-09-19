# Security policy

## Reporting a vulnerability

Report privately through GitHub's [security advisory
form](https://github.com/ianshank/planlint/security/advisories/new). Please do
not open a public issue for a vulnerability.

Include what you ran, against what shape of target repository, and what
happened. A reproducing target tree is worth more than a description — the
shapes under `tests/corpus/targets/` are the format this project already reads.

## What this tool's threat model is

`planlint` is pointed at repositories its operator does not control, including
in CI. The security-relevant guarantee is therefore narrow and specific:

**Scanning a target repository executes nothing from it.**

- **Makefiles are parsed, never run.** `openspec_graph/machinery.py` is a
  text-structural parser and never shells out to `make`, at any confidence
  level, not even as a fallback. This is deliberate: GNU Make evaluates
  `$(shell ...)` outside a recipe body at parse time, unconditionally, so no
  flag combination makes invoking real `make` safe against an untrusted
  Makefile. `tests/corpus/targets/hostile-makefile/` carries a specimen with
  `$(shell rm -rf …)`, `$(eval $(shell …))`, `.SHELLFLAGS` and `.ONESHELL`, and
  `test_parsing_a_hostile_makefile_executes_nothing` runs it against a canary
  directory — with a control run under `make -n` that *does* delete the canary,
  so the test is meaningful rather than vacuous.
- **The scan is read-only.** `detect` writes nothing into the target tree, and
  the composite action asserts `git diff --quiet` after every fixture run.
- **Zero runtime dependencies.** `[project] dependencies` is empty and guarded
  by `test_new_modules_stdlib_only`, so the supply chain for a scan is the
  Python standard library.
- **No network access.** Nothing in the package opens a socket.
- **Least privilege in CI.** The composite action runs with `contents: read`,
  no secrets, and `persist-credentials: false` — the posture a fork pull
  request gets — and that is asserted, not assumed.

Reports that would be especially valuable: any input that causes planlint to
execute target-repository content, to write into a target tree, to hang or
consume unbounded memory on a crafted file, or to leak absolute paths or
environment contents into its machine-readable output.

## What is not a vulnerability

- **A rule that misses a defect.** Coverage limits are tracked as findings in
  `docs/peer-review-2026-09.md` and `docs/next-steps.md`; several are recorded
  openly with reproductions. Please report these as issues, not advisories.
- **A false positive.** Same route — an issue, ideally with the target shape.
- **A secret you committed to your own repository.** `make security` runs
  gitleaks over this repository's history; scanning yours is your gate to run.

## Supported versions

Pre-1.0. Only the latest released version is supported. `v0.1.0` was tagged
under the previous distribution name (`openspec-graph`) and was never published
to a package index; it receives no fixes.

## Verifying what you installed

```bash
planlint --version          # the installed version
planlint rules --json       # the exact rule set that version enforces
```

The rule set is content-addressed by this repository's own tests
(`tests/baseline_rules.json`), so a build whose rule list differs from its
tag's baseline is worth asking about.
