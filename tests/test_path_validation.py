"""Tests for file path validation."""

import os
import tempfile
from pathlib import Path

import pytest

from agent_factory.core.exceptions import ToolExecutionError, ToolValidationError
from agent_factory.integrations.tools.file_io import _validate_path, read_file, write_file


@pytest.fixture
def temp_workdir():
    """Ensure working directory is safely restored after temporary directory usage."""
    old_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        try:
            yield Path(tmpdir)
        finally:
            os.chdir(old_cwd)


@pytest.mark.unit
def test_valid_relative_path(temp_workdir):
    """Test validation of valid relative paths."""
    test_file = Path("test.txt")
    test_file.write_text("test content")

    path = _validate_path("test.txt", allow_write=False)
    assert path.exists()
    assert path.name == "test.txt"


@pytest.mark.unit
def test_path_traversal_prevention(temp_workdir):
    """Test that path traversal attacks are prevented."""
    # Try to access parent directory
    with pytest.raises(ToolValidationError, match="Path traversal detected"):
        _validate_path("../etc/passwd", allow_write=False)

    # Try with multiple ..
    with pytest.raises(ToolValidationError, match="Path traversal detected"):
        _validate_path("../../etc/passwd", allow_write=False)

    # Try with absolute path outside sandbox
    with pytest.raises(ToolValidationError, match="Path traversal detected"):
        _validate_path("/etc/passwd", allow_write=False)


@pytest.mark.unit
def test_system_directory_protection(temp_workdir):
    """Test that system directories are protected."""
    forbidden_paths = [
        "/etc/passwd",
        "/usr/bin",
        "/bin/sh",
        "C:\\Windows\\System32",
    ]

    for path_str in forbidden_paths:
        with pytest.raises(
            ToolValidationError,
            match="(Access to system directory not allowed|Path traversal detected)",
        ):
            _validate_path(path_str, allow_write=False)


@pytest.mark.unit
def test_sandbox_directory(temp_workdir):
    """Test sandbox directory configuration."""
    sandbox = str(temp_workdir.resolve())
    os.environ["AGENT_FACTORY_SANDBOX_DIR"] = sandbox
    try:
        test_file = Path(sandbox) / "test.txt"
        test_file.write_text("test")

        path = _validate_path("test.txt", allow_write=False)
        assert str(path).lower().startswith(sandbox.lower())
    finally:
        os.environ.pop("AGENT_FACTORY_SANDBOX_DIR", None)


@pytest.mark.unit
def test_read_file_valid(temp_workdir):
    """Test reading a valid file."""
    test_file = Path("test.txt")
    test_file.write_text("Hello, World!")

    content = read_file("test.txt")
    assert content == "Hello, World!"


@pytest.mark.unit
def test_read_file_not_found(temp_workdir):
    """Test reading a non-existent file."""
    with pytest.raises((FileNotFoundError, ToolExecutionError)):
        read_file("nonexistent.txt")


@pytest.mark.unit
def test_read_file_path_traversal(temp_workdir):
    """Test that path traversal is prevented in read_file."""
    with pytest.raises((ToolValidationError, ToolExecutionError), match="Path traversal detected"):
        read_file("../etc/passwd")


@pytest.mark.unit
def test_write_file_valid(temp_workdir):
    """Test writing to a valid file."""
    result = write_file("output.txt", "Test content")
    assert "Successfully wrote" in result
    assert Path("output.txt").read_text() == "Test content"


@pytest.mark.unit
def test_write_file_path_traversal(temp_workdir):
    """Test that path traversal is prevented in write_file."""
    with pytest.raises((ToolValidationError, ToolExecutionError), match="Path traversal detected"):
        write_file("../etc/passwd", "malicious content")


@pytest.mark.unit
def test_write_file_nested_directories(temp_workdir):
    """Test writing to nested directories."""
    result = write_file("nested/dir/file.txt", "Content")
    assert "Successfully wrote" in result
    assert Path("nested/dir/file.txt").read_text() == "Content"


@pytest.mark.unit
def test_invalid_path_type():
    """Test that non-string paths are rejected."""
    with pytest.raises(ToolValidationError, match="File path must be a non-empty string"):
        _validate_path(None, allow_write=False)

    with pytest.raises(ToolValidationError, match="File path must be a non-empty string"):
        _validate_path("", allow_write=False)

    with pytest.raises(ToolValidationError, match="File path must be a non-empty string"):
        _validate_path(123, allow_write=False)


@pytest.mark.unit
def test_write_file_none_content(temp_workdir):
    """Test that None content is rejected."""
    with pytest.raises((ToolValidationError, ToolExecutionError), match="Content cannot be None"):
        write_file("test.txt", None)
