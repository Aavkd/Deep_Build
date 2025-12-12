"""
Core functionality module for Todo application.

This module provides the main operations for managing Todo items.
"""

from .models import TodoList, Todo
from .storage import load_data, save_data


def add_todo(todo_list: TodoList, title: str) -> TodoList:
    """
    Add a new todo item to the todo list.

    Args:
        todo_list (TodoList): The todo list to add to
        title (str): Title of the new todo

    Returns:
        TodoList: The updated todo list with new item
    """
    new_todo = Todo(id=len(todo_list.todos) + 1, title=title)
    todo_list.todos.append(new_todo)
    return todo_list


def complete_todo(todo_list: TodoList, todo_id: int) -> TodoList:
    """
    Mark a todo item as completed.

    Args:
        todo_list (TodoList): The todo list to update
        todo_id (int): ID of the todo to complete

    Returns:
        TodoList: The updated todo list
    """
    for todo in todo_list.todos:
        if todo.id == todo_id:
            todo.completed = True
    return todo_list


def delete_todo(todo_list: TodoList, todo_id: int) -> TodoList:
    """
    Remove a todo item from the todo list.

    Args:
        todo_list (TodoList): The todo list to update
        todo_id (int): ID of the todo to delete

    Returns:
        TodoList: The updated todo list
    """
    todo_list.todos = [todo for todo in todo_list.todos if todo.id != todo_id]
    return todo_list


# Helper function to save the updated todo list after modifications

def save_and_return(todo_list: TodoList) -> TodoList:
    """
    Save the todo list and return it.

    Args:
        todo_list (TodoList): The todo list to save

    Returns:
        TodoList: The saved todo list
    """
    save_data(todo_list)
    return todo_list