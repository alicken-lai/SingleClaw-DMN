"""Tests for MemorySearch – TF-IDF cosine similarity retrieval."""

from __future__ import annotations

from singleclaw.dmn.memory import MemoryStore
from singleclaw.dmn.search import MemorySearch


class TestMemorySearchQuery:
    def test_returns_top_k_by_relevance(self, tmp_path):
        store = MemoryStore(tmp_path)
        store.add("vendor procurement budget approval", tag="decision")
        store.add("team meeting agenda notes", tag="note")
        store.add("supplier contract renewal vendor", tag="decision")
        store.add("lunch preference sushi", tag="personal")
        store.add("procurement vendor evaluation criteria", tag="decision")

        results = MemorySearch(store).query("vendor procurement", top_k=3)

        assert len(results) == 3
        texts = [r["text"] for r in results]
        # The three vendor/procurement items should rank above unrelated ones
        assert "vendor procurement budget approval" in texts
        assert "supplier contract renewal vendor" in texts
        assert "procurement vendor evaluation criteria" in texts

    def test_top_k_respected(self, tmp_path):
        store = MemoryStore(tmp_path)
        for i in range(10):
            store.add(f"alpha beta gamma item {i}", tag="note")

        results = MemorySearch(store).query("alpha beta", top_k=4)
        assert len(results) == 4

    def test_top_k_larger_than_store_returns_all(self, tmp_path):
        store = MemoryStore(tmp_path)
        store.add("only item", tag="note")

        results = MemorySearch(store).query("only item", top_k=10)
        assert len(results) == 1

    def test_empty_store_returns_empty_list(self, tmp_path):
        store = MemoryStore(tmp_path)
        results = MemorySearch(store).query("anything", top_k=5)
        assert results == []

    def test_zero_score_fallback_to_recent(self, tmp_path):
        store = MemoryStore(tmp_path)
        for i in range(6):
            store.add(f"item {i}", tag="note")

        # Query with a term that matches nothing → should fall back to recent(n=3)
        results = MemorySearch(store).query("xyzzy quux", top_k=3)
        assert len(results) == 3
        # Fallback returns the most recent 3 items
        assert results[-1]["text"] == "item 5"

    def test_result_records_contain_original_fields(self, tmp_path):
        store = MemoryStore(tmp_path)
        store.add("procurement budget review", tag="decision")

        results = MemorySearch(store).query("procurement budget", top_k=1)
        assert len(results) == 1
        r = results[0]
        assert "id" in r
        assert "timestamp" in r
        assert "tag" in r
        assert r["text"] == "procurement budget review"

    def test_query_is_case_insensitive(self, tmp_path):
        store = MemoryStore(tmp_path)
        store.add("VENDOR Procurement Decision", tag="decision")
        store.add("team lunch meeting", tag="note")

        results = MemorySearch(store).query("vendor procurement", top_k=1)
        assert results[0]["text"] == "VENDOR Procurement Decision"

    def test_scores_ranked_highest_first(self, tmp_path):
        store = MemoryStore(tmp_path)
        store.add("procurement vendor approval", tag="decision")      # 2 matching terms
        store.add("procurement review", tag="decision")               # 1 matching term
        store.add("unrelated item about lunch", tag="personal")       # 0 matching terms

        results = MemorySearch(store).query("procurement vendor", top_k=2)
        assert len(results) == 2
        assert results[0]["text"] == "procurement vendor approval"
