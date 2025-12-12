```markdown
# 🏗️ Build Plan

**Date:** 2025-12-12
**Project:** CLI Todo Application
**Type:** Full Application
**Language:** Python

---

## 1. Project Overview

A command-line interface for managing todo items with persistence. Features:
- Add, view, complete, delete todos
- Save state to JSON file
- Basic CLI commands

### Success Criteria
- [ ] All CLI commands work as specified
- [ ] Todo data persists between sessions
- [ ] Clean, modular code structure
- [ ] Proper error handling

### Tech Stack
- **Language:** Python 3.8+
- **Dependencies:** `click` (CLI), `typer` (alternative), `rich` (optional for UI)
- **Persistence:** JSON file format
- **Testing:** `pytest`

---

## 2. File Structure

```
todo_app/
├── src/
│   ├── __init__.py
│   ├── cli.py          # Main CLI interface
│   ├── core.py         # Core todo logic
│   ├── storage.py      # Data persistence
│   └── models.py       # Data models
├── tests/
│   ├── test_cli.py
│   ├── test_core.py
│   └── test_storage.py
├── requirements.txt
├── todo.json           # Sample data file
└── README.md
```

---

## 3. Execution Steps

### Phase 1: Environment Setup

- [x] **Step 1.1: Create project directory**
    - *Command:* `mkdir todo_app && cd todo_app`
    - *Expected:* Directory created

- [x] **Step 1.2: Create requirements.txt**
    - *File:* `requirements.txt`
    - *Description:*
      ```
      click==8.1.3
      pytest==7.4.0
      ```

- [x] **Step 1.3: Install dependencies**
    - *Command:* `pip install -r requirements.txt`

### Phase 2: Core Implementation

#### Core Models
- [x] **Step 2.1: Create models.py**
    - *File:* `src/models.py`
    - *Description:*
      ```python
      from dataclasses import dataclass
      from datetime import datetime

      @dataclass
      class Todo:
          id: int
          title: str
          completed: bool = False
          created_at: datetime = datetime.now()

      @dataclass
      class TodoList:
          todos: list[Todo]
      ```

#### Data Storage
- [x] **Step 2.2: Create storage.py**
    - *File:* `src/storage.py`
    - *Description:*
      ```python
      import json
      from pathlib import Path
      from typing import Optional
      from .models import TodoList

      DATA_FILE = Path(__file__).parent / "todo.json"

      def load_data() -> TodoList:
          try:
              with open(DATA_FILE) as f:
                  data = json.load(f)
              return TodoList([Todo(**item) for item in data])
          except (FileNotFoundError, json.JSONDecodeError):
              return TodoList([])

      def save_data(todo_list: TodoList) -> None:
          data = [todo.__dict__ for todo in todo_list.todos]
          with open(DATA_FILE, "w") as f:
              json.dump(data, f, indent=2)
      ```

#### Core Logic
- [x] **Step 2.3: Create core.py**
    - *File:* `src/core.py`
    - *Description:*
      ```python
      from .models import TodoList, Todo
      from .storage import load_data, save_data

      def add_todo(todo_list: TodoList, title: str) -> TodoList:
          new_todo = Todo(id=len(todo_list.todos) + 1, title=title)
          todo_list.todos.append(new_todo)
          return todo_list

      def complete_todo(todo_list: TodoList, todo_id: int) -> TodoList:
          for todo in todo_list.todos:
              if todo.id == todo_id:
                  todo.completed = True
          return todo_list

      def delete_todo(todo_list: TodoList, todo_id: int) -> TodoList:
          todo_list.todos = [todo for todo in todo_list.todos if todo.id != todo_id]
          return todo_list
      ```

#### CLI Interface
- [x] **Step 2.4: Create cli.py**
    - *File:* `src/cli.py`
    - *Description:*
      ```python
      import click
      from .core import add_todo, complete_todo, delete_todo
      from .storage import load_data, save_data
      from .models import TodoList

      @click.group()
      def cli():
          pass

      @cli.command()
      def list():
          todo_list = load_data()
          for todo in todo_list.todos:
              status = "✓" if todo.completed else " "
              click.echo(f"[{status}] {todo.id}: {todo.title}")
          click.echo(f"Total: {len(todo_list.todos)} todos")

      @cli.command()
      @click.argument("title")
      def add(title):
          todo_list = load_data()
          todo_list = add_todo(todo_list, title)
          save_data(todo_list)
          click.echo(f"Added: {title}")

      @cli.command()
      @click.argument("todo_id")
      def complete(todo_id):
          todo_list = load_data()
          todo_list = complete_todo(todo_list, int(todo_id))
          save_data(todo_list)
          click.echo(f"Completed todo {todo_id}")

      @cli.command()
      @click.argument("todo_id")
      def delete(todo_id):
          todo_list = load_data()
          todo_list = delete_todo(todo_list, int(todo_id))
          save_data(todo_list)
          click.echo(f"Deleted todo {todo_id}")

      if __name__ == "__main__":
          cli()
      ```

- [x] **Step 2.5: Create __init__.py**
    - *File:* `src/__init__.py`
    - *Description:* Empty file to make src a package

### Phase 3: Testing

- [ ] **Step 3.1: Create test directory structure**
    - *Command:* `mkdir -p tests/{test_cli,test_core,test_storage}`

- [ ] **Step 3.2: Create test_storage.py**
    - *File:* `tests/test_storage.py`
    - *Description:*
      ```python
      import pytest
      import json
      from pathlib import Path
      from src.storage import load_data, save_data
      from src.models import TodoList

      @pytest.fixture
      def temp_json_file(tmp_path):
          return tmp_path / "test.json"

      def test_load_empty_file(temp_json_file):
          with open(temp_json_file, "w") as f:
              json.dump([], f)
          data = load_data()
          assert len(data.todos) == 0

      def test_save_and_load_data(temp_json_file):
          todo_list = TodoList([
              {"id": 1, "title": "Test", "completed": False}
          ])
          save_data(todo_list, temp_json_file)
          loaded = load_data()
          assert len(loaded.todos) == 1
      ```

- [ ] **Step 3.3: Create test_core.py**
    - *File:* `tests/test_core.py`
    - *Description:*
      ```python
      from src.core import add_todo, complete_todo, delete_todo
      from src.models import TodoList

      def test_add_todo():
          todo_list = TodoList([])
          todo_list = add_todo(todo_list, "Test")
          assert len(todo_list.todos) == 1
          assert todo_list.todos[0].title == "Test"

      def test_complete_todo():
          todo_list = TodoList([{"id": 1, "title": "Test", "completed": False}])
          todo_list = complete_todo(todo_list, 1)
          assert todo_list.todos[0].completed is True

      def test_delete_todo():
          todo_list = TodoList([{"id": 1, "title": "Test"}, {"id": 2, "title": "Other"}])
          todo_list = delete_todo(todo_list, 1)
          assert len(todo_list.todos) == 1
          assert todo_list.todos[0].id == 2
      ```

- [ ] **Step 3.4: Create test_cli.py**
    - *File:* `tests/test_cli.py`
    - *Description:* (Would use pytest-capture for CLI testing)

- [ ] **Step 3.5: Run tests**
    - *Command:* `pytest tests/ -v`
    - *Expected:* All tests pass

### Phase 4: Integration & Final Verification

- [ ] **Step 4.1: Create sample data file**
    - *File:* `todo.json`
    - *Description:* Empty JSON array `[]`

- [ ] **Step 4.2: Create README.md**
    - *File:* `README.md`
    - *Description:*
      ```markdown
      # CLI Todo App

      A simple todo list manager with CLI interface.

      ## Usage

      ```bash
      python -m src.cli add "Buy groceries"
      python -m src.cli list
      python -m src.cli complete 1
      python -m src.cli delete 2
      ```

      ## Commands

      - `list`: Show all todos
      - `add <title>`: Create new todo
      - `complete <id>`: Mark todo as completed
      - `delete <id>`: Remove todo
      ```

- [ ] **Step 4.3: Verify CLI functionality**
    - *Command:* `python -m src.cli --help`
    - *Expected:* Help menu shows all commands

- [ ] **Step 4.4: Test complete workflow**
    - *Commands:*
      ```bash
      python -m src.cli add "Test todo"
      python -m src.cli list
      python -m src.cli complete 1
      python -m src.cli list
      python -m src.cli delete 1
      python -m src.cli list
      ```
    - *Expected:* All commands execute without errors

---

## 4. Notes

1. **Data Persistence**: The app saves state to `todo.json` in the project root. Ensure this file isn't deleted accidentally.

2. **Error Handling**: Basic error handling is included but could be enhanced for production use.

3. **Testing**: The test suite covers core functionality. Add more edge cases (empty inputs, invalid IDs) as needed.

4. **Dependencies**: Uses `click` for CLI which is a common choice for Python CLI apps.

5. **Alternatives**: For a more feature-rich CLI, consider using `typer` instead of `click`.

6. **Future Extensions**:
   - Add due dates to todos
   - Implement categories/tags
   - Add CLI history
   - Support YAML/JSON config for CLI options
```