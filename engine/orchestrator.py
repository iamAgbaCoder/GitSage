from providers.base import AIProvider
import json
import re

async def generate_full_result_async(diff_summary_content: str, provider: AIProvider, style: str = "conventional") -> tuple[str, str]:
    """
    Highly optimized single-step generation that fetches both
    the commit message and explanation in a single AI round-trip.
    """
    prompt = f"""You are an expert tech lead and software engineer.
Analyze the following git diff and provide:
1. A perfectly structured git commit message in "{style}" style.
2. A concise explanation reviewing the changes.

FORMAT REQUIREMENT:
Your response must be structured as follows:

COMMIT_MESSAGE:
<insert message here>

EXPLANATION:
🧠 What changed:
<bullet points>

💡 Why it matters:
<one liner>

🎯 Scope:
<files/modules affecte using [color]filename[/color] markup if possible>

Diff Context:
{diff_summary_content}
"""
    
    raw_response = await provider.generate_async(prompt)
    
    # Advanced parsing to extract both parts
    try:
        message_match = re.search(r"COMMIT_MESSAGE:(.*?)(?=EXPLANATION:|$)", raw_response, re.DOTALL | re.IGNORECASE)
        explanation_match = re.search(r"EXPLANATION:(.*)", raw_response, re.DOTALL | re.IGNORECASE)
        
        message = message_match.group(1).strip() if message_match else "AI-generated commit"
        explanation = explanation_match.group(1).strip() if explanation_match else "Reviewing changes..."
        
        # Clean up any residual markers
        message = message.replace("COMMIT_MESSAGE:", "").strip()
        explanation = explanation.replace("EXPLANATION:", "").strip()
        
        return message, explanation
    except Exception:
        # Fallback to a naive split if regex fails
        parts = raw_response.split("EXPLANATION:")
        if len(parts) == 2:
            return parts[0].replace("COMMIT_MESSAGE:", "").strip(), parts[1].strip()
        return "Manual Review Required", raw_response
