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
