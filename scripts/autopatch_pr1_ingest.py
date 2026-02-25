
from pathlib import Path

TARGET = Path("src/services/document/ingest_service.py")

def main():
    text = TARGET.read_text(encoding="utf-8")

    if "_rollback_vectors(" in text:
        print("Already patched.")
        return

    marker = "async def _validate_text("
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError("Cannot find insertion point")

    insert_block = '''

    async def _rollback_vectors(self, chunk_ids: list[str], *, document_id: str | None = None) -> None:
        # Best-effort rollback for partial vector writes
        if not chunk_ids and not document_id:
            return

        store = getattr(self, "_vector_store", None) or getattr(self, "vector_store", None)
        if store is None:
            return

        try:
            if document_id and hasattr(store, "delete_by_document_id"):
                await store.delete_by_document_id(document_id)
                return

            if chunk_ids and hasattr(store, "delete_documents"):
                await store.delete_documents(chunk_ids)
                return
        except Exception as e:
            self._logger.warning(f"Rollback failed: {e}")

'''

    text = text[:idx] + insert_block + text[idx:]

    # inject rollback call in generic except
    except_marker = "except Exception as e:"
    idx2 = text.find(except_marker)
    if idx2 == -1:
        raise RuntimeError("Cannot find generic except")

    rollback_call = "            await self._rollback_vectors(chunk_ids, document_id=document_id)
"
    if rollback_call not in text:
        insert_pos = text.find("self._logger.error", idx2)
        insert_pos = text.find("
", insert_pos) + 1
        text = text[:insert_pos] + rollback_call + text[insert_pos:]

    TARGET.write_text(text, encoding="utf-8")
    print("Patched ingest_service.py successfully.")

if __name__ == "__main__":
    main()
