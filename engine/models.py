from dataclasses import dataclass
from typing import List

@dataclass
class DiffSummary:
    files_changed: List[str]
    intent_summary: str
    raw_content: str

@dataclass
class CommitResult:
    message: str
    explanation: str
    confidence_score: float
    files_changed: List[str]
