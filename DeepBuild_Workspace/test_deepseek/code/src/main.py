import click
from todo_manager import TodoManager

@click.group()
def cli():
    pass

@cli.command()
@click.option('--task', prompt='Enter task description', help='Task to be added.')
def add(task):
    """Add a new task."""
    manager = TodoManager('tasks.txt')
    manager.add_task(task)

@cli.command()
def view():
    """View all tasks."""
    manager = TodoManager('tasks.txt')
    tasks = manager.view_tasks()
    for task in tasks:
        print(f'- {task}')

# Add more commands as needed (update, delete)

if __name__ == '__main__':
    cli()