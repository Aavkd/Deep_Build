"""Todo module.

This module defines a simple todo list manager that stores tasks in a JSON
file.  The :class:`TodoItem` dataclass represents a single task and the
:class:`TodoManager` class provides CRUD operations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional


@dataclass
class TodoItem:
    """Represents a single todo item.

    Attributes
    ----------
    id : int
        Unique identifier for the task.
    description : str
        Human‑readable description of the task.
    completed : bool
        ``True`` if the task has been completed.
    """

    id: int
    description: str
    completed: bool = False


class TodoManager:
    """Manages a collection of :class:`TodoItem` objects.

    The tasks are persisted in a JSON file located at ``path``.  The file
    contains a list of dictionaries that can be directly converted to
    :class:`TodoItem` instances.

    Parameters
    ----------
    path : str | Path
        Path to the JSON file that stores the tasks.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._tasks: List[TodoItem] = []
        self._load()

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    def _load(self) -> None:
        """Load tasks from the JSON file.

        If the file does not exist, it is created with an empty list.
        """
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("[]", encoding="utf-8")
            self._tasks = []
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self._tasks = [TodoItem(**item) for item in data]
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError(f"Invalid todo file {self.path}: {exc}") from exc

    def _save(self) -> None:
        """Persist the current task list to the JSON file."""
        data = [asdict(task) for task in self._tasks]
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def add_task(self, description: str) -> TodoItem:
        """Create a new task and return it.

        Parameters
        ----------
        description : str
            The task description.

        Returns
        -------
        TodoItem
            The newly created task.
        """
        new_id = max((task.id for task in self._tasks), default=0) + 1
        task = TodoItem(id=new_id, description=description)
        self._tasks.append(task)
        self._save()
        return task

    def list_tasks(self) -> List[TodoItem]:
        """Return a list of all tasks.

        The returned list is a shallow copy to prevent accidental mutation.
        """
        return list(self._tasks)

    def complete_task(self, task_id: int) -> bool:
        """Mark a task as completed.

        Parameters
        ----------
        task_id : int
            Identifier of the task to complete.

        Returns
        -------
        bool
            ``True`` if the task was found and updated, ``False`` otherwise.
        """
        for task in self._tasks:
            if task.id == task_id:
                task.completed = True
                self._save()
                return True
        return False

    def delete_task(self, task_id: int) -> bool:
        """Delete a task by its identifier.

        Parameters
        ----------
        task_id : int
            Identifier of the task to delete.

        Returns
        -------
        bool
            ``True`` if a task was removed, ``False`` if no matching task
            was found.
        """
        original_len = len(self._tasks)
        self._tasks = [t for t in self._tasks if t.id != task_id]
        if len(self._tasks) < original_len:
            self._save()
            return True
        return False
