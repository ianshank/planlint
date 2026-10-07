"""The AST engine behind ``tests/test_suite_shape.py``'s tier guards -- never asserting.

``shape-the-test-suite`` R-TSS-5 and R-TSS-6: every test carries exactly one of
:data:`TIERS`, and the tier is decided by what the test *uses*, mechanically:

* ``e2e`` -- it reaches a process start: a reference to one of the functions in
  :data:`PROCESS_STARTS`, called, passed or aliased, never in an annotation.
  ``subprocess.CompletedProcess`` and ``subprocess.TimeoutExpired`` start
  nothing and do not count.
* ``integration`` -- not ``e2e``, and it reads this repository's own tree: it
  uses ``__file__`` (a bare name, or an attribute such as ``detect.__file__``)
  or a name bound to it, in a path expression whose chain carries no segment in
  :data:`LABELLED_INPUT_SEGMENTS`. A binding is not a use: a name bound to a tree
  path counts where it is used, and counts where it is bound only when nothing
  uses it. A name imported from a script under :data:`SCRIPT_DIRECTORY` runs
  that script in-process and counts the same way.
* ``unit`` -- neither.

What a test reaches: the functions, classes and module constants its body names
in its own module; the fixtures it requests -- its parameters, the autouse
fixtures in scope, ``usefixtures`` -- from its module or ``conftest.py``; and
the functions, classes and constants it imports from an uncollected support
module under ``tests/``; all transitively. A class reached absorbs every method
it defines. Nothing is listed by hand: ``run_cli``, ``load_tool``,
``run_tool_main`` and ``read_pyproject`` take their tiers from their bodies.

The classification errs upward: a cheap test may land above its cost, but a
test that starts a process or reads the tree never lands on ``unit``.

Debugging a disputed tier: ``python -m pytest tests/test_suite_shape.py -k
criterion -o log_cli=true --log-cli-level=DEBUG`` logs every test's tier with
the chain of names that decided it.
"""

from __future__ import annotations

import ast
import logging
from collections import Counter, deque
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

LOG = logging.getLogger(__name__)

#: The tiers, cheapest first. ``pyproject.toml`` registers exactly these.
TIERS: tuple[str, ...] = ("unit", "integration", "e2e")
UNIT, INTEGRATION, E2E = TIERS

_EXEC_SUFFIXES = ("l", "le", "lp", "lpe", "v", "ve", "vp", "vpe")

#: Module name -> the functions in it that start a process.
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
}

#: A path chain carrying one of these segments reads labelled input, not the tree.
LABELLED_INPUT_SEGMENTS = frozenset({"fixtures", "corpus"})

#: The package the support modules are imported from.
SUPPORT_PACKAGE = "tests"
#: This repository's script directory, beside ``tests/``. A name imported from
#: one of its scripts -- ``from tools import x``, or ``from x import y`` once a
#: test has put the directory on ``sys.path`` -- runs that script in-process,
#: which reads the tree as surely as ``load_tool`` does.
SCRIPT_DIRECTORY = "tools"
TEST_MODULE_GLOB = "test_*.py"
CONFTEST = "conftest.py"
PYTESTMARK = "pytestmark"

Node = tuple[Path, str]


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


def _labelled(expression: ast.AST) -> bool:
    return any(
        isinstance(sub, ast.Constant)
        and isinstance(sub.value, str)
        and bool(set(sub.value.replace("\\", "/").split("/")) & LABELLED_INPUT_SEGMENTS)
        for sub in ast.walk(expression)
    )


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


class _Module:
    """One parsed module: what it defines, imports and binds to the tree."""

    def __init__(self, path: Path, program: Program) -> None:
        self.path = path
        self.program = program
        self.tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        self.parents = _parents(self.tree)
        self.skip = _annotation_ids(self.tree)
        self.functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
        self.classes: dict[str, ast.ClassDef] = {}
        self.constants: dict[str, ast.expr] = {}
        self.imported: dict[str, tuple[str, str]] = {}  # local name -> (support stem, name)
        self.support_aliases: dict[str, str] = {}  # local name -> support stem
        self.process_modules: dict[str, str] = {}  # local name -> module in PROCESS_STARTS
        self.process_names: dict[str, str] = {}  # local name -> "module.function"
        self.script_names: dict[str, str] = {}  # local name -> the script it runs in-process
        for statement in self.tree.body:
            self._index(statement)
        # Imports anywhere -- a function-local import included -- resolve module-wide:
        # a name collision can only add a signal, which errs upward.
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                self._index_import(node)
        self.fixtures = {name for name, fn in self.functions.items() if _is_fixture(fn)}
        self.autouse = sorted(name for name, fn in self.functions.items() if _is_autouse(fn))
        self.tree_constants: set[str] = set()

    def bind_tree_constants(self) -> None:
        """Module constants bound to the tree, through other constants, to a fixed point."""
        changed = True
        while changed:
            changed = False
            for name, value in self.constants.items():
                if name not in self.tree_constants and self.reads_tree(value, set()):
                    self.tree_constants.add(name)
                    changed = True

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

    def _script(self, module: str) -> str | None:
        """The ``tools/`` script ``module`` names, if it is one of this repository's."""
        head, _, rest = module.partition(".")
        name = rest if head == SCRIPT_DIRECTORY else module
        if head != SCRIPT_DIRECTORY and "." in module:
            return None
        if not name:
            return f"{SCRIPT_DIRECTORY}/"
        script = self.program.repo_root / SCRIPT_DIRECTORY / f"{name}.py"
        return f"{SCRIPT_DIRECTORY}/{name}.py" if script.is_file() else None

    def _index_import(self, statement: ast.Import | ast.ImportFrom) -> None:
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                script = self._script(alias.name)
                if script is not None:
                    self.script_names[(alias.asname or alias.name).split(".")[0]] = script
                if alias.name in PROCESS_STARTS:
                    self.process_modules[alias.asname or alias.name] = alias.name
                elif alias.name.startswith(f"{SUPPORT_PACKAGE}.") and alias.asname:
                    self.support_aliases[alias.asname] = alias.name.split(".", 1)[1]
        elif statement.module and not statement.level:
            module = statement.module
            script = self._script(module)
            for alias in statement.names:
                local = alias.asname or alias.name
                if script is not None:
                    self.script_names[local] = (
                        self._script(f"{module}.{alias.name}") or script
                        if module == SCRIPT_DIRECTORY
                        else script
                    )
                elif module in PROCESS_STARTS and alias.name in PROCESS_STARTS[module]:
                    self.process_names[local] = f"{module}.{alias.name}"
                elif module == SUPPORT_PACKAGE:
                    self.support_aliases[local] = alias.name
                elif module.startswith(f"{SUPPORT_PACKAGE}."):
                    self.imported[local] = (module.split(".", 1)[1], alias.name)

    def is_tree_name(self, name: str, local: set[str]) -> bool:
        if name == "__file__" or name in local or name in self.tree_constants:
            return True
        if name in self.imported:
            stem, original = self.imported[name]
            support = self.program.support(stem)
            return support is not None and support.is_tree_name(original, set())
        return False

    def _tree_use(self, node: ast.AST, local: set[str]) -> str | None:
        """What ``node`` reads of the tree, when it is a use outside labelled input."""
        hit: str | None = None
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and self.is_tree_name(node.id, local)
        ):
            hit = node.id
        elif (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id in self.script_names
        ):
            return f"{node.id} (runs {self.script_names[node.id]} in-process)"
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
            if node.attr == "__file__":
                hit = ast.unparse(node)
            elif isinstance(node.value, ast.Name) and node.value.id in self.support_aliases:
                support = self.program.support(self.support_aliases[node.value.id])
                if support is not None and support.is_tree_name(node.attr, set()):
                    hit = ast.unparse(node)
        if hit is None or _labelled(_chain_root(node, self.parents)):
            return None
        return hit

    def reads_tree(self, expression: ast.AST, local: set[str]) -> bool:
        return any(self._tree_use(sub, local) for sub in ast.walk(expression))

    def spawn_use(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            module = self.process_modules.get(node.value.id)
            if module is not None and node.attr in PROCESS_STARTS[module]:
                return f"{module}.{node.attr}"
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            return self.process_names.get(node.id)
        return None

    def resolve(self, name: str) -> Node | None:
        """The definition ``name`` refers to here, following support re-exports."""
        if name in self.functions or name in self.classes or name in self.constants:
            return (self.path, name)
        if name in self.imported:
            stem, original = self.imported[name]
            support = self.program.support(stem)
            return support.resolve(original) if support is not None else None
        return None

    def resolve_fixture(self, name: str) -> Node | None:
        if name in self.fixtures:
            return (self.path, name)
        target = self.resolve(name) if name in self.imported else None
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
            module.bind_tree_constants()
        return self._modules[path]

    def support(self, stem: str) -> _Module | None:
        """The module ``tests.<stem>`` names: a support module, or a test module
        another test imports from."""
        for directory in (self.root, self.support_root):
            if directory is not None and (directory / f"{stem}.py").is_file():
                return self.module(directory / f"{stem}.py")
        return None

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
            if id(sub) in module.skip:
                continue
            target: Node | None = None
            label = ""
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load) and sub.id != own:
                target, label = module.resolve(sub.id), sub.id
            elif (
                isinstance(sub, ast.Attribute)
                and isinstance(sub.value, ast.Name)
                and sub.value.id in module.support_aliases
            ):
                support = self.support(module.support_aliases[sub.value.id])
                target = support.resolve(sub.attr) if support is not None else None
                label = ast.unparse(sub)
            if target is not None:
                edges.append((label, target))
        return edges

    def _expression_facts(self, module: _Module, value: ast.expr, own: str) -> _Facts:
        nodes = list(ast.walk(value))
        spawns = tuple(s for s in (module.spawn_use(sub) for sub in nodes) if s)
        return _Facts(spawns, (), tuple(self._references(module, nodes, own)))

    def _class_facts(self, module: _Module, cls: ast.ClassDef) -> _Facts:
        nodes: list[ast.AST] = list(cls.bases) + list(cls.decorator_list)
        methods: list[tuple[str, Node]] = []
        for statement in cls.body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append((f"{cls.name}.{statement.name}", (module.path, f"{cls.name}.{statement.name}")))
            else:
                nodes.extend(ast.walk(statement))
        spawns = tuple(s for s in (module.spawn_use(sub) for sub in nodes) if s)
        reads = tuple(r for r in (module._tree_use(sub, set()) for sub in nodes) if r)
        return _Facts(spawns, reads, tuple(self._references(module, nodes, cls.name)) + tuple(methods))

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
        # Locals bound to a tree path, to a fixed point: their bindings defer to their uses.
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
                if value is not None and names and module.reads_tree(value, local):
                    local.update(names)
                    deferred.add(id(sub))
                    deferred.update(id(x) for x in ast.walk(value))
                    changed = True
        spawns: list[str] = []
        reads: list[str] = []
        used: set[str] = set()
        for sub in nodes:
            if id(sub) in module.skip:
                continue
            spawn = module.spawn_use(sub)
            if spawn:
                spawns.append(spawn)  # a process start counts wherever it is named
            if id(sub) in deferred:
                continue
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load) and sub.id in local:
                used.add(sub.id)
            read = module._tree_use(sub, local)
            if read:
                reads.append(read)
        reads.extend(f"{name} (bound to the tree, never used)" for name in sorted(local - used))
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


def module_marks(path: Path) -> tuple[dict[str, list[str]], list[str]]:
    """Per test, every tier it carries -- module ``pytestmark`` plus decorators,
    both levels counted -- and the module's tier aliases."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    module_tiers: list[str] = []
    aliases: list[str] = []
    for statement in tree.body:
        value = _assigned_value(statement)
        if value is None:
            continue
        for name in _assigned_names(statement):
            if name == PYTESTMARK:
                marks = value.elts if isinstance(value, (ast.List, ast.Tuple)) else [value]
                module_tiers += [t for t in map(tier_of_mark, marks) if t]
            elif tier_of_mark(value):
                aliases.append(f"{name} = {ast.unparse(value)}")
    tiers = {
        statement.name: module_tiers
        + [t for t in map(tier_of_mark, statement.decorator_list) if t]
        for statement in tree.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
        and statement.name.startswith("test_")
    }
    return tiers, aliases


def tier_count_violations(root: Path) -> list[str]:
    """Every test without exactly one tier, and every tier alias, named."""
    found: list[str] = []
    for path in sorted(root.glob(TEST_MODULE_GLOB)):
        tiers, aliases = module_marks(path)
        found += [f"{path.name}: a tier through an alias: {alias}" for alias in aliases]
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
