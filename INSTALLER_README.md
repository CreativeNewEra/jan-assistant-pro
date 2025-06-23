# Jan Assistant Pro - One-Click Installation Guide

This guide covers the new one-click installation and startup system for Jan Assistant Pro.

## 🚀 Quick Start

### One-Click Installation

```bash
# Interactive installation with configuration wizard
python install_wizard.py

# Quick installation with minimal interaction
python install_wizard.py --quick

# Development installation with dev dependencies
python install_wizard.py --dev
```

### One-Click Startup

```bash
# Smart launcher with pre-flight checks
./start.sh

# Or using Make
make start

# Direct startup (minimal checks)
python main.py
```

## 📦 Installation Options

### Interactive Installer (`install_wizard.py`)

The advanced installer provides a complete setup experience:

- ✅ **System Requirements Check** - Validates Python, dependencies, permissions
- 🔧 **Dependency Management** - Auto-installs Poetry/pip dependencies  
- 🌐 **API Provider Wizard** - Configure OpenAI, Anthropic, local services, or custom APIs
- 🔒 **Security Configuration** - Choose security level and permissions
- 🎨 **UI Preferences** - Theme, window size, fonts
- ⚙️ **Feature Selection** - Enable/disable specific capabilities
- 💾 **Auto-Configuration** - Generates optimized config files

#### Command Line Options

```bash
# Full interactive setup
python install_wizard.py

# Quick setup with auto-detection
python install_wizard.py --quick

# Development setup with dev dependencies
python install_wizard.py --dev

# Skip system checks (not recommended)
python install_wizard.py --skip-checks

# Pre-configure API provider
python install_wizard.py --provider=openai --api-key=sk-...
```

### API Provider Support

The installer automatically detects and supports:

**Local Services:**
- 🏠 **Jan.ai** - `http://127.0.0.1:1337/v1`
- 🦙 **Ollama** - `http://127.0.0.1:11434/v1` 
- 🧠 **LM Studio** - `http://127.0.0.1:1234/v1`
- 🌐 **Text Generation WebUI** - `http://127.0.0.1:5000/v1`

**Cloud Services:**
- 🤖 **OpenAI** - GPT-4, GPT-3.5, etc.
- 🧠 **Anthropic Claude** - Claude-3 models
- 🔧 **Custom OpenAI-compatible APIs**

## 🛠️ Development Workflow

### New Developer Setup

```bash
# Clone repository
git clone https://github.com/CreativeNewEra/jan-assistant-pro.git
cd jan-assistant-pro

# One-command development setup
make dev-setup
```

This will:
1. Install Poetry dependencies with dev tools
2. Set up pre-commit hooks
3. Run quick configuration wizard
4. Create development-optimized config

### Make Commands

```bash
# Installation
make install           # Install dependencies
make install-wizard    # Run interactive installer
make quick-install     # Run quick installer
make system-check      # Check system requirements

# Development
make dev-setup         # Complete development setup
make test              # Run tests
make lint              # Check code quality
make format            # Format code

# Running
make start             # Smart launcher
make run               # Direct startup
make run-debug         # Debug mode
```

## 🔧 Smart Launcher (`start.sh`)

The smart launcher provides comprehensive pre-flight checks:

### Features

- 🔍 **Configuration Validation** - Checks for config files
- 🐍 **Python Environment Detection** - Poetry, venv, or system Python
- 📦 **Dependency Verification** - Ensures required modules are installed
- 🌐 **API Connectivity Check** - Tests configured API endpoints
- 🚀 **Process Management** - Prevents duplicate instances
- 🛑 **Graceful Shutdown** - Clean signal handling

### Pre-flight Checks

1. **Configuration Check** - Validates `config/config.json` or `.env`
2. **Python Version** - Ensures Python 3.8+
3. **Virtual Environment** - Detects and uses appropriate environment
4. **Dependencies** - Verifies required modules are installed
5. **API Connectivity** - Tests local service availability
6. **Process Check** - Prevents duplicate instances

### Local Service Detection

The launcher automatically detects running local AI services:

```bash
💡 Tip: Start a local AI service first:
  • Ollama is running (port 11434)
  • LM Studio is running (port 1234)
  • Text Generation WebUI is running (port 5000)
```

## 📁 File Structure After Installation

```
jan-assistant-pro/
├── install_wizard.py          # Advanced installer
├── start.sh                   # Smart launcher (executable)
├── config/
│   └── config.json           # Main configuration
├── .env                      # Environment variables
├── data/
│   ├── cache/               # Application cache
│   ├── memory.sqlite        # Persistent memory
│   └── jan-assistant.pid    # Process ID file
└── setup/                   # Installer modules
    ├── system_check.py      # System validation
    ├── dependency_manager.py # Dependency handling
    ├── api_providers.py     # API provider management
    └── config_wizard.py     # Configuration wizard
```

## 🔒 Security Levels

The installer offers three security presets:

### Strict
- Minimal command permissions (`ls`, `pwd`, `date`, `whoami`)
- Restricted path access (includes `/home`, `/root`)
- 1MB file size limit
- Enhanced logging and audit trails

### Moderate (Default)
- Balanced permissions (`ls`, `pwd`, `date`, `whoami`, `echo`)
- Standard restricted paths (`/etc`, `/sys`, `/proc`)
- 10MB file size limit
- Standard security logging

### Permissive  
- Extended permissions (includes `cat`, `grep`, `python3`, `pip`)
- Minimal path restrictions
- 100MB file size limit
- Reduced security constraints

## 🐛 Troubleshooting

### Common Issues

**"No configuration found"**
```bash
python install_wizard.py
```

**"Dependencies missing"**
```bash
# Poetry environment
poetry install

# Pip environment  
pip install -r requirements.txt
```

**"API service not responding"**
- Start your local AI service (Jan.ai, Ollama, etc.)
- Check API endpoint in `config/config.json`
- Verify API key for cloud services

**"Permission denied on start.sh"**
```bash
chmod +x start.sh
```

### Advanced Troubleshooting

**System Check**
```bash
python setup/system_check.py
```

**Dependency Check**
```bash
python setup/dependency_manager.py
```

**API Provider Detection**
```bash
python setup/api_providers.py
```

**Configuration Validation**
```bash
python -c "
import json
with open('config/config.json') as f:
    config = json.load(f)
print('✅ Configuration valid')
"
```

## 🔄 Migration from Manual Setup

If you have an existing manual installation:

1. **Backup Current Config**
   ```bash
   cp config/config.json config/config.json.backup
   cp .env .env.backup
   ```

2. **Run Installer**
   ```bash
   python install_wizard.py
   ```
   
   The installer will detect existing configuration and offer to create backups.

3. **Migrate Settings**
   - Review generated configuration
   - Manually merge any custom settings
   - Test with `./start.sh`

## 📖 Next Steps

After installation:

1. **Start Application**: `./start.sh`
2. **Test API Connection**: Use the "🔧 Test API" button in the GUI
3. **Explore Features**: Try file operations, memory system, command execution
4. **Customize**: Edit `config/config.json` for advanced settings
5. **Documentation**: See `docs/` for detailed feature guides

## 🤝 Contributing

The installer system is modular and extensible:

- **Add API Providers**: Edit `setup/api_providers.py`
- **Extend System Checks**: Modify `setup/system_check.py`
- **Enhance Wizard**: Update `setup/config_wizard.py`
- **Improve Launcher**: Enhance `start.sh`

For development setup with the new installer:
```bash
git clone <repo>
cd jan-assistant-pro
make dev-setup
```

---

**🎉 Enjoy your one-click Jan Assistant Pro experience!**
