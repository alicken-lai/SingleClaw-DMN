# ADR 0005 – LLM Authentication Dual-Mode (API Key + OAuth Device Flow)

**Status:** Accepted  
**Date:** 2026-05-05  
**Deciders:** @alicken-lai

---

## Context

v0.2 introduces real LLM integration into `SkillRunner`.  Different users have
different preferences and constraints for authenticating with LLM providers:

1. **Power users / developers** already hold an API key (OpenAI, Gemini) and
   prefer to paste it once in `.env`.  This is the fastest path.

2. **Non-technical users / teams** do not want to manage API keys.  They
   prefer to log in once with their existing Google or other provider account
   via a browser – exactly as they do with any SaaS product.

Neither mode should require the other; the system must support both without
forcing the user to choose up front (auto-detect is preferred).

---

## Decision

Introduce a `singleclaw/llm/` subsystem with a unified `LLMClient` protocol
that hides the authentication mechanism from `SkillRunner` and the CLI.

### Auth modes

| Mode | Trigger | Mechanism |
|------|---------|-----------|
| `api_key` | `OPENAI_API_KEY` or `GEMINI_API_KEY` env var set | Read key from env / `.env` file at start-up |
| `oauth` | No API key, `.singleclaw/auth_token.json` present and valid | Load persisted OAuth access token |
| *(interactive)* | Neither | CLI prompts: enter key **or** run `singleclaw auth login` |

**Priority order** (auto-detected by `LLMConfig.resolve()`):

1. API key env var present → `ApiKeyAuth`
2. Stored OAuth token present and unexpired → `OAuthTokenAuth`
3. Neither → raise `AuthNotConfiguredError` with helpful message

### OAuth standard: RFC 8628 Device Authorization Grant

Device Flow was chosen because:
- Works in terminal environments without a redirect URI.
- The user authenticates in their default browser; no copy-pasting tokens.
- Widely supported by Google (initial target provider for OAuth path).

Flow:
1. POST to provider's device-authorization endpoint → `device_code`, `user_code`, `verification_uri`.
2. CLI displays the URL and code via Rich; opens browser with `webbrowser.open()`.
3. Poll token endpoint every `interval` seconds until `access_token` arrives or timeout.
4. Store token in `.singleclaw/auth_token.json` (base64-obfuscated, never in git).

### Provider support matrix (v0.2)

| Provider | API Key | OAuth Device Flow |
|----------|---------|-------------------|
| OpenAI | ✔ | ✗ (not supported by OpenAI) |
| Google Gemini | ✔ | ✔ (Google OAuth 2.0) |
| Ollama (local) | ✗ (not required) | ✗ (not required) |

### HTTP client

All outbound HTTP calls to LLM APIs use **`httpx`** (sync client).  `httpx`
was chosen over `requests` because it provides a cleaner API, supports both
sync and async, and is well-maintained.

### Token storage

OAuth tokens are stored as JSON in `.singleclaw/auth_token.json`.  The file
is base64-obfuscated (not cryptographically encrypted) to avoid trivial
exposure in logs or screenshots.  The file is already covered by `.gitignore`.

The `keyring` library is used **if available** as a higher-security alternative
that delegates storage to the OS credential manager (macOS Keychain, Windows
Credential Locker, libsecret on Linux).

### Prompt templates

Each runnable skill may define a `prompt_template` string in its `skill.yaml`.
`singleclaw/llm/prompt.py` renders the template with `str.format_map()`,
injecting `input_data` and `memory_context`.

### SkillRunner fallback

When no LLM auth is configured, `SkillRunner` falls back to the existing
v0.1 placeholder output with a one-line suggestion to configure auth.

---

## Consequences

**Positive:**
- Zero-friction auth for both technical and non-technical users.
- `SkillRunner` and skills remain auth-agnostic; all provider detail is inside `singleclaw/llm/`.
- Device Flow adds no redirect-URI configuration burden.
- `LLMClient` Protocol makes it trivial to add new providers (Anthropic, Ollama, …).

**Negative / Trade-offs:**
- Device Flow requires internet access; Ollama (local) only uses API-key-free path.
- Base64 obfuscation is not encryption; users on shared machines should use `keyring`.
- Google Device Flow requires a registered OAuth 2.0 client ID (`GOOGLE_CLIENT_ID` env var).

**Architecture invariants preserved:**
- `singleclaw/skills/runner.py` does not import from `singleclaw/llm/` directly;
  the `LLMClient` instance (or `None`) is injected by `cli.py`.
- `singleclaw/llm/` does not import from `singleclaw/dmn/`; memory context is
  passed as a plain `list[dict]`.
