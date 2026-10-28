# Contributing to Download Organizer

Thank you for your interest in contributing to Download Organizer! This guide will help you get started with contributing to the project.

## How to Contribute

There are many ways to contribute to this project:

- **Report bugs** - Found something that doesn't work? Let us know!
- **Suggest features** - Have an idea to make the app better?
- **Improve documentation** - Help make the docs clearer and more comprehensive
- **Fix bugs** - Submit pull requests to resolve issues
- **Add features** - Implement new functionality
- **Test** - Help test the application on different platforms
- **UI/UX improvements** - Make the interface more user-friendly

## Getting Started

### Prerequisites

- **Python 3.12+** installed on your system
- **Git** for version control
- **Code editor** (VS Code, PyCharm, etc.)

### Development Setup

1. **Fork the repository** on GitHub
2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR-USERNAME/organizer.git
   cd organizer
   ```

3. **Create a virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application:**
   ```bash
   python source/main.py
   ```

## Development Guidelines

### Code Style

- Follow **PEP 8** Python style guidelines
- Use **descriptive variable names** and **clear comments**
- Keep functions **focused and small**
- Use **type hints** where appropriate
- Write **docstrings** for functions and classes

**Example:**
```python
def organize_files_by_rule(file_path: str, rule: dict) -> bool:
    """
    Organize a file according to a specific rule.
    
    Args:
        file_path: Path to the file to organize
        rule: Dictionary containing rule configuration
    
    Returns:
        bool: True if file was successfully organized
    """
    # Implementation here
    pass
```

### File Organization

- **`source/main.py`** - Application entry point and system tray logic
- **`source/gui.py`** - User interface components and window management
- **`source/utils.py`** - File operations, configuration, and utility functions
- **`resources/`** - Icons, default configurations, and assets

### Logging

Use the existing logger for consistent logging:
```python
from utils import logger

logger.info("Operation completed successfully")
logger.warning("Potential issue detected")
logger.error("Error occurred during operation")
```

### Configuration

- Default configuration ships in `resources/config.yaml`; user settings are stored in the per-user configuration directory documented in the README
- Use `utils.load_config()` and `utils.save_config()` for modifications
- Always validate configuration data before use

## Bug Reports

When reporting bugs, please include:

### Required Information
- **OS and version** (Windows 11, macOS 14, Ubuntu 22.04, etc.)
- **Python version** (`python --version`)
- **Download Organizer version** or commit hash
- **Steps to reproduce** the issue
- **Expected behavior** vs **actual behavior**
- **Error messages** (if any)
- **Log files** (`%APPDATA%\Organizer\organizer.log` on Windows)

### Bug Report Template
```markdown
**Environment:**
- OS: Windows 11 Pro
- Python: 3.12.1
- Version: v2.1.1

**Description:**
Brief description of the bug

**Steps to Reproduce:**
1. Open configuration window
2. Add new rule with...
3. Click save
4. Error occurs

**Expected Behavior:**
Rule should be saved successfully

**Actual Behavior:**
Application crashes with error message

**Error Messages:**
```
Paste any error messages here
```

**Additional Context:**
Any other relevant information
```

## Feature Requests

When suggesting features, please include:

- **Clear description** of the feature
- **Use case** - why would this be useful?
- **Implementation ideas** (if you have any)
- **Examples** from similar applications
- **Priority level** (nice-to-have vs essential)

## 🔧 Pull Request Process

### Before Submitting

1. **Check existing issues** - Is this already being worked on?
2. **Create an issue** for discussion (for major changes)
3. **Test your changes** thoroughly
4. **Update documentation** if needed
5. **Follow the code style** guidelines

### Pull Request Steps

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make your changes** with clear, logical commits:
   ```bash
   git commit -m "Add feature: detailed description of what was added"
   ```

3. **Push to your fork:**
   ```bash
   git push origin feature/amazing-feature
   ```

4. **Create a Pull Request** on GitHub

### Pull Request Template

```markdown
## Description
Brief description of changes made

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement

## Testing
- [ ] Tested on Windows
- [ ] Tested on macOS
- [ ] Tested on Linux
- [ ] Manual testing performed
- [ ] Edge cases considered

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated (if applicable)
- [ ] No breaking changes (or clearly documented)

## Screenshots (if applicable)
Add screenshots of UI changes
```

## Testing

Run the automated tests before submitting changes:

```bash
python -m unittest discover -s tests -v
```

The file-sorting tests use temporary directories, so they do not touch your
Downloads folder. When contributing, also use the manual checklist below:

### Manual Testing Checklist

**Core Functionality:**
- [ ] Application starts and system tray icon appears
- [ ] Configuration window opens correctly
- [ ] Rules can be added, edited, and deleted
- [ ] Drag-and-drop reordering works
- [ ] File sorting works with test files
- [ ] Interval setting updates correctly
- [ ] Manual sort button functions
- [ ] Default folders creation works

**Cross-Platform Testing:**
- [ ] Windows compatibility
- [ ] macOS compatibility (if available)
- [ ] Linux compatibility (if available)

**Error Handling:**
- [ ] Invalid configuration handling
- [ ] Missing folders handling
- [ ] Duplicate file naming
- [ ] Permission errors

## Recognition

Contributors will be recognized:

- **GitHub contributors page** - Automatic recognition
- **CHANGELOG.md** - Major contributions noted
- **README.md** - Significant contributors listed
- **Release notes** - Feature contributions highlighted

## Getting Help

**Need help getting started?**

- **GitHub Issues** - Ask questions with the `question` label
- **GitHub Discussions** - General discussion and ideas
- **Code Review** - Request feedback on your approach before implementing

**Communication Guidelines:**
- Be respectful and constructive
- Provide context for your questions
- Search existing issues before creating new ones
- Use clear, descriptive titles

## Code of Conduct

By participating in this project, you agree to:

- **Be respectful** to all contributors
- **Provide constructive feedback**
- **Focus on what's best** for the project

---

**Thank you for contributing to Download Organizer!** 🎉

Every contribution, no matter how small, helps make this project better for everyone.
