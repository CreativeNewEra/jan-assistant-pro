# Contributing to Jan Assistant Pro

Thank you for your interest in contributing to Jan Assistant Pro! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Jan.ai installed and running locally
- Basic knowledge of Python and tkinter

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/jan-assistant-pro.git
   cd jan-assistant-pro
   ```

2. **Install dependencies**
   ```bash
   poetry install --with dev
   ```

3. **Copy configuration**
   ```bash
   cp config/config.example.json config/config.json
   # Edit config.json with your settings
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

## 🏗️ Project Structure

```
jan-assistant-pro/
├── src/
│   ├── core/           # Core functionality
│   ├── gui/            # GUI components
│   └── tools/          # Tool implementations
├── config/             # Configuration files
├── tests/              # Test suites
├── docs/               # Documentation
└── assets/             # Static assets
```

## 🔧 Development Guidelines

### Code Style

- **Python**: Follow PEP 8
- **Line length**: 88 characters (Black formatter)
- **Imports**: Use absolute imports
- **Docstrings**: Google style docstrings
- **Type hints**: Use type hints where possible

### Naming Conventions

- **Files**: snake_case
- **Classes**: PascalCase
- **Functions/Methods**: snake_case
- **Constants**: UPPER_SNAKE_CASE
- **Private methods**: _leading_underscore

### Example Code Style

```python
"""
Module description here
"""

from typing import Dict, Any, Optional
from core.config import Config


class ExampleTool:
    """Example tool for demonstration purposes"""
    
    def __init__(self, config: Config):
        self.config = config
        self._private_attr = None
    
    def public_method(self, param: str) -> Dict[str, Any]:
        """
        Public method example
        
        Args:
            param: Description of parameter
            
        Returns:
            Dictionary with results
        """
        return {"success": True, "data": param}
    
    def _private_method(self) -> None:
        """Private method for internal use"""
        pass
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src/

# Run specific test file
python -m pytest tests/test_api_client.py
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Use descriptive test method names
- Include both positive and negative test cases
- Mock external dependencies

Example test:

```python
import pytest
from unittest.mock import Mock, patch
from core.api_client import APIClient, APIError


class TestAPIClient:
    """Test cases for APIClient"""
    
    def test_chat_completion_success(self):
        """Test successful chat completion"""
        client = APIClient("http://localhost:1337/v1", "test-key", "test-model")
        
        with patch.object(client.session, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Hello!"}}]
            }
            mock_post.return_value = mock_response
            
            result = client.chat_completion([{"role": "user", "content": "Hi"}])
            assert result["choices"][0]["message"]["content"] == "Hello!"
```

## 🔌 Adding New Tools

### Tool Structure

All tools should follow this pattern:

```python
"""
Tool description
"""

from typing import Dict, Any


class NewTool:
    """Description of what this tool does"""
    
    def __init__(self, config_param: str = "default"):
        self.config_param = config_param
    
    def tool_method(self, input_param: str) -> Dict[str, Any]:
        """
        Tool method description
        
        Args:
            input_param: Description
            
        Returns:
            Dictionary with 'success' boolean and result data
        """
        try:
            # Tool implementation
            result = self._perform_operation(input_param)
            
            return {
                'success': True,
                'result': result,
                'message': 'Operation completed successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _perform_operation(self, param: str) -> Any:
        """Private method for actual operation"""
        pass
```

### Tool Integration

1. **Add tool to main_window.py**:
   ```python
   # In __init__
   self.new_tool = NewTool(config.get('new_tool.setting'))
   
   # In handle_tool_call
   elif "TOOL_NEW_OPERATION:" in response:
       param = response.split("TOOL_NEW_OPERATION:")[1].strip()
       result = self.new_tool.tool_method(param)
       return self._format_tool_result(result)
   ```

2. **Update system message** in `chat_with_tools` method

3. **Add configuration** to `config.example.json`

4. **Write tests** in `tests/test_new_tool.py`

## 📖 Documentation

### Docstring Format

Use Google-style docstrings:

```python
def example_function(param1: str, param2: int = 10) -> Dict[str, Any]:
    """
    Brief description of the function
    
    Longer description if needed. Can span multiple lines.
    
    Args:
        param1: Description of param1
        param2: Description of param2 with default value
        
    Returns:
        Dictionary containing result data
        
    Raises:
        ValueError: When param1 is empty
        APIError: When API call fails
        
    Example:
        >>> result = example_function("test", 20)
        >>> print(result["success"])
        True
    """
    pass
```

### Adding Documentation

- Add documentation files to `docs/`
- Update README.md for significant changes
- Include examples and use cases
- Document configuration options

## 🐛 Bug Reports

### Before Submitting

- Check existing issues
- Test with the latest version
- Provide minimal reproduction case

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Enter '....'
4. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g. Ubuntu 20.04]
- Python version: [e.g. 3.9.5]
- Jan Assistant Pro version: [e.g. 0.1.0]
- Jan.ai version: [e.g. 0.6.1]

**Additional context**
Add any other context about the problem.
```

## 💡 Feature Requests

### Before Submitting

- Check if feature already exists
- Search existing feature requests
- Consider if it fits the project scope

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Other solutions you've considered.

**Additional context**
Add any other context about the feature request.
```

## 🔄 Pull Request Process

### Before Submitting PR

1. **Create feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make changes and test**
   ```bash
   python -m pytest tests/
   python main.py  # Manual testing
   ```

3. **Format code**
   ```bash
   black src/ tests/
   ruff src/ tests/
   ```

4. **Update documentation** if needed

5. **Commit with clear message**
   ```bash
   git commit -m "feat: add amazing new feature
   
   - Implements X functionality
   - Adds Y capability
   - Fixes issue #123"
   ```

### PR Requirements

- [ ] Code follows project style guidelines
- [ ] Tests pass (`python -m pytest tests/`)
- [ ] New features include tests
- [ ] Documentation updated if needed
- [ ] PR description explains changes
- [ ] Linked to relevant issues

### PR Review Process

1. **Automated checks** must pass
2. **Code review** by maintainers
3. **Testing** on different platforms
4. **Merge** after approval

## 🏷️ Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] Update version in `setup.py`
- [ ] Update `CHANGELOG.md`
- [ ] Create release notes
- [ ] Tag release: `git tag v0.1.0`
- [ ] Push tags: `git push --tags`

## 🤝 Community

### Communication

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Discord**: Real-time chat (link in README)

### Code of Conduct

- Be respectful and inclusive
- Help others learn and grow
- Focus on constructive feedback
- Follow the [Contributor Covenant](https://www.contributor-covenant.org/)

## 📚 Resources

### Helpful Links

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [tkinter Documentation](https://docs.python.org/3/library/tkinter.html)
- [Jan.ai Documentation](https://jan.ai/docs)

### Development Tools

- **Code formatting**: [Black](https://black.readthedocs.io/)
- **Linting**: [ruff](https://docs.astral.sh/ruff/)
- **Type checking**: [mypy](https://mypy.readthedocs.io/)
- **Testing**: [pytest](https://docs.pytest.org/)

## ❓ Questions?

If you have questions about contributing, feel free to:

- Open a GitHub Discussion
- Create an issue with the "question" label
- Ask in our Discord community

Thank you for contributing to Jan Assistant Pro! 🚀
