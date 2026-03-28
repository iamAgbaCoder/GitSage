from .models import CommitResult
from .analyzer import parse_diff
from .generator import generate_commit_message
from .explainer import generate_explanation, calculate_confidence
from providers.base import AIProvider
from utils.helpers import truncate_diff

class GitAIEngine:
    def __init__(self, provider: AIProvider, config: dict):
        self.provider = provider
        self.config = config

    async def generate_commit_async(self, raw_diff: str) -> CommitResult:
        if not raw_diff:
            raise ValueError("No staged changes provided.")
            
        truncated_diff = truncate_diff(raw_diff)
        
        from .cache import GitSageCache
        cache = GitSageCache()
        
        # Check cache first
        cached_result = cache.get(truncated_diff)
        if cached_result:
            return cached_result
            
        summary = parse_diff(truncated_diff)
        style = self.config.get("style", "conventional")
        
        from .orchestrator import generate_full_result_async
        from .explainer import calculate_confidence
        
        # Step 1: Single-Round AI Generation (Optimized)
        message, explanation = await generate_full_result_async(
            summary.raw_content, 
            self.provider, 
            style=style
        )
        
        # Step 2: Parallelize confidence calculation
        confidence = calculate_confidence(message, truncated_diff)
        
        result = CommitResult(
            message=message,
            explanation=explanation,
            confidence_score=confidence,
            files_changed=summary.files_changed
        )
        
        # Save to cache
        cache.save(truncated_diff, result)
        
        return result

    def generate_commit(self, raw_diff: str) -> CommitResult:
        import asyncio
        import warnings
        warnings.warn("Use generate_commit_async instead for better performance.", DeprecationWarning)
        return asyncio.run(self.generate_commit_async(raw_diff))
