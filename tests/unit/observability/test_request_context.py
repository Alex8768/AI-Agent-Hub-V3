from types import SimpleNamespace

from src.observability.request_context import get_request_id, get_workspace_id, set_workspace_id


class _DummyRequest:
    def __init__(self, *, request_id=None, workspace_id=None, headers=None):
        self.state = SimpleNamespace()
        if request_id is not None:
            self.state.request_id = request_id
        if workspace_id is not None:
            self.state.workspace_id = workspace_id
        self.headers = dict(headers or {})


def test_get_request_id_prefers_state():
    req = _DummyRequest(request_id="rid-state", headers={"X-Request-ID": "rid-header"})
    assert get_request_id(req) == "rid-state"


def test_get_workspace_id_header_fallback_and_default():
    req_header = _DummyRequest(headers={"X-Workspace-Id": "ws-header"})
    req_default = _DummyRequest()
    assert get_workspace_id(req_header) == "ws-header"
    assert get_workspace_id(req_default) == "default"


def test_set_workspace_id_writes_request_state():
    req = _DummyRequest()
    set_workspace_id(req, "ws-123")
    assert req.state.workspace_id == "ws-123"
