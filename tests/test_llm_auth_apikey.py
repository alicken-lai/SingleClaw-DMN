"""Tests for API key authentication helper."""

from __future__ import annotations


from singleclaw.llm.auth.api_key import get_api_key


class TestGetApiKey:
    def test_returns_key_when_env_var_set(self, monkeypatch):
        monkeypatch.setenv("TEST_API_KEY", "sk-test")
        assert get_api_key("TEST_API_KEY") == "sk-test"

    def test_returns_none_when_env_var_absent(self, monkeypatch):
        monkeypatch.delenv("TEST_API_KEY", raising=False)
        assert get_api_key("TEST_API_KEY") is None

    def test_returns_none_for_empty_string(self, monkeypatch):
        monkeypatch.setenv("TEST_API_KEY", "")
        assert get_api_key("TEST_API_KEY") is None

    def test_returns_none_for_whitespace_only(self, monkeypatch):
        monkeypatch.setenv("TEST_API_KEY", "   ")
        assert get_api_key("TEST_API_KEY") is None

    def test_strips_surrounding_whitespace(self, monkeypatch):
        monkeypatch.setenv("TEST_API_KEY", "  sk-abc  ")
        assert get_api_key("TEST_API_KEY") == "sk-abc"
