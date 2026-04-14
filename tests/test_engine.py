"""Tests for engine.core.GitAIEngine — both fast-path (API) and legacy-path."""

from __future__ import annotations

import pytest

from engine.core import GitAIEngine
from engine.models import CommitResult
from providers.base import AIProvider
from providers.gitsage import AnalysisResult

# ── Helpers ────────────────────────────────────────────────────────────────

SAMPLE_DIFF = "+++ b/tests/mock.py\n+def mock_fn(): pass\n-def old_fn(): pass"


class LegacyMockProvider(AIProvider):
    """Simulates a local (Gemini/Ollama) provider via the orchestrator path."""

    def generate(self, _prompt: str) -> str:
        return (
            "COMMIT_MESSAGE: feat: add mock provider\n"
            "EXPLANATION: 🧠 What changed:\n- Mocked it\n"
            "💡 Why it matters:\nTo test\n🎯 Scope:\ntests"
        )

    async def generate_async(self, _prompt: str) -> str:
        return self.generate(_prompt)


class APIMockProvider:
    """
    Simulates GitSageAPIProvider (has analyze_diff_async, not a subclass of AIProvider).
    Engine detects it via duck-typing (hasattr check).
    """

    async def analyze_diff_async(self, **_kwargs) -> AnalysisResult:
        return AnalysisResult(
            commit_message="feat: backend api result",
            explanation="🧠 What changed:\n- API returned this\n"
            "💡 Why it matters:\nSpeed\n🎯 Scope:\nmock.py",
            confidence=0.92,
            provider="gitsage",
            model="gpt-4o",
            analysis_time_ms=120,
        )

    async def close(self):
        pass


# ── Legacy provider tests ──────────────────────────────────────────────────


def test_engine_generate_commit_sync_legacy(tmp_path):
    provider = LegacyMockProvider()
    engine = GitAIEngine(provider, config={})
    # Override cache path so test doesn't pollute home dir
    engine._cache_path = tmp_path / ".cache"

    # result = engine.generate_commit(SAMPLE_DIFF)
    result = engine.generate_commit(SAMPLE_DIFF)

    assert isinstance(result, CommitResult)
    assert result.message == "feat: add mock provider"
    assert "What changed:" in result.explanation
    assert result.confidence_score > 0


@pytest.mark.asyncio
async def test_engine_generate_commit_async_legacy(tmp_path):
    provider = LegacyMockProvider()
    engine = GitAIEngine(provider, config={})

    from engine.cache import GitSageCache

    engine._cache_override = GitSageCache(cache_path=tmp_path / ".cache")

    result = await engine.generate_commit_async(SAMPLE_DIFF)

    assert isinstance(result, CommitResult)
    assert result.message == "feat: add mock provider"
    assert result.confidence_score >= 0.5


# ── API provider (fast-path) tests ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_engine_uses_api_fast_path(tmp_path):
    provider = APIMockProvider()
    engine = GitAIEngine(provider, config={"style": "conventional"})

    from engine.cache import GitSageCache

    engine._cache_override = GitSageCache(cache_path=tmp_path / ".cache")

    result = await engine.generate_commit_async(SAMPLE_DIFF)

    assert isinstance(result, CommitResult)
    assert result.message == "feat: backend api result"
    assert result.confidence_score == 0.92


@pytest.mark.asyncio
async def test_engine_returns_cached_result(tmp_path):
    cache_path = tmp_path / ".cache"

    from engine.cache import GitSageCache

    # Pre-populate cache
    cache = GitSageCache(cache_path=cache_path)
    cached = CommitResult(
        message="feat: from cache",
        explanation="cached explanation",
        confidence_score=0.88,
        files_changed=["cached.py"],
    )
    from utils.helpers import truncate_diff

    cache.save(truncate_diff(SAMPLE_DIFF), cached)

    provider = APIMockProvider()
    engine = GitAIEngine(provider, config={})
    engine._cache_override = cache

    result = await engine.generate_commit_async(SAMPLE_DIFF)

    # Must come from cache, not the provider
    assert result.message == "feat: from cache"
    assert result.confidence_score == 0.88


def test_engine_raises_on_empty_diff():
    provider = LegacyMockProvider()
    engine = GitAIEngine(provider, config={})

    with pytest.raises(ValueError, match="No staged changes"):
        import asyncio

        asyncio.run(engine.generate_commit_async(""))
