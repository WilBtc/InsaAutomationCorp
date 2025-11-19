# Contributing to INSA IoT Platform

## Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please review our Code of Conduct before participating.

## Development Process

We follow a structured development process to ensure code quality and system reliability.

### 1. Issue Tracking

All work should be tracked through GitHub Issues:

- **Bug Reports**: Use the bug report template
- **Feature Requests**: Use the feature request template
- **Documentation**: Use the documentation template

### 2. Branch Strategy

We use GitFlow branching model:

```
main            → Production-ready code
├── develop     → Integration branch for features
│   ├── feature/xxx → Feature branches
│   ├── bugfix/xxx  → Bug fix branches
│   └── hotfix/xxx  → Emergency fixes
└── release/x.x → Release preparation
```

### 3. Development Workflow

1. **Fork the repository**
2. **Create a feature branch** from `develop`
3. **Make your changes** following our coding standards
4. **Write/update tests** for your changes
5. **Update documentation** if needed
6. **Submit a pull request** to `develop`

## Coding Standards

### Python Style Guide

```python
"""
Module docstring explaining the purpose.
"""

from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class ExampleClass:
    """
    Class description.

    Attributes:
        attribute_name: Description of attribute
    """

    def __init__(self, param: str) -> None:
        """
        Initialize the class.

        Args:
            param: Description of parameter
        """
        self.attribute_name = param

    def example_method(self, value: int) -> Optional[Dict]:
        """
        Method description.

        Args:
            value: Input value

        Returns:
            Optional dictionary with results

        Raises:
            ValueError: If value is negative
        """
        if value < 0:
            raise ValueError("Value must be non-negative")

        return {"result": value * 2}
```

### Code Quality Requirements

- **Type Hints**: All functions must have type hints
- **Docstrings**: All modules, classes, and functions need docstrings
- **Testing**: Minimum 80% code coverage
- **Linting**: Must pass flake8, black, and mypy checks

## Testing Guidelines

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch

class TestExampleClass:
    """Test suite for ExampleClass."""

    def setup_method(self):
        """Set up test fixtures."""
        self.instance = ExampleClass("test")

    def test_initialization(self):
        """Test class initialization."""
        assert self.instance.attribute_name == "test"

    @pytest.mark.parametrize("value,expected", [
        (5, {"result": 10}),
        (0, {"result": 0}),
    ])
    def test_example_method(self, value, expected):
        """Test example_method with various inputs."""
        result = self.instance.example_method(value)
        assert result == expected

    def test_example_method_raises_on_negative(self):
        """Test that negative values raise ValueError."""
        with pytest.raises(ValueError):
            self.instance.example_method(-1)
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_example.py

# Run with verbose output
pytest -v

# Run only marked tests
pytest -m "not slow"
```

## Documentation

### API Documentation

Use docstrings for automatic API documentation generation:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class ItemResponse(BaseModel):
    """Response model for item data."""
    id: int
    name: str
    value: float

@router.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int) -> ItemResponse:
    """
    Retrieve an item by ID.

    Args:
        item_id: The unique identifier of the item

    Returns:
        ItemResponse: The requested item data

    Raises:
        HTTPException: If item not found (404)
    """
    # Implementation here
    pass
```

### README Updates

When adding new features, update relevant sections:

- **Installation**: If new dependencies are added
- **Configuration**: If new environment variables are needed
- **API Documentation**: If new endpoints are created
- **Architecture**: If system design changes

## Commit Guidelines

### Commit Message Format

We follow Conventional Commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or corrections
- `chore`: Maintenance tasks
- `perf`: Performance improvements

### Examples

```bash
# Feature
git commit -m "feat(telemetry): add support for OPC UA protocol"

# Bug fix
git commit -m "fix(api): resolve memory leak in WebSocket handler"

# Documentation
git commit -m "docs(readme): update installation instructions for Ubuntu 22.04"

# Breaking change
git commit -m "feat(api)!: change authentication from JWT to OAuth2

BREAKING CHANGE: JWT tokens are no longer supported"
```

## Pull Request Process

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] Documentation is updated
- [ ] Commit messages follow convention
- [ ] PR description clearly explains changes
- [ ] Linked to relevant issue(s)

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

## Release Process

### Version Numbering

We use Semantic Versioning (SemVer):

- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible functionality
- **PATCH**: Backwards-compatible bug fixes

### Release Steps

1. Create release branch from `develop`
2. Update version in `pyproject.toml`
3. Update CHANGELOG.md
4. Create PR to `main`
5. Tag release after merge
6. Deploy to production

## Getting Help

### Resources

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/WilBtc/Insa-iot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/WilBtc/Insa-iot/discussions)

### Contact

- **Email**: dev@insaautomation.com
- **Slack**: #insa-iot-dev channel

## License Agreement

By contributing to this project, you agree that your contributions will be licensed under the project's proprietary license.