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
