"""
System command tools for Jan Assistant Pro
"""

import subprocess
import shlex
import os
from typing import List, Dict, Any, Optional
import platform


class SystemTools:
    """Tools for executing system commands safely"""
    
    def __init__(self, allowed_commands: List[str] = None, timeout: int = 30):
        self.allowed_commands = allowed_commands or [
            "ls", "pwd", "cat", "echo", "python3", "python", "pip", "pip3",
            "git", "curl", "wget", "grep", "find", "wc", "head", "tail",
            "sort", "uniq", "date", "whoami", "which", "type"
        ]
        self.timeout = timeout
        self.system = platform.system().lower()
    
    def _is_command_allowed(self, command: str) -> bool:
        """Check if a command is in the allowed list"""
        # Extract the base command (first word)
        base_command = command.strip().split()[0]
        return base_command in self.allowed_commands
    
    def _sanitize_command(self, command: str) -> str:
        """Basic command sanitization"""
        # Remove potentially dangerous characters/patterns
        dangerous_patterns = [
            '&&', '||', ';', '|', '>', '>>', '<', '$(', '`',
            'rm -rf', 'sudo', 'su ', 'chmod', 'chown'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in command.lower():
                raise ValueError(f"Command contains potentially dangerous pattern: {pattern}")
        
        return command.strip()
    
    def run_command(self, command: str, working_dir: str = None, 
                   capture_output: bool = True, shell: bool = True) -> Dict[str, Any]:
        """
        Execute a system command
        
        Args:
            command: Command to execute
            working_dir: Working directory for the command
            capture_output: Whether to capture stdout and stderr
            shell: Whether to use shell execution
            
        Returns:
            Dictionary with execution results and metadata
        """
        try:
            # Security checks
            if not self._is_command_allowed(command):
                base_cmd = command.strip().split()[0]
                return {
                    'success': False,
                    'error': f"Command '{base_cmd}' is not allowed. Allowed commands: {', '.join(self.allowed_commands)}"
                }
            
            # Sanitize command
            try:
                sanitized_command = self._sanitize_command(command)
            except ValueError as e:
                return {
                    'success': False,
                    'error': str(e)
                }
            
            # Set working directory
            if working_dir and not os.path.exists(working_dir):
                return {
                    'success': False,
                    'error': f"Working directory '{working_dir}' does not exist"
                }
            
            # Execute command
            if shell:
                # Use shell execution
                result = subprocess.run(
                    sanitized_command,
                    shell=True,
                    capture_output=capture_output,
                    text=True,
                    timeout=self.timeout,
                    cwd=working_dir
                )
            else:
                # Use argument list (safer)
                args = shlex.split(sanitized_command)
                result = subprocess.run(
                    args,
                    capture_output=capture_output,
                    text=True,
                    timeout=self.timeout,
                    cwd=working_dir
                )
            
            return {
                'success': True,
                'command': sanitized_command,
                'return_code': result.returncode,
                'stdout': result.stdout if capture_output else None,
                'stderr': result.stderr if capture_output else None,
                'working_dir': working_dir or os.getcwd()
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f"Command timed out after {self.timeout} seconds"
            }
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f"Command failed with return code {e.returncode}",
                'stdout': e.stdout if capture_output else None,
                'stderr': e.stderr if capture_output else None
            }
        except FileNotFoundError:
            return {
                'success': False,
                'error': f"Command not found: {command.split()[0]}"
            }
        except PermissionError:
            return {
                'success': False,
                'error': f"Permission denied executing command: {command}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error executing command: {str(e)}"
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get system information
        
        Returns:
            Dictionary with system information
        """
        try:
            import psutil
            
            # Get CPU info
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Get memory info
            memory = psutil.virtual_memory()
            
            # Get disk info
            disk = psutil.disk_usage('/')
            
            return {
                'success': True,
                'platform': platform.platform(),
                'system': platform.system(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'cpu': {
                    'count': cpu_count,
                    'usage_percent': cpu_percent
                },
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'usage_percent': memory.percent
                },
                'disk': {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'usage_percent': round((disk.used / disk.total) * 100, 1)
                }
            }
        
        except ImportError:
            # Fallback without psutil
            return {
                'success': True,
                'platform': platform.platform(),
                'system': platform.system(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'note': 'Install psutil for detailed system metrics'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error getting system info: {str(e)}"
            }
    
    def list_processes(self, filter_name: str = None) -> Dict[str, Any]:
        """
        List running processes
        
        Args:
            filter_name: Optional filter for process names
            
        Returns:
            Dictionary with process information
        """
        try:
            import psutil
            
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    if filter_name is None or filter_name.lower() in pinfo['name'].lower():
                        processes.append({
                            'pid': pinfo['pid'],
                            'name': pinfo['name'],
                            'cpu_percent': pinfo['cpu_percent'],
                            'memory_percent': round(pinfo['memory_percent'], 2)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            return {
                'success': True,
                'processes': processes[:20],  # Limit to top 20
                'total_count': len(processes),
                'filter': filter_name
            }
            
        except ImportError:
            return {
                'success': False,
                'error': 'psutil not available. Install with: pip install psutil'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error listing processes: {str(e)}"
            }
    
    def get_environment_variables(self, pattern: str = None) -> Dict[str, Any]:
        """
        Get environment variables
        
        Args:
            pattern: Optional pattern to filter variables
            
        Returns:
            Dictionary with environment variables
        """
        try:
            env_vars = {}
            
            for key, value in os.environ.items():
                if pattern is None or pattern.lower() in key.lower():
                    env_vars[key] = value
            
            return {
                'success': True,
                'variables': env_vars,
                'count': len(env_vars),
                'filter': pattern
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error getting environment variables: {str(e)}"
            }
    
    def check_network_connectivity(self, host: str = "8.8.8.8", timeout: int = 5) -> Dict[str, Any]:
        """
        Check network connectivity
        
        Args:
            host: Host to ping (default: Google DNS)
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with connectivity status
        """
        try:
            # Use ping command appropriate for the system
            if self.system == "windows":
                ping_cmd = f"ping -n 1 -w {timeout*1000} {host}"
            else:
                ping_cmd = f"ping -c 1 -W {timeout} {host}"
            
            result = self.run_command(ping_cmd)

            if result.get('success') and result.get('return_code') == 0:
                return {
                    'success': True,
                    'connected': True,
                    'host': host,
                    'message': f"Successfully connected to {host}"
                }
            else:
                return {
                    'success': False,
                    'connected': False,
                    'host': host,
                    'message': f"Could not connect to {host}",
                    'error': result.get('stderr', 'Unknown error')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error checking connectivity: {str(e)}"
            }
    
    def get_current_directory(self) -> Dict[str, Any]:
        """
        Get current working directory
        
        Returns:
            Dictionary with current directory information
        """
        try:
            cwd = os.getcwd()
            return {
                'success': True,
                'current_directory': cwd,
                'exists': os.path.exists(cwd),
                'is_writable': os.access(cwd, os.W_OK)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error getting current directory: {str(e)}"
            }
