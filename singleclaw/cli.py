"""SingleClaw DMN – command-line interface.

Entry point for all user-facing commands:

    singleclaw init
    singleclaw remember "text"
    singleclaw run <skill_name> --input <file>
    singleclaw reflect
    singleclaw guardian-check <action>
"""

from __future__ import annotations

import typer
from rich.console import Console

from singleclaw.dmn.journal import TaskJournal
from singleclaw.dmn.memory import MemoryStore
from singleclaw.dmn.reflect import reflect_on_memory
from singleclaw.guardian.policy import GuardianPolicy
from singleclaw.skills.registry import SkillRegistry
from singleclaw.workspace.manager import WorkspaceManager

app = typer.Typer(
    name="singleclaw",
    help="SingleClaw DMN – single-agent personal AI work OS.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()


# ─────────────────────────────────────────
# init
# ─────────────────────────────────────────


@app.command()
def init() -> None:
    """Initialise a new SingleClaw workspace in the current directory."""
    manager = WorkspaceManager()
    journal = TaskJournal(manager.workspace_dir)

    try:
        manager.initialise()
        console.print("[bold green]✔[/bold green] Workspace initialised at "
                      f"[cyan]{manager.workspace_dir}[/cyan]")
        journal.log(command="init", status="success")
    except Exception as exc:  # noqa: BLE001
        console.print(f"[bold red]✘ Init failed:[/bold red] {exc}")
        journal.log(command="init", status="error", notes=str(exc))
        raise typer.Exit(code=1) from exc


# ─────────────────────────────────────────
# remember
# ─────────────────────────────────────────


@app.command()
def remember(
    text: str = typer.Argument(..., help="Text to store in DMN memory."),
    tag: str = typer.Option("note", "--tag", "-t", help="Tag/category for the memory item."),
) -> None:
    """Store a piece of text in local DMN memory."""
    manager = WorkspaceManager()
    journal = TaskJournal(manager.workspace_dir)

    if not manager.is_initialised():
        console.print("[yellow]Workspace not initialised – run [bold]singleclaw init[/bold] first.[/yellow]")
        raise typer.Exit(code=1)

    memory = MemoryStore(manager.workspace_dir)
    try:
        entry = memory.add(text=text, tag=tag)
        console.print(f"[bold green]✔[/bold green] Stored memory [dim]{entry['id']}[/dim]: {text!r}")
        journal.log(command="remember", input_summary=text[:80], status="success")
    except Exception as exc:  # noqa: BLE001
        console.print(f"[bold red]✘ Remember failed:[/bold red] {exc}")
        journal.log(command="remember", input_summary=text[:80], status="error", notes=str(exc))
        raise typer.Exit(code=1) from exc


# ─────────────────────────────────────────
# run
# ─────────────────────────────────────────


@app.command()
def run(
    skill_name: str = typer.Argument(..., help="Name of the skill to run."),
    input_file: str = typer.Option(..., "--input", "-i", help="Path to the JSON input file."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview the action without executing."),
) -> None:
    """Run a skill from the skill library."""
    manager = WorkspaceManager()
    journal = TaskJournal(manager.workspace_dir)
    guardian = GuardianPolicy()

    if not manager.is_initialised():
        console.print("[yellow]Workspace not initialised – run [bold]singleclaw init[/bold] first.[/yellow]")
        raise typer.Exit(code=1)

    registry = SkillRegistry()
    skill = registry.get(skill_name)

    if skill is None:
        console.print(f"[bold red]✘ Unknown skill:[/bold red] [cyan]{skill_name}[/cyan]")
        raise typer.Exit(code=1)

    risk = skill.metadata.get("risk_level", "low")
    decision = guardian.check(action=f"run skill {skill_name}", risk_level=risk)

    journal.log(
        command="run",
        input_summary=f"skill={skill_name} input={input_file}",
        status="pending",
        risk_level=risk,
    )

    if decision == "BLOCK":
        console.print(f"[bold red]✘ BLOCKED by Guardian:[/bold red] skill [cyan]{skill_name}[/cyan] "
                      f"has risk_level=[red]{risk}[/red].")
        journal.log(command="run", input_summary=skill_name, status="blocked", risk_level=risk)
        raise typer.Exit(code=1)

    if decision == "REVIEW_REQUIRED" and not dry_run:
        console.print(
            f"[yellow]⚠ Guardian requires review for skill [cyan]{skill_name}[/cyan] "
            f"(risk_level=[yellow]{risk}[/yellow]).\n"
            "Re-run with [bold]--dry-run[/bold] to preview, or accept the risk by "
            "re-running with [bold]--force[/bold] (not implemented in MVP).[/yellow]"
        )
        journal.log(command="run", input_summary=skill_name, status="review_required", risk_level=risk)
        raise typer.Exit(code=1)

    from singleclaw.skills.runner import SkillRunner  # local import to keep startup fast

    runner = SkillRunner(dry_run=dry_run or decision == "REVIEW_REQUIRED")
    result = runner.execute(skill=skill, input_file=input_file)

    console.print(result)
    journal.log(
        command="run",
        input_summary=f"skill={skill_name}",
        status="dry_run" if (dry_run or decision == "REVIEW_REQUIRED") else "success",
        risk_level=risk,
    )


# ─────────────────────────────────────────
# reflect
# ─────────────────────────────────────────


@app.command()
def reflect() -> None:
    """Summarise recent DMN memory items and task journal entries."""
    manager = WorkspaceManager()
    journal = TaskJournal(manager.workspace_dir)

    if not manager.is_initialised():
        console.print("[yellow]Workspace not initialised – run [bold]singleclaw init[/bold] first.[/yellow]")
        raise typer.Exit(code=1)

    memory = MemoryStore(manager.workspace_dir)
    try:
        summary = reflect_on_memory(memory=memory, journal=journal)
        console.print(summary)
        journal.log(command="reflect", status="success")
    except Exception as exc:  # noqa: BLE001
        console.print(f"[bold red]✘ Reflect failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


# ─────────────────────────────────────────
# guardian-check
# ─────────────────────────────────────────


@app.command(name="guardian-check")
def guardian_check(
    action: str = typer.Argument(..., help="Describe the action to evaluate."),
    risk_level: str = typer.Option("low", "--risk", "-r",
                                   help="Risk level hint: low | medium | high | critical"),
) -> None:
    """Evaluate an action against the Guardian policy and display the decision."""
    guardian = GuardianPolicy()
    decision = guardian.check(action=action, risk_level=risk_level)

    colour_map = {"ALLOW": "green", "REVIEW_REQUIRED": "yellow", "BLOCK": "red"}
    colour = colour_map.get(decision, "white")

    console.print(
        f"Guardian decision for [bold]{action!r}[/bold]: "
        f"[bold {colour}]{decision}[/bold {colour}]"
    )

    manager = WorkspaceManager()
    journal = TaskJournal(manager.workspace_dir)
    journal.log(
        command="guardian-check",
        input_summary=action[:80],
        status=decision.lower(),
        risk_level=risk_level,
    )


if __name__ == "__main__":
    app()
