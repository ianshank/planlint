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
4. one ``validate`` per ``--expect PATH=CODE``, exiting exactly CODE with no
   traceback on stderr (an uncaught exception also exits 1) -- a
   labelled fixture whose expected verdict is committed beside it, so the
   installed artifact is shown to *fail* a failing tree, not merely to run.

Exit codes: 0 every probe passed, 1 a probe failed, 2 the smoke could not run
(no wheel, more than one wheel, a malformed ``--expect``, the venv or the
install failed). Exit 2 is never a pass. Stdlib only.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import logger, read_pyproject_str, repo_root, table_lines

#: Where the console script under test is declared; its first entry is the
#: script the probes run, so a rename there needs no edit here.
SCRIPTS_SECTION = "[project.scripts]"
PROJECT_SECTION = "[project]"
_SCRIPT_ENTRY = re.compile(r"""^["']?([A-Za-z0-9_.-]+)["']?\s*=""")
_EXIT_CODE = re.compile(r"^-?\d+$")

#: What CPython prints when an exception escapes. An uncaught exception also
#: exits 1 -- the same code as "findings" -- so a probe expecting a failing
#: verdict must also show it was a verdict, not a crash.
TRACEBACK_MARKER = "Traceback (most recent call last)"

Runner = Callable[[Sequence[str]], "subprocess.CompletedProcess[str]"]


@dataclass(frozen=True)
class Probe:
    """One console-script invocation and the exit code it must return."""

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


def console_script(pyproject: Path) -> str | None:
    """The console script to probe: the one named like the project, else the first declared.

    Preferring ``[project] name`` keeps the choice stable when the table is
    reordered -- this project also ships a deprecated alias that would pass
    every probe while testing the wrong entry point. ``None`` when none.
    """
    names = [m.group(1) for line in table_lines(pyproject, SCRIPTS_SECTION)
             if (m := _SCRIPT_ENTRY.match(line))]
    project = read_pyproject_str(pyproject, PROJECT_SECTION, "name")
    if project in names:
        return project
    return names[0] if names else None


def parse_expect(raw: str) -> tuple[str, int]:
    """``"path=1"`` -> ``("path", 1)``; anything else is a ``ValueError``."""
    path, sep, code = raw.rpartition("=")
    if not sep or not path or not _EXIT_CODE.match(code.strip()):
        raise ValueError(f"--expect wants PATH=EXITCODE, got {raw!r}")
    return path, int(code)


def build_probes(target: str, severity: str, expects: Sequence[tuple[str, int]]) -> list[Probe]:
    """The three default probes against ``target``, then one ``validate`` per expectation."""
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
    script: str,
    runner: Runner | None = None,
) -> int:
    """Install the one wheel in ``dist`` into a fresh ``venv`` and run ``probes`` with ``script``.

    The venv is created with ``--clear``: an existing directory (a reused
    ``--venv`` path, a self-hosted runner) would otherwise keep an earlier
    install, and pip would report a same-version wheel as already satisfied
    -- smoking the old artifact instead of this one.
    """
    run = runner or _run
    wheels = sorted(dist.glob("*.whl")) if dist.is_dir() else []
    if len(wheels) != 1:
        # Exactly one: zero is "nothing was built", and more than one means
        # whichever pip picked is not necessarily the one under test.
        print(f"ERROR expected exactly one wheel in {dist}, found {len(wheels)}", file=sys.stderr)
        return 2
    wheel = wheels[0]

    for label, args in (
        ("create venv", [python, "-m", "venv", "--clear", str(venv)]),
        ("install wheel", [str(venv_bin(venv, "python")), "-m", "pip", "install", "--quiet", str(wheel)]),
    ):
        done = run(args)
        logger.debug("smoke_wheel: %s -> %s", label, done.returncode)
        if done.returncode != 0:
            print(f"ERROR {label} failed ({done.returncode}): {done.stderr.strip()}", file=sys.stderr)
            return 2

    executable = str(venv_bin(venv, script))
    failed = 0
    for probe in probes:
        done = run([executable, *probe.args])
        logger.debug("smoke_wheel: %s -> %s (expected %s)", probe.label, done.returncode, probe.expected)
        crashed = TRACEBACK_MARKER in done.stderr
        if done.returncode == probe.expected and not crashed:
            print(f"PASS {probe.label} (exit {done.returncode})")
            continue
        failed += 1
        if crashed:
            print(f"FAIL {probe.label}: the console script crashed (exit {done.returncode})")
        else:
            print(f"FAIL {probe.label}: expected exit {probe.expected}, got {done.returncode}")
        for stream in (done.stdout, done.stderr):
            if stream.strip():
                print(stream.rstrip())
    return 1 if failed else 0


def _parser() -> argparse.ArgumentParser:
    # `or ""`: under `python -OO` docstrings are stripped to None.
    parser = argparse.ArgumentParser(prog="smoke_wheel.py", description=(__doc__ or "").split("\n\n")[0])
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
    parser.add_argument(
        "--script", default=None,
        help=f"console script to probe (default: the first entry of {SCRIPTS_SECTION} in --pyproject)",
    )
    parser.add_argument(
        "--pyproject", type=Path, default=None,
        help="where the console script is declared (default: this repository's pyproject.toml)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse ``argv`` and smoke the wheel; return 0, 1 or 2 as the module docstring says."""
    args = _parser().parse_args(argv)
    try:
        expects = [parse_expect(raw) for raw in args.expect]
    except ValueError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    script = args.script or console_script(args.pyproject or repo_root() / "pyproject.toml")
    if not script:
        print(f"ERROR no console script: pass --script or declare one under {SCRIPTS_SECTION}",
              file=sys.stderr)
        return 2
    logger.debug("smoke_wheel: probing console script %r", script)
    probes = build_probes(args.target, args.fail_on, expects)
    if args.venv is not None:
        return smoke(Path(args.dist), args.venv, probes, python=args.python, script=script)
    with tempfile.TemporaryDirectory(prefix="planlint-smoke-") as scratch:
        return smoke(Path(args.dist), Path(scratch) / "venv", probes, python=args.python, script=script)


if __name__ == "__main__":
    sys.exit(main())
