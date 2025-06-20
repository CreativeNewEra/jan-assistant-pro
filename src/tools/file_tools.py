"""
File operation tools for Jan Assistant Pro
"""

import os
import shutil
from typing import Optional, List, Dict, Any
from pathlib import Path


class FileTools:
    """Tools for file operations"""
    
    def __init__(self, max_file_size: str = "10MB", restricted_paths: List[str] = None):
        self.max_file_size = self._parse_size(max_file_size)
        self.restricted_paths = restricted_paths or ["/etc", "/sys", "/proc", "/dev"]
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '10MB' to bytes"""
        size_str = size_str.upper().strip()
        
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
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
    
    def read_file(self, file_path: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        Read a file
        
        Args:
            file_path: Path to the file
            encoding: File encoding (default: utf-8)
            
        Returns:
            Dictionary with success status and content or error message
        """
        try:
            # Security checks
            if not self._is_path_allowed(file_path):
                return {
                    'success': False,
                    'error': f"Access to path '{file_path}' is restricted"
                }
            
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': f"File '{file_path}' does not exist"
                }
            
            if not os.path.isfile(file_path):
                return {
                    'success': False,
                    'error': f"'{file_path}' is not a file"
                }
            
            if not self._check_file_size(file_path):
                return {
                    'success': False,
                    'error': f"File '{file_path}' is too large (max {self.max_file_size} bytes)"
                }
            
            # Read the file
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            return {
                'success': True,
                'content': content,
                'file_path': file_path,
                'size_bytes': len(content.encode(encoding))
            }
            
        except UnicodeDecodeError:
            return {
                'success': False,
                'error': f"Could not decode file '{file_path}' with encoding '{encoding}'"
            }
        except PermissionError:
            return {
                'success': False,
                'error': f"Permission denied accessing '{file_path}'"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error reading file '{file_path}': {str(e)}"
            }
    
    def write_file(self, file_path: str, content: str, encoding: str = 'utf-8', 
                   overwrite: bool = True) -> Dict[str, Any]:
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
                    'success': False,
                    'error': f"Access to path '{file_path}' is restricted"
                }
            
            # Check if file exists and overwrite is False
            if os.path.exists(file_path) and not overwrite:
                return {
                    'success': False,
                    'error': f"File '{file_path}' already exists and overwrite is disabled"
                }
            
            # Create directory if it doesn't exist
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # Write the file
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            return {
                'success': True,
                'file_path': file_path,
                'size_bytes': len(content.encode(encoding)),
                'created': not os.path.exists(file_path) if not overwrite else None
            }
            
        except PermissionError:
            return {
                'success': False,
                'error': f"Permission denied writing to '{file_path}'"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error writing file '{file_path}': {str(e)}"
            }
    
    def append_file(self, file_path: str, content: str, encoding: str = 'utf-8') -> Dict[str, Any]:
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
                    'success': False,
                    'error': f"Access to path '{file_path}' is restricted"
                }
            
            # Create directory if it doesn't exist
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # Append to the file
            with open(file_path, 'a', encoding=encoding) as f:
                f.write(content)
            
            return {
                'success': True,
                'file_path': file_path,
                'appended_bytes': len(content.encode(encoding))
            }
            
        except PermissionError:
            return {
                'success': False,
                'error': f"Permission denied writing to '{file_path}'"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error appending to file '{file_path}': {str(e)}"
            }
    
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
                    'success': False,
                    'error': f"Access to path '{file_path}' is restricted"
                }
            
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': f"File '{file_path}' does not exist"
                }
            
            if not os.path.isfile(file_path):
                return {
                    'success': False,
                    'error': f"'{file_path}' is not a file"
                }
            
            # Delete the file
            os.remove(file_path)
            
            return {
                'success': True,
                'file_path': file_path,
                'message': f"File '{file_path}' deleted successfully"
            }
            
        except PermissionError:
            return {
                'success': False,
                'error': f"Permission denied deleting '{file_path}'"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error deleting file '{file_path}': {str(e)}"
            }
    
    def list_files(self, directory: str = ".", pattern: str = "*", 
                   include_hidden: bool = False) -> Dict[str, Any]:
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
            # Security checks
            if not self._is_path_allowed(directory):
                return {
                    'success': False,
                    'error': f"Access to path '{directory}' is restricted"
                }
            
            if not os.path.exists(directory):
                return {
                    'success': False,
                    'error': f"Directory '{directory}' does not exist"
                }
            
            if not os.path.isdir(directory):
                return {
                    'success': False,
                    'error': f"'{directory}' is not a directory"
                }
            
            # List files
            path = Path(directory)
            files = []
            directories = []
            
            for item in path.glob(pattern):
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                item_info = {
                    'name': item.name,
                    'path': str(item),
                    'size': item.stat().st_size if item.is_file() else None,
                    'modified': item.stat().st_mtime,
                    'is_file': item.is_file(),
                    'is_directory': item.is_dir()
                }
                
                if item.is_file():
                    files.append(item_info)
                elif item.is_dir():
                    directories.append(item_info)
            
            return {
                'success': True,
                'directory': directory,
                'files': sorted(files, key=lambda x: x['name']),
                'directories': sorted(directories, key=lambda x: x['name']),
                'total_files': len(files),
                'total_directories': len(directories)
            }
            
        except PermissionError:
            return {
                'success': False,
                'error': f"Permission denied accessing '{directory}'"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error listing directory '{directory}': {str(e)}"
            }
    
    def copy_file(self, source: str, destination: str, overwrite: bool = False) -> Dict[str, Any]:
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
            if not self._is_path_allowed(source) or not self._is_path_allowed(destination):
                return {
                    'success': False,
                    'error': "Access to one or both paths is restricted"
                }
            
            if not os.path.exists(source):
                return {
                    'success': False,
                    'error': f"Source file '{source}' does not exist"
                }
            
            if not os.path.isfile(source):
                return {
                    'success': False,
                    'error': f"'{source}' is not a file"
                }
            
            if os.path.exists(destination) and not overwrite:
                return {
                    'success': False,
                    'error': f"Destination '{destination}' already exists and overwrite is disabled"
                }
            
            # Create destination directory if needed
            dest_dir = os.path.dirname(destination)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
            
            # Copy the file
            shutil.copy2(source, destination)
            
            return {
                'success': True,
                'source': source,
                'destination': destination,
                'size_bytes': os.path.getsize(destination)
            }
            
        except PermissionError:
            return {
                'success': False,
                'error': f"Permission denied copying from '{source}' to '{destination}'"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error copying file: {str(e)}"
            }
    
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
                return {
                    'success': False,
                    'error': f"Path '{file_path}' does not exist"
                }
            
            stat = os.stat(file_path)
            path = Path(file_path)
            
            return {
                'success': True,
                'path': file_path,
                'name': path.name,
                'size_bytes': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'is_file': path.is_file(),
                'is_directory': path.is_dir(),
                'is_symlink': path.is_symlink(),
                'extension': path.suffix,
                'parent': str(path.parent)
            }
            
        except PermissionError:
            return {
                'success': False,
                'error': f"Permission denied accessing '{file_path}'"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error getting file info for '{file_path}': {str(e)}"
            }
