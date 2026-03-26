import typer
from rich.console import Console
import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

from config.loader import load_config
from engine.core import GitAIEngine
from git.diff import get_staged_diff, execute_commit
from providers.gemini import GeminiProvider
from providers.local import LocalProvider
from providers.base import AIProvider

app = typer.Typer(help="GitSage - Git Commit AI Assistant (Git Intelligence Layer)")
console = Console()

def get_provider(config: dict) -> AIProvider:
    provider_name = config.get("ai_provider", "gemini").lower()
    if provider_name == "gemini":
        try:
            return GeminiProvider(api_key=config.get("api_key"))
        except ValueError:
            # Prompt the user for the API key quietly
            console.print("[yellow]GitSage Intelligence Engine API Key is required but not found.[/yellow]")
            api_key = typer.prompt("Please enter your Intelligence Engine API Key", hide_input=True)
            if not api_key:
                console.print("[bold red]Error:[/bold red] API Key is required to connect to the intelligence engine.")
                raise typer.Exit(1)
            
            # Save it explicitly mapped back to user config
            config["api_key"] = api_key
            from config.loader import save_config
            save_config(config)
            
            # Reattempt initializing
            return GeminiProvider(api_key=api_key)
        except ImportError as e:
            console.print(f"[bold red]Dependency Error:[/bold red] {e}")
            raise typer.Exit(1)
    elif provider_name == "local":
        return LocalProvider()
    else:
        console.print(f"[bold red]Error:[/bold red] Unknown provider '{provider_name}'.")
        raise typer.Exit(1)

@app.command(name="commit", help="Analyze staged changes and generate a commit message.")
def commit():
    config = load_config()
    provider = get_provider(config)
    engine = GitAIEngine(provider=provider, config=config)

    with console.status("[bold cyan]Analyzing staged changes...[/bold cyan]", spinner="dots"):
        diff = get_staged_diff()
        
    if not diff:
        console.print("[yellow]No staged changes found. Did you forget to 'git add'?[/yellow]")
        raise typer.Exit(0)

    with console.status("[bold cyan]Generating commit and explanation...[/bold cyan]", spinner="dots"):
        try:
            result = engine.generate_commit(diff)
        except Exception as e:
            console.print(f"[bold red]Engine Error:[/bold red] {e}")
            raise typer.Exit(1)

    console.print(f"\n[bold green]Suggested commit:[/bold green] {result.message}\n")
    clean_explanation = result.explanation.replace("**", "")
    console.print(f"[bold blue]Explanation:[/bold blue]\n{clean_explanation}\n")
    
    conf_color = "green" if result.confidence_score >= 0.7 else "yellow" if result.confidence_score >= 0.4 else "red"
    console.print(f"[bold]Confidence:[/bold] [{conf_color}]{result.confidence_score}[/{conf_color}]\n")

    action = typer.prompt("Proceed? (y/n/edit)", default="y").strip().lower()

    if action == "y":
        if execute_commit(result.message):
            console.print("[bold green]✔ Successfully committed changes![/bold green]")
        else:
            console.print("[bold red]✖ Failed to execute commit.[/bold red]")
    elif action == "edit":
        edited_message = typer.prompt("Edit message", default=result.message)
        if execute_commit(edited_message):
            console.print("[bold green]✔ Successfully committed changes![/bold green]")
        else:
            console.print("[bold red]✖ Failed to execute commit.[/bold red]")
    else:
        console.print("[yellow]Commit aborted.[/yellow]")

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    c: bool = typer.Option(False, "--commit", "-c", help="Analyze staged changes and generate a commit message.")
):
    if ctx.invoked_subcommand is None:
        if c:
            commit()
        else:
            console.print(ctx.get_help())

if __name__ == "__main__":
    app()
