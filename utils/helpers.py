def truncate_diff(diff: str, max_tokens: int = 3000) -> str:
    """A naive way to limit the size of diff so it doesn't break AI context window."""
    max_chars = max_tokens * 4
    if len(diff) <= max_chars:
        return diff
    return diff[:max_chars] + "\n\n...[DIFF TRUNCATED]..."
