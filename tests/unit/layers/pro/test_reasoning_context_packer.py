from __future__ import annotations

import pytest

from src.layers.pro.reasoning.context_packer import pack_context


def test_pack_context_preserves_order_and_dedupes():
    chunks = ["A", "B", "A", "", "C"]
    ctx, used = pack_context(chunks, max_chars=10_000)
    assert used == ["A", "B", "C"]
    assert ctx == "A\n\nB\n\nC"


def test_pack_context_hard_cap():
    chunks = ["AAAA", "BBBB", "CCCC"]
    # "AAAA" (4) + "\n\n" (2) + "BBBB"(4) => 10 fits, next would exceed
    ctx, used = pack_context(chunks, max_chars=10)
    assert used == ["AAAA", "BBBB"]
    assert ctx == "AAAA\n\nBBBB"


def test_pack_context_invalid_budget():
    with pytest.raises(ValueError):
        pack_context(["A"], max_chars=0)
