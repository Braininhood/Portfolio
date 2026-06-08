# Contributing to Poker AI

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## Getting Started

### Development Setup

1. Clone the repository
2. Install dependencies:

```bash
cd poker_ai
uv sync --all-extras
```

3. Run the test suite:

```bash
uv run pytest
```

### Project Structure

- `poker_ai/` — Main Python package
- `apps/api/` — FastAPI backend
- `apps/web/` — React frontend
- `doc/` — Documentation

## Development Workflow

### Branch Naming

- `feature/` — New features
- `fix/` — Bug fixes
- `docs/` — Documentation updates
- `refactor/` — Code refactoring

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add equity backfill command
fix: correct side pot calculation in engine
docs: update API documentation
test: add coverage for replay module
```

### Code Style

The project uses:

- **ruff** for linting and formatting
- **mypy** for type checking
- **pytest** for testing

Run checks before committing:

```bash
uv run ruff check .
uv run ruff format .
uv run mypy src tests
uv run pytest
```

## Pull Requests

1. Create a feature branch from `main`
2. Make your changes with tests
3. Ensure all checks pass
4. Submit a PR with a clear description

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests added/updated for changes
- [ ] Documentation updated if needed
- [ ] All CI checks pass

## Testing

### Running Tests

```bash
# All tests
uv run pytest

# Specific module
uv run pytest tests/test_core_engine.py

# With coverage
uv run pytest --cov=poker_ai
```

### Test Categories

- Unit tests in `poker_ai/tests/`
- API tests in `apps/api/scripts/`
- Slow tests marked with `@pytest.mark.slow`

## Documentation

- Main documentation lives in `doc/`
- Package-specific docs in `poker_ai/docs/`
- API documentation auto-generated at `/docs`

### Writing Documentation

- Use Markdown
- Include code examples
- Keep documentation in sync with code

## Hard Constraints

When contributing, respect these invariants:

1. **No external AI services** — No OpenAI, Anthropic, etc.
2. **Local-first** — Must work offline
3. **Reproducible** — Artifacts need provenance tracking
4. **Compliant** — No real-time assistance on third-party clients

## Questions?

- Check existing documentation in `doc/`
- Review the [ROADMAP.md](doc/ROADMAP.md) for project direction
- Open an issue for discussion

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
