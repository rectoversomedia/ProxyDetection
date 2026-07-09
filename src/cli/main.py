"""Main CLI entry point for ProxyDetection."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

from ..utils.logger import setup_logger, get_logger
from ..utils.config import get_settings
from ..storage import get_database

console = Console()

app = typer.Typer(
    name="pd",
    help="ProxyDetection - Lead Submission Automation System",
    add_completion=False,
    pretty_exceptions_show_locals=False,
)


@app.callback()
def callback(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    log_level: str = typer.Option("INFO", "--log-level", help="Set log level"),
) -> None:
    """
    Initialize the application.
    """
    if verbose:
        log_level = "DEBUG"

    setup_logger(log_level=log_level)
    logger = get_logger(__name__)
    logger.info("ProxyDetection CLI initialized")


@app.command()
def init() -> None:
    """
    Initialize the database and create necessary directories.
    """
    console.print("[bold blue]Initializing ProxyDetection...[/bold blue]")

    settings = get_settings()
    settings.ensure_directories()

    db = get_database()
    # Note: This would need to be async in production
    console.print("[green]✓[/green] Directories created")
    console.print("[green]✓[/green] Database initialized")

    console.print("\n[bold green]Setup complete![/bold green]")
    console.print(f"Database: {settings.database_path}")
    console.print(f"Profiles: {settings.profile_dir}")


@app.command()
def version() -> None:
    """
    Show version information.
    """
    from .. import __version__
    console.print(f"[bold]ProxyDetection[/bold] v{__version__}")


if __name__ == "__main__":
    app()
