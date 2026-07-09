"""Proxy command - Manage proxy rotation and health."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ...utils.logger import get_logger
from ...proxy.rotator import ProxyRotator, ProxyConfig
from ...proxy.health_checker import ProxyHealthChecker

logger = get_logger(__name__)
console = Console()

proxy_app = typer.Typer(name="proxy", help="Manage proxy rotation and health")


@proxy_app.command()
def add(
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Path to proxy list file"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Proxy provider (dat_impulse, decodo)"),
    country: Optional[str] = typer.Option(None, "--country", "-c", help="Filter by country code"),
    format: str = typer.Option("auto", "--format", help="File format (auto, host:port, json)"),
) -> None:
    """
    Add proxies to the pool.

    Example:
        pd proxy add --file proxies.txt
        pd proxy add --provider dat_impulse --country US
    """
    console.print(f"[bold blue]Adding Proxies[/bold blue]")

    rotator = ProxyRotator()
    added_count = 0

    if file:
        if not file.exists():
            console.print(f"[red]Error: File not found: {file}[/red]")
            raise typer.Exit(1)

        console.print(f"[cyan]Loading from file: {file}[/cyan]")

        # Parse file
        with open(file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                try:
                    proxy = ProxyConfig.from_url(line, country=country)
                    rotator.add_proxy(proxy)
                    added_count += 1
                except Exception as e:
                    logger.warning(f"Failed to parse proxy line: {line} - {e}")

        console.print(f"[green]✓[/green] Added {added_count} proxies from file")

    elif provider:
        console.print(f"[cyan]Fetching from provider: {provider}[/cyan]")

        if provider == "dat_impulse":
            from ...proxy.providers.dat_impulse import DataImpulseProvider

            try:
                provider_obj = DataImpulseProvider()
                proxies = asyncio.run(provider_obj.fetch_proxies(country=country))

                for proxy in proxies:
                    rotator.add_proxy(proxy)
                    added_count += 1

                console.print(f"[green]✓[/green] Added {added_count} proxies from DataImpulse")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

        elif provider == "decodo":
            from ...proxy.providers.decodo import DecodoProvider

            try:
                provider_obj = DecodoProvider()
                proxies = asyncio.run(provider_obj.fetch_proxies(country=country))

                for proxy in proxies:
                    rotator.add_proxy(proxy)
                    added_count += 1

                console.print(f"[green]✓[/green] Added {added_count} proxies from Decodo")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

        else:
            console.print(f"[red]Unknown provider: {provider}[/red]")
            console.print("Available providers: dat_impulse, decodo")

    else:
        console.print("[red]Error: Please specify --file or --provider[/red]")
        raise typer.Exit(1)

    # Save to file for persistence
    if added_count > 0:
        rotator.export_to_file("data/proxies.txt")
        console.print(f"[green]✓[/green] Saved to data/proxies.txt")


@proxy_app.command()
def list(
    filter: Optional[str] = typer.Option(None, "--filter", "-f", help="Filter proxies (healthy, unhealthy, all)"),
    country: Optional[str] = typer.Option(None, "--country", "-c", help="Filter by country"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number to show"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Export to file"),
) -> None:
    """
    List available proxies.

    Example:
        pd proxy list
        pd proxy list --filter healthy --country US
    """
    console.print(f"[bold blue]Proxy List[/bold blue]")

    # Load proxies from file if exists
    rotator = ProxyRotator()
    proxy_file = Path("data/proxies.txt")

    if proxy_file.exists():
        rotator.add_proxies_from_file(str(proxy_file))

    if rotator.count == 0:
        console.print("[yellow]No proxies loaded. Use 'pd proxy add' first.[/yellow]")
        return

    # Filter
    proxies = rotator.list_proxies(
        country=country,
        filter_healthy=(filter == "healthy") if filter else True,
    )

    if not proxies:
        console.print("[yellow]No proxies match the filter[/yellow]")
        return

    # Show table
    table = Table(title=f"Proxies ({min(len(proxies), limit)} shown)")
    table.add_column("Host", style="cyan")
    table.add_column("Port", style="white")
    table.add_column("Country", style="green")
    table.add_column("Health", style="yellow")
    table.add_column("Success", style="magenta")
    table.add_column("Latency", style="blue")

    for proxy in proxies[:limit]:
        health_icon = "[green]●[/green]" if proxy.success_rate >= 0.8 else (
            "[yellow]●[/yellow]" if proxy.success_rate >= 0.5 else "[red]●[/red]"
        )
        success_str = f"{proxy.success_rate*100:.0f}%" if proxy.success_rate else "N/A"
        latency_str = f"{proxy.latency:.1f}s" if proxy.latency else "N/A"

        table.add_row(
            proxy.host[:30],
            str(proxy.port),
            proxy.country or "N/A",
            health_icon,
            success_str,
            latency_str,
        )

    console.print(table)

    # Stats
    stats = rotator.get_stats()
    console.print(f"\n[dim]Total: {stats['total']} | "
                 f"Healthy: [green]{stats['healthy_count']}[/green] | "
                 f"Unhealthy: [red]{stats['unhealthy_count']}[/red][/dim]")

    # Export
    if output:
        import json
        with open(output, "w") as f:
            json.dump([p.to_dict() for p in proxies], f, indent=2)
        console.print(f"[green]✓[/green] Exported to {output}")


@proxy_app.command()
def test(
    count: int = typer.Option(10, "--count", "-n", help="Number of proxies to test"),
    timeout: int = typer.Option(30, "--timeout", "-t", help="Timeout per proxy (seconds)"),
    test_url: str = typer.Option("https://www.google.com", "--url", help="URL to test"),
    workers: int = typer.Option(5, "--workers", "-w", help="Concurrent workers"),
) -> None:
    """
    Test proxy health and connectivity.

    Example:
        pd proxy test --count 20
        pd proxy test --count 50 --url https://example.com
    """
    console.print(f"[bold blue]Testing Proxy Health[/bold blue]")
    console.print(f"  Testing up to {count} proxies")
    console.print(f"  Timeout: {timeout}s")
    console.print(f"  Test URL: {test_url}")
    console.print(f"  Workers: {workers}")

    # Load proxies
    rotator = ProxyRotator()
    proxy_file = Path("data/proxies.txt")

    if proxy_file.exists():
        rotator.add_proxies_from_file(str(proxy_file))

    if rotator.count == 0:
        console.print("[yellow]No proxies loaded. Use 'pd proxy add' first.[/yellow]")
        return

    proxies = rotator.list_proxies()[:count]

    console.print(f"\n[cyan]Testing {len(proxies)} proxies...[/cyan]\n")

    # Test with progress
    checker = ProxyHealthChecker(timeout=timeout)

    results_table = Table(title="Test Results")
    results_table.add_column("Host", style="cyan")
    results_table.add_column("Status", style="white")
    results_table.add_column("Latency", style="yellow")
    results_table.add_column("Success Rate", style="green")

    healthy = 0
    unhealthy = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Testing...", total=len(proxies))

        for proxy in proxies:
            is_healthy = asyncio.run(checker.check_proxy(proxy, test_url))

            if is_healthy:
                healthy += 1
                status = "[green]✓[/green]"
            else:
                unhealthy += 1
                status = "[red]✗[/red]"

            latency = f"{proxy.latency:.2f}s" if proxy.latency else "N/A"
            success = f"{proxy.success_rate*100:.0f}%" if proxy.success_rate else "N/A"

            results_table.add_row(proxy.host[:25], status, latency, success)
            progress.advance(task)

    console.print(results_table)

    # Summary
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  [green]Healthy: {healthy}[/green]")
    console.print(f"  [red]Unhealthy: {unhealthy}[/red]")
    console.print(f"  Success rate: {healthy/len(proxies)*100:.1f}%")


@proxy_app.command()
def stats() -> None:
    """
    Show proxy statistics.

    Example:
        pd proxy stats
    """
    rotator = ProxyRotator()
    proxy_file = Path("data/proxies.txt")

    if proxy_file.exists():
        rotator.add_proxies_from_file(str(proxy_file))

    stats = rotator.get_stats()

    table = Table(title="Proxy Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Proxies", str(stats["total"]))
    table.add_row("Healthy", str(stats["healthy_count"]))
    table.add_row("Unhealthy", str(stats["unhealthy_count"]))
    table.add_row("Avg Success Rate", f"{stats['avg_success_rate']*100:.1f}%")
    table.add_row("Avg Latency", f"{stats['avg_latency']:.2f}s" if stats['avg_latency'] else "N/A")

    console.print(table)

    # By country
    if stats["by_country"]:
        console.print("\n[bold]By Country:[/bold]")
        country_table = Table(show_header=False)
        country_table.add_column("Country", style="cyan")
        country_table.add_column("Count", style="white")

        for country, count in sorted(stats["by_country"].items(), key=lambda x: -x[1]):
            country_table.add_row(country, str(count))

        console.print(country_table)


@proxy_app.command()
def remove(
    proxy: str = typer.Argument(..., help="Proxy to remove (format: host:port)"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
) -> None:
    """
    Remove a proxy from the pool.

    Example:
        pd proxy remove proxy.example.com:8080
    """
    if not force:
        confirm = typer.confirm(f"Remove proxy {proxy}?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    # Parse proxy
    try:
        parts = proxy.split(":")
        host = parts[0]
        port = int(parts[1])

        rotator = ProxyRotator()
        proxy_file = Path("data/proxies.txt")

        if proxy_file.exists():
            rotator.add_proxies_from_file(str(proxy_file))

        if rotator.remove_proxy(host, port):
            rotator.export_to_file(str(proxy_file))
            console.print(f"[green]✓[/green] Removed {proxy}")
        else:
            console.print(f"[yellow]Proxy not found: {proxy}[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@proxy_app.command()
def clean(
    min_success_rate: float = typer.Option(0.3, "--min-rate", "-r", help="Minimum success rate"),
) -> None:
    """
    Remove unhealthy proxies from the pool.

    Example:
        pd proxy clean
        pd proxy clean --min-rate 0.5
    """
    console.print(f"[bold blue]Cleaning Unhealthy Proxies[/bold blue]")
    console.print(f"  Minimum success rate: {min_success_rate*100:.0f}%")

    rotator = ProxyRotator()
    proxy_file = Path("data/proxies.txt")

    if proxy_file.exists():
        rotator.add_proxies_from_file(str(proxy_file))

    original_count = rotator.count

    # Filter unhealthy
    proxies = rotator.list_proxies(filter_healthy=True)

    # Remove all and re-add healthy
    rotator._proxies = proxies

    removed = original_count - rotator.count

    if removed > 0:
        rotator.export_to_file(str(proxy_file))
        console.print(f"[green]✓[/green] Removed {removed} unhealthy proxies")
        console.print(f"[green]✓[/green] Remaining: {rotator.count}")
    else:
        console.print("[green]No unhealthy proxies found[/green]")
