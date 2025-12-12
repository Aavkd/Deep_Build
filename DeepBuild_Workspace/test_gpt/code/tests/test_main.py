"""Integration tests for the CLI.

These tests exercise the command‑line interface defined in :mod:`src.main`.
They use :class:`click.testing.CliRunner` to invoke commands and a temporary
JSON file to avoid modifying real user data.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

# Ensure the ``src`` package is importable for the tests.
src_path = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(src_path))

# Import the CLI group from the application.
from main import cli


@pytest.fixture
def runner() -> CliRunner:
    """Return a fresh :class:`CliRunner` instance."""
    return CliRunner()


@pytest.fixture
def temp_file(tmp_path: Path) -> Path:
    """Provide a path to a temporary JSON file used by the CLI."""
    return tmp_path / "todo.json"


def test_add_and_list(runner: CliRunner, temp_file: Path) -> None:
    """Add a task and then list it to confirm persistence.

    The test verifies that the ``add`` command exits successfully and that
    the ``list`` command outputs the description that was just added.
    """
    # Add a task.
    result = runner.invoke(cli, ["add", "Test task", "--file", str(temp_file)])
    assert result.exit_code == 0, f"Add command failed: {result.exception}"

    # List tasks and check that the description appears.
    result = runner.invoke(cli, ["list", "--file", str(temp_file)])
    assert result.exit_code == 0, f"List command failed: {result.exception}"
    assert "Test task" in result.output


def test_complete(runner: CliRunner, temp_file: Path) -> None:
    """Mark a task as completed and verify the side effect.

    The test assumes that the ``list`` command renders a completed task with
    a ``[x]`` marker.  If the application uses a different marker, the
    assertion can be adjusted accordingly.
    """
    # Add a task.
    runner.invoke(cli, ["add", "Complete me", "--file", str(temp_file)])

    # Complete the task with id ``1``.
    result = runner.invoke(cli, ["complete", "1", "--file", str(temp_file)])
    assert result.exit_code == 0, f"Complete command failed: {result.exception}"

    # List tasks and confirm the completion marker is present.
    result = runner.invoke(cli, ["list", "--file", str(temp_file)])
    assert result.exit_code == 0, f"List after complete failed: {result.exception}"
    assert "[x]" in result.output or "✓" in result.output, "Completion marker not found"


def test_delete(runner: CliRunner, temp_file: Path) -> None:
    """Delete a task and confirm it is removed from the list."""
    # Add a task.
    runner.invoke(cli, ["add", "Delete me", "--file", str(temp_file)])

    # Delete the task with id ``1``.
    result = runner.invoke(cli, ["delete", "1", "--file", str(temp_file)])
    assert result.exit_code == 0, f"Delete command failed: {result.exception}"

    # List tasks and ensure the description is no longer present.
    result = runner.invoke(cli, ["list", "--file", str(temp_file)])
    assert result.exit_code == 0, f"List after delete failed: {result.exception}"
    assert "Delete me" not in result.output
