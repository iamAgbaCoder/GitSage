from .models import CommitResult
from .analyzer import parse_diff
from .generator import generate_commit_message
from .explainer import generate_explanation, calculate_confidence
from providers.base import AIProvider
from utils.helpers import truncate_diff

class GitAIEngine:
    """
    Main orchestration engine for AI-powered git commit intelligence.
    
    Coordinates the parse, analyze, generate, and calculate phases of the intelligence pipeline.
    """
    def __init__(self, provider: AIProvider, config: dict):
        """
        Initialize the Git Sage AI engine.
        
        Args:
            provider (AIProvider): The intelligence provider (e.g. Gemini, Local/Ollama).
            config (dict): The configuration settings (e.g. style, filters).
        """
        self.provider = provider
        self.config = config

    async def generate_commit_async(self, raw_diff: str) -> CommitResult:
        """
        Analyze the staged changes asynchronously and generate a full intelligence report.
        
        This method checks the local cache first before performing any AI operations.
        It uses the single-step orchestrator for optimized performance.
        
        Args:
            raw_diff (str): The raw text of the git diff to analyze.
            
        Returns:
            CommitResult: A structured data object containing the commit message,
                        the explanation report, confidence score, and meta info.
                        
        Raises:
            ValueError: If no staged changes are provided.
        """
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
        """
        Synchronous wrapper for commit generation (Legacy).
        
        Note: Use generate_commit_async instead for better performance and non-blocking I/O.
        """
        import asyncio
        import warnings
        warnings.warn("Use generate_commit_async instead for better performance.", DeprecationWarning)
        return asyncio.run(self.generate_commit_async(raw_diff))
