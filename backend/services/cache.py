"""
FAISS-based semantic similarity cache.
Falls back gracefully if sentence-transformers or faiss are not available.
"""
from typing import Optional
import json

_model = None
_index = None
_records: list[dict] = []  # [{id, result}]
_dim: int = 384

SIMILARITY_THRESHOLD = 0.92

def _load():
    global _model, _index, _dim
    if _model is not None:
        return True
    try:
        from sentence_transformers import SentenceTransformer
        import faiss
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        _dim = _model.get_sentence_embedding_dimension()
        _index = faiss.IndexFlatIP(_dim)
        return True
    except Exception:
        _model = False
        return False

def encode(text: str):
    if not _load() or not _model:
        return None
    import numpy as np
    vec = _model.encode([text[:1000]], normalize_embeddings=True)
    return vec.astype("float32")

def search(text: str) -> Optional[tuple[dict, float]]:
    if not _records or not _load() or not _model or _index is None:
        return None
    import faiss
    vec = encode(text)
    if vec is None:
        return None
    D, I = _index.search(vec, 1)
    score = float(D[0][0])
    idx = int(I[0][0])
    if score >= SIMILARITY_THRESHOLD and 0 <= idx < len(_records):
        return _records[idx], score
    return None

def add(text: str, result: dict):
    global _index
    if not _load() or not _model or _index is None:
        return
    vec = encode(text)
    if vec is None:
        return
    _index.add(vec)
    _records.append(result)
