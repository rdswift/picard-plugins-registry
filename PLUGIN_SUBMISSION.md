# Plugin Submission Guide

This guide is for **plugin developers** who want to submit a new plugin, update an existing entry, or handle a repository move.

For registry development and maintenance, see [README.md](README.md).

---

## Prerequisites

Your plugin must:

- Be a **git repository** hosted on a public platform (GitHub, GitLab, Codeberg, Bitbucket, Sourcehut, or any git host)
- Have a valid **`MANIFEST.toml`** in the repository root (see the [specification](https://github.com/metabrainz/picard/blob/main/docs/PLUGINSV3/MANIFEST.md))
- Follow the [Picard plugin guidelines](https://picard-docs.musicbrainz.org/)

---

## Setting Up

1. **Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you don't have it:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Fork this repository:**
   - Go to <https://github.com/metabrainz/picard-plugins-registry>
   - Click "Fork"

3. **Clone your fork and set up:**
   ```bash
   git clone https://github.com/YOUR-USERNAME/picard-plugins-registry.git
   cd picard-plugins-registry
   uv sync
   source .venv/bin/activate
   ```

4. **Validate your plugin's manifest** (optional but recommended):
   ```bash
   # From a remote repository
   registry plugin validate https://github.com/YOUR-USERNAME/your-plugin

   # Or from a local directory
   registry plugin validate /path/to/your-plugin
   ```

---

## Submitting a New Plugin

We recommend using **semantic versioning** (git tags like `v1.0.0`, `v1.1.0`, etc.) for your plugin releases. This allows Picard to automatically discover new versions without requiring registry updates.

Before submitting, make sure you have **at least one version tag** pushed to your repository:

```bash
git tag v1.0.0
git push --tags
```

1. **Add your plugin (recommended — with semver):**
   ```bash
   registry plugin add https://github.com/YOUR-USERNAME/your-plugin \
       --trust community \
       --categories metadata \
       --versioning-scheme semver
   ```

   Available categories: `metadata`, `coverart`, `ui`, `scripting`, `formats`, `other`

   Multiple categories can be specified: `--categories metadata,coverart`

   With `--versioning-scheme semver`, releasing a new version is just:
   ```bash
   git tag v1.1.0
   git push --tags
   ```
   Picard will automatically discover the new tag and offer the update to users — no registry PR needed. Without semver, users would only get updates when the branch moves forward, with no clear version to display.

   **Note:** The command fetches `MANIFEST.toml` from the `main` branch by default. If your default branch is named differently (e.g., `master`), specify it with `--refs master`.

2. **Additionally, if your plugin supports multiple Picard versions** with different branches:
   ```bash
   registry plugin add https://github.com/YOUR-USERNAME/your-plugin \
       --trust community \
       --categories metadata \
       --refs 'main:4.0,picard-v3:3.0-3.99'
   ```

3. **Validate the registry:**
   ```bash
   registry validate
   ```

4. **Commit and push:**
   ```bash
   git add plugins.toml
   git commit -m "Add plugin: Your Plugin Name"
   git push
   ```

5. **Create a pull request** at <https://github.com/metabrainz/picard-plugins-registry/pulls>

   The Picard team will review your submission. CI automatically validates the registry — make sure it passes. Once approved and merged, your plugin will be available to all Picard users.

---

## Updating an Existing Plugin

### Updating Metadata

If your plugin's `MANIFEST.toml` has changed (name, description, authors, etc.):

```bash
registry plugin update your-plugin-id
```

This fetches the latest `MANIFEST.toml` from your repository and updates the registry entry. The UUID must match — it cannot change.

Then validate, commit, push, and create a pull request:

```bash
registry validate
git add plugins.toml
git commit -m "Update plugin: your-plugin-id"
git push
```

### Changing Categories or Other Registry Fields

```bash
# Change categories
registry plugin edit your-plugin-id --categories metadata,ui

# Add versioning scheme
registry plugin edit your-plugin-id --versioning-scheme semver
```

Then validate, commit, push, and create a pull request as above.

---

## Moving Your Plugin Repository

If your plugin moves to a new URL (e.g., from a personal account to an organization):

1. **Update the git URL:**
   ```bash
   registry plugin edit your-plugin-id \
       --git-url https://github.com/new-org/your-plugin
   ```

2. **Add a redirect** so users with the old URL still get updates:
   ```bash
   registry plugin redirect your-plugin-id \
       https://github.com/old-user/old-repo
   ```

3. **Validate, commit, push, and create a pull request.**

Users who installed from the old URL will be transparently redirected to the new one.

---

## Pull Request Guidelines

- **One plugin per PR** — don't bundle multiple plugin changes
- **Descriptive title** — e.g., "Add plugin: My Plugin Name" or "Update plugin: my-plugin-id"
- **Include in the PR description:**
  - What the plugin does (for new submissions)
  - What changed (for updates)
  - Link to the plugin repository
- **CI must pass** — the registry is automatically validated
- **Don't edit `plugins.toml` by hand** — always use the `registry` CLI

---

## Trust Levels

All new plugins are added with `community` trust level. After establishing a good track record, plugins may be promoted by the Picard team:

| Level | Description |
|-------|-------------|
| **official** | Maintained by the MusicBrainz Picard team |
| **trusted** | Well-known authors with established reputation |
| **community** | All other plugins (default for new submissions) |

---

## Finding Your Plugin ID

If you're not sure what your plugin ID is:

```bash
registry plugin list
```

The ID is derived from your repository name (e.g., `picard-plugin-my-feature` becomes `my-feature`).

---

## My Repository Was Compromised

If your plugin repository has been compromised (unauthorized access, malicious code injected), act quickly:

### 1. Contact the Picard Team Immediately

- **Email:** <support@metabrainz.org>
- **Forum:** <https://community.metabrainz.org/c/picard>
- **IRC/Matrix:** [#musicbrainz-picard-dev](https://matrix.to/#/#musicbrainz-picard-dev:chatbrainz.org)

Report the compromise with as much detail as possible (what happened, when, which branches/tags are affected). The team will blacklist your plugin to protect users while you regain control.

You can also submit an urgent PR yourself — fork the registry, run the blacklist command, and open a pull request:

```bash
registry blacklist add \
    --uuid YOUR-PLUGIN-UUID \
    --reason "Repository compromised - do not install"
```

### 2. After Regaining Control

Once your repository is secure again:

1. **Generate a new UUID** for your plugin (`python -c "import uuid; print(uuid.uuid4())"`)
2. **Update your `MANIFEST.toml`** with the new UUID
3. **If you moved to a new repository**, update the registry entry:
   ```bash
   registry plugin edit your-plugin-id \
       --git-url https://github.com/YOUR-USERNAME/new-safe-repo
   registry plugin redirect your-plugin-id \
       https://github.com/YOUR-USERNAME/compromised-repo
   ```
4. **Request removal of the blacklist entry** via a pull request

The old UUID remains blacklisted, and existing users are redirected to the safe version via the new UUID.

### What Gets Blocked

| Blacklist method | What it blocks |
|-----------------|----------------|
| `--uuid` | The plugin everywhere, at any URL (recommended) |
| `--url` | A specific repository URL only |
| `--url-regex` | All URLs matching a pattern (e.g., an entire organization) |

For maximum protection, blacklist by UUID — it cannot be evaded by moving the malicious code to a different URL.

---

## Troubleshooting

**"Cannot resolve imported module" or "MANIFEST.toml not found":**
Make sure your `MANIFEST.toml` is in the repository root and pushed to the branch being fetched (default: `main`). Use `--refs` if your default branch has a different name.

**"Plugin with UUID already exists":**
Your plugin's UUID is already registered (possibly under a different URL). Each plugin must have a globally unique UUID.

**"Plugin with git URL already exists":**
This repository URL is already in the registry. Use `registry plugin update` to refresh its metadata instead.

**"Manifest validation failed":**
Run `registry plugin validate` on your repository to see the specific validation errors.

---

## Need Help?

- **Forum:** <https://community.metabrainz.org/c/picard>
- **Plugin documentation:** <https://github.com/metabrainz/picard/blob/main/docs/PLUGINSV3/MANIFEST.md>
- **Registry documentation:** [README.md](README.md)
