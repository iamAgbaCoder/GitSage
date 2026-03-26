from providers.base import AIProvider

def generate_commit_message(diff_summary_content: str, provider: AIProvider, style: str = "conventional") -> str:
    prompt = f"""You are an expert software engineer generating a perfectly structured git commit message.
    
The commit must follow the "{style}" style.
Only output the commit message string. Do not include quotes, explanations, backticks or any other text.
Max 72 characters if possible.

Diff Summary:
{diff_summary_content}
"""
    return provider.generate(prompt)
