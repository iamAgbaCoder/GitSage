from .models import DiffSummary


def parse_diff(raw_diff: str) -> DiffSummary:
    """
    Parse a raw git diff and extract meaningful structural components.

    Transforms the raw diff text into a structured DiffSummary containing
    the list of affected files, a human-readable intent summary, and
    cleaned-up content for AI consumption.

    Args:
        raw_diff (str): The raw output from a git diff command.

    Returns:
        DiffSummary: A structured object containing the meta info and filtered diff content.
    """
    files_changed = []
    cleaned_lines = []

    for line in raw_diff.splitlines():
        if line.startswith("+++ b/"):
            files_changed.append(line[6:])

        if line.startswith("Index:") or line.startswith("================"):
            continue
        if len(line.strip()) == 0:
            continue

        cleaned_lines.append(line)

    cleaned_content = "\n".join(cleaned_lines)

    intent_summary = ""
    if files_changed:
        intent_summary = "Modified " + ", ".join(files_changed[:3])
        if len(files_changed) > 3:
            intent_summary += f" and {len(files_changed) - 3} others"

    return DiffSummary(
        files_changed=files_changed,
        intent_summary=intent_summary,
        raw_content=cleaned_content,
    )
