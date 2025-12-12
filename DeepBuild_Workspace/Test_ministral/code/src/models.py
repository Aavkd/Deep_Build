"""
Module containing data models for the Todo application.

This file defines the core data structures using Python dataclasses.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Todo:
    """
    Represents a single todo item with basic properties.
    
    Attributes:
        id (int): Unique identifier for the todo
        title (str): Description of the todo task
        completed (bool): Task completion status
        created_at (datetime): When the todo was created
    """
    id: int
    title: str
    completed: bool = False
    created_at: datetime = datetime.now()


@dataclass
class TodoList:
    """
    Container for a collection of Todo items.
    
    Attributes:
        todos (list[Todo]): Collection of Todo items
    """
    todos: list[Todo]
