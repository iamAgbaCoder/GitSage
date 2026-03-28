import subprocess
from typing import Optional

def get_staged_diff() -> Optional[str]:
    """
    Retrieve the staged git diff, ignoring whitespace-only changes and sensitive files.
    """
    import re
    # Patterns for sensitive files that should NEVER be sent to the AI
    SENSITIVE_PATTERNS = [
        r"\.env$", r"\.key$", r"\.pem$", r"id_rsa", r"secrets", r"config\.json$",
        r"credentials", r"token", r"api_key"
    ]
    
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        # Get staged diff, ignoring whitespace
        result = subprocess.run(
            ["git", "diff", "--cached", "-w"],
            capture_output=True,
            check=False
        )
        
        if result.returncode != 0 or not result.stdout:
            return None
            
        # Safely decode raw bytes back to utf-8, ignoring CP1252 local charmap errors
        raw_diff = result.stdout.decode("utf-8", errors="replace").strip()
        
        if not raw_diff:
            return None
            
        # Filter out sensitive files from the diff
        filtered_lines = []
        skip_current_file = False
        
        for line in raw_diff.splitlines():
            # If we encounter a new file header
            if line.startswith("diff --git"):
                # Check if the filename matches any sensitive pattern
                skip_current_file = any(re.search(p, line, re.IGNORECASE) for p in SENSITIVE_PATTERNS)
            
            if not skip_current_file:
                filtered_lines.append(line)
        
        diff_text = "\n".join(filtered_lines).strip()
        return diff_text if diff_text else None
    except Exception:
        return None

def execute_commit(message: str) -> bool:
    """Execute the git commit with the given message."""
    try:
        subprocess.run(["git", "commit", "-m", message], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

async def get_staged_diff_async() -> Optional[str]:
    import asyncio
    return await asyncio.to_thread(get_staged_diff)

async def execute_commit_async(message: str) -> bool:
    import asyncio
    return await asyncio.to_thread(execute_commit, message)
