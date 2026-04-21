"""Tests for manifest module."""

from unittest.mock import (
    Mock,
    patch,
)

import pytest

from registry_lib.manifest import (
    fetch_manifest,
    raw_url,
    validate_manifest,
)


@patch("registry_lib.manifest.requests.get")
def test_fetch_manifest_success(mock_get):
    """Test successful manifest fetch."""
    mock_response = Mock()
    mock_response.text = """
uuid = "6de6a3bf-a524-42b6-83cb-a36b2ec2e246"
name = "Test Plugin"
version = "1.0.0"
description = "A test plugin"
api = ["3.0"]
"""
    mock_get.return_value = mock_response

    manifest = fetch_manifest("https://github.com/user/plugin", "main")

    assert manifest["uuid"] == "6de6a3bf-a524-42b6-83cb-a36b2ec2e246"
    assert manifest["name"] == "Test Plugin"
    mock_get.assert_called_once()


@patch("registry_lib.manifest.requests.get")
def test_fetch_manifest_with_git_suffix(mock_get):
    """Test manifest fetch with .git suffix."""
    mock_response = Mock()
    mock_response.text = """
uuid = "6de6a3bf-a524-42b6-83cb-a36b2ec2e246"
name = "Test Plugin"
version = "1.0.0"
description = "A test plugin"
api = ["3.0"]
"""
    mock_get.return_value = mock_response

    fetch_manifest("https://github.com/user/plugin.git", "main")

    # Should strip .git suffix from repo name
    call_url = mock_get.call_args[0][0]
    assert "plugin.git" not in call_url
    assert "plugin/main" in call_url


@pytest.mark.parametrize(
    "repo_url, expected_manifest_url",
    [
        ("https://github.com/user/plugin", "raw.githubusercontent.com/user/plugin/main/MANIFEST.toml"),
        ("https://gitlab.com/user/plugin", "gitlab.com/user/plugin/-/raw/main/MANIFEST.toml"),
        ("https://git.sr.ht/~user/plugin", "git.sr.ht/~user/plugin/blob/main/MANIFEST.toml"),
        ("https://codeberg.org/user/plugin", "codeberg.org/user/plugin/raw/branch/main/MANIFEST.toml"),
        ("https://bitbucket.org/user/plugin", "bitbucket.org/user/plugin/raw/main/MANIFEST.toml"),
    ],
)
@patch("registry_lib.manifest.requests.get")
def test_fetch_manifest_supported(mock_get, repo_url, expected_manifest_url):
    """Test successful manifest fetch from GitLab."""
    mock_response = Mock()
    mock_response.text = """
uuid = "6de6a3bf-a524-42b6-83cb-a36b2ec2e246"
name = "Test Plugin"
version = "1.0.0"
description = "A test plugin"
api = ["3.0"]
"""
    mock_get.return_value = mock_response

    manifest = fetch_manifest(repo_url, "main")

    assert manifest["uuid"] == "6de6a3bf-a524-42b6-83cb-a36b2ec2e246"
    call_url = mock_get.call_args[0][0]
    assert expected_manifest_url in call_url


def test_fetch_manifest_unsupported():
    """Test fetch manifest with unsupported URL."""
    with pytest.raises(ValueError, match="Unsupported git host"):
        fetch_manifest("https://unknown.example.com/user/plugin")


@pytest.mark.parametrize(
    "repo_url, ref, path, expected",
    [
        (
            "https://github.com/user/plugin",
            "main",
            "MANIFEST.toml",
            "https://raw.githubusercontent.com/user/plugin/main/MANIFEST.toml",
        ),
        (
            "https://gitlab.com/user/plugin",
            "v2",
            "MANIFEST.toml",
            "https://gitlab.com/user/plugin/-/raw/v2/MANIFEST.toml",
        ),
        (
            "https://git.sr.ht/~user/plugin",
            "main",
            "some/path.txt",
            "https://git.sr.ht/~user/plugin/blob/main/some/path.txt",
        ),
        (
            "https://codeberg.org/user/plugin",
            "main",
            "MANIFEST.toml",
            "https://codeberg.org/user/plugin/raw/branch/main/MANIFEST.toml",
        ),
        (
            "https://bitbucket.org/user/plugin",
            "main",
            "MANIFEST.toml",
            "https://bitbucket.org/user/plugin/raw/main/MANIFEST.toml",
        ),
    ],
)
def test_raw_url(repo_url, ref, path, expected):
    """Test raw_url builds correct URLs for each host."""
    assert raw_url(repo_url, ref, path) == expected


def test_raw_url_strips_git_suffix():
    """Test raw_url strips .git suffix."""
    url = raw_url("https://github.com/user/plugin.git", "main", "file.txt")
    assert "plugin.git" not in url
    assert "plugin/main/file.txt" in url


def test_raw_url_unsupported():
    """Test raw_url with unsupported host."""
    with pytest.raises(ValueError, match="Unsupported git host"):
        raw_url("https://unknown.example.com/user/plugin", "main", "file.txt")


def test_validate_manifest_valid():
    """Test validation with valid manifest."""
    manifest = {
        "uuid": "6de6a3bf-a524-42b6-83cb-a36b2ec2e246",
        "name": "Test Plugin",
        "version": "1.0.0",
        "description": "A test plugin",
        "api": ["3.0"],
    }
    validate_manifest(manifest)  # Should not raise


def test_validate_manifest_invalid():
    """Test validation with invalid manifest."""
    manifest = {
        "uuid": "invalid-uuid",
        "name": "Test Plugin",
    }
    with pytest.raises(ValueError, match="Manifest validation failed"):
        validate_manifest(manifest)
