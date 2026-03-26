from providers.base import AIProvider

def generate_explanation(commit_message: str, diff_summary_content: str, provider: AIProvider) -> str:
    prompt = f"""You are an expert tech lead reviewing a git commit.
    
Commit Message: {commit_message}

Provide a concise, insightful explanation of this commit. Must include EXACTLY these headers:
🧠 What changed: (Bullet points summarizing changes)
💡 Why it matters: (The impact of this change)
🎯 Scope: (Files/modules affected)

Make it extremely concise and developer-friendly. Do not include markdown asterisks (**text**) for bolding.
Instead, strictly use terminal rich markup colors to signify changes, particularly in the Scope section:
- New files/code: [green]filename[/green]
- Modified files/code: [yellow]filename[/yellow]
- Deleted files/code: [red]filename[/red]

Diff Context:
{diff_summary_content}
"""
    return provider.generate(prompt)

def calculate_confidence(commit_message: str, diff: str) -> float:
    # Basic heuristic scoring
    score = 0.5
    # Conventional commit heuristic
    if ":" in commit_message and len(commit_message.split(":")[0]) < 15:
        score += 0.2
    # Shorter diffs typically yield better summaries
    if len(diff) < 2000:
        score += 0.1
    # Conciseness heuristic
    if len(commit_message) <= 72:
        score += 0.1
        
    return round(min(score, 0.99), 2)
