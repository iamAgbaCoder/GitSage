"""
GitSage CLI - AI-Powered Git Commit Assistant.

Commands
--------
  gitsage commit        Analyse staged changes and generate a commit message.
  gitsage auth          Manage your GitSage API key.
  gitsage config        Manage local preferences (style, telemetry, etc.).
"""

from __future__ import annotations

import asyncio
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from config.loader import delete_api_key, load_api_key, load_config, save_api_key
from config.remote import get_remote_config
from utils import __version__
from utils.telemetry import track_event

load_dotenv()

_REMOTE = get_remote_config()
_FRONTEND = _REMOTE.get("frontend_base_url", "https://gitsage-ai.vercel.app").rstrip("/")

app = typer.Typer(
    help=f"GitSage — AI-Powered Git Commit Assistant • {__version__} • {_FRONTEND}",
    add_completion=False,
)
console = Console()

LOGO = rf"""[bold cyan]
   ______ _ __  _____
  / ____/(_) /_/ ___/ ____ _ ____ _ ___
 / / __ / / __/\__ \ / __ `// __ `// _ \\
/ /_/ // / /_ ___/ // /_/ // /_/ //  __/
\____//_/\__//____/ \__,_/ \__, / \___/
                          /____/        [/bold cyan]
 [dim]AI-Powered Commit Intelligence • {__version__}[/dim]
"""


def _get_no_key_message() -> str:
    return (
        "No GitSage API key found.\n\n"
        f"  1. Get a free key at [bold cyan]{_FRONTEND}/docs[/bold cyan]\n"
        "  2. Authenticate with:  [bold white]gitsage auth --token <KEY>[/bold white]\n\n"
        "[dim]Your key is stored in [bold]~/.gitsage_auth[/bold] with restricted "
        "file permissions so only your user account can read it.[/dim]"
    )


# ── Helpers ────────────────────────────────────────────────────────────────


def version_callback(value: bool):
    if value:
        Console().print(f"[bold cyan]GitSage[/bold cyan] [dim]{__version__}[/dim]")
        raise typer.Exit()


def show_error(message: str, title: str = "Error"):
    console.print(
        Panel(
            f"[bold red]{message}[/bold red]",
            title=f"[bold red]{title}[/bold red]",
            border_style="red",
            expand=False,
            padding=(1, 2),
        )
    )
    raise typer.Exit(1)


def _build_provider():
    """
    Resolve the GitSage API key and return a ready GitSageAPIProvider.

    If no key is stored, print a friendly onboarding panel and exit 1.
    """
    from providers.gitsage import AuthenticationError, GitSageAPIProvider

    api_key = load_api_key()
    if not api_key:
        console.print(
            Panel(
                _get_no_key_message(),
                title="[bold yellow]Authentication Required[/bold yellow]",
                border_style="yellow",
                expand=False,
                padding=(1, 2),
            )
        )
        raise typer.Exit(1)

    try:
        return GitSageAPIProvider(api_key=api_key)
    except AuthenticationError as exc:
        show_error(str(exc), title="Authentication Error")


def display_result(result):
    """Render the intelligence report to the terminal."""
    console.print()

    files_count = len(result.files_changed)
    files_plural = "file" if files_count == 1 else "files"

    console.print(
        Panel(
            Text(result.message, style="bold cyan"),
            title="[bold blue]🚀 GitSage Suggestion[/bold blue]",
            subtitle=f"[dim blue]{files_count} {files_plural} affected[/dim blue]",
            border_style="blue",
            padding=(1, 2),
        )
    )

    console.print("\n[bold magenta]🧠 Intelligence Engine Report[/bold magenta]")
    console.print(f"[dim]{'━' * console.width}[/dim]")

    explanation_text = result.explanation.replace("**", "").strip()
    for line in explanation_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if "🧠 What changed:" in line:
            console.print("\n[bold cyan]• WHAT CHANGED[/bold cyan]")
        elif "💡 Why it matters:" in line:
            console.print("\n[bold yellow]• WHY IT MATTERS[/bold yellow]")
        elif "🎯 Scope:" in line:
            console.print("\n[bold magenta]• REACH & SCOPE[/bold magenta]")
        elif line.startswith(("*", "-")):
            console.print(f"  [dim]↳[/dim] {escape(line.lstrip('*- ').strip())}")
        else:
            if line.endswith(":") and any(
                h in line.lower() for h in ["changed", "matters", "scope"]
            ):
                console.print(f"\n[bold]{escape(line.upper())}[/bold]")
            else:
                console.print(f"  {escape(line)}")

    console.print(f"\n[dim]{'━' * console.width}[/dim]")

    conf_value = int(result.confidence_score * 100)
    conf_color = "green" if conf_value >= 80 else "yellow" if conf_value >= 50 else "red"
    bar_length = 30
    filled = int(bar_length * result.confidence_score)
    bar = (
        f"[{conf_color}]{'█' * filled}[/{conf_color}]"
        f"[dim grey]{'░' * (bar_length - filled)}[/dim grey]"
    )
    status_text = "TRUSTED" if conf_value >= 80 else "MODERATE" if conf_value >= 50 else "LOW"
    console.print(
        f"\n [bold white]Intelligence Confidence:[/bold white] {bar} "
        f"[{conf_color}]● {conf_value}% ({status_text})[/{conf_color}]\n"
    )


# ── Commands ───────────────────────────────────────────────────────────────


@app.command(name="auth", help="Save or remove your GitSage API key.")
def auth_cmd(
    token: Optional[str] = typer.Option(
        None,
        "--token",
        "-t",
        help=f"Your GitSage API key (get one at {_FRONTEND}/docs).",
    ),
    logout: bool = typer.Option(
        False,
        "--logout",
        help="Remove the stored API key.",
    ),
    status: bool = typer.Option(
        False,
        "--status",
        "-s",
        help="Show whether an API key is currently stored.",
    ),
):
    """Manage the GitSage API key stored in ~/.gitsage_auth."""
    if logout:
        delete_api_key()
        console.print("[bold green]✔ API key removed.[/bold green]")
        return

    if status:
        key = load_api_key()
        if key:
            masked = key[:6] + "..." + key[-4:]
            console.print(f"[bold green]✔ API key stored:[/bold green] [dim]{masked}[/dim]")
        else:
            console.print(
                "[bold yellow]⚠  No API key stored.[/bold yellow]  "
                "Run [bold cyan]gitsage auth --token <KEY>[/bold cyan] to add one."
            )
        return

    if not token:
        # No --token flag — if a key is already saved, just show its status
        existing = load_api_key()
        if existing:
            masked = existing[:6] + "..." + existing[-4:]
            console.print(
                Panel(
                    f"[bold green]✔ API key is active:[/bold green] [dim]{masked}[/dim]\n\n"
                    "  • [bold cyan]gitsage auth --token <KEY>[/bold cyan]  — replace key\n"
                    "  • [bold cyan]gitsage auth --logout[/bold cyan]         — remove key",
                    title="[bold green]Authenticated[/bold green]",
                    border_style="green",
                    expand=False,
                    padding=(1, 2),
                )
            )
            return

        # No key stored — walk the user through setup
        console.print(
            Panel(
                _get_no_key_message(),
                title="[bold yellow]Authentication Setup[/bold yellow]",
                border_style="yellow",
                expand=False,
                padding=(1, 2),
            )
        )
        token = typer.prompt("Paste your API key", hide_input=True).strip()
        if not token:
            show_error("No API key provided. Authentication cancelled.")

    save_api_key(token)
    console.print(
        Panel(
            "[bold green]✔ API key saved successfully![/bold green]\n\n"
            "  Your key is stored in [bold]~/.gitsage_auth[/bold] with "
            "restricted permissions.\n"
            "  Run [bold cyan]gitsage commit[/bold cyan] to generate your first AI commit.",
            title="[bold green]Authenticated[/bold green]",
            border_style="green",
            expand=False,
            padding=(1, 2),
        )
    )
    config = load_config()
    track_event("auth_success", config)


@app.command(name="commit", help="Analyse staged changes and generate a commit message.")
def commit_sync():
    """Entry-point that runs the async commit workflow in a synchronous context."""
    asyncio.run(_commit())


async def _commit():
    """Core async commit workflow."""
    from engine.core import GitAIEngine
    from git.diff import execute_commit_async, get_staged_diff_async
    from providers.gitsage import AuthenticationError, RateLimitError

    config = load_config()
    provider = _build_provider()
    engine = GitAIEngine(provider=provider, config=config)

    with console.status(
        "[bold cyan]🔍 Analysing staged changes...[/bold cyan]",
        spinner="dots12",
        spinner_style="bold cyan",
    ):
        diff = await get_staged_diff_async()

    if not diff:
        console.print(
            Panel(
                "[bold yellow]⚠️  No staged changes found.[/bold yellow]\n"
                "[dim]Use [bold]git add <file>[/bold] to stage changes first.[/dim]",
                border_style="yellow",
                expand=False,
                padding=(1, 2),
            )
        )
        raise typer.Exit(0)

    with console.status(
        "[bold magenta]🧠 Generating intelligence...[/bold magenta]",
        spinner="dots12",
        spinner_style="bold magenta",
    ):
        try:
            result = await engine.generate_commit_async(diff)
        except AuthenticationError as exc:
            console.print(
                Panel(
                    str(exc),
                    title="[bold red]Authentication Error[/bold red]",
                    border_style="red",
                    expand=False,
                    padding=(1, 2),
                )
            )
            raise typer.Exit(1)
        except RateLimitError as exc:
            console.print(
                Panel(
                    f"[bold yellow]{exc}[/bold yellow]\n\n"
                    f"[dim]You have hit the rate limit on your current plan.\n"
                    f"Upgrade at [bold cyan]{_FRONTEND}/docs[/bold cyan][/dim]",
                    title="[bold yellow]Rate Limit Exceeded[/bold yellow]",
                    border_style="yellow",
                    expand=False,
                    padding=(1, 2),
                )
            )
            raise typer.Exit(1)
        except Exception as exc:
            show_error(str(exc), title="Engine Error")

    display_result(result)

    action = (
        Prompt.ask(
            "\n[bold yellow]Ready to commit?[/bold yellow]",
            choices=["y", "n", "edit"],
            default="y",
        )
        .strip()
        .lower()
    )

    if action == "y":
        with console.status("[dim]Creating commit...[/dim]", spinner="simpleDots"):
            success = await execute_commit_async(result.message)
        if success:
            console.print("\n[bold green]✔ Commit created successfully![/bold green] 🚀")
            console.print("[dim]Use 'git push' to share your changes.[/dim]\n")
            track_event("commit_success", config)
        else:
            show_error("Git failed to execute the commit.", title="Git Error")

    elif action == "edit":
        console.print("\n[bold cyan]✎ Edit Mode[/bold cyan]")
        edited = typer.prompt("Revised message", default=result.message)
        if not edited:
            console.print("[yellow]Empty message. Commit aborted.[/yellow]")
            return
        with console.status("[dim]Creating commit...[/dim]", spinner="simpleDots"):
            success = await execute_commit_async(edited)
        if success:
            console.print("\n[bold green]✔ Commit created successfully![/bold green] 🚀")
        else:
            show_error("Git failed to execute the commit.", title="Git Error")
    else:
        console.print("\n[dim]✖ Commit aborted.[/dim]\n")

    await provider.close()


@app.command(name="explain", help="Explain the staged changes.")
def explain_sync():
    """Entry-point that runs the async explain workflow in a synchronous context."""
    asyncio.run(_explain())


async def _explain():
    """Core async explain workflow."""
    from git.diff import get_staged_diff_async
    from providers.gitsage import AuthenticationError, RateLimitError

    config = load_config()
    provider = _build_provider()

    with console.status(
        "[bold cyan]🔍 Analysing staged changes...[/bold cyan]",
        spinner="dots12",
        spinner_style="bold cyan",
    ):
        diff = await get_staged_diff_async()

    if not diff:
        console.print(
            Panel(
                "[bold yellow]⚠️  No staged changes found.[/bold yellow]\n"
                "[dim]Use [bold]git add <file>[/bold] to stage changes first.[/dim]",
                border_style="yellow",
                expand=False,
                padding=(1, 2),
            )
        )
        raise typer.Exit(0)

    with console.status(
        "[bold magenta]🧠 Generating explanation...[/bold magenta]",
        spinner="dots12",
        spinner_style="bold magenta",
    ):
        try:
            result = await provider.explain_diff_async(diff)
        except AuthenticationError as exc:
            console.print(
                Panel(
                    str(exc),
                    title="[bold red]Authentication Error[/bold red]",
                    border_style="red",
                    expand=False,
                    padding=(1, 2),
                )
            )
            raise typer.Exit(1)
        except RateLimitError as exc:
            console.print(
                Panel(
                    f"[bold yellow]{exc}[/bold yellow]\n\n"
                    f"[dim]You have hit the rate limit on your current plan.\n"
                    f"Upgrade at [bold cyan]{_FRONTEND}/docs[/bold cyan][/dim]",
                    title="[bold yellow]Rate Limit Exceeded[/bold yellow]",
                    border_style="yellow",
                    expand=False,
                    padding=(1, 2),
                )
            )
            raise typer.Exit(1)
        except Exception as exc:
            show_error(str(exc), title="Engine Error")

    track_event("explain_success", config)

    console.print("\n[bold magenta]🧠 Intelligence Explanation[/bold magenta]")
    console.print(f"[dim]{'━' * console.width}[/dim]")

    if result.get("what_changed"):
        console.print("\n[bold cyan]• WHAT CHANGED[/bold cyan]")
        console.print(f"  {escape(result.get('what_changed'))}")

    if result.get("why_it_matters"):
        console.print("\n[bold yellow]• WHY IT MATTERS[/bold yellow]")
        console.print(f"  {escape(result.get('why_it_matters'))}")

    if result.get("reach_scope"):
        console.print("\n[bold magenta]• REACH & SCOPE[/bold magenta]")
        console.print(f"  {escape(result.get('reach_scope'))}")

    if result.get("impact_level"):
        console.print(
            f"\n[bold white]Impact Level:[/bold white] {escape(result.get('impact_level'))}\n"
        )

    await provider.close()


@app.command(name="config", help="Manage GitSage preferences (style, telemetry, etc.).")
def config_cmd(
    style: Optional[str] = typer.Option(
        None, "--style", help="Commit message style (conventional, simple, emoji)."
    ),
    telemetry: Optional[bool] = typer.Option(
        None,
        "--telemetry/--no-telemetry",
        help="Enable or disable anonymous usage tracking.",
    ),
    reset: bool = typer.Option(False, "--reset", help="Reset preferences to defaults."),
):
    """Manage the local GitSage preferences file."""
    from config.loader import DEFAULT_CONFIG, load_config, save_config

    config = load_config()

    if reset:
        save_config(DEFAULT_CONFIG)
        console.print("[bold green]✔ Configuration reset to defaults.[/bold green]")
        return

    updated = False
    if style:
        config["style"] = style.lower()
        updated = True
        console.print(f"[bold green]✔ Commit style set to:[/bold green] {style}")
    if telemetry is not None:
        config["telemetry"] = telemetry
        updated = True
        label = "enabled" if telemetry else "disabled"
        console.print(f"[bold green]✔ Anonymous telemetry {label}.[/bold green]")

    if updated:
        save_config(config)
    else:
        console.print("\n[bold cyan]GitSage Preferences[/bold cyan]")
        console.print(f"[dim]{'━' * 30}[/dim]")
        key_stored = "✔ stored" if load_api_key() else "✖ not set"
        console.print(f"[bold white]{'api_key':15}:[/bold white] {key_stored}")
        for k, v in config.items():
            if k == "anonymous_id":
                continue
            console.print(f"[bold white]{k:15}:[/bold white] {v}")
        console.print(f"[dim]{'━' * 30}[/dim]")
        console.print("[dim]Use 'gitsage config --help' to see available options.[/dim]\n")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    c: bool = typer.Option(
        False,
        "--commit",
        "-c",
        help="Shorthand for 'gitsage commit'.",
    ),
    e: bool = typer.Option(
        False,
        "--explain",
        "-e",
        help="Shorthand for 'gitsage explain'.",
    ),
    _version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
):
    # Fetch and handle remote configuration on CLI startup
    get_remote_config()

    if ctx.invoked_subcommand is None:
        if c:
            asyncio.run(_commit())
        elif e:
            asyncio.run(_explain())
        else:
            config = load_config()
            track_event("app_start", config)
            console.print(LOGO)
            console.print(ctx.get_help())


if __name__ == "__main__":
    app()
