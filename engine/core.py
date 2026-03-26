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

    def generate_commit(self, raw_diff: str) -> CommitResult:
        if not raw_diff:
            raise ValueError("No diff provided.")
            
        truncated_diff = truncate_diff(raw_diff)
        summary = parse_diff(truncated_diff)
        
        style = self.config.get("style", "conventional")
        
        # Step 1: Generate commit message
        message = generate_commit_message(summary.raw_content, self.provider, style=style)
        
        # Step 2: Generate explanation
        explanation = generate_explanation(message, summary.raw_content, self.provider)
        
        # Step 3: Confidence Score
        confidence = calculate_confidence(message, truncated_diff)
        
        return CommitResult(
            message=message,
            explanation=explanation,
            confidence_score=confidence
        )
