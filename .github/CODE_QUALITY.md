# Code Quality Standards & Automation

## Overview

This document defines code quality standards for the INSA Automation Corp codebase and describes the automated quality checks implemented via GitHub Actions CI/CD workflows.

**Repository**: [WilBtc/InsaAutomationCorp](https://github.com/WilBtc/InsaAutomationCorp)

## Quality Tools

### 1. Ruff - Fast Python Linter

**Purpose**: Lightning-fast Python linting with automatic error detection and fixing.

**What it does**:
- Detects syntax errors and common Python mistakes
- Identifies unused imports and variables
- Enforces naming conventions (PEP8)
- Checks for code simplification opportunities
- Formats errors in GitHub CI format for easy viewing

**Configuration** (`pyproject.toml`):
```toml
[tool.ruff]
line-length = 100
target-version = "py310"
select = ["E", "F", "W", "I", "N", "UP", "B", "A", "C4", "SIM"]
```

**Rule Categories**:
- **E**: PEP8 errors (whitespace, indentation)
- **F**: Pyflakes (undefined names, unused imports)
- **W**: PEP8 warnings
- **I**: isort (import sorting)
- **N**: PEP8 naming conventions
- **UP**: pyupgrade (modern Python syntax)
- **B**: flake8-bugbear (bug detection)
- **A**: flake8-builtins (builtin shadowing)
- **C4**: flake8-comprehensions (list/dict comprehensions)
- **SIM**: flake8-simplify (simplification suggestions)

**Run locally**:
```bash
ruff check . --output-format=github
ruff check . --fix  # Auto-fix some issues
```

### 2. Pylint - Deep Code Analysis

**Purpose**: Comprehensive static code analysis for quality and maintainability.

**What it does**:
- Analyzes code structure and logic
- Detects design flaws and code duplication
- Provides quality metrics
- Identifies potential bugs before runtime
- Suggests refactoring opportunities

**Configuration** (`pyproject.toml`):
```toml
[tool.pylint.messages_control]
disable = ["C0330", "C0326", "R0913", "R0914", "W0212", "C0111"]
max-line-length = 100
max-attributes = 7
```

**Run locally**:
```bash
pylint automation/ --exit-zero --output-format=text
```

### 3. Black - Code Formatter

**Purpose**: Automatic, deterministic Python code formatting.

**What it does**:
- Enforces consistent code style across the codebase
- Removes manual style discussions in code reviews
- Deterministic formatting (idempotent)
- Respects code structure and readability

**Configuration** (`pyproject.toml`):
```toml
[tool.black]
line-length = 100
target-version = ['py310', 'py311', 'py312']
```

**Run locally**:
```bash
black .              # Format all Python files
black --check .      # Check without modifying
black --diff .       # Show what would change
```

### 4. isort - Import Sorting

**Purpose**: Automatically sort and organize Python imports.

**What it does**:
- Organizes imports into groups (stdlib, third-party, local)
- Sorts imports alphabetically within groups
- Removes duplicate imports
- Adds/removes blank lines per PEP8

**Configuration** (`pyproject.toml`):
```toml
[tool.isort]
profile = "black"
line_length = 100
known_first_party = ["automation", "platforms", "mcp_servers"]
```

**Run locally**:
```bash
isort .              # Sort all imports
isort --check-only . # Check without modifying
isort --diff .       # Show what would change
```

### 5. mypy - Type Checking

**Purpose**: Static type checking for Python code.

**What it does**:
- Detects type mismatches before runtime
- Validates function signatures
- Checks type annotations
- Prevents TypeErrors in production

**Configuration** (`pyproject.toml`):
```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
check_untyped_defs = true
```

**Run locally**:
```bash
mypy automation/ --ignore-missing-imports
```

**Best Practices**:
- Add type hints to function signatures
- Use `Optional[T]` for nullable types
- Use `Union[T1, T2]` for multiple types
- Document complex types with type comments

### 6. pytest - Testing Framework

**Purpose**: Automated testing with coverage tracking.

**What it does**:
- Runs unit and integration tests
- Measures code coverage (% of code tested)
- Reports test failures with detailed output
- Generates HTML coverage reports

**Configuration** (`pyproject.toml`):
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--strict-markers", "--cov-report=html"]
```

**Run locally**:
```bash
pytest                                    # Run all tests
pytest --cov=automation                   # With coverage
pytest --cov-report=html                  # Generate HTML report
pytest -v                                 # Verbose output
pytest -k test_specific                   # Run specific test
pytest --markers                          # Show available markers
```

**Test Organization**:
```
tests/
├── unit/
│   ├── test_agent.py
│   └── test_utils.py
├── integration/
│   └── test_github_integration.py
└── e2e/
    └── test_full_workflow.py
```

### 7. radon - Code Complexity

**Purpose**: Measure code complexity and maintainability.

**What it does**:
- Calculates cyclomatic complexity (code paths)
- Computes maintainability index
- Identifies overly complex functions
- Suggests refactoring targets

**Metrics**:
- **Cyclomatic Complexity** (CC):
  - 1-5: Simple, low risk
  - 6-10: Moderate, some risk
  - 11+: Complex, high risk (refactor!)

- **Maintainability Index** (MI):
  - 100-20: High (green)
  - 19-10: Medium (yellow)
  - <10: Low (red)

**Run locally**:
```bash
radon cc automation/ -a -nb      # Cyclomatic complexity
radon mi automation/ -nb          # Maintainability index
```

### 8. Bandit - Security Scanner

**Purpose**: Security-focused code analysis.

**What it does**:
- Detects common security issues
- Finds hardcoded secrets and credentials
- Identifies insecure functions
- Reports vulnerability classifications

**Run locally**:
```bash
bandit -r automation/ -f json
bandit -r automation/ -f txt
```

## CI/CD Workflows

### Code Quality Workflow (`.github/workflows/code-quality.yml`)

**Triggers**:
- Pull requests touching Python files
- Pushes to main/develop branches

**Steps**:
1. Ruff linting (fast)
2. Pylint analysis (deep)
3. Black format check
4. isort import check
5. mypy type checking
6. radon complexity analysis
7. pytest with coverage
8. Bandit security scan
9. Codecov upload
10. PR comment with summary

**Artifacts**:
- `coverage-report/`: HTML coverage report (30-day retention)
- `bandit-security-report.json`: Security findings

### Auto-Format Workflow (`.github/workflows/auto-format.yml`)

**Triggers**:
- Pull request opened/synchronized
- Manual workflow dispatch

**Steps**:
1. Checkout PR branch
2. Run Black formatter
3. Run isort
4. Commit changes (if any)
5. Push to PR branch
6. Comment on PR

**Benefits**:
- Keeps code style consistent
- Reduces review comments on formatting
- Automatic cleanup of new PRs

## Local Development

### Setup

1. **Install development dependencies**:
```bash
pip install -e ".[dev]"
```

2. **Install pre-commit hooks** (optional):
```bash
pre-commit install
```

### Run Quality Checks Locally

**Quick check** (fast):
```bash
ruff check .
black --check .
isort --check-only .
```

**Full check** (comprehensive):
```bash
ruff check .
pylint automation/
black --check .
isort --check-only .
mypy automation/
pytest --cov=automation
radon cc automation/ -a -nb
bandit -r automation/
```

**Auto-fix issues**:
```bash
ruff check . --fix
black .
isort .
```

### Pre-commit Hooks (Optional)

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/psf/black
    rev: 23.9.0
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

Install hooks:
```bash
pre-commit install
pre-commit run --all-files
```

## Quality Gates & Standards

### Code Coverage

**Minimum**: 70% overall coverage
**Target**: 85%+ coverage
**Critical paths**: 95%+ coverage

View coverage:
```bash
pytest --cov=automation --cov-report=html
open htmlcov/index.html
```

### Complexity Limits

| Metric | Threshold | Action |
|--------|-----------|--------|
| Cyclomatic Complexity | > 10 | Refactor |
| Maintainability Index | < 70 | Review |
| Line Length | > 100 | Format |
| Max Function Lines | > 50 | Split |

### Type Coverage

**Minimum**: 80% of public APIs typed
**Goal**: 100% type hints in new code

```python
# Good
def process_data(items: List[str]) -> Dict[str, int]:
    """Process items and return counts."""
    return {item: len(item) for item in items}

# Avoid
def process_data(items):
    return {item: len(item) for item in items}
```

### Test Requirements

- **Unit tests**: All business logic
- **Integration tests**: External service calls
- **E2E tests**: Critical user workflows
- **Performance tests**: Performance-critical code

Markers available:
```bash
pytest -m unit           # Run unit tests only
pytest -m "not slow"     # Skip slow tests
pytest -m integration    # Run integration tests
```

## Code Review Checklist

- [ ] Code passes all quality checks (CI green)
- [ ] Coverage ≥ 70% for new code
- [ ] No security issues (Bandit clean)
- [ ] Type hints on public APIs
- [ ] Docstrings on functions
- [ ] Tests included for new features
- [ ] Complexity acceptable (CC < 10)
- [ ] No hardcoded secrets/credentials

## Troubleshooting

### Black and Pylint Conflicts

**Issue**: isort/Black import formatting differs

**Solution**: Use Black profile in isort:
```toml
[tool.isort]
profile = "black"
```

### mypy Errors on Third-Party Packages

**Issue**: `error: Skipping cache due to errors from mypy on [package]`

**Solution**: Use `--ignore-missing-imports` or add to `pyproject.toml`:
```toml
[[tool.mypy.overrides]]
module = ["external_package.*"]
ignore_missing_imports = true
```

### pytest Warnings

**Issue**: `PytestUnraisableExceptionWarning`

**Solution**: Update pytest and dependencies:
```bash
pip install --upgrade pytest
```

### Coverage Not Generated

**Issue**: `coverage: no data to report`

**Solution**: Ensure tests actually run:
```bash
pytest -v --cov=automation
```

## Resources

- **Ruff**: https://github.com/astral-sh/ruff
- **Black**: https://github.com/psf/black
- **isort**: https://github.com/PyCQA/isort
- **mypy**: https://github.com/python/mypy
- **pytest**: https://github.com/pytest-dev/pytest
- **Radon**: https://github.com/rubik/radon
- **Bandit**: https://github.com/PyCQA/bandit

## Questions?

Contact: [Wil Aroca](mailto:w.aroca@insaing.com) | [Juan Casas](mailto:j.casas@insaing.com)

---

**Last Updated**: November 14, 2025
**Version**: 1.0.0
