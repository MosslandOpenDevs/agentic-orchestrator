"""
CLI entry point for the Agentic Orchestrator.

Provides commands: init, step, loop, status
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from . import __version__
from .orchestrator import Orchestrator
from .utils.config import get_env_bool

console = Console()


def create_orchestrator(dry_run: bool = False) -> Orchestrator:
    """Create an orchestrator instance."""
    return Orchestrator(
        base_path=Path.cwd(),
        dry_run=dry_run or get_env_bool("DRY_RUN"),
    )


@click.group()
@click.version_option(version=__version__, prog_name="Agentic Orchestrator")
def main():
    """
    Mossland Agentic Orchestrator

    An autonomous system for discovering, planning, implementing,
    and validating micro Web3 services for the Mossland ecosystem.
    """
    pass


@main.command()
@click.option("--project-id", "-p", help="Custom project ID")
@click.option("--dry-run", is_flag=True, help="Run without making changes")
def init(project_id: Optional[str], dry_run: bool):
    """Initialize a new project."""
    console.print("[bold blue]Initializing new project...[/bold blue]")

    orchestrator = create_orchestrator(dry_run)

    try:
        pid = orchestrator.init_project(project_id)
        console.print(f"[bold green]Project initialized: {pid}[/bold green]")
        console.print(f"\nNext step: Run [bold]ao step[/bold] to start ideation")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@main.command()
@click.option("--dry-run", is_flag=True, help="Run without making changes")
def step(dry_run: bool):
    """Execute a single pipeline step."""
    orchestrator = create_orchestrator(dry_run)

    # Check if we have a project
    if not orchestrator.state.project_id:
        console.print("[yellow]No active project. Initializing new project...[/yellow]")
        pid = orchestrator.init_project()
        console.print(f"[green]Created project: {pid}[/green]\n")

    current_stage = orchestrator.state.stage.value
    console.print(f"[blue]Current stage: {current_stage}[/blue]")

    if dry_run:
        console.print("[yellow](Dry run mode - no actual changes)[/yellow]")

    try:
        with console.status(f"[bold green]Executing {current_stage}...[/bold green]"):
            result = orchestrator.step()

        if result.success:
            console.print(f"[bold green]Stage completed successfully[/bold green]")
            console.print(f"  Message: {result.message}")

            if result.next_stage:
                console.print(f"  Next stage: {result.next_stage.value}")

            if result.artifacts:
                console.print(f"  Artifacts created: {len(result.artifacts)}")
                for artifact in result.artifacts[:5]:  # Show first 5
                    console.print(f"    - {artifact}")
        else:
            console.print(f"[bold red]Stage failed[/bold red]")
            console.print(f"  Error: {result.error}")
            console.print(f"  Message: {result.message}")
            sys.exit(1)

    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")
        sys.exit(1)


@main.command()
@click.option("--max-steps", "-m", type=int, help="Maximum steps to execute")
@click.option("--delay", "-d", type=int, help="Delay between steps (seconds)")
@click.option("--dry-run", is_flag=True, help="Run without making changes")
def loop(max_steps: Optional[int], delay: Optional[int], dry_run: bool):
    """Run in continuous loop mode."""
    orchestrator = create_orchestrator(dry_run)

    # Check if we have a project
    if not orchestrator.state.project_id:
        console.print("[yellow]No active project. Initializing...[/yellow]")
        pid = orchestrator.init_project()
        console.print(f"[green]Created project: {pid}[/green]\n")

    console.print("[bold blue]Starting loop mode[/bold blue]")
    console.print(f"  Max steps: {max_steps or orchestrator.config.loop_max_steps}")
    console.print(f"  Delay: {delay or orchestrator.config.loop_delay}s")

    if dry_run:
        console.print("[yellow](Dry run mode)[/yellow]")

    console.print()

    try:
        results = orchestrator.loop(max_steps=max_steps, delay_seconds=delay)

        # Summary
        console.print("\n[bold blue]Loop Summary[/bold blue]")
        console.print(f"  Total steps: {len(results)}")
        console.print(f"  Successful: {sum(1 for r in results if r.success)}")
        console.print(f"  Failed: {sum(1 for r in results if not r.success)}")
        console.print(f"  Final stage: {orchestrator.state.stage.value}")

        if orchestrator.state.is_complete():
            console.print("\n[bold green]Project completed successfully![/bold green]")
        elif orchestrator.state.is_paused():
            console.print(f"\n[bold yellow]Paused: {orchestrator.state.errors.paused_reason}[/bold yellow]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Loop interrupted by user[/yellow]")
        orchestrator.save_state()
    except Exception as e:
        console.print(f"[bold red]Loop error: {e}[/bold red]")
        sys.exit(1)


@main.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def status(as_json: bool):
    """Show current orchestrator status."""
    orchestrator = create_orchestrator()
    status_data = orchestrator.status()

    if as_json:
        import json
        click.echo(json.dumps(status_data, indent=2, default=str))
        return

    # Rich output
    console.print()

    # Header
    project_id = status_data["project_id"] or "(none)"
    stage = status_data["stage"]

    console.print(Panel(
        f"[bold]Project:[/bold] {project_id}\n"
        f"[bold]Stage:[/bold] {stage}",
        title="Orchestrator Status",
        border_style="blue",
    ))

    # Flags
    flags = status_data["flags"]
    flag_str = []
    if flags["is_complete"]:
        flag_str.append("[green]COMPLETE[/green]")
    if flags["is_paused"]:
        flag_str.append("[yellow]PAUSED[/yellow]")
    if flags["can_continue"]:
        flag_str.append("[blue]READY[/blue]")

    if flag_str:
        console.print(f"Status: {' | '.join(flag_str)}")

    # Iterations
    table = Table(title="Iterations")
    table.add_column("Type", style="cyan")
    table.add_column("Current", style="magenta")
    table.add_column("Max", style="green")

    iter_data = status_data["iteration"]
    limits = status_data["limits"]

    table.add_row("Planning", str(iter_data["planning"]), str(limits["planning_max"]))
    table.add_row("Development", str(iter_data["dev"]), str(limits["dev_max"]))

    console.print(table)

    # Quality
    quality = status_data["quality"]
    if quality["review_score"] is not None or quality["tests_passed"] is not None:
        console.print("\n[bold]Quality Metrics:[/bold]")
        if quality["review_score"] is not None:
            score_color = "green" if quality["review_score"] >= quality["required_score"] else "yellow"
            console.print(f"  Review Score: [{score_color}]{quality['review_score']}/{quality['required_score']}[/{score_color}]")
        if quality["tests_passed"] is not None:
            test_color = "green" if quality["tests_passed"] else "red"
            test_str = "PASSED" if quality["tests_passed"] else "FAILED"
            console.print(f"  Tests: [{test_color}]{test_str}[/{test_color}]")

    # Errors
    errors = status_data["errors"]
    if errors["last_error"] or errors["paused_reason"]:
        console.print("\n[bold red]Errors:[/bold red]")
        if errors["paused_reason"]:
            console.print(f"  Paused: {errors['paused_reason']}")
        if errors["last_error"]:
            console.print(f"  Last Error: {errors['last_error']}")
        console.print(f"  Error Count: {errors['error_count']}")

    # Timestamps
    ts = status_data["timestamps"]
    if ts["created"]:
        console.print(f"\n[dim]Created: {ts['created']}[/dim]")
    if ts["last_updated"]:
        console.print(f"[dim]Updated: {ts['last_updated']}[/dim]")

    # Next step hint
    console.print()
    if flags["is_complete"]:
        console.print("[dim]Run 'ao init' to start a new project[/dim]")
    elif flags["is_paused"]:
        console.print("[dim]Resolve the issue and run 'ao resume' to continue[/dim]")
    elif flags["can_continue"]:
        console.print("[dim]Run 'ao step' to continue[/dim]")


@main.command()
@click.option("--dry-run", is_flag=True, help="Run without making changes")
def resume(dry_run: bool):
    """Resume from a paused state."""
    orchestrator = create_orchestrator(dry_run)

    if not orchestrator.state.is_paused():
        console.print("[yellow]Orchestrator is not paused. Use 'ao step' to continue.[/yellow]")
        return

    console.print(f"[blue]Resuming from: {orchestrator.state.errors.paused_reason}[/blue]")

    try:
        result = orchestrator.resume()

        if result.success:
            console.print("[green]Resumed successfully[/green]")
            console.print(f"  Message: {result.message}")
        else:
            console.print(f"[red]Resume failed: {result.error}[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@main.command()
@click.option("--keep-project", is_flag=True, help="Keep current project ID")
@click.confirmation_option(prompt="Are you sure you want to reset?")
def reset(keep_project: bool):
    """Reset the orchestrator state."""
    orchestrator = create_orchestrator()

    try:
        orchestrator.reset(keep_project=keep_project)
        console.print("[green]State reset successfully[/green]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@main.command()
@click.option("--dry-run", is_flag=True, help="Show what would be pushed")
def push(dry_run: bool):
    """Push all committed changes to remote."""
    orchestrator = create_orchestrator(dry_run)

    try:
        if dry_run:
            console.print("[yellow]Dry run - would push to remote[/yellow]")
            return

        success = orchestrator.push_changes()
        if success:
            console.print("[green]Changes pushed successfully[/green]")
        else:
            console.print("[red]Push failed[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
