"""Plugin operations."""

from registry_lib.manifest import fetch_manifest, validate_manifest
from registry_lib.picard.constants import REGISTRY_TRUST_LEVELS
from registry_lib.utils import derive_plugin_id, now_iso8601


DEFAULT_REF = "main"


def _sync_optional_fields(plugin, manifest, fields):
    """Sync optional fields from manifest to plugin.

    Args:
        plugin: Plugin dict to update
        manifest: Manifest dict to read from
        fields: List of field names to sync
    """
    for field in fields:
        if field in manifest:
            plugin[field] = manifest[field]
        elif field in plugin:
            del plugin[field]


def add_plugin(registry, git_url, trust_level, categories=None, refs=None):
    """Add plugin to registry.

    Args:
        registry: Registry instance
        git_url: Git repository URL
        trust_level: Trust level (official, trusted, community)
        categories: List of categories (optional)
        refs: Comma-separated refs with optional API versions (e.g., "main:4.0,picard-v3:3.0-3.99")
              or None for default "main"

    Returns:
        dict: Added plugin entry

    Raises:
        ValueError: If validation fails or plugin exists
    """
    if trust_level not in REGISTRY_TRUST_LEVELS:
        raise ValueError(f"Invalid trust level: {trust_level}")

    # Parse refs
    if refs:
        refs_list = _parse_refs(refs)
    else:
        refs_list = [{"name": DEFAULT_REF}]

    # Fetch and validate manifest from first ref (default ref)
    manifest = fetch_manifest(git_url, refs_list[0]["name"])
    validate_manifest(manifest)

    # Derive plugin ID
    plugin_id = derive_plugin_id(git_url)

    # Check for duplicates in single pass
    for existing in registry.data["plugins"]:
        if existing["git_url"] == git_url:
            raise ValueError(f"Plugin with git URL '{git_url}' already exists (plugin: {existing['id']})")
        if existing["uuid"] == manifest["uuid"]:
            raise ValueError(f"Plugin with UUID '{manifest['uuid']}' already exists (plugin: {existing['id']})")

    # Check for duplicate ID
    if registry.find_plugin(plugin_id):
        raise ValueError(f"Plugin with ID '{plugin_id}' already exists")

    # Build plugin entry
    now = now_iso8601()
    plugin = {
        "id": plugin_id,
        "uuid": manifest["uuid"],
        "name": manifest["name"],
        "description": manifest["description"],
        "git_url": git_url,
        "categories": categories or manifest.get("categories", []),
        "trust_level": trust_level,
        "authors": manifest.get("authors", []),
        "added_at": now,
        "updated_at": now,
    }

    # Add optional fields
    _sync_optional_fields(plugin, manifest, ["maintainers", "name_i18n", "description_i18n"])

    # Add refs if not default single main
    if not (len(refs_list) == 1 and refs_list[0]["name"] == DEFAULT_REF and "min_api_version" not in refs_list[0]):
        plugin["refs"] = refs_list

    registry.add_plugin(plugin)
    return plugin


def _parse_refs(refs_str):
    """Parse refs string.

    Formats:
    - "main" - single ref
    - "main,beta" - multiple refs
    - "main:4.0" - ref with min API version
    - "main:4.0-4.99" - ref with min and max API versions
    - "main:4.0,picard-v3:3.0-3.99" - multiple refs with versions

    Args:
        refs_str: Comma-separated refs string

    Returns:
        list: List of ref dicts with name and optional API versions
    """
    refs = []
    for ref_spec in refs_str.split(','):
        ref_spec = ref_spec.strip()
        if ':' in ref_spec:
            # Format: name:api_version or name:min-max
            name, api_spec = ref_spec.split(':', 1)
            ref = {"name": name.strip()}
            if '-' in api_spec:
                min_api, max_api = api_spec.split('-', 1)
                ref["min_api_version"] = min_api.strip()
                ref["max_api_version"] = max_api.strip()
            else:
                ref["min_api_version"] = api_spec.strip()
        else:
            # Simple format: just name
            ref = {"name": ref_spec}
        refs.append(ref)
    return refs


def update_plugin(registry, plugin_id, ref=None):
    """Update plugin metadata from MANIFEST.

    Args:
        registry: Registry instance
        plugin_id: Plugin ID to update
        ref: Git ref to fetch from (optional, defaults to first ref or main)

    Returns:
        dict: Updated plugin entry

    Raises:
        ValueError: If plugin not found, validation fails, or UUID changed
    """
    plugin = registry.find_plugin(plugin_id)
    if not plugin:
        raise ValueError(f"Plugin {plugin_id} not found")

        refs = plugin.get("refs", [{"name": DEFAULT_REF}])
    if ref is None:
        refs = plugin.get("refs", [{"name": "main"}])
        ref = refs[0]["name"]

    # Fetch and validate manifest
    manifest = fetch_manifest(plugin["git_url"], ref)
    validate_manifest(manifest)

    # Check UUID hasn't changed
    if manifest["uuid"] != plugin["uuid"]:
        raise ValueError(
            f"UUID mismatch: MANIFEST has {manifest['uuid']} but registry has {plugin['uuid']}. UUIDs must not change."
        )

    # Update fields from manifest
    plugin["name"] = manifest["name"]
    plugin["description"] = manifest["description"]
    plugin["authors"] = manifest.get("authors", [])
    plugin["updated_at"] = now_iso8601()

    # Update optional fields
    _sync_optional_fields(plugin, manifest, ["maintainers", "name_i18n", "description_i18n"])

    return plugin
