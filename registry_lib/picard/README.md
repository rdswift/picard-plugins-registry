# Picard Source Files

This directory contains files copied from the main Picard repository to keep the registry tool standalone.

## Files

- **constants.py** - Plugin system constants (trust levels, categories, validation constraints)
- **validator.py** - Standalone manifest validation logic

## Source

Copied from: https://github.com/metabrainz/picard
- `picard/plugin3/constants.py` → `constants.py`
- `picard/plugin3/validator.py` → `validator.py`

## Maintenance

These files should be copied **without modification**. If changes are needed, make them in the Picard repository first, then copy the updated files here.

To update:
```bash
cp /path/to/picard/picard/plugin3/constants.py registry_lib/picard/
cp /path/to/picard/picard/plugin3/validator.py registry_lib/picard/
```

## Why Copy?

The registry tool needs to be standalone and not depend on the full Picard installation. These files (~180 lines total) provide the validation logic needed to verify plugin manifests.
