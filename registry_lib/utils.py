"""Utility functions for registry management."""

from datetime import datetime, timezone
import re


def derive_plugin_id(git_url: str) -> str:
    """Derive plugin ID from git URL.

    Args:
        git_url: Git repository URL

    Returns:
        str: Plugin ID (lowercase, alphanumeric + hyphens)

    Examples:
        >>> derive_plugin_id("https://github.com/user/picard-plugin-name")
        'name'
        >>> derive_plugin_id("https://github.com/user/my-plugin")
        'my-plugin'
    """
    # Extract repo name from URL
    match = re.search(r"/([^/]+?)(?:\.git)?$", git_url.rstrip("/"))
    if not match:
        raise ValueError(f"Cannot derive plugin ID from URL: {git_url}")

    repo_name = match.group(1)

    # Remove common prefixes
    for prefix in ["picard-plugin-", "picard-", "plugin-"]:
        if repo_name.lower().startswith(prefix):
            repo_name = repo_name[len(prefix) :]
            break

    # Normalize to lowercase with hyphens
    plugin_id = repo_name.lower()
    plugin_id = re.sub(r"[^a-z0-9-]", "-", plugin_id)
    plugin_id = re.sub(r"-+", "-", plugin_id)
    plugin_id = plugin_id.strip("-")

    if not plugin_id:
        raise ValueError(f"Cannot derive valid plugin ID from URL: {git_url}")

    return plugin_id


def now_iso8601() -> str:
    """Get current time in ISO 8601 format with Z suffix (no microseconds).

    Returns:
        str: ISO 8601 timestamp like "2025-12-01T10:30:00Z"
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
