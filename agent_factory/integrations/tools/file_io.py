"""File I/O tools for reading and writing files."""

import os
from pathlib import Path

from agent_factory.core.exceptions import ToolValidationError
from agent_factory.tools.decorator import function_tool


def _validate_path(file_path: str, allow_write: bool = False) -> Path:
    """
    Validate and sanitize a file path.

    Args:
        file_path: Path to validate
        allow_write: Whether write operations are allowed

    Returns:
        Resolved Path object

    Raises:
        ToolValidationError: If path is invalid or unsafe
    """
    if not file_path or not isinstance(file_path, str):
        raise ToolValidationError("File path must be a non-empty string")

    # Allowed base directory (configured sandbox, else current working directory)
    allowed_base = Path(os.getcwd()).resolve()
    sandbox_dir = os.getenv("AGENT_FACTORY_SANDBOX_DIR")
    if sandbox_dir:
        allowed_base = Path(sandbox_dir).resolve()

    # Resolve path. Relative paths resolve against the allowed base —
    # otherwise a configured sandbox rejects every legitimate relative path.
    try:
        path = (allowed_base / file_path).resolve()
    except Exception as e:
        raise ToolValidationError(f"Invalid path: {e}") from e

    # Prevent access to system directories (substring match also catches
    # Windows-style paths smuggled onto POSIX as literal filenames)
    forbidden_paths = [
        "/etc",
        "/usr",
        "/bin",
        "/sbin",
        "/sys",
        "/proc",
        "/dev",
        "C:\\Windows",
        "C:\\System32",
        "/System",
        "/Library",
    ]
    path_str = str(path)
    is_system_path = any(f.lower() in path_str.lower() for f in forbidden_paths)

    try:
        # Check if path is within allowed base
        path.relative_to(allowed_base)
    except ValueError:
        msg = f"Path traversal detected. Path must be within {allowed_base}"
        if is_system_path:
            msg += " — Access to system directory not allowed"
        raise ToolValidationError(msg) from None

    if is_system_path:
        raise ToolValidationError("Access to system directory not allowed")

    # For write operations, check if parent directory exists or can be created
    if allow_write:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise ToolValidationError("Permission denied: cannot create directory") from None
        except Exception as e:
            raise ToolValidationError(f"Cannot create directory: {e}") from e

    return path


@function_tool(name="read_file", description="Read contents of a file")
def read_file(file_path: str) -> str:
    """
    Read a file and return its contents.

    Paths are validated and sanitized to prevent path traversal attacks.
    Only files within the current working directory (or configured sandbox) can be accessed.

    Args:
        file_path: Path to the file (relative to current directory or sandbox)

    Returns:
        File contents as string

    Raises:
        ToolValidationError: If path is invalid or unsafe
        FileNotFoundError: If file does not exist
        ValueError: If path is not a file
    """
    path = _validate_path(file_path, allow_write=False)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Try with error handling
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        raise ToolValidationError(f"Error reading file: {e}") from e


@function_tool(name="write_file", description="Write content to a file")
def write_file(file_path: str, content: str) -> str:
    """
    Write content to a file.

    Paths are validated and sanitized to prevent path traversal attacks.
    Only files within the current working directory (or configured sandbox) can be written.
    Parent directories will be created if they don't exist.

    Args:
        file_path: Path to the file (relative to current directory or sandbox)
        content: Content to write

    Returns:
        Success message

    Raises:
        ToolValidationError: If path is invalid or unsafe
        PermissionError: If write permission is denied
    """
    if content is None:
        raise ToolValidationError("Content cannot be None")

    path = _validate_path(file_path, allow_write=True)

    try:
        path.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content)} characters to {file_path}"
    except PermissionError:
        raise ToolValidationError(f"Permission denied: cannot write to {file_path}") from None
    except Exception as e:
        raise ToolValidationError(f"Error writing file: {e}") from e


# The decorator returns Tool instances, so these are already Tools
read_file_tool = read_file
write_file_tool = write_file
