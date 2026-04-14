"""
GitSage AI Engine — orchestrates diff parsing, provider dispatch, and caching.

When the provider is a GitSageAPIProvider the backend handles generation in a
single round-trip (diff → commit_message + explanation + confidence).  For
legacy local providers (Gemini, Ollama) the existing orchestrator path is kept.
"""

from __future__ import annotations

from providers.base import AIProvider
from utils.helpers import truncate_diff

from .analyzer import parse_diff
from .models import CommitResult


class GitAIEngine:
    """
    Main orchestration engine for AI-powered git commit intelligence.

    Coordinates parsing, provider dispatch, caching, and result assembly.
    """

    def __init__(self, provider: AIProvider, config: dict):
        self.provider = provider
        self.config = config
        # Tests can inject a pre-configured GitSageCache instance here
        self._cache_override = None

    async def generate_commit_async(self, raw_diff: str) -> CommitResult:
        """
        Analyse staged changes and return a full intelligence result.

        Fast path: if the provider exposes `analyze_diff_async` (GitSageAPIProvider)
        the backend returns everything in one call.  Otherwise fall back to the
        local orchestrator (Gemini / Ollama).

        Args:
            raw_diff: Raw text from `git diff --cached`.

        Returns:
            CommitResult with message, explanation, confidence, and files list.
        """
        if not raw_diff:
            raise ValueError("No staged changes provided.")

        truncated = truncate_diff(raw_diff)
        summary = parse_diff(truncated)
        style = self.config.get("style", "conventional")

        from .cache import GitSageCache

        cache = self._cache_override or GitSageCache()
        cached = cache.get(truncated)
        if cached:
            return cached

        # ── Fast path: hosted GitSage backend ──────────────────────────────
        if hasattr(self.provider, "analyze_diff_async"):
            api_result = await self.provider.analyze_diff_async(
                diff=truncated,
                context=summary.intent_summary,
                style=style,
            )
            result = CommitResult(
                message=api_result.commit_message,
                explanation=api_result.explanation,
                confidence_score=api_result.confidence,
                files_changed=summary.files_changed,
            )
        else:
            # ── Legacy path: local provider via orchestrator ────────────────
            from .explainer import calculate_confidence
            from .orchestrator import generate_full_result_async

            message, explanation = await generate_full_result_async(
                summary.raw_content, self.provider, style=style
            )
            confidence = calculate_confidence(message, truncated)
            result = CommitResult(
                message=message,
                explanation=explanation,
                confidence_score=confidence,
                files_changed=summary.files_changed,
            )

        cache.save(truncated, result)
        return result

    def generate_commit(self, raw_diff: str) -> CommitResult:
        """Synchronous wrapper (legacy). Prefer generate_commit_async."""
        import asyncio
        import warnings

        warnings.warn(
            "Use generate_commit_async for better performance.",
            DeprecationWarning,
            stacklevel=2,
        )
        return asyncio.run(self.generate_commit_async(raw_diff))
