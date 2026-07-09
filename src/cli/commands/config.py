"""Config command - Manage application configuration."""

from __future__ import annotations

import os
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

    Example:
        pd config show
    """
    settings = get_settings()

    table = Table(title="Current Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Source", style="dim")

    # Core settings
    core_settings = [
        ("browser_type", settings.browser_type, "env/BROWSER_TYPE"),
        ("browser_headless", str(settings.browser_headless), "env/BROWSER_HEADLESS"),
        ("default_delay", str(settings.default_delay), "env/DEFAULT_DELAY"),
        ("max_parallel", str(settings.max_parallel), "env/MAX_PARALLEL"),
        ("max_retries", str(settings.max_retries), "env/MAX_RETRIES"),
        ("log_level", settings.log_level, "env/LOG_LEVEL"),
    ]

    # Paths
    paths = [
        ("database_path", settings.database_path, "env/DATABASE_PATH"),
        ("profile_dir", settings.profile_dir, "env/PROFILE_DIR"),
        ("screenshot_dir", settings.screenshot_dir, "env/SCREENSHOT_DIR"),
    ]

    # API Keys (masked)
    api_keys = []
    if settings.dat_impulse_api_key:
        api_keys.append(("dat_impulse_api_key", "***" + settings.dat_impulse_api_key[-4:], "env"))
    if settings.decodo_api_key:
        api_keys.append(("decodo_api_key", "***" + settings.decodo_api_key[-4:], "env"))

    for key, value, source in core_settings + paths + api_keys:
        table.add_row(key, value, source)

    console.print(table)


@config_app.command()
def get(
    key: str = typer.Argument(..., help="Configuration key to get"),
) -> None:
    """
    Get a specific configuration value.

    Example:
        pd config get browser_type
        pd config get dat_impulse_api_key
    """
    settings = get_settings()

    # Try direct attribute
    if hasattr(settings, key):
        value = getattr(settings, key)
        console.print(f"[cyan]{key}[/cyan] = [green]{value}[/green]")
        return

    # Try nested access
    parts = key.split(".")
    if len(parts) == 2:
        section, subkey = parts
        if hasattr(settings, section):
            section_obj = getattr(settings, section)
            if hasattr(section_obj, subkey):
                value = getattr(section_obj, subkey)
                console.print(f"[cyan]{key}[/cyan] = [green]{value}[/green]")
                return

    console.print(f"[red]Key not found:[/red] {key}")
    console.print("\n[dim]Available keys:[/dim]")
    console.print("  browser_type, browser_headless")
    console.print("  default_delay, max_parallel, max_retries")
    console.print("  log_level, database_path")


@config_app.command()
def set(
    key: str = typer.Argument(..., help="Configuration key to set"),
    value: str = typer.Argument(..., help="Value to set"),
    persist: bool = typer.Option(True, "--persist/--no-persist", help="Save to .env file"),
) -> None:
    """
    Set a configuration value.

    Example:
        pd config set log_level DEBUG
        pd config set default_delay 10
    """
    # Map config keys to env variable names
    env_map = {
        "browser_type": "BROWSER_TYPE",
        "browser_headless": "BROWSER_HEADLESS",
        "default_delay": "DEFAULT_DELAY",
        "max_parallel": "MAX_PARALLEL",
        "max_retries": "MAX_RETRIES",
        "log_level": "LOG_LEVEL",
        "dat_impulse_api_key": "DAT_IMPULSE_API_KEY",
        "decodo_api_key": "DECODO_API_KEY",
    }

    env_key = env_map.get(key, key.upper())

    # Set in environment
    os.environ[env_key] = value

    # Persist to .env
    if persist:
        env_file = Path(".env")
        env_file.touch(exist_ok=True)

        # Read existing
        lines = []
        if env_file.exists():
            with open(env_file) as f:
                lines = f.readlines()

        # Update or add
        found = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"{env_key}="):
                new_lines.append(f"{env_key}={value}\n")
                found = True
            else:
                new_lines.append(line)

        if not found:
            new_lines.append(f"{env_key}={value}\n")

        with open(env_file, "w") as f:
            f.writelines(new_lines)

    # Reload settings
    reload_settings()

    console.print(f"[green]✓[/green] Set {key} = {value}")
    if persist:
        console.print(f"[dim]  Saved to .env[/dim]")


@config_app.command()
def reset(
    scope: str = typer.Option("all", "--scope", help="Scope to reset (all, env, cache)"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
) -> None:
    """
    Reset configuration to defaults.

    Example:
        pd config reset
        pd config reset --scope env --force
    """
    if not force and scope == "all":
        confirm = typer.confirm("Reset all configuration to defaults?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    if scope in ("all", "env"):
        env_file = Path(".env")
        if env_file.exists():
            backup = Path(".env.backup")
            env_file.rename(backup)
            console.print(f"[yellow]Backed up .env to {backup}[/yellow]")

    if scope in ("all", "cache"):
        from ...utils import config as config_module
        config_module._settings = None
        console.print("[yellow]Cleared config cache[/yellow]")

    reload_settings()
    console.print("[green]✓[/green] Configuration reset complete")


@config_app.command()
def edit() -> None:
    """
    Open configuration file in editor.

    Example:
        pd config edit
    """
    import subprocess

    env_file = Path(".env")

    if not env_file.exists():
        # Create from example
        example = Path(".env.example")
        if example.exists():
            import shutil
            shutil.copy(example, env_file)
            console.print(f"[cyan]Created .env from .env.example[/cyan]")

    # Open in editor
    editor = os.environ.get("EDITOR", "nano")
    try:
        subprocess.run([editor, str(env_file)], check=True)
        reload_settings()
        console.print("[green]✓[/green] Configuration updated")
    except Exception as e:
        console.print(f"[red]Error opening editor: {e}[/red]")
        console.print(f"[dim]Config file: {env_file.absolute()}[/dim]")


from pathlib import Path
