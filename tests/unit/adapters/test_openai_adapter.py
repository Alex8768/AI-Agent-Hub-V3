import pytest

from src.adapters.llm.openai_adapter import OpenAIAdapter
from src.core.types import LLMConfig, Message, MessageRole


def _make_adapter(model: str = "gpt-4o-mini") -> OpenAIAdapter:
    cfg = LLMConfig(
        provider="openai",
        model=model,
        api_key="test-key",
        base_url="https://api.openai.com/v1",
        timeout=10.0,
        max_retries=1,
    )
    return OpenAIAdapter(cfg)


def test_context_length_for_modern_gpt4_model():
    adapter = _make_adapter("gpt-4o-mini")
    assert adapter.context_length == 128000


def test_responses_fallback_input_preserves_roles():
    adapter = _make_adapter("gpt-4o-mini")
    messages = [
        Message(role=MessageRole.SYSTEM, content="You are concise."),
        Message(role=MessageRole.USER, content="Summarize this text."),
        Message(role=MessageRole.ASSISTANT, content="Need source."),
        Message(role=MessageRole.TOOL, content="source: doc-1"),
    ]
    openai_messages = adapter._convert_messages(messages)

    text = adapter._build_responses_input(openai_messages)

    assert "SYSTEM: You are concise." in text
    assert "USER: Summarize this text." in text
    assert "ASSISTANT: Need source." in text
    assert "TOOL: source: doc-1" in text


def test_build_completion_from_responses_fallback_parity():
    adapter = _make_adapter("gpt-4o-mini")

    class _Usage:
        total_tokens = 77

    class _Resp:
        model = "gpt-4.1-mini"
        status = "completed"
        id = "resp_123"
        usage = _Usage()

    completion = adapter._build_completion_from_responses_fallback(
        response=_Resp(),
        request_id="req_1",
        latency=0.42,
        model="gpt-4o-mini",
        content="ok",
    )

    assert completion.content == "ok"
    assert completion.model == "gpt-4.1-mini"
    assert completion.provider == "openai"
    assert completion.tokens_used == 77
    assert completion.finish_reason == "completed"
    assert completion.metadata["id"] == "resp_123"
    assert completion.metadata["fallback_api"] == "responses"
    assert completion.metadata["fallback_reason"] == "chat_completions_404"


def test_build_completion_from_chat_parity():
    adapter = _make_adapter("gpt-4o-mini")

    class _Usage:
        total_tokens = 33
        prompt_tokens = 20
        completion_tokens = 13

    class _Message:
        content = "answer"

    class _Choice:
        message = _Message()
        finish_reason = "stop"

    class _Resp:
        model = "gpt-4o-mini"
        usage = _Usage()
        choices = [_Choice()]
        id = "chatcmpl_1"
        created = 1234567890

    completion = adapter._build_completion_from_chat(
        response=_Resp(),  # type: ignore[arg-type]
        request_id="req_2",
        latency=0.11,
    )

    assert completion.content == "answer"
    assert completion.model == "gpt-4o-mini"
    assert completion.provider == "openai"
    assert completion.tokens_used == 33
    assert completion.finish_reason == "stop"
    assert completion.metadata["id"] == "chatcmpl_1"
    assert completion.metadata["prompt_tokens"] == 20
    assert completion.metadata["completion_tokens"] == 13


def test_merge_runtime_config_overrides_values():
    adapter = _make_adapter("gpt-4o-mini")
    merged = adapter._merge_runtime_config({"temperature": 0.2, "model": "gpt-4.1"})

    assert merged["temperature"] == 0.2
    assert merged["model"] == "gpt-4.1"


def test_build_chat_completion_request_params_prunes_nones():
    adapter = _make_adapter("gpt-4o-mini")
    merged = {"model": "gpt-4o-mini", "max_tokens": None, "stop_sequences": None}
    params = adapter._build_chat_completion_request_params(merged_config=merged)

    assert params["model"] == "gpt-4o-mini"
    assert params["stream"] is False
    assert "max_tokens" not in params
    assert "stop" not in params
    assert "messages" not in params


def test_build_chat_stream_request_params_defaults_and_stream_flag():
    adapter = _make_adapter("gpt-4o-mini")
    params = adapter._build_chat_stream_request_params(merged_config={})

    assert params["model"] == "gpt-4o-mini"
    assert params["stream"] is True
    assert params["temperature"] == 0.7
    assert params["top_p"] == 1.0
    assert "messages" not in params


def test_build_stream_final_chunk_parity():
    adapter = _make_adapter("gpt-4o-mini")
    final = adapter._build_stream_final_chunk(chunk_index=3, finish_reason="stop")

    assert final.content == ""
    assert final.chunk_index == 3
    assert final.is_final is True
    assert final.finish_reason == "stop"


def test_iter_stream_output_chunks_preserves_order_and_finish_reason():
    adapter = _make_adapter("gpt-4o-mini")

    class _Delta:
        def __init__(self, content):
            self.content = content

    class _Choice:
        def __init__(self, content=None, finish_reason=None):
            self.delta = _Delta(content)
            self.finish_reason = finish_reason

    class _Chunk:
        def __init__(self, content=None, finish_reason=None):
            self.choices = [_Choice(content=content, finish_reason=finish_reason)]

    class _FakeStream:
        def __init__(self, items):
            self._items = list(items)

        def __aiter__(self):
            self._idx = 0
            return self

        async def __anext__(self):
            if self._idx >= len(self._items):
                raise StopAsyncIteration
            item = self._items[self._idx]
            self._idx += 1
            return item

    stream = _FakeStream(
        [
            _Chunk(content="Hel"),
            _Chunk(content="lo"),
            _Chunk(content=None, finish_reason="stop"),
        ]
    )

    async def _collect():
        out = []
        async for c in adapter._iter_stream_output_chunks(stream=stream):  # type: ignore[arg-type]
            out.append(c)
        return out

    import asyncio

    chunks = asyncio.run(_collect())
    assert [c.content for c in chunks] == ["Hel", "lo", ""]
    assert [c.chunk_index for c in chunks] == [0, 1, 2]
    assert [c.is_final for c in chunks] == [False, False, True]
    assert chunks[-1].finish_reason == "stop"


@pytest.mark.asyncio
async def test_complete_contract_shape_chat_path():
    adapter = _make_adapter("gpt-4o-mini")

    class _Usage:
        total_tokens = 11
        prompt_tokens = 7
        completion_tokens = 4

    class _MessageObj:
        content = "pong"

    class _Choice:
        message = _MessageObj()
        finish_reason = "stop"

    class _Resp:
        model = "gpt-4o-mini"
        usage = _Usage()
        choices = [_Choice()]
        id = "chatcmpl_contract_1"
        created = 1111111111

    class _Completions:
        async def create(self, **kwargs):
            return _Resp()

    class _Chat:
        completions = _Completions()

    class _Client:
        chat = _Chat()

    adapter._client = _Client()
    out = await adapter.complete([Message(role=MessageRole.USER, content="ping")])

    assert out.content == "pong"
    assert out.provider == "openai"
    assert out.model == "gpt-4o-mini"
    assert out.tokens_used == 11
    assert out.finish_reason == "stop"
    assert set(out.metadata.keys()) == {
        "id",
        "created",
        "latency_seconds",
        "request_id",
        "prompt_tokens",
        "completion_tokens",
    }


@pytest.mark.asyncio
async def test_complete_stream_contract_shape():
    adapter = _make_adapter("gpt-4o-mini")

    class _Delta:
        def __init__(self, content):
            self.content = content

    class _Choice:
        def __init__(self, content=None, finish_reason=None):
            self.delta = _Delta(content)
            self.finish_reason = finish_reason

    class _Chunk:
        def __init__(self, content=None, finish_reason=None):
            self.choices = [_Choice(content=content, finish_reason=finish_reason)]

    class _FakeStream:
        def __init__(self, items):
            self._items = list(items)

        def __aiter__(self):
            self._idx = 0
            return self

        async def __anext__(self):
            if self._idx >= len(self._items):
                raise StopAsyncIteration
            item = self._items[self._idx]
            self._idx += 1
            return item

    class _Completions:
        async def create(self, **kwargs):
            return _FakeStream(
                [
                    _Chunk(content="A"),
                    _Chunk(content="B"),
                    _Chunk(content=None, finish_reason="stop"),
                ]
            )

    class _Chat:
        completions = _Completions()

    class _Client:
        chat = _Chat()

    adapter._client = _Client()
    out = []
    async for chunk in adapter.complete_stream([Message(role=MessageRole.USER, content="go")]):
        out.append(chunk)

    assert [c.content for c in out] == ["A", "B", ""]
    assert [c.chunk_index for c in out] == [0, 1, 2]
    assert [c.is_final for c in out] == [False, False, True]
    assert out[-1].finish_reason == "stop"
