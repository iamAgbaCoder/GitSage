"""Tests for providers.gitsage.GitSageAPIProvider (uses respx to mock httpx)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from config.remote import get_remote_config
from providers.gitsage import (
    AnalysisResult,
    AuthenticationError,
    GitSageAPIProvider,
    RateLimitError,
    _clean_commit_message,
)


# Use default or dynamic base for tests
def _get_test_endpoint():
    config = get_remote_config()
    base = config.get("api_base_url", "https://gitsage-api.up.railway.app").rstrip("/")
    return f"{base}/v1/intelligence/analyze"


ENDPOINT = _get_test_endpoint()

GOOD_RESPONSE = {
    "success": True,
    "message": "Request successful",
    "data": {
        "commit_message": "feat: add user authentication",
        "explanation": "🧠 What changed:\n- Added auth module\n💡 Why it matters:\nSecurity\n🎯 Scope:\nauth.py",
        "confidence": 87,
        "analysis_time_ms": 430,
        "provider": "openai",
        "model": "gpt-4o",
    },
}


# ── _clean_commit_message unit tests ──────────────────────────────────────


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("feat: plain message", "feat: plain message"),
        ("**feat: bold**", "feat: bold"),
        ("`feat: backtick`", "feat: backtick"),
        ("**`feat: both`**", "feat: both"),
        (
            "**\n`feat: multiline`\n\n**EXPLANATION**\nstuff",
            "feat: multiline",
        ),
        ("  feat: whitespace  ", "feat: whitespace"),
        (
            "feat: with explanation\nEXPLANATION: details here",
            "feat: with explanation",
        ),
    ],
)
def test_clean_commit_message(raw: str, expected: str):
    assert _clean_commit_message(raw) == expected


# ── Network-level tests (respx) ────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_analyze_success():
    respx.post(ENDPOINT).mock(return_value=httpx.Response(200, json=GOOD_RESPONSE))

    provider = GitSageAPIProvider(api_key="gs_test_key_123")
    result = await provider.analyze_diff_async(
        diff="+ new line", context="feat branch", style="conventional"
    )
    await provider.close()

    assert isinstance(result, AnalysisResult)
    assert result.commit_message == "feat: add user authentication"
    assert result.confidence == 0.87  # normalised from 87
    assert result.provider == "openai"
    assert result.model == "gpt-4o"


@pytest.mark.asyncio
@respx.mock
async def test_analyze_401_raises_auth_error():
    respx.post(ENDPOINT).mock(
        return_value=httpx.Response(
            200,
            json={"success": False, "statusCode": 401, "message": "Invalid API Key."},
        )
    )

    provider = GitSageAPIProvider(api_key="gs_bad_key")
    with pytest.raises(AuthenticationError):
        await provider.analyze_diff_async(diff="diff text")
    await provider.close()


@pytest.mark.asyncio
@respx.mock
async def test_analyze_429_raises_rate_limit():
    respx.post(ENDPOINT).mock(
        return_value=httpx.Response(
            200,
            json={
                "success": False,
                "statusCode": 429,
                "message": "Rate limit exceeded. Upgrade your plan.",
            },
        )
    )

    provider = GitSageAPIProvider(api_key="gs_test_key")
    with pytest.raises(RateLimitError, match="Rate limit exceeded"):
        await provider.analyze_diff_async(diff="diff text")
    await provider.close()


@pytest.mark.asyncio
@respx.mock
async def test_analyze_timeout_raises_runtime_error():
    respx.post(ENDPOINT).mock(side_effect=httpx.TimeoutException("timed out"))

    provider = GitSageAPIProvider(api_key="gs_test_key")
    with pytest.raises(RuntimeError, match="timed out"):
        await provider.analyze_diff_async(diff="diff text")
    await provider.close()


@pytest.mark.asyncio
@respx.mock
async def test_analyze_network_error_raises_runtime_error():
    respx.post(ENDPOINT).mock(side_effect=httpx.NetworkError("no route to host"))

    provider = GitSageAPIProvider(api_key="gs_test_key")
    with pytest.raises(RuntimeError, match="reach the GitSage API"):
        await provider.analyze_diff_async(diff="diff text")
    await provider.close()


@pytest.mark.asyncio
@respx.mock
async def test_confidence_normalised_from_0_to_1():
    """Backend returning confidence as 0–1 float should not be divided by 100."""
    response = json.loads(json.dumps(GOOD_RESPONSE))
    response["data"]["confidence"] = 0.92  # already normalised

    respx.post(ENDPOINT).mock(return_value=httpx.Response(200, json=response))

    provider = GitSageAPIProvider(api_key="gs_test_key")
    result = await provider.analyze_diff_async(diff="diff")
    await provider.close()

    assert result.confidence == 0.92


def test_missing_api_key_raises():
    with pytest.raises(AuthenticationError):
        GitSageAPIProvider(api_key="")

    with pytest.raises(AuthenticationError):
        GitSageAPIProvider(api_key="   ")
