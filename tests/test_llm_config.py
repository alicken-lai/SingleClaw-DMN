"""Tests for LLM configuration and auth mode detection."""

from __future__ import annotations

import time

import pytest

from singleclaw.llm.config import AuthMode, LLMConfig, Provider
from singleclaw.llm.exceptions import AuthNotConfiguredError


class TestLLMConfigAuthModeDetection:
    def test_resolves_api_key_mode_when_openai_key_set(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test123")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("SINGLECLAW_LLM_PROVIDER", raising=False)

        config = LLMConfig.resolve(workspace_dir=tmp_path)

        assert config.auth_mode == AuthMode.API_KEY
        assert config.provider == Provider.OPENAI
        assert config.api_key == "sk-test123"

    def test_resolves_api_key_mode_when_gemini_key_set(self, tmp_path, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("GEMINI_API_KEY", "AIzatest")
        monkeypatch.setenv("SINGLECLAW_LLM_PROVIDER", "google")

        config = LLMConfig.resolve(workspace_dir=tmp_path)

        assert config.auth_mode == AuthMode.API_KEY
        assert config.provider == Provider.GOOGLE
        assert config.api_key == "AIzatest"

    def test_resolves_oauth_mode_when_valid_token_exists(self, tmp_path, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.setenv("SINGLECLAW_LLM_PROVIDER", "google")

        # Write a valid (non-expired) token file.
        import base64
        import json
        token = {"access_token": "ya29.test", "expires_in": 3600, "saved_at": int(time.time())}
        encoded = base64.b64encode(json.dumps(token).encode()).decode()
        token_file = tmp_path / "auth_token.json"
        token_file.write_text(json.dumps({"v": 1, "data": encoded}))

        config = LLMConfig.resolve(workspace_dir=tmp_path)

        assert config.auth_mode == AuthMode.OAUTH
        assert config.provider == Provider.GOOGLE
        assert config.token_path == token_file

    def test_raises_when_no_auth_configured(self, tmp_path, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("SINGLECLAW_LLM_PROVIDER", raising=False)

        with pytest.raises(AuthNotConfiguredError):
            LLMConfig.resolve(workspace_dir=tmp_path)

    def test_api_key_takes_priority_over_oauth_token(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-priority")
        monkeypatch.delenv("SINGLECLAW_LLM_PROVIDER", raising=False)

        # Also write an OAuth token – should be ignored because API key is set.
        import base64
        import json
        token = {"access_token": "ya29.oauth", "expires_in": 3600, "saved_at": int(time.time())}
        encoded = base64.b64encode(json.dumps(token).encode()).decode()
        (tmp_path / "auth_token.json").write_text(json.dumps({"v": 1, "data": encoded}))

        config = LLMConfig.resolve(workspace_dir=tmp_path)

        assert config.auth_mode == AuthMode.API_KEY
        assert config.api_key == "sk-priority"

    def test_expired_oauth_token_falls_through_to_error(self, tmp_path, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.setenv("SINGLECLAW_LLM_PROVIDER", "google")

        # Write an expired token.
        import base64
        import json
        token = {
            "access_token": "ya29.expired",
            "expires_in": 60,
            "saved_at": int(time.time()) - 7200,  # saved 2 hours ago
        }
        encoded = base64.b64encode(json.dumps(token).encode()).decode()
        (tmp_path / "auth_token.json").write_text(json.dumps({"v": 1, "data": encoded}))

        with pytest.raises(AuthNotConfiguredError):
            LLMConfig.resolve(workspace_dir=tmp_path)

    def test_unknown_provider_env_falls_back_to_openai(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-abc")
        monkeypatch.setenv("SINGLECLAW_LLM_PROVIDER", "unknownprovider")

        config = LLMConfig.resolve(workspace_dir=tmp_path)

        assert config.provider == Provider.OPENAI

    def test_whitespace_api_key_treated_as_absent(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "   ")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("SINGLECLAW_LLM_PROVIDER", raising=False)

        with pytest.raises(AuthNotConfiguredError):
            LLMConfig.resolve(workspace_dir=tmp_path)
