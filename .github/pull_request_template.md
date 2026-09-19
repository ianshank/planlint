<!--
This template mirrors the gates that already exist. It asks for evidence, not
promises: every box below is something `make pre-pr` or a named command can
prove, and the point is to paste what it printed.
-->

## What changed, and why

<!-- The defect or the capability, in a sentence or two. If a reviewer has to
     read the diff to learn what problem this solves, this section is short. -->

## Evidence

<!-- Paste real output. A claim this repository cannot reproduce is the exact
     drift planlint exists to catch in other people's repositories. -->

```
make pre-pr
```

- [ ] `make pre-pr` is exit 0
- [ ] Reproduced the defect **before** the fix, and showed the same check passing after (for a fix)
- [ ] New or changed behaviour has a test that **fails without the change**

## Scope

- [ ] Behaviour change is covered by an OpenSpec change package under `openspec/changes/`, and its `spec.md` — not only its `proposal.md` — matches what shipped
- [ ] A new or renamed rule followed `.claude/skills/planlint-add-rule/SKILL.md` in full (baseline, `make skill-catalog`, README table, `c4.md` count *and* per-family range, harness doc, `rules.py` docstring)
- [ ] A detection change added a labelled shape per `.claude/skills/planlint-add-detect-shape/SKILL.md`, written expectation-first
- [ ] A prose-matcher change re-measured with `make matcher-accuracy`

## Compatibility

- [ ] Additive: no repository that passes `--fail-on ERROR` today starts failing
- [ ] `validate` and `graph` golden hashes in `tests/test_decomposition.py` are unmoved, or the move is explained above
- [ ] No hard-coded threshold or tool-version pin introduced (`make thresholds`)
- [ ] Zero new runtime dependencies (`[project] dependencies` stays empty)

## Known limitations

<!-- Anything you chose NOT to fix, and why. A limitation recorded here is
     cheaper than one a reviewer finds. "None" is a valid answer. -->
