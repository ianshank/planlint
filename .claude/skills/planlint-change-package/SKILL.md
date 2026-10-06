---
name: planlint-change-package
description: Plan a planlint change as an OpenSpec change package and drive it through draft, gate, adversarial review and revision before any code is written. Use when a fix or feature needs a change package under openspec/changes/, when a planning document's open item is being turned into one, or when a drafted package needs its review findings resolved.
---

# Planning a change package

This repository designs before it codes: every behaviour change lands with a
package under `openspec/changes/<name>/` whose `spec.md` matches what ships.
This skill is the loop that produced the reviewed packages in
`docs/peer-review-2026-10.md`, written down so the next one does not relearn it.

## The loop

1. **Gate, then measure, before drafting.** The root `AGENTS.md` requires
   `planlint --target . validate --fail-on ERROR` and its exit code before
   any edit under `openspec/`; a tree that already fails must be reported as
   such before a draft lands on it. Then re-run every reproduction the
   package will cite, at HEAD, in a scratch directory outside the repository. A planning
   document's number is a claim until it is re-measured. For anything about
   cited stages or witness mode, `make stage-citations` reports per stage how
   many specs mention it and how many cite it on a verification line.
2. **Draft with `spec-drafter`.** Hand it the measured evidence with file and
   symbol pointers, a fresh area code, the decisions you have already made and
   the ones it must make, and the precedent packages to read in full.
3. **Gate the draft yourself.** Run, and report both exit codes verbatim:

   ```
   planlint --target . validate --fail-on ERROR --change <name>
   python -m pytest tests/test_spec_test_citations.py -q
   ```

   Then the whole tree with `make validate`: a sibling package can fail it.
4. **Review with `spec-adversary`.** Name the decisions to pressure-test and
   ask for executed checks, not reasoning. It edits nothing.
5. **Resolve every finding with a decision, not a rewording.** A HIGH that
   changes the design becomes a new or rewritten `DEC-<AREA>-nnn`. A finding
   you decline gets a sentence saying why, in the package.
6. **Re-gate, and re-review if a HIGH changed the design.** A second pass is
   cheap next to an implementation built on a rejected premise.
7. **Commit only a gate-green tree.** A half-revised package fails the
   `self-validate` job for everyone on the branch.

## Traps the gate catches only afterwards

- A backticked `make <stage>` anywhere in the spec is a citation (G004).
- A dialect marker quoted as prose can misclassify the spec.
- The verification marker inside an acceptance criterion's own prose becomes
  its verification line, so H001 fires on a criterion that does cite a stage.
- A spec count, test count or line number pinned in the package drifts when
  another package lands. Describe the set instead.
- Every `pytest -k` selector must name an existing test function; cite the
  stage only until the test exists, and re-point the citation when it does.

Precedence: `skills/planlint-spec-governance/SKILL.md`, then the root
`AGENTS.md`, then `openspec/AGENTS.md`, then this file.
