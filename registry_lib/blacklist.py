"""Blacklist operations."""

from registry_lib.registry import Registry
from registry_lib.utils import now_iso8601


def add_blacklist(
    registry: Registry,
    url: str | None = None,
    uuid: str | None = None,
    url_regex: str | None = None,
    reason: str | None = None,
) -> dict[str, str]:
    """Add entry to blacklist.

    Args:
        registry: Registry instance
        url: Git URL to blacklist (optional)
        uuid: Plugin UUID to blacklist (optional)
        url_regex: URL regex pattern to blacklist (optional)
        reason: Reason for blacklisting (required)

    Returns:
        dict: Blacklist entry

    Raises:
        ValueError: If no identifier provided or no reason given
    """
    if not reason:
        raise ValueError("Reason is required for blacklisting")

    if not any([url, uuid, url_regex]):
        raise ValueError("At least one of url, uuid, or url_regex must be provided")

    entry = {
        "reason": reason,
        "blacklisted_at": now_iso8601(),
    }

    # Add identifiers
    if uuid:
        entry["uuid"] = uuid
    if url:
        entry["url"] = url
    if url_regex:
        entry["url_regex"] = url_regex

    registry.add_blacklist(entry)
    return entry
