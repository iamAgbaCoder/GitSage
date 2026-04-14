# GitSage AI

> AI-powered Git commit assistant — one command, production-quality commits.

GitSage analyses your staged changes and returns a perfectly structured commit message plus a full intelligence report, powered by a hosted backend that makes a single AI round-trip so you never wait for a local model to spin up.

---

## Features

| Feature | Detail |
|---|---|
| **Single-round-trip intelligence** | One API call returns the commit message, explanation, and confidence score together |
| **Secure key storage** | API key lives in `~/.gitsage_auth` with `chmod 600` permissions — never in your repo |
| **Smart diff cache** | Results are cached in `~/.gitsage_cache` by SHA-256(diff) — repeated commits are instant |
| **Sensitive file filtering** | `.env`, `.key`, `credentials`, `secrets`, and similar files are stripped from diffs before any network call |
| **Rich terminal UI** | Confidence bar, colour-coded scope, structured explanation panels |
| **Async by default** | All I/O (git, HTTP, cache) is non-blocking via `asyncio` + `httpx` |
| **Edit mode** | Review and revise the AI suggestion before it's committed |
| **Anonymous telemetry** | Optional, opt-out, fires on a daemon thread — never blocks the CLI |
| **Conventional commits** | Default style; configurable to `simple`, `emoji`, or any custom style |

---

## Quick start

### 1 — Install

```bash
pip install gitsage
```

### 2 — Get an API key

Visit **[https://gitsage-ai.vercel.app/docs](https://gitsage-ai.vercel.app/docs)** to generate a free key.

### 3 — Authenticate

```bash
gitsage auth --token gs_YOUR_KEY_HERE
```

Your key is saved to `~/.gitsage_auth` with restricted file permissions (`600` on Unix).

### 4 — Commit

```bash
git add .
gitsage commit
# or the shorthand
gitsage -c
```

---

## Commands

### `gitsage commit`

Analyses staged changes and opens an interactive prompt:

```
y     — accept and commit
edit  — revise the message before committing
n     — abort
```

### `gitsage auth`

```bash
gitsage auth --token <KEY>   # save / replace API key
gitsage auth                 # show current key status (masked)
gitsage auth --status        # same as above, explicit
gitsage auth --logout        # remove stored key
```

### `gitsage config`

```bash
gitsage config                        # show current preferences
gitsage config --style emoji          # change commit style
gitsage config --no-telemetry         # disable anonymous telemetry
gitsage config --reset                # restore all defaults
```

### `gitsage --version`

Prints the installed version and exits.

---

## Configuration

Preferences are stored in `~/.git-sage.json`. The API key is kept **separately** in `~/.gitsage_auth` and is never written to the preferences file.

| Key | Default | Description |
|---|---|---|
| `style` | `conventional` | Commit message style |
| `auto_commit` | `false` | Skip the interactive prompt |
| `max_length` | `72` | Soft cap on commit message length |
| `telemetry` | `true` | Anonymous usage analytics |

---

## Architecture

```
cli/main.py          — Typer app, auth command, commit workflow, rich UI
│
├── config/loader.py — Preferences (~/.git-sage.json) + secure key (~/.gitsage_auth)
├── git/diff.py      — Staged diff retrieval, sensitive-file filtering, async wrappers
│
├── engine/
│   ├── core.py      — Orchestrator: cache → fast-path (API) or legacy (local)
│   ├── cache.py     — SHA-256 keyed result cache in ~/.gitsage_cache
│   ├── analyzer.py  — Diff parser → DiffSummary (files, intent, cleaned content)
│   ├── models.py    — CommitResult, DiffSummary dataclasses
│   ├── orchestrator.py — Single-prompt generator for local providers
│   ├── explainer.py — Explanation generator + confidence heuristic (local path)
│   └── formatter.py — Output formatting utilities
│
└── providers/
    ├── base.py      — AIProvider ABC (generate / generate_async)
    ├── gitsage.py   — GitSageAPIProvider — async httpx, AnalysisResult, _clean_commit_message
    ├── gemini.py    — Google Gemini (optional, pip install gitsage[gemini])
    └── local.py     — Ollama local provider (optional, pip install gitsage[local])
```

### Request flow

```
gitsage commit
    │
    ├─ git diff --cached          (async subprocess)
    ├─ sensitive-file filter
    ├─ truncate to 3 000 tokens
    ├─ SHA-256 cache lookup       → hit: return immediately
    │
    └─ POST /v1/intelligence/analyze
           X-API-Key: gs_...
           { diff, context, style }
           ↓
       { commit_message, explanation, confidence, provider, model }
           ↓
       _clean_commit_message()    (strip markdown from message)
       cache.save()
       display_result()           (rich panels + confidence bar)
       prompt: y / edit / n
```

---

## Development

```bash
git clone https://github.com/iamAgbaCoder/gitsage
cd gitsage
python -m venv .dev && source .dev/bin/activate   # or .dev\Scripts\activate on Windows
pip install -e ".[dev]"
```

### Run tests

```bash
pytest tests/ -v
```

### Lint & format

```bash
ruff check .
black .
```

### Build

```bash
python -m build
```

---

## Publishing

| Event | Target |
|---|---|
| Push to `main` | TestPyPI (auto) |
| Push to `release` or tag `v*` | PyPI (auto) + GitHub Release |

Trusted Publishing (OIDC) is used — no `PYPI_TOKEN` secret needed. Set up the PyPI and TestPyPI environments in your GitHub repo settings.

---

## License

Apache 2.0 — see [LICENSE](LICENSE).
