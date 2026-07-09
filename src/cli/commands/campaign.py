"""Campaign command - Manage marketing campaigns."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.prompt import Prompt, Confirm

from ...utils.logger import get_logger

logger = get_logger(__name__)
console = Console()

campaign_app = typer.Typer(name="campaign", help="Manage marketing campaigns")


@campaign_app.command()
def create(
    name: str = typer.Option(..., "--name", "-n", help="Campaign name"),
    sheet_url: str = typer.Option(..., "--sheet", "-s", help="Google Sheets URL"),
    target_url: str = typer.Option(..., "--target", "-t", help="Target form URL"),
    description: str = typer.Option("", "--desc", help="Campaign description"),
    delay: float = typer.Option(5.0, "--delay", help="Delay between submissions"),
) -> None:
    """
    Create a new campaign.

    Example:
        pd campaign create \
            --name "Prulady Januari 2024" \
            --sheet "https://docs.google.com/spreadsheets/d/xxx/edit" \
            --target "https://prulady.vcbl.co.id/form"
    """
    from ...campaign import CampaignManager, create_prulady_campaign

    console.print(f"[bold blue]Creating Campaign[/bold blue]")
    console.print(f"  Name: {name}")
    console.print(f"  Sheet: {sheet_url}")
    console.print(f"  Target: {target_url}")

    # Test sheet URL
    console.print("\n[cyan]Validating Google Sheet...[/cyan]")
    from ...campaign import GoogleSheetsReader

    reader = GoogleSheetsReader()

    try:
        info = asyncio.run(reader.get_sheet_info(sheet_url))
        console.print(f"[green]✓[/green] Sheet found: {info['total_rows']} rows, {len(info['columns'])} columns")
        console.print(f"  Columns: {', '.join(info['columns'][:5])}{'...' if len(info['columns']) > 5 else ''}")

        # Ask for field mappings
        console.print("\n[yellow]Note: Default Prulady field mappings will be used.[/yellow]")
        console.print("[dim]Run 'pd campaign config --id <id>' to customize field mappings later.[/dim]")

        # Create campaign
        manager = CampaignManager()
        campaign = manager.create_campaign(
            name=name,
            sheet_url=sheet_url,
            target_url=target_url,
            description=description,
            field_mappings=[
                {"sheet_column": "name", "form_selector": 'input[name="name"]', "field_type": "input", "required": True},
                {"sheet_column": "email", "form_selector": 'input[name="email"]', "field_type": "input", "required": True},
                {"sheet_column": "phone", "form_selector": 'input[name="phone"]', "field_type": "input", "required": True},
                {"sheet_column": "age", "form_selector": 'input[name="age"]', "field_type": "input"},
                {"sheet_column": "gender", "form_selector": 'select[name="gender"]', "field_type": "select"},
                {"sheet_column": "city", "form_selector": 'input[name="city"]', "field_type": "input"},
                {"sheet_column": "state", "form_selector": 'select[name="state"]', "field_type": "select"},
                {"sheet_column": "zip", "form_selector": 'input[name="zip"]', "field_type": "input"},
            ],
            delay_between=delay,
        )

        console.print(f"\n[green]✓[/green] Campaign created: {campaign.id}")
        console.print(f"[dim]Config saved to: data/campaigns/{campaign.id}.json[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@campaign_app.command()
def list() -> None:
    """
    List all campaigns.

    Example:
        pd campaign list
    """
    from ...campaign import CampaignManager

    manager = CampaignManager()
    campaigns = manager.list_campaigns()

    if not campaigns:
        console.print("[yellow]No campaigns found.[/yellow]")
        console.print("[dim]Create one with: pd campaign create --name '...' --sheet '...' --target '...'[/dim]")
        return

    table = Table(title=f"Campaigns ({len(campaigns)})")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Status", style="yellow")
    table.add_column("Leads", style="green")
    table.add_column("Success", style="green")
    table.add_column("Failed", style="red")
    table.add_column("Last Run", style="dim")

    for campaign in campaigns:
        status_color = {
            "draft": "[yellow]draft[/yellow]",
            "ready": "[green]ready[/green]",
            "running": "[cyan]running[/cyan]",
            "completed": "[blue]completed[/blue]",
            "paused": "[yellow]paused[/yellow]",
            "failed": "[red]failed[/red]",
        }.get(campaign.status.value, campaign.status.value)

        table.add_row(
            campaign.id[:20],
            campaign.name[:30],
            status_color,
            str(campaign.total_leads),
            str(campaign.success_count),
            str(campaign.failed_count),
            campaign.last_run[:10] if campaign.last_run else "Never",
        )

    console.print(table)


@campaign_app.command()
def show(
    campaign_id: str = typer.Argument(..., help="Campaign ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """
    Show campaign details.

    Example:
        pd campaign show prulady_januari_2024
    """
    from ...campaign import CampaignManager

    manager = CampaignManager()
    campaign = manager.get_campaign(campaign_id)

    if not campaign:
        console.print(f"[red]Campaign not found: {campaign_id}[/red]")
        raise typer.Exit(1)

    if json_output:
        console.print(json.dumps(campaign.to_dict(), indent=2))
        return

    table = Table(title=f"Campaign: {campaign.name}", show_header=False)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    details = [
        ("ID", campaign.id),
        ("Name", campaign.name),
        ("Status", campaign.status.value),
        ("Description", campaign.description),
        ("Sheet URL", campaign.sheet_url[:50] + "..." if len(campaign.sheet_url) > 50 else campaign.sheet_url),
        ("Target URL", campaign.target_url),
        ("Delay", f"{campaign.delay_between}s"),
        ("Max Retries", str(campaign.max_retries)),
        ("Total Leads", str(campaign.total_leads)),
        ("Success", str(campaign.success_count)),
        ("Failed", str(campaign.failed_count)),
        ("Created", campaign.created_at[:10]),
        ("Last Run", campaign.last_run[:10] if campaign.last_run else "Never"),
    ]

    for field, value in details:
        table.add_row(field, str(value))

    console.print(table)

    # Show field mappings
    console.print("\n[bold]Field Mappings:[/bold]")
    mapping_table = Table(show_header=True)
    mapping_table.add_column("Sheet Column", style="cyan")
    mapping_table.add_column("Form Selector", style="green")
    mapping_table.add_column("Type", style="yellow")
    mapping_table.add_column("Required", style="magenta")

    for fm in campaign.field_mappings:
        mapping_table.add_row(
            fm.sheet_column,
            fm.form_selector[:40] + "..." if len(fm.form_selector) > 40 else fm.form_selector,
            fm.field_type,
            "✓" if fm.required else "",
        )

    console.print(mapping_table)


@campaign_app.command()
def preview(
    campaign_id: str = typer.Argument(..., help="Campaign ID"),
    limit: int = typer.Option(5, "--limit", "-l", help="Number of leads to preview"),
) -> None:
    """
    Preview leads from a campaign's Google Sheet.

    Example:
        pd campaign preview prulady_januari_2024
    """
    from ...campaign import CampaignManager, GoogleSheetsReader

    manager = CampaignManager()
    campaign = manager.get_campaign(campaign_id)

    if not campaign:
        console.print(f"[red]Campaign not found: {campaign_id}[/red]")
        raise typer.Exit(1)

    console.print(f"[bold blue]Previewing Campaign:[/bold] {campaign.name}")
    console.print(f"[cyan]Fetching from Google Sheet...[/cyan]\n")

    reader = GoogleSheetsReader()

    try:
        leads = asyncio.run(reader.read(campaign.sheet_url))
        campaign.total_leads = len(leads)
        manager.update_campaign(campaign)

        console.print(f"[green]✓[/green] Found {len(leads)} leads\n")

        # Show sample
        if leads:
            console.print("[bold]Sample Leads:[/bold]")

            # Get all columns
            columns = list(leads[0].keys())
            preview_table = Table(show_header=True)
            for col in columns[:6]:  # Limit columns
                preview_table.add_column(col[:15], style="cyan")

            for lead in leads[:limit]:
                preview_table.add_row(*[str(lead.get(col, ""))[:15] for col in columns[:6]])

            console.print(preview_table)

            console.print(f"\n[dim]Showing {limit} of {len(leads)} leads[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@campaign_app.command()
def run(
    campaign_id: str = typer.Argument(..., help="Campaign ID"),
    test: bool = typer.Option(False, "--test", help="Run in test mode (2 leads only)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate without submitting"),
) -> None:
    """
    Run a campaign.

    Example:
        pd campaign run prulady_januari_2024
        pd campaign run prulady_januari_2024 --test
    """
    from ...campaign import CampaignManager, GoogleSheetsReader
    from ...core.engine import LeadSubmissionEngine, SubmissionConfig

    manager = CampaignManager()
    campaign = manager.get_campaign(campaign_id)

    if not campaign:
        console.print(f"[red]Campaign not found: {campaign_id}[/red]")
        raise typer.Exit(1)

    console.print(f"[bold blue]Running Campaign:[/bold] {campaign.name}")

    if dry_run:
        console.print("[yellow]⚠ DRY RUN MODE - No actual submission[/yellow]\n")

    # Fetch leads
    console.print("[cyan]Fetching leads from Google Sheet...[/cyan]")
    reader = GoogleSheetsReader()

    try:
        leads = asyncio.run(reader.read(campaign.sheet_url))

        if test:
            leads = leads[:2]
            console.print(f"[yellow]Test mode: Limiting to 2 leads[/yellow]")

        campaign.total_leads = len(leads)
        manager.update_campaign(campaign)

        console.print(f"[green]✓[/green] Loaded {len(leads)} leads\n")

    except Exception as e:
        console.print(f"[red]Error fetching leads: {e}[/red]")
        raise typer.Exit(1)

    # Show summary
    console.print("[bold]Campaign Summary:[/bold]")
    console.print(f"  Total Leads: {len(leads)}")
    console.print(f"  Target URL: {campaign.target_url}")
    console.print(f"  Delay: {campaign.delay_between}s")
    console.print(f"  Mode: {'Test' if test else 'Production'}\n")

    if dry_run:
        return

    # Check dependencies
    if not _check_browser_installed():
        console.print("[yellow]⚠ Browser not ready. Install with: pip install playwright && playwright install[/yellow]")
        if not Confirm.ask("Continue anyway?"):
            return

    # Create submission config
    form_selectors = {fm.sheet_column: fm.form_selector for fm in campaign.field_mappings}
    form_selectors["submit"] = 'button[type="submit"]'

    config = SubmissionConfig(
        target_url=campaign.target_url,
        parallel=campaign.parallel,
        delay_between=campaign.delay_between,
        max_retries=campaign.max_retries,
        form_selectors=form_selectors,
        success_selectors=campaign.success_selectors,
        failure_selectors=campaign.failure_selectors,
    )

    # Run submission
    engine = LeadSubmissionEngine(config=config)

    console.print("[cyan]Starting submission...\n[/cyan]")

    try:
        results = asyncio.run(engine.submit_batch(leads, config))

        # Update campaign stats
        campaign.success_count = sum(1 for r in results if r.success)
        campaign.failed_count = sum(1 for r in results if not r.success)
        campaign.status = campaign.status.RUNNING
        manager.update_campaign(campaign)

        # Show results
        _show_results_table(results)

    except KeyboardInterrupt:
        console.print("\n[yellow]Campaign interrupted by user[/yellow]")
        engine.stop()


def _show_results_table(results: list) -> None:
    """Show submission results."""
    total = len(results)
    success = sum(1 for r in results if r.success)
    failed = total - success

    table = Table(title="Submission Results")
    table.add_column("Status", style="cyan")
    table.add_column("Count", style="white")
    table.add_column("Percentage", style="white")

    table.add_row("[green]Success[/green]", str(success), f"{success/total*100:.1f}%")
    table.add_row("[red]Failed[/red]", str(failed), f"{failed/total*100:.1f}%")
    table.add_row("[bold]Total[/bold]", str(total), "100%")

    console.print(table)

    # Show failures
    if failed > 0:
        console.print("\n[bold red]Failed Submissions:[/bold red]")
        for r in results:
            if not r.success:
                msg = r.message[:50] if r.message else "Unknown error"
                console.print(f"  [red]•[/red] {r.lead_id}: {msg}")


def _check_browser_installed() -> bool:
    """Check if browser automation is available."""
    try:
        import playwright
        return True
    except ImportError:
        return False


@campaign_app.command()
def delete(
    campaign_id: str = typer.Argument(..., help="Campaign ID to delete"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
) -> None:
    """
    Delete a campaign.

    Example:
        pd campaign delete prulady_januari_2024
    """
    from ...campaign import CampaignManager

    if not force:
        confirm = typer.confirm(f"Delete campaign '{campaign_id}'?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    manager = CampaignManager()
    if manager.delete_campaign(campaign_id):
        console.print(f"[green]✓[/green] Deleted campaign: {campaign_id}")
    else:
        console.print(f"[red]Campaign not found: {campaign_id}[/red]")


@campaign_app.command()
def config(
    campaign_id: str = typer.Argument(..., help="Campaign ID"),
    field: Optional[str] = typer.Option(None, "--field", help="Field to set"),
    value: Optional[str] = typer.Option(None, "--value", help="Value to set"),
) -> None:
    """
    Configure campaign settings.

    Example:
        pd campaign config prulady_januari_2024 --field delay_between --value 10
    """
    from ...campaign import CampaignManager

    manager = CampaignManager()
    campaign = manager.get_campaign(campaign_id)

    if not campaign:
        console.print(f"[red]Campaign not found: {campaign_id}[/red]")
        raise typer.Exit(1)

    if field and value:
        # Set value
        if hasattr(campaign, field):
            setattr(campaign, field, value)
            manager.update_campaign(campaign)
            console.print(f"[green]✓[/green] Set {field} = {value}")
        else:
            console.print(f"[red]Unknown field: {field}[/red]")
    else:
        # Show current config
        console.print(f"\n[bold cyan]Campaign Config:[/bold cyan] {campaign.name}")
        console.print(f"[dim]ID: {campaign.id}[/dim]\n")

        config_table = Table(show_header=False)
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="white")

        config_table.add_row("target_url", campaign.target_url)
        config_table.add_row("delay_between", str(campaign.delay_between))
        config_table.add_row("max_retries", str(campaign.max_retries))
        config_table.add_row("parallel", str(campaign.parallel))
        config_table.add_row("use_proxy", str(campaign.use_proxy))
        config_table.add_row("proxy_country", str(campaign.proxy_country or "any"))

        console.print(config_table)

        console.print("\n[dim]To change a setting: pd campaign config <id> --field <name> --value <value>[/dim]")
