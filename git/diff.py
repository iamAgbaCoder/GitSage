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
            check=False
        )
        
        if result.returncode != 0 or not result.stdout:
            return None
            
        # Safely decode raw bytes back to utf-8, ignoring CP1252 local charmap errors
        diff_text = result.stdout.decode("utf-8", errors="replace").strip()
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

async def get_staged_diff_async() -> Optional[str]:
    import asyncio
    return await asyncio.to_thread(get_staged_diff)

async def execute_commit_async(message: str) -> bool:
    import asyncio
    return await asyncio.to_thread(execute_commit, message)
