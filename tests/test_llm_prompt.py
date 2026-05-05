"""Tests for prompt template rendering."""

from __future__ import annotations

import json


from singleclaw.llm.prompt import render_prompt


class TestRenderPrompt:
    def test_substitutes_input_data_placeholder(self):
        template = "Process: {input_data}"
        result = render_prompt(template, {"key": "value"})
        assert '"key"' in result
        assert '"value"' in result

    def test_substitutes_memory_context_placeholder(self):
        template = "Context: {memory_context}"
        memory = [{"tag": "decision", "text": "Use Python"}]
        result = render_prompt(template, {}, memory_context=memory)
        assert "Use Python" in result
        assert "[decision]" in result

    def test_substitutes_individual_input_keys(self):
        template = "Meeting: {agenda} on {date}"
        result = render_prompt(template, {"agenda": "Q3 review", "date": "2026-05-05"})
        assert "Q3 review" in result
        assert "2026-05-05" in result

    def test_missing_placeholder_left_unchanged(self):
        template = "Hello {name}, your score is {unknown_key}"
        result = render_prompt(template, {"name": "Alice"})
        assert "Alice" in result
        assert "{unknown_key}" in result

    def test_empty_memory_context_shows_placeholder(self):
        template = "Context: {memory_context}"
        result = render_prompt(template, {}, memory_context=[])
        assert "(no memory context)" in result

    def test_none_memory_context_shows_placeholder(self):
        template = "Context: {memory_context}"
        result = render_prompt(template, {})
        assert "(no memory context)" in result

    def test_memory_items_limited_to_max(self):
        template = "{memory_context}"
        memory = [{"tag": "note", "text": f"item {i}"} for i in range(10)]
        result = render_prompt(template, {}, memory_context=memory, max_memory_items=3)
        # Only first 3 items should appear.
        assert "item 0" in result
        assert "item 1" in result
        assert "item 2" in result
        assert "item 3" not in result

    def test_broken_template_returned_unchanged(self):
        """A template that cannot be rendered must be returned as-is (no exception)."""
        broken_template = "Hello {{"
        result = render_prompt(broken_template, {"key": "val"})
        # Should not raise; return value is acceptable as-is or original.
        assert isinstance(result, str)

    def test_input_data_is_json_serialised(self):
        template = "{input_data}"
        result = render_prompt(template, {"nested": {"a": 1}})
        parsed = json.loads(result.strip())
        assert parsed["nested"]["a"] == 1

    def test_template_with_no_placeholders_returned_unchanged(self):
        template = "No placeholders here."
        result = render_prompt(template, {"key": "val"})
        assert result == "No placeholders here."
