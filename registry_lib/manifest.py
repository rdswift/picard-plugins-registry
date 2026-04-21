"""MANIFEST.toml fetching and validation."""

import sys

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
        str: Raw file URL

    Raises:
        ValueError: If the git host is not supported
    """
    git_url = git_url.rstrip("/").removesuffix(".git")
    for host, build_url in GIT_SOURCES.items():
        if host in git_url:
            return build_url(git_url, ref, path)
    supported = ", ".join(GIT_SOURCES)
    raise ValueError(f"Unsupported git host: {git_url} (supported: {supported})")


def fetch_manifest(git_url, ref="main"):
    """Fetch MANIFEST.toml from git repository.

    Args:
        git_url: Git repository URL
        ref: Git ref (branch, tag, or commit)

    Returns:
        dict: Parsed MANIFEST.toml content

    Raises:
        ValueError: If the git host is not supported or manifest is invalid
        requests.HTTPError: If manifest cannot be fetched
    """
    manifest_url = raw_url(git_url, ref, "MANIFEST.toml")
    response = requests.get(manifest_url, timeout=10)
    response.raise_for_status()

    return tomllib.loads(response.text)


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
