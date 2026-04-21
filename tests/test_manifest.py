"""Tests for manifest module."""

import subprocess
from unittest.mock import (
    Mock,
    mock_open,
    patch,
)

import pytest

from registry_lib.manifest import (
    GitOperationError,
    _fetch_file_git_cli,
    _fetch_file_pygit2,
    fetch_file_via_clone,
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


def test_fetch_manifest_unsupported_falls_back_to_clone():
    """Test fetch manifest falls back to clone for unknown hosts."""
    manifest_toml = """\
uuid = "6de6a3bf-a524-42b6-83cb-a36b2ec2e246"
name = "Test Plugin"
version = "1.0.0"
description = "A test plugin"
api = ["3.0"]
"""
    with patch("registry_lib.manifest.fetch_file_via_clone", return_value=manifest_toml) as mock_clone:
        manifest = fetch_manifest("https://unknown.example.com/user/plugin", "main")

    assert manifest["name"] == "Test Plugin"
    mock_clone.assert_called_once_with(
        "https://unknown.example.com/user/plugin",
        "main",
        "MANIFEST.toml",
    )


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


def test_raw_url_unknown_host():
    """Test raw_url returns None for unknown hosts."""
    assert raw_url("https://unknown.example.com/user/plugin", "main", "file.txt") is None


@patch("registry_lib.manifest.subprocess.run")
def test_fetch_file_via_clone_success(mock_run):
    """Test successful file fetch via git CLI."""
    manifest_content = 'name = "Test"\n'
    with patch("builtins.open", mock_open(read_data=manifest_content)):
        result = _fetch_file_git_cli("https://example.com/repo", "main", "MANIFEST.toml")

    assert result == manifest_content
    assert mock_run.call_count == 2


@patch("registry_lib.manifest.subprocess.run")
def test_fetch_file_via_clone_clone_fails(mock_run):
    """Test git CLI clone failure raises ValueError."""
    mock_run.side_effect = subprocess.CalledProcessError(
        128,
        "git",
        stderr=b"fatal: repository not found",
    )
    with pytest.raises(GitOperationError, match="Failed to clone"):
        _fetch_file_git_cli("https://example.com/repo", "main", "MANIFEST.toml")


def test_fetch_file_via_clone_prefers_pygit2():
    """Test fetch_file_via_clone uses pygit2 when available."""
    with patch("registry_lib.manifest.pygit2", new=Mock()):
        with patch("registry_lib.manifest._fetch_file_pygit2", return_value="content") as mock_pygit2:
            result = fetch_file_via_clone("https://example.com/repo", "main", "file.txt")

    assert result == "content"
    mock_pygit2.assert_called_once()


def test_fetch_file_via_clone_falls_back_to_git_cli():
    """Test fetch_file_via_clone falls back to git CLI when pygit2 is unavailable."""
    with patch("registry_lib.manifest.pygit2", new=None):
        with patch("registry_lib.manifest._fetch_file_git_cli", return_value="content") as mock_cli:
            result = fetch_file_via_clone("https://example.com/repo", "main", "file.txt")

    assert result == "content"
    mock_cli.assert_called_once()


def test_fetch_file_pygit2_success():
    """Test successful file fetch via pygit2."""
    mock_blob = Mock()
    mock_blob.data = b'name = "Test"\n'
    mock_tree = {"MANIFEST.toml": Mock(id="blob-id")}
    mock_commit = Mock()
    mock_commit.type = 1  # GIT_OBJECT_COMMIT
    mock_commit.peel.return_value = mock_tree
    mock_repo = Mock()
    mock_repo.revparse_single.return_value = mock_commit
    mock_repo.__getitem__ = Mock(return_value=mock_blob)

    with (
        patch("registry_lib.manifest.pygit2") as mock_pygit2,
        patch("registry_lib.manifest.tempfile.TemporaryDirectory") as mock_tmpdir,
    ):
        mock_tmpdir.return_value.__enter__ = Mock(return_value="/tmp/test")
        mock_tmpdir.return_value.__exit__ = Mock(return_value=False)
        mock_pygit2.clone_repository.return_value = mock_repo
        mock_pygit2.GIT_OBJECT_TAG = 4
        result = _fetch_file_pygit2("https://example.com/repo", "main", "MANIFEST.toml")

    assert result == 'name = "Test"\n'


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
