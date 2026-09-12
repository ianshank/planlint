# Action-contract fixtures

Each subdirectory is a minimal target repository the hosted
`action-contract` job (and `tests/test_report.py`) run the composite action
and the CLI against. The directory name is the expected `status` (or, for
`nested/`, the shape that only passes when `--target` is the subdirectory).

| Dir | Expected `status` | CLI `validate --format json` |
|---|---|---|
| `passing/` | `pass` | exit 0, `specs_checked >= 1` |
| `failing/` | `fail` | exit 1, `blocking > 0`, findings in both packages |
| `empty-tree/` | `indeterminate` | exit 0, `specs_checked == 0` |
| `no-tree/` | `error` | exit 2, no-spec-tree message on stderr |
| `nested/` | `pass` only at `nested/target/` | repository-root run is not a pass |

`.gitattributes` pins this tree `-text` so a Windows checkout cannot rewrite
the specimens.
