from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.services.answer.answer_service import AnswerService
from src.services.answer.interface_contract import build_answer_service_request_contract


ROOT = Path(__file__).resolve().parents[4]


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
