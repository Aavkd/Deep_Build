"""
File Tools Service - Surgical File Editing for LLM-driven Updates

Provides precision tools for modifying files safely:
- read_file: Read file content with optional line range
- search_in_file: Find line numbers where patterns appear
- str_replace: Replace exact text with uniqueness validation
- create_file: Create new files with content
- list_dir: List directory contents recursively

These tools follow the "Aider" approach for reliable file editing.
"""

import re
import os
from pathlib import Path
from typing import Union, Optional, List, Dict


class FileTools:
    """
    Surgical file editing tools for LLM-driven content updates.
    
    These tools are designed to be used by an LLM to make precise,
    safe edits to files without accidentally deleting content.
    """
    
    @staticmethod
    def _normalize_path(path: Union[str, Path]) -> Path:
        """
        Normalize path input to Path object.
        
        Args:
            path: File path as string or Path object
            
        Returns:
            Path object
        """
        if isinstance(path, str):
            return Path(path)
        return path
    
    # =========================================================================
    # New Methods for DeepBuild
    # =========================================================================
    
    @staticmethod
    def create_file(
        path: Union[str, Path],
        content: str,
        overwrite: bool = False
    ) -> Dict:
        """
        Create a new file with the specified content.
        
        Creates parent directories if they don't exist.
        
        Args:
            path: Path to the file to create
            content: Content to write to the file
            overwrite: If True, overwrite existing file. If False, fail if exists.
            
        Returns:
            Dictionary with:
                - success: bool
                - message: str
                - path: str (absolute path to created file)
                
        Example:
            >>> FileTools.create_file("src/main.py", "print('Hello World')")
            {"success": True, "message": "Created file", "path": "/workspace/src/main.py"}
        """
        path = FileTools._normalize_path(path)
        
        try:
            # Check if file exists
            if path.exists() and not overwrite:
                return {
                    "success": False,
                    "message": f"File already exists: {path}. Set overwrite=True to replace.",
                    "path": str(path.resolve())
                }
            
            # Create parent directories
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            path.write_text(content, encoding="utf-8")
            
            return {
                "success": True,
                "message": f"Created file with {len(content)} characters",
                "path": str(path.resolve())
            }
            
        except PermissionError:
            return {
                "success": False,
                "message": f"Permission denied: Cannot write to {path}",
                "path": str(path)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error creating file: {str(e)}",
                "path": str(path)
            }
    
    @staticmethod
    def list_dir(
        path: Union[str, Path],
        recursive: bool = False,
        max_depth: int = 3,
        include_hidden: bool = False
    ) -> Dict:
        """
        List the contents of a directory.
        
        Returns a tree-like structure of files and subdirectories.
        
        Args:
            path: Path to the directory to list
            recursive: If True, list contents recursively
            max_depth: Maximum recursion depth (only used if recursive=True)
            include_hidden: If True, include hidden files/directories
            
        Returns:
            Dictionary with:
                - success: bool
                - items: List of item dictionaries with name, type, size
                - tree: str (formatted tree view)
                - total_files: int
                - total_dirs: int
                - error: str (if success is False)
                
        Example:
            >>> FileTools.list_dir("src/", recursive=True)
            {"success": True, "items": [...], "tree": "src/\\n├── main.py\\n└── utils/"}
        """
        path = FileTools._normalize_path(path)
        
        if not path.exists():
            return {
                "success": False,
                "items": [],
                "tree": "",
                "total_files": 0,
                "total_dirs": 0,
                "error": f"Directory not found: {path}"
            }
        
        if not path.is_dir():
            return {
                "success": False,
                "items": [],
                "tree": "",
                "total_files": 0,
                "total_dirs": 0,
                "error": f"Not a directory: {path}"
            }
        
        items = []
        tree_lines = [str(path.name) + "/"]
        total_files = 0
        total_dirs = 0
        
        def scan_dir(dir_path: Path, depth: int, prefix: str = ""):
            nonlocal total_files, total_dirs
            
            if recursive and depth > max_depth:
                return
            
            try:
                entries = sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            except PermissionError:
                return
            
            # Filter hidden files if needed
            if not include_hidden:
                entries = [e for e in entries if not e.name.startswith('.')]
            
            for i, entry in enumerate(entries):
                is_last = i == len(entries) - 1
                connector = "└── " if is_last else "├── "
                
                if entry.is_dir():
                    total_dirs += 1
                    items.append({
                        "name": entry.name,
                        "type": "directory",
                        "path": str(entry.relative_to(path)),
                        "size": None
                    })
                    tree_lines.append(f"{prefix}{connector}{entry.name}/")
                    
                    if recursive and depth < max_depth:
                        extension = "    " if is_last else "│   "
                        scan_dir(entry, depth + 1, prefix + extension)
                else:
                    total_files += 1
                    size = entry.stat().st_size
                    items.append({
                        "name": entry.name,
                        "type": "file",
                        "path": str(entry.relative_to(path)),
                        "size": size
                    })
                    tree_lines.append(f"{prefix}{connector}{entry.name}")
        
        try:
            scan_dir(path, 0)
            
            return {
                "success": True,
                "items": items,
                "tree": "\n".join(tree_lines),
                "total_files": total_files,
                "total_dirs": total_dirs
            }
            
        except Exception as e:
            return {
                "success": False,
                "items": [],
                "tree": "",
                "total_files": 0,
                "total_dirs": 0,
                "error": f"Error listing directory: {str(e)}"
            }
    
    # =========================================================================
    # Existing Methods from DeepResearch
    # =========================================================================
    
    @staticmethod
    def read_file(
        path: Union[str, Path],
        start_line: Optional[int] = None,
        end_line: Optional[int] = None
    ) -> Dict:
        """
        Read file content with optional line range windowing.
        
        This allows the LLM to read only the relevant portion of a large file,
        saving tokens and improving focus.
        
        Args:
            path: Path to the file to read
            start_line: First line to read (1-indexed, inclusive). None = start from beginning
            end_line: Last line to read (1-indexed, inclusive). None = read to end
            
        Returns:
            Dictionary with:
                - success: bool
                - content: str (the file content or error message)
                - total_lines: int (total lines in file)
                - start_line: int (actual start line read)
                - end_line: int (actual end line read)
        """
        path = FileTools._normalize_path(path)
        
        if not path.exists():
            return {
                "success": False,
                "content": f"File not found: {path}",
                "total_lines": 0,
                "start_line": 0,
                "end_line": 0
            }
        
        try:
            content = path.read_text(encoding="utf-8")
            lines = content.splitlines(keepends=True)
            total_lines = len(lines)
            
            # Handle empty file
            if total_lines == 0:
                return {
                    "success": True,
                    "content": "",
                    "total_lines": 0,
                    "start_line": 0,
                    "end_line": 0
                }
            
            # Normalize line numbers (1-indexed)
            if start_line is None:
                start_line = 1
            if end_line is None:
                end_line = total_lines
            
            # Clamp to valid range
            start_line = max(1, min(start_line, total_lines))
            end_line = max(start_line, min(end_line, total_lines))
            
            # Extract the requested lines (convert to 0-indexed)
            selected_lines = lines[start_line - 1:end_line]
            selected_content = "".join(selected_lines)
            
            return {
                "success": True,
                "content": selected_content,
                "total_lines": total_lines,
                "start_line": start_line,
                "end_line": end_line
            }
            
        except Exception as e:
            return {
                "success": False,
                "content": f"Error reading file: {str(e)}",
                "total_lines": 0,
                "start_line": 0,
                "end_line": 0
            }
    
    @staticmethod
    def search_in_file(
        path: Union[str, Path],
        query: str,
        is_regex: bool = False,
        context_lines: int = 2
    ) -> Dict:
        """
        Search for a pattern in a file and return matching line numbers with context.
        
        Args:
            path: Path to the file to search
            query: String or regex pattern to search for
            is_regex: If True, treat query as a regex pattern
            context_lines: Number of context lines to include around each match
            
        Returns:
            Dictionary with:
                - success: bool
                - matches: List of match dictionaries
                - total_matches: int
                - error: str (if success is False)
        """
        path = FileTools._normalize_path(path)
        
        if not path.exists():
            return {
                "success": False,
                "matches": [],
                "total_matches": 0,
                "error": f"File not found: {path}"
            }
        
        try:
            content = path.read_text(encoding="utf-8")
            lines = content.splitlines(keepends=True)
            
            matches = []
            
            for i, line in enumerate(lines):
                line_number = i + 1  # 1-indexed
                
                # Check for match
                if is_regex:
                    is_match = bool(re.search(query, line))
                else:
                    is_match = query in line
                
                if is_match:
                    # Get context lines
                    start_ctx = max(0, i - context_lines)
                    end_ctx = min(len(lines), i + context_lines + 1)
                    
                    context_before = [l.rstrip('\n\r') for l in lines[start_ctx:i]]
                    context_after = [l.rstrip('\n\r') for l in lines[i + 1:end_ctx]]
                    
                    matches.append({
                        "line_number": line_number,
                        "line_content": line.rstrip('\n\r'),
                        "context_before": context_before,
                        "context_after": context_after
                    })
            
            return {
                "success": True,
                "matches": matches,
                "total_matches": len(matches)
            }
            
        except re.error as e:
            return {
                "success": False,
                "matches": [],
                "total_matches": 0,
                "error": f"Invalid regex pattern: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "matches": [],
                "total_matches": 0,
                "error": f"Error searching file: {str(e)}"
            }
    
    @staticmethod
    def str_replace(
        path: Union[str, Path],
        old_str: str,
        new_str: str
    ) -> Dict:
        """
        Replace an exact string in a file with uniqueness validation.
        
        The old_str must be unique in the file - if it appears multiple times,
        the operation fails and more context must be provided.
        
        Args:
            path: Path to the file to modify
            old_str: The exact string to replace (must be unique in the file)
            new_str: The replacement string
            
        Returns:
            Dictionary with:
                - success: bool
                - message: str
                - occurrences: int
                - line_numbers: list
        """
        path = FileTools._normalize_path(path)
        
        if not path.exists():
            return {
                "success": False,
                "message": f"File not found: {path}",
                "occurrences": 0,
                "line_numbers": []
            }
        
        try:
            content = path.read_text(encoding="utf-8")
            
            # Count occurrences
            occurrences = content.count(old_str)
            
            if occurrences == 0:
                old_str_stripped = old_str.strip()
                if old_str_stripped and old_str_stripped in content:
                    return {
                        "success": False,
                        "message": "String not found exactly as provided. Check whitespace/newlines.",
                        "occurrences": 0,
                        "line_numbers": []
                    }
                return {
                    "success": False,
                    "message": "String not found in file. Ensure exact match including whitespace.",
                    "occurrences": 0,
                    "line_numbers": []
                }
            
            if occurrences > 1:
                lines = content.splitlines()
                line_numbers = []
                for i, line in enumerate(lines):
                    if old_str in line or (len(old_str.splitlines()) > 1 and old_str.splitlines()[0] in line):
                        line_numbers.append(i + 1)
                
                return {
                    "success": False,
                    "message": f"String appears {occurrences} times. Provide more context to make it unique.",
                    "occurrences": occurrences,
                    "line_numbers": line_numbers[:10]
                }
            
            # Exactly one occurrence - safe to replace
            new_content = content.replace(old_str, new_str, 1)
            path.write_text(new_content, encoding="utf-8")
            
            return {
                "success": True,
                "message": "Successfully replaced 1 occurrence",
                "occurrences": 1,
                "line_numbers": []
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error modifying file: {str(e)}",
                "occurrences": 0,
                "line_numbers": []
            }
    
    @staticmethod
    def append_to_file(
        path: Union[str, Path],
        content: str,
        ensure_newline: bool = True
    ) -> Dict:
        """
        Append content to the end of a file.
        
        Args:
            path: Path to the file to modify
            content: Content to append
            ensure_newline: If True, ensure a newline separates existing content
            
        Returns:
            Dictionary with success and message
        """
        path = FileTools._normalize_path(path)
        
        if not path.exists():
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                return {
                    "success": True,
                    "message": "Created new file and wrote content"
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Error creating file: {str(e)}"
                }
        
        try:
            existing_content = path.read_text(encoding="utf-8")
            
            if ensure_newline and existing_content and not existing_content.endswith('\n'):
                existing_content += '\n'
            
            new_content = existing_content + content
            path.write_text(new_content, encoding="utf-8")
            
            return {
                "success": True,
                "message": "Successfully appended content to file"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error appending to file: {str(e)}"
            }
    
    @staticmethod
    def insert_after(
        path: Union[str, Path],
        anchor: str,
        content: str
    ) -> Dict:
        """
        Insert content immediately after a unique anchor string.
        
        Args:
            path: Path to the file to modify
            anchor: The unique string after which to insert
            content: Content to insert
            
        Returns:
            Dictionary with success, message, and occurrences
        """
        path = FileTools._normalize_path(path)
        
        if not path.exists():
            return {
                "success": False,
                "message": f"File not found: {path}",
                "occurrences": 0
            }
        
        try:
            file_content = path.read_text(encoding="utf-8")
            occurrences = file_content.count(anchor)
            
            if occurrences == 0:
                return {
                    "success": False,
                    "message": "Anchor string not found in file.",
                    "occurrences": 0
                }
            
            if occurrences > 1:
                return {
                    "success": False,
                    "message": f"Anchor appears {occurrences} times. Provide a more specific anchor.",
                    "occurrences": occurrences
                }
            
            new_content = file_content.replace(anchor, anchor + content, 1)
            path.write_text(new_content, encoding="utf-8")
            
            return {
                "success": True,
                "message": "Successfully inserted content after anchor",
                "occurrences": 1
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error modifying file: {str(e)}",
                "occurrences": 0
            }
    
    @staticmethod
    def delete_file(path: Union[str, Path]) -> Dict:
        """
        Delete a file.
        
        Args:
            path: Path to the file to delete
            
        Returns:
            Dictionary with success and message
        """
        path = FileTools._normalize_path(path)
        
        if not path.exists():
            return {
                "success": False,
                "message": f"File not found: {path}"
            }
        
        if path.is_dir():
            return {
                "success": False,
                "message": f"Cannot delete directory with this method: {path}"
            }
        
        try:
            path.unlink()
            return {
                "success": True,
                "message": f"Successfully deleted file: {path}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error deleting file: {str(e)}"
            }
