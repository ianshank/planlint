"""The promotion jobs, as the workflows state them (adopt-branch-promotion-model).

Split out of ``tests/test_ci_workflow.py`` when that module neared the suite's
line bound: this is one self-contained concern -- the ``promotion``,
``release-tier`` and ``ci-ok`` jobs of ``ci.yml``, the release workflow's use of
the same smoke tool, and the configuration they rest on. Every guard is a
``*_problems(text)`` reader returning what is wrong, so it is asserted twice:
empty on the committed workflow, and naming the defect on a planted one.
Comments are stripped before anything is matched (R-HCW-15): a comment naming
a command satisfies nothing and trips nothing.
"""

from __future__ import annotations

import re
import textwrap

import pytest

from tests.support import read_pyproject, workflow_job_blocks
from tests.workflow_support import (
    CI_YML,
    DEPENDABOT,
    PULL_REQUEST_TEST,
    RELEASE_YML,
    SOFT_FAIL,
    _code_lines,
    _job_level_keys,
)

#: The aggregator job, and the flags it reads its conditional jobs from.
AGGREGATOR = "ci-ok"
#: The jobs the single required check rests on: none may soften its own failure.
PROMOTION_JOBS = ("promotion", "release-tier", AGGREGATOR)
CONDITION_FLAGS = ("--pull-request-only", "--release-tier-only")
#: How each flag's jobs are conditioned in ci.yml.
CONDITION_OF_FLAG = {
    "--pull-request-only": PULL_REQUEST_TEST,
    "--release-tier-only": "needs.promotion.outputs.release-tier",
}
PROMOTION_ROLES = ("integration_branch", "candidate_branch", "production_branch")
#: The smoke invocation both workflows must make, and the probes it must carry.
SMOKE_CALL = re.compile(r"python tools/smoke_wheel\.py dist\b")
SMOKE_PROBES = ("--expect tests/fixtures/action/passing=0", "--expect tests/fixtures/action/failing=1")
#: What release-tier must run besides the smoke test: the release gate's ladder.
RELEASE_TIER_STEPS = (
    "run: make pre-pr",
    "run: python -m build --outdir dist",
    "run: python tools/check_wheel_metadata.py dist",
)


def _code(body: str) -> str:
    return "\n".join(code for _, code in _code_lines(body))


def _jobs(text: str) -> dict[str, str]:
    """Job name -> its comment-stripped body."""
    return {job: _code(body) for job, body in workflow_job_blocks(text).items()}


def _ci() -> str:
    return CI_YML.read_text(encoding="utf-8")


def _release() -> str:
    return RELEASE_YML.read_text(encoding="utf-8")


# --- readers: read, never assert ----------------------------------------------


def push_branches(workflow_text: str) -> list[str]:
    """``on.push.branches`` as a flow or block list, comments stripped."""
    lines = [code for _, code in _code_lines(workflow_text)]
    for index, line in enumerate(lines):
        if line.strip() != "push:":
            continue
        for nested in lines[index + 1:]:
            stripped = nested.strip()
            if stripped.startswith("branches:"):
                flow = stripped.partition(":")[2].strip()
                if flow.startswith("["):
                    return [n.strip().strip("'\"") for n in flow.strip("[]").split(",") if n.strip()]
                return _block_items(lines, lines.index(nested))
            if not nested.startswith("    "):
                break
    return []


def _block_items(lines: list[str], position: int) -> list[str]:
    indent = len(lines[position]) - len(lines[position].lstrip())
    items: list[str] = []
    for line in lines[position + 1:]:
        if len(line) - len(line.lstrip()) <= indent or not line.strip().startswith("- "):
            break
        items.append(line.strip()[2:].strip().strip("'\""))
    return items


def block_list(job_body: str, key: str) -> list[str]:
    """A job-level block list (``key:`` then ``- item`` lines)."""
    items: list[str] = []
    collecting = False
    for _, line in _code_lines(job_body):
        if line == f"    {key}:":
            collecting = True
            continue
        if collecting:
            if line.startswith("      ") and line.strip().startswith("- "):
                items.append(line.strip()[2:].strip())
                continue
            break
    return items


def aggregator_problems(text: str) -> list[str]:
    """What keeps ``ci-ok`` from gating every other job."""
    jobs = workflow_job_blocks(text)
    if AGGREGATOR not in jobs:
        return [f"no {AGGREGATOR} job"]
    body = _code(jobs[AGGREGATOR])
    problems = [f"not gated by {AGGREGATOR}: {job}"
                for job in sorted(set(jobs) - set(block_list(jobs[AGGREGATOR], "needs")) - {AGGREGATOR})]
    if not re.search(r"^    if: \$\{\{ always\(\) \}\}$", body, re.MULTILINE):
        problems.append(f"{AGGREGATOR} does not run always()")
    if not re.search(r"run: >-\n\s+printf '%s' \"\$NEEDS\" \| python tools/check_promotion\.py aggregate", body):
        problems.append(f"{AGGREGATOR} does not pipe NEEDS into the aggregate command")
    for needed in ("NEEDS: ${{ toJSON(needs) }}", "--release-tier-from promotion"):
        if needed not in body:
            problems.append(f"{AGGREGATOR} lacks {needed!r}")
    return problems


def condition_problems(text: str) -> list[str]:
    """Conditional jobs undeclared to the aggregator, or declared under the wrong flag."""
    jobs = workflow_job_blocks(text)
    body = _code(jobs.get(AGGREGATOR, ""))
    declared = {flag: set(re.findall(rf"{re.escape(flag)}\s+([\w-]+)", body)) for flag in CONDITION_FLAGS}
    conditional = {
        job: _job_level_keys(job_body).get("if", "")
        for job, job_body in jobs.items()
        if job != AGGREGATOR and "if" in _job_level_keys(job_body)
    }
    problems: list[str] = []
    for job, condition in sorted(conditional.items()):
        flags = [flag for flag, marker in CONDITION_OF_FLAG.items() if marker in condition]
        if not flags:
            problems.append(f"{job}: a condition the aggregator cannot model: {condition}")
        elif job not in declared[flags[0]]:
            problems.append(f"{job}: conditional but not declared {flags[0]}")
    for flag, names in declared.items():
        problems += [f"{name}: declared {flag} but unconditional" for name in sorted(names - set(conditional))]
    return problems


def soft_fail_problems(text: str, jobs: tuple[str, ...]) -> list[str]:
    bodies = _jobs(text)
    return [f"{job}: {token}" for job in jobs for token in SOFT_FAIL if token in bodies.get(job, "")]


def smoke_problems(ci_text: str, release_text: str) -> list[str]:
    """Where the two smoke callers stop being one definition."""
    tier = _jobs(ci_text).get("release-tier", "")
    build = _jobs(release_text).get("build", "")
    problems: list[str] = []
    for label, body in (("ci.yml release-tier", tier), ("release.yml build", build)):
        if not SMOKE_CALL.search(body):
            problems.append(f"{label}: no shared smoke call")
        problems += [f"{label}: missing {probe}" for probe in SMOKE_PROBES if probe not in body]
    problems += [f"ci.yml release-tier: missing {step}" for step in RELEASE_TIER_STEPS if step not in tier]
    if "needs: promotion" not in tier:
        problems.append("ci.yml release-tier: does not take its decision from the promotion job")
    venv = re.search(r"smoke_wheel\.py dist --venv (\S+)", build)
    if not venv:
        problems.append("release.yml build: the smoke step names no venv")
    elif f"{venv.group(1)}/bin/planlint --version" not in build:
        problems.append("release.yml build: the version check reads a different venv")
    return problems


def wiring_problems(text: str) -> list[str]:
    """The promotion job's output must come from the step that runs route."""
    body = _jobs(text).get("promotion", "")
    wired = re.search(r"release-tier: \$\{\{ steps\.([\w-]+)\.outputs\.release-tier \}\}", body)
    if not wired:
        return ["promotion exposes no release-tier step output"]
    step = re.search(
        rf"- id: {re.escape(wired.group(1))}\n(?:\s+.*\n)*?\s+run: >-\n\s+python tools/check_promotion\.py route",
        body + "\n",
    )
    return [] if step else [f"step {wired.group(1)!r} does not run check_promotion.py route"]


# --- the committed workflows ------------------------------------------------------


@pytest.mark.integration
def test_ci_push_branches_match_the_promotion_config() -> None:
    """The one literal copy of the topology equals the configured roles.

    Read with a structural TOML parser, independently of the tool's own line
    scanner, so a reader bug in either cannot make both agree on a wrong value.
    """
    promotion = read_pyproject()["tool"]["specgraph"]["promotion"]
    configured = sorted(promotion[role] for role in PROMOTION_ROLES)
    assert sorted(push_branches(_ci())) == configured


@pytest.mark.unit
@pytest.mark.parametrize(
    "text,expected",
    [
        ("on:\n  push:\n    branches: [a, 'b']  # c\n  pull_request:\n", ["a", "b"]),
        ('on:\n  push:\n    branches:\n      - a\n      - "b"\n  pull_request:\n', ["a", "b"]),
        ("on:\n  pull_request:\n# push:\n#   branches: [x]\n", []),
    ],
    ids=["flow", "block", "commented-out"],
)
def test_push_branch_reader_handles_both_list_shapes(text: str, expected: list[str]) -> None:
    assert push_branches(text) == expected


@pytest.mark.integration
def test_ci_ok_needs_every_other_ci_job() -> None:
    """The single required check gates every job, including one added later."""
    assert aggregator_problems(_ci()) == []


@pytest.mark.unit
def test_a_job_missing_from_the_aggregator_is_named() -> None:
    text = textwrap.dedent(
        """\
        jobs:
          lint:
            runs-on: ubuntu-latest
          late:
            runs-on: ubuntu-latest
          ci-ok:
            if: ${{ always() }}
            needs:
              - lint  # a trailing comment is not a job
            steps:
              # tools/check_promotion.py aggregate toJSON(needs) --release-tier-from promotion
              - run: "true"
        """
    )
    problems = aggregator_problems(text)
    assert "not gated by ci-ok: late" in problems
    assert "ci-ok does not pipe NEEDS into the aggregate command" in problems
    assert aggregator_problems("jobs:\n  lint:\n    runs-on: x\n") == ["no ci-ok job"]


@pytest.mark.integration
def test_every_conditional_ci_job_is_declared_to_the_aggregator() -> None:
    assert condition_problems(_ci()) == []


@pytest.mark.unit
def test_an_undeclared_or_misdeclared_conditional_job_is_named() -> None:
    text = textwrap.dedent(
        f"""\
        jobs:
          graph-diff:
            if: {PULL_REQUEST_TEST}
          odd:
            if: github.actor == 'x'
          ci-ok:
            steps:
              - run: >-
                  aggregate --pull-request-only graph-diff --release-tier-only ghost
        """
    )
    assert condition_problems(text) == [
        "odd: a condition the aggregator cannot model: github.actor == 'x'",
        "ghost: declared --release-tier-only but unconditional",
    ]
    undeclared = text.replace("--pull-request-only graph-diff", "")
    assert "graph-diff: conditional but not declared --pull-request-only" in condition_problems(undeclared)


@pytest.mark.integration
def test_release_and_ci_share_one_smoke_tool() -> None:
    """The release tier is the release: one smoke call, the same probes, one venv path."""
    assert smoke_problems(_ci(), _release()) == []


@pytest.mark.unit
def test_a_diverging_smoke_caller_is_named() -> None:
    ci = "jobs:\n  release-tier:\n    needs: promotion\n    steps:\n      - run: echo skipped  # make pre-pr\n"
    release = (
        "jobs:\n  build:\n    steps:\n      - run: python tools/smoke_wheel.py dist --venv /tmp/a\n"
        "      - run: /tmp/b/bin/planlint --version\n"
    )
    problems = smoke_problems(ci, release)
    assert "ci.yml release-tier: no shared smoke call" in problems
    assert "ci.yml release-tier: missing run: make pre-pr" in problems
    assert f"release.yml build: missing {SMOKE_PROBES[0]}" in problems
    assert "release.yml build: the version check reads a different venv" in problems


@pytest.mark.integration
def test_promotion_jobs_cannot_soften_their_own_failure() -> None:
    assert soft_fail_problems(_ci(), PROMOTION_JOBS) == []


@pytest.mark.unit
def test_a_soft_failing_promotion_job_is_named() -> None:
    text = textwrap.dedent(
        """\
        jobs:
          promotion:
            steps:
              - run: python tools/check_promotion.py route || true
          ci-ok:
            steps:
              - run: python tools/check_promotion.py aggregate  # never || true
        """
    )
    assert soft_fail_problems(text, ("promotion", "ci-ok")) == ["promotion: || true"]


@pytest.mark.integration
def test_the_route_output_is_wired_to_the_step_that_runs_route() -> None:
    """A renamed step id empties the job output; the aggregator then exits 2."""
    assert wiring_problems(_ci()) == []


@pytest.mark.unit
def test_a_miswired_route_output_is_named() -> None:
    text = textwrap.dedent(
        """\
        jobs:
          promotion:
            outputs:
              release-tier: ${{ steps.route.outputs.release-tier }}
            steps:
              - id: decide
                run: >-
                  python tools/check_promotion.py route
        """
    )
    assert wiring_problems(text) == ["step 'route' does not run check_promotion.py route"]
    assert wiring_problems("jobs:\n  promotion:\n    steps: []\n") == [
        "promotion exposes no release-tier step output"
    ]


@pytest.mark.integration
def test_route_enforcement_and_dependabot_flip_together() -> None:
    """DEC-BPM-011 / DEC-BPM-013 as a test, not a reminder.

    Dependabot's ``target-branch`` must name the integration branch exactly
    when routes are enforced: enforced without it, every version-update pull
    request lands on production and is refused; retargeted without
    enforcement, the branch it names may not exist yet.
    """
    promotion = read_pyproject()["tool"]["specgraph"]["promotion"]
    enforced = promotion.get("enforce_routes", "true") == "true"
    code = [line.strip() for _, line in _code_lines(DEPENDABOT.read_text(encoding="utf-8"))]
    entries = sum(1 for line in code if line.lstrip("- ").startswith("package-ecosystem:"))
    targets = [line.partition(":")[2].strip().strip("'\"") for line in code if line.startswith("target-branch:")]
    assert entries, "parsed no dependabot entries; this guard would be vacuous"
    if enforced:
        assert targets == [promotion["integration_branch"]] * entries, (
            "routes are enforced: every dependabot entry needs "
            f"target-branch: {promotion['integration_branch']!r}"
        )
    else:
        assert targets == [], "dependabot is retargeted while routes are not yet enforced"
