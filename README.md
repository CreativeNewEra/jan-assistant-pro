# Jan Assistant Pro

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A powerful, local-first AI assistant with tools that works with [Jan.ai](https://jan.ai) and other OpenAI-compatible APIs.

![Jan Assistant Pro Screenshot](assets/screenshot.png)

## 🚀 Features

- 📁 **File Operations**: Read, write, list, copy, and delete files with security controls
- 🧠 **Persistent Memory**: Remember information between sessions with fuzzy search
- 💻 **System Commands**: Execute terminal commands safely with configurable permissions
- 🎨 **Beautiful GUI**: Dark theme with intuitive interface and status indicators
- ⚡ **Multi-threading**: Responsive, non-blocking interface
- 🔧 **Tool System**: Extensible framework for adding new capabilities
- 🔒 **Privacy First**: Everything runs locally, your data stays yours
- ⚙️ **Configurable**: JSON-based configuration for all settings
- 🏗️ **Modular Architecture**: Clean, extensible codebase for developers

## 📸 Screenshots

| Main Interface | Memory Manager | Settings |
|---|---|---|
| ![Main](assets/main-interface.png) | ![Memory](assets/memory-manager.png) | ![Settings](assets/settings.png) |

## 📋 Requirements

- **Python 3.8+**
- **Jan.ai** running locally (or any OpenAI-compatible API)
- **Operating System**: Windows, macOS, or Linux
- **Memory**: 4GB RAM minimum
- **Storage**: 100MB free space

### Dependencies
- `requests` - HTTP client for API communication
- `tkinter` - GUI framework (usually included with Python)
- `psutil` - System monitoring (optional but recommended)

## 🛠️ Installation

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/CreativeNewEra/jan-assistant-pro.git
   cd jan-assistant-pro
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your API settings**:
   ```bash
   cp config/config.example.json config/config.json
   # Edit config.json with your API details
   ```

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

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -e .[dev]

# Run tests
python -m pytest tests/
```

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
    "allowed_commands": ["ls", "pwd", "python3"],
    "restricted_paths": ["/etc", "/sys"]
  }
}
```

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

## 🏗️ Architecture

### Project Structure

```
jan-assistant-pro/
├── main.py                 # Application entry point
├── src/
│   ├── core/
│   │   ├── config.py       # Configuration management
│   │   ├── api_client.py   # API communication
│   │   └── memory.py       # Memory management
│   ├── gui/
│   │   └── main_window.py  # Main GUI interface
│   └── tools/
│       ├── file_tools.py   # File operations
│       └── system_tools.py # System commands
├── config/
│   ├── config.example.json # Example configuration
│   └── config.json         # User configuration
├── tests/                  # Test suite
└── docs/                   # Documentation
```

### Core Components

- **Config Manager**: JSON-based configuration with dot notation access
- **API Client**: Robust OpenAI-compatible API client with error handling
- **Memory Manager**: Persistent storage with fuzzy search capabilities
- **Tool System**: Modular architecture for extensible functionality
- **GUI Framework**: Professional interface with threading support

## 🔧 Development

### Adding New Tools

1. **Create tool class** in `src/tools/`:
   ```python
   class NewTool:
       def __init__(self, config_param):
           self.config_param = config_param
       
       def tool_method(self, input_param):
           return {"success": True, "result": "Tool output"}
   ```

2. **Add to main window**:
   ```python
   # In __init__
   self.new_tool = NewTool(config.get('new_tool.setting'))
   
   # In handle_tool_call
   elif "TOOL_NEW_OPERATION:" in response:
       result = self.new_tool.tool_method(param)
       return self._format_tool_result(result)
   ```

3. **Update system message** with new tool syntax

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src/

# Run specific test
python -m pytest tests/test_memory_manager.py -v
```

### Code Style

```bash
# Format code
black src/ tests/

# Check style
flake8 src/ tests/

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

- [ ] **v0.2.0**: Web search, calendar integration, email tools
- [ ] **v0.3.0**: Voice interface, web dashboard, plugin system
- [ ] **v0.4.0**: Multi-user support, collaboration features

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
