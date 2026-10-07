"""The helpers behind ``tests/test_static_ratchets.py`` -- never asserting.

``ratchet-test-types-and-docstrings`` R-TDR-1 to R-TDR-7 and R-TDR-16: each
helper takes what it judges as an argument -- the ``typecheck`` recipe, the
parsed ``[tool.mypy]`` table, the ``Options`` mypy itself loaded, a run's
stdout, a module's text, the dev extra -- and returns every offender it finds,
named. ``tests/test_static_ratchets.py`` feeds them the tree and asserts nothing
is named; ``tests/test_static_ratchets_planted.py`` feeds them planted input and
asserts each violation is named and each well-formed shape is not.

Shared here, uncollected, because those two collected modules need them
(DEC-TDR-012, R-TSS-2). Nothing here reads this repository: no path is rooted
at ``__file__``, so a test that reaches only these helpers stays ``unit``.

mypy's own reading is the authority on what an override does
(DEC-TDR-015): :func:`load_mypy_config` loads a configuration through
``mypy.main.process_options``, which applies ``strict`` through mypy's own
callback, and :func:`option_differences` compares ``Options.snapshot()`` of the
global options with that of ``clone_for_module`` for each module.
"""

from __future__ import annotations

import ast
import io
import json
import os
import re
import shlex
import sys
import tokenize
from collections import Counter
from collections.abc import Collection, Iterable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

from mypy.main import process_options
from mypy.options import Options
from packaging.requirements import Requirement

from tests.support import COVERAGE_ENV_VARS

#: R-TDR-1: the recipe, the trees, the six keys and the four fixed values.
TYPECHECK_RECIPE = "python -m mypy --config-file pyproject.toml"
MYPY_TREES = ("openspec_graph", "tools", "tests")
MYPY_FIXED: dict[str, object] = {
    "explicit_package_bases": True, "strict": True, "warn_unreachable": True, "python_version": "3.10",
}
MYPY_KEYS = frozenset({"files", "mypy_path", *MYPY_FIXED})
#: R-TDR-2: the codes the tests entry may list, and how that entry is spelled.
LISTABLE_CODES = frozenset(
    {"no-untyped-def", "attr-defined", "arg-type", "type-arg", "no-any-return", "index", "union-attr"}
)
TESTS_ENTRY = "tests.*"
UNUSED_IGNORE = "unused-ignore"
#: mypy 1.11.0's bookkeeping in ``snapshot()``, the one field never compared (DEC-TDR-015).
_BOOKKEEPING = frozenset({"unused_configs"})
_DISABLED_FIELDS = frozenset({"disable_error_code", "disabled_error_codes"})
PLATFORMS = ("linux", "win32")
#: R-TDR-16: the first mypy release that accepts ``-O json`` (DEC-TDR-014).
MYPY_FLOOR = ">=1.11"
#: DEC-TDR-016: what hides code from mypy with no comment, and R-TDR-6's one allowed site.
UNCHECKED_NAMES = frozenset({"no_type_check", "no_type_check_decorator", "TYPE_CHECKING", "MYPY", "PY2", "PY3"})
ALLOWED_VERSION_CHECK = ("tests/support.py", "read_pyproject")
_IGNORE = re.compile(r"#\s*type:\s*ignore(?:\s*\[([^\]#]*)\])?")
_MYPY_LINE = "# mypy: "  # mypy/util.py get_mypy_comments, by physical line

Ignore = tuple[str, int, list[str] | None, str]  # path, line, codes (None: bare), waived line


# --- the configuration: recipe, keys, the tests entry -------------------------


def makefile_recipe(text: str, target: str) -> list[str]:
    """The recipe lines of ``target`` in Makefile ``text``, stripped."""
    lines = text.splitlines()
    starts = [n for n, line in enumerate(lines) if line.startswith(f"{target}:")]
    recipe: list[str] = []
    for line in lines[starts[0] + 1:] if starts else []:
        if not line.startswith("\t"):
            break
        recipe.append(line.strip())
    return recipe


def mypy_config_problems(recipe: Sequence[str], table: Mapping[str, Any]) -> list[str]:
    """R-TDR-1: the recipe names its configuration file and no path; the table holds exactly its keys."""
    commands = [line for line in recipe if not line.lstrip("@").startswith("#")]
    problems = [] if commands == [TYPECHECK_RECIPE] else [f"typecheck recipe {commands} is not [{TYPECHECK_RECIPE!r}]"]
    for command in commands:
        argv = shlex.split(command)[3:]
        if "--config-file pyproject.toml" not in command:
            problems.append(f"{command!r} names no configuration file; a stray mypy.ini or .mypy.ini would win")
        paths = [a for i, a in enumerate(argv) if not a.startswith("-") and (i == 0 or argv[i - 1] != "--config-file")]
        if paths:
            problems.append(f"{command!r} passes paths {paths}, which override [tool.mypy] files")
    allowed = MYPY_KEYS | ({"overrides"} if table.get("overrides") else set())
    problems += [f"[tool.mypy] lacks {key}" for key in sorted(MYPY_KEYS - set(table))]
    problems += [f"[tool.mypy] sets {key}, a key no guard measured (DEC-TDR-016)" for key in sorted(set(table) - allowed)]
    files = table.get("files")
    missing = [tree for tree in MYPY_TREES if not isinstance(files, list) or tree not in files]
    problems += [f"[tool.mypy] files {files!r} lacks {missing}"] if missing else []
    if table.get("mypy_path") not in ("tools", ["tools"]):
        problems.append(f"[tool.mypy] mypy_path is {table.get('mypy_path')!r}, not 'tools' alone")
    problems += [f"[tool.mypy] {k} is {table.get(k)!r}, not {v!r}" for k, v in MYPY_FIXED.items() if table.get(k) != v]
    return problems


def _is_tests_entry(entry: Mapping[str, Any]) -> bool:
    return entry.get("module") in (TESTS_ENTRY, [TESTS_ENTRY])


def listed_codes(overrides: Sequence[Mapping[str, Any]]) -> tuple[list[str], list[str]]:
    """R-TDR-2: the codes the one ``tests.*`` entry lists, and what is wrong with its shape."""
    entries = [entry for entry in overrides if _is_tests_entry(entry)]
    problems = [f"{len(entries)} overrides are spelled {TESTS_ENTRY!r}; the listed codes sit in one"] * (len(entries) > 1)
    listed: list[str] = []
    for entry in entries:
        extra = sorted(set(entry) - {"module", "disable_error_code"})
        problems += [f"the tests entry sets {extra} beside disable_error_code"] if extra else []
        codes = entry.get("disable_error_code")
        if not isinstance(codes, list) or not codes:
            problems.append("the tests entry lists no code; the commit that empties it removes it")
        else:
            listed += [str(code) for code in codes]
    problems += [f"{code} is not one of R-TDR-2's seven codes" for code in sorted(set(listed) - LISTABLE_CODES)]
    return listed, problems


# --- mypy's own reading of the configuration (DEC-TDR-015) ----------------------


def load_mypy_config(config: Path) -> tuple[Options, str]:
    """Load ``config`` as mypy's command line does, with its strict callback; return the stderr text.

    ``parse_config_file`` sets ``MYPY_CONFIG_FILE_DIR`` in ``os.environ``, so the
    environment is restored afterwards.
    """
    saved = dict(os.environ)
    stderr = io.StringIO()
    try:
        _, options = process_options(
            ["--config-file", str(config)], require_targets=False, stdout=io.StringIO(), stderr=stderr
        )
    finally:
        for key in set(os.environ) - set(saved):
            del os.environ[key]
        os.environ.update(saved)
    return options, stderr.getvalue()


def option_differences(options: Options, modules: Iterable[str]) -> dict[str, dict[str, tuple[object, object]]]:
    """Per module, each field where ``clone_for_module`` differs from the global options."""
    base = options.snapshot()
    found: dict[str, dict[str, tuple[object, object]]] = {}
    for module in modules:
        clone = options.clone_for_module(module).snapshot()
        fields = {
            key: (base.get(key), clone.get(key))
            for key in sorted(set(base) | set(clone))
            if key not in _BOOKKEEPING and base.get(key) != clone.get(key)
        }
        if fields:
            found[module] = fields
    return found


def override_problems(options: Options, stderr: str, modules: Iterable[str], listed: Collection[str]) -> list[str]:
    """R-TDR-2: each test module differs from the global options only by disabling exactly ``listed``."""
    problems = [f"mypy wrote to stderr loading the configuration: {stderr!r}"] if stderr else []
    base = {code.code for code in options.disabled_error_codes}
    modules = list(modules)
    differences = option_differences(options, modules)
    for module in modules:
        fields = differences.get(module, {})
        problems += [f"{module}: {k} {a!r} -> {b!r}" for k, (a, b) in fields.items() if k not in _DISABLED_FIELDS]
        added = {code.code for code in options.clone_for_module(module).disabled_error_codes} - base
        if added != set(listed):
            problems.append(f"{module}: disables {sorted(added)}, not the listed {sorted(listed)}")
    return problems


def _ini_value(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(_ini_value(item) for item in value)
    return str(value)


def derive_config(table: Mapping[str, Any]) -> str:
    """mypy INI text for ``table`` less the tests entry: every other key and override kept (R-TDR-5)."""
    lines = ["[mypy]", *(f"{k} = {_ini_value(v)}" for k, v in table.items() if k != "overrides")]
    overrides = list(table.get("overrides", []))
    dropped = next((entry for entry in overrides if _is_tests_entry(entry)), None)
    for entry in overrides:
        if entry is dropped:
            continue
        module = entry.get("module", "")
        lines += ["", f"[mypy-{_ini_value(module).replace(', ', ',')}]"]
        lines += [f"{k} = {_ini_value(v)}" for k, v in entry.items() if k != "module"]
    return "\n".join(lines) + "\n"


def derived_problems(derived: Options, source: Options, modules: Iterable[str]) -> list[str]:
    """R-TDR-5: the derived configuration is ``source`` less the tests entry, and changes no test module."""
    a, b = source.snapshot(), derived.snapshot()
    skip = _BOOKKEEPING | {"config_file", "per_module_options"}
    problems = [f"derived {k}: {a.get(k)!r} != {b.get(k)!r}" for k in sorted(set(a) | set(b)) if k not in skip and a.get(k) != b.get(k)]
    expected = {k: v for k, v in source.per_module_options.items() if k != TESTS_ENTRY}
    if derived.per_module_options != expected:
        problems.append(f"derived per-module options {derived.per_module_options!r} != {expected!r}")
    for module, fields in option_differences(derived, modules).items():
        problems += [f"derived, {module}: {k} {x!r} -> {y!r}" for k, (x, y) in fields.items()]
    return problems


# --- the occurrence run (R-TDR-5) ------------------------------------------------


def run_environment(base: Mapping[str, str]) -> dict[str, str]:
    """``base`` without the coverage variables or ``MYPYPATH``, which mypy puts ahead of ``mypy_path``."""
    return {key: value for key, value in base.items() if key not in (*COVERAGE_ENV_VARS, "MYPYPATH")}


def mypy_errors(stdout: str, stderr: str, returncode: int) -> tuple[list[dict[str, Any]], list[str]]:
    """The ``-O json`` error objects under ``tests/``, and every reason the run cannot be read."""
    problems = [f"mypy wrote to stderr: {stderr!r}"] if stderr else []
    problems += [f"mypy exited {returncode}, not 0 or 1"] if returncode not in (0, 1) else []
    errors: list[dict[str, Any]] = []
    for number, line in enumerate(stdout.splitlines(), 1):
        if not line.strip():
            continue  # a run with nothing to report prints one newline
        try:
            found = json.loads(line)
        except json.JSONDecodeError:
            found = None
        if not isinstance(found, dict):
            problems.append(f"stdout line {number} is not a JSON object: {line!r}")
        elif found.get("severity") == "error" and not found.get("code"):
            problems.append(f"an error without a code: {line}")
        elif found.get("severity") == "error":
            path = str(found.get("file", "")).replace("\\", "/")
            errors += [{**found, "file": path}] if path.startswith("tests/") else []
    return errors, problems


def platform_only(runs: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[str]:
    """Every (file, line, code) one platform reports and another does not (R-TDR-3)."""
    keyed = {name: Counter((e["file"], e["line"], e["code"]) for e in errors) for name, errors in runs.items()}
    problems: list[str] = []
    for name, keys in keyed.items():
        others: Counter[tuple[Any, Any, Any]] = Counter()
        for other, found in keyed.items():
            others |= found if other != name else Counter()
        problems += [f"platform-only ({name}): {f}:{n} [{c}]; fix it, never list it" for f, n, c in keys - others]
    return problems


def ceiling_problems(
    listed: Collection[str],
    ceilings: Mapping[str, int],
    counts: Mapping[str, int] | None = None,
    *,
    table: str = "MYPY_TESTS_CEILINGS",
    lister: str = "the override",
    where: str = "under tests/",
    unit: str = "occurrence",
) -> list[str]:
    """R-TDR-4, R-TDR-5 and R-TDR-9: the listed keys and the ceilings are one set, and each count is exact.

    The defaults word it for mypy's codes; :func:`docstring_ceiling_problems`
    words it for the docstring pairs.
    """
    problems = [f"{key} is listed without a ceiling in {table}" for key in sorted(set(listed) - set(ceilings))]
    problems += [f"{table} holds {key}, which {lister} does not list" for key in sorted(set(ceilings) - set(listed))]
    if counts is None:
        return problems
    for key in sorted(set(listed) | set(counts)):
        count, ceiling = counts.get(key, 0), ceilings.get(key, 0)
        if key not in listed:
            problems.append(f"{key} occurs {count} times {where} and is not listed")
        elif count == 0:
            problems.append(f"{key} is stale: no {unit}; remove it from {lister} and the ceilings")
        elif count > ceiling:
            problems.append(f"{key}: {count} {unit}s, above its ceiling of {ceiling}")
        elif count < ceiling:
            problems.append(f"lower {key} from {ceiling} to {count}")
    return problems


# --- comments, stubs, names and conditions (R-TDR-7, DEC-TDR-006, DEC-TDR-016) --


def read_comments(path: str, text: str) -> tuple[list[Ignore], list[str]]:
    """Each inline ignore in ``text`` keyed by its waived line, and every comment or line configuring mypy."""
    ignores: list[Ignore] = []
    problems: list[str] = []
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type != tokenize.COMMENT:
            continue
        match = _IGNORE.search(token.string)
        if match:
            codes = None if match[1] is None else [c.strip() for c in match[1].split(",") if c.strip()]
            ignores.append((path, token.start[0], codes, " ".join(token.line[: token.start[1]].split())))
        if token.string[1:].lstrip().startswith("mypy:"):
            problems.append(f"{path}:{token.start[0]}: a comment that configures mypy")
    problems += [f"{path}:{n}: a line mypy reads as configuration" for n, line in enumerate(text.split("\n"), 1) if line.startswith(_MYPY_LINE)]
    return ignores, problems


def waiver_problems(ignores: Iterable[Ignore], recorded: Iterable[tuple[str, str, str]], listed: Collection[str]) -> list[str]:
    """R-TDR-7: the ignores and the recorded waivers are one multiset, each holding one code."""
    remaining = Counter(recorded)
    problems: list[str] = []
    for path, line, codes, key in ignores:
        where, named = f"{path}:{line}", [code for code in codes or [] if code != UNUSED_IGNORE]
        unused = UNUSED_IGNORE in (codes or [])
        if len(named) != 1:
            problems.append(f"{where}: an ignore holding {len(named)} codes besides {UNUSED_IGNORE}: {codes}")
        elif unused and named[0] not in listed:
            problems.append(f"{where}: {UNUSED_IGNORE} beside {named[0]}, which the override does not list")
        elif not unused and named[0] in listed:
            problems.append(f"{where}: {named[0]} is listed, so its waiver needs {UNUSED_IGNORE}")
        entry = (path, ",".join(named), key)
        if remaining[entry] > 0:
            remaining[entry] -= 1
        else:
            problems.append(f"{where}: unrecorded waiver {entry!r}; MYPY_WAIVERS only shrinks")
    return problems + [f"recorded waiver {entry!r} is no longer in the tree" for entry in remaining.elements()]


def stub_problems(paths: Iterable[str]) -> list[str]:
    """Every ``.pyi`` under the three trees: mypy reads it in place of its module."""
    return [f"{p}: a stub mypy reads in place of its module" for p in sorted(paths) if p.endswith(".pyi") and p.split("/")[0] in MYPY_TREES]


def _branch_tests(tree: ast.AST, scope: str) -> Iterator[tuple[str, ast.expr]]:
    for node in ast.iter_child_nodes(tree):
        inner = scope
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            inner = node.name if scope == "<module>" else f"{scope}.{node.name}"
        if isinstance(node, (ast.If, ast.While, ast.IfExp, ast.Assert)):
            yield scope, node.test
        elif isinstance(node, ast.match_case) and node.guard is not None:
            yield scope, node.guard
        yield from _branch_tests(node, inner)


def _reads_sys_version_or_platform(test: ast.expr) -> bool:
    return any(
        isinstance(sub, ast.Attribute) and sub.attr in ("version_info", "platform")
        and isinstance(sub.value, ast.Name) and sub.value.id == "sys"
        for sub in ast.walk(test)
    )


def hidden_code(path: str, text: str) -> list[str]:
    """Each unchecked name, and each branch test on ``sys.version_info`` or ``sys.platform`` but R-TDR-6's one."""
    tokens = tokenize.generate_tokens(io.StringIO(text).readline)
    problems = [f"{path}:{t.start[0]}: {t.string}" for t in tokens if t.type == tokenize.NAME and t.string in UNCHECKED_NAMES]
    allowed = path == ALLOWED_VERSION_CHECK[0]
    for scope, test in _branch_tests(ast.parse(text), "<module>"):
        if not _reads_sys_version_or_platform(test):
            continue
        if allowed and scope == ALLOWED_VERSION_CHECK[1]:
            allowed = False
            continue
        problems.append(f"{path}:{test.lineno}: a branch test in {scope} that mypy may judge: {ast.unparse(test)}")
    return problems


def dev_extra_problems(entries: Iterable[str]) -> list[str]:
    """R-TDR-16: one ``mypy`` entry floored exactly at :data:`MYPY_FLOOR`, and no entry pinned."""
    requirements = [Requirement(entry) for entry in entries]
    mypy = [r for r in requirements if r.name.lower() == "mypy"]
    problems = [] if len(mypy) == 1 else [f"{len(mypy)} dev-extra entries name mypy, not 1"]
    problems += [f"{str(r)!r} is not floored exactly {MYPY_FLOOR!r} (-O json)" for r in mypy if str(r.specifier) != MYPY_FLOOR]
    problems += [f"{str(r)!r} pins a version" for r in requirements if any(s.operator in ("==", "===") for s in r.specifier)]
    return problems


# --- docstrings by per-file ratchet (R-TDR-8, R-TDR-9, DEC-TDR-009) --------------

#: R-TDR-8: the four rules selected, the trees they are ratcheted in, and the policy key.
DOCSTRING_CODES = ("D100", "D101", "D102", "D103")
DOCSTRING_TREES = ("openspec_graph", "tools")
POLICY_KEY = "tests/*"
PER_FILE_IGNORES = "[tool.ruff.lint.per-file-ignores]"
_D_RULE = re.compile(r"D\d*")  # a pydocstyle selector, fully matched: `D`, `D1`, `D103`; never `DTZ`
#: ruff's `noqa` grammar as measured (DEC-TDR-009): upper-case codes separated by
#: commas, whitespace or both, the list ending at the first token that is not a
#: code; a line directive anywhere in a comment, and the file-level `ruff:` and
#: `flake8:` forms, whose prefixes are matched in any case.
_CODE_LIST = r"[A-Z]+[0-9]+(?:[\s,]+[A-Z]+[0-9]+)*"
_NOQA = re.compile(rf"#\s*(?i:noqa)\s*:\s*({_CODE_LIST})")
_FILE_NOQA = re.compile(rf"#\s*(?i:ruff|flake8)\s*:\s*(?i:noqa)\s*:\s*({_CODE_LIST})")


def _d_codes(codes: object) -> list[str]:
    return [str(code) for code in codes if _D_RULE.fullmatch(str(code))] if isinstance(codes, list) else []


def _is_ratchet_key(key: str) -> bool:
    """One concrete file under the package or ``tools/``: no glob character."""
    return key.split("/")[0] in DOCSTRING_TREES and key.endswith(".py") and not set(key) & set("*?[]{}!")


def docstring_config_problems(lint: Mapping[str, Any]) -> tuple[dict[str, list[str]], list[str]]:
    """R-TDR-8 over a parsed ``[tool.ruff.lint]``: the ratchet entries (file -> ``D`` codes), and the offenders."""
    missing = [code for code in DOCSTRING_CODES if code not in lint.get("select", [])]
    problems = [f"select lacks {missing}"] if missing else []
    for key in ("select", "extend-select", "ignore", "extend-ignore"):
        extra = [c for c in _d_codes(lint.get(key)) if key.endswith("ignore") or c not in DOCSTRING_CODES]
        problems += [f"{key} holds {extra}: only {list(DOCSTRING_CODES)} are selected, never ignored"] if extra else []
    if "pydocstyle" in lint:
        problems.append("a [tool.ruff.lint.pydocstyle] table sets a convention no selected verdict depends on (R-TDR-10)")
    table = lint.get("per-file-ignores", {})
    lacking = [code for code in DOCSTRING_CODES if code not in _d_codes(table.get(POLICY_KEY))]
    problems += [f"{POLICY_KEY} lacks {lacking}, its policy exemption"] if lacking else []
    entries: dict[str, list[str]] = {}
    for key, codes in table.items():
        found = _d_codes(codes)
        if not found or key == POLICY_KEY:
            continue
        if _is_ratchet_key(key):
            entries[key] = found
            beyond = [code for code in found if code not in DOCSTRING_CODES]
            problems += [f"ratchet entry {key!r} lists {beyond}, beyond the four"] if beyond else []
        else:
            problems.append(f"per-file-ignores {key!r} carries {found}: only a concrete file under openspec_graph/ or tools/, or {POLICY_KEY}, may")
    for key, codes in lint.get("extend-per-file-ignores", {}).items():
        found = _d_codes(codes)
        problems += [f"extend-per-file-ignores {key!r} carries {found}: no D code may sit there"] if found else []
    return entries, problems


def noqa_problems(path: str, text: str) -> list[str]:
    """Each comment in ``text`` holding a ``noqa`` directive, read as ruff reads it, that names a ``D`` code."""
    problems: list[str] = []
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type != tokenize.COMMENT:
            continue
        lists = [match[1] for pattern in (_NOQA, _FILE_NOQA) for match in pattern.finditer(token.string)]
        named = [code for codes in lists for code in re.split(r"[\s,]+", codes) if _D_RULE.fullmatch(code)]
        problems += [f"{path}:{token.start[0]}: a noqa naming {named}: {token.string}"] if named else []
    return problems


def ruff_docstring_command(*paths: str) -> list[str]:
    """The occurrence run: no configuration file, no ignore file and no ``noqa`` honoured (DEC-TDR-009)."""
    return [
        sys.executable, "-m", "ruff", "check", "--no-cache", "--isolated", "--no-respect-gitignore",
        "--ignore-noqa", "--select", ",".join(DOCSTRING_CODES), "--output-format", "json", "--exit-zero", *paths,
    ]


def _relative(filename: str, roots: Sequence[str]) -> str | None:
    path = filename.replace("\\", "/")
    for root in roots:
        base = root.replace("\\", "/").rstrip("/") + "/"
        if path.startswith(base) or path.casefold().startswith(base.casefold()):  # a drive letter's case
            return path[len(base):]
    return None


def docstring_counts(stdout: str, roots: Sequence[str], stderr: str, returncode: int) -> tuple[dict[str, dict[str, int]], list[str]]:
    """ruff's JSON findings as file -> code -> count, each path relative to a spelling of the root, in POSIX form."""
    problems = [f"ruff wrote to stderr: {stderr!r}"] if stderr else []
    problems += [f"ruff exited {returncode}, not 0"] if returncode != 0 else []
    try:
        findings = json.loads(stdout)
    except json.JSONDecodeError:
        findings = None
    if not isinstance(findings, list):
        return {}, [*problems, f"ruff's stdout is not a JSON list: {stdout[:200]!r}"]
    counts: dict[str, dict[str, int]] = {}
    for finding in findings:
        path = _relative(str(finding.get("filename", "")), roots) if isinstance(finding, dict) else None
        if path is None:
            problems.append(f"a finding outside {list(roots)}: {finding!r}")
            continue
        codes = counts.setdefault(path, {})
        codes[str(finding.get("code"))] = codes.get(str(finding.get("code")), 0) + 1
    return counts, problems


def docstring_ceiling_problems(
    entries: Mapping[str, Iterable[str]],
    ceilings: Mapping[str, Mapping[str, int]],
    counts: Mapping[str, Mapping[str, int]] | None = None,
) -> list[str]:
    """R-TDR-9: the ratchet pairs and the ceilings' pairs are one set, and each pair's count is exact."""

    def flat(table: Mapping[str, Mapping[str, int]]) -> dict[str, int]:
        return {f"{path} {code}": count for path, codes in table.items() for code, count in codes.items()}

    listed = [f"{path} {code}" for path, codes in entries.items() for code in codes]
    return ceiling_problems(
        listed, flat(ceilings), None if counts is None else flat(counts), table="DOCSTRING_CEILINGS",
        lister=PER_FILE_IGNORES, where="under openspec_graph/ and tools/", unit="finding",
    )
