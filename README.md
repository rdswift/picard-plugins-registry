# Picard Plugins Registry

Official registry and maintenance tools for MusicBrainz Picard plugins.

## Overview

This repository contains:
- `plugins.json` - The official plugin registry
- `registry` - CLI tool for maintaining the registry
- Validation and testing infrastructure

## Setup

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/metabrainz/picard-plugins-registry.git
cd picard-plugins-registry
uv sync

# Install pre-commit hooks
uv run pre-commit install

# Activate virtual environment (optional - allows running `registry` directly)
source .venv/bin/activate
```

**Note:** After activating the virtual environment, you can run `registry` directly instead of `uv run registry`.

## Usage

### Add a Plugin

```bash
uv run registry plugin add https://github.com/user/plugin-name \
    --trust community \
    --categories metadata coverart

# With custom git ref
uv run registry plugin add https://github.com/user/plugin-name \
    --trust community \
    --ref develop
```

### List Plugins

```bash
uv run registry plugin list
```

### Remove a Plugin

```bash
uv run registry plugin remove plugin-id
```

### Blacklist a Plugin

```bash
uv run registry blacklist add https://github.com/bad/plugin \
    --reason "Contains malicious code"

# Blacklist entire organization
uv run registry blacklist add "https://github.com/badorg/*" \
    --reason "Compromised account"
```

### List Blacklist

```bash
uv run registry blacklist list
```

## Trust Levels

- **official** - Maintained by MusicBrainz Picard team
- **trusted** - Well-known authors with established reputation
- **community** - Other plugins (default for new submissions)

## Development

### Run Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=registry_lib

# Specific test file
uv run pytest tests/test_registry.py -v
```

### Code Quality

```bash
# Run ruff checks
uv run ruff check .

# Format code
uv run ruff format .

# Run pre-commit on all files
uv run pre-commit run --all-files
```

## Architecture

- `registry_lib/` - Main package
  - `cli.py` - Command-line interface
  - `registry.py` - Registry file management
  - `plugin.py` - Plugin operations
  - `blacklist.py` - Blacklist operations
  - `manifest.py` - MANIFEST.toml fetching/validation
  - `utils.py` - Utility functions
  - `picard/` - Files copied from Picard (validator, constants)
- `tests/` - Unit tests
- `plugins.json` - The registry file

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run `uv run pytest` to verify
5. Submit a pull request

All commits must pass pre-commit hooks (ruff format, ruff check, pytest).

## License

GPL-2.0-or-later
