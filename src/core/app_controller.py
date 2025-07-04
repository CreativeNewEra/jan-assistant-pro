"""
Application Controller for Jan Assistant Pro
Handles the main application logic, decoupling it from the GUI.
"""

from typing import Any, Callable, Dict, List

from src.core.api_client import APIClient, APIError
from src.core.circuit_breaker import CircuitBreaker
from src.core.config import Config
from src.core.history import (
    FileWriteCommand,
    MemoryRememberCommand,
    UndoRedoManager,
)
from src.core.logging_config import LoggerMixin
from src.core.memory import MemoryManager
from src.tools.file_tools import FileTools
from src.tools.system_tools import SystemTools


class AppController(LoggerMixin):
    """Handles the core application logic."""

    def __init__(self, config: Config):
        self.config = config
        self.conversation_history: List[Dict[str, str]] = []
        self.last_tool_result: str | None = None

        # Initialize core components
        self.api_client = APIClient(
            base_url=config.api_base_url,
            api_key=config.api_key,
            model=config.model_name,
            timeout=int(config.get("api.timeout", 30)),
            cache_enabled=bool(config.get("api.cache_enabled", False)),
            cache_ttl=int(config.get("api.cache_ttl", 300)),
            cache_size=int(config.get("api.cache_size", 128)),
            circuit_breaker=CircuitBreaker(
                fail_max=config.breaker_fail_max,
                reset_timeout=config.breaker_reset_timeout,
            ),
        )

        self.memory_manager = MemoryManager(
            memory_file=config.memory_file,
            max_entries=int(config.get("memory.max_entries", 1000)),
            auto_save=bool(config.get("memory.auto_save", True)),
        )

        # Initialize tools
        self.file_tools = FileTools(
            max_file_size=str(config.get("security.max_file_size", "10MB")),
            restricted_paths=list(config.get("security.restricted_paths", [])),
        )

        self.system_tools = SystemTools(
            allowed_commands=list(config.get("security.allowed_commands", [])),
            timeout=int(config.get("api.timeout", 30)),
        )

        # History manager for undo/redo
        self.history = UndoRedoManager()

    def process_message(
        self,
        message: str,
        *,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Dict[str, Any]:
        """
        Processes a user message, interacts with the API and tools,
        and returns the response.
        """
        try:
            response = self._chat_with_tools(message, progress_callback)
            return {"type": "assistant", "content": response}
        except Exception as e:
            return {"type": "error", "content": f"Error: {str(e)}"}

    def _chat_with_tools(
        self,
        message: str,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> str:
        """Chat with tools available"""
        system_message = self._get_system_prompt()

        messages = [{"role": "system", "content": system_message}]

        messages.extend(self.conversation_history[-6:])
        messages.append({"role": "user", "content": message})

        try:
            response_data = self.api_client.chat_completion(messages)
            response = self.api_client.extract_content(response_data)
        except APIError as e:
            self.log_error("Initial API call failed", error=str(e))
            if self.last_tool_result:
                return (
                    "\u26a0\ufe0f Language model unavailable. "
                    "Using last tool result:\n" + self.last_tool_result
                )
            return (
                "\u26a0\ufe0f Unable to reach the language model. "
                "Please try again later."
            )

        if "TOOL_" in response:
            tool_result = self._handle_tool_call(response, progress_callback)

            messages.append({"role": "assistant", "content": response})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"Tool result: {tool_result}. "
                        "Please respond to the user based on this result."
                    ),
                }
            )

            try:
                final_response_data = self.api_client.chat_completion(messages)
                final_response = self.api_client.extract_content(final_response_data)

                self.conversation_history.append({"role": "user", "content": message})
                self.conversation_history.append(
                    {"role": "assistant", "content": final_response}
                )

                return final_response
            except APIError as e:
                self.log_error("Final API call failed", error=str(e))
                if self.last_tool_result:
                    return (
                        "\u26a0\ufe0f Language model unavailable. "
                        "Using cached tool result:\n" + self.last_tool_result
                    )
                return "\u26a0\ufe0f Unable to reach the language model for final response."
        else:
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": response})
            return response

    def _handle_tool_call(
        self,
        response: str,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> str:
        """Handle tool calls"""
        response = response.strip()

        # File tools
        if "TOOL_READ_FILE:" in response:
            filename = response.split("TOOL_READ_FILE:")[1].strip()
            result = self.file_tools.read_file(filename)
            formatted = self._format_tool_result(result)
            self.last_tool_result = formatted
            return formatted

        elif "TOOL_WRITE_FILE:" in response:
            parts = response.split("TOOL_WRITE_FILE:")[1].strip().split("|", 1)
            filename = parts[0].strip()
            content = parts[1].strip() if len(parts) > 1 else ""
            cmd = FileWriteCommand(self.file_tools, filename, content)
            result = self.history.execute(cmd)
            formatted = self._format_tool_result(result)
            self.last_tool_result = formatted
            return formatted

        elif "TOOL_LIST_FILES:" in response:
            directory = response.split("TOOL_LIST_FILES:")[1].strip() or "."
            result = self.file_tools.list_files(
                directory, progress_callback=progress_callback
            )
            formatted = self._format_tool_result(result)
            self.last_tool_result = formatted
            return formatted

        elif "TOOL_COPY_FILE:" in response:
            parts = response.split("TOOL_COPY_FILE:")[1].strip().split("|", 1)
            if len(parts) >= 2:
                source, destination = parts[0].strip(), parts[1].strip()
                result = self.file_tools.copy_file(
                    source, destination, progress_callback=progress_callback
                )
                formatted = self._format_tool_result(result)
                self.last_tool_result = formatted
                return formatted
            else:
                return "Error: Copy file requires source and destination"

        elif "TOOL_DELETE_FILE:" in response:
            filename = response.split("TOOL_DELETE_FILE:")[1].strip()
            result = self.file_tools.delete_file(filename)
            formatted = self._format_tool_result(result)
            self.last_tool_result = formatted
            return formatted

        # Memory tools
        elif "TOOL_REMEMBER:" in response:
            parts = response.split("TOOL_REMEMBER:")[1].strip().split("|")
            key = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""
            category = parts[2].strip() if len(parts) > 2 else "general"

            cmd = MemoryRememberCommand(self.memory_manager, key, value, category)
            success = self.history.execute(cmd)
            result = (
                f"Successfully remembered: {key} = {value}"
                if success
                else "Failed to store memory"
            )
            self.last_tool_result = result
            return result

        elif "TOOL_RECALL:" in response:
            key = response.split("TOOL_RECALL:")[1].strip()
            memory = self.memory_manager.recall(key)
            if memory:
                result = f"Recalled: {key} = {memory['value']} (stored on {memory['timestamp']})"
                self.last_tool_result = result
                return result
            else:
                # Try fuzzy search
                matches = self.memory_manager.fuzzy_recall(key)
                if matches:
                    similar = [f"{k}: {v['value']}" for k, v in matches[:3]]
                    result = "Found similar memories: " + ", ".join(similar)
                    self.last_tool_result = result
                    return result
                else:
                    result = f"No memory found for: {key}"
                    self.last_tool_result = result
                    return result

        elif "TOOL_SEARCH_MEMORY:" in response:
            search_term = response.split("TOOL_SEARCH_MEMORY:")[1].strip()
            matches = self.memory_manager.fuzzy_recall(search_term)
            if matches:
                results = [f"• {k}: {v['value']}" for k, v in matches[:5]]
                result = f"Memory search results for '{search_term}':\n" + "\n".join(
                    results
                )
                self.last_tool_result = result
                return result
            else:
                result = f"No memories found matching: {search_term}"
                self.last_tool_result = result
                return result

        # System tools
        elif "TOOL_COMMAND:" in response:
            command = response.split("TOOL_COMMAND:")[1].strip()
            result = self.system_tools.run_command(command)
            formatted = self._format_tool_result(result)
            self.last_tool_result = formatted
            return formatted

        elif "TOOL_SYSTEM_INFO" in response:
            result = self.system_tools.get_system_info()
            formatted = self._format_tool_result(result)
            self.last_tool_result = formatted
            return formatted

        elif "TOOL_PROCESSES:" in response:
            filter_name = response.split("TOOL_PROCESSES:")[1].strip() or None
            result = self.system_tools.list_processes(filter_name)
            formatted = self._format_tool_result(result)
            self.last_tool_result = formatted
            return formatted

        return "Tool not recognized"

    def _format_tool_result(self, result: Dict[str, Any]) -> str:
        """Format tool result for display"""
        if not result.get("success", False):
            return f"❌ Error: {result.get('error', 'Unknown error')}"

        if "content" in result:
            return f"📄 File content:\n{result['content']}"
        elif "files" in result and "directories" in result:
            files = result["files"]
            dirs = result["directories"]
            output = f"📁 Directory: {result['directory']}\n"
            if dirs:
                output += f"Directories ({len(dirs)}):\n"
                for d in dirs[:10]:
                    output += f"  📁 {d['name']}\n"
            if files:
                output += f"Files ({len(files)}):\n"
                for f in files[:10]:
                    size = f"({f['size']} bytes)" if f.get("size") else ""
                    output += f"  📄 {f['name']} {size}\n"
            return output
        elif "stdout" in result:
            output = "✅ Command executed successfully"
            if result.get("stdout"):
                output += f"\nOutput:\n{result['stdout']}"
            if result.get("stderr"):
                output += f"\nErrors:\n{result['stderr']}"
            return output
        else:
            return "✅ Operation completed successfully"

    def _get_system_prompt(self) -> str:
        """Returns the system prompt for the AI."""
        return (
            "You are Jan Assistant Pro, a helpful AI assistant with access "
            "to advanced tools. When the user asks you to:\n\n"
            "FILE OPERATIONS:\n"
            '- READ a file: respond with "TOOL_READ_FILE: filename"\n'
            '- WRITE to a file: respond with "TOOL_WRITE_FILE: filename|content"\n'
            '- LIST files: respond with "TOOL_LIST_FILES: directory_path"\n'
            '- COPY file: respond with "TOOL_COPY_FILE: source|destination"\n'
            '- DELETE file: respond with "TOOL_DELETE_FILE: filename"\n\n'
            "MEMORY OPERATIONS:\n"
            '- REMEMBER something: respond with "TOOL_REMEMBER: key|value|category"\n'
            '- RECALL something: respond with "TOOL_RECALL: key"\n'
            '- SEARCH memory: respond with "TOOL_SEARCH_MEMORY: search_term"\n\n'
            "SYSTEM OPERATIONS:\n"
            '- RUN a command: respond with "TOOL_COMMAND: command"\n'
            '- GET system info: respond with "TOOL_SYSTEM_INFO"\n'
            '- CHECK processes: respond with "TOOL_PROCESSES: filter_name"\n\n'
            "After using a tool, I'll give you the result and you can respond "
            "normally to the user."
        )

    def test_api_connection(self):
        return self.api_client.test_connection()

    def get_welcome_message(self) -> str:
        """Get welcome message"""
        return (
            "Hello! I'm your Jan Assistant Pro with advanced tools. I can:\n\n"
            "📁 **File Operations**:\n"
            '   • "read file example.txt"\n'
            '   • "write python script to hello.py"\n'
            '   • "list files in current directory"\n\n'
            "🧠 **Memory Management**:\n"
            '   • "remember my favorite color is blue"\n'
            '   • "what do you recall about my preferences?"\n\n'
            "💻 **System Commands**:\n"
            '   • "run command ls -la"\n'
            '   • "check system information"\n'
            '   • "get current directory"\n\n'
            "🔧 **Advanced Features**:\n"
            "   • Persistent memory between sessions\n"
            "   • Secure command execution\n"
            "   • Configuration management\n"
            "   • API health monitoring\n\n"
            "What would you like me to help you with?"
        )

    def undo_last(self) -> bool:
        """Undo the last file or memory operation."""
        return self.history.undo_last()

    def redo_last(self) -> bool:
        """Redo the last undone operation."""
        return self.history.redo_last()
