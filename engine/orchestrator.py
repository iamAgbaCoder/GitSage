from providers.base import AIProvider
import re


async def generate_full_result_async(
    diff_summary_content: str, provider: AIProvider, style: str = "conventional"
) -> tuple[str, str]:
    """
    Highly optimized single-step generation that fetches both the commit message
    and detailed explanation in a single AI round-trip.

    This drastically reduces latency by minimizing the number of distinct API requests
    sent to the underlying AI provider.

    Args:
        diff_summary_content (str): The pre-processed git diff content.
        provider (AIProvider): The configured AI provider instance.
        style (str): The desired commit style (default: "conventional").

    Returns:
        tuple[str, str]: A tuple containing (commit_message, explanation).

    Note:
        The function uses robust regex parsing to separate the commitment message
        from the explanation block in the AI's single response.
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
        # Use more comprehensive regex that handles potential variations in the AI output
        message_match = re.search(
            r"(?:COMMIT_MESSAGE|COMMIT MESSAGE):?\s*(.*?)(?=(?:EXPLANATION|EXPLAINED|WHY IT MATTERS):|$)",
            raw_response,
            re.DOTALL | re.IGNORECASE,
        )
        explanation_match = re.search(
            r"(?:EXPLANATION|EXPLAINED):?\s*(.*)",
            raw_response,
            re.DOTALL | re.IGNORECASE,
        )

        message = message_match.group(1).strip() if message_match else None
        explanation = explanation_match.group(1).strip() if explanation_match else None

        # Fallback to naive split if regex fails
        if not message or not explanation:
            # Try splitting by common markers
            for marker in ["EXPLANATION:", "EXPLANATION", "WHY IT MATTERS:"]:
                if marker in raw_response:
                    parts = raw_response.split(marker)
                    message = (
                        parts[0]
                        .replace("COMMIT_MESSAGE:", "")
                        .replace("COMMIT_MESSAGE", "")
                        .strip()
                    )
                    explanation = parts[1].strip()
                    break

        # Final defaults if all else fails
        return message or "AI-generated commit", explanation or "Reviewing changes..."
    except Exception:
        # Fallback to a naive split if regex fails
        parts = raw_response.split("EXPLANATION:")
        if len(parts) == 2:
            return parts[0].replace("COMMIT_MESSAGE:", "").strip(), parts[1].strip()
        return "Manual Review Required", raw_response
