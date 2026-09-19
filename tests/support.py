"""Shared test helpers for the planlint test suite.

Only genuinely-duplicated helpers live here. Tailored per-test fixture *variants*
( GOOD_HARNESS, MAKEFILE, etc.) stay inline in the test modules that use them,
because each variant asserts behavior specific to its content.
"""

from __future__ import annotations

import contextlib
import importlib.util
import os
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def supports_case_sensitive_filenames() -> bool:
    """Whether this filesystem holds ``makefile`` and ``Makefile`` as two files.

    macOS and Windows default to case-insensitive, where the two names are one
    path -- a fixture pinning their precedence could not even be checked out
    there. A capability probe rather than a ``sys.platform`` check, for the
    same reason as :func:`supports_symlinks`: a case-sensitive volume mounted
    on macOS should still run the tests this guards.
    """
    with tempfile.TemporaryDirectory() as td:
        lower = Path(td) / "makefile"
        upper = Path(td) / "Makefile"
        lower.write_text("lower", encoding="utf-8")
        upper.write_text("upper", encoding="utf-8")
        try:
            return lower.read_text(encoding="utf-8") == "lower"
        except OSError:
            return False


def supports_symlinks() -> bool:
    """Whether this process can create a filesystem symlink right now.

    Windows requires either Administrator rights or Developer Mode enabled
    (SeCreateSymbolicLinkPrivilege) to create any symlink at all, unlike
    POSIX where an unprivileged user always can -- a capability probe, not a
    bare ``sys.platform`` check, so a Windows box that *does* have one of
    those enabled still runs the tests this guards.
    """
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "target"
        target.write_text("")
        try:
            (Path(td) / "link").symlink_to(target)
        except (OSError, NotImplementedError):
            # OSError: the common case (Windows without the privilege).
            # NotImplementedError: Path.symlink_to()'s own fallback when
            # os.symlink doesn't exist on this platform at all -- letting
            # this one escape would crash the *importing* test module at
            # collection time (see the module-level probes in
            # test_witness.py/graft_support.py), the exact all-or-nothing
            # failure this capability probe exists to avoid.
            return False
        return True


def load_tool(name: str, filename: str) -> ModuleType:
    """Import a ``tools/`` script by path, in-process, under ``name``.

    In-process rather than as a subprocess so coverage sees the module and
    its functions can be called directly. Registered in ``sys.modules`` so a
    script that imports a sibling (``from _common import ...``) resolves it
    the same way twice. Shared by the three test modules that exercise the
    gate scripts; the previous three verbatim copies are exactly what this
    file exists to hold.
    """
    path = Path(__file__).resolve().parent.parent / "tools" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write_spec(repo: Path, change: str, capability: str, body: str) -> Path:
    """Write a spec body into ``openspec/changes/<change>/specs/<capability>/spec.md``."""
    path = repo / "openspec" / "changes" / change / "specs" / capability / "spec.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    # Explicit encoding matches every read/write in openspec_graph itself
    # (parse.py, detect.py, scaffold.py all pass encoding="utf-8") -- without
    # it, Path.write_text's platform-default encoding (e.g. cp1252 on
    # Windows) can't represent arbitrary non-ASCII spec content and raises
    # UnicodeEncodeError before the CLI under test ever runs.
    path.write_text(body, encoding="utf-8")
    return path


def write_speckit_spec(repo: Path, feature: str, body: str) -> Path:
    """Write a spec body into ``specs/<feature>/spec.md`` (SpecKit layout --
    no ``changes/`` nesting, no ``openspec/`` ancestor)."""
    path = repo / "specs" / feature / "spec.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def run_cli(repo: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Run the planlint CLI against ``repo`` and return the completed process.

    Injects ``COVERAGE_PROCESS_START`` so this subprocess's coverage is
    tracked, not just the parent test process's -- pytest-cov's own
    auto-installed subprocess hook (a .pth file in site-packages, active
    whenever this env var is set) reads it, no project-specific hook file
    needed. A caller-supplied ``env`` value for the same key always wins,
    never overridden.
    """
    subprocess_env = dict(os.environ if env is None else env)
    subprocess_env.setdefault("COVERAGE_PROCESS_START", str(_PYPROJECT))
    return subprocess.run(
        [sys.executable, "-m", "openspec_graph.cli", "--target", str(repo), *args],
        capture_output=True, text=True, check=False, env=subprocess_env,
        # cli.py's main() always forces its own stdout/stderr to UTF-8
        # (Defect D fix), regardless of the child's ambient encoding -- so
        # the parent side must decode as UTF-8 too, not whatever
        # locale.getpreferredencoding() would otherwise pick (e.g. cp1252 on
        # Windows), or non-ASCII content round-trips as mojibake here even
        # though the child emitted it correctly.
        encoding="utf-8",
    )


def normalize_root(text: str, root: Path) -> str:
    """Replace ``root`` with ``<ROOT>`` in CLI output, raw and JSON-escaped.

    ``json.dumps`` escapes each backslash as ``\\\\``, so on Windows the raw
    native path never textually matches inside ``--json`` output -- a bare
    ``text.replace(str(root), ...)`` normalizes POSIX only. And the CLI emits
    ``Path(args.target).resolve()``, whose spelling can differ from the
    ``str(root)`` a test built (8.3 short names, junctions, a symlinked
    ``TemporaryDirectory``) -- so a single fixed spelling can be a silent
    no-op, leaving the absolute path in the hash (this exact failure shipped
    the windows-latest CI leg red). Try every plausible spelling of the same
    directory, in both raw and JSON-escaped form, so the absolute path is
    always erased regardless of how ``resolve()`` rendered it.
    """
    spellings = {str(root), str(root.resolve())}
    for spelling in spellings:
        text = text.replace(spelling, "<ROOT>").replace(spelling.replace("\\", "\\\\"), "<ROOT>")
    return text


#: Environment variables that hand a child process this run's coverage identity.
#:
#: ``COVERAGE_FILE`` names the data file; ``COVERAGE_PROCESS_START`` names the
#: config a child reads on startup (``run_cli`` sets it deliberately); the
#: ``COV_CORE_*`` family is pytest-cov's own subprocess channel. Which of these
#: are actually present depends on the pytest-cov version and on whether the
#: outer run was invoked with ``--cov`` at all, so the set is stripped whole
#: rather than probed -- removing an unset name is a no-op, and the point is
#: that a nested run must not share this repo's coverage identity by any route.
COVERAGE_ENV_VARS: tuple[str, ...] = (
    "COVERAGE_FILE",
    "COVERAGE_PROCESS_START",
    "COV_CORE_SOURCE",
    "COV_CORE_CONFIG",
    "COV_CORE_DATAFILE",
    "COV_CORE_BRANCH",
)


def env_without_coverage(**overrides: str) -> dict[str, str]:
    """``os.environ`` with every coverage variable removed, plus ``overrides``.

    For subprocesses that run *their own* coverage session -- the nested
    ``pytest --cov`` runs that prove pytest-cov's ``--cov-fail-under`` gate
    fires. Those children must write their data somewhere this run will never
    combine, because they measure a throwaway package with different settings.

    Inheriting ``COVERAGE_FILE`` is the failure case, and it is not a test
    failure but a crash: with ``[tool.coverage.run] parallel = true`` the outer
    run combines every sibling data file at teardown, the nested run writes
    statement-only data (no ``--cov-branch``) into that same location, and
    ``combine`` raises ``DataError: Can't combine branch coverage data with
    statement data`` from inside pytest's teardown -- INTERNALERROR, exit 3,
    the whole suite gone rather than one test red.

    Nothing in this repository sets ``COVERAGE_FILE``, so the trap is ambient:
    it springs for anyone whose CI names a per-leg data file, the standard way
    to keep a build matrix's coverage separate.
    """
    env = {k: v for k, v in os.environ.items() if k not in COVERAGE_ENV_VARS}
    env.update(overrides)
    return env


@contextlib.contextmanager
def working_directory(path: Path) -> Iterator[None]:
    """Run the block with the process cwd set to ``path``, restoring it after.

    ``contextlib.chdir`` would do, but it is 3.11+ and this project supports
    3.10 (``requires-python``), so it is spelled out. Restores in a ``finally``
    so a failing assertion inside the block cannot strand the whole session in
    a temporary directory that the fixture is about to delete.
    """
    prior = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prior)


def run_tool_main(
    module_name: str,
    filename: str,
    *args: str,
    cwd: Path | None = None,
    pass_argv0: bool = True,
) -> int:
    """Call a ``tools/`` script's ``main()`` in-process and return its exit code.

    In-process rather than as a subprocess for the reason :func:`load_tool`
    already gives, but with a second consequence that only shows up on the
    gate scripts: **a subprocess's execution is invisible to coverage** unless
    it is handed the coverage config, and handing it over is not simply a
    matter of setting ``COVERAGE_PROCESS_START``. These scripts read
    ``Path("pyproject.toml")`` from the cwd, so their tests run them with
    ``cwd`` set to a throwaway directory -- and coverage resolves a *relative*
    ``source`` entry against that same cwd, so ``source = ["tools"]`` would
    resolve to a ``tools`` directory inside the fixture that does not exist.
    Four gate scripts read 0% that way while being thoroughly tested, which is
    a gate that cannot tell a tested script from an untested one.

    ``tools/`` is split on the argv convention, so ``pass_argv0`` is explicit
    rather than assumed: the eight hand-rolled scripts index ``argv[1]`` and
    are called as ``main(sys.argv)``, while the two argparse ones
    (``render_plugin_manifests``, ``render_rule_catalog``) are called as
    ``main(sys.argv[1:])``, because argparse treats every element it is given
    as an argument. Passing the wrong one is not a quiet mismatch in either
    direction -- argparse rejects the stray filename as an unrecognized
    argument, and a hand-rolled script silently drops the first real argument.

    The end-to-end `python tools/<script>.py` invocation the Makefile actually
    uses stays covered by its own subprocess test; this covers the logic.
    """
    tool = load_tool(module_name, filename)
    argv = [filename, *args] if pass_argv0 else list(args)
    if cwd is None:
        return int(tool.main(argv))
    with working_directory(cwd):
        return int(tool.main(argv))
