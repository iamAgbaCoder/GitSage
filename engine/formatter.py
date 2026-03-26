def format_output(message: str, explanation: str, confidence: float) -> str:
    return f"""\
Suggested commit: {message}

Explanation:
{explanation}

Confidence: {confidence:.2f}"""
