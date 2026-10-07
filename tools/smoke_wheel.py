"""Smoke-test the built wheel's console script in a clean virtual environment.

The suite runs the CLI as ``python -m openspec_graph.cli``, so nothing else
ever exercises the ``planlint`` console script a wheel actually installs, or
proves the package really declares no runtime dependencies -- a missing one
surfaces here as an ImportError. One definition, two callers
(adopt-branch-promotion-model): the release workflow's ``build`` job, after a
tag, and ci.yml's ``release-tier`` job, on every pull request and push into the
candidate and production branches -- so the release tier has already passed on
the exact commit before anything is tagged against an index whose versions are
immutable.

Probes, in order, each a separate PASS/FAIL line:

1. ``planlint --version`` exits 0;
2. ``planlint --target TARGET detect`` exits 0;
3. ``planlint --target TARGET validate --fail-on SEVERITY`` exits 0;
4. one ``validate`` per ``--expect PATH=CODE``, exiting exactly CODE -- a
   labelled fixture whose expected verdict is committed beside it, so the
   installed artifact is shown to *fail* a failing tree, not merely to run.

Exit codes: 0 every probe passed, 1 a probe failed, 2 the smoke could not run
(no wheel, more than one wheel, a malformed ``--expect``, the venv or the
install failed). Exit 2 is never a pass. Stdlib only.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import logger

#: The console script ``[project.scripts]`` declares.
CONSOLE_SCRIPT = "planlint"

Runner = Callable[[Sequence[str]], "subprocess.CompletedProcess[str]"]


@dataclass(frozen=True)
class Probe:
    label: str
    args: tuple[str, ...]
    expected: int


def _run(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), capture_output=True, text=True, check=False, encoding="utf-8"
    )


def venv_bin(venv: Path, name: str, *, windows: bool | None = None) -> Path:
    """Where ``name`` lands inside ``venv``: ``Scripts/<name>.exe`` on Windows, else ``bin/<name>``.

    ``windows`` defaults to this interpreter's platform. It is read from
    ``os.name`` rather than ``sys.platform`` because mypy narrows the latter
    per ``--platform``, which made one branch "unreachable" on each CI leg;
    passing it explicitly is how a test asserts both layouts on one host.
    """
    if windows is None:
        windows = os.name == "nt"
    if windows:
        return venv / "Scripts" / f"{name}.exe"
    return venv / "bin" / name


def parse_expect(raw: str) -> tuple[str, int]:
    """``"path=1"`` -> ``("path", 1)``; anything else is a ``ValueError``."""
    path, sep, code = raw.rpartition("=")
    if not sep or not path or not code.strip().lstrip("-").isdigit():
        raise ValueError(f"--expect wants PATH=EXITCODE, got {raw!r}")
    return path, int(code)


def build_probes(target: str, severity: str, expects: Sequence[tuple[str, int]]) -> list[Probe]:
    probes = [
        Probe("version", ("--version",), 0),
        Probe(f"detect {target}", ("--target", target, "detect"), 0),
        Probe(f"validate {target}", ("--target", target, "validate", "--fail-on", severity), 0),
    ]
    probes.extend(
        Probe(f"validate {path}", ("--target", path, "validate", "--fail-on", severity), code)
        for path, code in expects
    )
    return probes


def smoke(
    dist: Path,
    venv: Path,
    probes: Sequence[Probe],
    *,
    python: str,
    runner: Runner | None = None,
) -> int:
    """Install the one wheel in ``dist`` into a fresh ``venv`` and run ``probes``."""
    run = runner or _run
    wheels = sorted(dist.glob("*.whl")) if dist.is_dir() else []
    if len(wheels) != 1:
        # Exactly one: zero is "nothing was built", and more than one means
        # whichever pip picked is not necessarily the one under test.
        print(f"ERROR expected exactly one wheel in {dist}, found {len(wheels)}", file=sys.stderr)
        return 2
    wheel = wheels[0]

    for label, args in (
        ("create venv", [python, "-m", "venv", str(venv)]),
        ("install wheel", [str(venv_bin(venv, "python")), "-m", "pip", "install", "--quiet", str(wheel)]),
    ):
        done = run(args)
        logger.debug("smoke_wheel: %s -> %s", label, done.returncode)
        if done.returncode != 0:
            print(f"ERROR {label} failed ({done.returncode}): {done.stderr.strip()}", file=sys.stderr)
            return 2

    script = str(venv_bin(venv, CONSOLE_SCRIPT))
    failed = 0
    for probe in probes:
        done = run([script, *probe.args])
        logger.debug("smoke_wheel: %s -> %s (expected %s)", probe.label, done.returncode, probe.expected)
        if done.returncode == probe.expected:
            print(f"PASS {probe.label} (exit {done.returncode})")
            continue
        failed += 1
        print(f"FAIL {probe.label}: expected exit {probe.expected}, got {done.returncode}")
        for stream in (done.stdout, done.stderr):
            if stream.strip():
                print(stream.rstrip())
    return 1 if failed else 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="smoke_wheel.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("dist", nargs="?", default="dist", help="directory holding the built wheel")
    parser.add_argument(
        "--venv", type=Path, default=None,
        help="where to create the environment (default: a fresh temporary directory)",
    )
    parser.add_argument("--target", default=".", help="the tree the detect/validate probes read")
    parser.add_argument("--fail-on", default="ERROR", help="the validate gate's severity")
    parser.add_argument(
        "--expect", action="append", default=[], metavar="PATH=CODE",
        help="also validate PATH and require exactly CODE (repeatable)",
    )
    parser.add_argument("--python", default=sys.executable, help="interpreter that creates the venv")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        expects = [parse_expect(raw) for raw in args.expect]
    except ValueError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    probes = build_probes(args.target, args.fail_on, expects)
    if args.venv is not None:
        return smoke(Path(args.dist), args.venv, probes, python=args.python)
    with tempfile.TemporaryDirectory(prefix="planlint-smoke-") as scratch:
        return smoke(Path(args.dist), Path(scratch) / "venv", probes, python=args.python)


if __name__ == "__main__":
    sys.exit(main())
