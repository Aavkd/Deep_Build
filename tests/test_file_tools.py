"""
Tests for FileTools

Verifies file creation, listing, and editing functionality.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.file_tools import FileTools


class TestFileTools:
    """Test cases for FileTools."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp = Path(tempfile.mkdtemp())
        yield temp
        shutil.rmtree(temp, ignore_errors=True)
    
    def test_create_file(self, temp_dir):
        """Test creating a new file."""
        file_path = temp_dir / "test.py"
        content = "print('Hello World')"
        
        result = FileTools.create_file(file_path, content)
        
        assert result["success"] is True
        assert file_path.exists()
        assert file_path.read_text() == content
    
    def test_create_file_with_nested_dirs(self, temp_dir):
        """Test creating a file in nested directories."""
        file_path = temp_dir / "src" / "utils" / "helper.py"
        content = "# Helper module"
        
        result = FileTools.create_file(file_path, content)
        
        assert result["success"] is True
        assert file_path.exists()
        assert (temp_dir / "src" / "utils").is_dir()
    
    def test_create_file_no_overwrite(self, temp_dir):
        """Test that create_file fails when file exists and overwrite=False."""
        file_path = temp_dir / "existing.py"
        file_path.write_text("original content")
        
        result = FileTools.create_file(file_path, "new content", overwrite=False)
        
        assert result["success"] is False
        assert "already exists" in result["message"]
        assert file_path.read_text() == "original content"
    
    def test_create_file_with_overwrite(self, temp_dir):
        """Test that create_file succeeds when overwrite=True."""
        file_path = temp_dir / "existing.py"
        file_path.write_text("original content")
        
        result = FileTools.create_file(file_path, "new content", overwrite=True)
        
        assert result["success"] is True
        assert file_path.read_text() == "new content"
    
    def test_list_dir_basic(self, temp_dir):
        """Test listing directory contents."""
        # Create some files
        (temp_dir / "file1.py").write_text("content1")
        (temp_dir / "file2.py").write_text("content2")
        (temp_dir / "subdir").mkdir()
        (temp_dir / "subdir" / "file3.py").write_text("content3")
        
        result = FileTools.list_dir(temp_dir, recursive=False)
        
        assert result["success"] is True
        assert result["total_files"] == 2  # Only top-level files
        assert result["total_dirs"] == 1
    
    def test_list_dir_recursive(self, temp_dir):
        """Test listing directory contents recursively."""
        # Create some files
        (temp_dir / "file1.py").write_text("content1")
        (temp_dir / "subdir").mkdir()
        (temp_dir / "subdir" / "file2.py").write_text("content2")
        (temp_dir / "subdir" / "nested").mkdir()
        (temp_dir / "subdir" / "nested" / "file3.py").write_text("content3")
        
        result = FileTools.list_dir(temp_dir, recursive=True)
        
        assert result["success"] is True
        assert result["total_files"] == 3
        assert result["total_dirs"] == 2
    
    def test_list_dir_tree_format(self, temp_dir):
        """Test that list_dir produces a tree view."""
        (temp_dir / "main.py").write_text("# main")
        (temp_dir / "utils").mkdir()
        
        result = FileTools.list_dir(temp_dir, recursive=True)
        
        assert result["success"] is True
        assert "tree" in result
        assert "main.py" in result["tree"]
        assert "utils/" in result["tree"]
    
    def test_read_file(self, temp_dir):
        """Test reading file contents."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("Line 1\nLine 2\nLine 3\n")
        
        result = FileTools.read_file(file_path)
        
        assert result["success"] is True
        assert result["total_lines"] == 3  # 3 lines with trailing newline
        assert "Line 1" in result["content"]
    
    def test_read_file_with_line_range(self, temp_dir):
        """Test reading specific lines from a file."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")
        
        result = FileTools.read_file(file_path, start_line=2, end_line=4)
        
        assert result["success"] is True
        assert result["start_line"] == 2
        assert result["end_line"] == 4
        assert "Line 2" in result["content"]
        assert "Line 4" in result["content"]
        assert "Line 1" not in result["content"]
    
    def test_str_replace(self, temp_dir):
        """Test string replacement."""
        file_path = temp_dir / "code.py"
        file_path.write_text("def old_function():\n    pass")
        
        result = FileTools.str_replace(
            file_path,
            "def old_function():",
            "def new_function():"
        )
        
        assert result["success"] is True
        assert "new_function" in file_path.read_text()
    
    def test_str_replace_multiple_occurrences_fails(self, temp_dir):
        """Test that str_replace fails when string appears multiple times."""
        file_path = temp_dir / "code.py"
        file_path.write_text("hello world\nhello again")
        
        result = FileTools.str_replace(file_path, "hello", "hi")
        
        assert result["success"] is False
        assert result["occurrences"] == 2
        assert "2 times" in result["message"]
    
    def test_str_replace_not_found(self, temp_dir):
        """Test str_replace when string is not found."""
        file_path = temp_dir / "code.py"
        file_path.write_text("some content")
        
        result = FileTools.str_replace(file_path, "nonexistent", "replacement")
        
        assert result["success"] is False
        assert "not found" in result["message"].lower()
    
    def test_append_to_file(self, temp_dir):
        """Test appending content to a file."""
        file_path = temp_dir / "log.txt"
        file_path.write_text("Initial content")
        
        result = FileTools.append_to_file(file_path, "\nAppended content")
        
        assert result["success"] is True
        content = file_path.read_text()
        assert "Initial content" in content
        assert "Appended content" in content
    
    def test_append_creates_new_file(self, temp_dir):
        """Test that append_to_file creates the file if it doesn't exist."""
        file_path = temp_dir / "new_log.txt"
        
        result = FileTools.append_to_file(file_path, "First content")
        
        assert result["success"] is True
        assert file_path.exists()
        assert file_path.read_text() == "First content"
    
    def test_insert_after(self, temp_dir):
        """Test inserting content after an anchor string."""
        file_path = temp_dir / "code.py"
        file_path.write_text("class MyClass:\n    pass")
        
        result = FileTools.insert_after(
            file_path,
            "class MyClass:",
            "\n    def __init__(self):\n        pass"
        )
        
        assert result["success"] is True
        content = file_path.read_text()
        assert "__init__" in content
    
    def test_delete_file(self, temp_dir):
        """Test deleting a file."""
        file_path = temp_dir / "to_delete.py"
        file_path.write_text("delete me")
        
        result = FileTools.delete_file(file_path)
        
        assert result["success"] is True
        assert not file_path.exists()
    
    def test_search_in_file(self, temp_dir):
        """Test searching for patterns in a file."""
        file_path = temp_dir / "code.py"
        file_path.write_text("def func1():\n    pass\n\ndef func2():\n    return True")
        
        result = FileTools.search_in_file(file_path, "def ")
        
        assert result["success"] is True
        assert result["total_matches"] == 2
        assert result["matches"][0]["line_number"] == 1
        assert result["matches"][1]["line_number"] == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
