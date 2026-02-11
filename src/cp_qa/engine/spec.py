"""API specification fetching and lookup.

Downloads the Check Point Management API specification (a large JSON
document) from ``sc1.checkpoint.com`` and provides helpers to look up
command definitions and object schemas by name or section.
"""

from __future__ import annotations

from typing import Any

import requests

from cp_qa.logging import get_logger

log = get_logger(__name__)


def fetch_spec(spec_url: str) -> dict | None:
    """Download and parse the API specification JSON.

    Args:
        spec_url: Fully qualified URL to the ``apis.json`` spec file
                  (e.g. ``https://sc1.checkpoint.com/…/v2.1/dynamic/apis.json``).

    Returns:
        Parsed specification dictionary, or ``None`` on failure.
    """
    log.info("Fetching API spec from %s", spec_url)
    try:
        response = requests.get(spec_url, verify=False, timeout=30)
        response.raise_for_status()
        spec = response.json()
        log.info(
            "Spec fetched successfully. Commands: %d",
            len(spec.get("commands", [])),
        )
        return spec
    except Exception as exc:
        log.error("Failed to fetch API spec: %s", exc)
        return None


def get_commands_by_section(spec: dict, section_name: str) -> list[dict]:
    """Return all documented commands within a specific section.

    Args:
        spec:         Parsed API specification dictionary.
        section_name: Section/group name to filter by (case-insensitive
                      substring match against the command's ``group`` field).

    Returns:
        List of command definition dicts matching the section.
    """
    if not spec:
        return []

    commands: list[dict] = []
    for cmd in spec.get("commands", []):
        if not cmd.get("documented"):
            continue
        if section_name.lower() in cmd.get("group", "").lower():
            commands.append(cmd)
    return commands


def get_object_by_name(spec: dict, obj_name: str) -> dict | None:
    """Retrieve an object definition from the spec's ``objects`` list.

    Args:
        spec:     Parsed API specification dictionary.
        obj_name: Exact object schema name (e.g. ``"HostRequestNew"``).

    Returns:
        The matching object dict, or ``None`` if not found.
    """
    if not spec:
        return None
    for obj in spec.get("objects", []):
        if obj.get("name") == obj_name:
            return obj
    return None
