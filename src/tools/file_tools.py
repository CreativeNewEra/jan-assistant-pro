"""
File operation tools for Jan Assistant Pro
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List

from src.core.cache import MEMORY_TTL_CACHE, DiskCache
from src.core.logging_config import get_logger
from src.core.metrics import record_tool
from src.core.user_friendly_error import UserFriendlyError


class FileTools:
    """Tools for file operations"""

    def __init__(
        self,
        max_file_size: str = "10MB",
        restricted_paths: List[str] = None,
        *,
        disk_cache_dir: str | None = "data/cache/file_tools",
        disk_cache_ttl: int = 300,
    ):
        self.max_file_size = self._parse_size(max_file_size)
        self.restricted_paths = restricted_paths or ["/etc", "/sys", "/proc", "/dev"]
        self.logger = get_logger(
            f"{self.__class__.__module__}.{self.__class__.__name__}",
            {"max_file_size": self.max_file_size},
        )
        self.disk_cache = (
            DiskCache(disk_cache_dir, default_ttl=disk_cache_ttl)
            if disk_cache_dir
            else None
        )

    def clear_disk_cache(self) -> None:
        """Clear the file tool disk cache."""
        if self.disk_cache:
            self.disk_cache.clear()

    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '10MB' to bytes"""
        size_str = size_str.upper().strip()

        if size_str.endswith("KB"):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith("MB"):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith("GB"):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)

    def _is_path_allowed(self, file_path: str) -> bool:
        """Check if path is allowed (not in restricted paths)"""
        abs_path = os.path.abspath(file_path)

        for restricted in self.restricted_paths:
            if abs_path.startswith(os.path.abspath(restricted)):
                return False

        return True

    def _check_file_size(self, file_path: str) -> bool:
        """Check if file size is within limits"""
        try:
            size = os.path.getsize(file_path)
            return size <= self.max_file_size
        except OSError:
            return True  # If we can't get size, allow the operation

    def _make_user_error(
        self,
        cause: str,
        message: str,
        suggestions: List[str] | None = None,
        doc: str | None = None,
    ) -> Dict[str, Any]:
        return UserFriendlyError(
            cause=cause,
            user_message=message,
            suggestions=suggestions or [],
            documentation_link=doc,
        ).to_dict()

    @record_tool("read_file")
    def read_file(self, file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Read a file

        Args:
            file_path: Path to the file
            encoding: File encoding (default: utf-8)

        Returns:
            Dictionary with success status and content or error message
        """
        cache_key = f"read:{Path(file_path).resolve()}:{encoding}"
        cached = MEMORY_TTL_CACHE.get(cache_key)
        if cached is not None:
            return cached

        try:
            # Security checks
            if not self._is_path_allowed(file_path):
                return {
                    "success": False,
                    "error": f"Access to path '{file_path}' is restricted",
                    "user_error": self._make_user_error(
                        "SecurityError",
                        f"Access to '{file_path}' is not allowed",
                        [
                            "Choose a file in your workspace",
                            "Contact an administrator to adjust security settings",
                        ],
                        "https://example.com/docs/errors#security",
                    ),
                }

            if not os.path.exists(file_path):
                return {"success": False, "error": f"File '{file_path}' does not exist"}

            if not os.path.isfile(file_path):
                return {"success": False, "error": f"'{file_path}' is not a file"}

            if not self._check_file_size(file_path):
                return {
                    "success": False,
                    "error": f"File '{file_path}' is too large (max {self.max_file_size} bytes)",
                }

            # Read the file
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()

            result = {
                "success": True,
                "content": content,
                "file_path": file_path,
                "size_bytes": len(content.encode(encoding)),
            }
            MEMORY_TTL_CACHE[cache_key] = result
            return result

        except UnicodeDecodeError:
            return {
                "success": False,
                "error": f"Could not decode file '{file_path}' with encoding '{encoding}'",
            }
        except PermissionError:
            return {
                "success": False,
                "error": f"Permission denied accessing '{file_path}'",
                "user_error": self._make_user_error(
                    "PermissionError",
                    f"Cannot read '{file_path}'",
                    [
                        "Check file permissions",
                        "Ensure the file exists and is readable",
                    ],
                    "https://example.com/docs/errors#permissions",
                ),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error reading file '{file_path}': {str(e)}",
            }

    @record_tool("write_file")
    def write_file(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        overwrite: bool = True,
    ) -> Dict[str, Any]:
        """
        Write content to a file

        Args:
            file_path: Path to the file
            content: Content to write
            encoding: File encoding (default: utf-8)
            overwrite: Whether to overwrite existing files

        Returns:
            Dictionary with success status and info or error message
        """
        try:
            # Security checks
            if not self._is_path_allowed(file_path):
                return {
                    "success": False,
                    "error": f"Access to path '{file_path}' is restricted",
                    "user_error": self._make_user_error(
                        "SecurityError",
                        f"Access to '{file_path}' is not allowed",
                        [
                            "Choose a location within your workspace",
                            "Contact an administrator to adjust security settings",
                        ],
                        "https://example.com/docs/errors#security",
                    ),
                }

            file_existed = os.path.exists(file_path)

            # Check if file exists and overwrite is False
            if file_existed and not overwrite:
                return {
                    "success": False,
                    "error": f"File '{file_path}' already exists and overwrite is disabled",
                }

            # Create directory if it doesn't exist
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            # Write to a temporary file in the same directory for atomic replace
            temp_dir = directory if directory else "."
            tmp_file = None
            try:
                with tempfile.NamedTemporaryFile(
                    "w", delete=False, dir=temp_dir, encoding=encoding
                ) as tmp:
                    tmp_file = tmp.name
                    tmp.write(content)
                    tmp.flush()
                    os.fsync(tmp.fileno())
                os.replace(tmp_file, file_path)
            finally:
                if tmp_file and os.path.exists(tmp_file):
                    os.remove(tmp_file)

            return {
                "success": True,
                "file_path": file_path,
                "size_bytes": len(content.encode(encoding)),
                "created": not file_existed,
            }

        except PermissionError:
            return {
                "success": False,
                "error": f"Permission denied writing to '{file_path}'",
                "user_error": self._make_user_error(
                    "PermissionError",
                    f"Cannot write to '{file_path}'",
                    [
                        "Check file or directory permissions",
                        "Ensure the directory is writable or choose another path",
                    ],
                    "https://example.com/docs/errors#permissions",
                ),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error writing file '{file_path}': {str(e)}",
            }

    @record_tool("append_file")
    def append_file(
        self, file_path: str, content: str, encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """
        Append content to a file

        Args:
            file_path: Path to the file
            content: Content to append
            encoding: File encoding (default: utf-8)

        Returns:
            Dictionary with success status and info or error message
        """
        try:
            # Security checks
            if not self._is_path_allowed(file_path):
                return {
                    "success": False,
                    "error": f"Access to path '{file_path}' is restricted",
                    "user_error": self._make_user_error(
                        "SecurityError",
                        f"Access to '{file_path}' is not allowed",
                        [
                            "Choose a location within your workspace",
                            "Contact an administrator to adjust security settings",
                        ],
                        "https://example.com/docs/errors#security",
                    ),
                }

            # Create directory if it doesn't exist
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            # Append by writing to a temporary file and then replacing atomically
            temp_dir = directory if directory else "."
            tmp_file = None
            try:
                with tempfile.NamedTemporaryFile(
                    "w", delete=False, dir=temp_dir, encoding=encoding
                ) as tmp:
                    tmp_file = tmp.name
                    if os.path.exists(file_path):
                        with open(file_path, "r", encoding=encoding) as original:
                            shutil.copyfileobj(original, tmp)
                    tmp.write(content)
                    tmp.flush()
                    os.fsync(tmp.fileno())
                os.replace(tmp_file, file_path)
            finally:
                if tmp_file and os.path.exists(tmp_file):
                    os.remove(tmp_file)

            return {
                "success": True,
                "file_path": file_path,
                "appended_bytes": len(content.encode(encoding)),
            }

        except PermissionError:
            return {
                "success": False,
                "error": f"Permission denied writing to '{file_path}'",
                "user_error": self._make_user_error(
                    "PermissionError",
                    f"Cannot write to '{file_path}'",
                    [
                        "Check file or directory permissions",
                        "Ensure the directory is writable or choose another path",
                    ],
                    "https://example.com/docs/errors#permissions",
                ),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error appending to file '{file_path}': {str(e)}",
            }

    @record_tool("delete_file")
    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        Delete a file

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with success status and info or error message
        """
        try:
            # Security checks
            if not self._is_path_allowed(file_path):
                return {
                    "success": False,
                    "error": f"Access to path '{file_path}' is restricted",
                    "user_error": self._make_user_error(
                        "SecurityError",
                        f"Access to '{file_path}' is not allowed",
                        [
                            "Choose a file in your workspace",
                            "Contact an administrator to adjust security settings",
                        ],
                        "https://example.com/docs/errors#security",
                    ),
                }

            if not os.path.exists(file_path):
                return {"success": False, "error": f"File '{file_path}' does not exist"}

            if not os.path.isfile(file_path):
                return {"success": False, "error": f"'{file_path}' is not a file"}

            # Delete the file
            os.remove(file_path)

            return {
                "success": True,
                "file_path": file_path,
                "message": f"File '{file_path}' deleted successfully",
            }

        except PermissionError:
            return {
                "success": False,
                "error": f"Permission denied deleting '{file_path}'",
                "user_error": self._make_user_error(
                    "PermissionError",
                    f"Cannot delete '{file_path}'",
                    [
                        "Check file permissions",
                        "Ensure you own the file or have sufficient rights",
                    ],
                    "https://example.com/docs/errors#permissions",
                ),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error deleting file '{file_path}': {str(e)}",
            }

    @record_tool("list_files")
    def list_files(
        self,
        directory: str = ".",
        pattern: str = "*",
        include_hidden: bool = False,
        *,
        use_cache: bool = True,
        clear_cache: bool = False,
        ttl: int | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Dict[str, Any]:
        """
        List files in a directory

        Args:
            directory: Directory to list (default: current directory)
            pattern: File pattern to match (default: all files)
            include_hidden: Whether to include hidden files

        Returns:
            Dictionary with success status and file list or error message
        """
        try:
            cache_key = f"list:{Path(directory).resolve()}:{pattern}:{include_hidden}"
            if clear_cache and self.disk_cache:
                self.disk_cache.delete(cache_key)
            should_use_cache = use_cache and self.disk_cache and not clear_cache
            if should_use_cache:
                cached = self.disk_cache.get(cache_key)
                if cached is not None:
                    return cached

            # Security checks
            if not self._is_path_allowed(directory):
                return {
                    "success": False,
                    "error": f"Access to path '{directory}' is restricted",
                    "user_error": self._make_user_error(
                        "SecurityError",
                        f"Access to '{directory}' is not allowed",
                        [
                            "Choose a directory within your workspace",
                            "Contact an administrator to adjust security settings",
                        ],
                        "https://example.com/docs/errors#security",
                    ),
                }

            if not os.path.exists(directory):
                return {
                    "success": False,
                    "error": f"Directory '{directory}' does not exist",
                }

            if not os.path.isdir(directory):
                return {"success": False, "error": f"'{directory}' is not a directory"}

            # List files
            path = Path(directory)
            files = []
            directories = []

            all_items = list(path.glob(pattern))
            items = [i for i in all_items if include_hidden or not i.name.startswith(".")]
            total = len(items)

            for idx, item in enumerate(items, start=1):

                item_info = {
                    "name": item.name,
                    "path": str(item),
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": item.stat().st_mtime,
                    "is_file": item.is_file(),
                    "is_directory": item.is_dir(),
                }

                if item.is_file():
                    files.append(item_info)
                elif item.is_dir():
                    directories.append(item_info)

                if progress_callback:
                    progress_callback(idx, total)

            result = {
                "success": True,
                "directory": directory,
                "files": sorted(files, key=lambda x: x["name"]),
                "directories": sorted(directories, key=lambda x: x["name"]),
                "total_files": len(files),
                "total_directories": len(directories),
            }
            if use_cache and self.disk_cache and not clear_cache:
                self.disk_cache.set(cache_key, result, ttl)
            return result

        except PermissionError:
            return {
                "success": False,
                "error": f"Permission denied accessing '{directory}'",
                "user_error": self._make_user_error(
                    "PermissionError",
                    f"Cannot access '{directory}'",
                    [
                        "Check directory permissions",
                        "Ensure you have read access",
                    ],
                    "https://example.com/docs/errors#permissions",
                ),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error listing directory '{directory}': {str(e)}",
            }

    @record_tool("copy_file")
    def copy_file(
        self,
        source: str,
        destination: str,
        overwrite: bool = False,
        *,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Dict[str, Any]:
        """
        Copy a file

        Args:
            source: Source file path
            destination: Destination file path
            overwrite: Whether to overwrite existing files

        Returns:
            Dictionary with success status and info or error message
        """
        try:
            # Security checks
            if not self._is_path_allowed(source) or not self._is_path_allowed(
                destination
            ):
                return {
                    "success": False,
                    "error": "Access to one or both paths is restricted",
                    "user_error": self._make_user_error(
                        "SecurityError",
                        "Copy operation not allowed for one or both paths",
                        [
                            "Use paths within your workspace",
                            "Contact an administrator if this should be permitted",
                        ],
                        "https://example.com/docs/errors#security",
                    ),
                }

            if not os.path.exists(source):
                return {
                    "success": False,
                    "error": f"Source file '{source}' does not exist",
                }

            if not os.path.isfile(source):
                return {"success": False, "error": f"'{source}' is not a file"}

            if os.path.exists(destination) and not overwrite:
                return {
                    "success": False,
                    "error": f"Destination '{destination}' already exists and overwrite is disabled",
                }

            # Create destination directory if needed
            dest_dir = os.path.dirname(destination)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)

            # Copy the file with progress reporting
            total_size = os.path.getsize(source)
            bytes_copied = 0
            with open(source, "rb") as src_f, open(destination, "wb") as dst_f:
                while True:
                    chunk = src_f.read(1024 * 1024)
                    if not chunk:
                        break
                    dst_f.write(chunk)
                    bytes_copied += len(chunk)
                    if progress_callback:
                        progress_callback(bytes_copied, total_size)

            shutil.copystat(source, destination)

            return {
                "success": True,
                "source": source,
                "destination": destination,
                "size_bytes": os.path.getsize(destination),
            }

        except PermissionError:
            return {
                "success": False,
                "error": f"Permission denied copying from '{source}' to '{destination}'",
                "user_error": self._make_user_error(
                    "PermissionError",
                    f"Cannot copy from '{source}'",
                    [
                        "Check permissions on the source and destination",
                        "Ensure the destination is writable",
                    ],
                    "https://example.com/docs/errors#permissions",
                ),
            }
        except Exception as e:
            return {"success": False, "error": f"Error copying file: {str(e)}"}

    @record_tool("get_file_info")
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about a file

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with file information or error message
        """
        try:
            if not os.path.exists(file_path):
                return {"success": False, "error": f"Path '{file_path}' does not exist"}

            stat = os.stat(file_path)
            path = Path(file_path)

            return {
                "success": True,
                "path": file_path,
                "name": path.name,
                "size_bytes": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "is_file": path.is_file(),
                "is_directory": path.is_dir(),
                "is_symlink": path.is_symlink(),
                "extension": path.suffix,
                "parent": str(path.parent),
            }

        except PermissionError:
            return {
                "success": False,
                "error": f"Permission denied accessing '{file_path}'",
                "user_error": self._make_user_error(
                    "PermissionError",
                    f"Cannot access '{file_path}'",
                    [
                        "Check file permissions",
                        "Ensure the file is readable",
                    ],
                    "https://example.com/docs/errors#permissions",
                ),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting file info for '{file_path}': {str(e)}",
            }
