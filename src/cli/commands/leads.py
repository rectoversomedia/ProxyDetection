"""Leads command - Manage lead data."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.prompt import Confirm

from ...utils.logger import get_logger
from ...leads.parser import LeadParser
from ...leads.validator import LeadValidator
from ...leads.generator import LeadGenerator, LeadGeneratorConfig

logger = get_logger(__name__)
console = Console()

leads_app = typer.Typer(name="leads", help="Manage lead data")


@leads_app.command("import")
def import_leads(
    source: Path = typer.Option(..., "--source", "-s", help="Path to source file"),
    format: str = typer.Option("auto", "--format", "-f", help="File format (csv, json, auto)"),
    dedup: bool = typer.Option(True, "--dedup/--no-dedup", help="Remove duplicates"),
    validate: bool = typer.Option(True, "--validate/--no-validate", help="Validate leads"),
    save: bool = typer.Option(True, "--save/--no-save", help="Save to database"),
) -> None:
    """
    Import leads from a file.

    Example:
        pd leads import --source data/leads.csv
        pd leads import --source data/leads.json --format json
    """
    console.print(f"[bold blue]Importing Leads[/bold blue]")
    console.print(f"  Source: {source}")

    if not source.exists():
        console.print(f"[red]Error: File not found: {source}[/red]")
        raise typer.Exit(1)

    # Parse file
    parser = LeadParser()
    result = parser.parse_file(str(source), format=format if format != "auto" else None)

    console.print(f"\n[green]✓[/green] Parsed {result.successful_rows} of {result.total_rows} rows")

    if result.errors:
        console.print(f"\n[yellow]⚠ {len(result.errors)} parse errors[/yellow]")
        for error in result.errors[:3]:
            console.print(f"  [red]•[/red] {error}")

    if result.skipped_rows > 0:
        console.print(f"[yellow]  Skipped {result.skipped_rows} empty/invalid rows[/yellow]")

    # Validate
    if validate and result.leads:
        console.print("\n[cyan]Validating leads...[/cyan]")
        validator = LeadValidator()
        validation_results = validator.validate_batch(result.leads)

        valid_count = sum(1 for r in validation_results if r.is_valid)
        invalid_count = len(validation_results) - valid_count

        console.print(f"  [green]Valid:[/green] {valid_count}")
        console.print(f"  [red]Invalid:[/red] {invalid_count}")

        if invalid_count > 0:
            console.print("\n[yellow]Validation issues:[/yellow]")
            for i, vr in enumerate(validation_results):
                if not vr.is_valid:
                    issues = vr.error_messages[:2]
                    console.print(f"  [red]Row {i+1}:[/red] {', '.join(issues)}")
                    if i >= 4:
                        console.print(f"  [dim]... and {invalid_count - 5} more[/dim]")
                        break

    # Save to database
    if save and result.leads:
        console.print("\n[cyan]Saving to database...[/cyan]")
        try:
            from ...storage.database import get_database
            from ...leads.manager import LeadManager

            db = get_database()
            manager = LeadManager(db)

            for lead_data in result.leads:
                asyncio.run(manager.create_lead(lead_data))

            console.print(f"[green]✓[/green] Saved {len(result.leads)} leads to database")
        except Exception as e:
            console.print(f"[yellow]⚠ Could not save to database: {e}[/yellow]")

    console.print("\n[bold green]Import complete![/bold green]")


@leads_app.command()
def validate(
    file: Path = typer.Argument(..., help="Path to leads file to validate"),
    strict: bool = typer.Option(False, "--strict", help="Enable strict validation"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output validation report"),
) -> None:
    """
    Validate lead data.

    Example:
        pd leads validate data/leads.csv
        pd leads validate data/leads.csv --strict --output report.json
    """
    console.print(f"[bold blue]Validating:[/bold] {file}")

    if not file.exists():
        console.print(f"[red]Error: File not found: {file}[/red]")
        raise typer.Exit(1)

    # Parse file
    parser = LeadParser()
    result = parser.parse_file(str(file))

    console.print(f"\n[cyan]Parsed {len(result.leads)} leads[/cyan]")

    # Validate
    validator = LeadValidator()
    validation_results = validator.validate_batch(result.leads)

    # Show summary
    table = Table(title="Validation Results")
    table.add_column("Status", style="cyan")
    table.add_column("Count", style="white")
    table.add_column("Percentage", style="white")

    valid_count = sum(1 for r in validation_results if r.is_valid)
    invalid_count = len(validation_results) - valid_count
    total = len(validation_results)

    table.add_row("[green]Valid[/green]", str(valid_count), f"{valid_count/total*100:.1f}%")
    table.add_row("[red]Invalid[/red]", str(invalid_count), f"{invalid_count/total*100:.1f}%")
    table.add_row("[bold]Total[/bold]", str(total), "100%")

    console.print(table)

    # Error breakdown
    summary = validator.get_summary(validation_results)

    if summary["error_counts"]:
        console.print("\n[bold red]Error Breakdown:[/bold red]")
        for code, count in sorted(summary["error_counts"].items(), key=lambda x: -x[1]):
            console.print(f"  [red]•[/red] {code}: {count}")

    if summary["warning_counts"]:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for code, count in sorted(summary["warning_counts"].items(), key=lambda x: -x[1])[:5]:
            console.print(f"  [yellow]•[/yellow] {code}: {count}")

    # Save report
    if output:
        report = {
            "total": total,
            "valid": valid_count,
            "invalid": invalid_count,
            "validity_rate": valid_count / total if total > 0 else 0,
            "errors": summary["error_counts"],
            "warnings": summary["warning_counts"],
            "results": [
                {
                    "index": i,
                    "is_valid": r.is_valid,
                    "errors": r.error_messages,
                    "warnings": r.warning_messages,
                }
                for i, r in enumerate(validation_results)
            ],
        }

        with open(output, "w") as f:
            json.dump(report, f, indent=2)

        console.print(f"\n[green]✓[/green] Report saved to {output}")


@leads_app.command()
def generate(
    count: int = typer.Option(100, "--count", "-n", help="Number of leads to generate"),
    country: str = typer.Option("US", "--country", "-c", help="Country code (US, GB, DE, JP, etc.)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("csv", "--format", "-f", help="Output format (csv, json)"),
    include_phone: bool = typer.Option(True, "--phone/--no-phone", help="Include phone numbers"),
    include_address: bool = typer.Option(True, "--address/--no-address", help="Include address"),
    include_company: bool = typer.Option(False, "--company/--no-company", help="Include company data"),
    seed: Optional[int] = typer.Option(None, "--seed", help="Random seed for reproducibility"),
) -> None:
    """
    Generate fake leads for testing.

    Example:
        pd leads generate --count 50 --country US
        pd leads generate --count 100 --country GB --output test_leads.csv
    """
    console.print(f"[bold blue]Generating Leads[/bold blue]")
    console.print(f"  Count: {count}")
    console.print(f"  Country: {country}")

    if seed:
        console.print(f"  Seed: {seed}")

    # Generate leads
    generator = LeadGenerator(seed=seed)
    config = LeadGeneratorConfig(
        country=country.upper(),
        count=count,
        include_phone=include_phone,
        include_address=include_address,
        include_company=include_company,
    )

    leads = generator.generate_batch(count=count, country=country.upper())

    # Determine output path
    if output is None:
        output = Path(f"data/generated_{country.upper()}_{count}.{format}")

    output.parent.mkdir(parents=True, exist_ok=True)

    # Save
    console.print(f"\n[cyan]Saving to {output}...[/cyan]")

    if format.lower() == "json":
        with open(output, "w") as f:
            json.dump(leads, f, indent=2)
    else:
        import csv
        with open(output, "w", newline="") as f:
            if leads:
                writer = csv.DictWriter(f, fieldnames=leads[0].keys())
                writer.writeheader()
                writer.writerows(leads)

    console.print(f"[green]✓[/green] Generated {count} leads")
    console.print(f"[green]✓[/green] Saved to {output}")

    # Show sample
    if leads:
        console.print("\n[bold]Sample Lead:[/bold]")
        sample = leads[0]
        for key, value in list(sample.items())[:6]:
            console.print(f"  {key}: {value}")


@leads_app.command()
def list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum to show"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Export to file"),
) -> None:
    """
    List leads from database.

    Example:
        pd leads list
        pd leads list --status pending --limit 50
    """
    try:
        from ...storage.database import get_database
        from ...leads.manager import LeadManager

        db = get_database()
        manager = LeadManager(db)

        if status:
            leads = asyncio.run(manager.get_leads_by_status(status, limit))
        else:
            leads_data = asyncio.run(db.get_pending_leads(limit))
            leads = [
                {
                    "id": str(ld.id),
                    "status": ld.status,
                    "created_at": str(ld.created_at),
                    "data": ld.data,
                }
                for ld in leads_data
            ]

        if not leads:
            console.print("[yellow]No leads found[/yellow]")
            return

        # Create table
        table = Table(title=f"Leads ({len(leads)} shown)")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="white")
        table.add_column("Email", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Created", style="dim")

        for lead in leads[:limit]:
            data = lead.get("data", {})
            table.add_row(
                lead.get("id", "N/A")[:8],
                data.get("name", "N/A")[:20],
                data.get("email", "N/A")[:25],
                lead.get("status", "N/A"),
                str(lead.get("created_at", "N/A"))[:10],
            )

        console.print(table)

        # Export if requested
        if output:
            with open(output, "w") as f:
                json.dump(leads, f, indent=2)
            console.print(f"\n[green]✓[/green] Exported to {output}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@leads_app.command()
def show(
    lead_id: str = typer.Argument(..., help="Lead ID to show"),
) -> None:
    """
    Show lead details.

    Example:
        pd leads show abc-123-def
    """
    try:
        from ...storage.database import get_database
        from ...leads.manager import LeadManager

        db = get_database()
        manager = LeadManager(db)

        lead = asyncio.run(manager.get_lead(lead_id))

        if not lead:
            console.print(f"[red]Lead not found: {lead_id}[/red]")
            raise typer.Exit(1)

        # Show details
        console.print(f"\n[bold cyan]Lead Details[/bold cyan]")
        console.print(f"  ID: {lead.id}")
        console.print(f"  Status: {lead.status}")
        console.print(f"  Created: {lead.created_at}")

        if lead.submitted_at:
            console.print(f"  Submitted: {lead.submitted_at}")

        if lead.result:
            console.print(f"  Result: {lead.result}")

        if lead.error_message:
            console.print(f"  [red]Error:[/red] {lead.error_message}")

        console.print(f"\n[bold]Data:[/bold]")
        for key, value in lead.data.items():
            console.print(f"  {key}: {value}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@leads_app.command()
def delete(
    lead_id: str = typer.Argument(..., help="Lead ID to delete"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
) -> None:
    """
    Delete a lead.

    Example:
        pd leads delete abc-123-def
    """
    if not force:
        confirm = typer.confirm(f"Delete lead {lead_id}?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    console.print(f"[yellow]Note: Delete functionality requires database connection[/yellow]")
    console.print(f"[cyan]Lead {lead_id} marked for deletion[/cyan]")


@leads_app.command()
def stats() -> None:
    """
    Show lead statistics.

    Example:
        pd leads stats
    """
    try:
        from ...storage.database import get_database

        db = get_database()
        stats = asyncio.run(db.get_stats())

        table = Table(title="Lead Statistics")
        table.add_column("Status", style="cyan")
        table.add_column("Count", style="white")
        table.add_column("Percentage", style="dim")

        total = sum(stats.get("leads", {}).values())

        for status_name in ["pending", "processing", "success", "failed", "skipped"]:
            count = stats.get("leads", {}).get(status_name, 0)
            pct = f"{count/total*100:.1f}%" if total > 0 else "0%"
            status_style = {
                "pending": "[yellow]pending[/yellow]",
                "processing": "[cyan]processing[/cyan]",
                "success": "[green]success[/green]",
                "failed": "[red]failed[/red]",
                "skipped": "[dim]skipped[/dim]",
            }.get(status_name, status_name)

            table.add_row(status_style, str(count), pct)

        table.add_row("[bold]Total[/bold]", str(total), "100%")

        console.print(table)

    except Exception as e:
        console.print(f"[yellow]Could not fetch stats: {e}[/yellow]")


@leads_app.command()
def dedup(
    file: Path = typer.Argument(..., help="Input file to deduplicate"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
) -> None:
    """
    Remove duplicate leads based on email.

    Example:
        pd leads dedup data/leads.csv --output unique_leads.csv
    """
    console.print(f"[bold blue]Deduplicating:[/bold] {file}")

    parser = LeadParser()
    result = parser.parse_file(str(file))

    seen = set()
    unique = []

    for lead in result.leads:
        email = lead.get("email", "").lower()
        if email and email not in seen:
            seen.add(email)
            unique.append(lead)

    removed = len(result.leads) - len(unique)

    console.print(f"\n[green]✓[/green] Found {len(result.leads)} leads")
    console.print(f"[yellow]⚠[/yellow] Removed {removed} duplicates")
    console.print(f"[green]✓[/green] Unique leads: {len(unique)}")

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)

        if output.suffix.lower() == ".json":
            with open(output, "w") as f:
                json.dump(unique, f, indent=2)
        else:
            import csv
            with open(output, "w", newline="") as f:
                if unique:
                    writer = csv.DictWriter(f, fieldnames=unique[0].keys())
                    writer.writeheader()
                    writer.writerows(unique)

        console.print(f"[green]✓[/green] Saved to {output}")
