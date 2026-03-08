from __future__ import annotations

import re


_BULLET_PREFIX_RE = re.compile(r"^\s*(?:[-*]\s+|\d+[.)]\s+)")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_claim_text(text: str) -> str:
    cleaned = _BULLET_PREFIX_RE.sub("", text.strip())
    cleaned = _WHITESPACE_RE.sub(" ", cleaned).strip()
    return cleaned


def extract_claims(
    *,
    reasoning_output: str,
    max_claims: int = 8,
    min_claim_chars: int = 12,
) -> list[str]:
    """Extract deterministic claim candidates from reasoning output text.

    This boundary intentionally keeps extraction heuristic and lightweight:
    - split by lines first, then by sentence punctuation;
    - normalize whitespace and list prefixes;
    - keep insertion order and dedupe case-insensitively;
    - bound output size with ``max_claims``.
    """
    if max_claims <= 0 or min_claim_chars <= 0:
        return []

    text = str(reasoning_output or "").strip()
    if not text:
        return []

    claims: list[str] = []
    seen: set[str] = set()

    for line in text.splitlines():
        normalized_line = line.strip()
        if not normalized_line:
            continue
        for part in _SENTENCE_SPLIT_RE.split(normalized_line):
            claim = _normalize_claim_text(part)
            if len(claim) < min_claim_chars:
                continue
            if not any(ch.isalpha() for ch in claim):
                continue
            dedupe_key = claim.lower()
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            claims.append(claim)
            if len(claims) >= max_claims:
                return claims
    return claims
