"""Config command - Manage application configuration."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ...utils.config import get_settings, reload_settings

console = Console()

config_app = typer.Typer(name="config", help="Manage application configuration")


@config_app.command()
def show() -> None:
    """
    Show current configuration.
    """
    settings = get_settings()

    table = Table(title="Current Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    # Show relevant settings
    config_items = [
        ("browser_type", settings.browser_type),
        ("browser_headless", str(settings.browser_headless)),
        ("default_delay", str(settings.default_delay)),
        ("max_parallel", str(settings.max_parallel)),
        ("max_retries", str(settings.max_retries)),
        ("log_level", settings.log_level),
        ("database_path", settings.database_path),
    ]

    # Add API keys if set (masked)
    if settings.dat_impulse_api_key:
        config_items.append(("dat_impulse_api_key", "***" + settings.dat_impulse_api_key[-4:]))
    if settings.decodo_api_key:
        config_items.append(("decodo_api_key", "***" + settings.decodo_api_key[-4:]))

    for key, value in config_items:
        table.add_row(key, value)

    console.print(table)


@config_app.command()
def get(
    key: str = typer.Argument(..., help="Configuration key to get"),
) -> None:
    """
    Get a specific configuration value.
    """
    settings = get_settings()

    # Try to get from settings
    value = getattr(settings, key, None)
    if value is None:
        console.print(f"[red]Key not found:[/red] {key}")
        raise typer.Exit(1)

    console.print(f"[cyan]{key}[/cyan] = [green]{value}[/green]")


@config_app.command()
def set(
    key: str = typer.Argument(..., help="Configuration key to set"),
    value: str = typer.Argument(..., help="Value to set"),
) -> None:
    """
    Set a configuration value.
    """
    console.print(f"[yellow]Note: Settings are loaded from environment variables.[/yellow]")
    console.print(f"[yellow]To set '{key}', either:[/yellow]")
    console.print(f"  1. Set environment variable: export {key.upper()}='{value}'")
    console.print(f"  2. Add to .env file: {key.upper()}={value}")
    console.print(f"  3. Use: pd config set-env {key} {value}")


@config_app.command()
def set_env(
    key: str = typer.Argument(..., help="Environment variable key"),
    value: str = typer.Argument(..., help="Value to set"),
) -> None:
    """
    Set an environment variable.
    """
    import os
    os.environ[key.upper()] = value
    reload_settings()
    console.print(f"[green]Set {key.upper()}={value}[/green]")
    console.print("[yellow]Note: This only affects the current session.[/yellow]")


@config_app.command()
def reset() -> None:
    """
    Reset configuration to defaults.
    """
    console.print("[yellow]This will remove the .env file and reset to defaults.[/yellow]")
    confirm = typer.confirm("Are you sure?")
    if confirm:
        console.print("[red]Reset not implemented - please manually delete .env file.[/red]")
