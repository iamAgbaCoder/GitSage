from engine.core import GitAIEngine
from engine.models import CommitResult
from providers.base import AIProvider


class MockProvider(AIProvider):
    def generate(self, prompt: str) -> str:
        return "COMMIT_MESSAGE: feat: add mock provider\nEXPLANATION: 🧠 What changed: Mocked it\n💡 Why it matters: To test\n🎯 Scope: tests"

    async def generate_async(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(self.generate, prompt)


def test_engine_generate_commit():
    provider = MockProvider()
    engine = GitAIEngine(provider, config={})

    mock_diff = "+++ b/tests/mock.py\n+def mock_fn(): pass"

    result = engine.generate_commit(mock_diff)

    assert isinstance(result, CommitResult)
    assert result.message == "feat: add mock provider"
    assert "What changed:" in result.explanation
    assert result.confidence_score > 0
