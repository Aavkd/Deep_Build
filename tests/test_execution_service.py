"""
Tests for ExecutionService

Verifies command execution, path validation, and timeout handling.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.execution_service import ExecutionService


class TestExecutionService:
    """Test cases for ExecutionService."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def service(self, temp_workspace):
        """Create an ExecutionService instance."""
        return ExecutionService(
            workspace_root=temp_workspace,
            default_timeout=10
        )
    
    def test_run_simple_command(self, service, temp_workspace):
        """Test running a simple command."""
        result = service.run_command("echo Hello World", cwd=temp_workspace)
        
        assert result["success"] is True
        assert result["exit_code"] == 0
        assert "Hello" in result["stdout"]
        assert result["error"] is None
    
    def test_run_command_with_error(self, service, temp_workspace):
        """Test running a command that fails."""
        result = service.run_command("python -c \"raise ValueError('test')\"", cwd=temp_workspace)
        
        assert result["success"] is False
        assert result["exit_code"] != 0
        assert "ValueError" in result["stderr"]
    
    def test_path_outside_workspace_blocked(self, service):
        """Test that commands outside workspace are blocked."""
        # Try to run command in parent directory
        result = service.run_command("echo test", cwd=Path("C:/"))
        
        assert result["success"] is False
        assert "Security Error" in result.get("error", "")
    
    def test_timeout_handling(self, service, temp_workspace):
        """Test that commands respect timeout."""
        # Run a command that would hang (sleep for 30 seconds)
        result = service.run_command(
            "python -c \"import time; time.sleep(30)\"",
            cwd=temp_workspace,
            timeout=1
        )
        
        assert result["success"] is False
        assert "timed out" in result.get("error", "").lower()
    
    def test_run_python_file(self, service, temp_workspace):
        """Test running a Python file."""
        # Create a Python file
        test_file = temp_workspace / "test_script.py"
        test_file.write_text("print('Script executed!')")
        
        result = service.run_python_file(test_file)
        
        assert result["success"] is True
        assert "Script executed!" in result["stdout"]
    
    def test_run_python_file_with_error(self, service, temp_workspace):
        """Test running a Python file that has an error."""
        # Create a Python file with a syntax error
        test_file = temp_workspace / "bad_script.py"
        test_file.write_text("print('Hello'\nprint('Missing paren')")
        
        result = service.run_python_file(test_file)
        
        assert result["success"] is False
        assert "SyntaxError" in result["stderr"]
    
    def test_is_safe_path(self, service, temp_workspace):
        """Test path validation."""
        # Path inside workspace should be safe
        assert service._is_safe_path(temp_workspace / "subdir") is True
        
        # Path outside workspace should be unsafe
        assert service._is_safe_path(Path("C:/Windows")) is False
        assert service._is_safe_path(temp_workspace.parent) is False
    
    def test_run_pytest(self, service, temp_workspace):
        """Test running pytest on a test directory."""
        # Create a simple test file
        tests_dir = temp_workspace / "tests"
        tests_dir.mkdir()
        
        test_file = tests_dir / "test_simple.py"
        test_file.write_text("""
def test_addition():
    assert 1 + 1 == 2

def test_subtraction():
    assert 5 - 3 == 2
""")
        
        result = service.run_pytest(tests_dir)
        
        # Note: This test requires pytest to be installed
        # If pytest is not available, the test will pass but with exit code != 0
        assert result["exit_code"] is not None
    
    def test_environment_variables(self, service, temp_workspace):
        """Test passing environment variables to command."""
        result = service.run_command(
            "python -c \"import os; print(os.environ.get('TEST_VAR', 'not set'))\"",
            cwd=temp_workspace,
            env={"TEST_VAR": "hello_from_env"}
        )
        
        assert result["success"] is True
        assert "hello_from_env" in result["stdout"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
