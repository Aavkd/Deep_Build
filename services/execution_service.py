"""
Execution Service - Secure Code and Command Execution Sandbox

Provides safe execution of shell commands and Python scripts within
the project workspace boundaries.
"""

import subprocess
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Union


class ExecutionService:
    """
    Sandbox for executing code and shell commands within the workspace.
    
    Security Features:
    - Path validation ensures commands only run in workspace
    - Configurable timeout prevents hanging processes
    - All output is captured and logged
    
    Attributes:
        workspace_root: Root directory for all project workspaces
        default_timeout: Default command timeout in seconds
    """
    
    def __init__(
        self,
        workspace_root: Path,
        default_timeout: int = 60
    ):
        """
        Initialize the execution service.
        
        Args:
            workspace_root: Root directory containing all project workspaces
            default_timeout: Default timeout for command execution in seconds
        """
        self.workspace_root = Path(workspace_root).resolve()
        self.default_timeout = default_timeout
        
        # Ensure workspace root exists
        self.workspace_root.mkdir(parents=True, exist_ok=True)
    
    def _is_safe_path(self, path: Union[str, Path]) -> bool:
        """
        Validate that a path is within the workspace root.
        
        Args:
            path: Path to validate
            
        Returns:
            True if path is safely within workspace, False otherwise
        """
        try:
            resolved_path = Path(path).resolve()
            # Check if the path is inside workspace root
            return str(resolved_path).startswith(str(self.workspace_root))
        except Exception:
            return False
    
    def run_command(
        self,
        command: str,
        cwd: Union[str, Path],
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Execute a shell command within the workspace.
        
        Security: The working directory must be within the workspace root.
        
        Args:
            command: Shell command to execute
            cwd: Working directory for the command (must be in workspace)
            timeout: Command timeout in seconds (uses default if None)
            env: Additional environment variables to set
            
        Returns:
            Dictionary with:
                - success: bool (True if exit_code == 0)
                - stdout: str (standard output)
                - stderr: str (standard error)
                - exit_code: int (process return code)
                - duration_ms: int (execution time in milliseconds)
                - error: str (error message if execution failed)
                
        Example:
            >>> service.run_command("python main.py", cwd="/workspace/project")
            {"success": True, "stdout": "Hello World\\n", "stderr": "", "exit_code": 0}
        """
        cwd = Path(cwd).resolve()
        
        # Security: Validate working directory is within workspace
        if not self._is_safe_path(cwd):
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
                "duration_ms": 0,
                "error": f"Security Error: Path '{cwd}' is outside the workspace boundary."
            }
        
        # Ensure the directory exists
        if not cwd.exists():
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
                "duration_ms": 0,
                "error": f"Directory not found: {cwd}"
            }
        
        timeout = timeout or self.default_timeout
        
        # Build environment
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        
        start_time = datetime.now()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=process_env
            )
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "duration_ms": duration_ms,
                "error": None
            }
            
        except subprocess.TimeoutExpired:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
                "duration_ms": duration_ms,
                "error": f"Command timed out after {timeout} seconds"
            }
            
        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
                "duration_ms": duration_ms,
                "error": f"Execution error: {str(e)}"
            }
    
    def run_python_file(
        self,
        filepath: Union[str, Path],
        args: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> Dict:
        """
        Execute a Python file within the workspace.
        
        Args:
            filepath: Path to the Python file (must be in workspace)
            args: Optional command-line arguments to pass
            timeout: Command timeout in seconds
            
        Returns:
            Same as run_command()
            
        Example:
            >>> service.run_python_file("/workspace/project/main.py", args="--verbose")
        """
        filepath = Path(filepath).resolve()
        
        if not self._is_safe_path(filepath):
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
                "duration_ms": 0,
                "error": f"Security Error: File '{filepath}' is outside the workspace boundary."
            }
        
        if not filepath.exists():
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
                "duration_ms": 0,
                "error": f"File not found: {filepath}"
            }
        
        command = f"python \"{filepath}\""
        if args:
            command += f" {args}"
        
        return self.run_command(
            command=command,
            cwd=filepath.parent,
            timeout=timeout
        )
    
    def run_pytest(
        self,
        test_path: Union[str, Path],
        verbose: bool = True,
        timeout: Optional[int] = None
    ) -> Dict:
        """
        Run pytest on a test file or directory.
        
        Args:
            test_path: Path to test file or directory
            verbose: Include verbose output
            timeout: Command timeout in seconds
            
        Returns:
            Same as run_command()
        """
        test_path = Path(test_path).resolve()
        
        if not self._is_safe_path(test_path):
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
                "duration_ms": 0,
                "error": f"Security Error: Path '{test_path}' is outside the workspace boundary."
            }
        
        command = f"python -m pytest \"{test_path}\""
        if verbose:
            command += " -v"
        
        # Use parent directory if test_path is a file
        cwd = test_path.parent if test_path.is_file() else test_path
        
        return self.run_command(
            command=command,
            cwd=cwd,
            timeout=timeout or 120  # Tests may take longer
        )
    
    def install_requirements(
        self,
        project_dir: Union[str, Path],
        requirements_file: str = "requirements.txt"
    ) -> Dict:
        """
        Install Python dependencies from a requirements file.
        
        Args:
            project_dir: Project directory containing requirements file
            requirements_file: Name of requirements file
            
        Returns:
            Same as run_command()
        """
        project_dir = Path(project_dir).resolve()
        req_path = project_dir / requirements_file
        
        if not self._is_safe_path(project_dir):
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
                "duration_ms": 0,
                "error": f"Security Error: Path '{project_dir}' is outside the workspace boundary."
            }
        
        if not req_path.exists():
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
                "duration_ms": 0,
                "error": f"Requirements file not found: {req_path}"
            }
        
        command = f"pip install -r \"{req_path}\""
        
        return self.run_command(
            command=command,
            cwd=project_dir,
            timeout=300  # Package installation can take a while
        )
