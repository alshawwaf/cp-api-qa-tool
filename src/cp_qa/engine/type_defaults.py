"""Type-specific known-good payload defaults.

Some object types (time, network-feed, simple-gateway, etc.) require
very specific field combinations that the generic payload generator
cannot infer.  This module applies proven-working overrides **before**
the first API call to prevent known failures.

Called by :func:`lifecycle.run_lifecycle_test` and
:func:`demo.run_demo_create` before the adaptive ADD loop.
"""

from __future__ import annotations

import random

from cp_qa.engine.testdata import generate_test_data
from cp_qa.logging import get_logger

log = get_logger(__name__)


def apply_type_defaults(
    obj_type: str,
    payload: dict,
    spec: dict | None = None,
    current_obj_type: str = "",
) -> None:
    """Apply type-specific known-good defaults to *payload* in-place.

    Args:
        obj_type:         The Check Point object type (e.g. ``"time"``).
        payload:          Request payload dict (modified in-place).
        spec:             Parsed API spec (needed for VPN community sub-objects).
        current_obj_type: Top-level object type context for test-data generation.
    """
    if obj_type == "time":
        # Time objects need proper date/recurrence format — not random strings
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors"},
        )
        payload["start-now"] = True
        payload["end-never"] = True

    elif obj_type == "time-group":
        _keep_only(
            payload,
            {
                "name", "color", "comments", "members",
                "ignore-warnings", "ignore-errors",
            },
        )

    elif obj_type == "network-feed":
        # Needs a valid feed-url at minimum
        payload["feed-url"] = (
            "https://secureupdates.checkpoint.com/IP-list/TOR.txt"
        )
        payload["feed-format"] = "Flat List"
        payload["feed-type"] = "IP Address"
        for f in [
            "certificate-id", "custom-header", "data-column",
            "fields-delimiter", "ignore-lines-that-start-with",
            "json-query", "use-gateway-proxy", "update-interval",
        ]:
            payload.pop(f, None)

    elif obj_type in ("simple-gateway", "simple-cluster"):
        _keep_only(
            payload,
            {
                "name", "color", "comments",
                "ignore-warnings", "ignore-errors", "ipv4-address", "vpn",
            },
        )
        payload["ipv4-address"] = f"10.100.99.{random.randint(10, 200)}"
        payload["version"] = "R81.10"
        payload["vpn"] = True

    elif obj_type == "checkpoint-host":
        _keep_only(
            payload,
            {
                "name", "color", "comments",
                "ignore-warnings", "ignore-errors", "ipv4-address",
            },
        )
        payload["ipv4-address"] = f"10.100.98.{random.randint(10, 200)}"

    elif obj_type == "interoperable-device":
        _keep_only(
            payload,
            {
                "name", "color", "comments",
                "ignore-warnings", "ignore-errors", "ipv4-address",
            },
        )
        payload["ipv4-address"] = f"10.100.97.{random.randint(10, 200)}"

    elif obj_type == "lsv-profile":
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors"},
        )

    elif obj_type in ("vpn-community-meshed", "vpn-community-star"):
        _apply_vpn_community_defaults(obj_type, payload, spec, current_obj_type)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _keep_only(payload: dict, allowed: set[str]) -> None:
    """Remove all keys from *payload* that are not in *allowed*."""
    for key in list(payload.keys()):
        if key not in allowed:
            payload.pop(key, None)


def _apply_vpn_community_defaults(
    obj_type: str,
    payload: dict,
    spec: dict | None,
    current_obj_type: str,
) -> None:
    """Inject comprehensive defaults for VPN community objects."""
    safe_fields = {
        "name", "color", "comments", "ignore-warnings", "ignore-errors",
        "center-gateways", "gateways", "encryption-method", "encryption-suite",
        "ike-phase-1", "ike-phase-2", "advanced-settings", "vpn-routing",
        "shared-secret", "override-vpn-domains", "ikev1-only", "ikev2-only",
        "satellite-gateways", "advanced-properties",
    }

    if "encryption-method" not in payload:
        payload["encryption-method"] = "prefer ikev2 but support ikev1"
    if "encryption-suite" not in payload:
        payload["encryption-suite"] = "custom"
    if "ike-phase-1" not in payload:
        payload["ike-phase-1"] = generate_test_data(
            {
                "name": "ike-phase-1",
                "types": [{"name": "object", "object-name": "vpn-ike-phase-all"}],
            },
            current_obj_type=current_obj_type,
            spec=spec,
        )
    if "advanced-settings" not in payload:
        payload["advanced-settings"] = generate_test_data(
            {
                "name": "advanced-settings",
                "types": [
                    {
                        "name": "object",
                        "object-name": "vpn-community-advanced-settings",
                    }
                ],
            },
            current_obj_type=current_obj_type,
            spec=spec,
        )

    # Type-specific gateway lists
    if obj_type == "vpn-community-star":
        if not payload.get("center-gateways"):
            payload["center-gateways"] = ["DEMO_SIMPLE_GATEWAY_1"]
        if not payload.get("satellite-gateways"):
            payload["satellite-gateways"] = ["DEMO_INTEROPERABLE_DEVICE_1"]
    elif obj_type == "vpn-community-meshed":
        if not payload.get("gateways"):
            payload["gateways"] = [
                "DEMO_SIMPLE_GATEWAY_1",
                "DEMO_INTEROPERABLE_DEVICE_1",
            ]

    # Strip unsupported fields
    for key in list(payload.keys()):
        if key not in safe_fields:
            payload.pop(key, None)
