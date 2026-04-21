"""MANIFEST.toml fetching and validation."""

import shutil
import subprocess
import sys
import tempfile

import requests


try:
    import pygit2
except ImportError:
    pygit2 = None


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


def _fetch_file_pygit2(git_url, ref, path):
    """Fetch a file using pygit2 (no git CLI needed)."""
    tmpdir = tempfile.mkdtemp()
    try:
        repo = pygit2.clone_repository(git_url, tmpdir, bare=True)
        commit = repo.revparse_single(ref)
        if commit.type == pygit2.GIT_OBJECT_TAG:
            commit = commit.peel(pygit2.Commit)
        entry = commit.peel(pygit2.Tree)[path]
        return repo[entry.id].data.decode()
    except (KeyError, pygit2.GitError) as e:
        raise ValueError(f"Failed to fetch {path} from {git_url}: {e}") from e
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _fetch_file_git_cli(git_url, ref, path):
    """Fetch a file using git CLI with shallow sparse clone."""
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
        try:
            with open(f"{tmpdir}/{path}") as f:
                return f.read()
        except FileNotFoundError as e:
            raise ValueError(f"File not found in repository: {path}") from e


def fetch_file_via_clone(git_url, ref, path):
    """Fetch a file from a git repository via clone.

    Uses pygit2 if available, otherwise falls back to git CLI.

    Args:
        git_url: Git repository URL
        ref: Git ref (branch, tag, or commit)
        path: File path within the repository

    Returns:
        str: File content

    Raises:
        ValueError: If the clone fails or the file is not found
    """
    if pygit2 is not None:
        return _fetch_file_pygit2(git_url, ref, path)
    return _fetch_file_git_cli(git_url, ref, path)


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
