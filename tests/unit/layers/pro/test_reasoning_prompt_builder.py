from __future__ import annotations

from src.layers.pro.reasoning.contracts import AnswerRequest, ProvenanceItem
from src.layers.pro.reasoning.prompt_builder import build_reasoning_prompt


def test_prompt_builder_includes_question_and_context():
    req = AnswerRequest(query="What is X?")
    prompt = build_reasoning_prompt(req, context_preview="CTX")
    assert "Question: What is X?" in prompt
    assert "Context:" in prompt
    assert "\nCTX\n" in prompt
    assert prompt.strip().endswith("Answer:")


def test_prompt_builder_includes_provenance_when_present():
    req = AnswerRequest(query="Q")
    prov = [ProvenanceItem(type="chunk", id="c1", source_refs=["doc:A#1", "doc:A#2"])]
    prompt = build_reasoning_prompt(req, context_preview="CTX", provenance=prov)
    assert "Provenance:" in prompt
    assert "- chunk:c1 -> doc:A#1, doc:A#2" in prompt


def test_prompt_builder_enforces_reply_language_to_match_question():
    req = AnswerRequest(query="Привет, что это?")
    prompt = build_reasoning_prompt(req, context_preview="CTX")
    assert "Always respond in the same language as the user's question." in prompt
    assert "If the context is insufficient, say you don't know in the same language as the user's question." in prompt


def test_prompt_builder_normalizes_query_input_consistently():
    req_prompt = build_reasoning_prompt(AnswerRequest(query="  What is X?  "), context_preview="CTX")
    str_prompt = build_reasoning_prompt("What is X?", context_preview="CTX")
    assert req_prompt == str_prompt
