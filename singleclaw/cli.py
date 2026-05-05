"""SingleClaw DMN – command-line interface.

Entry point for all user-facing commands:

    singleclaw init
    singleclaw remember "text"
    singleclaw run <skill_name> --input <file>
    singleclaw reflect [--since YYYY-MM-DD]
    singleclaw guardian-check <action>
    singleclaw skill show <name>
    singleclaw auth login [--provider google|openai]
    singleclaw auth logout
    singleclaw auth status
    singleclaw memory list [--tag TAG]
    singleclaw memory search "query"
    singleclaw memory export [--format markdown|json] [--output PATH]
    singleclaw memory archive --before DATE
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from singleclaw.dmn.journal import TaskJournal
from singleclaw.dmn.memory import MemoryStore
from singleclaw.dmn.search import MemorySearch
from singleclaw.dmn.reflect import reflect_on_memory
from singleclaw.guardian.policy import GuardianPolicy
from singleclaw.skills.registry import SkillRegistry
from singleclaw.workspace.manager import WorkspaceManager

# Number of recent memory items injected as context into skill execution (see ADR 0004).
_MEMORY_CONTEXT_SIZE = 5

# Date/time formats accepted by the --since option (tried in order).
_SINCE_DATE_FORMATS = ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z")

app = typer.Typer(
    name="singleclaw",
    help="SingleClaw DMN – single-agent personal AI work OS.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# ─── skill sub-app ────────────────────────────────────────────────────────────

skill_app = typer.Typer(
    name="skill",
    help="Browse and display guidance skills.",
    no_args_is_help=True,
)
app.add_typer(skill_app, name="skill")

# ─── auth sub-app ─────────────────────────────────────────────────────────────

auth_app = typer.Typer(
    name="auth",
    help="Manage LLM authentication (API key or browser login).",
    no_args_is_help=True,
)
app.add_typer(auth_app, name="auth")

# ─── memory sub-app ───────────────────────────────────────────────────────────

memory_app = typer.Typer(
    name="memory",
    help="Browse, search, export, and archive DMN memory.",
    no_args_is_help=True,
)
app.add_typer(memory_app, name="memory")

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

    from singleclaw.skills.runner import SkillRunner  # local import to keep startup fast

    # Build query text from skill description for relevance-ranked context retrieval.
    memory = MemoryStore(manager.workspace_dir)
    query_text = skill.metadata.get("description", skill.name)
    memory_context = MemorySearch(memory).query(query_text, top_k=_MEMORY_CONTEXT_SIZE)

    # Attempt to resolve an LLM client (best-effort; falls back if unconfigured).
    llm_client = _resolve_llm_client(manager)

    if decision == "REVIEW_REQUIRED" and not dry_run:
        # Show a dry-run preview first, then ask the user to confirm.
        preview_runner = SkillRunner(dry_run=True)
        preview = preview_runner.execute(skill=skill, input_file=input_file)
        console.print(preview)

        if not typer.confirm("Proceed with execution?", default=False):
            console.print("[yellow]Execution cancelled.[/yellow]")
            journal.log(command="run", input_summary=skill_name, status="aborted", risk_level=risk)
            raise typer.Exit(code=0)

        # User confirmed – run for real.
        runner = SkillRunner(dry_run=False, llm_client=llm_client)
        result = runner.execute(skill=skill, input_file=input_file, memory_context=memory_context)
        console.print(result)
        journal.log(
            command="run",
            input_summary=f"skill={skill_name}",
            status="success",
            risk_level=risk,
            token_usage=getattr(result, "_llm_token_usage", None),
        )
        return

    runner = SkillRunner(dry_run=dry_run, llm_client=llm_client)
    result = runner.execute(skill=skill, input_file=input_file, memory_context=memory_context)

    console.print(result)
    journal.log(
        command="run",
        input_summary=f"skill={skill_name}",
        status="dry_run" if dry_run else "success",
        risk_level=risk,
        token_usage=getattr(result, "_llm_token_usage", None),
    )


# ─────────────────────────────────────────
# reflect
# ─────────────────────────────────────────


@app.command()
def reflect(
    since: Optional[str] = typer.Option(
        None,
        "--since",
        help="Only show items from this date onwards (YYYY-MM-DD or ISO 8601).",
    ),
) -> None:
    """Summarise recent DMN memory items and task journal entries."""
    manager = WorkspaceManager()
    journal = TaskJournal(manager.workspace_dir)

    if not manager.is_initialised():
        console.print("[yellow]Workspace not initialised – run [bold]singleclaw init[/bold] first.[/yellow]")
        raise typer.Exit(code=1)

    since_dt: Optional[datetime] = None
    if since is not None:
        try:
            since_dt = _parse_since(since)
        except ValueError:
            console.print(
                f"[bold red]✘ Invalid --since value:[/bold red] {since!r}. "
                "Use YYYY-MM-DD or ISO 8601 format."
            )
            raise typer.Exit(code=1)

    memory = MemoryStore(manager.workspace_dir)
    try:
        summary = reflect_on_memory(memory=memory, journal=journal, since=since_dt)
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


# ─────────────────────────────────────────
# skill show
# ─────────────────────────────────────────


@skill_app.command(name="show")
def skill_show(
    name: str = typer.Argument(..., help="Name of the guidance skill to display."),
) -> None:
    """Display the SKILL.md for a guidance skill."""
    registry = SkillRegistry()
    guidance = registry.get_guidance(name)

    if guidance is None:
        console.print(f"[bold red]✘ Unknown guidance skill:[/bold red] [cyan]{name}[/cyan]")
        available = [g.name for g in registry.list_guidance()]
        if available:
            console.print(f"Available: {', '.join(sorted(available))}")
        raise typer.Exit(code=1)

    content = guidance.skill_md.read_text(encoding="utf-8")
    console.print(Markdown(content))


# ─────────────────────────────────────────
# auth login
# ─────────────────────────────────────────


@auth_app.command(name="login")
def auth_login(
    provider: str = typer.Option(
        "google",
        "--provider",
        "-p",
        help="LLM provider to authenticate with: google",
    ),
) -> None:
    """Authenticate with an LLM provider via browser (OAuth Device Flow).

    Supports providers that implement OAuth 2.0 Device Authorization Grant
    (RFC 8628).  Currently: Google (Gemini).

    For API-key based providers (OpenAI), set OPENAI_API_KEY in your .env file
    instead.
    """
    import os
    from singleclaw.llm.auth.oauth_device import DeviceFlow, DeviceFlowConfig
    from singleclaw.llm.auth.token_store import TokenStore
    from singleclaw.llm.providers.google import GOOGLE_DEVICE_AUTH_URL, GOOGLE_TOKEN_URL, GOOGLE_GEMINI_SCOPE
    from singleclaw.llm.exceptions import LLMProviderError

    manager = WorkspaceManager()
    journal = TaskJournal(manager.workspace_dir)

    if provider.lower() != "google":
        console.print(
            f"[bold red]✘[/bold red] Provider [cyan]{provider}[/cyan] does not support "
            "OAuth Device Flow.\n"
            "For OpenAI, set [bold]OPENAI_API_KEY[/bold] in your .env file."
        )
        raise typer.Exit(code=1)

    client_id = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
    if not client_id:
        console.print(
            "[bold red]✘[/bold red] GOOGLE_CLIENT_ID is not set.\n"
            "Register an OAuth 2.0 application in Google Cloud Console and set\n"
            "[bold]GOOGLE_CLIENT_ID[/bold] in your .env file."
        )
        raise typer.Exit(code=1)

    config = DeviceFlowConfig(
        device_authorization_url=GOOGLE_DEVICE_AUTH_URL,
        token_url=GOOGLE_TOKEN_URL,
        client_id=client_id,
        scope=GOOGLE_GEMINI_SCOPE,
    )
    flow = DeviceFlow(config=config, console=console)

    try:
        token_data = flow.run()
    except LLMProviderError as exc:
        console.print(f"[bold red]✘ Login failed:[/bold red] {exc}")
        journal.log(command="auth login", status="error", notes=str(exc))
        raise typer.Exit(code=1) from exc

    token_path = manager.workspace_dir / "auth_token.json"
    store = TokenStore(token_path)
    store.save(token_data)

    console.print(
        f"[bold green]✔[/bold green] Authenticated with Google. "
        f"Token saved to [cyan]{token_path}[/cyan]"
    )
    journal.log(command="auth login", status="success", notes=f"provider={provider}")


# ─────────────────────────────────────────
# auth logout
# ─────────────────────────────────────────


@auth_app.command(name="logout")
def auth_logout() -> None:
    """Remove the stored OAuth token and return to unauthenticated state."""
    manager = WorkspaceManager()
    journal = TaskJournal(manager.workspace_dir)

    token_path = manager.workspace_dir / "auth_token.json"
    from singleclaw.llm.auth.token_store import TokenStore

    store = TokenStore(token_path)
    store.delete()
    console.print("[bold green]✔[/bold green] Logged out. OAuth token removed.")
    journal.log(command="auth logout", status="success")


# ─────────────────────────────────────────
# auth status
# ─────────────────────────────────────────


@auth_app.command(name="status")
def auth_status() -> None:
    """Show the current LLM authentication status."""
    from singleclaw.llm.config import LLMConfig
    from singleclaw.llm.exceptions import AuthNotConfiguredError

    manager = WorkspaceManager()

    try:
        config = LLMConfig.resolve(workspace_dir=manager.workspace_dir)
        console.print(
            f"[bold green]✔ Authenticated[/bold green]  "
            f"provider=[cyan]{config.provider.value}[/cyan]  "
            f"mode=[cyan]{config.auth_mode.value}[/cyan]"
        )
    except AuthNotConfiguredError:
        console.print(
            "[yellow]✘ Not authenticated.[/yellow]\n"
            "  • Set [bold]OPENAI_API_KEY[/bold] (or [bold]GEMINI_API_KEY[/bold]) "
            "in your .env file, or\n"
            "  • Run [bold]singleclaw auth login[/bold] to authenticate via browser."
        )


# ─────────────────────────────────────────
# memory list
# ─────────────────────────────────────────


@memory_app.command(name="list")
def memory_list(
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by exact tag match."),
) -> None:
    """List memory items, optionally filtered by tag."""
    manager = WorkspaceManager()
    if not manager.is_initialised():
        console.print("[yellow]Workspace not initialised – run [bold]singleclaw init[/bold] first.[/yellow]")
        raise typer.Exit(code=1)

    store = MemoryStore(manager.workspace_dir)
    records = store.by_tag(tag) if tag else store.list_all()

    if not records:
        msg = "No memory items found" + (f" with tag [cyan]{tag}[/cyan]" if tag else "") + "."
        console.print(f"[dim]{msg}[/dim]")
        return

    table = Table(title="DMN Memory", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", width=10)
    table.add_column("Timestamp", style="dim", width=26)
    table.add_column("Tag", width=12)
    table.add_column("Text")
    for r in records:
        table.add_row(
            r.get("id", ""),
            r.get("timestamp", ""),
            r.get("tag", ""),
            r.get("text", ""),
        )
    console.print(table)


# ─────────────────────────────────────────
# memory search
# ─────────────────────────────────────────


@memory_app.command(name="search")
def memory_search(
    query: str = typer.Argument(..., help="Natural-language query to search memory."),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results to return."),
) -> None:
    """Search memory by relevance and display ranked results."""
    manager = WorkspaceManager()
    if not manager.is_initialised():
        console.print("[yellow]Workspace not initialised – run [bold]singleclaw init[/bold] first.[/yellow]")
        raise typer.Exit(code=1)

    store = MemoryStore(manager.workspace_dir)
    results = MemorySearch(store).query(query, top_k=top_k)

    if not results:
        console.print("[dim]No memory items found.[/dim]")
        return

    table = Table(title=f"Memory search: {query!r}", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", width=10)
    table.add_column("Timestamp", style="dim", width=26)
    table.add_column("Tag", width=12)
    table.add_column("Text")
    for r in results:
        table.add_row(
            r.get("id", ""),
            r.get("timestamp", ""),
            r.get("tag", ""),
            r.get("text", ""),
        )
    console.print(table)


# ─────────────────────────────────────────
# memory export
# ─────────────────────────────────────────


@memory_app.command(name="export")
def memory_export(
    fmt: str = typer.Option("markdown", "--format", "-f", help="Output format: markdown or json."),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path."),
) -> None:
    """Export the full memory store to Markdown or JSON."""
    manager = WorkspaceManager()
    if not manager.is_initialised():
        console.print("[yellow]Workspace not initialised – run [bold]singleclaw init[/bold] first.[/yellow]")
        raise typer.Exit(code=1)

    fmt = fmt.lower()
    if fmt not in ("markdown", "json"):
        console.print(f"[bold red]✘ Unknown format:[/bold red] {fmt!r}. Choose [bold]markdown[/bold] or [bold]json[/bold].")
        raise typer.Exit(code=1)

    store = MemoryStore(manager.workspace_dir)
    records = store.list_all()

    if fmt == "json":
        content = json.dumps(records, indent=2, ensure_ascii=False)
    else:
        lines = ["# SingleClaw Memory Export\n"]
        for r in records:
            lines.append(f"- [{r.get('timestamp', '')}] **[{r.get('tag', '')}]** {r.get('text', '')}")
        content = "\n".join(lines) + "\n"

    if output:
        from pathlib import Path
        out_path = Path(output)
        out_path.write_text(content, encoding="utf-8")
        console.print(f"[bold green]✔[/bold green] Memory exported to [cyan]{out_path}[/cyan] ({len(records)} records).")
    else:
        console.print(content)


# ─────────────────────────────────────────
# memory archive
# ─────────────────────────────────────────


@memory_app.command(name="archive")
def memory_archive(
    before: str = typer.Option(..., "--before", help="Archive records older than this date (YYYY-MM-DD)."),
) -> None:
    """Move memory records older than --before DATE to the archive file.

    This is a destructive operation: records are removed from the live memory
    store.  A Guardian REVIEW_REQUIRED decision is required to proceed.
    """
    import shutil

    manager = WorkspaceManager()
    journal = TaskJournal(manager.workspace_dir)

    if not manager.is_initialised():
        console.print("[yellow]Workspace not initialised – run [bold]singleclaw init[/bold] first.[/yellow]")
        raise typer.Exit(code=1)

    try:
        cutoff = _parse_since(before)
    except ValueError:
        console.print(
            f"[bold red]✘ Invalid --before value:[/bold red] {before!r}. Use YYYY-MM-DD or ISO 8601 format."
        )
        raise typer.Exit(code=1)

    guardian = GuardianPolicy()
    decision = guardian.check(action="archive memory records", risk_level="medium")

    if decision == "BLOCK":
        console.print("[bold red]✘ BLOCKED by Guardian:[/bold red] archive is not permitted.")
        journal.log(command="memory archive", input_summary=f"before={before}", status="blocked")
        raise typer.Exit(code=1)

    store = MemoryStore(manager.workspace_dir)
    all_records = store.list_all()

    to_archive = [r for r in all_records if r.get("timestamp", "") < cutoff.isoformat()]
    to_keep = [r for r in all_records if r.get("timestamp", "") >= cutoff.isoformat()]

    if not to_archive:
        console.print(f"[dim]No records found older than {before}.[/dim]")
        return

    console.print(
        f"[yellow]This will move [bold]{len(to_archive)}[/bold] record(s) older than "
        f"[bold]{before}[/bold] to the archive.[/yellow]\n"
        f"[dim]{len(to_keep)} record(s) will remain in the active store.[/dim]"
    )

    if not typer.confirm("Proceed with archiving?", default=False):
        console.print("[yellow]Archive cancelled.[/yellow]")
        journal.log(command="memory archive", input_summary=f"before={before}", status="aborted")
        raise typer.Exit(code=0)

    # Back up the existing memory file before modification
    memory_path = manager.workspace_dir / MemoryStore.MEMORY_FILE
    archive_path = manager.workspace_dir / "memory_archive.jsonl"

    if memory_path.exists():
        shutil.copy2(memory_path, str(memory_path) + ".bak")

    # Write archive records (append)
    with archive_path.open("a", encoding="utf-8") as fh:
        for r in to_archive:
            fh.write(json.dumps(r) + "\n")

    # Rewrite live memory file with only records to keep
    with memory_path.open("w", encoding="utf-8") as fh:
        for r in to_keep:
            fh.write(json.dumps(r) + "\n")

    console.print(
        f"[bold green]✔[/bold green] Archived [bold]{len(to_archive)}[/bold] record(s) to "
        f"[cyan]{archive_path}[/cyan]."
    )
    journal.log(
        command="memory archive",
        input_summary=f"before={before} archived={len(to_archive)}",
        status="success",
    )


# ─────────────────────────────────────────
# helpers
# ─────────────────────────────────────────


def _resolve_llm_client(manager: WorkspaceManager) -> object:
    """Attempt to build an LLM client; return ``None`` on failure (no crash)."""
    from singleclaw.llm.config import LLMConfig
    from singleclaw.llm.factory import LLMClientFactory
    from singleclaw.llm.exceptions import AuthNotConfiguredError, LLMProviderError

    try:
        config = LLMConfig.resolve(workspace_dir=manager.workspace_dir)
        return LLMClientFactory.create(config)
    except (AuthNotConfiguredError, LLMProviderError):
        return None


def _parse_since(value: str) -> datetime:
    """Parse a ``--since`` date string into a timezone-aware ``datetime``.

    Accepts ``YYYY-MM-DD`` or any ISO 8601 format.

    Raises:
        ValueError: when the string cannot be parsed.
    """
    # Try plain date first (YYYY-MM-DD)
    for fmt in _SINCE_DATE_FORMATS:
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    # Last resort: fromisoformat (Python 3.11+ accepts full spec; 3.10 is partial)
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


if __name__ == "__main__":
    app()
