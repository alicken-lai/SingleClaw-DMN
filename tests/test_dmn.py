"""Tests for DMN memory store and task journal."""


from singleclaw.dmn.memory import MemoryStore
from singleclaw.dmn.journal import TaskJournal


class TestMemoryStore:
    def test_add_and_list(self, tmp_path):
        store = MemoryStore(tmp_path)
        record = store.add("Hello world", tag="note")

        assert record["text"] == "Hello world"
        assert record["tag"] == "note"
        assert "id" in record
        assert "timestamp" in record

        all_items = store.list_all()
        assert len(all_items) == 1
        assert all_items[0]["text"] == "Hello world"

    def test_recent_returns_last_n(self, tmp_path):
        store = MemoryStore(tmp_path)
        for i in range(5):
            store.add(f"item {i}")

        recent = store.recent(n=3)
        assert len(recent) == 3
        assert recent[-1]["text"] == "item 4"

    def test_by_tag_filter(self, tmp_path):
        store = MemoryStore(tmp_path)
        store.add("decision 1", tag="decision")
        store.add("note 1", tag="note")
        store.add("decision 2", tag="decision")

        decisions = store.by_tag("decision")
        assert len(decisions) == 2
        assert all(r["tag"] == "decision" for r in decisions)

    def test_notes_file_updated(self, tmp_path):
        store = MemoryStore(tmp_path)
        store.add("Test memory", tag="test")

        notes_path = tmp_path / "memory_notes.md"
        assert notes_path.exists()
        content = notes_path.read_text(encoding="utf-8")
        assert "Test memory" in content
        assert "[test]" in content

    def test_empty_store_returns_empty_list(self, tmp_path):
        store = MemoryStore(tmp_path)
        assert store.list_all() == []
        assert store.recent() == []


class TestTaskJournal:
    def test_log_creates_file(self, tmp_path):
        journal = TaskJournal(tmp_path)
        journal.log(command="test", status="success")

        journal_path = tmp_path / "journal.jsonl"
        assert journal_path.exists()

    def test_log_record_structure(self, tmp_path):
        journal = TaskJournal(tmp_path)
        journal.log(command="run", input_summary="skill=foo", status="success", risk_level="low")

        records = journal.load()
        assert len(records) == 1
        r = records[0]
        assert r["command"] == "run"
        assert r["input_summary"] == "skill=foo"
        assert r["status"] == "success"
        assert r["risk_level"] == "low"

    def test_recent_returns_last_n(self, tmp_path):
        journal = TaskJournal(tmp_path)
        for i in range(5):
            journal.log(command=f"cmd{i}", status="success")

        recent = journal.recent(n=2)
        assert len(recent) == 2
        assert recent[-1]["command"] == "cmd4"

    def test_log_skipped_when_workspace_missing(self, tmp_path):
        # workspace_dir does not exist – log should be silently skipped
        missing = tmp_path / "does_not_exist"
        journal = TaskJournal(missing)
        journal.log(command="init", status="success")  # should not raise
        assert not (missing / "journal.jsonl").exists()
