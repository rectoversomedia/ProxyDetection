"""Main CLI entry point for ProxyDetection."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .commands.submit import submit_app
from .commands.config import config_app
from .commands.proxy import proxy_app
from .commands.leads import leads_app
from .commands.profile import profile_app

console = Console()

app = typer.Typer(
    name="pd",
    help="ProxyDetection - Lead Submission Automation System",
    add_completion=False,
    pretty_exceptions_show_locals=False,
    no_args_is_help=True,
)

# Register subcommands
app.add_typer(submit_app, name="submit")
app.add_typer(config_app, name="config")
app.add_typer(proxy_app, name="proxy")
app.add_typer(leads_app, name="leads")
app.add_typer(profile_app, name="profile")


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    log_level: str = typer.Option("INFO", "--log-level", help="Set log level"),
) -> None:
    """Initialize the application."""
    from ..utils.logger import setup_logger, get_logger

    if verbose:
        log_level = "DEBUG"

    setup_logger(log_level=log_level)
    logger = get_logger(__name__)

    # Show banner on main command
    if ctx.invoked_subcommand is None:
        show_banner()


def show_banner() -> None:
    """Show application banner."""
    banner = """
[bold cyan]╔═══════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║[/bold cyan]                                                           [bold cyan]║[/bold cyan]
[bold cyan]║[/bold cyan]   [bold white]ProxyDetection[/bold white] - Lead Submission Automation        [bold cyan]║[/bold cyan]
[bold cyan]║[/bold cyan]                                                           [bold cyan]║[/bold cyan]
[bold cyan]║[/bold cyan]   [dim]Advanced anti-detection browser automation[/dim]            [bold cyan]║[/bold cyan]
[bold cyan]║[/bold cyan]                                                           [bold cyan]║[/bold cyan]
[bold cyan]╚═══════════════════════════════════════════════════════════╝[/bold cyan]
"""
    console.print(banner)

    # Show available commands
    table = Table(title="Available Commands", show_header=True, header_style="bold magenta")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="white")

    commands = [
        ("submit", "Submit leads to target URLs"),
        ("leads", "Manage lead data"),
        ("proxy", "Manage proxy rotation"),
        ("profile", "Manage browser profiles"),
        ("config", "View and modify configuration"),
    ]

    for cmd, desc in commands:
        table.add_row(f"[bold]{cmd}[/bold]", desc)

    console.print(table)
    console.print("\n[dim]Run 'pd <command> --help' for more info on a command.[/dim]")


@app.command()
def init(
    force: bool = typer.Option(False, "--force", help="Force re-initialization"),
) -> None:
    """
    Initialize the database and create necessary directories.
    """
    from ..utils.logger import get_logger
    from ..utils.config import get_settings
    from ..storage.database import Database

    logger = get_logger(__name__)

    console.print("[bold blue]Initializing ProxyDetection...[/bold blue]\n")

    settings = get_settings()

    # Ensure directories
    console.print("[yellow]Creating directories...[/yellow]")
    settings.ensure_directories()
    console.print("[green]✓[/green] Directories created")

    # Initialize database
    console.print("\n[yellow]Initializing database...[/yellow]")
    db_url = f"sqlite+aiosqlite:///{settings.database_path}"
    db = Database(db_url)

    asyncio.run(db.initialize())
    console.print("[green]✓[/green] Database initialized")

    # Create default profiles
    console.print("\n[yellow]Creating default profiles...[/yellow]")
    from ..antidetect.profile import ProfileManager
    pm = ProfileManager()
    profiles = pm.list_profiles()
    console.print(f"[green]✓[/green] {len(profiles)} profiles available")

    console.print(f"""
[bold green]Setup complete![/bold green]

Database: {settings.database_path}
Profiles: {settings.profile_dir}
Screenshots: {settings.screenshot_dir}

Next steps:
  1. Configure API keys: pd config set proxy.dat_impulse.api_key YOUR_KEY
  2. Add proxies: pd proxy add --file proxies.txt
  3. Import leads: pd leads import --source your_leads.csv
  4. Submit: pd submit --leads leads.csv --target https://example.com
""")


@app.command()
def version() -> None:
    """Show version information."""
    from .. import __version__
    console.print(f"[bold]ProxyDetection[/bold] v{__version__}")


@app.command()
def status() -> None:
    """Show system status and statistics."""
    from ..utils.config import get_settings

    settings = get_settings()

    # Database stats
    try:
        from ..storage.database import get_database
        db = get_database()
        stats = asyncio.run(db.get_stats())
    except Exception:
        stats = {"leads": {}, "total_proxies": 0, "healthy_proxies": 0}

    # Create status table
    table = Table(title="System Status", show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Status", "[green]Ready[/green]")
    table.add_row("Database", settings.database_path)

    if "leads" in stats:
        total_leads = sum(stats["leads"].values())
        table.add_row("Total Leads", str(total_leads))
        for status, count in stats["leads"].items():
            table.add_row(f"  - {status}", str(count))

    table.add_row("Total Proxies", str(stats.get("total_proxies", 0)))
    table.add_row("Healthy Proxies", str(stats.get("healthy_proxies", 0)))

    console.print(table)


@app.command()
def shell(
    command: str = typer.Argument(..., help="Python command to execute"),
) -> None:
    """Run Python commands in the application context."""
    import sys
    from io import StringIO

    try:
        # Execute command
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()

        result = eval(command, {"__builtins__": __builtins__})

        stdout = sys.stdout.getvalue()
        stderr = sys.stderr.getvalue()

        sys.stdout = old_stdout
        sys.stderr = old_stderr

        if stdout:
            console.print(Panel(stdout, title="stdout", border_style="green"))
        if stderr:
            console.print(Panel(stderr, title="stderr", border_style="red"))
        if result is not None:
            console.print(Panel(str(result), title="result", border_style="cyan"))

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


if __name__ == "__main__":
    app()
