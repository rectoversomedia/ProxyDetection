"""Submit command - Submit leads to target URLs."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.live import Live

from ...utils.logger import get_logger
from ...core.engine import LeadSubmissionEngine, SubmissionConfig, SubmissionResult

logger = get_logger(__name__)
console = Console()

submit_app = typer.Typer(name="submit", help="Submit leads to target URLs")


@submit_app.command()
def submit(
    leads: Path = typer.Option(..., "--leads", "-l", help="Path to leads file (CSV/JSON)"),
    target: str = typer.Option(..., "--target", "-t", help="Target URL to submit to"),
    profile: str = typer.Option("default", "--profile", "-p", help="Browser profile to use"),
    parallel: int = typer.Option(1, "--parallel", help="Number of parallel submissions"),
    delay: float = typer.Option(5.0, "--delay", help="Delay between submissions (seconds)"),
    max_retries: int = typer.Option(3, "--max-retries", help="Maximum retry attempts"),
    headless: bool = typer.Option(False, "--headless", help="Run browser in headless mode"),
    save_screenshots: bool = typer.Option(True, "--screenshots/--no-screenshots", help="Save screenshots"),
    stop_on_challenge: bool = typer.Option(True, "--stop-challenge/--continue-challenge", help="Stop when challenge detected"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate but don't submit"),
) -> None:
    """
    Submit leads to a target URL with anti-detection.

    Example:
        pd submit --leads data/leads.csv --target https://example.com/form
    """
    console.print(f"[bold blue]Lead Submission[/bold blue]")
    console.print(f"  Target: {target}")
    console.print(f"  Leads: {leads}")
    console.print(f"  Parallel: {parallel}")
    console.print(f"  Delay: {delay}s")

    if not leads.exists():
        console.print(f"[red]Error: File not found: {leads}[/red]")
        raise typer.Exit(1)

    if dry_run:
        console.print("[yellow]⚠ DRY RUN MODE - No actual submission[/yellow]\n")
        _validate_dry_run(leads)
        return

    # Check dependencies
    if not _check_dependencies():
        console.print("[yellow]⚠ Some dependencies may not be installed[/yellow]")

    console.print("\n[cyan]Starting submission...[/cyan]\n")

    # Create submission config
    config = SubmissionConfig(
        target_url=target,
        parallel=parallel,
        delay_between=delay,
        max_retries=max_retries,
        headless=headless,
        save_screenshots=save_screenshots,
        stop_on_challenge=stop_on_challenge,
    )

    # Create engine and run
    engine = LeadSubmissionEngine(config=config)

    try:
        results = asyncio.run(engine.submit_from_file(str(leads), config))

        # Show summary
        _show_results_summary(results)

    except KeyboardInterrupt:
        console.print("\n[yellow]Submission interrupted by user[/yellow]")
        engine.stop()
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        logger.exception("Submission failed")
        raise typer.Exit(1)


def _validate_dry_run(leads: Path) -> None:
    """Validate leads file in dry run mode."""
    from ...leads.parser import LeadParser
    from ...leads.validator import LeadValidator

    parser = LeadParser()
    result = parser.parse_file(str(leads))

    console.print(f"[green]✓[/green] Parsed {result.successful_rows}/{result.total_rows} leads")

    if result.errors:
        console.print(f"[yellow]⚠ {len(result.errors)} parse errors[/yellow]")
        for error in result.errors[:5]:
            console.print(f"  [red]•[/red] {error}")

    # Validate leads
    validator = LeadValidator()
    valid_count = 0
    invalid_count = 0

    for lead in result.leads:
        is_valid, _ = validator.validate(lead)
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1

    console.print(f"\n[bold]Validation Results:[/bold]")
    console.print(f"  [green]Valid:[/green] {valid_count}")
    console.print(f"  [red]Invalid:[/red] {invalid_count}")

    if result.leads:
        console.print(f"\n[bold]Sample Lead:[/bold]")
        sample = result.leads[0]
        for key, value in list(sample.items())[:5]:
            console.print(f"  {key}: {value}")


def _show_results_summary(results: list) -> None:
    """Show submission results summary."""
    total = len(results)
    success = sum(1 for r in results if r.success)
    failed = total - success

    # Create summary table
    table = Table(title="Submission Results", show_header=True)
    table.add_column("Status", style="cyan")
    table.add_column("Count", style="white")
    table.add_column("Percentage", style="white")

    table.add_row("[green]Success[/green]", str(success), f"{success/total*100:.1f}%")
    table.add_row("[red]Failed[/red]", str(failed), f"{failed/total*100:.1f}%")
    table.add_row("[bold]Total[/bold]", str(total), "100%")

    console.print(table)

    # Show failed submissions
    if failed > 0:
        console.print("\n[bold red]Failed Submissions:[/bold red]")
        for r in results:
            if not r.success:
                console.print(f"  [red]•[/red] {r.lead_id}: {r.message}")
                if r.challenge_type:
                    console.print(f"    Challenge: {r.challenge_type}")


def _check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    dependencies_ok = True

    try:
        import playwright
    except ImportError:
        console.print("[yellow]⚠ Playwright not installed. Run: pip install playwright[/yellow]")
        dependencies_ok = False

    try:
        import camoufox
    except ImportError:
        console.print("[yellow]⚠ Camoufox not installed. Run: pip install camoufox[/yellow]")
        console.print("[dim]  Falling back to standard Playwright[/dim]")

    return dependencies_ok


@submit_app.command()
def status(
    session_id: Optional[str] = typer.Option(None, "--session", "-s", help="Session ID to check"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of results to show"),
) -> None:
    """
    Check submission status and history.
    """
    console.print("[bold blue]Submission Status[/bold blue]\n")

    try:
        from ...storage.database import get_database
        db = get_database()

        stats = asyncio.run(db.get_stats())

        # Show stats
        table = Table(title="Statistics", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        if "leads" in stats:
            for status, count in stats["leads"].items():
                table.add_row(f"  {status}", str(count))

        console.print(table)

    except Exception as e:
        console.print(f"[yellow]Could not fetch status: {e}[/yellow]")


@submit_app.command()
def stop(
    session_id: str = typer.Argument(..., help="Session ID to stop"),
    force: bool = typer.Option(False, "--force", help="Force stop"),
) -> None:
    """
    Stop an active submission session.
    """
    console.print(f"[yellow]Stopping session:[/yellow] {session_id}")

    if not force:
        confirm = typer.confirm("Are you sure you want to stop this session?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    console.print(f"[green]✓[/green] Session {session_id} stopped")


@submit_app.command()
def replay(
    result_file: Path = typer.Argument(..., help="Path to result JSON file"),
) -> None:
    """
    Replay failed submissions from a previous run.

    Example:
        pd submit replay results_2024-01-01.json
    """
    if not result_file.exists():
        console.print(f"[red]Error: File not found: {result_file}[/red]")
        raise typer.Exit(1)

    with open(result_file) as f:
        results = json.load(f)

    # Filter failed
    failed = [r for r in results if not r.get("success")]

    if not failed:
        console.print("[green]No failed submissions to replay[/green]")
        return

    console.print(f"[yellow]Found {len(failed)} failed submissions[/yellow]")
    console.print("[yellow]Use 'pd submit' with the original leads file to retry[/yellow]")
