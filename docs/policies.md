# Policies

This is the document of record for how this repository is versioned and
worked on. Each policy is stated here once and pointed at from everywhere
else: a file that needs a local reminder links the policy's anchor and adds
no detail this document lacks, and a statement of a policy's instance — a
particular deprecation's window where its audience reads it, a particular
measurement with the command behind it — is what the policies themselves ask
for, not a second copy. Three things that look like policy live elsewhere on
purpose: the operating contract — floors move up and never down, no
agent-written waivers, no hand-run `witness` — is
[`skills/planlint-spec-governance/SKILL.md`](../skills/planlint-spec-governance/SKILL.md)'s
and outranks every `AGENTS.md`; disclosure and the threat model are
[`SECURITY.md`](../SECURITY.md)'s; the gate ladder — what runs at commit
time, in continuous integration and before a pull request — is
[`hooks.md`](hooks.md)'s.

- [Versioning and deprecation](#versioning-and-deprecation) — Semantic
  Versioning read for a 0.x package, one `schema_version` integer per
  machine-readable output, and the minimum notice a deprecation gives
- [Count cites a command](#count-cites-a-command) — a number written into a
  spec, a decision, a plan or a document of record names the command that
  regenerates it
- [One agent per thread](#one-agent-per-thread) — who owns a pull-request
  thread, when a second agent speaks, and merge over force-push

## Versioning and deprecation

**The package.** planlint follows Semantic Versioning 2.0.0, and
`openspec_graph.__version__` is the one source of the version: `pyproject.toml`
reads it, nothing restates it. While the major is 0, a minor release
(0.Y.0) is the only release in which a user-facing surface may be removed or
a machine-readable output's shape broken. A patch release (0.Y.Z, Z > 0) is a
fix: it never removes a surface and never breaks an output.

**The schema integers.** Every machine-readable output carries its own
integer `schema_version`, declared beside the type whose serialization it
describes and independent of the package version. There are five: the
`validate --json` findings envelope (`FINDINGS_SCHEMA_VERSION` in
`openspec_graph/rule_types.py`), the dialect card (`SCHEMA_VERSION` in
`openspec_graph/dialect_card.py`), the witness record
(`WITNESS_SCHEMA_VERSION` in `openspec_graph/witness.py`), the card diff
(`DELTA_SCHEMA_VERSION` in `openspec_graph/delta.py`) and the stage-citations
report (`SCHEMA_VERSION` in `tools/stage_citations.py`). A bump of one of
these integers is a breaking change for every consumer of that output: a
saved findings envelope the next `report` refuses with exit 2, a witness
record the next run skips rather than reads. So a bump lands only in a
release that may break — a minor while the major is 0, a major from 1.0 —
never in a patch, and always with a `CHANGELOG.md` entry naming the output,
the old and the new integer, and the keys that changed. An additive key never
bumps the integer. `tool_version`, where an output carries it, is
informational: a mismatch is a stderr warning, never a refusal. The SARIF
projection has no planlint schema version, because its shape is SARIF
2.1.0's and not this tool's to version; a change to what planlint writes into
SARIF follows the package rule above.

**The deprecation window is a minimum.** A deprecation of a user-facing
surface — a command or alias, a flag, an output shape, a public import, an
interpreter version — is announced under `Deprecated` in the release notes of
a minor release 0.Y.0, naming the version that removes it. The surface keeps
working through the whole 0.Y.x series, and where it is something the tool
runs it warns on stderr with its exit code unchanged. It is removable from
0.(Y+1).0. A longer window may be named; an unnamed window may not be
written. Three instances show the rule against the tree:

- `specgraph`, the pre-rename command. It has printed a bare "will be removed"
  warning since 0.2.0, whose notes had no `Deprecated` group and filed the
  rename under `Changed`. The 0.3.0 release notes announce it with its removal
  version: the alias warns through every 0.3.x release and is removed in
  0.4.0. That exceeds the minimum, having warned for two minor series.
- `detect --json`, deprecated in 0.2.0 with its removal named as 1.0 — also
  longer than the minimum.
- Python 3.10, announced in the 0.3.0 release notes and dropped in 0.4.0;
  nothing changes through 0.3.x. An interpreter has no warning to print, so
  the window's substance is the named version and the full series of notice.
  This meets the minimum exactly.

## Count cites a command

A number written into a spec, a decision record, a plan or a document of
record names the command that produced it — a `make` report target or the
exact command line — so that a reader re-runs it rather than trusts it. A
number no command regenerates is written as a description of the set ("every
package present when this lands"), not as a count. A measurement is dated
with the commit it was taken at, in the form "at `5fe043e`
`make stage-citations` reports `ci` mentioned in 14 specs and verified by 7,
`pre-pr` mentioned in 41 and verified by 9": the commit, the command, then
the figures. `make stage-citations` is the regenerator for every count of
cited stages; a count of rules is read from `openspec_graph.rules.RULES`
through `tests/test_rule_registry_docs.py`, which fails when the prose
drifts. `spec-adversary`, the reviewer that reads every drafted change
package before implementation, re-measures every count a draft states. The
`CHANGELOG.md` is a dated record of what each release did and is exempt: its
numbers were true on the day they were written and are not expected to
track the tree.

## One agent per thread

One session owns a pull-request thread: the session that opened the pull
request, or, on a review thread, whoever first replies with a commit. A second
agent — another Claude session, Copilot's coding agent, a bot a human drives —
answers only when it is addressed in the thread, and otherwise waits for the
owner's push before touching the same files. When two pushes race anyway, the
result is merged and never force-pushed. This is a convention, not a guard: a
hook cannot see another agent's intent, and the mechanism that makes a merge
wait lives in branch protection outside the tree, so the test over this
document holds that the convention is written and pointed at, not that it is
obeyed.
