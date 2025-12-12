# Task Management Module

import json

class Task:
    """Represents a single task."""
    def __init__(self, title: str, completed: bool = False):
        self.title = title
        self.completed = completed
    
    def toggle_completion(self) -> None:
        """Toggle the completion status of the task."""
        self.completed = not self.completed
    
    def to_dict(self) -> dict:
        return {
            'title': self.title,
            'completed': self.completed
        }

class TaskManager:
    """Manages a list of tasks."""
    
    def __init__(self):
        self.tasks = []
    
    def add_task(self, title: str) -> None:
        """Add a new task with the given title."""
        task = Task(title)
        self.tasks.append(task)
    
    def list_tasks(self) -> list[dict]:
        """Return all tasks as a list of dictionaries."""
        return [task.to_dict() for task in self.tasks]
    
    def remove_task(self, title: str) -> None:
        """Remove the task with the specified title."""
        self.tasks = [task for task in self.tasks if task.title != title]
    
    def save_to_file(self, filename: str) -> None:
        """Save tasks to a JSON file."""
        data = json.dumps([task.to_dict() for task in self.tasks], indent=4)
        with open(filename, 'w') as f:
            f.write(data)
    
    def load_from_file(self, filename: str) -> None:
        """Load tasks from a JSON file."""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.tasks = [Task(task['title'], task['completed']) for task in data]
        except FileNotFoundError:
            pass

def main_function(args: list[str]) -> None:
    """Entry point function for the todo_module."""
    if not args:
        print(json.dumps({'error': 'No command provided'}, indent=2))
        return
    cmd = args[0]
    
    if cmd == 'add' and len(args) >= 3:
        title = args[1]
        task_manager.add_task(title)
        print(json.dumps({'message': f'Task added: {title}'}, indent=2))
    elif cmd == 'list':
        tasks = task_manager.list_tasks()
        print(json.dumps(tasks, indent=2))
    elif cmd == 'remove' and len(args) >= 3:
        title = args[1]
        task_manager.remove_task(title)
        print(json.dumps({'message': f'Task removed: {title}'}, indent=2))
    elif cmd == 'save' and len(args) >= 2:
        filename = args[1]
        task_manager.save_to_file(filename)
        print(json.dumps({'message': f'Tasks saved to {filename}'}, indent=2))
    elif cmd == 'load' and len(args) >= 2:
        filename = args[1]
        task_manager.load_from_file(filename)
        print(json.dumps({'message': f'Tasks loaded from {filename}'}, indent=2))
    else:
        print(json.dumps({'error': 'Invalid command or arguments'}, indent=2))