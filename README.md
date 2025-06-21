# Jan Assistant Pro

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://docs.astral.sh/ruff/)
[![Tests](https://img.shields.io/badge/tests-comprehensive-green.svg)](#testing)

A **professional-grade**, local-first AI assistant with enterprise-ready architecture and extensible tool system that **works** with Jan.ai.

## 🚀 Features

### Core Capabilities
- 📁 **File Operations**: Read, write, list, copy, and delete files with security controls
- 🧠 **Persistent Memory**: Remember information between sessions with fuzzy search
- 💻 **System Commands**: Execute terminal commands safely with configurable permissions
- 🌐 **Network Connectivity**: Verify connection status using a ping check
- 🎨 **Beautiful GUI**: Dark theme with intuitive interface and status indicators
- ⚡ **Multi-threading**: Responsive, non-blocking interface
- ⏳ **Progress Bar**: See request progress at a glance
- 🔵 **Connection Indicator**: Real-time API status with latency
- ⬆️⬇️ **History Navigation**: Cycle through previous prompts
- ✨ **Autocomplete**: Suggestions while typing commands
- 🧩 **Plugin Loader**: Load third-party tools dynamically

### Enterprise Features ✨ **NEW**
- 🏗️ **Dynamic Tool Registry**: Hot-loadable tool system with automatic validation
- 🛡️ **Structured Error Handling**: Rich error context and debugging information
 - 📊 **Advanced Logging**: JSON logs with correlation IDs, rotation, and audit trails
- ✅ **Configuration Validation**: Schema-based config validation with auto-documentation
- 🧪 **Comprehensive Testing**: Full test suite with high coverage and CI/CD ready
- 🔧 **Professional Architecture**: Clean MVC separation with extensible design
- 📣 **Event Manager**: Subscribe to configuration change notifications
- 🔒 **Privacy First**: Everything runs locally, your data stays yours
- ⚙️ **Enterprise Configuration**: Validated JSON configuration with rich schemas
- 📈 **Prometheus Metrics**: Built-in metrics endpoint for monitoring
- 🩺 **Health Checks**: Monitor API availability, memory, and disk space
- ♻️ **Degraded Mode**: Cached tool output shown when the API is unreachable

## 📸 Screenshots

| Main Interface | Memory Manager | Settings |
|---|---|---|
| ![Main](assets/main-interface.png) | ![Memory](assets/memory-manager.png) | ![Settings](assets/settings.png) |

The main view shows a progress bar at the top-right and a colored connection indicator
next to the send button. Use the up/down arrow keys to navigate your message history,
and enjoy inline autocomplete suggestions while typing.

## 📋 Requirements

- **Python 3.8+**
- **Jan.ai** running locally (or any OpenAI-compatible API)
- **Operating System**: Windows, macOS, or Linux
- **Memory**: 4GB RAM minimum
- **Storage**: 100MB free space

### Dependencies
- `requests` - HTTP client for API communication
- `tkinter` - GUI framework (usually included with Python)
- `psutil` - System monitoring (optional extra via `poetry install --with system`)

## 🛠️ Installation

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/CreativeNewEra/jan-assistant-pro.git
   cd jan-assistant-pro
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Configure your API settings**:
   ```bash
 cp config/config.example.json config/config.json
 # Edit config.json with your API details
 ```
  You can also set the API key via the `JAN_API_KEY` environment variable. When
  using `SecureConfig`, the key is saved to your system keyring after the first
  prompt.

4. **Run the application**:
   ```bash
   python main.py
   ```

### Development Installation

For development with additional tools:

```bash
# Clone and enter directory
git clone https://github.com/CreativeNewEra/jan-assistant-pro.git
cd jan-assistant-pro


# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest tests/

# Install git hooks
pre-commit install
```
Running this command sets up git hooks so Ruff and mypy run automatically
before each commit.

## ⚙️ Configuration

Edit `config/config.json` to customize settings:

```json
{
  "api": {
    "base_url": "http://127.0.0.1:1337/v1",
    "api_key": "your-api-key",
    "model": "qwen3:30b-a3b"
  },
  "memory": {
    "file": "data/memory.json",
    "max_entries": 1000
  },
  "ui": {
    "theme": "dark",
    "window_size": "800x600"
  },
  "security": {
    "allowed_commands": ["ls", "pwd", "date", "whoami", "echo", "cat", "head", "tail", "grep"],
    "restricted_paths": ["/etc", "/sys"]
  }
}
```

To enable the network connectivity check, add `"ping"` to `allowed_commands`.

### Cache Management

Jan Assistant Pro caches API responses, disk operations and configuration files
to improve performance. Adjust cache sizes and expiration in `config/config.json`:

```json
"cache": {
  "api": {"size": 64, "ttl": 300},
  "disk": {"dir": "data/cache", "ttl": 86400},
  "config": {"ttl": 60}
}
```

Set a value to `0` to disable a cache. TTL values are in seconds.

To clear all caches, delete the contents of the `data/cache` directory and
restart the application.

### Database Migrations

The SQLite memory database is versioned with a lightweight migration system.
Migrations are stored in `src/migrations/` and run automatically when the
`EnhancedMemoryManager` starts. You can apply or rollback migrations manually:

```bash
python -m src.core.migration_manager data/memory.sqlite        # apply pending
python -m src.core.migration_manager data/memory.sqlite --rollback 1
```

### Degraded Mode

If the connection to the language model fails, Jan Assistant Pro enters a
degraded mode. The last successful tool output is returned so you can keep
working offline. The incident is logged and normal responses resume once the
API becomes available.

### Jan.ai Setup

1. **Download and install** [Jan.ai](https://jan.ai)
2. **Load your preferred model** (e.g., Qwen3, Mistral, Llama)
3. **Enable API server** in Jan settings
4. **Note the API endpoint** (usually `http://127.0.0.1:1337`)
5. **Create API key** in Jan settings
6. **Update config.json** with your settings

## 🎯 Quick Start Guide

### First Steps

1. **Start Jan.ai** and load your model
2. **Run Jan Assistant Pro**: `python main.py`
3. **Test the connection**: Click "🔧 Test API" button
4. **Try basic commands**:

### Example Commands

**File Operations:**
```
write a Python hello world script to hello.py
read the file hello.py
list files in current directory
copy hello.py to backup.py
```

**Memory System:**
```
remember my favorite programming language is Python
remember my project name is jan-assistant-pro
what do you recall about my favorite programming language?
search memory for programming
```

**System Commands:**
```
run command ls -la
check system information
get current directory
```

## 🏗️ Enterprise Architecture

### Project Structure

```
jan-assistant-pro/
├── main.py                          # Application entry point
├── src/
│   ├── core/                        # Core application logic
│   │   ├── app_controller.py        # ✨ NEW: Application controller (MVC)
│   │   ├── config.py                # Configuration management
│   │   ├── enhanced_config.py       # ✨ NEW: Env-based config
│   │   ├── config_validator.py      # ✨ NEW: Schema validation
│   │   ├── exceptions.py            # ✨ NEW: Structured error handling
│   │   ├── logging_config.py        # ✨ NEW: Advanced logging system
│   │   ├── api_client.py            # API communication
│   │   └── memory.py                # Memory management
│   ├── gui/
│   │   └── main_window.py           # 🔄 REFACTORED: Clean UI layer
│   └── tools/                       # ✨ NEW: Dynamic tool system
│       ├── base_tool.py             # ✨ NEW: Tool interface
│       ├── tool_registry.py         # ✨ NEW: Dynamic registry
│       ├── file_tools.py            # File operations
│       └── system_tools.py          # System commands
├── tests/                           # ✨ NEW: Comprehensive test suite
│   ├── test_enhanced_features.py    # ✨ NEW: Integration tests
│   ├── test_api_client.py          # API client tests
│   ├── test_file_tools.py          # File tools tests
│   ├── test_memory_manager.py      # Memory tests
│   └── test_system_tools.py        # System tools tests
├── config/
│   ├── config.example.json         # Example configuration
│   └── config.json                 # User configuration
└── docs/                           # Documentation
    ├── REFACTORING_SUMMARY.md      # ✨ NEW: Architecture changes
    └── HIGH_IMPACT_IMPROVEMENTS_SUMMARY.md  # ✨ NEW: Enhancement guide
```

### Enterprise Components

- **🏛️ MVC Architecture**: Clean separation between View, Controller, and Model layers
- **🔧 Dynamic Tool Registry**: Automatic tool discovery, validation, and execution
- **⚡ App Controller**: Centralized business logic with clean API
- **🛡️ Exception Hierarchy**: Structured error handling with rich context
- **📊 Advanced Logging**: JSON logging, rotation, audit trails, and performance monitoring
- **✅ Config Validation**: Schema-based validation with auto-generated documentation
- **🧪 Testing Framework**: Comprehensive test suite with mocks and integration tests
- **🔒 Security Layer**: Input validation, path restrictions, and audit logging
- **📚 Auto Documentation**: Self-documenting tools and configuration schemas

## 🔧 Development

### Adding New Tools (Simplified) ✨

The new dynamic tool registry makes adding tools incredibly simple:

1. **Create your tool class** inheriting from `BaseTool`:
   ```python
   from tools.base_tool import BaseTool, ToolInfo, ToolParameter
   
   class WeatherTool(BaseTool):
       def get_tool_info(self) -> ToolInfo:
           return ToolInfo(
               name="weather",
               description="Get weather information for a city",
               category="utilities",
               parameters=[
                   ToolParameter("city", "City name", str, required=True),
                   ToolParameter("units", "Temperature units", str, 
                               required=False, default="celsius")
               ],
               examples=["Get weather for Tokyo", "Check weather in Paris"]
           )
       
       def execute(self, **kwargs) -> Dict[str, Any]:
           city = kwargs['city']
           units = kwargs.get('units', 'celsius')
           
           # Your weather API logic here
           weather_data = get_weather(city, units)
           
           return self._create_success_response(weather_data)
   ```

2. **Register the tool** (automatic with registry):
   ```python
   from tools.tool_registry import register_tool
   
   # Registration is this simple!
   register_tool(WeatherTool)
   ```

**That's it!** Your tool now has:
- ✅ Automatic parameter validation
- ✅ Built-in help generation
- ✅ Error handling and logging
- ✅ Integration with the UI
- ✅ No manual string parsing needed

### Legacy Tool Migration

Existing tools can be easily migrated to the new system. See `docs/REFACTORING_SUMMARY.md` for migration guides.

### Testing ✨

Our comprehensive testing framework ensures code quality:

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=src/ --cov-report=html

# Run specific test suites
python -m pytest tests/test_enhanced_features.py -v     # New features
python -m pytest tests/test_memory_manager.py -v       # Memory system
python -m pytest tests/test_file_tools.py -v          # File operations

# Run performance benchmarks
python -m pytest tests/test_performance.py --benchmark-only -v

# Generate coverage report
coverage html  # Creates htmlcov/ directory
```

**Test Coverage:**
- 🧪 **Unit Tests**: Individual component testing
- 🔗 **Integration Tests**: Cross-component interaction testing
- 🎭 **Mock Testing**: External dependency isolation
- 🏗️ **Architecture Tests**: Design pattern validation
- 🚨 **Error Testing**: Exception handling verification
- ⚡ **Performance Tests**: Speed and memory benchmarks

#### Coverage Results

CI runs tests with `pytest-cov` and saves a `coverage.xml` artifact. Download this
file from the workflow run or connect Codecov for detailed coverage reports.

### Code Style

```bash
# Format code
ruff format src/ tests/

# Check style
ruff src/ tests/

# Type checking
mypy src/
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Contribution Steps

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes and test**: `python -m pytest tests/`
4. **Commit changes**: `git commit -m 'feat: add amazing feature'`
5. **Push branch**: `git push origin feature/amazing-feature`
6. **Open Pull Request**

### Development Roadmap

#### ✅ **v0.2.0 - Enterprise Foundation (COMPLETED)**
- [x] **Dynamic Tool Registry**: Hot-loadable tool system
- [x] **Structured Error Handling**: Rich error context and debugging
- [x] **Advanced Logging**: Production-ready logging infrastructure
- [x] **Configuration Validation**: Schema-based validation
- [x] **Comprehensive Testing**: Full test suite with high coverage
- [x] **MVC Architecture**: Clean separation of concerns

#### 🚀 **v0.3.0 - Plugin Ecosystem**
- [x] **Plugin System**: Third-party tool plugins with hot-loading
- [ ] **Tool Marketplace**: Community tool sharing and installation
- [ ] **Web Search Tools**: Internet search and web scraping capabilities
- [ ] **Calendar Integration**: Schedule management and reminders
- [ ] **Email Tools**: Email composition and management

#### 🔮 **v0.4.0 - Advanced Features (Planned)**
- [ ] **Voice Interface**: Speech recognition and text-to-speech
- [ ] **Web Dashboard**: Browser-based interface with REST API
- [ ] **Multi-User Support**: User profiles and collaboration features
- [ ] **Advanced Analytics**: Usage statistics and performance monitoring
- [ ] **Cloud Integration**: Deploy as a service with horizontal scaling

#### 🌟 **v0.5.0 - AI Enhancement (Future)**
- [ ] **Model Fine-tuning**: Custom model training for specific tasks
- [ ] **Intelligent Automation**: AI-driven workflow automation
- [ ] **Advanced Memory**: Vector embeddings and semantic search
- [ ] **Multi-Modal Support**: Image, audio, and video processing

## 🐛 Troubleshooting

### Common Issues

**"Engine is not loaded yet"**
- Start your model in Jan.ai before using the assistant
- Check that Jan's API server is enabled

**GUI not opening on Linux**
- Install tkinter: `sudo apt-get install python3-tk`
- Check display settings: `echo $DISPLAY`

**API connection failed**
- Verify Jan.ai is running
- Check API endpoint in config.json
- Ensure API key is correct

**Memory not persisting**
- Check file permissions in data directory
- Verify config.json has correct memory.file path

### Getting Help

- 📖 Check our [Documentation](docs/)
- 💡 Build API docs locally with `make html` in the `docs` directory
- 🐛 Open an [Issue](https://github.com/CreativeNewEra/jan-assistant-pro/issues)
- 💬 Start a [Discussion](https://github.com/CreativeNewEra/jan-assistant-pro/discussions)
- 💝 Join our [Discord](https://discord.gg/your-discord-link)

## 🔐 Security

### Security Features

- **Command filtering**: Only allowed commands can be executed
- **Path restrictions**: Prevents access to sensitive system directories
- **File size limits**: Prevents processing of extremely large files
- **Local processing**: All data stays on your machine

### Security Best Practices

- Review allowed commands in config.json
- Don't add sensitive directories to file access
- Keep API keys secure and don't commit them
- Regularly update dependencies

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[Jan.ai](https://jan.ai)** for the excellent local LLM platform
- **[Anthropic](https://anthropic.com)** for MCP inspiration and Claude's assistance
- **The open-source AI community** for making local AI accessible
- **Contributors** who help improve this project

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=CreativeNewEra/jan-assistant-pro&type=Timeline)](https://star-history.com/#CreativeNewEra/jan-assistant-pro&Timeline)
## 🚀 What's Next?

- **Try it out** and give us feedback!
- **Star the repository** if you find it useful
- **Share with others** who might benefit
- **Contribute** new features or improvements
- **Join our community** for support and discussions

---

**Built with ❤️ for the local-first AI community**

[Report Bug](https://github.com/CreativeNewEra/jan-assistant-pro/issues) · [Request Feature](https://github.com/CreativeNewEra/jan-assistant-pro/issues) · [Join Discussion](https://github.com/CreativeNewEra/jan-assistant-pro/discussions)
