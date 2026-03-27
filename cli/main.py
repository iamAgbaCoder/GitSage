import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

from config.loader import load_config
from engine.core import GitAIEngine
from git.diff import get_staged_diff_async, execute_commit_async
from providers.gemini import GeminiProvider
from providers.local import LocalProvider
from providers.base import AIProvider

app = typer.Typer(
    help="GitSage - Git Commit AI Assistant (Git Intelligence Layer)",
    add_completion=False,
)
console = Console()

LOGO = r"""[bold cyan]
   ______ _ __  _____                  
  / ____/(_) /_/ ___/ ____ _ ____ _ ___ 
 / / __ / / __/\__ \ / __ `// __ `// _ \\
/ /_/ // / /_ ___/ // /_/ // /_/ //  __/
\____//_/\__//____/ \__,_/ \__, / \___/ 
                          /____/        [/bold cyan]
 [dim]AI-Powered Commit Intelligence • v1.0.0[/dim]
"""


def show_error(message: str, title: str = "Error"):
    console.print(
        Panel(
            f"[bold red]❌ {message}[/bold red]",
            title=f"[bold red]{title}[/bold red]",
            border_style="red",
            expand=False,
            padding=(1, 2),
        )
    )
    raise typer.Exit(1)


def get_provider(config: dict) -> AIProvider:
    provider_name = config.get("ai_provider", "gemini").lower()
    if provider_name == "gemini":
        try:
            return GeminiProvider(api_key=config.get("api_key"))
        except ValueError:
            console.print(
                Panel(
                    "GitSage Intelligence Engine API Key is required but not found.",
                    border_style="yellow",
                    expand=False,
                )
            )
            api_key = typer.prompt(
                "Please enter your Intelligence Engine API Key", hide_input=True
            )
            if not api_key:
                show_error("API Key is required to connect to the intelligence engine.")

            # Save it explicitly mapped back to user config
            config["api_key"] = api_key
            from config.loader import save_config

            save_config(config)

            return GeminiProvider(api_key=api_key)
        except ImportError as e:
            show_error(f"{e}", title="Dependency Error")
    elif provider_name == "local":
        return LocalProvider()
    else:
        show_error(f"Unknown provider '{provider_name}'.")


def display_result(result):
    console.print()

    # Files summary for meta info
    files_count = len(result.files_changed)
    files_plural = "file" if files_count == 1 else "files"

    # 1. Suggested Commit Panel

    commit_panel = Panel(
        Text(result.message, style="bold cyan"),
        title="[bold blue]🚀 GitSage Suggestion[/bold blue]",
        subtitle=f"[dim blue]{files_count} {files_plural} affected[/dim blue]",
        border_style="blue",
        padding=(1, 2),
    )
    console.print(commit_panel)

    # 2. Intelligence Section
    console.print("\n[bold magenta]🧠 Intelligence Engine Report[/bold magenta]")
    console.print(f"[dim]{'━' * console.width}[/dim]")

    explanation_text = result.explanation.replace("**", "").strip()

    for line in explanation_text.split("\n"):
        line = line.strip()
        if not line:
            continue

        if "🧠 What changed:" in line:
            console.print(f"\n[bold cyan]• WHAT CHANGED[/bold cyan]")
        elif "💡 Why it matters:" in line:
            console.print(f"\n[bold yellow]• WHY IT MATTERS[/bold yellow]")
        elif "🎯 Scope:" in line:
            console.print(f"\n[bold magenta]• REACH & SCOPE[/bold magenta]")
        elif line.startswith("*") or line.startswith("-"):
            # Clean up the bullet and content
            content = line.lstrip("*- ").strip()
            console.print(f"  [dim]↳[/dim] {content}")
        else:
            # Handle AI-generated headers if it missed emojis
            if line.endswith(":") and any(
                h in line.lower() for h in ["changed", "matters", "scope"]
            ):
                console.print(f"\n[bold]{line.upper()}[/bold]")
            else:
                console.print(f"  {line}")

    console.print(f"\n[dim]{'━' * console.width}[/dim]")

    # 3. Confidence Score Bar (Redesigned for Premium Look)
    conf_value = int(result.confidence_score * 100)
    conf_color = (
        "green" if conf_value >= 80 else "yellow" if conf_value >= 50 else "red"
    )

    bar_length = 30
    filled = int(bar_length * result.confidence_score)
    empty = bar_length - filled

    # Use a more high-end bar design
    bar = (
        f"[{conf_color}]{'█' * filled}[/{conf_color}][dim grey]{'░' * empty}[/dim grey]"
    )

    indicator = "●"
    status_text = (
        "TRUSTED" if conf_value >= 80 else "MODERATE" if conf_value >= 50 else "LOW"
    )

    console.print(
        f"\n [bold white]Intelligence Confidence:[/bold white] {bar} [{conf_color}]{indicator} {conf_value}% ({status_text})[/{conf_color}]\n"
    )


@app.command(
    name="commit", help="Analyze staged changes and generate a commit message."
)
def commit_sync():
    import asyncio

    asyncio.run(commit())


async def commit():
    # Hide logo from normal output as requested
    config = load_config()
    provider = get_provider(config)
    engine = GitAIEngine(provider=provider, config=config)

    from git.diff import get_staged_diff_async, execute_commit_async

    with console.status(
        "[bold cyan]🔍 Analyzing staged changes...[/bold cyan]",
        spinner="dots12",
        spinner_style="bold cyan",
    ):
        diff = await get_staged_diff_async()

    if not diff:
        console.print(
            Panel(
                "[bold yellow]⚠️ No staged changes found.[/bold yellow]\n[dim]Use 'git add <file>' to stage changes before running GitSage.[/dim]",
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
        except Exception as e:
            show_error(str(e), title="Engine Error")

    display_result(result)

    # Interactive Prompt
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
            console.print(
                "\n[bold green]✔ Commit created successfully![/bold green] 🚀"
            )
            console.print("[dim]Use 'git push' to share your changes.[/dim]\n")
        else:
            show_error("Git failed to execute the commit command.", title="Git Error")

    elif action == "edit":
        console.print("\n[bold cyan]✎ Entering Edit Mode[/bold cyan]")
        edited_message = typer.prompt("Revised message", default=result.message)

        if not edited_message:
            console.print("[yellow]Empty message. Commit aborted.[/yellow]")
            return

        with console.status("[dim]Creating commit...[/dim]", spinner="simpleDots"):
            success = await execute_commit_async(edited_message)

        if success:
            console.print(
                "\n[bold green]✔ Commit created successfully![/bold green] 🚀"
            )
        else:
            show_error("Git failed to execute the commit command.", title="Git Error")
    else:
        console.print("\n[dim]✖ Commit aborted by user.[/dim]\n")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    c: bool = typer.Option(
        False,
        "--commit",
        "-c",
        help="Analyze staged changes and generate a commit message.",
    ),
):
    if ctx.invoked_subcommand is None:
        if c:
            import asyncio

            asyncio.run(commit())
        else:
            console.print(LOGO)  # Print logo on root or help
            console.print(ctx.get_help())


if __name__ == "__main__":
    app()
