# GitSage - Git Commit AI Assistant

A production-grade CLI tool backed by a reusable intelligence engine that generates conventional commit messages with deep explanations.

## Setup

1. Clone repository
2. Run `pip install -e .`
3. Export your Gemini API Key:
   ```bash
   export GEMINI_API_KEY="your-api-key"
   ```

## Usage

```bash
git add .
gitsage commit
# Or use the shortcut
gitsage -c
```

## Configuration

Settings are automatically saved and loaded from `~/.git-sage.json`. Example minimal config:

```json
{
  "ai_provider": "gemini",
  "auto_commit": false,
  "max_length": 72,
  "style": "conventional"
}
```

Providers supported:
- `"gemini"` (default, requires `GEMINI_API_KEY`)
- `"local"` (fallback via Ollama, uses local models)

## Architecture

At its core, GitSage focuses on a pristine **Git Intelligence Engine** separated from its UI. This means the intelligence layer can easily be dropped into git hooks, VS Code extensions, or serverless functions.
