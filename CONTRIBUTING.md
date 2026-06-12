# Contributing to iTab Migration Tool

Thank you for your interest in contributing to iTab Migration Tool! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project follows the Contributor Covenant Code of Conduct. By participating, you are expected to uphold this code.

## How to Contribute

### Types of Contributions

1. **Bug Reports**: Report bugs and issues
2. **Feature Requests**: Suggest new features
3. **Code Contributions**: Submit bug fixes or new features
4. **Documentation**: Improve documentation
5. **Testing**: Add or improve tests

### Before You Start

1. Check existing issues and pull requests
2. For major changes, open an issue first to discuss
3. For small fixes, feel free to submit a pull request directly

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- pip

### Setup Steps

1. **Fork the repository**
   ```bash
   # Click the "Fork" button on GitHub
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/itab-migration.git
   cd itab-migration
   ```

3. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   # Install package in development mode
   pip install -e ".[dev]"
   ```

5. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

## Code Style

This project follows PEP 8 and uses the following tools:

### Formatting

We use [Black](https://github.com/psf/black) for code formatting:

```bash
# Format all files
black .

# Check formatting without making changes
black --check .
```

### Linting

We use [Ruff](https://github.com/astral-sh/ruff) for linting:

```bash
# Run linter
ruff check .

# Fix auto-fixable issues
ruff check --fix .
```

### Type Checking

We use [mypy](https://mypy-lang.org/) for type checking:

```bash
mypy src/
```

### Code Style Guidelines

1. **Line Length**: 88 characters (Black default)
2. **Imports**: Use absolute imports, group by standard/third-party/local
3. **Docstrings**: Use Google-style docstrings
4. **Type Hints**: Add type hints to all function signatures
5. **Naming**: Follow PEP 8 naming conventions

### Example Code Style

```python
"""Module docstring."""

from typing import List, Optional

from itab_migration.parser import BookmarkItem


def process_bookmarks(
    bookmarks: List[BookmarkItem],
    filter_category: Optional[str] = None,
) -> List[BookmarkItem]:
    """
    Process a list of bookmarks.

    Args:
        bookmarks: List of bookmark items to process
        filter_category: Optional category to filter by

    Returns:
        Processed list of bookmarks

    Raises:
        ValueError: If bookmarks list is empty
    """
    if not bookmarks:
        raise ValueError("Bookmarks list cannot be empty")
    
    if filter_category:
        return [b for b in bookmarks if b.category == filter_category]
    
    return bookmarks
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=itab_migration

# Run specific test file
pytest tests/test_parser.py

# Run with verbose output
pytest -v
```

### Writing Tests

1. Create test files in `tests/` directory
2. Name test files as `test_*.py`
3. Use descriptive test function names
4. Include docstrings for test functions

### Example Test

```python
"""Tests for the parser module."""

import pytest
from pathlib import Path

from itab_migration.parser import ITABParser, BookmarkItem


class TestITABParser:
    """Tests for ITABParser class."""
    
    def test_parse_valid_file(self, tmp_path):
        """Test parsing a valid backup file."""
        # Create test file
        test_file = tmp_path / "test.itabdata"
        test_file.write_text('{"navConfig": []}')
        
        parser = ITABParser()
        result = parser.parse(test_file)
        
        assert result.total_count == 0
        assert result.categories == []
    
    def test_parse_nonexistent_file(self):
        """Test parsing a non-existent file."""
        parser = ITABParser()
        
        with pytest.raises(FileNotFoundError):
            parser.parse("nonexistent.itabdata")
    
    def test_parse_invalid_extension(self, tmp_path):
        """Test parsing file with invalid extension."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("{}")
        
        parser = ITABParser()
        
        with pytest.raises(ValueError):
            parser.parse(test_file)
```

### Test Coverage

We aim for high test coverage. Check coverage with:

```bash
pytest --cov=itab_migration --cov-report=html
```

Then open `htmlcov/index.html` in your browser.

## Pull Request Process

### Before Submitting

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Run all tests** and ensure they pass
4. **Update CHANGELOG.md** with your changes
5. **Format code** with Black
6. **Lint code** with Ruff

### Submitting a Pull Request

1. **Commit your changes**
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

2. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill in the PR template

### PR Template

```markdown
## Description

Brief description of the changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Other (please describe)

## Testing

- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing performed

## Checklist

- [ ] Code follows the project's style guidelines
- [ ] Self-review of code completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

### Review Process

1. **Automated checks** will run (tests, linting, etc.)
2. **Maintainers** will review your code
3. **Address feedback** if requested
4. **Merge** once approved

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

1. **Description**: Clear description of the issue
2. **Steps to Reproduce**: Detailed steps to reproduce the bug
3. **Expected Behavior**: What you expected to happen
4. **Actual Behavior**: What actually happened
5. **Environment**: Python version, OS, etc.
6. **Screenshots**: If applicable
7. **Error Messages**: Full error traceback

### Feature Requests

When requesting features, please include:

1. **Description**: Clear description of the feature
2. **Use Case**: Why this feature would be useful
3. **Proposed Solution**: If you have one
4. **Alternatives**: Any alternatives you've considered

### Issue Template

```markdown
## Bug Report / Feature Request

### Description
[Clear description]

### Steps to Reproduce (for bugs)
1. Step 1
2. Step 2
3. ...

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Environment
- Python version:
- OS:
- Package version:

### Additional Context
[Any other information]
```

## Getting Help

- **Issues**: Use GitHub Issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions and general discussion
- **Email**: Contact maintainers directly for sensitive issues

## Recognition

Contributors will be recognized in:

- README.md (Contributors section)
- CHANGELOG.md (release notes)
- GitHub Contributors page

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to iTab Migration Tool! 🎉
