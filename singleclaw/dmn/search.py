"""MemorySearch – TF-IDF cosine similarity retrieval over a MemoryStore.

Pure-Python implementation; no external runtime dependencies required.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from singleclaw.dmn.memory import MemoryStore


def _tokenize(text: str) -> list[str]:
    """Lowercase and split *text* into word tokens."""
    return re.findall(r"[a-z0-9]+", text.lower())


def _tf(tokens: list[str]) -> dict[str, float]:
    """Compute term-frequency dict for *tokens*."""
    if not tokens:
        return {}
    counts = Counter(tokens)
    total = len(tokens)
    return {term: count / total for term, count in counts.items()}


def _idf(term: str, documents: list[list[str]]) -> float:
    """Compute inverse document frequency for *term* over *documents*."""
    n_docs = len(documents)
    containing = sum(1 for doc in documents if term in doc)
    if containing == 0:
        return 0.0
    return math.log(n_docs / containing)


def _cosine(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """Cosine similarity between two sparse vectors."""
    dot = sum(vec_a.get(t, 0.0) * vec_b.get(t, 0.0) for t in vec_b)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class MemorySearch:
    """Relevance-ranked retrieval over a :class:`~singleclaw.dmn.memory.MemoryStore`.

    Uses TF-IDF cosine similarity computed at query time.  Falls back to
    ``MemoryStore.recent(n=top_k)`` when the store is empty or all similarity
    scores are zero.

    Args:
        store: The :class:`~singleclaw.dmn.memory.MemoryStore` to search.

    Example::

        results = MemorySearch(store).query("vendor procurement", top_k=5)
    """

    def __init__(self, store: "MemoryStore") -> None:
        self._store = store

    def query(self, text: str, top_k: int = 5) -> list[dict]:
        """Return the *top_k* most relevant memory records for *text*.

        Args:
            text:   The query string.
            top_k:  Maximum number of records to return.

        Returns:
            List of record dicts ordered from most to least relevant.  Falls
            back to the most recent *top_k* records when no record scores above
            zero.
        """
        records = self._store.list_all()
        if not records:
            return []

        # Tokenise all documents
        doc_tokens: list[list[str]] = [_tokenize(r.get("text", "")) for r in records]
        query_tokens = _tokenize(text)

        if not query_tokens:
            return self._store.recent(n=top_k)

        # Build vocabulary of unique terms appearing in query *and* any document
        vocab = set(query_tokens)
        for tokens in doc_tokens:
            vocab.update(tokens)

        # Compute TF-IDF vector for the query
        query_tf = _tf(query_tokens)
        query_vec: dict[str, float] = {
            term: query_tf.get(term, 0.0) * _idf(term, doc_tokens)
            for term in vocab
            if term in query_tf
        }

        # Compute TF-IDF vectors for each document and score against query
        scored: list[tuple[float, dict]] = []
        for tokens, record in zip(doc_tokens, records):
            doc_tf = _tf(tokens)
            doc_vec: dict[str, float] = {
                term: doc_tf.get(term, 0.0) * _idf(term, doc_tokens)
                for term in vocab
                if term in doc_tf
            }
            score = _cosine(doc_vec, query_vec)
            scored.append((score, record))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)

        # Fallback: if every score is zero, return most recent records
        if scored[0][0] == 0.0:
            return self._store.recent(n=top_k)

        return [record for _, record in scored[:top_k]]
