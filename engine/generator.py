from providers.base import AIProvider


def generate_commit_message(
    diff_summary_content: str, provider: AIProvider, style: str = "conventional"
) -> str:
    """
    Generate a high-quality git commit message based on the provided diff.

    Args:
        diff_summary_content (str): The pre-processed and cleaned diff text.
        provider (AIProvider): The configured AI provider (e.g. Gemini).
        style (str): The commit style to follow (e.g. "conventional").

    Returns:
        str: The generated commit message string.
    """
    prompt = f"""You are an expert software engineer generating a perfectly structured git commit message.
    
The commit must follow the "{style}" style.
Only output the commit message string. Do not include quotes, explanations, backticks or any other text.
Max 72 characters if possible.

Diff Summary:
{diff_summary_content}
"""
    return provider.generate(prompt)
