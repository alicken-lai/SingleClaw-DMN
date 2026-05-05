"""Tests for token store – read / write / validate / delete."""

from __future__ import annotations

import base64
import json
import time


from singleclaw.llm.auth.token_store import TokenStore


class TestTokenStore:
    def test_save_and_load_roundtrip(self, tmp_path):
        token_path = tmp_path / "auth_token.json"
        store = TokenStore(token_path)

        token_data = {"access_token": "ya29.test", "token_type": "Bearer"}
        store.save(token_data)

        loaded = store.load()
        assert loaded is not None
        assert loaded["access_token"] == "ya29.test"
        assert loaded["token_type"] == "Bearer"
        # saved_at timestamp is added automatically
        assert "saved_at" in loaded

    def test_file_is_base64_obfuscated(self, tmp_path):
        token_path = tmp_path / "auth_token.json"
        store = TokenStore(token_path)
        store.save({"access_token": "plain_text_secret"})

        raw = token_path.read_text(encoding="utf-8")
        # The token value must not appear as plaintext in the file.
        assert "plain_text_secret" not in raw
        # But the wrapper must be valid JSON with 'data' key.
        wrapper = json.loads(raw)
        assert "data" in wrapper
        assert wrapper["v"] == 1

    def test_load_returns_none_when_file_missing(self, tmp_path):
        store = TokenStore(tmp_path / "nonexistent.json")
        assert store.load() is None

    def test_load_returns_none_for_corrupt_file(self, tmp_path):
        token_path = tmp_path / "bad.json"
        token_path.write_text("not-valid-json", encoding="utf-8")
        store = TokenStore(token_path)
        assert store.load() is None

    def test_is_valid_returns_true_for_fresh_token(self, tmp_path):
        store = TokenStore(tmp_path / "token.json")
        store.save({"access_token": "ya29.fresh", "expires_in": 3600})
        assert store.is_valid() is True

    def test_is_valid_returns_false_for_expired_token(self, tmp_path):
        store = TokenStore(tmp_path / "token.json")
        # Manually write an expired token (saved 2 hours ago, expires in 60s).
        token = {
            "access_token": "ya29.expired",
            "expires_in": 60,
            "saved_at": int(time.time()) - 7200,
        }
        encoded = base64.b64encode(json.dumps(token).encode()).decode()
        (tmp_path / "token.json").write_text(json.dumps({"v": 1, "data": encoded}))

        assert store.is_valid() is False

    def test_is_valid_returns_true_when_no_expiry_info(self, tmp_path):
        store = TokenStore(tmp_path / "token.json")
        store.save({"access_token": "ya29.noexpiry"})
        assert store.is_valid() is True

    def test_is_valid_returns_false_when_file_missing(self, tmp_path):
        store = TokenStore(tmp_path / "missing.json")
        assert store.is_valid() is False

    def test_delete_removes_file(self, tmp_path):
        token_path = tmp_path / "token.json"
        store = TokenStore(token_path)
        store.save({"access_token": "ya29.todelete"})
        assert token_path.exists()

        store.delete()
        assert not token_path.exists()

    def test_delete_is_safe_when_file_missing(self, tmp_path):
        store = TokenStore(tmp_path / "absent.json")
        store.delete()  # must not raise

    def test_get_access_token_returns_token_string(self, tmp_path):
        store = TokenStore(tmp_path / "token.json")
        store.save({"access_token": "ya29.mytoken", "expires_in": 3600})
        assert store.get_access_token() == "ya29.mytoken"

    def test_get_access_token_returns_none_when_missing(self, tmp_path):
        store = TokenStore(tmp_path / "absent.json")
        assert store.get_access_token() is None

    def test_parent_directory_created_on_save(self, tmp_path):
        nested_path = tmp_path / "nested" / "dir" / "token.json"
        store = TokenStore(nested_path)
        store.save({"access_token": "ya29.nested"})
        assert nested_path.exists()
