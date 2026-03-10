from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def _iter_python_files(relative_dir: str):
    base = ROOT / relative_dir
    if not base.exists():
        return []
    return sorted(path for path in base.rglob("*.py") if path.is_file())


def _read_import_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(str(alias.name or ""))
        elif isinstance(node, ast.ImportFrom):
            module = str(node.module or "")
            if module:
                modules.append(module)
    return modules


def _assert_no_forbidden_imports(*, files: list[Path], forbidden_prefixes: list[str], gate_name: str) -> None:
    violations: list[str] = []
    for path in files:
        rel = path.relative_to(ROOT)
        modules = _read_import_modules(path)
        for mod in modules:
            if any(mod == prefix or mod.startswith(f"{prefix}.") for prefix in forbidden_prefixes):
                violations.append(f"{rel}: {mod}")
    assert not violations, f"{gate_name} violations detected:\n" + "\n".join(sorted(violations))


def test_topology_dependency_gate_kernel_forbidden_directions():
    files = _iter_python_files("src/layers/pro/reasoning/kernel")
    _assert_no_forbidden_imports(
        files=list(files),
        forbidden_prefixes=[
            "src.layers.pro.reasoning.execution_plane",
            "src.api",
            "src.services",
        ],
        gate_name="kernel_forbidden_dependencies",
    )


def test_topology_dependency_gate_governance_forbidden_interface_dependency():
    files = _iter_python_files("src/layers/pro/reasoning/governance")
    _assert_no_forbidden_imports(
        files=list(files),
        forbidden_prefixes=[
            "src.api",
        ],
        gate_name="governance_forbidden_interface_dependencies",
    )


def test_topology_dependency_gate_extensions_forbidden_execution_side_effects():
    extension_dirs = [
        "src/layers/pro/meta_cognition",
        "src/layers/pro/anticipatory",
    ]
    files: list[Path] = []
    for rel in extension_dirs:
        files.extend(list(_iter_python_files(rel)))
    _assert_no_forbidden_imports(
        files=files,
        forbidden_prefixes=[
            "src.layers.pro.reasoning.execution_plane",
            "src.services",
        ],
        gate_name="extensions_forbidden_execution_dependencies",
    )


def test_topology_dependency_gate_planner_forbidden_composition_assembly_imports():
    planner_file = ROOT / "src/layers/pro/reasoning/planner/planner.py"
    modules = _read_import_modules(planner_file)
    forbidden_prefixes = [
        "src.layers.pro.composition.registry",
        "src.layers.pro.composition.composer",
    ]
    violations = [
        mod
        for mod in modules
        if any(mod == prefix or mod.startswith(f"{prefix}.") for prefix in forbidden_prefixes)
    ]
    assert not violations, (
        "planner_forbidden_composition_assembly_imports violations detected:\n"
        + "\n".join(sorted(violations))
    )
