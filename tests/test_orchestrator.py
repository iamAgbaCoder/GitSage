import pytest
from unittest.mock import AsyncMock
from engine.orchestrator import generate_full_result_async
from providers.base import AIProvider

class MockProvider(AIProvider):
    def generate(self, prompt: str) -> str:
        return ""
    async def generate_async(self, prompt: str) -> str:
        return """
COMMIT_MESSAGE:
feat: Add unit testing

EXPLANATION:
🧠 What changed:
- Added pytest and tests/ directory.

💡 Why it matters:
Ensures codebase stability.

🎯 Scope:
[color]tests/test_cache.py[/color]
"""

@pytest.mark.asyncio
async def test_generate_full_result_async():
    provider = MockProvider()
    diff = "some git diff"
    
    msg, exp = await generate_full_result_async(diff, provider)
    
    assert msg == "feat: Add unit testing"
    assert "🧠 What changed:" in exp
    assert "💡 Why it matters:" in exp
    assert "🎯 Scope:" in exp
