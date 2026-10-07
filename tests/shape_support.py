"""The AST engine behind ``tests/test_suite_shape.py``'s guards -- never asserting.

``shape-the-test-suite`` R-TSS-5 and R-TSS-6: every test carries exactly one of
:data:`TIERS`, and the tier is decided by what the test's own code under
``tests/`` *uses*, mechanically:

* ``e2e`` -- it reaches a process start: a reference to a function in
  :data:`PROCESS_STARTS`, called, passed or aliased, never in an annotation.
  ``subprocess.CompletedProcess`` and ``subprocess.TimeoutExpired`` start
  nothing and do not count.
* ``integration`` -- not ``e2e``, and it reads this repository's own tree: it
  uses ``__file__`` (a bare name, or an attribute such as ``detect.__file__``)
  or a name bound to it in a path whose final segments hold none of
  :data:`LABELLED_INPUT_SEGMENTS` (``.parent`` and ``..`` are applied first, so
  a path that climbs out of ``fixtures/`` counts); or it uses a function of
  :data:`SOURCE_READERS`, which reads a source file through an object rather
  than a path; or it uses a name imported from a script under
  :data:`SCRIPT_DIRECTORY`, which runs that script in-process. A binding is not
  a use: a name bound to a tree path counts where it is used, and where it is
  bound only when nothing uses it.
* ``unit`` -- neither.

What a test reaches: the functions, classes and module constants its body names
in its own module; the fixtures it requests -- its parameters, the autouse
fixtures in scope, ``usefixtures`` -- from its module or ``conftest.py``; and
the functions, classes and constants it imports from another module under
``tests/``, however the import is spelt; all transitively. A class reached
absorbs every method it defines. Nothing is listed by hand: ``run_cli``,
``load_tool``, ``run_tool_main`` and ``read_pyproject`` take their tiers from
their bodies.

The classification errs upward: a cheap test may land above its cost, but a
test whose own code starts a process or reads the tree never lands on
``unit``. The criterion stops at ``tests/``: a process the code under test
starts (``detect._current_sha``'s ``git rev-parse``) does not count (DEC-TSS-017).

Debugging a disputed tier: ``python -m pytest tests/test_suite_shape.py -k
criterion -o log_cli=true --log-cli-level=DEBUG`` logs every test's tier with
the chain of names that decided it.

The routing half (R-TSS-8) finds a test module that spawns the CLI in
``run_cli``'s shape or writes a spec at ``write_spec``'s or
``write_speckit_spec``'s path by hand. Each shape is read from the helper's
own body in ``tests/support.py``, so the guard follows the helper if it moves.
"""

from __future__ import annotations

import ast
import logging
import textwrap
from collections import Counter, deque
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

LOG = logging.getLogger(__name__)

#: The tiers, cheapest first. ``pyproject.toml`` registers exactly these.
TIERS: tuple[str, ...] = ("unit", "integration", "e2e")
UNIT, INTEGRATION, E2E = TIERS

_EXEC_SUFFIXES = ("l", "le", "lp", "lpe", "v", "ve", "vp", "vpe")

#: Module (dotted) -> the functions in it that start a process.
PROCESS_STARTS: dict[str, frozenset[str]] = {
    "subprocess": frozenset(
        {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"}
    ),
    "os": frozenset(
        {"system", "popen", "fork", "forkpty", "posix_spawn", "posix_spawnp"}
        | {f"exec{suffix}" for suffix in _EXEC_SUFFIXES}
        | {f"spawn{suffix}" for suffix in _EXEC_SUFFIXES}
    ),
    "asyncio": frozenset({"create_subprocess_exec", "create_subprocess_shell"}),
    "pty": frozenset({"spawn"}),
    "multiprocessing": frozenset({"Process", "Pool", "get_context"}),
    "concurrent.futures": frozenset({"ProcessPoolExecutor"}),
}

#: Module (dotted) -> the functions in it that read a source file through an
#: object rather than a path: ``inspect.getsource(parse.parse_spec)`` opens
#: ``openspec_graph/parse.py`` with no ``__file__`` in sight.
SOURCE_READERS: dict[str, frozenset[str]] = {
    "inspect": frozenset(
        {"getsource", "getsourcelines", "getsourcefile", "getfile", "findsource", "getcomments"}
    ),
    "linecache": frozenset({"getline", "getlines", "updatecache", "checkcache"}),
    "importlib.resources": frozenset(
        {"files", "read_text", "read_binary", "open_text", "open_binary", "path", "as_file"}
    ),
}

#: A path whose final segments hold one of these reads labelled input, not the tree.
LABELLED_INPUT_SEGMENTS = frozenset({"fixtures", "corpus"})

#: The package the support modules are imported from.
SUPPORT_PACKAGE = "tests"
#: This repository's script directory, beside ``tests/``. A name imported from
#: one of its scripts -- ``from tools import x``, or ``from x import y`` once a
#: test has put the directory on ``sys.path`` -- runs that script in-process,
#: which reads the tree as surely as ``load_tool`` does.
SCRIPT_DIRECTORY = "tools"
TEST_MODULE_GLOB = "test_*.py"
TEST_CLASS_PREFIX = "Test"
CONFTEST = "conftest.py"
PYTESTMARK = "pytestmark"

#: What ``__file__`` contributes to a path: a directory and a file, so that
#: ``.parent`` and ``..`` climb out of it the way they climb out of a real one.
_FILE_SEGMENTS = ("<dir>", "<file>")
_PARENT = ".."

Node = tuple[Path, str]
Resolver = Callable[[str], "list[str] | None"]


@dataclass(frozen=True)
class Evidence:
    """One signal and the chain of names through which a test reached it."""

    kind: str  # E2E or INTEGRATION
    what: str
    via: tuple[str, ...]

    def __str__(self) -> str:
        return " -> ".join((*self.via, self.what))


@dataclass(frozen=True)
class Classification:
    tier: str
    evidence: Evidence | None

    def __str__(self) -> str:
        return self.tier if self.evidence is None else f"{self.tier} ({self.evidence})"


@dataclass(frozen=True)
class _Facts:
    spawns: tuple[str, ...]
    reads: tuple[str, ...]
    edges: tuple[tuple[str, Node], ...]


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}


def _annotation_ids(tree: ast.AST) -> set[int]:
    """Every node inside an annotation: a type names a thing, it does not use it."""
    skip: set[int] = set()
    for node in ast.walk(tree):
        annotations: list[ast.expr] = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.returns:
            annotations.append(node.returns)
        elif isinstance(node, (ast.arg, ast.AnnAssign)) and node.annotation:
            annotations.append(node.annotation)
        for annotation in annotations:
            skip.update(id(sub) for sub in ast.walk(annotation))
    return skip


def _chain_root(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> ast.AST:
    """The whole path expression ``node`` sits in: ``/`` joins, attribute and
    method access, subscripts, and ``Path(...)`` wrapping."""
    current = node
    while True:
        parent = parents.get(current)
        wrapped = (
            (isinstance(parent, ast.BinOp) and isinstance(parent.op, ast.Div))
            or (isinstance(parent, (ast.Attribute, ast.Subscript)) and parent.value is current)
            or (
                isinstance(parent, ast.Call)
                and (
                    parent.func is current
                    or (
                        isinstance(parent.func, ast.Name)
                        and parent.func.id == "Path"
                        and current in parent.args
                    )
                )
            )
        )
        if not wrapped or parent is None:
            return current
        current = parent


def _append(segments: list[str], more: Iterable[str]) -> list[str]:
    """Join ``more`` onto ``segments`` the way a filesystem does: ``..`` climbs,
    and a ``..`` with nothing left to climb is kept for the left side to meet."""
    out = list(segments)
    for segment in more:
        if segment == _PARENT and out and out[-1] != _PARENT:
            out.pop()
        elif segment not in ("", "."):
            out.append(segment)
    return out


def path_segments(expression: ast.AST | None, resolve: Resolver | None = None, depth: int = 0) -> list[str]:
    """The segments a path expression ends at, in order: literals split on
    ``/``, names through ``resolve``, ``.parent`` and ``..`` applied, method
    arguments ignored (``.count("fixtures")`` names no segment)."""
    if expression is None or depth > 64:
        return []
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        return _append([], expression.value.replace("\\\\", "/").split("/"))
    if isinstance(expression, ast.BinOp) and isinstance(expression.op, ast.Div):
        left = path_segments(expression.left, resolve, depth + 1)
        return _append(left, path_segments(expression.right, resolve, depth + 1))
    if isinstance(expression, ast.Name):
        if expression.id == "__file__":
            return list(_FILE_SEGMENTS)
        found = resolve(expression.id) if resolve is not None else None
        return list(found) if found is not None else []
    if isinstance(expression, ast.Attribute):
        if expression.attr == "__file__":
            return list(_FILE_SEGMENTS)
        inner = path_segments(expression.value, resolve, depth + 1)
        return _append(inner, [_PARENT]) if expression.attr == "parent" else inner
    if isinstance(expression, ast.Subscript):
        return path_segments(expression.value, resolve, depth + 1)
    if isinstance(expression, ast.Call):
        func = expression.func
        if isinstance(func, ast.Attribute):
            base = path_segments(func.value, resolve, depth + 1)
            if func.attr == "joinpath":
                for arg in expression.args:
                    base = _append(base, path_segments(arg, resolve, depth + 1))
            return base
        segments: list[str] = []
        for arg in expression.args:
            segments = _append(segments, path_segments(arg, resolve, depth + 1))
        return segments
    return []


def _decorator_target(decorator: ast.expr) -> ast.expr:
    return decorator.func if isinstance(decorator, ast.Call) else decorator


def _is_fixture(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in function.decorator_list:
        target = _decorator_target(decorator)
        if (isinstance(target, ast.Attribute) and target.attr == "fixture") or (
            isinstance(target, ast.Name) and target.id == "fixture"
        ):
            return True
    return False


def _is_autouse(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(
        isinstance(decorator, ast.Call)
        and any(
            kw.arg == "autouse" and isinstance(kw.value, ast.Constant) and kw.value.value is True
            for kw in decorator.keywords
        )
        for decorator in function.decorator_list
    ) and _is_fixture(function)


def _usefixtures(decorators: Iterable[ast.expr]) -> list[str]:
    names: list[str] = []
    for decorator in decorators:
        if isinstance(decorator, ast.Call):
            target = decorator.func
            if isinstance(target, ast.Attribute) and target.attr == "usefixtures":
                names.extend(
                    arg.value
                    for arg in decorator.args
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
                )
    return names


def tier_of_mark(expression: ast.expr) -> str | None:
    """The tier a ``pytest.mark.<tier>`` (or ``mark.<tier>``) expression names, if any."""
    target = _decorator_target(expression)
    if isinstance(target, ast.Attribute) and target.attr in TIERS:
        base = target.value
        if (isinstance(base, ast.Attribute) and base.attr == "mark") or (
            isinstance(base, ast.Name) and base.id == "mark"
        ):
            return target.attr
    return None


def _assigned_names(statement: ast.stmt) -> list[str]:
    if isinstance(statement, ast.Assign):
        return [t.id for t in statement.targets if isinstance(t, ast.Name)]
    if isinstance(statement, ast.AnnAssign) and statement.value is not None:
        return [statement.target.id] if isinstance(statement.target, ast.Name) else []
    return []


def _assigned_value(statement: ast.stmt) -> ast.expr | None:
    if isinstance(statement, (ast.Assign, ast.AnnAssign)):
        return statement.value
    return None


def _split(qualified: str) -> tuple[str, str]:
    module, _, name = qualified.rpartition(".")
    return module, name


def import_bindings(tree: ast.AST) -> dict[str, str]:
    """Local name -> the dotted name an import bound it to, from any import in
    ``tree`` -- a function-local one included: a collision can only add a signal."""
    bindings: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    bindings[alias.asname] = alias.name
                else:
                    head = alias.name.split(".")[0]
                    bindings[head] = head
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            for alias in node.names:
                bindings[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return bindings


def dotted_name(node: ast.AST, bindings: dict[str, str]) -> str | None:
    """The dotted name ``node`` has through ``bindings``: ``sp.run`` -> ``subprocess.run``."""
    if isinstance(node, ast.Name):
        return bindings.get(node.id)
    if isinstance(node, ast.Attribute):
        inner = dotted_name(node.value, bindings)
        return f"{inner}.{node.attr}" if inner else None
    return None


def plant(root: Path, files: dict[str, str]) -> None:
    """Write planted module texts under ``root``, dedented; a key may climb out of it."""
    for relative, text in files.items():
        target = (root / relative).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")


class _Module:
    """One parsed module: what it defines, what its names are bound to, and
    which of its constants are rooted at ``__file__``."""

    def __init__(self, path: Path, program: Program) -> None:
        self.path = path
        self.program = program
        self.tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        self.parents = _parents(self.tree)
        self.skip = _annotation_ids(self.tree)
        self.functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
        self.classes: dict[str, ast.ClassDef] = {}
        self.constants: dict[str, ast.expr] = {}
        #: local name -> the dotted name an import bound it to.
        self.bindings = import_bindings(self.tree)
        for statement in self.tree.body:
            self._index(statement)
        self.fixtures = {name for name, fn in self.functions.items() if _is_fixture(fn)}
        self.autouse = sorted(name for name, fn in self.functions.items() if _is_autouse(fn))
        self.rooted: set[str] = set()
        self._segments: dict[str, list[str]] = {}

    def _index(self, statement: ast.stmt) -> None:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self.functions[statement.name] = statement
        elif isinstance(statement, ast.ClassDef):
            self.classes[statement.name] = statement
        elif not isinstance(statement, (ast.Import, ast.ImportFrom)):
            value = _assigned_value(statement)
            if value is not None:
                for name in _assigned_names(statement):
                    self.constants[name] = value

    def bind_rooted_constants(self) -> None:
        """Module constants rooted at ``__file__``, through other constants, to a fixed point."""
        changed = True
        while changed:
            changed = False
            for name, value in self.constants.items():
                if name not in self.rooted and self.mentions_root(value, set()):
                    self.rooted.add(name)
                    changed = True

    # -- names ------------------------------------------------------------------

    def dotted(self, node: ast.AST) -> str | None:
        """The dotted name an import gave ``node``: ``sp.run`` -> ``subprocess.run``."""
        return dotted_name(node, self.bindings)

    def support_target(self, qualified: str) -> tuple[_Module, str] | None:
        """``tests.<stem>.<name>[...]`` -> that module and the name, if it exists."""
        parts = qualified.split(".")
        if len(parts) < 3 or parts[0] != SUPPORT_PACKAGE:
            return None
        support = self.program.support(parts[1])
        return (support, parts[2]) if support is not None else None

    def is_rooted(self, name: str, local: set[str]) -> bool:
        if name == "__file__" or name in local or name in self.rooted:
            return True
        qualified = self.bindings.get(name)
        target = self.support_target(qualified) if qualified else None
        return target is not None and target[0].is_rooted(target[1], set())

    def mentions_root(self, expression: ast.AST, local: set[str]) -> bool:
        return any(
            (isinstance(sub, ast.Name) and self.is_rooted(sub.id, local))
            or (isinstance(sub, ast.Attribute) and sub.attr == "__file__")
            for sub in ast.walk(expression)
        )

    def constant_segments(self, name: str) -> list[str] | None:
        """Where a module constant's path ends, or ``None`` if it is no constant here."""
        if name in self._segments:
            return self._segments[name]
        if name in self.constants:
            self._segments[name] = []  # cycle guard
            self._segments[name] = path_segments(self.constants[name], self.constant_segments)
            return self._segments[name]
        qualified = self.bindings.get(name)
        target = self.support_target(qualified) if qualified else None
        return target[0].constant_segments(target[1]) if target else None

    def resolver(self, local_values: dict[str, ast.expr]) -> Resolver:
        def resolve(name: str) -> list[str] | None:
            if name in local_values:
                value = local_values.pop(name)  # a local is resolved once, never through itself
                try:
                    return path_segments(value, resolve)
                finally:
                    local_values[name] = value
            return self.constant_segments(name)

        return resolve

    def tree_use(self, node: ast.AST, local: set[str], resolve: Resolver) -> str | None:
        """What ``node`` reads of the tree, when it is a rooted use outside labelled input."""
        if not isinstance(getattr(node, "ctx", None), ast.Load):
            return None
        hit: str | None = None
        if isinstance(node, ast.Name) and self.is_rooted(node.id, local):
            hit = node.id
        elif isinstance(node, ast.Attribute) and node.attr == "__file__":
            hit = ast.unparse(node)
        if hit is None:
            return None
        final = path_segments(_chain_root(node, self.parents), resolve)
        return None if set(final) & LABELLED_INPUT_SEGMENTS else hit

    def signal_use(self, node: ast.AST) -> tuple[str, str] | None:
        """``(kind, what)`` when ``node`` names a process start, a source reader or a
        ``tools/`` script."""
        if not isinstance(node, (ast.Name, ast.Attribute)) or not isinstance(
            getattr(node, "ctx", None), ast.Load
        ):
            return None
        qualified = self.dotted(node)
        if not qualified:
            return None
        module, name = _split(qualified)
        if name in PROCESS_STARTS.get(module, frozenset()):
            return E2E, qualified
        if name in SOURCE_READERS.get(module, frozenset()):
            return INTEGRATION, qualified
        script = self.program.script(qualified)
        if script is not None:
            return INTEGRATION, f"{ast.unparse(node)} (runs {script} in-process)"
        return None

    def resolve(self, name: str) -> Node | None:
        """The definition ``name`` refers to here, following imports under ``tests/``."""
        if name in self.functions or name in self.classes or name in self.constants:
            return (self.path, name)
        qualified = self.bindings.get(name)
        target = self.support_target(qualified) if qualified else None
        return target[0].resolve(target[1]) if target else None

    def resolve_fixture(self, name: str) -> Node | None:
        if name in self.fixtures:
            return (self.path, name)
        target = self.resolve(name) if name in self.bindings else None
        if target is not None:
            return target
        conftest = self.program.conftest
        if conftest is not None and conftest is not self and name in conftest.fixtures:
            return (conftest.path, name)
        return None


class Program:
    """The modules of one ``tests/`` directory, analysed on demand.

    ``root`` holds the test modules and ``conftest.py``; a support module is
    looked up in ``root`` first and then in ``support_root``, so a planted
    tree under ``tmp_path`` can import this repository's real helpers.
    """

    def __init__(self, root: Path, support_root: Path | None = None) -> None:
        self.root = root
        self.repo_root = root.parent
        self.support_root = support_root
        self._modules: dict[Path, _Module] = {}
        self._facts: dict[Node, _Facts] = {}
        conftest = root / CONFTEST
        self.conftest = self.module(conftest) if conftest.is_file() else None

    def module(self, path: Path) -> _Module:
        if path not in self._modules:
            # Registered before its constants are bound, so a circular import ends here.
            self._modules[path] = module = _Module(path, self)
            module.bind_rooted_constants()
        return self._modules[path]

    def support(self, stem: str) -> _Module | None:
        """The module ``tests.<stem>`` names: a support module, or a test module
        another test imports from."""
        for directory in (self.root, self.support_root):
            if directory is not None and (directory / f"{stem}.py").is_file():
                return self.module(directory / f"{stem}.py")
        return None

    def script(self, qualified: str) -> str | None:
        """The ``tools/`` script a dotted import name runs, if it is one of this repository's."""
        parts = qualified.split(".")
        name = parts[1] if parts[0] == SCRIPT_DIRECTORY and len(parts) > 1 else parts[0]
        script = self.repo_root / SCRIPT_DIRECTORY / f"{name}.py"
        return f"{SCRIPT_DIRECTORY}/{name}.py" if script.is_file() else None

    def test_modules(self) -> list[Path]:
        return sorted(self.root.glob(TEST_MODULE_GLOB))

    # -- facts per definition ------------------------------------------------

    def facts(self, node: Node) -> _Facts:
        if node not in self._facts:
            self._facts[node] = self._compute_facts(node)
        return self._facts[node]

    def _compute_facts(self, node: Node) -> _Facts:
        path, name = node
        module = self.module(path)
        owner, _, method = name.partition(".")
        if method:
            return self._function_facts(module, module.classes[owner], method)
        if name in module.functions:
            return self._function_facts(module, module.functions[name], None)
        if name in module.classes:
            return self._class_facts(module, module.classes[name])
        return self._expression_facts(module, module.constants[name], name)

    def _references(self, module: _Module, nodes: Iterable[ast.AST], own: str) -> list[tuple[str, Node]]:
        edges: list[tuple[str, Node]] = []
        for sub in nodes:
            if id(sub) in module.skip or not isinstance(getattr(sub, "ctx", None), ast.Load):
                continue
            target: Node | None = None
            if isinstance(sub, ast.Name) and sub.id != own:
                target = module.resolve(sub.id)
            elif isinstance(sub, ast.Attribute):
                qualified = module.dotted(sub)
                found = module.support_target(qualified) if qualified else None
                target = found[0].resolve(found[1]) if found else None
            if target is not None:
                edges.append((ast.unparse(sub), target))
        return edges

    @staticmethod
    def _signals(module: _Module, nodes: Iterable[ast.AST]) -> tuple[list[str], list[str]]:
        spawns: list[str] = []
        reads: list[str] = []
        for sub in nodes:
            if id(sub) in module.skip:
                continue
            signal = module.signal_use(sub)
            if signal is not None:
                (spawns if signal[0] == E2E else reads).append(signal[1])
        return spawns, reads

    def _expression_facts(self, module: _Module, value: ast.expr, own: str) -> _Facts:
        nodes = list(ast.walk(value))
        spawns, reads = self._signals(module, nodes)
        return _Facts(tuple(spawns), tuple(reads), tuple(self._references(module, nodes, own)))

    def _class_facts(self, module: _Module, cls: ast.ClassDef) -> _Facts:
        nodes: list[ast.AST] = [*cls.bases, *cls.decorator_list]
        methods: list[tuple[str, Node]] = []
        for statement in cls.body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qualname = f"{cls.name}.{statement.name}"
                methods.append((qualname, (module.path, qualname)))
            else:
                nodes.extend(ast.walk(statement))
        spawns, reads = self._signals(module, nodes)
        resolve = module.resolver({})
        reads += [r for r in (module.tree_use(sub, set(), resolve) for sub in nodes) if r]
        edges = tuple(self._references(module, nodes, cls.name)) + tuple(methods)
        return _Facts(tuple(spawns), tuple(reads), edges)

    def _function_facts(
        self,
        module: _Module,
        container: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
        method: str | None,
    ) -> _Facts:
        function = container
        if method is not None:
            assert isinstance(container, ast.ClassDef)
            function = next(
                s
                for s in container.body
                if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)) and s.name == method
            )
        assert isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef))
        nodes = list(ast.walk(function))
        values: dict[str, ast.expr] = {}
        for sub in nodes:
            if isinstance(sub, (ast.Assign, ast.AnnAssign)) and sub.value is not None:
                for name in _assigned_names(sub):
                    values.setdefault(name, sub.value)
        # Locals rooted at __file__, to a fixed point: their bindings defer to their uses.
        local: set[str] = set()
        deferred: set[int] = set()
        changed = True
        while changed:
            changed = False
            for sub in nodes:
                if not isinstance(sub, (ast.Assign, ast.AnnAssign)) or id(sub) in deferred:
                    continue
                value = _assigned_value(sub)
                names = _assigned_names(sub)
                if value is not None and names and module.mentions_root(value, local):
                    local.update(names)
                    deferred.add(id(sub))
                    deferred.update(id(x) for x in ast.walk(value))
                    changed = True
        resolve = module.resolver(values)
        spawns, reads = self._signals(module, nodes)  # a signal counts wherever it is named
        used: set[str] = set()
        for sub in nodes:
            if id(sub) in module.skip or id(sub) in deferred:
                continue
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load) and sub.id in local:
                used.add(sub.id)
            read = module.tree_use(sub, local, resolve)
            if read:
                reads.append(read)
        for name in sorted(local - used):
            final = path_segments(values.get(name), resolve)
            if not set(final) & LABELLED_INPUT_SEGMENTS:
                reads.append(f"{name} (bound to the tree, never used)")
        edges = self._references(module, nodes, function.name)
        is_test_or_fixture = function.name.startswith("test_") or _is_fixture(function)
        if method is None and is_test_or_fixture:
            requested = [arg.arg for arg in (*function.args.posonlyargs, *function.args.args)]
            requested += _usefixtures(function.decorator_list)
            for parameter in requested:
                fixture = module.resolve_fixture(parameter)
                if fixture is not None and fixture != (module.path, function.name):
                    edges.append((parameter, fixture))
        return _Facts(tuple(spawns), tuple(reads), tuple(edges))

    # -- reach -----------------------------------------------------------------

    def _starts(self, module: _Module, test: str) -> list[tuple[str, Node]]:
        starts: list[tuple[str, Node]] = [("", (module.path, test))]
        scopes = [module] + ([self.conftest] if self.conftest and self.conftest is not module else [])
        for scope in scopes:
            starts += [(f"autouse {name}", (scope.path, name)) for name in scope.autouse]
        pytestmark = module.constants.get(PYTESTMARK)
        if pytestmark is not None:
            marks = pytestmark.elts if isinstance(pytestmark, (ast.List, ast.Tuple)) else [pytestmark]
            for name in _usefixtures(marks):
                fixture = module.resolve_fixture(name)
                if fixture is not None:
                    starts.append((name, fixture))
        return starts

    def classify(self, path: Path, test: str) -> Classification:
        module = self.module(path)
        queue: deque[tuple[Node, tuple[str, ...]]] = deque(
            (node, (label,) if label else ()) for label, node in self._starts(module, test)
        )
        seen: set[Node] = set()
        first: dict[str, Evidence] = {}
        while queue:
            node, via = queue.popleft()
            if node in seen:
                continue
            seen.add(node)
            facts = self.facts(node)
            if facts.spawns and E2E not in first:
                first[E2E] = Evidence(E2E, facts.spawns[0], via)
            if facts.reads and INTEGRATION not in first:
                first[INTEGRATION] = Evidence(INTEGRATION, facts.reads[0], via)
            if E2E in first:
                break
            for label, target in facts.edges:
                if target not in seen:
                    queue.append((target, (*via, label)))
        for tier in (E2E, INTEGRATION):
            if tier in first:
                return Classification(tier, first[tier])
        return Classification(UNIT, None)

    def tests(self, path: Path) -> list[str]:
        module = self.module(path)
        return [name for name in module.functions if name.startswith("test_")]

    def classifications(self) -> Iterator[tuple[Path, str, Classification]]:
        for path in self.test_modules():
            for test in self.tests(path):
                found = self.classify(path, test)
                LOG.debug("%s::%s: %s", path.name, test, found)
                yield path, test, found


# -- marks ---------------------------------------------------------------------


def _mark_list(value: ast.expr) -> list[ast.expr]:
    return list(value.elts) if isinstance(value, (ast.List, ast.Tuple)) else [value]


def module_marks(path: Path) -> tuple[dict[str, list[str]], list[str]]:
    """Per test, every tier it carries -- module ``pytestmark`` plus decorators,
    both levels counted -- and every shape the one-tier rule cannot count:
    a tier alias, a test class, a tier inside ``pytest.param(marks=...)``."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    module_tiers: list[str] = []
    forbidden: list[str] = []
    for statement in tree.body:
        if isinstance(statement, ast.ClassDef) and statement.name.startswith(TEST_CLASS_PREFIX):
            forbidden.append(f"a test class, whose items the one-tier guard cannot count: {statement.name}")
        value = _assigned_value(statement)
        if value is None:
            continue
        for name in _assigned_names(statement):
            if name == PYTESTMARK:
                module_tiers += [t for t in map(tier_of_mark, _mark_list(value)) if t]
            elif tier_of_mark(value):
                forbidden.append(f"a tier through an alias: {name} = {ast.unparse(value)}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "param":
            for keyword in node.keywords:
                if keyword.arg == "marks" and any(map(tier_of_mark, _mark_list(keyword.value))):
                    forbidden.append(f"a tier inside pytest.param marks, line {node.lineno}")
    tiers = {
        statement.name: module_tiers
        + [t for t in map(tier_of_mark, statement.decorator_list) if t]
        for statement in tree.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
        and statement.name.startswith("test_")
    }
    return tiers, forbidden


def tier_count_violations(root: Path) -> list[str]:
    """Every test without exactly one tier, and every shape that hides a tier, named."""
    found: list[str] = []
    for path in sorted(root.glob(TEST_MODULE_GLOB)):
        tiers, forbidden = module_marks(path)
        found += [f"{path.name}: {shape}" for shape in forbidden]
        found += [
            f"{path.name}::{test}: {', '.join(marks) or 'no tier'}"
            for test, marks in tiers.items()
            if len(marks) != 1
        ]
    return found


def criterion_disagreements(program: Program) -> list[str]:
    """Every test whose one tier disagrees with what it uses; idle on unmarked tests."""
    found: list[str] = []
    for path, test, classification in program.classifications():
        marks = module_marks(path)[0].get(test, [])
        if len(marks) == 1 and marks[0] != classification.tier:
            found.append(
                f"{path.name}::{test} is marked {marks[0]}, the criterion says {classification}"
            )
    return found


def tier_tally(program: Program) -> str:
    """Per module, the tier counts in :data:`TIERS` order, then the total."""
    per_module: dict[str, Counter[str]] = {}
    for path, _test, classification in program.classifications():
        per_module.setdefault(path.name, Counter())[classification.tier] += 1
    total: Counter[str] = Counter()
    lines = []
    for name, counts in per_module.items():
        total.update(counts)
        shape = next((t for t in TIERS if counts[t] == sum(counts.values())), "mixed")
        lines.append(f"{shape:12} {'/'.join(str(counts[t]) for t in TIERS):>10}  {name}")
    lines.append(
        f"total {'/'.join(TIERS)}: {'/'.join(str(total[t]) for t in TIERS)} of {sum(total.values())}"
    )
    return "\n".join(lines)

# -- routing (R-TSS-8) -----------------------------------------------------------

#: The shared module the routed helpers live in, and the helpers whose shapes
#: no other module under ``tests/`` may repeat by hand.
SUPPORT_MODULE = "support.py"
ROUTED_SPAWN = "run_cli"
ROUTED_WRITERS = ("write_spec", "write_speckit_spec")
WRITE_METHOD = "write_text"


@dataclass(frozen=True)
class RoutedShapes:
    """What a hand-rolled copy of a routed helper looks like, read from the helper."""

    spawn_module: str
    spawn_function: str
    spawn_literals: frozenset[str]
    writers: dict[str, tuple[str, ...]]


def _locals(function: ast.AST) -> dict[str, ast.expr]:
    return {
        target.id: node.value
        for node in ast.walk(function)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }


def _dict_resolver(assigned: dict[str, ast.expr]) -> Resolver:
    """Resolve a name to where its local assignment's path ends, once per name."""
    def resolve(name: str) -> list[str] | None:
        if name not in assigned:
            return None
        value = assigned.pop(name)
        try:
            return path_segments(value, resolve)
        finally:
            assigned[name] = value

    return resolve


def _process_start(call: ast.Call, bindings: dict[str, str]) -> tuple[str, str] | None:
    """``(module, function)`` when ``call`` starts a process, under any import spelling."""
    qualified = dotted_name(call.func, bindings)
    if qualified is None:
        return None
    module, name = _split(qualified)
    return (module, name) if name in PROCESS_STARTS.get(module, frozenset()) else None


def _argv(call: ast.Call) -> ast.expr | None:
    if call.args:
        return call.args[0]
    return next((kw.value for kw in call.keywords if kw.arg == "args"), None)


def _string_constants(
    expression: ast.AST | None, assigned: dict[str, ast.expr] | None = None, depth: int = 0
) -> list[str]:
    """The string literals of ``expression``, a name in ``assigned`` read through its value:
    ``argv = [...]; run(argv)`` holds what ``run([...])`` holds."""
    if expression is None or depth > 8:
        return []
    found: list[str] = []
    for sub in ast.walk(expression):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            found.append(sub.value)
        elif isinstance(sub, ast.Name) and assigned and sub.id in assigned:
            found += _string_constants(assigned[sub.id], assigned, depth + 1)
    return found


def routed_shapes(support: Path) -> RoutedShapes:
    """Read the routed helpers' shapes from their bodies in ``support``."""
    tree = ast.parse(support.read_text(encoding="utf-8"), filename=str(support))
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    spawn = functions[ROUTED_SPAWN]
    bindings = import_bindings(tree)
    call = next(
        node
        for node in ast.walk(spawn)
        if isinstance(node, ast.Call) and _process_start(node, bindings)
    )
    module, function = _process_start(call, bindings) or ("", "")
    writers: dict[str, tuple[str, ...]] = {}
    for name in ROUTED_WRITERS:
        writer = functions[name]
        write = next(
            node
            for node in ast.walk(writer)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == WRITE_METHOD
        )
        assert isinstance(write.func, ast.Attribute)
        writers[name] = tuple(path_segments(write.func.value, _dict_resolver(_locals(writer))))
    return RoutedShapes(module, function, frozenset(_string_constants(_argv(call))), writers)


def _routed_modules(root: Path) -> list[Path]:
    return sorted(path for path in root.glob("*.py") if path.name != SUPPORT_MODULE)


def _functions_and_module(tree: ast.Module) -> list[ast.AST]:
    return [tree, *(n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))]


def inline_cli_spawns(root: Path, shapes: RoutedShapes) -> list[str]:
    """Every spawn under ``root`` with ``run_cli``'s argv literals, outside the helper --
    however the process start is imported, and with the argv read through the locals
    and module constants it was built in."""
    found: set[str] = set()
    target = (shapes.spawn_module, shapes.spawn_function)
    for path in _routed_modules(root):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        bindings = import_bindings(tree)
        constants = {
            name: statement.value
            for statement in tree.body
            if isinstance(statement, (ast.Assign, ast.AnnAssign)) and statement.value is not None
            for name in _assigned_names(statement)
        }
        for scope in _functions_and_module(tree):
            assigned = {**constants, **(_locals(scope) if scope is not tree else {})}
            for node in ast.walk(scope):
                if not isinstance(node, ast.Call) or _process_start(node, bindings) != target:
                    continue
                if shapes.spawn_literals <= set(_string_constants(_argv(node), assigned)):
                    found.add(f"{path.name}:{node.lineno}")
    return sorted(found)


def _writer_for(segments: list[str], shapes: RoutedShapes) -> str | None:
    """The routed writer whose path ``segments`` spell, if any.

    A shape matches when its literals appear in order and the path carries no
    literal that only another, longer shape has: ``openspec/specs/<cap>/spec.md``
    holds ``specs`` and ``spec.md`` but also ``openspec``, so it is no SpecKit
    path, and no writer exists for it.
    """
    every = {literal for shape in shapes.writers.values() for literal in shape}
    for name, shape in shapes.writers.items():
        remaining = iter(segments)
        in_order = all(literal in remaining for literal in shape)
        foreign = (every - set(shape)) & set(segments)
        if in_order and not foreign:
            return name
    return None


def hand_written_specs(root: Path, shapes: RoutedShapes) -> list[str]:
    """Every ``write_text`` under ``root`` at a routed writer's path, named with it."""
    found: list[str] = []
    for path in _routed_modules(root):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for scope in _functions_and_module(tree):
            assigned = _locals(scope)
            for node in ast.walk(scope):
                if not (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == WRITE_METHOD
                ):
                    continue
                writer = _writer_for(path_segments(node.func.value, _dict_resolver(assigned)), shapes)
                if writer is not None:
                    found.append(f"{path.name}:{node.lineno} ({writer})")
    return sorted(set(found))


# -- converted loops (R-TSS-9) -------------------------------------------------------

#: The entry point a converted loop runs in-process.
IN_PROCESS_ENTRY = "main"
_LOOPS = (ast.For, ast.AsyncFor, ast.While, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


def _inside_loop(node: ast.AST, parents: dict[ast.AST, ast.AST], stop: ast.AST) -> bool:
    current = parents.get(node)
    while current is not None and current is not stop:
        if isinstance(current, _LOOPS):
            return True
        current = parents.get(current)
    return False


def converted_loop_violations(root: Path, converted: dict[str, tuple[str, ...]]) -> list[str]:
    """Each named test that does not run its loop in-process with exactly one
    ``run_cli`` outside any loop as its entry-point check."""
    found: list[str] = []
    for module, tests in sorted(converted.items()):
        tree = ast.parse((root / module).read_text(encoding="utf-8"), filename=module)
        parents = _parents(tree)
        functions = {
            node.name: node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for test in tests:
            function = functions.get(test)
            if function is None:
                found.append(f"{module}::{test}: not found")
                continue
            calls = [
                node
                for node in ast.walk(function)
                if isinstance(node, ast.Call)
                and (
                    (isinstance(node.func, ast.Name) and node.func.id == ROUTED_SPAWN)
                    or (isinstance(node.func, ast.Attribute) and node.func.attr == ROUTED_SPAWN)
                )
            ]
            looped = [call for call in calls if _inside_loop(call, parents, function)]
            entry = any(
                (isinstance(node, ast.Name) and node.id == IN_PROCESS_ENTRY)
                or (isinstance(node, ast.Attribute) and node.attr == IN_PROCESS_ENTRY)
                for node in ast.walk(function)
            )
            if len(calls) != 1:
                found.append(f"{module}::{test}: {len(calls)} {ROUTED_SPAWN} calls, not 1")
            if looped:
                found.append(f"{module}::{test}: {ROUTED_SPAWN} inside a loop")
            if not entry:
                found.append(f"{module}::{test}: no reference to {IN_PROCESS_ENTRY}")
    return found
