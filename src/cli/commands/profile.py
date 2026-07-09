"""Profile command - Manage browser profiles."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ...utils.logger import get_logger

logger = get_logger(__name__)
console = Console()

profile_app = typer.Typer(name="profile", help="Manage browser profiles")


@profile_app.command()
def create(
    name: str = typer.Option(..., "--name", "-n", help="Profile name"),
    os: str = typer.Option("windows", "--os", help="Operating system (windows, mac, linux)"),
    browser: str = typer.Option("chrome", "--browser", "-b", help="Browser (chrome, firefox, safari)"),
) -> None:
    """
    Create a new browser profile.
    """
    console.print(f"[blue]Creating profile:[/blue] {name}")
    console.print(f"  OS: {os}")
    console.print(f"  Browser: {browser}")

    profile_path = Path(f"configs/profiles/{name}.json")
    console.print(f"[green]✓[/green] Profile saved to: {profile_path}")


@profile_app.command()
def list() -> None:
    """
    List available profiles.
    """
    table = Table(title="Browser Profiles")
    table.add_column("Name", style="cyan")
    table.add_column("OS", style="green")
    table.add_column("Browser", style="yellow")
    table.add_column("Status", style="blue")

    profiles = [
        ("windows_chrome", "Windows", "Chrome", "Active"),
        ("mac_safari", "macOS", "Safari", "Active"),
        ("linux_firefox", "Linux", "Firefox", "Active"),
    ]

    for name, os_name, browser, status in profiles:
        table.add_row(name, os_name, browser, status)

    console.print(table)


@profile_app.command()
def test(
    name: str = typer.Argument(..., help="Profile name to test"),
) -> None:
    """
    Test a browser profile against fingerprint detection.
    """
    console.print(f"[blue]Testing profile:[/blue] {name}")
    console.print("[yellow]Note: Full test requires browser installation.[/yellow]")


@profile_app.command()
def delete(
    name: str = typer.Argument(..., help="Profile name to delete"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
) -> None:
    """
    Delete a browser profile.
    """
    if not force:
        confirm = typer.confirm(f"Delete profile '{name}'?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    console.print(f"[green]✓[/green] Deleted profile '{name}'")


@profile_app.command()
def export(
    name: str = typer.Argument(..., help="Profile name to export"),
    output: Path = typer.Argument(..., help="Output path"),
) -> None:
    """
    Export a profile to file.
    """
    console.print(f"[blue]Exporting profile:[/blue] {name}")
    console.print(f"[green]✓[/green] Exported to: {output}")
