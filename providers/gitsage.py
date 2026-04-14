"""
GitSage API Backend Provider.

Calls the hosted GitSage intelligence endpoint — returns both commit message
and explanation in a single round-trip, eliminating local LLM dependency.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import httpx

BASE_URL = "https://gitsage-api.up.railway.app"
ANALYZE_ENDPOINT = "/v1/intelligence/analyze"
REQUEST_TIMEOUT = 45.0


@dataclass
class AnalysisResult:
    """Structured response from the GitSage intelligence backend."""

    commit_message: str
    explanation: str
    confidence: float
    provider: str
    model: str
    analysis_time_ms: int


class AuthenticationError(Exception):
    """Raised when the API key is missing, invalid, or revoked."""

    pass


class RateLimitError(Exception):
    """Raised when the API rate limit has been exceeded."""

    pass


class GitSageAPIProvider:
    """
    Async provider that calls the hosted GitSage backend API.

    Single round-trip returns commit_message + explanation + confidence,
    avoiding local model setup and eliminating per-provider prompt engineering.
    """

    def __init__(self, api_key: str):
        if not api_key or not api_key.strip():
            raise AuthenticationError("API key is required.")
        self.api_key = api_key.strip()
        self._client: Optional[httpx.AsyncClient] = None

    def _client_instance(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=BASE_URL,
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": f"gitsage-cli/{_get_version()}",
                },
                timeout=REQUEST_TIMEOUT,
            )
        return self._client

    async def analyze_diff_async(
        self,
        diff: str,
        context: str = "",
        style: str = "conventional",
    ) -> AnalysisResult:
        """
        Send the diff to the backend and return the structured intelligence result.

        Args:
            diff: Raw (already truncated) git diff text.
            context: Optional extra context string sent alongside the diff.
            style: Commit message style — defaults to "conventional".

        Returns:
            AnalysisResult: Parsed intelligence from the backend.

        Raises:
            AuthenticationError: On 401 / invalid key.
            RateLimitError: On 429 with the backend's detailed message.
            RuntimeError: On any other API or network failure.
        """
        client = self._client_instance()
        try:
            response = await client.post(
                ANALYZE_ENDPOINT,
                json={"diff": diff, "context": context, "style": style},
            )
            data = response.json()
        except httpx.TimeoutException:
            raise RuntimeError(
                "Request to GitSage API timed out. "
                "Check your connection or try again in a moment."
            )
        except httpx.NetworkError:
            raise RuntimeError(
                "Could not reach the GitSage API. " "Check your internet connection and try again."
            )
        except Exception as exc:
            raise RuntimeError(f"Unexpected network error: {exc}")

        success = data.get("success", False)
        if not success:
            status_code = data.get("statusCode", response.status_code)
            message = data.get("message", "Unknown error from API.")

            if status_code == 401:
                raise AuthenticationError(
                    "Invalid or expired API key.\n\n"
                    "  • Run [bold cyan]gitsage auth --token <KEY>[/bold cyan] to update your key.\n"
                    "  • Get a free key at [bold cyan]https://gitsage-ai.vercel.app/docs[/bold cyan]"
                )
            if status_code == 429:
                raise RateLimitError(message)
            raise RuntimeError(f"API error {status_code}: {message}")

        result_data = data["data"]
        raw_confidence = result_data.get("confidence", 0)
        # Normalise: backend may return 0–100 or 0–1
        confidence = raw_confidence / 100.0 if raw_confidence > 1 else float(raw_confidence)

        return AnalysisResult(
            commit_message=_clean_commit_message(result_data["commit_message"]),
            explanation=result_data["explanation"],
            confidence=round(min(max(confidence, 0.0), 1.0), 2),
            provider=result_data.get("provider", "gitsage"),
            model=result_data.get("model", "unknown"),
            analysis_time_ms=result_data.get("analysis_time_ms", 0),
        )

    async def close(self):
        """Gracefully close the underlying HTTP connection pool."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


def _clean_commit_message(raw: str) -> str:
    """
    Strip markdown formatting from a commit message returned by the backend.

    The backend occasionally returns messages like:
        **`feat: add thing`**
    or includes the EXPLANATION block in the same field. This extracts
    only the first clean conventional-commit line.
    """
    # Truncate at explanation markers so we never include the body
    for marker in ("**EXPLANATION**", "EXPLANATION:", "🧠", "\n\n"):
        if marker in raw:
            raw = raw.split(marker)[0]

    # Remove markdown bold/italic (**text**, *text*) and inline code (`text`)
    raw = re.sub(r"\*\*(.+?)\*\*", r"\1", raw, flags=re.DOTALL)
    raw = re.sub(r"\*(.+?)\*", r"\1", raw, flags=re.DOTALL)
    raw = re.sub(r"`([^`]+)`", r"\1", raw)

    # Strip stray *, `, and whitespace from the whole string
    raw = raw.strip().strip("`*").strip()

    # Return the first non-empty line
    for line in raw.splitlines():
        line = line.strip().strip("`*").strip()
        if line:
            return line

    return raw.strip()


def _get_version() -> str:
    try:
        from utils import __version__

        return __version__.lstrip("v")
    except Exception:
        return "unknown"
