import subprocess
from typing import Optional

def get_staged_diff() -> Optional[str]:
    """Retrieve the staged git diff, ignoring whitespace only changes."""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        # Get staged diff, ignoring whitespace
        result = subprocess.run(
            ["git", "diff", "--cached", "-w"],
            capture_output=True,
            text=True,
            check=True
        )
        diff_text = result.stdout.strip()
        return diff_text if diff_text else None
    except subprocess.CalledProcessError:
        return None
    except FileNotFoundError:
        return None

def execute_commit(message: str) -> bool:
    """Execute the git commit with the given message."""
    try:
        subprocess.run(["git", "commit", "-m", message], check=True)
        return True
    except subprocess.CalledProcessError:
        return False
