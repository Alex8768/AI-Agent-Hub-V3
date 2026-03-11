from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.services.answer.answer_service import AnswerService
from src.services.answer.interface_contract import build_answer_service_request_contract


ROOT = Path(__file__).resolve().parents[4]


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


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


def _assert_no_forbidden_imports(path: Path, forbidden_prefixes: list[str], gate_name: str) -> None:
    modules = _read_import_modules(path)
    violations = [
        mod
        for mod in modules
        if any(mod == prefix or mod.startswith(f"{prefix}.") for prefix in forbidden_prefixes)
    ]
    assert not violations, f"{gate_name} violations detected:\n" + "\n".join(sorted(violations))


def _count_imports_with_prefix(path: Path, prefix: str) -> int:
    modules = _read_import_modules(path)
    return sum(
        1
        for mod in modules
        if mod == prefix or mod.startswith(f"{prefix}.")
    )


def _read_function_calls(path: Path, function_name: str) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    target: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "AnswerService":
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == function_name:
                    target = child
                    break
    if target is None:
        return []
    calls: list[str] = []
    for node in ast.walk(target):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            calls.append(str(node.func.id or ""))
        elif isinstance(node.func, ast.Attribute):
            calls.append(str(node.func.attr or ""))
    return calls


def _has_silent_except_pass(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if len(node.body) != 1:
            continue
        only_stmt = node.body[0]
        if isinstance(only_stmt, ast.Pass):
            return True
    return False


def _read_exception_policy_violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if not isinstance(node.type, ast.Name) or str(node.type.id or "") != "Exception":
            continue
        has_exception_binding = bool(getattr(node, "name", None))
        has_warning_call = False
        has_reason_code_literal = False
        for subnode in ast.walk(node):
            if isinstance(subnode, ast.Call) and isinstance(subnode.func, ast.Attribute) and subnode.func.attr == "warning":
                has_warning_call = True
            if isinstance(subnode, ast.Constant) and isinstance(subnode.value, str) and subnode.value == "reason_code":
                has_reason_code_literal = True
        missing: list[str] = []
        if not has_exception_binding:
            missing.append("missing_exception_binding")
        if not has_warning_call:
            missing.append("missing_warning_call")
        if not has_reason_code_literal:
            missing.append("missing_reason_code_context")
        if missing:
            violations.append(
                f"{path.relative_to(ROOT)}:{int(getattr(node, 'lineno', 0))}:"
                + ",".join(sorted(missing))
            )
    return violations


def test_answer_endpoint_dependency_gate_forbidden_internal_imports():
    endpoint_path = ROOT / "src/api/endpoints/answer.py"
    _assert_no_forbidden_imports(
        endpoint_path,
        forbidden_prefixes=[
            "src.services.answer.orchestrator",
            "src.services.answer.response_assembly",
        ],
        gate_name="answer_endpoint_forbidden_internal_service_imports",
    )


def test_answer_orchestration_dependency_gate_layering_rules():
    orchestrator_path = ROOT / "src/services/answer/orchestrator.py"
    _assert_no_forbidden_imports(
        orchestrator_path,
        forbidden_prefixes=[
            "src.api",
            "src.services.answer.response_assembly",
        ],
        gate_name="answer_orchestrator_forbidden_imports",
    )

    response_assembly_path = ROOT / "src/services/answer/response_assembly.py"
    _assert_no_forbidden_imports(
        response_assembly_path,
        forbidden_prefixes=[
            "src.api",
            "src.core.providers",
            "src.layers.pro.rag",
            "src.services.answer.orchestrator",
        ],
        gate_name="answer_response_assembly_forbidden_imports",
    )


def test_answer_service_facade_gate_requires_seam_imports():
    answer_service_path = ROOT / "src/services/answer/answer_service.py"
    modules = _read_import_modules(answer_service_path)
    required = {
        "src.services.answer.interface_contract",
        "src.services.answer.orchestrator",
        "src.services.answer.post_orchestration",
        "src.services.answer.diagnostics_merge",
        "src.services.answer.response_assembly",
    }
    missing = sorted(mod for mod in required if mod not in modules)
    assert not missing, "answer_service_missing_required_seams:\n" + "\n".join(missing)


def test_answer_service_facade_gate_requires_extracted_runtime_wiring_seam_import():
    answer_service_path = ROOT / "src/services/answer/answer_service.py"
    modules = _read_import_modules(answer_service_path)
    required = {
        "src.services.answer.diagnostics.runtime_wiring",
    }
    missing = sorted(mod for mod in required if mod not in modules)
    assert not missing, "answer_service_missing_runtime_wiring_seam:\n" + "\n".join(missing)


def test_reasoning_engine_facade_gate_requires_extracted_runtime_productization_seam_import():
    reasoning_engine_path = ROOT / "src/layers/pro/reasoning/engine.py"
    modules = _read_import_modules(reasoning_engine_path)
    required = {
        "src.layers.pro.reasoning.evaluation.runtime_productization",
    }
    missing = sorted(mod for mod in required if mod not in modules)
    assert not missing, "reasoning_engine_missing_runtime_productization_seam:\n" + "\n".join(missing)


def test_reasoning_engine_facade_gate_requires_runtime_diagnostics_seam_import():
    reasoning_engine_path = ROOT / "src/layers/pro/reasoning/engine.py"
    modules = _read_import_modules(reasoning_engine_path)
    required = {
        "src.layers.pro.reasoning.evaluation.runtime_diagnostics",
    }
    missing = sorted(mod for mod in required if mod not in modules)
    assert not missing, "reasoning_engine_missing_runtime_diagnostics_seam:\n" + "\n".join(missing)


def test_answer_service_facade_gate_requires_extracted_llm_planner_policy_seam_import():
    answer_service_path = ROOT / "src/services/answer/answer_service.py"
    modules = _read_import_modules(answer_service_path)
    required = {
        "src.services.answer.reasoning.llm_planner_policy",
    }
    missing = sorted(mod for mod in required if mod not in modules)
    assert not missing, "answer_service_missing_llm_planner_policy_seam:\n" + "\n".join(missing)


def test_reasoning_engine_facade_gate_requires_extracted_multi_agent_runtime_seam_import():
    reasoning_engine_path = ROOT / "src/layers/pro/reasoning/engine.py"
    modules = _read_import_modules(reasoning_engine_path)
    required = {
        "src.layers.pro.reasoning.multi_agent.runtime_contracts",
    }
    missing = sorted(mod for mod in required if mod not in modules)
    assert not missing, "reasoning_engine_missing_multi_agent_runtime_seam:\n" + "\n".join(missing)


def test_reasoning_engine_facade_gate_requires_runtime_diagnostics_contracts_seam_import():
    reasoning_engine_path = ROOT / "src/layers/pro/reasoning/engine.py"
    modules = _read_import_modules(reasoning_engine_path)
    required = {
        "src.layers.pro.reasoning.diagnostics.runtime_contracts",
    }
    missing = sorted(mod for mod in required if mod not in modules)
    assert not missing, "reasoning_engine_missing_runtime_diagnostics_contracts_seam:\n" + "\n".join(missing)


def test_reasoning_engine_facade_gate_requires_loop_guard_control_seam_import():
    reasoning_engine_path = ROOT / "src/layers/pro/reasoning/engine.py"
    modules = _read_import_modules(reasoning_engine_path)
    required = {
        "src.layers.pro.reasoning.control.loop_guard",
    }
    missing = sorted(mod for mod in required if mod not in modules)
    assert not missing, "reasoning_engine_missing_loop_guard_control_seam:\n" + "\n".join(missing)


def test_facade_import_budget_no_growth_gate_answer_and_reasoning():
    answer_service_path = ROOT / "src/services/answer/answer_service.py"
    reasoning_engine_path = ROOT / "src/layers/pro/reasoning/engine.py"

    answer_local_import_budget = 15
    reasoning_local_import_budget = 17

    answer_local_imports = _count_imports_with_prefix(answer_service_path, "src.services.answer")
    reasoning_local_imports = _count_imports_with_prefix(reasoning_engine_path, "src.layers.pro.reasoning")

    assert answer_local_imports <= answer_local_import_budget, (
        "decomposition_import_budget_gate_answer_service_exceeded:"
        f" {answer_local_imports} > {answer_local_import_budget}"
    )
    assert reasoning_local_imports <= reasoning_local_import_budget, (
        "decomposition_import_budget_gate_reasoning_engine_exceeded:"
        f" {reasoning_local_imports} > {reasoning_local_import_budget}"
    )


def test_answer_service_facade_gate_handle_contract_pipeline_calls():
    answer_service_path = ROOT / "src/services/answer/answer_service.py"
    calls = _read_function_calls(answer_service_path, "handle_contract")
    required = {
        "_run_answer_primary_pipeline",
        "run_answer_post_orchestration_flow",
        "_build_post_orchestration_deps",
        "run_answer_diagnostics_merge_flow",
        "_build_diagnostics_merge_deps",
    }
    missing = sorted(call for call in required if call not in calls)
    assert not missing, "answer_service_handle_contract_missing_pipeline_calls:\n" + "\n".join(missing)


def test_answer_soft_failure_gate_no_silent_except_pass_in_a253_scoped_runtime_modules():
    answer_paths = [
        ROOT / "src/services/answer/answer_service.py",
        ROOT / "src/services/answer/orchestrator.py",
        ROOT / "src/services/answer/response_assembly.py",
        ROOT / "src/services/answer/post_orchestration.py",
        ROOT / "src/services/answer/diagnostics_merge.py",
    ]
    violations = [str(path.relative_to(ROOT)) for path in answer_paths if _has_silent_except_pass(path)]
    assert not violations, "answer_soft_failure_gate_detected_silent_except_pass:\n" + "\n".join(sorted(violations))


def test_answer_exception_policy_gate_scoped_handlers_require_warning_and_reason_code_context():
    scoped_paths = [
        ROOT / "src/services/answer/orchestrator.py",
        ROOT / "src/services/answer/response_assembly.py",
        ROOT / "src/services/answer/post_orchestration.py",
        ROOT / "src/services/answer/diagnostics_merge.py",
    ]
    violations: list[str] = []
    for path in scoped_paths:
        violations.extend(_read_exception_policy_violations(path))
    assert not violations, (
        "answer_exception_policy_gate_scoped_handler_contract_violations:\n" + "\n".join(sorted(violations))
    )


def test_decomposition_no_growth_gate_answer_and_reasoning_monolith_line_budgets():
    # A2.67 patch 4: no-growth guardrail budgets recalibrated to latest reduced baselines.
    answer_service_path = ROOT / "src/services/answer/answer_service.py"
    reasoning_engine_path = ROOT / "src/layers/pro/reasoning/engine.py"

    answer_service_max_lines = 2832
    reasoning_engine_max_lines = 481

    answer_service_lines = _line_count(answer_service_path)
    reasoning_engine_lines = _line_count(reasoning_engine_path)

    assert answer_service_lines <= answer_service_max_lines, (
        "decomposition_no_growth_gate_answer_service_line_budget_exceeded:"
        f" {answer_service_lines} > {answer_service_max_lines}"
    )
    assert reasoning_engine_lines <= reasoning_engine_max_lines, (
        "decomposition_no_growth_gate_reasoning_engine_line_budget_exceeded:"
        f" {reasoning_engine_lines} > {reasoning_engine_max_lines}"
    )


class _DummyState:
    def __init__(self, request_id: str):
        self.request_id = request_id


class _DummyAppState:
    def __init__(self, rag_engine: object, hybrid_retriever: object):
        self.rag_engine = rag_engine
        self.hybrid_retriever = hybrid_retriever


class _DummyApp:
    def __init__(self, state: _DummyAppState):
        self.state = state


class _DummyHTTP:
    def __init__(self, *, request_id: str, rag_engine: object, hybrid_retriever: object):
        self.state = _DummyState(request_id)
        self.headers = {}
        self.app = _DummyApp(_DummyAppState(rag_engine, hybrid_retriever))


class _FakeHybrid:
    async def retrieve(self, **kwargs):
        return {"graph": {"nodes": [], "edges": []}, "results": [], "evidence": [], "stats": {}}


class _FakeResp:
    def __init__(self):
        self.answer = "ok"
        self.diagnostics = {}
        self.timings = {}
        self.provenance = []
        self.used_chunks = []
        self.used_nodes = []
        self.used_edges = []


class _FakeReasoningEngine:
    async def synthesize(self, req):
        return _FakeResp()


@pytest.mark.asyncio
async def test_answer_service_interface_contract_path_preserves_runtime_parity(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_assistant_mode = False
        feature_assistant_proactive = False
        feature_assistant_actions = False
        feature_reasoning_llm_enabled = False
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.core.providers.get_reasoning_engine", lambda **kwargs: _FakeReasoningEngine())
    monkeypatch.setattr("src.core.providers.get_memory_store", lambda: None)
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-a2-51", raising=False)

    http = _DummyHTTP(request_id="rid-a2-51", rag_engine=object(), hybrid_retriever=_FakeHybrid())

    legacy_req = AnswerRequest(query="parity check", session_id="legacy", filters={})
    contract_req = AnswerRequest(query="parity check", session_id="contract", filters={})

    service = AnswerService()
    legacy_resp = await service.handle(http, legacy_req, workspace_id="default")
    contract = build_answer_service_request_contract(
        http=http,
        req=contract_req,
        workspace_id="default",
        engine=http.app.state.rag_engine,
        retriever=http.app.state.hybrid_retriever,
    )
    contract_resp = await service.handle_contract(contract)

    assert str(getattr(legacy_resp, "answer", "")) == str(getattr(contract_resp, "answer", ""))
    legacy_diag = dict(getattr(legacy_resp, "diagnostics", None) or {})
    contract_diag = dict(getattr(contract_resp, "diagnostics", None) or {})
    assert set(legacy_diag.keys()) == set(contract_diag.keys())
    assert legacy_diag.get("response_mode") == contract_diag.get("response_mode")
    assert legacy_diag.get("planner_runtime_parity") == contract_diag.get("planner_runtime_parity")
    assert legacy_diag.get("conversational_runtime_parity") == contract_diag.get("conversational_runtime_parity")
