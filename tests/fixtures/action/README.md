# Action contract fixtures

Labelled target repositories for the composite action's contract job and for
`tests/test_report.py`. Each one exists to pin one outcome of the action's
four-way status, so a regression shows up as the wrong label rather than as a
subtly different number.

The label is the contract. A fixture whose real behaviour drifts from the row
below fails `tests/test_report.py`, and the hosted `action-contract` job
asserts the same rows against the action's own outputs.

| Fixture | `validate` exit | `status` | Why it is here |
|---|---|---|---|
| `passing/` | 0 | `pass` | Real machinery, one change package whose citations all resolve. |
| `failing/` | 1 | `fail` | Two packages, each citing a make target the Makefile does not have, so findings land in more than one spec file. |
| `empty-tree/` | 0 | `indeterminate` | A spec tree that exists and holds no change package: `validate` exits 0 having checked nothing, and a wrapper that calls that green gates nothing. |
| `no-tree/` | 2 | `error` | No `openspec/` and no `specs/`, so `validate` is a precondition failure and writes no envelope. |
| `nested/` | 0 | `pass` | The valid target is `nested/sub`, so a repository-root run and a subdirectory run differ; also the fixture for annotation path prefixes. |

These are targets, never part of this repository's own spec tree:
`detect.profile()` looks only at `<root>/openspec`, so a nested `openspec/`
under `tests/` is invisible to `planlint --target . validate`. The same is
true of `tests/corpus/targets/`, which is the precedent this layout follows.

`empty-tree/openspec/changes/.gitkeep` is a placeholder, not a spec. Removing
it removes the directory from git and turns the fixture into a second
`no-tree/`.
