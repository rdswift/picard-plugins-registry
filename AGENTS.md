# AI Assistant Context for Picard Plugins Registry

> **Purpose:** Essential patterns, conventions, and gotchas for AI assistants.
> For usage and architecture, see `README.md`.

**What is this?** CLI tool and registry file (`plugins.toml`) for managing MusicBrainz Picard plugins. Plugins are registered by git URL, validated via `MANIFEST.toml`, and served to Picard clients.

---

## Quick Facts

- **Language:** Python 3.10+
- **Package Manager:** uv
- **Entry Point:** `registry_lib/cli.py:main()`
- **Tests:** `tests/` directory (pytest)
- **Registry File:** `plugins.toml` (DO NOT EDIT MANUALLY — use the `registry` CLI)
- **Picard Source:** <https://github.com/metabrainz/picard>

---

## Critical Patterns & Gotchas

### Files Copied from Picard

Files in `registry_lib/picard/` are copied from the Picard source tree using `scripts/`. **Do not modify them directly** — changes will be overwritten on next sync. If type checking or linting issues arise in these files, suppress them via tool configuration (e.g., `[tool.ty.src] exclude`).

### Registry File

Never edit `plugins.toml` by hand. Always use the `registry` CLI commands (`registry plugin add`, `registry plugin edit`, etc.). The file is sorted and formatted automatically on save.

### Import Rules

```python
# ❌ Don't use inline imports (unless breaking circular dependencies)
def my_function():
    from registry_lib.some_module import something
    return something()

# ❌ Don't put multiple imports on one line
from registry_lib.manifest import fetch_manifest, validate_manifest

# ✅ Imports go at the top of the file, each imported name on its own line with trailing commas
from registry_lib.manifest import (
    fetch_manifest,
    validate_manifest,
)
```

**Exception:** Inline imports are acceptable only to break circular dependencies. Place them as close to usage as possible with a comment explaining why.

### Optional Dependencies

`pygit2` and `tomli` are optional/conditional. Use `try/except ImportError` with a `None` fallback, and narrow with `assert` or `is not None` checks before use:

```python
try:
    import pygit2
except ImportError:
    pygit2 = None

def _use_pygit2():
    assert pygit2 is not None
    # now safe to use pygit2 attributes
```

---

## Code Style

### Conventions
- **Standard:** PEP 8, 120 char lines
- **Linter/Formatter:** Ruff (`ruff check`, `ruff format`)
- **Type Checker:** ty (`ty check`)
- **Type hints:** Required for all new code
- **Naming:** `PascalCase` classes, `snake_case` functions, `UPPER_SNAKE` constants

### Before Committing
```bash
# 1. Format code
ruff format .

# 2. Check for issues
ruff check .

# 3. Type check
ty check

# 4. Run tests
pytest
```

Pre-commit hooks run all of these automatically.

---

## AI Assistant Guidelines

When making code changes:
1. **Imports go at the top of files** — use `(name,)` style for multiple imports; inline imports only to break circular dependencies
2. **Run `ruff format` after all changes** — ensures code follows project style
3. **Run `ruff check` to catch issues** — fix any linting errors before committing
4. **Run `ty check`** — fix type errors before committing
5. **Add type annotations** to all new functions and methods
6. **Never commit editor or agent-specific files** — do not `git add` files from AI tool directories (`.kiro/`, `.cursor/`, `.aider*`, etc.)
7. **Don't push to remote** without explicit user approval
8. **Don't modify files in `registry_lib/picard/`** — they are synced from Picard source

---

## Key Locations

- `registry_lib/cli.py` — Command-line interface
- `registry_lib/registry.py` — Registry file management
- `registry_lib/plugin.py` — Plugin add/update operations
- `registry_lib/blacklist.py` — Blacklist operations
- `registry_lib/manifest.py` — MANIFEST.toml fetching/validation, git operations
- `registry_lib/utils.py` — Utility functions
- `registry_lib/picard/` — Files copied from Picard (validator, constants) — **do not edit**
- `tests/` — Unit tests
- `plugins.toml` — The registry file

---

## Testing

```bash
# All tests
pytest

# With coverage
pytest --cov=registry_lib

# Specific test file
pytest tests/test_manifest.py -v
```

---

## Resources

- **Picard:** <https://github.com/metabrainz/picard>
- **Picard Docs:** <https://picard-docs.musicbrainz.org/>
- **Forum:** <https://community.metabrainz.org/c/picard>
