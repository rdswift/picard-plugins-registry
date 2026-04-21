"""MANIFEST.toml fetching and validation."""

import subprocess
import sys
import tempfile

import requests


if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from registry_lib.picard.validator import validate_manifest_dict


GIT_SOURCES = {
    "github.com": lambda url, ref, path: (url.replace("github.com", "raw.githubusercontent.com") + f"/{ref}/{path}"),
    "gitlab.com": lambda url, ref, path: f"{url}/-/raw/{ref}/{path}",
    "git.sr.ht": lambda url, ref, path: f"{url}/blob/{ref}/{path}",
    "codeberg.org": lambda url, ref, path: f"{url}/raw/branch/{ref}/{path}",
    "bitbucket.org": lambda url, ref, path: f"{url}/raw/{ref}/{path}",
}


def raw_url(git_url, ref, path):
    """Build a raw file URL for a git hosting service.

    Args:
        git_url: Git repository URL
        ref: Git ref (branch, tag, or commit)
        path: File path within the repository

    Returns:
        str or None: Raw file URL, or None if the host is not in GIT_SOURCES
    """
    git_url = git_url.rstrip("/").removesuffix(".git")
    for host, build_url in GIT_SOURCES.items():
        if host in git_url:
            return build_url(git_url, ref, path)
    return None


def fetch_file_via_clone(git_url, ref, path):
    """Fetch a file from a git repository via shallow clone.

    Args:
        git_url: Git repository URL
        ref: Git ref (branch, tag, or commit)
        path: File path within the repository

    Returns:
        str: File content

    Raises:
        ValueError: If the clone fails or the file is not found
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "--branch",
                    ref,
                    "--filter=blob:none",
                    "--sparse",
                    git_url,
                    tmpdir,
                ],
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "sparse-checkout", "set", path],
                capture_output=True,
                check=True,
                cwd=tmpdir,
            )
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to clone {git_url}: {e.stderr.decode().strip()}") from e
        filepath = f"{tmpdir}/{path}"
        try:
            with open(filepath) as f:
                return f.read()
        except FileNotFoundError as e:
            raise ValueError(f"File not found in repository: {path}") from e


def fetch_manifest(git_url, ref="main"):
    """Fetch MANIFEST.toml from git repository.

    Uses raw HTTP URL for known hosts, falls back to shallow clone.

    Args:
        git_url: Git repository URL
        ref: Git ref (branch, tag, or commit)

    Returns:
        dict: Parsed MANIFEST.toml content

    Raises:
        ValueError: If manifest cannot be fetched or is invalid
        requests.HTTPError: If HTTP fetch fails for a known host
    """
    url = raw_url(git_url, ref, "MANIFEST.toml")
    if url:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content = response.text
    else:
        content = fetch_file_via_clone(git_url, ref, "MANIFEST.toml")

    return tomllib.loads(content)


def validate_manifest(manifest):
    """Validate MANIFEST.toml structure.

    Args:
        manifest: Parsed MANIFEST.toml dict

    Raises:
        ValueError: If manifest is invalid
    """
    errors = validate_manifest_dict(manifest)
    if errors:
        raise ValueError(f"Manifest validation failed: {', '.join(errors)}")
