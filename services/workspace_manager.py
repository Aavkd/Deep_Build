"""
Workspace Manager - File System State Management for DeepBuild

Manages the directory structure and file I/O for coding projects.
The file system is the source of truth for project state.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List


class WorkspaceManager:
    """
    Manages the DeepBuild workspace directory structure.
    
    Directory Structure:
        DeepBuild_Workspace/
        ├── {project_name}/
        │   ├── build_plan.md
        │   ├── build_report.md
        │   ├── project_info.json
        │   ├── code/
        │   │   ├── src/
        │   │   └── tests/
        │   └── run_logs/
        │       └── {timestamp}_run.log
        └── settings.json
    """
    
    def __init__(self, workspace_root: Optional[Path] = None):
        """
        Initialize the workspace manager.
        
        Args:
            workspace_root: Root directory for the workspace.
                           Defaults to ./DeepBuild_Workspace
        """
        if workspace_root is None:
            self.workspace_root = Path.cwd() / "DeepBuild_Workspace"
        else:
            self.workspace_root = Path(workspace_root)
        
        # Ensure workspace root exists
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        
        # Initialize settings if not exists
        self._init_settings()
    
    def _init_settings(self):
        """Initialize workspace settings file if it doesn't exist."""
        settings_path = self.workspace_root / "settings.json"
        
        if not settings_path.exists():
            default_settings = {
                "created_at": datetime.now().isoformat(),
                "version": "1.0.0",
                "default_model": "granite4:3b",
                "max_execution_timeout": 60
            }
            settings_path.write_text(
                json.dumps(default_settings, indent=2),
                encoding="utf-8"
            )
    
    def get_settings(self) -> Dict:
        """Get workspace settings."""
        settings_path = self.workspace_root / "settings.json"
        
        if settings_path.exists():
            return json.loads(settings_path.read_text(encoding="utf-8"))
        
        return {}
    
    def update_settings(self, updates: Dict):
        """Update workspace settings."""
        settings = self.get_settings()
        settings.update(updates)
        
        settings_path = self.workspace_root / "settings.json"
        settings_path.write_text(
            json.dumps(settings, indent=2),
            encoding="utf-8"
        )
    
    def init_project(self, project_name: str, user_query: Optional[str] = None) -> Path:
        """
        Initialize a new coding project with the required directory structure.
        
        Args:
            project_name: Name of the project (will be sanitized)
            user_query: Optional initial user query
            
        Returns:
            Path to the project directory
        """
        # Sanitize project name
        safe_name = self._sanitize_name(project_name)
        project_path = self.workspace_root / safe_name
        
        # Create directory structure for coding projects
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / "code").mkdir(exist_ok=True)
        (project_path / "code" / "src").mkdir(exist_ok=True)
        (project_path / "code" / "tests").mkdir(exist_ok=True)
        (project_path / "run_logs").mkdir(exist_ok=True)
        
        # Create project info file
        info_path = project_path / "project_info.json"
        if not info_path.exists():
            info = {
                "name": project_name,
                "safe_name": safe_name,
                "created_at": datetime.now().isoformat(),
                "user_query": user_query,
                "status": "initialized",
                "language": "python",  # Default, can be updated
                "framework": None
            }
            info_path.write_text(
                json.dumps(info, indent=2),
                encoding="utf-8"
            )
        
        return project_path
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize a project name for use as directory name."""
        import re
        # Replace spaces and special chars with underscores
        safe = re.sub(r'[^\w\-]', '_', name)
        # Remove consecutive underscores
        safe = re.sub(r'_+', '_', safe)
        # Remove leading/trailing underscores
        safe = safe.strip('_')
        # Limit length
        return safe[:100] if safe else "unnamed_project"
    
    def get_project_path(self, project_name: str) -> Path:
        """Get the path to a project directory."""
        safe_name = self._sanitize_name(project_name)
        project_path = self.workspace_root / safe_name
        
        if not project_path.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found")
        
        return project_path
    
    def project_exists(self, project_name: str) -> bool:
        """Check if a project exists."""
        safe_name = self._sanitize_name(project_name)
        return (self.workspace_root / safe_name).exists()
    
    def list_projects(self) -> List[Dict]:
        """List all projects in the workspace."""
        projects = []
        
        for path in self.workspace_root.iterdir():
            if path.is_dir() and not path.name.startswith('.'):
                info_path = path / "project_info.json"
                if info_path.exists():
                    try:
                        info = json.loads(info_path.read_text(encoding="utf-8"))
                        info["path"] = str(path)
                        projects.append(info)
                    except (json.JSONDecodeError, Exception):
                        projects.append({
                            "name": path.name,
                            "path": str(path),
                            "status": "unknown"
                        })
        
        return projects
    
    # =========================================================================
    # Build Plan Operations
    # =========================================================================
    
    def read_plan(self, project_name: str) -> Optional[str]:
        """Read the build plan for a project."""
        project_path = self.get_project_path(project_name)
        plan_path = project_path / "build_plan.md"
        
        if plan_path.exists():
            return plan_path.read_text(encoding="utf-8")
        
        return None
    
    def write_plan(self, project_name: str, content: str):
        """Write/update the build plan for a project."""
        project_path = self.get_project_path(project_name)
        plan_path = project_path / "build_plan.md"
        plan_path.write_text(content, encoding="utf-8")
        
        self._update_project_status(project_name, "planning")
    
    # =========================================================================
    # Build Report Operations
    # =========================================================================
    
    def read_report(self, project_name: str) -> Optional[str]:
        """Read the build report for a project."""
        project_path = self.get_project_path(project_name)
        report_path = project_path / "build_report.md"
        
        if report_path.exists():
            return report_path.read_text(encoding="utf-8")
        
        return None
    
    def write_report(self, project_name: str, content: str):
        """Write/update the build report for a project."""
        project_path = self.get_project_path(project_name)
        report_path = project_path / "build_report.md"
        report_path.write_text(content, encoding="utf-8")
        
        self._update_project_status(project_name, "building")
    
    # =========================================================================
    # Code Directory Operations
    # =========================================================================
    
    def get_code_dir(self, project_name: str) -> Path:
        """Get the code directory path for a project."""
        project_path = self.get_project_path(project_name)
        return project_path / "code"
    
    def get_src_dir(self, project_name: str) -> Path:
        """Get the source directory path for a project."""
        return self.get_code_dir(project_name) / "src"
    
    def get_tests_dir(self, project_name: str) -> Path:
        """Get the tests directory path for a project."""
        return self.get_code_dir(project_name) / "tests"
    
    # =========================================================================
    # Execution Logging
    # =========================================================================
    
    def get_run_logs_dir(self, project_name: str) -> Path:
        """Get the run logs directory path for a project."""
        project_path = self.get_project_path(project_name)
        return project_path / "run_logs"
    
    def log_execution(
        self,
        project_name: str,
        command: str,
        result: Dict,
        step_title: Optional[str] = None
    ) -> Path:
        """
        Log an execution result to the run_logs directory.
        
        Args:
            project_name: Name of the project
            command: Command that was executed
            result: Execution result dictionary
            step_title: Optional step title for context
            
        Returns:
            Path to the log file
        """
        logs_dir = self.get_run_logs_dir(project_name)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{timestamp}_run.log"
        log_path = logs_dir / log_filename
        
        log_content = f"""# Execution Log
**Timestamp:** {datetime.now().isoformat()}
**Command:** `{command}`
**Step:** {step_title or 'N/A'}
**Exit Code:** {result.get('exit_code', 'N/A')}
**Success:** {result.get('success', False)}
**Duration:** {result.get('duration_ms', 0)}ms

## STDOUT
```
{result.get('stdout', '')}
```

## STDERR
```
{result.get('stderr', '')}
```

## Error (if any)
{result.get('error', 'None')}
"""
        
        log_path.write_text(log_content, encoding="utf-8")
        return log_path
    
    def get_recent_logs(self, project_name: str, count: int = 5) -> List[Dict]:
        """
        Get the most recent execution logs for a project.
        
        Args:
            project_name: Name of the project
            count: Number of recent logs to retrieve
            
        Returns:
            List of log dictionaries with content and metadata
        """
        logs_dir = self.get_run_logs_dir(project_name)
        
        log_files = sorted(
            logs_dir.glob("*.log"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )[:count]
        
        logs = []
        for log_file in log_files:
            logs.append({
                "filename": log_file.name,
                "path": str(log_file),
                "content": log_file.read_text(encoding="utf-8"),
                "modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
            })
        
        return logs
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _update_project_status(self, project_name: str, status: str):
        """Update the project status in project_info.json."""
        project_path = self.get_project_path(project_name)
        info_path = project_path / "project_info.json"
        
        if info_path.exists():
            try:
                info = json.loads(info_path.read_text(encoding="utf-8"))
                info["status"] = status
                info["updated_at"] = datetime.now().isoformat()
                info_path.write_text(
                    json.dumps(info, indent=2),
                    encoding="utf-8"
                )
            except (json.JSONDecodeError, Exception):
                pass
    
    def get_project_info(self, project_name: str) -> Optional[Dict]:
        """Get project info dictionary."""
        try:
            project_path = self.get_project_path(project_name)
            info_path = project_path / "project_info.json"
            
            if info_path.exists():
                return json.loads(info_path.read_text(encoding="utf-8"))
        except Exception:
            pass
        
        return None
    
    def delete_project(self, project_name: str):
        """Delete a project and all its contents."""
        import shutil
        
        project_path = self.get_project_path(project_name)
        shutil.rmtree(project_path)
