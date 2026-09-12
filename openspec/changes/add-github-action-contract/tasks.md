# Milestones

> Every milestone below is implemented and verified. `AC-GA-23` is the one
> criterion still open: it can only be closed by the hosted `action-contract`
> job running green on the pull request, because a local simulation cannot
> cover the `uses:` steps, the artifact upload, or the action path.

## Milestone 0 — Grounding pass [DONE]

- Established against the tree and the live index, each cited in `proposal.md`:
  the install line resolves to nothing because the distribution is unpublished;
  the action had no `outputs:` block and wrote into the consumer's checkout; a
  zero-spec run prints `PASS` and exits 0; the SARIF upload had no fork guard
  and could not have had a working file guard under `$RUNNER_TEMP`;
  `sarif.to_sarif` consumes the envelope's own findings list.
- Two assumptions from the external design brief did not survive contact and
  were corrected before any code: helper subcommands that *write*
  `$GITHUB_OUTPUT` through flags contradict the stdout-only stance
  (`DEC-SA-012`), so `report` prints and the action redirects; and an
  `--exit-code` flag is redundant, because `blocking > 0` and exit 1 are one
  fact (`DEC-GA-004`).
- Adversarial review of the draft found two blocking defects in the drafted
  YAML expressions — a fork guard that would skip every push and a
  `hashFiles` guard that cannot address `$RUNNER_TEMP` — and both are why
  `DEC-GA-008` moves the upload to the consumer workflow instead of fixing the
  expression in place.

## Milestone 1 — Change package [DONE]

- `proposal.md`, `tasks.md`, `specs/github-action-contract/spec.md`, written
  spec-first and then rewritten against the implementation so no criterion
  describes something that was not built.

## Milestone 2 — `report.py` [DONE]

- Pure, stdlib-only, zero intra-package imports; `parse_envelope` as the single
  gate and every projection total downstream of it; per-severity annotation cap
  as a module constant; workflow-command escaping as two module-level tables
  with `%` substituted first; `parse_card`/`discovery_notes` for the
  detected-machinery facts.
- `tests/test_report.py` unit half, plus `_NEW_MODULES` and a dedicated
  intra-package-import test — the existing stdlib-only guard drops relative
  imports, so it could not have seen a violation here.

## Milestone 3 — CLI wiring [DONE]

- `cmd_report` and its subparser; a shared `_read_json` beside `_load_card`;
  exit 2 on every unprojectable input and never exit 1; one stderr warning on a
  `tool_version` mismatch; `--format sarif` using the producer's version so the
  driver block matches `validate --format sarif` byte for byte.
- `ALLOWED_VERBS`, `READ_ONLY_INVOCATIONS` (with a findings placeholder written
  outside the target), SKILL.md's read-only table, the exit-code reference and
  `llms.txt`.

## Milestone 4 — Fixture targets [DONE]

- `tests/fixtures/action/` with five labelled targets and a README stating each
  one's expected status, each verified against the real CLI.

## Milestone 5 — The action [DONE]

- Rewritten to the contract. Evidence under `RUNNER_TEMP`; the CLI installed
  from a copy so the build cannot write into the scanned checkout; every
  fallible step clearing `errexit` explicitly.
- `tests/test_action_contract.py` — the declarative half, and an executable
  half that extracts the action's steps and runs them. It found the `errexit`
  defect on its first run, before any runner did.

## Milestone 6 — Consumer template [DONE]

- `templates/spec-gate.yml` rewritten as the consumer workflow, copied
  byte-for-byte into the skill's assets, with the SARIF upload moved here from
  the action. The pin-parity test now reads the `uses:` ref and additionally
  requires it to equal the package version.

## Milestone 7 — The hosted contract job [DONE, pending its first green run]

- `action-contract` in `ci.yml`, matrixed over every fixture, under a read-only
  token with no secret; `docs/hooks.md`'s CI table row; three structural guards
  including one that fails when a fixture has no leg.
- `AC-GA-23` stays unchecked until the job is observed green.

## Milestone 8 — Docs and close-out [DONE]

- README's CI section leads with the action and its four statuses;
  `docs/architecture/c4.md` gains component rows for `report.py` and
  `sarif.py`; `CHANGELOG.md` records the additions and the four fixes;
  `docs/next-steps.md` records seven deferrals with their reopen triggers;
  `docs/differentiation-roadmap.md` gains a CP-GA section naming what CP-6's
  framing missed.
- No version bump: `v0.2.0` is untagged, so `0.2.0` is the release carrying
  `report`.

## Milestone 9 — Outside this repository (owner-executed)

- `docs/distribution-plan.md` §3 in full: the pending trusted publisher, the
  `pypi` environment, the tag, the three release jobs, the fresh-venv install.
  Until then the action works from any ref of this repository, but
  `pip install planlint`, the skill preflight and the pre-commit hook still do
  not resolve.
- The measure that matters afterwards, in place of any traffic proxy: clones,
  unique visitors, package downloads, and the only one that proves the action
  is workable — a repository this account does not own running it in CI and
  acting on a finding.
