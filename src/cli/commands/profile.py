"""Profile command - Manage browser profiles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ...utils.logger import get_logger
from ...antidetect.profile import ProfileManager, BrowserProfile
from ...antidetect.fingerprint import FingerprintGenerator
from ...antidetect.matcher import ConsistencyChecker

logger = get_logger(__name__)
console = Console()

profile_app = typer.Typer(name="profile", help="Manage browser profiles")


@profile_app.command()
def create(
    name: str = typer.Option(..., "--name", "-n", help="Profile name"),
    os: str = typer.Option("windows", "--os", help="Operating system (windows, mac, linux)"),
    browser: str = typer.Option("chrome", "--browser", "-b", help="Browser (chrome, firefox, safari)"),
    timezone: Optional[str] = typer.Option(None, "--timezone", "-t", help="Timezone"),
    language: Optional[str] = typer.Option(None, "--lang", help="Language (e.g., en-US, de-DE)"),
    headless: bool = typer.Option(False, "--headless", help="Run headless"),
) -> None:
    """
    Create a new browser profile.

    Example:
        pd profile create --name my-profile --os windows --browser chrome
        pd profile create --name german-profile --os windows --browser chrome --lang de-DE
    """
    console.print(f"[bold blue]Creating Profile:[/bold] {name}")

    manager = ProfileManager()

    # Generate fingerprint for profile
    gen = FingerprintGenerator()

    country_map = {
        "en-US": "US", "de-DE": "DE", "fr-FR": "FR", "ja-JP": "JP",
        "es-ES": "ES", "it-IT": "IT", "pt-BR": "BR", "zh-CN": "CN",
    }

    country = country_map.get(language or "en-US", "US")
    fp = gen.generate(os=os, browser=browser, country=country, language=language)

    # Create profile
    profile = BrowserProfile(
        name=name,
        os=os,
        browser=browser,
        headless=headless,
        user_agent=fp.user_agent,
        platform=fp.platform,
        timezone=timezone or fp.timezone,
        locale=language or fp.language,
        languages=fp.languages,
        window_width=fp.screen_width,
        window_height=fp.screen_height,
        hardware_concurrency=fp.hardware_concurrency,
        device_memory=fp.device_memory,
    )

    manager.save_profile(profile)

    console.print(f"[green]✓[/green] Profile created: {name}")
    console.print(f"\n[bold]Details:[/bold]")
    console.print(f"  OS: {profile.os}")
    console.print(f"  Browser: {profile.browser}")
    console.print(f"  Timezone: {profile.timezone}")
    console.print(f"  Language: {profile.locale}")
    console.print(f"  Window: {profile.window_width}x{profile.window_height}")


@profile_app.command()
def list() -> None:
    """
    List available profiles.

    Example:
        pd profile list
    """
    manager = ProfileManager()
    profiles = manager.list_profiles()

    if not profiles:
        console.print("[yellow]No profiles found. Use 'pd profile create' to create one.[/yellow]")
        return

    table = Table(title="Browser Profiles")
    table.add_column("Name", style="cyan")
    table.add_column("OS", style="green")
    table.add_column("Browser", style="yellow")
    table.add_column("Timezone", style="blue")
    table.add_column("Language", style="magenta")

    for profile_name in profiles:
        profile = manager.get_profile(profile_name)
        if profile:
            table.add_row(
                profile.name,
                profile.os,
                profile.browser,
                profile.timezone,
                profile.locale,
            )

    console.print(table)


@profile_app.command()
def show(
    name: str = typer.Argument(..., help="Profile name to show"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """
    Show profile details.

    Example:
        pd profile show windows_chrome
    """
    manager = ProfileManager()
    profile = manager.get_profile(name)

    if not profile:
        console.print(f"[red]Profile not found: {name}[/red]")
        raise typer.Exit(1)

    if json_output:
        console.print(json.dumps(profile.to_dict(), indent=2))
        return

    console.print(f"\n[bold cyan]Profile: {profile.name}[/bold cyan]")

    table = Table(show_header=False)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    settings = [
        ("Name", profile.name),
        ("OS", profile.os),
        ("Browser", profile.browser),
        ("Headless", str(profile.headless)),
        ("Timezone", profile.timezone),
        ("Language", profile.locale),
        ("Languages", ", ".join(profile.languages)),
        ("Window Size", f"{profile.window_width}x{profile.window_height}"),
        ("User Agent", profile.user_agent[:60] + "..." if len(profile.user_agent) > 60 else profile.user_agent),
        ("Hardware Concurrency", str(profile.hardware_concurrency)),
        ("Device Memory", f"{profile.device_memory} GB"),
    ]

    for key, value in settings:
        table.add_row(key, str(value))

    console.print(table)


@profile_app.command()
def test(
    name: str = typer.Argument(..., help="Profile name to test"),
    test_url: str = typer.Option("https://botdetector.io", "--url", help="Test URL"),
) -> None:
    """
    Test a browser profile against fingerprint detection.

    Example:
        pd profile test windows_chrome
    """
    console.print(f"[bold blue]Testing Profile:[/bold] {name}")

    manager = ProfileManager()
    profile = manager.get_profile(name)

    if not profile:
        console.print(f"[red]Profile not found: {name}[/red]")
        raise typer.Exit(1)

    # Generate fingerprint from profile
    gen = FingerprintGenerator(seed=42)
    country_map = {"US": "US", "DE": "DE", "GB": "GB", "JP": "JP"}
    fp = gen.generate(os=profile.os, browser=profile.browser, country=country_map.get(profile.locale[:2], "US"))

    # Check consistency
    checker = ConsistencyChecker()
    issues = checker.check(fp)

    console.print(f"\n[bold]Fingerprint Analysis:[/bold]")
    console.print(f"  User Agent: {fp.user_agent[:50]}...")
    console.print(f"  Canvas Hash: {fp.canvas_hash[:16]}...")
    console.print(f"  WebGL: {fp.webgl_vendor}")

    if not issues:
        console.print("\n[green]✓ No consistency issues found[/green]")
    else:
        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]

        if errors:
            console.print(f"\n[bold red]Errors ({len(errors)}):[/bold red]")
            for issue in errors:
                console.print(f"  [red]•[/red] {issue.category}: {issue.message}")

        if warnings:
            console.print(f"\n[bold yellow]Warnings ({len(warnings)}):[/bold yellow]")
            for issue in warnings[:5]:
                console.print(f"  [yellow]•[/yellow] {issue.category}: {issue.message}")

    console.print("\n[cyan]Note: Full browser test requires running 'pd submit'[/cyan]")


@profile_app.command()
def delete(
    name: str = typer.Argument(..., help="Profile name to delete"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
) -> None:
    """
    Delete a browser profile.

    Example:
        pd profile delete custom-profile
    """
    if not force:
        confirm = typer.confirm(f"Delete profile '{name}'?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    manager = ProfileManager()

    if manager.delete_profile(name):
        console.print(f"[green]✓[/green] Deleted profile '{name}'")
    else:
        console.print(f"[red]Profile not found: {name}[/red]")


@profile_app.command()
def export(
    name: str = typer.Argument(..., help="Profile name to export"),
    output: Path = typer.Argument(..., help="Output path"),
) -> None:
    """
    Export a profile to file.

    Example:
        pd profile export windows_chrome exports/my_profile.json
    """
    manager = ProfileManager()
    profile = manager.get_profile(name)

    if not profile:
        console.print(f"[red]Profile not found: {name}[/red]")
        raise typer.Exit(1)

    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w") as f:
        json.dump(profile.to_dict(), f, indent=2)

    console.print(f"[green]✓[/green] Exported to {output}")


@profile_app.command()
def import_profile(
    file: Path = typer.Argument(..., help="Profile file to import"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="New profile name"),
) -> None:
    """
    Import a profile from file.

    Example:
        pd profile import profile.json --name new-profile
    """
    if not file.exists():
        console.print(f"[red]File not found: {file}[/red]")
        raise typer.Exit(1)

    with open(file) as f:
        data = json.load(f)

    profile = BrowserProfile.from_dict(data)

    if name:
        profile.name = name

    manager = ProfileManager()
    manager.save_profile(profile)

    console.print(f"[green]✓[/green] Imported profile: {profile.name}")


@profile_app.command()
def generate_fingerprint(
    os: str = typer.Option("windows", "--os", help="Operating system"),
    browser: str = typer.Option("chrome", "--browser", help="Browser"),
    country: str = typer.Option("US", "--country", "-c", help="Country code"),
    count: int = typer.Option(1, "--count", "-n", help="Number to generate"),
) -> None:
    """
    Generate browser fingerprints.

    Example:
        pd profile generate-fingerprint --os windows --browser chrome --country US --count 5
    """
    console.print(f"[bold blue]Generating Fingerprints[/bold blue]")
    console.print(f"  OS: {os}")
    console.print(f"  Browser: {browser}")
    console.print(f"  Country: {country}")

    gen = FingerprintGenerator()
    profiles = gen.generate_batch(count=count, os=os, browser=browser, country=country)

    for i, fp in enumerate(profiles):
        console.print(f"\n[bold]Fingerprint {i+1}:[/bold]")
        console.print(f"  User Agent: {fp.user_agent[:60]}...")
        console.print(f"  Platform: {fp.platform}")
        console.print(f"  Screen: {fp.screen_width}x{fp.screen_height}")
        console.print(f"  Timezone: {fp.timezone}")
        console.print(f"  Language: {fp.language}")
        console.print(f"  Canvas Hash: {fp.canvas_hash[:16]}...")
