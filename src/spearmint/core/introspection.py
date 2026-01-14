"""Static analysis utilities for experiment introspection.

This module provides tools for analyzing Python source code to discover
experiment-decorated functions, their configurations, and call relationships.
This enables precomputation of all execution paths before runtime.
"""

from __future__ import annotations

import ast
import hashlib
import importlib
import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

from .config import parse_configs
from .utils.handlers import yaml_handler


@dataclass(frozen=True)
class ExperimentFunction:
    """Metadata about an experiment-decorated function discovered via AST."""

    key: str  # Unique identifier: "path/to/file.py:function_name"
    name: str  # Function name
    file_path: Path  # Source file
    lineno: int  # Line number of function definition
    is_async: bool  # Whether the function is async
    branch_strategy: str | None  # Strategy class name if specified
    config_count: int | None  # Number of configs if determinable
    config_ids: list[str] = field(default_factory=list)  # Config IDs if available


@dataclass
class ExperimentPath:
    """A single execution path through the experiment graph.

    Represents a unique combination of config selections across
    all experiment functions in a call chain.
    """

    path_id: str  # Unique identifier for this path
    config_assignments: dict[str, str]  # func_key -> config_id
    function_order: list[str]  # Order of function execution


@dataclass
class ExperimentPlan:
    """Complete execution plan for an experiment.

    Contains all discovered experiment functions, their relationships,
    and enumerated execution paths with pre-assigned config IDs.
    """

    functions: dict[str, ExperimentFunction]  # key -> ExperimentFunction
    call_graph: dict[str, set[str]]  # caller_key -> set of callee_keys
    paths: list[ExperimentPath]  # All execution paths to run
    root_key: str | None = None  # Entry point function key


class ExperimentIntrospector:
    """Analyzes source files to discover experiment structure."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()
        self._parsed_files: dict[Path, tuple[str, ast.AST]] = {}
        self._import_aliases: dict[Path, dict[str, str]] = {}
        self._instance_info: dict[Path, dict[str, dict[str, Any]]] = {}

    def parse_file(self, path: Path) -> tuple[str, ast.AST]:
        """Parse a Python file and cache the result."""
        path = path.resolve()
        if path not in self._parsed_files:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
            self._parsed_files[path] = (source, tree)
        return self._parsed_files[path]

    def discover_experiments(
        self, entry_file: Path, follow_imports: bool = True
    ) -> tuple[dict[str, ExperimentFunction], dict[str, set[str]]]:
        """Discover all experiment functions reachable from entry file.

        Args:
            entry_file: The Python file to start analysis from.
            follow_imports: If True, follow local imports to find more experiments.

        Returns:
            Tuple of (functions dict, call_graph dict)
        """
        files = self._collect_files(entry_file) if follow_imports else [entry_file]

        # First pass: collect import aliases and Spearmint instance info
        for file_path in files:
            source, tree = self.parse_file(file_path)
            self._import_aliases[file_path] = self._build_import_alias_map(tree, file_path)
            self._instance_info[file_path] = self._extract_spearmint_instances(
                tree, source, file_path
            )

        # Second pass: find experiment functions and build call graph
        functions: dict[str, ExperimentFunction] = {}
        func_metadata: dict[str, bool] = {}  # key -> is_experiment
        call_map: dict[str, list[str]] = {}  # key -> list of callee names

        for file_path in files:
            source, tree = self.parse_file(file_path)
            rel_path = self._relative_label(file_path)
            imports = self._import_aliases.get(file_path, {})

            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    key = f"{rel_path}:{node.name}"
                    is_experiment = self._is_experiment_decorated(node)
                    func_metadata[key] = is_experiment
                    call_map[key] = self._collect_callee_names(node)

                    if is_experiment:
                        exp_func = self._extract_experiment_function(
                            node, file_path, source, imports
                        )
                        functions[exp_func.key] = exp_func

        # Build call graph (experiment -> experiment edges)
        call_graph = self._build_call_graph(functions, func_metadata, call_map)

        return functions, call_graph

    def build_plan(
        self,
        entry_file: Path,
        entry_func: str | None = None,
        follow_imports: bool = True,
    ) -> ExperimentPlan:
        """Build an execution plan for experiments starting from entry point.

        Args:
            entry_file: File containing the entry point function.
            entry_func: Name of entry function (uses first found if None).
            follow_imports: Whether to follow imports for experiment discovery.

        Returns:
            ExperimentPlan with all paths enumerated.
        """
        functions, call_graph = self.discover_experiments(entry_file, follow_imports)

        # Determine root function
        root_key = None
        if entry_func:
            rel_path = self._relative_label(entry_file.resolve())
            root_key = f"{rel_path}:{entry_func}"
        else:
            # Find roots (functions not called by other experiments)
            called = set()
            for callees in call_graph.values():
                called.update(callees)
            roots = [k for k in functions if k not in called]
            root_key = roots[0] if roots else (list(functions.keys())[0] if functions else None)

        # Enumerate all execution paths
        paths = self._enumerate_paths(functions, call_graph, root_key)

        return ExperimentPlan(
            functions=functions,
            call_graph=call_graph,
            paths=paths,
            root_key=root_key,
        )

    def _collect_files(self, entry: Path) -> list[Path]:
        """Collect entry file and imported Python files (best effort)."""
        entry = entry.resolve()
        visited: set[Path] = set()
        ordered: list[Path] = []
        stack = [entry]

        while stack:
            path = stack.pop().resolve()
            if path in visited or not path.exists() or path.suffix != ".py":
                continue
            visited.add(path)
            ordered.append(path)

            _, tree = self.parse_file(path)
            base_dir = path.parent

            for module in self._iter_import_modules(tree):
                resolved = self._resolve_module_path(module, base_dir)
                if resolved and resolved not in visited:
                    stack.append(resolved)

        return ordered

    def _iter_import_modules(self, tree: ast.AST) -> Iterable[str]:
        """Yield module names from import statements."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    yield alias.name
            elif isinstance(node, ast.ImportFrom) and node.module:
                yield node.module
                for alias in node.names:
                    if alias.name != "*":
                        yield f"{node.module}.{alias.name}"

    def _resolve_module_path(self, module: str, base_dir: Path) -> Path | None:
        """Attempt to resolve a module name to a file path."""
        parts = module.split(".")
        if not parts:
            return None

        candidates = [
            base_dir.joinpath(*parts).with_suffix(".py"),
            base_dir.joinpath(*parts, "__init__.py"),
            self.repo_root.joinpath(*parts).with_suffix(".py"),
            self.repo_root.joinpath(*parts, "__init__.py"),
        ]

        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _relative_label(self, path: Path) -> str:
        """Get a relative path label for display."""
        try:
            return str(path.resolve().relative_to(self.repo_root.resolve()))
        except ValueError:
            return str(path)

    def _build_import_alias_map(self, tree: ast.AST, file_path: Path) -> dict[str, str]:
        """Build a map of import aliases to module names."""
        rel_path = self._relative_label(file_path)
        parts = rel_path.split("/")
        package = ".".join(parts[:-1]) if len(parts) > 1 else ""

        aliases: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod and "." not in mod and package:
                    mod = f"{package}.{mod}"
                for alias in node.names:
                    aliases[alias.asname or alias.name] = mod or alias.name
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name
                    if mod and "." not in mod and package:
                        mod = f"{package}.{mod}"
                    aliases[alias.asname or alias.name] = mod
        return aliases

    def _extract_spearmint_instances(
        self, tree: ast.AST, source: str, file_path: Path
    ) -> dict[str, dict[str, Any]]:
        """Extract Spearmint instance configurations from module-level assignments."""
        info: dict[str, dict[str, Any]] = {}
        imports = self._import_aliases.get(file_path, {})

        for node in ast.iter_child_nodes(tree):
            if not isinstance(node, ast.Assign):
                continue
            if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                continue
            name = node.targets[0].id
            if not isinstance(node.value, ast.Call):
                continue

            func = node.value.func
            is_spearmint = (
                (isinstance(func, ast.Name) and func.id == "Spearmint")
                or (isinstance(func, ast.Attribute) and func.attr == "Spearmint")
            )
            if not is_spearmint:
                continue

            bs = self._extract_branch_strategy(node.value, source)
            cfg_count = None
            config_ids: list[str] = []

            configs_kw = next(
                (kw for kw in node.value.keywords if kw.arg == "configs"), None
            )
            if configs_kw:
                parsed = self._parse_configs_node(
                    configs_kw.value, file_path.parent, imports
                )
                if parsed is not None:
                    try:
                        configs = parse_configs(parsed, yaml_handler)
                        cfg_count = len(configs)
                        config_ids = [c["config_id"] for c in configs]
                    except Exception:
                        pass

            info[name] = {
                "branch_strategy": bs,
                "config_count": cfg_count,
                "config_ids": config_ids,
            }

        return info

    def _is_experiment_decorated(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Check if a function has an @experiment or @configure decorator."""
        for decorator in node.decorator_list:
            if self._is_experiment_decorator(decorator):
                return True
        return False

    def _is_experiment_decorator(self, decorator: ast.AST) -> bool:
        """Check if a decorator is @experiment or @configure."""
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target, ast.Attribute):
            return target.attr in ("experiment", "configure")
        if isinstance(target, ast.Name):
            return target.id in ("experiment", "configure")
        return False

    def _extract_experiment_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        file_path: Path,
        source: str,
        imports: dict[str, str],
    ) -> ExperimentFunction:
        """Extract ExperimentFunction metadata from a decorated function."""
        rel_path = self._relative_label(file_path)
        key = f"{rel_path}:{node.name}"

        bs, cfg_count, config_ids = self._extract_decorator_info(
            node.decorator_list, source, file_path, imports
        )

        return ExperimentFunction(
            key=key,
            name=node.name,
            file_path=file_path,
            lineno=node.lineno,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            branch_strategy=bs,
            config_count=cfg_count,
            config_ids=config_ids,
        )

    def _extract_decorator_info(
        self,
        decorators: list[ast.AST],
        source: str,
        file_path: Path,
        imports: dict[str, str],
    ) -> tuple[str | None, int | None, list[str]]:
        """Extract branch_strategy and config info from decorators."""
        instance_info = self._instance_info.get(file_path, {})

        for deco in decorators:
            if isinstance(deco, ast.Call) and self._is_experiment_decorator(deco):
                bs = self._extract_branch_strategy(deco, source)
                cfg_count = None
                config_ids: list[str] = []

                # Check for instance-level defaults
                inst_name = None
                if isinstance(deco.func, ast.Attribute) and isinstance(
                    deco.func.value, ast.Name
                ):
                    inst_name = deco.func.value.id

                if inst_name and inst_name in instance_info:
                    inst = instance_info[inst_name]
                    cfg_count = inst.get("config_count")
                    config_ids = inst.get("config_ids", [])
                    if not bs:
                        bs = inst.get("branch_strategy")

                # Check for inline configs
                configs_kw = next(
                    (kw for kw in deco.keywords if kw.arg == "configs"), None
                )
                if configs_kw:
                    parsed = self._parse_configs_node(
                        configs_kw.value, file_path.parent, imports
                    )
                    if parsed is not None:
                        try:
                            configs = parse_configs(parsed, yaml_handler)
                            cfg_count = len(configs)
                            config_ids = [c["config_id"] for c in configs]
                        except Exception:
                            pass

                return bs, cfg_count, config_ids

            elif self._is_experiment_decorator(deco):
                # Decorator without call, check for instance
                if isinstance(deco, ast.Attribute) and isinstance(deco.value, ast.Name):
                    inst_name = deco.value.id
                    if inst_name in instance_info:
                        inst = instance_info[inst_name]
                        return (
                            inst.get("branch_strategy"),
                            inst.get("config_count"),
                            inst.get("config_ids", []),
                        )

        return None, None, []

    def _extract_branch_strategy(self, call: ast.Call, source: str) -> str | None:
        """Extract branch_strategy keyword argument from a call."""
        for kw in call.keywords:
            if kw.arg == "branch_strategy":
                segment = ast.get_source_segment(source, kw.value)
                if segment:
                    return segment
                try:
                    return ast.unparse(kw.value)
                except Exception:
                    return None
        return None

    def _parse_configs_node(
        self, node: ast.AST, file_dir: Path, imports: dict[str, str]
    ) -> list[Any] | None:
        """Parse a configs argument node into a list of config sources."""
        # Try literal evaluation first
        literal = self._try_literal(node)
        if literal is not None:
            if isinstance(literal, (list, tuple)):
                return list(literal)
            return [literal]

        # String constant = path
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return [file_dir / node.value]

        # List/tuple of items
        if isinstance(node, (ast.List, ast.Tuple)):
            items: list[Any] = []
            for elt in node.elts:
                parsed = self._parse_configs_node(elt, file_dir, imports)
                if parsed is None:
                    return None
                items.extend(parsed)
            return items

        # Name reference to imported config
        if isinstance(node, ast.Name) and node.id in imports:
            mod_name = imports[node.id]
            try:
                if str(self.repo_root) not in sys.path:
                    sys.path.insert(0, str(self.repo_root))
                try:
                    mod = importlib.import_module(mod_name)
                except ModuleNotFoundError:
                    candidate = self.repo_root / (mod_name.replace(".", "/") + ".py")
                    if candidate.exists():
                        spec = importlib.util.spec_from_file_location(mod_name, candidate)
                        if spec and spec.loader:
                            mod = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(mod)
                        else:
                            return None
                    else:
                        return None
                return [getattr(mod, node.id)]
            except Exception:
                return None

        return None

    def _try_literal(self, node: ast.AST) -> Any:
        """Try to evaluate a node as a literal value."""
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            vals = []
            for elt in node.elts:
                val = self._try_literal(elt)
                if val is None and not isinstance(elt, ast.Constant):
                    return None
                vals.append(val)
            return tuple(vals) if isinstance(node, ast.Tuple) else vals
        if isinstance(node, ast.Dict):
            keys = []
            vals = []
            for k, v in zip(node.keys, node.values):
                key = self._try_literal(k)
                val = self._try_literal(v)
                if key is None or val is None:
                    return None
                keys.append(key)
                vals.append(val)
            return dict(zip(keys, vals))
        return None

    def _collect_callee_names(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> list[str]:
        """Collect names of functions called within a function body."""
        collector = _CallCollector()
        for stmt in func_node.body:
            collector.visit(stmt)
        return collector.names

    def _build_call_graph(
        self,
        functions: dict[str, ExperimentFunction],
        func_metadata: dict[str, bool],
        call_map: dict[str, list[str]],
    ) -> dict[str, set[str]]:
        """Build experiment-to-experiment call graph."""
        # Build name -> keys mapping
        by_name: dict[str, list[str]] = {}
        for key in func_metadata:
            name = key.split(":", 1)[1]
            by_name.setdefault(name, []).append(key)

        edges: dict[str, set[str]] = {k: set() for k in functions}

        for exp_key in functions:
            visited: set[str] = {exp_key}

            def dfs(func_key: str) -> None:
                for callee_name in call_map.get(func_key, []):
                    for target_key in by_name.get(callee_name, []):
                        if target_key in visited:
                            continue
                        visited.add(target_key)
                        if target_key in functions:
                            edges[exp_key].add(target_key)
                        dfs(target_key)

            dfs(exp_key)

        return edges

    def _enumerate_paths(
        self,
        functions: dict[str, ExperimentFunction],
        call_graph: dict[str, set[str]],
        root_key: str | None,
    ) -> list[ExperimentPath]:
        """Enumerate all execution paths through the experiment graph."""
        if not root_key or root_key not in functions:
            return []

        paths: list[ExperimentPath] = []
        self._enumerate_paths_recursive(
            functions, call_graph, root_key, {}, [root_key], paths
        )
        return paths

    def _enumerate_paths_recursive(
        self,
        functions: dict[str, ExperimentFunction],
        call_graph: dict[str, set[str]],
        current_key: str,
        config_assignments: dict[str, str],
        function_order: list[str],
        paths: list[ExperimentPath],
    ) -> None:
        """Recursively enumerate paths, expanding config combinations."""
        func = functions[current_key]
        config_ids = func.config_ids if func.config_ids else [f"{func.name}_default"]

        callees = call_graph.get(current_key, set())

        for config_id in config_ids:
            new_assignments = {**config_assignments, current_key: config_id}

            if not callees:
                # Leaf node - complete path
                path_id = self._generate_path_id(new_assignments)
                paths.append(
                    ExperimentPath(
                        path_id=path_id,
                        config_assignments=new_assignments,
                        function_order=list(function_order),
                    )
                )
            else:
                # Recurse into callees
                for callee_key in callees:
                    if callee_key not in function_order:
                        self._enumerate_paths_recursive(
                            functions,
                            call_graph,
                            callee_key,
                            new_assignments,
                            function_order + [callee_key],
                            paths,
                        )

    def _generate_path_id(self, config_assignments: dict[str, str]) -> str:
        """Generate a unique ID for an execution path."""
        items = sorted(config_assignments.items())
        content = ":".join(f"{k}={v}" for k, v in items)
        return hashlib.sha256(content.encode()).hexdigest()[:12]


class _CallCollector(ast.NodeVisitor):
    """Collect function call names from AST, skipping nested definitions."""

    def __init__(self) -> None:
        self.names: list[str] = []

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Name):
            self.names.append(func.id)
        elif isinstance(func, ast.Attribute):
            self.names.append(func.attr)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        pass  # Skip nested functions

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        pass  # Skip nested async functions

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        pass  # Skip nested classes


__all__ = [
    "ExperimentFunction",
    "ExperimentPath",
    "ExperimentPlan",
    "ExperimentIntrospector",
]
