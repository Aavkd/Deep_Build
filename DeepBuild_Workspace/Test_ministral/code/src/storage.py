"""
Storage module for handling Todo data persistence.

This module provides functionality to load and save TodoList data
to/from a JSON file.
"""

import json
from pathlib import Path
from typing import Optional
from .models import TodoList


DATA_FILE = Path(__file__).parent / "todo.json"


def load_data() -> TodoList:
    """Load TodoList data from JSON file.
    
    Returns:
        TodoList: Loaded todo list, or empty TodoList if file doesn't exist
    """
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
        return TodoList([Todo(**item) for item in data])
    except (FileNotFoundError, json.JSONDecodeError):
        return TodoList([])


def save_data(todo_list: TodoList) -> None:
    """Save TodoList data to JSON file.
    
    Args:
        todo_list (TodoList): TodoList to save
    """
    data = [todo.__dict__ for todo in todo_list.todos]
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
