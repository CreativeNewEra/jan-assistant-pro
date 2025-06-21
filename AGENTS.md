# Jan Assistant Pro - AI Agent Configuration

## Overview
Jan Assistant Pro is an AI assistant that operates locally with a set of modular tools. It communicates with Jan.ai-compatible LLM APIs and provides a chat interface, persistent memory, system command execution and file manipulation.

## Agent Capabilities

### Core Functions
- **Chat Interface**: Hold natural conversations and keep context across messages
- **Memory System**: Persist information across sessions
- **Tool Integration**: Easily extend the assistant by adding tools
- **Plugin System**: Load external tool plugins on the fly
- **Event Notifications**: Subscribe to configuration and app events
- **Multi-threading**: GUI remains responsive while operations run in the background
- **Structured Logging**: Correlation IDs for tracing requests
- **Health Checks**: Monitor API, memory and disk usage

### Available Tools

#### File Operations (`file_tools.py`)
- `read_file` – read a text file
- `write_file` – create or overwrite a file
- `append_file` – append to an existing file
- `list_files` – list directory contents
- `copy_file` – copy files
- `delete_file` – remove files safely
- `get_file_info` – fetch file metadata

Security features:
- Restricts access to paths like `/etc`, `/sys` and `/proc`
- Limits file size (default 10MB)
- Validates allowed file extensions when writing

#### System Operations (`system_tools.py`)
- `run_command` – execute a shell command
- `get_system_info` – show CPU, memory and disk info
- `list_processes` – list running processes
- `check_network_connectivity` – verify network status with ping
- `get_environment_variables` – show environment variables
- `get_current_directory` – show the current working directory

Security features:
- Only allowed commands run (configurable whitelist)
- Detects dangerous patterns like `&&` or `rm -rf`
- Commands time out after a configurable period (30s default)
- Validates the working directory

#### Memory Operations (`memory.py`)
- `remember` – store information with a key and category
- `recall` – retrieve stored info
- `fuzzy_recall` – search memory with partial terms
- `forget` – remove a memory entry
- `list_memories` – list all stored memories
- `import/export` – backup or restore memory

Features:
- Thread‑safe using `RLock`
- Automatic cleanup with a max entry limit
- Tracks timestamps and access counts
- Organizes items by category

## Agent Prompting Framework

### Tool Invocation Syntax
Use the following prefixes to trigger tools:

```
FILE OPERATIONS:
- TOOL_READ_FILE: filename
- TOOL_WRITE_FILE: filename|content
- TOOL_LIST_FILES: directory_path
- TOOL_COPY_FILE: source|destination
- TOOL_DELETE_FILE: filename

MEMORY OPERATIONS:
- TOOL_REMEMBER: key|value|category
- TOOL_RECALL: key
- TOOL_SEARCH_MEMORY: search_term

SYSTEM OPERATIONS:
- TOOL_COMMAND: command
- TOOL_SYSTEM_INFO
- TOOL_PROCESSES: filter_name
```

### System Message Template
```
You are Jan Assistant Pro, a helpful AI assistant with access to advanced tools.
When the user asks you to perform file operations, memory operations, or system
commands, respond with the appropriate TOOL_ prefix followed by the required parameters.

After using a tool, I'll provide the result and you can respond naturally to the user.
```

## Configuration Schema

### Required Settings
```json
{
  "api": {
    "base_url": "http://127.0.0.1:1337/v1",
    "api_key": "your-api-key",
    "model": "model-name",
    "timeout": 30
  },
  "memory": {
    "file": "data/memory.json",
    "max_entries": 1000,
    "auto_save": true
  },
  "security": {
    "allowed_commands": ["ls", "pwd", "cat", "echo", "ping"],
    "restricted_paths": ["/etc", "/sys", "/proc"],
    "max_file_size": "10MB"
  }
}
```

## Agent Behavior Guidelines

### Security Principles
1. **Least Privilege** – only allow necessary commands and paths
2. **Input Validation** – sanitize user inputs before tool execution
3. **Output Filtering** – limit large outputs
4. **Error Handling** – degrade gracefully and provide helpful messages

### Response Patterns
- **Success** – confirm the action and include relevant details
- **Errors** – explain failures and suggest alternatives
- **Large Output** – summarize results and offer more detail on request
- **Security Blocks** – mention restrictions without revealing security rules

### Memory Management
- Organize memories by category
- Reference prior conversations when relevant
- Do not store sensitive information like passwords or keys

## Development Guidelines

### Adding New Tools
1. Create a tool class in `src/tools/`
2. Methods should return `{"success": bool, "data": any, "error": str}`
3. Add security checks relevant to the tool
4. Update the system message template with the new tool syntax
5. Add tests for success and failure cases
6. Update this file with the new capability

### Error Handling Strategy
- Use the `JanAssistantError` exception hierarchy
- Log errors but show user-friendly messages
- Retry transient failures when appropriate
- Fail gracefully when a tool is unavailable

### Testing Requirements
- Unit tests for each tool
- Integration tests for tool chains
- Security tests using malicious inputs
- Performance tests for large operations
- Mock external dependencies in tests

## API Integration

### Supported Providers
- **Primary** – Jan.ai (local LLM processing)
- **Compatible** – any OpenAI-style API endpoint
- **Authentication** – Bearer token or API key

### Model Requirements
- Must support chat-completion format
- Should handle system messages for tool invocation
- Models with good instruction following (Qwen, Llama, Mistral) are recommended

## Deployment Considerations

### Dependencies
- Python 3.8+
- tkinter
- requests
- psutil (optional)

### Resource Requirements
- 4GB RAM minimum
- ~100MB storage for the app and config (model storage extra)
- Local network access for Jan.ai

### Security Hardening
- Run with minimal user privileges
- Firewall rules should only allow Jan.ai communication
- Keep dependencies updated
- Review allowed commands and paths regularly

## Future Roadmap

### Planned Features
- Web search integration
- Calendar/email tools
- Voice interface
- Plugin system (implemented)
- Multi-user support
- Web dashboard

### Extensibility Points
- Modular tool system
- Configuration-driven security policies
- UI theming
- Memory backend abstraction
- API provider abstraction

---

*Update this document whenever new tools, capabilities, or security features are added.*
