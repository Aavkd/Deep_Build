"""Unit tests for the :mod:`todo` module.

The tests use a temporary JSON file to avoid modifying real data.
They cover adding, listing, completing, and deleting tasks.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Ensure the ``src`` package is importable
src_path = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(src_path))

import pytest

from todo import TodoManager, TodoItem

# Helper fixture that provides a fresh TodoManager backed by a temp file
@pytest.fixture
def manager() -> TodoManager:
    """Return a :class:`TodoManager` instance with a temporary JSON file.

    The file is removed after the test finishes.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        tmp_path = Path(tmp.name)
    try:
        mgr = TodoManager(tmp_path)
        yield mgr
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_add_task(manager: TodoManager) -> None:
    """Adding a task should create a :class:`TodoItem` with a unique id."""
    description = "Buy milk"
    manager.add(description)
    tasks = manager.list()
    assert len(tasks) == 1
    task = tasks[0]
    assert isinstance(task, TodoItem)
    assert task.description == description
    assert task.completed is False
    assert isinstance(task.id, int)


def test_list_tasks(manager: TodoManager) -> None:
    """Listing should return all added tasks in the order they were added."""
    descriptions = ["Task A", "Task B", "Task C"]
    for d in descriptions:
        manager.add(d)
    tasks = manager.list()
    assert len(tasks) == 3
    assert [t.description for t in tasks] == descriptions


def test_complete_task(manager: TodoManager) -> None:
    """Completing a task should set its ``completed`` flag to ``True``."""
    manager.add("Finish report")
    tasks = manager.list()
    task_id = tasks[0].id
    manager.complete(task_id)
    updated_task = manager.list()[0]
    assert updated_task.completed is True


def test_delete_task(manager: TodoManager) -> None:
    """Deleting a task should remove it from the list."""
    manager.add("Clean house")
    manager.add("Read book")
    tasks_before = manager.list()
    assert len(tasks_before) == 2
    delete_id = tasks_before[0].id
    manager.delete(delete_id)
    tasks_after = manager.list()
    assert len(tasks_after) == 1
    assert tasks_after[0].description == "Read book"
    # Ensure the deleted id is no longer present
    ids = [t.id for t in tasks_after]
    assert delete_id not in ids
