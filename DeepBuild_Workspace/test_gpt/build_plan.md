# 🏗️ Build Plan

**Date:** 2025-12-12  
**Project:** CLI Todo App  
**Type:** Application  
**Language:** Python

---

## 1. Project Overview

> A command-line interface (CLI) Todo application that allows users to add, list, complete, and delete tasks. Tasks are persisted in a local JSON file. The application uses the `click` library for CLI handling and `pytest` for testing.

### Success Criteria
- [ ] The CLI supports `add`, `list`, `complete`, and `delete` commands with appropriate arguments.
- [ ] Tasks are stored persistently in `~/.todo_app/tasks.json`.
- [ ] All unit tests pass, ensuring correct functionality of each command.

### Tech Stack
- **Language:** Python
- **Dependencies:** click, pytest
- **Testing:** pytest

---

## 2. File Structure

```
cli_todo_app/
├── src/
│   ├── __init__.py
│   ├── todo.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_todo.py
│   └── test_main.py
├── requirements.txt
└── README.md
```

---

## 3. Execution Steps

### Phase 1: Setup

- [x] **Step 1.1: Create requirements.txt**
    - *File:* `requirements.txt`
    - *Description:* List all Python dependencies needed for the project.

- [x] **Step 1.2: Install dependencies**
    - *Command:* `pip install -r requirements.txt`

### Phase 2: Core Implementation

- [x] **Step 2.1: Create todo module**
    - *File:* `src/todo.py`
    - *Description:*  
        - Define `TodoItem` dataclass with `id`, `description`, `completed`.  
        - Implement `TodoManager` class to load/save tasks from/to JSON file.  
        - Provide methods: `add_task`, `list_tasks`, `complete_task`, `delete_task`.

- [x] **Step 2.2: Create CLI entry point**
    - *File:* `src/main.py`
    - *Description:*  
        - Use `click` to create a group `cli`.  
        - Add commands: `add`, `list`, `complete`, `delete` that delegate to `TodoManager`.  
        - Include helpful help text and error handling.

- [x] **Step 2.3: Create package initializer**
    - *File:* `src/__init__.py`
    - *Description:* Empty file to make `src` a package.

### Phase 3: Testing

- [x] **Step 3.1: Create unit tests for todo logic**
    - *File:* `tests/test_todo.py`
    - *Description:*  
        - Test adding, listing, completing, and deleting tasks.  
        - Use a temporary file or mock the file system to avoid modifying real data.

- [x] **Step 3.2: Create integration tests for CLI**
    - *File:* `tests/test_main.py`
    - *Description:*  
        - Use `click.testing.CliRunner` to invoke CLI commands.  
        - Verify correct output and side effects.

- [x] **Step 3.3: Create package initializer for tests**
    - *File:* `tests/__init__.py`
    - *Description:* Empty file to make `tests` a package.

- [ ] **Step 3.4: Run tests**
    - *Command:* `python -m pytest tests/ -v`
    - *Expected:* All tests pass with no failures.

### Phase 4: Verification

- [ ] **Step 4.1: Run application manually**
    - *Command:* `python src/main.py --help`
    - *Expected:* Help message displays all commands.

- [ ] **Step 4.2: Add a sample task**
    - *Command:* `python src/main.py add "Buy milk"`
    - *Expected:* Confirmation message indicating task added.

- [ ] **Step 4.3: List tasks**
    - *Command:* `python src/main.py list`
    - *Expected:* Displays the newly added task with its ID and status.

- [ ] **Step 4.4: Complete the task**
    - *Command:* `python src/main.py complete 1`
    - *Expected:* Confirmation message indicating task marked as completed.

- [ ] **Step 4.5: Delete the task**
    - *Command:* `python src/main.py delete 1`
    - *Expected:* Confirmation message indicating task removed.

- [ ] **Step 4.6: Verify persistence**
    - *Command:* `python src/main.py list`
    - *Expected:* No tasks listed (since the only task was deleted).

---

## 4. Notes

- The application stores tasks in `~/.todo_app/tasks.json`. Ensure the directory exists or create it at runtime.  
- Use `pathlib` for cross-platform path handling.  
- Consider adding a `--verbose` flag for detailed output during debugging.  
- Edge cases: attempting to complete or delete a non-existent task should produce a user-friendly error.  
- Future enhancements: support task priorities, due dates, or tagging.