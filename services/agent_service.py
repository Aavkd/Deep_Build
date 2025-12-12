"""
Agent Service - Build Plan Orchestration + Execution Loop

Orchestrates the coding workflow by:
1. Generating build plans from user queries
2. Parsing plans to find unchecked steps
3. Executing steps (create files, run commands, fix errors)
4. Updating plans and reports
"""

import re
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple

from .llm_service import LLMService
from .execution_service import ExecutionService
from .workspace_manager import WorkspaceManager
from .file_tools import FileTools


class AgentService:
    """
    Orchestrates the autonomous coding agent workflow.
    
    Responsibilities:
    - Generate build plans from user queries
    - Parse plans to find unchecked steps
    - Execute steps (create/edit files, run commands)
    - Handle errors with auto-fix loop
    - Update plans and reports
    """
    
    def __init__(
        self,
        workspace_manager: WorkspaceManager,
        llm_service: LLMService,
        execution_service: ExecutionService,
        prompts_dir: Optional[Path] = None
    ):
        """
        Initialize the agent service.
        
        Args:
            workspace_manager: WorkspaceManager instance
            llm_service: LLMService instance
            execution_service: ExecutionService instance
            prompts_dir: Path to PROMPTS directory
        """
        self.workspace = workspace_manager
        self.llm = llm_service
        self.execution = execution_service
        self.file_tools = FileTools()
        
        if prompts_dir is None:
            self.prompts_dir = Path.cwd() / "PROMPTS"
        else:
            self.prompts_dir = Path(prompts_dir)
        
        # Max retry attempts for error fixing
        self.max_fix_attempts = 3
    
    # =========================================================================
    # Prompt Loading
    # =========================================================================
    
    def _load_architect_prompt(self) -> str:
        """Load the engineering architect prompt."""
        prompt_path = self.prompts_dir / "Engineering_Architect_Prompt.md"
        
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        
        # Fallback inline prompt
        return """You are a Senior Software Architect. Generate a build plan with:
- Step-by-step file creation and command execution
- Use [ ] checkbox format for steps
- Include *File:* or *Command:* markers for each step
Output ONLY the Markdown plan starting with # 🏗️ Build Plan"""
    
    def _load_developer_prompt(self) -> str:
        """Load the engineering developer prompt."""
        prompt_path = self.prompts_dir / "Engineering_Developer_Prompt.md"
        
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        
        # Fallback inline prompt
        return """You are a Senior Developer. Execute the given step by outputting JSON:
For file creation: {"action": "create_file", "path": "...", "content": "..."}
For file modification: {"action": "str_replace", "path": "...", "old_str": "...", "new_str": "..."}
For command steps: {"action": "none", "message": "..."}
Output ONLY valid JSON."""
    
    # =========================================================================
    # Plan Generation
    # =========================================================================
    
    def generate_plan(self, project_name: str, user_query: str) -> str:
        """
        Generate a build plan for a project.
        
        Args:
            project_name: Name of the project
            user_query: User's build request
            
        Returns:
            Generated plan content
        """
        # Load the architect prompt template
        prompt_template = self._load_architect_prompt()
        
        # Fill in template variables
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        system_prompt = prompt_template.replace("{{CURRENT_DATE}}", current_date)
        system_prompt = system_prompt.replace("{{USER_QUERY}}", user_query)
        system_prompt = system_prompt.replace("{{LANGUAGE}}", "Python")
        
        user_prompt = f"""Please generate a comprehensive build plan for the following request:

**User Request:** {user_query}

Remember to:
1. Break down the task into granular, testable steps
2. Use `- [ ]` checkbox format for steps
3. Include `*File:*` for file creation steps
4. Include `*Command:*` for command execution steps
5. Follow the template structure exactly
6. Output ONLY the Markdown content, starting with `# 🏗️ Build Plan`"""
        
        # Generate the plan
        plan_content = self.llm.generate(system_prompt, user_prompt, temperature=0.7)
        
        # Clean up the response
        plan_content = self._clean_llm_output(plan_content)
        
        # Ensure the plan has required structure
        if "# 🏗️ Build Plan" not in plan_content and "# Build Plan" not in plan_content:
            plan_content = f"# 🏗️ Build Plan\n\n{plan_content}"
        
        # Save the plan
        self.workspace.write_plan(project_name, plan_content)
        
        return plan_content
    
    def _clean_llm_output(self, content: str) -> str:
        """Clean LLM output by removing code block markers."""
        content = re.sub(r'^```(?:markdown|md|json)?\\s*\\n?', '', content, flags=re.MULTILINE)
        content = re.sub(r'\\n?```\\s*$', '', content, flags=re.MULTILINE)
        return content.strip()
    
    # =========================================================================
    # Plan Parsing
    # =========================================================================
    
    def parse_plan_steps(self, plan_content: str) -> List[Dict]:
        """
        Parse a build plan to extract all steps.
        
        Args:
            plan_content: Plan Markdown content
            
        Returns:
            List of step dictionaries
        """
        steps = []
        
        # Pattern: - [ ] or - [x] followed by **Step content**
        checkbox_pattern = r'- \[([ x])\] \*\*(.+?)\*\*\s*(.*?)(?=(?:- \[[ x]\]|### |## |\Z))'
        matches = list(re.finditer(checkbox_pattern, plan_content, re.DOTALL))
        
        for match in matches:
            is_checked = match.group(1) == 'x'
            step_title = match.group(2).strip()
            step_content = match.group(3).strip()
            
            # Determine step type
            step_type = self._determine_step_type(step_content)
            
            # Extract file path if present
            file_match = re.search(r'\*File:\*\s*`?([^`\n]+)`?', step_content)
            file_path = file_match.group(1).strip() if file_match else None
            
            # Extract command if present
            cmd_match = re.search(r'\*Command:\*\s*`?([^`\n]+)`?', step_content)
            command = cmd_match.group(1).strip() if cmd_match else None
            
            # Extract description
            desc_match = re.search(r'\*Description:\*\s*(.+?)(?=\n\*|\Z)', step_content, re.DOTALL)
            description = desc_match.group(1).strip() if desc_match else ""
            
            steps.append({
                "checked": is_checked,
                "title": step_title,
                "type": step_type,
                "file_path": file_path,
                "command": command,
                "description": description,
                "raw_content": step_content
            })
        
        print(f"[Agent] Parsed {len(steps)} steps from plan")
        return steps
    
    def _determine_step_type(self, step_content: str) -> str:
        """Determine the type of step based on content markers."""
        if '*File:*' in step_content or '**File:**' in step_content:
            return "file"
        elif '*Command:*' in step_content or '**Command:**' in step_content:
            return "command"
        elif '*Action:*' in step_content or '**Action:**' in step_content:
            return "command"
        else:
            return "other"
    
    def find_next_unchecked_step(self, plan_content: str) -> Optional[Dict]:
        """Find the first unchecked step in the plan."""
        steps = self.parse_plan_steps(plan_content)
        
        for step in steps:
            if not step["checked"]:
                return step
        
        return None
    
    def mark_step_complete(self, plan_content: str, step_title: str) -> str:
        """Mark a step as complete in the plan."""
        escaped_title = re.escape(step_title)
        
        # Replace [ ] with [x]
        pattern = rf'(- \[) (\] \*\*{escaped_title}\*\*)'
        replacement = r'\1x\2'
        
        return re.sub(pattern, replacement, plan_content)
    
    # =========================================================================
    # Step Execution
    # =========================================================================
    
    def execute_next_step(self, project_name: str) -> Dict:
        """
        Execute the next unchecked step in the build plan.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Dictionary with execution results
        """
        # Read the current plan
        plan_content = self.workspace.read_plan(project_name)
        
        if plan_content is None:
            return {
                "success": False,
                "error": "No build plan found. Generate a plan first.",
                "step": None
            }
        
        # Find the next unchecked step
        step = self.find_next_unchecked_step(plan_content)
        
        if step is None:
            # All steps complete - finalize the report
            print("[Agent] All build steps complete. Finalizing report...")
            self._finalize_report(project_name)
            
            return {
                "success": True,
                "completed": True,
                "message": "All steps in the plan have been completed.",
                "step": None
            }
        
        print(f"[Agent] Executing step: {step['title']}")
        
        # Execute based on step type
        if step["type"] == "file":
            result = self._execute_file_step(project_name, step)
        elif step["type"] == "command":
            result = self._execute_command_step(project_name, step)
        else:
            # For other step types, just mark complete
            result = {"success": True, "message": "Step marked complete"}
        
        # If successful, mark step complete
        if result.get("success"):
            updated_plan = self.mark_step_complete(plan_content, step["title"])
            self.workspace.write_plan(project_name, updated_plan)
        
        return {
            "success": result.get("success", False),
            "completed": False,
            "step": step,
            "result": result,
            "message": result.get("message", "Step executed")
        }
    
    def _execute_file_step(self, project_name: str, step: Dict) -> Dict:
        """
        Execute a file creation/modification step.
        
        Uses LLM to generate the file content based on step description.
        """
        code_dir = self.workspace.get_code_dir(project_name)
        
        # Get existing file context
        file_context = self._get_project_file_context(project_name)
        
        # Load developer prompt
        system_prompt = self._load_developer_prompt()
        
        # Build user prompt
        user_prompt = f"""Execute this build step:

**Step Title:** {step['title']}
**File to Create/Modify:** {step.get('file_path', 'N/A')}
**Description:** {step.get('description', step.get('raw_content', ''))}

**Existing Project Files:**
{file_context}

Generate the file content and output as JSON with action "create_file"."""
        
        # Generate code
        response = self.llm.generate(system_prompt, user_prompt, temperature=0.4)
        
        # Parse the JSON response
        try:
            # Clean any markdown formatting
            response = self._clean_llm_output(response)
            response = response.strip()
            
            # Try to extract JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                action = json.loads(json_match.group())
            else:
                return {
                    "success": False,
                    "message": f"Failed to parse LLM response as JSON: {response[:200]}"
                }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "message": f"Invalid JSON from LLM: {str(e)}"
            }
        
        # Execute the action
        return self._execute_file_action(project_name, action, step)
    
    def _execute_file_action(self, project_name: str, action: Dict, step: Dict) -> Dict:
        """Execute a file action (create, replace, append)."""
        code_dir = self.workspace.get_code_dir(project_name)
        action_type = action.get("action", "none")
        
        if action_type == "create_file":
            path = action.get("path", step.get("file_path"))
            content = action.get("content", "")
            
            if not path:
                return {"success": False, "message": "No file path provided"}
            
            # Make path relative to code directory
            full_path = code_dir / path
            
            result = self.file_tools.create_file(full_path, content, overwrite=True)
            return result
            
        elif action_type == "str_replace":
            path = action.get("path")
            old_str = action.get("old_str")
            new_str = action.get("new_str")
            
            if not all([path, old_str, new_str]):
                return {"success": False, "message": "Missing parameters for str_replace"}
            
            full_path = code_dir / path
            result = self.file_tools.str_replace(full_path, old_str, new_str)
            return result
            
        elif action_type == "append_to_file":
            path = action.get("path")
            content = action.get("content", "")
            
            if not path:
                return {"success": False, "message": "No file path provided"}
            
            full_path = code_dir / path
            result = self.file_tools.append_to_file(full_path, content)
            return result
            
        elif action_type == "none":
            return {"success": True, "message": action.get("message", "No action needed")}
            
        else:
            return {"success": False, "message": f"Unknown action type: {action_type}"}
    
    def _execute_command_step(self, project_name: str, step: Dict) -> Dict:
        """
        Execute a command step with error handling and auto-fix loop.
        
        If the command fails, attempts to analyze the error and fix it.
        """
        code_dir = self.workspace.get_code_dir(project_name)
        command = step.get("command", "")
        
        if not command:
            return {"success": True, "message": "No command specified, step complete"}
        
        print(f"[Agent] Running command: {command}")
        
        # Execute the command
        result = self.execution.run_command(command, cwd=code_dir)
        
        # Log the execution
        self.workspace.log_execution(
            project_name,
            command,
            result,
            step_title=step.get("title")
        )
        
        # If successful, return
        if result.get("success"):
            return {
                "success": True,
                "message": f"Command completed successfully",
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", "")
            }
        
        # Command failed - attempt auto-fix loop
        print(f"[Agent] Command failed with exit code {result.get('exit_code')}. Attempting fix...")
        
        return self._attempt_error_fix(project_name, step, result)
    
    def _attempt_error_fix(
        self,
        project_name: str,
        step: Dict,
        last_result: Dict,
        attempt: int = 1
    ) -> Dict:
        """
        Attempt to fix an error from a failed command execution.
        
        Uses LLM to analyze the error and generate a fix.
        """
        if attempt > self.max_fix_attempts:
            return {
                "success": False,
                "message": f"Max fix attempts ({self.max_fix_attempts}) reached",
                "stderr": last_result.get("stderr", ""),
                "stdout": last_result.get("stdout", "")
            }
        
        print(f"[Agent] Fix attempt {attempt}/{self.max_fix_attempts}")
        
        # Get file context
        file_context = self._get_project_file_context(project_name)
        
        # Build error analysis prompt
        system_prompt = self._load_developer_prompt()
        
        user_prompt = f"""The following command failed. Analyze the error and provide a fix.

**Failed Command:** `{step.get('command', 'N/A')}`

**STDERR:**
```
{last_result.get('stderr', 'No stderr')}
```

**STDOUT:**
```
{last_result.get('stdout', 'No stdout')}
```

**Current Project Files:**
{file_context}

Analyze the error and output a JSON fix using str_replace or create_file."""
        
        # Generate fix
        response = self.llm.generate(system_prompt, user_prompt, temperature=0.3)
        
        # Parse and execute fix
        try:
            response = self._clean_llm_output(response)
            json_match = re.search(r'\{[\s\S]*\}', response)
            
            if json_match:
                action = json.loads(json_match.group())
            else:
                return {
                    "success": False,
                    "message": f"Failed to parse fix response: {response[:200]}"
                }
            
            # Execute the fix
            fix_result = self._execute_file_action(project_name, action, step)
            
            if not fix_result.get("success"):
                return fix_result
            
            # Re-run the original command
            code_dir = self.workspace.get_code_dir(project_name)
            command = step.get("command", "")
            
            retry_result = self.execution.run_command(command, cwd=code_dir)
            
            # Log the retry
            self.workspace.log_execution(
                project_name,
                f"(retry {attempt}) {command}",
                retry_result,
                step_title=step.get("title")
            )
            
            if retry_result.get("success"):
                return {
                    "success": True,
                    "message": f"Fixed after {attempt} attempt(s)",
                    "stdout": retry_result.get("stdout", ""),
                    "fix_applied": action
                }
            
            # Still failing, recurse for another attempt
            return self._attempt_error_fix(project_name, step, retry_result, attempt + 1)
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "message": f"Invalid JSON in fix response: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error during fix attempt: {str(e)}"
            }
    
    def _get_project_file_context(self, project_name: str, max_files: int = 10) -> str:
        """
        Get context of existing project files for LLM.
        
        Args:
            project_name: Name of the project
            max_files: Maximum number of files to include
            
        Returns:
            Formatted string with file contents
        """
        code_dir = self.workspace.get_code_dir(project_name)
        
        if not code_dir.exists():
            return "No files created yet."
        
        # Get file listing
        listing = self.file_tools.list_dir(code_dir, recursive=True)
        
        if not listing.get("success") or not listing.get("items"):
            return "No files created yet."
        
        context_parts = []
        file_count = 0
        
        for item in listing.get("items", []):
            if item["type"] != "file":
                continue
            
            if file_count >= max_files:
                context_parts.append(f"\n... and more files (showing first {max_files})")
                break
            
            file_path = code_dir / item["path"]
            
            try:
                content = file_path.read_text(encoding="utf-8")
                
                # Truncate long files
                if len(content) > 2000:
                    content = content[:2000] + "\n... [truncated]"
                
                context_parts.append(f"--- {item['path']} ---\n{content}\n")
                file_count += 1
                
            except Exception:
                continue
        
        return "\n".join(context_parts) if context_parts else "No files created yet."
    
    def _finalize_report(self, project_name: str) -> None:
        """Finalize the build report after all steps complete."""
        # Get project info
        project_info = self.workspace.get_project_info(project_name)
        original_query = project_info.get("user_query", "Build project") if project_info else "Build project"
        
        # Get file context for the report
        file_context = self._get_project_file_context(project_name, max_files=20)
        
        # Get execution logs
        recent_logs = self.workspace.get_recent_logs(project_name, count=5)
        logs_summary = "\n".join([f"- {log['filename']}" for log in recent_logs])
        
        # Generate report
        report = f"""# 📋 Build Report

**Project:** {project_name}
**Completed:** {datetime.now().isoformat()}
**Status:** ✅ Complete

## Original Request
> {original_query}

## Generated Files

{file_context}

## Execution Logs
{logs_summary if logs_summary else "No execution logs."}

---
*Generated by DeepBuild*
"""
        
        self.workspace.write_report(project_name, report)
        print("[Agent] Build report finalized.")
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def get_plan_progress(self, project_name: str) -> Dict:
        """Get the progress status of a build plan."""
        plan_content = self.workspace.read_plan(project_name)
        
        if plan_content is None:
            return {
                "exists": False,
                "total_steps": 0,
                "completed_steps": 0,
                "progress_percent": 0
            }
        
        steps = self.parse_plan_steps(plan_content)
        completed = sum(1 for s in steps if s["checked"])
        
        return {
            "exists": True,
            "total_steps": len(steps),
            "completed_steps": completed,
            "progress_percent": (completed / len(steps) * 100) if steps else 100,
            "all_complete": completed == len(steps)
        }
    
    def execute_all_steps(self, project_name: str) -> List[Dict]:
        """Execute all remaining unchecked steps in sequence."""
        results = []
        
        while True:
            result = self.execute_next_step(project_name)
            results.append(result)
            
            if not result["success"] or result.get("completed"):
                break
        
        return results
