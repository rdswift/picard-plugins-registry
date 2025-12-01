"""Tests for plugin operations."""

from unittest.mock import patch

import pytest

from registry_lib.plugin import add_plugin
from registry_lib.registry import Registry


@pytest.fixture
def temp_registry(tmp_path):
    """Create temporary registry."""
    return Registry(str(tmp_path / "plugins.json"))


@patch("registry_lib.plugin.fetch_manifest")
def test_add_plugin_basic(mock_fetch, temp_registry):
    """Test adding a basic plugin."""
    mock_fetch.return_value = {
        "uuid": "12345678-1234-4234-8234-123456789abc",
        "name": "Test Plugin",
        "version": "1.0.0",
        "description": "A test plugin",
        "api": ["3.0"],
        "authors": ["Test Author"],
    }

    plugin = add_plugin(temp_registry, "https://github.com/user/test-plugin", "community")

    assert plugin["id"] == "test-plugin"
    assert plugin["uuid"] == "12345678-1234-4234-8234-123456789abc"
    assert plugin["name"] == "Test Plugin"
    assert plugin["trust_level"] == "community"
    assert plugin["authors"] == ["Test Author"]
    assert "added_at" in plugin
    assert "updated_at" in plugin


@patch("registry_lib.plugin.fetch_manifest")
def test_add_plugin_with_categories(mock_fetch, temp_registry):
    """Test adding plugin with custom categories."""
    mock_fetch.return_value = {
        "uuid": "12345678-1234-4234-8234-123456789abc",
        "name": "Test Plugin",
        "version": "1.0.0",
        "description": "A test plugin",
        "api": ["3.0"],
    }

    plugin = add_plugin(
        temp_registry, "https://github.com/user/test-plugin", "community", categories=["metadata", "coverart"]
    )

    assert plugin["categories"] == ["metadata", "coverart"]


@patch("registry_lib.plugin.fetch_manifest")
def test_add_plugin_with_i18n(mock_fetch, temp_registry):
    """Test adding plugin with translations."""
    mock_fetch.return_value = {
        "uuid": "12345678-1234-4234-8234-123456789abc",
        "name": "Test Plugin",
        "version": "1.0.0",
        "description": "A test plugin",
        "api": ["3.0"],
        "name_i18n": {"de": "Test Plugin DE"},
        "description_i18n": {"de": "Ein Test Plugin"},
    }

    plugin = add_plugin(temp_registry, "https://github.com/user/test-plugin", "community")

    assert plugin["name_i18n"] == {"de": "Test Plugin DE"}
    assert plugin["description_i18n"] == {"de": "Ein Test Plugin"}


@patch("registry_lib.plugin.fetch_manifest")
def test_add_plugin_invalid_trust_level(mock_fetch, temp_registry):
    """Test adding plugin with invalid trust level."""
    mock_fetch.return_value = {
        "uuid": "12345678-1234-4234-8234-123456789abc",
        "name": "Test Plugin",
        "version": "1.0.0",
        "description": "A test plugin",
        "api": ["3.0"],
    }

    with pytest.raises(ValueError, match="Invalid trust level"):
        add_plugin(temp_registry, "https://github.com/user/test-plugin", "invalid")


@patch("registry_lib.plugin.fetch_manifest")
def test_add_plugin_duplicate(mock_fetch, temp_registry):
    """Test adding duplicate plugin."""
    mock_fetch.return_value = {
        "uuid": "12345678-1234-4234-8234-123456789abc",
        "name": "Test Plugin",
        "version": "1.0.0",
        "description": "A test plugin",
        "api": ["3.0"],
    }

    add_plugin(temp_registry, "https://github.com/user/test-plugin", "community")

    with pytest.raises(ValueError, match="already exists"):
        add_plugin(temp_registry, "https://github.com/user/test-plugin", "community")
