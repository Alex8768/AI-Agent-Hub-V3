from __future__ import annotations


def pack_context(
    chunks: list[str],
    *,
    max_chars: int,
) -> tuple[str, list[str]]:
    """Deterministic context packer (MVP).

    Rules:
      - preserve input order
      - deduplicate exact duplicate chunk strings
      - join with \n\n
      - stop before exceeding max_chars (hard cap)
      - return (context_text, used_chunks)
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be > 0")

    seen: set[str] = set()
    used: list[str] = []
    parts: list[str] = []
    total = 0

    for c in chunks:
        if not c:
            continue
        if c in seen:
            continue
        seen.add(c)

        sep = "\n\n" if parts else ""
        add_len = len(sep) + len(c)
        if total + add_len > max_chars:
            break

        if sep:
            parts.append(sep)
            total += len(sep)

        parts.append(c)
        total += len(c)
        used.append(c)

    return "".join(parts), used
