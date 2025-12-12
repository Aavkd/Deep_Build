"""Command‑line interface for the todo application.

This module uses :mod:`click` to expose a group of commands that
delegate to :class:`todo.TodoManager`.  The commands are:

* ``add`` – Add a new todo item.
* ``list`` – List all todo items.
* ``complete`` – Mark an item as completed.
* ``delete`` – Delete an item.

The CLI is intentionally simple and focuses on clear error handling
and helpful help text.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

# Import the TodoManager from the project module
try:
    from todo import TodoManager
except Exception as exc:  # pragma: no cover – defensive import
    click.echo(f"Failed to import TodoManager: {exc}", err=True)
    sys.exit(1)

# Default path for the todo JSON file
DEFAULT_TODO_FILE = Path.home() / ".todo.json"


@click.group(help="Simple todo list manager.")
@click.option(
    "--file",
    "-f",
    type=click.Path(dir_okay=False, writable=True, resolve_path=True),
    default=str(DEFAULT_TODO_FILE),
    show_default=True,
    help="Path to the JSON file that stores the todo items.",
)
@click.pass_context
def cli(ctx: click.Context, file: str) -> None:
    """Create a :class:`TodoManager` instance and store it in the context.

    Parameters
    ----------
    ctx:
        Click context object.
    file:
        Path to the JSON file.
    """
    ctx.ensure_object(dict)
    ctx.obj["manager"] = TodoManager(file)


@cli.command(help="Add a new todo item.")
@click.argument("description", nargs=-1, required=True)
@click.pass_context
def add(ctx: click.Context, description: tuple[str, ...]) -> None:
    """Add a new todo item with the given description.

    The description is joined from all positional arguments.
    """
    desc = " ".join(description).strip()
    if not desc:
        click.echo("Error: description cannot be empty.", err=True)
        ctx.exit(1)
    manager: TodoManager = ctx.obj["manager"]
    try:
        manager.add(desc)
    except Exception as exc:  # pragma: no cover – defensive
        click.echo(f"Failed to add todo: {exc}", err=True)
        ctx.exit(1)
    click.echo(f"Added todo: {desc}")


@cli.command(name="list", help="List all todo items.")
@click.pass_context
def list_items(ctx: click.Context) -> None:
    """Display all todo items in a table format."""
    manager: TodoManager = ctx.obj["manager"]
    items = manager.list()
    if not items:
        click.echo("No todo items found.")
        return
    # Simple table header
    click.echo(f"{'ID':<4} {'Completed':<10} Description")
    click.echo("-" * 50)
    for item in items:
        status = "✓" if item.completed else "✗"
        click.echo(f"{item.id:<4} {status:<10} {item.description}")


@cli.command(help="Mark a todo item as completed.")
@click.argument("item_id", type=int)
@click.pass_context
def complete(ctx: click.Context, item_id: int) -> None:
    """Mark the todo item with *item_id* as completed.

    Parameters
    ----------
    item_id:
        Identifier of the todo item.
    """
    manager: TodoManager = ctx.obj["manager"]
    try:
        manager.complete(item_id)
    except ValueError as exc:  # pragma: no cover – defensive
        click.echo(f"Error: {exc}", err=True)
        ctx.exit(1)
    click.echo(f"Marked todo {item_id} as completed.")


@cli.command(help="Delete a todo item.")
@click.argument("item_id", type=int)
@click.pass_context
def delete(ctx: click.Context, item_id: int) -> None:
    """Delete the todo item with *item_id*.

    Parameters
    ----------
    item_id:
        Identifier of the todo item.
    """
    manager: TodoManager = ctx.obj["manager"]
    try:
        manager.delete(item_id)
    except ValueError as exc:  # pragma: no cover – defensive
        click.echo(f"Error: {exc}", err=True)
        ctx.exit(1)
    click.echo(f"Deleted todo {item_id}.")


if __name__ == "__main__":  # pragma: no cover – entry point
    cli()
