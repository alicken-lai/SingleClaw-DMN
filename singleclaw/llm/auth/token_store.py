"""OAuth token persistence – read / write / validate stored tokens.

Tokens are stored in ``<workspace>/.singleclaw/auth_token.json`` as a
base64-encoded JSON blob.  Base64 provides basic obfuscation so the token is
not immediately visible in terminal output or screenshots; it is **not**
cryptographic encryption.

If the ``keyring`` package is installed, :class:`TokenStore` will prefer to
save the raw token in the OS credential manager (macOS Keychain, Windows
Credential Locker, libsecret on Linux) instead of the JSON file.
"""

from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from typing import Any, Optional

# Service/user identifiers used when keyring is available.
_KEYRING_SERVICE = "singleclaw-dmn"
_KEYRING_USER = "oauth_token"


class TokenStore:
    """Read and write OAuth tokens to/from persistent storage.

    Args:
        token_path: Path to the JSON file used when ``keyring`` is unavailable.
    """

    def __init__(self, token_path: Path) -> None:
        self._path = Path(token_path)

    # ── write ────────────────────────────────────────────────────────────────

    def save(self, token_data: dict[str, Any]) -> None:
        """Persist *token_data* to storage.

        The dict should contain at minimum ``access_token`` and, if provided
        by the provider, ``expires_in`` (seconds from now) and
        ``refresh_token``.  A ``saved_at`` epoch timestamp is always added
        automatically so expiry can be checked later.

        Args:
            token_data: Raw token dict from the OAuth provider.
        """
        enriched = dict(token_data)
        enriched["saved_at"] = int(time.time())

        if _try_keyring_save(enriched):
            return  # stored in OS keychain

        # Fall back to base64-obfuscated JSON file.
        self._path.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(enriched, ensure_ascii=False)
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        self._path.write_text(
            json.dumps({"v": 1, "data": encoded}) + "\n", encoding="utf-8"
        )

    # ── read ─────────────────────────────────────────────────────────────────

    def load(self) -> Optional[dict[str, Any]]:
        """Return the stored token dict, or ``None`` if none is found."""
        # Try keyring first.
        token = _try_keyring_load()
        if token is not None:
            return token

        if not self._path.exists():
            return None

        try:
            wrapper = json.loads(self._path.read_text(encoding="utf-8"))
            encoded = wrapper.get("data", "")
            raw = base64.b64decode(encoded.encode("ascii")).decode("utf-8")
            return json.loads(raw)
        except Exception:  # noqa: BLE001
            return None

    def delete(self) -> None:
        """Remove the stored token from all storage backends."""
        _try_keyring_delete()
        if self._path.exists():
            self._path.unlink()

    # ── validation ────────────────────────────────────────────────────────────

    def is_valid(self) -> bool:
        """Return ``True`` when a token exists and has not expired.

        A token without ``expires_in`` is considered non-expiring (valid
        indefinitely).  A token is considered expired 60 seconds before its
        actual expiry time to avoid using a token that is about to expire.
        """
        token = self.load()
        if token is None:
            return False
        if "access_token" not in token:
            return False
        expires_in = token.get("expires_in")
        saved_at = token.get("saved_at", 0)
        if expires_in is None:
            return True  # no expiry information – assume valid
        expiry_epoch = saved_at + int(expires_in) - 60  # 60-second grace period
        return int(time.time()) < expiry_epoch

    def get_access_token(self) -> Optional[str]:
        """Return the raw access token string, or ``None``."""
        token = self.load()
        if token is None:
            return None
        return token.get("access_token")


# ── keyring helpers ──────────────────────────────────────────────────────────


def _try_keyring_save(token_data: dict[str, Any]) -> bool:
    """Save *token_data* to the OS keychain.  Returns ``True`` on success."""
    try:
        import keyring  # type: ignore[import]

        raw = json.dumps(token_data, ensure_ascii=False)
        keyring.set_password(_KEYRING_SERVICE, _KEYRING_USER, raw)
        return True
    except Exception:  # noqa: BLE001
        return False


def _try_keyring_load() -> Optional[dict[str, Any]]:
    """Load token from the OS keychain.  Returns ``None`` on failure."""
    try:
        import keyring  # type: ignore[import]

        raw = keyring.get_password(_KEYRING_SERVICE, _KEYRING_USER)
        if raw:
            return json.loads(raw)
    except Exception:  # noqa: BLE001
        pass
    return None


def _try_keyring_delete() -> None:
    """Remove token from the OS keychain (best-effort)."""
    try:
        import keyring  # type: ignore[import]

        keyring.delete_password(_KEYRING_SERVICE, _KEYRING_USER)
    except Exception:  # noqa: BLE001
        pass
