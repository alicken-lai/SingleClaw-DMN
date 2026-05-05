"""Tests for the auth CLI sub-commands (login, logout, status)."""

from __future__ import annotations

import base64
import json
import time
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from singleclaw.cli import app


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def workspace(tmp_path):
    """Create an initialised workspace in tmp_path."""
    ws = tmp_path / ".singleclaw"
    ws.mkdir()
    (ws / "journal.jsonl").touch()
    return tmp_path


class TestAuthStatus:
    def test_shows_unauthenticated_when_no_config(self, runner, workspace, monkeypatch):
        monkeypatch.chdir(workspace)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("SINGLECLAW_LLM_PROVIDER", raising=False)

        result = runner.invoke(app, ["auth", "status"])

        assert result.exit_code == 0
        assert "Not authenticated" in result.output

    def test_shows_authenticated_when_api_key_set(self, runner, workspace, monkeypatch):
        monkeypatch.chdir(workspace)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("SINGLECLAW_LLM_PROVIDER", raising=False)

        result = runner.invoke(app, ["auth", "status"])

        assert result.exit_code == 0
        assert "Authenticated" in result.output
        assert "openai" in result.output
        assert "api_key" in result.output

    def test_shows_authenticated_for_oauth_token(self, runner, workspace, monkeypatch):
        monkeypatch.chdir(workspace)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.setenv("SINGLECLAW_LLM_PROVIDER", "google")

        # Write a valid token.
        token = {"access_token": "ya29.x", "expires_in": 3600, "saved_at": int(time.time())}
        encoded = base64.b64encode(json.dumps(token).encode()).decode()
        (workspace / ".singleclaw" / "auth_token.json").write_text(
            json.dumps({"v": 1, "data": encoded})
        )

        result = runner.invoke(app, ["auth", "status"])

        assert result.exit_code == 0
        assert "Authenticated" in result.output
        assert "oauth" in result.output


class TestAuthLogout:
    def test_logout_removes_token_file(self, runner, workspace, monkeypatch):
        monkeypatch.chdir(workspace)

        token = {"access_token": "ya29.todelete"}
        encoded = base64.b64encode(json.dumps(token).encode()).decode()
        token_path = workspace / ".singleclaw" / "auth_token.json"
        token_path.write_text(json.dumps({"v": 1, "data": encoded}))
        assert token_path.exists()

        result = runner.invoke(app, ["auth", "logout"])

        assert result.exit_code == 0
        assert "Logged out" in result.output
        assert not token_path.exists()

    def test_logout_is_safe_when_no_token_exists(self, runner, workspace, monkeypatch):
        monkeypatch.chdir(workspace)
        result = runner.invoke(app, ["auth", "logout"])
        assert result.exit_code == 0


class TestAuthLogin:
    def test_login_fails_for_unsupported_provider(self, runner, workspace, monkeypatch):
        monkeypatch.chdir(workspace)
        result = runner.invoke(app, ["auth", "login", "--provider", "openai"])
        assert result.exit_code == 1
        assert "does not support" in result.output

    def test_login_fails_when_client_id_not_set(self, runner, workspace, monkeypatch):
        monkeypatch.chdir(workspace)
        monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)

        result = runner.invoke(app, ["auth", "login", "--provider", "google"])

        assert result.exit_code == 1
        assert "GOOGLE_CLIENT_ID" in result.output

    def test_login_success_saves_token(self, runner, workspace, monkeypatch):
        monkeypatch.chdir(workspace)
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")

        token_data = {
            "access_token": "ya29.saved_by_test",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        with patch("singleclaw.llm.auth.oauth_device.DeviceFlow") as MockFlow:
            instance = MockFlow.return_value
            instance.run.return_value = token_data

            result = runner.invoke(app, ["auth", "login", "--provider", "google"])

        assert result.exit_code == 0
        assert "Authenticated" in result.output or "Token saved" in result.output

        token_path = workspace / ".singleclaw" / "auth_token.json"
        assert token_path.exists()
