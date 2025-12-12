"""
Command Line Interface for Todo application.

This module provides the CLI interface using Click for:
- Listing todos
- Adding new todos
- Completing todos
- Deleting todos
"""

import click
from .core import add_todo, complete_todo, delete_todo
from .storage import load_data, save_data
from .models import TodoList


@click.group()
def cli():
    """Main CLI entry point."""
    pass


@cli.command()
def list():
    """List all todos with their status."""
    todo_list = load_data()
    for todo in todo_list.todos:
        status = "✓" if todo.completed else " "
        click.echo(f"[{status}] {todo.id}: {todo.title}")
    click.echo(f"Total: {len(todo_list.todos)} todos")


@cli.command()
@click.argument("title")
def add(title):
    """Add a new todo."""
    todo_list = load_data()
    todo_list = add_todo(todo_list, title)
    save_data(todo_list)
    click.echo(f"Added: {title}")


@cli.command()
@click.argument("todo_id")
def complete(todo_id):
    """Mark a todo as completed."""
    todo_list = load_data()
    todo_list = complete_todo(todo_list, int(todo_id))
    save_data(todo_list)
    click.echo(f"Completed todo {todo_id}")


@cli.command()
@click.argument("todo_id")
def delete(todo_id):
    """Delete a todo."""
    todo_list = load_data()
    todo_list = delete_todo(todo_list, int(todo_id))
    save_data(todo_list)
    click.echo(f"Deleted todo {todo_id}")


if __name__ == "__main__":
    cli()