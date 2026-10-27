import sys
import os
import asyncio
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add package root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nexus_worker.hardware import detect_hardware
from nexus_worker.engine import InferenceEngineClient
from nexus_worker.client import WorkerDaemon

console = Console()

BANNER = r"""
[bold cyan]  _   _                      ____                            _       [/bold cyan]
[bold cyan] | \ | | _____  ___   _ ___ / ___|___  _ __ ___  _ __  _   _| |_ ___ [/bold cyan]
[bold cyan] |  \| |/ _ \ \/ / | | / __| |   / _ \| '_ ` _ \| '_ \| | | | __/ _ \[/bold cyan]
[bold cyan] | |\  |  __/>  <| |_| \__ \ |__| (_) | | | | | | |_) | |_| | ||  __/[/bold cyan]
[bold cyan] |_| \_|\___/_/\_\\__,_|___/\____\___/|_| |_| |_| .__/ \__,_|\__\___|[/bold cyan]
[bold cyan]                                                |_|                  [/bold cyan]
[bold yellow]   >>> Decentralized AI Inference Provider Node (Antseed-Compatible) <<<   [/bold yellow]
"""

@click.group()
def cli():
    """NexusCompute Worker CLI - Monetize your GPU by serving open-source AI inference."""
    pass

@cli.command()
def info():
    """Display local GPU hardware specifications and discovered AI engines."""
    console.print(BANNER)
    hw = detect_hardware()
    
    table = Table(title="Detected Hardware & Compute Environment", style="cyan")
    table.add_column("Property", style="bold white")
    table.add_column("Detected Value", style="green")

    table.add_row("GPU Model", hw["gpu_name"])
    table.add_row("VRAM Capacity", f"{hw['vram_mb']} MB")
    table.add_row("Platform Backend", hw["platform"])
    
    console.print(table)

    # Check local engines
    console.print("\n[bold yellow]Scanning for Local AI Inference Engines...[/bold yellow]")
    engine = InferenceEngineClient()
    models = engine.discover_models()
    
    engine_table = Table(title="Inference Engine Status", style="magenta")
    engine_table.add_column("Engine", style="bold white")
    engine_table.add_column("Available Models", style="green")
    engine_table.add_row(engine.active_engine.upper(), ", ".join(models) if models else "None detected")
    console.print(engine_table)

@cli.command()
@click.option("--token", "-t", required=True, help="Provider node authentication token (nx-node-...) from dashboard.")
@click.option("--server", "-s", default="ws://localhost:8000/api/v1/ws/worker", help="NexusCompute Coordinator WebSocket URL.")
@click.option("--ollama-url", default="http://localhost:11434", help="Local Ollama HTTP endpoint.")
@click.option("--vllm-url", default="http://localhost:8000", help="Local vLLM HTTP endpoint.")
@click.option("--emulate", is_flag=True, default=False, help="Enable test emulation mode (simulates GPU streaming without Ollama).")
@click.option("--prompt-price", default=0.20, type=float, help="Custom price per 1M prompt tokens (in credits).")
@click.option("--completion-price", default=0.40, type=float, help="Custom price per 1M completion tokens (in credits).")
def start(token, server, ollama_url, vllm_url, emulate, prompt_price, completion_price):
    """Start the provider daemon and connect outbound to the NexusCompute network."""
    console.print(BANNER)
    console.print(Panel(
        f"[bold green]Node Token:[/bold green] {token[:12]}...\n"
        f"[bold green]Coordinator Target:[/bold green] {server}\n"
        f"[bold green]Pricing Config:[/bold green] ${prompt_price}/M prompt | ${completion_price}/M completion\n"
        f"[bold green]Emulation Mode:[/bold green] {'Active' if emulate else 'Auto-detect'}",
        title="Worker Configuration",
        style="blue"
    ))

    daemon = WorkerDaemon(
        node_token=token,
        server_ws_url=server,
        ollama_url=ollama_url,
        vllm_url=vllm_url,
        emulate=emulate,
        prompt_price=prompt_price,
        completion_price=completion_price
    )

    try:
        asyncio.run(daemon.start())
    except KeyboardInterrupt:
        console.print("\n[bold red]Worker shut down gracefully by operator.[/bold red]")

if __name__ == "__main__":
    cli()
