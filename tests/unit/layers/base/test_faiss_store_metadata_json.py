from src.core.contracts import VectorDocument
from src.layers.base.rag.vector_stores.faiss_store import FAISSVectorStore


def test_faiss_metadata_document_json_roundtrip(tmp_path):
    store = FAISSVectorStore(index_path=str(tmp_path / "faiss_index"), dimension=4)
    doc = VectorDocument(
        id="doc-1",
        content="hello world",
        metadata={"workspace_id": "default"},
        embedding=[0.1, 0.2, 0.3, 0.4],
    )

    payload = store._serialize_document(doc)
    decoded = store._deserialize_document(payload, fallback_id="fallback")

    assert decoded is not None
    assert decoded.id == "doc-1"
    assert decoded.metadata["workspace_id"] == "default"
    assert decoded.embedding == [0.1, 0.2, 0.3, 0.4]


def test_faiss_metadata_deserialize_legacy_vector_document(tmp_path):
    store = FAISSVectorStore(index_path=str(tmp_path / "faiss_index"), dimension=4)
    legacy_doc = VectorDocument(
        id="doc-legacy",
        content="legacy payload",
        metadata={"source": "pickle"},
        embedding=[0.11, 0.22, 0.33, 0.44],
    )

    decoded = store._deserialize_document(legacy_doc, fallback_id="fallback")

    assert decoded is not None
    assert decoded.id == "doc-legacy"
    assert decoded.metadata["source"] == "pickle"
