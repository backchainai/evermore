"""Tests for the shared LLM gateway client builder against retriever Settings.

The pure-builder tests (no real ``retriever.config.Settings`` involved) moved
to ``packages/llm/tests/test_gateway_client.py`` when ``build_gateway_client``
was promoted into the shared ``evermore_llm`` package (issue #93; see ADR
0028's Follow-ups). The 3 tests below stay here because they instantiate the
real ``retriever.config.Settings``: moving them would import a service into a
package, an ADR 0001 violation.
"""

from __future__ import annotations

from evermore_llm import build_gateway_client

from retriever.config import Settings


def test_build_gateway_client_uses_scoped_chat_token() -> None:
    """scope='chat' puts the chat-scoped token on the auth header, not the shared one."""
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        cloudflare_account_id="acct123",
        cloudflare_gateway_id="gw456",
        llm_gateway_token="shared-token",
        llm_gateway_token_chat="chat-token",
    )

    client = build_gateway_client(settings, scope="chat")

    assert client.default_headers["cf-aig-authorization"] == "Bearer chat-token"
    assert client.api_key == "chat-token"


def test_build_gateway_client_scope_falls_back_to_shared_token() -> None:
    """A scope whose scoped field is empty falls back to the shared token on the header."""
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        cloudflare_account_id="acct123",
        cloudflare_gateway_id="gw456",
        llm_gateway_token="shared-token",
    )

    client = build_gateway_client(settings, scope="embeddings")

    assert client.default_headers["cf-aig-authorization"] == "Bearer shared-token"
    assert client.api_key == "shared-token"


def test_build_gateway_client_scope_none_uses_shared_token_directly() -> None:
    """scope=None (the default) uses the shared token even when scoped fields are set."""
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        cloudflare_account_id="acct123",
        cloudflare_gateway_id="gw456",
        llm_gateway_token="shared-token",
        llm_gateway_token_chat="chat-token",
    )

    client = build_gateway_client(settings)

    assert client.default_headers["cf-aig-authorization"] == "Bearer shared-token"
