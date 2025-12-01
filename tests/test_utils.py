"""Tests for utils module."""

import pytest

from registry_lib.utils import derive_plugin_id


def test_derive_plugin_id_basic():
    """Test basic plugin ID derivation."""
    assert derive_plugin_id("https://github.com/user/my-plugin") == "my-plugin"
    assert derive_plugin_id("https://github.com/user/test") == "test"


def test_derive_plugin_id_with_picard_prefix():
    """Test plugin ID derivation with picard- prefix."""
    assert derive_plugin_id("https://github.com/user/picard-plugin-name") == "name"
    assert derive_plugin_id("https://github.com/user/picard-test") == "test"
    assert derive_plugin_id("https://github.com/user/plugin-test") == "test"


def test_derive_plugin_id_with_git_suffix():
    """Test plugin ID derivation with .git suffix."""
    assert derive_plugin_id("https://github.com/user/my-plugin.git") == "my-plugin"


def test_derive_plugin_id_normalize():
    """Test plugin ID normalization."""
    assert derive_plugin_id("https://github.com/user/My_Plugin") == "my-plugin"
    assert derive_plugin_id("https://github.com/user/test__plugin") == "test-plugin"


def test_derive_plugin_id_invalid():
    """Test plugin ID derivation with invalid URLs."""
    with pytest.raises(ValueError):
        derive_plugin_id("not-a-url")
