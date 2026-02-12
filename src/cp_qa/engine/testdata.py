"""Test data generation for API payloads.

Generates realistic, type-aware test values for every field in the
API specification.  Handles enums, booleans, integers, IPv4/IPv6
addresses, subnet masks, nested sub-objects, and lists.

The generator uses contextual hints (field name patterns like
``"ipv4-address"`` or ``"mask-length"``) to produce values that
pass server-side validation on the first attempt wherever possible.
"""

from __future__ import annotations

import random
from typing import Any

from cp_qa.engine.spec import get_object_by_name
from cp_qa.logging import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Type selection
# ---------------------------------------------------------------------------

def select_best_type(types: list[dict]) -> dict:
    """Select the most appropriate type from a multi-type field definition.

    Strategy (in priority order):
        1. Any type with ``valid-values`` (enum) — most constrained.
        2. A ``list`` whose elements are objects — richest payload.
        3. An ``object`` with an ``object-name`` — nested sub-object.
        4. A simple ``list`` (of strings).
        5. Fall back to the first type.

    Args:
        types: List of type-definition dicts from the API spec.

    Returns:
        The single best type dict to use for value generation.
    """
    if not types:
        return {"name": "string"}

    # Prefer enums
    for t in types:
        if t.get("valid-values"):
            return t

    # Prefer list-of-objects (e.g. interfaces)
    for t in types:
        if t.get("name") == "list":
            element = t.get("element-type", {})
            if element.get("name") == "object" and element.get("object-name"):
                return t

    # Prefer named objects
    for t in types:
        if t.get("name") == "object" and t.get("object-name"):
            return t

    # Prefer simple lists
    for t in types:
        if t.get("name") == "list":
            return t

    return types[0]


# ---------------------------------------------------------------------------
# Sub-object building
# ---------------------------------------------------------------------------

def get_sub_object_name_hints(object_name: str) -> dict:
    """Return contextual realistic values for sub-object fields.

    Provides known-good defaults for common nested object types
    (interfaces, web-server configs, host-servers, IKE phases, etc.)
    so that generated sub-objects pass validation.

    Args:
        object_name: The spec object-name (e.g. ``"InterfaceRequest"``).

    Returns:
        Dict of field-name -> value hints.
    """
    name_lower = object_name.lower()

    if "interface" in name_lower and object_name.endswith("Request"):
        return {
            "name": "eth0",
            "subnet": "10.200.0.0",
            "mask-length": 24,
            "comments": "QA test interface",
        }
    if "webserver" in name_lower or "web_server" in name_lower:
        return {
            "additional-ports": ["80", "443"],
            "application-engines": ["ASP", "General"],
            "operating-system": "x86 linux",
        }
    if "hostservers" in name_lower or "host.servers" in name_lower:
        return {
            "dns-server": "true",
            "mail-server": "true",
            "web-server": "true",
        }
    if "nat-settings" in name_lower or "natsettings" in name_lower:
        return {
            "auto-rule": True,
            "method": "hide",
            "hide-behind": "gateway",
            "install-on": "Policy Targets"
        }
    if "ike-phase" in name_lower:
        return {
            "data-integrity": "sha256",
            "encryption-algorithm": "aes-256",
            "diffie-hellman-group": "group-19",
        }
    if (
        "advanced-settings" in name_lower
        or "vpn-routing" in name_lower
        or "vpn-advanced-settings" in name_lower
    ):
        return {
            "support-ip-compression": True,
            "use-aggressive-mode": False,
            "vpn-routing-usage": "all",
        }
    if "advanced-properties" in name_lower:
        return {
            "support-ip-compression": True,
            "use-aggressive-mode": False,
        }

    return {}


def build_sub_object(
    object_name: str,
    spec: dict,
    current_obj_type: str = "",
    depth: int = 0,
) -> dict:
    """Recursively build a fully populated sub-object from the spec.

    Populates **all** fields (required + optional) to create realistic
    payloads.  Uses a depth limit to prevent infinite recursion on
    circular references.

    Args:
        object_name:     Spec object-name to build (e.g. ``"NatSettings"``).
        spec:            Parsed API specification dictionary.
        current_obj_type: The top-level object type being tested
                         (used for contextual value generation).
        depth:           Current recursion depth (max 3).

    Returns:
        A dict representing the fully populated sub-object.
    """
    if depth > 3:
        return {}

    name_hints = get_sub_object_name_hints(object_name)

    obj_def = get_object_by_name(spec, object_name)
    if not obj_def:
        return name_hints

    # Special handling for nat-settings: use proven working config
    if "NatSettings" in object_name and "CommWithServer" not in object_name:
        return {"auto-rule": "true", "method": "hide", "hide-behind": "gateway"}

    result = dict(name_hints)

    for section in ["required-fields", "fields", "under-more-fields"]:
        for field in obj_def.get(section, []):
            fname = field.get("name", "")
            ftypes = field.get("types", [{"name": "string"}])

            # Skip details-level within sub-objects (not useful for test data)
            if fname == "details-level":
                continue

            # Special case: interfaces list with realistic dummy
            if fname == "interfaces":
                result[fname] = [
                    {
                        "name": "eth0",
                        "subnet": "10.200.0.0",
                        "mask-length": 24,
                        "color": "aquamarine",
                        "comments": "QA test interface",
                        "ignore-warnings": True,
                        "ignore-errors": True,
                    }
                ]
                continue

            param_info = {"name": fname, "types": ftypes}
            best_type = select_best_type(ftypes)

            if best_type.get("name") == "object" and best_type.get("object-name"):
                result[fname] = build_sub_object(
                    best_type["object-name"], spec, current_obj_type, depth + 1
                )
            elif best_type.get("name") == "list":
                element = best_type.get("element-type", {})
                if element.get("name") == "object" and element.get("object-name"):
                    sub = build_sub_object(
                        element["object-name"], spec, current_obj_type, depth + 1
                    )
                    result[fname] = [sub] if sub else []
                else:
                    result[fname] = []
            else:
                # Only generate if not already set by hints
                if fname not in result:
                    result[fname] = generate_test_data(
                        param_info, current_obj_type=current_obj_type, spec=spec
                    )

    # Post-build fixup: web-server must be true when web-server-config is set
    if "web-server-config" in result and result["web-server-config"]:
        result["web-server"] = True

    return result


# ---------------------------------------------------------------------------
# Value generation
# ---------------------------------------------------------------------------

def generate_test_data(
    param_info: dict,
    current_obj_type: str = "",
    spec: dict | None = None,
    seed: int | None = None,
) -> Any:
    """Generate a valid test value using the full type schema from the spec.

    Applies contextual heuristics based on the field name to produce
    values that are likely to pass server-side validation (correct IP
    formats, valid mask lengths, proper enum values, etc.).

    Args:
        param_info:       Parameter info dict with ``name`` and ``types`` keys.
        current_obj_type: Top-level object type being tested (e.g.
                         ``"multicast-address-range"``), used for
                         context-specific value selection.
        spec:             Parsed API spec (needed for sub-object building).
        seed:             Optional deterministic seed for IPv6 generation.

    Returns:
        A value of the appropriate type (str, int, bool, list, or dict).
    """
    types = param_info.get("types", [{"name": "string"}])
    name = param_info.get("name", "").lower()

    primary_type = select_best_type(types)
    type_name = primary_type.get("name", "string")
    valid_values = primary_type.get("valid-values", [])
    object_name = primary_type.get("object-name", "")

    # --- 1. ENUMS: pick from valid-values ---
    if valid_values:
        return random.choice(valid_values)

    # --- 2. SUB-OBJECTS: build from spec definition ---
    if type_name == "object" and object_name and spec:
        return build_sub_object(object_name, spec, current_obj_type)

    # --- 3. LISTS ---
    if type_name == "list":
        element = primary_type.get("element-type", {})
        if (
            element.get("name") == "object"
            and element.get("object-name")
            and spec
        ):
            sub = build_sub_object(element["object-name"], spec, current_obj_type)
            return [sub] if sub else []
        return []

    # --- 4. BOOLEANS ---
    if type_name == "boolean":
        if any(
            x in name
            for x in [
                "ignore-warnings",
                "ignore-errors",
                "set-if-exists",
                "auto-rule",
            ]
        ):
            return True
        if "is-sub-domain" in name:
            return False
        return False

    # --- 5. INTEGERS ---
    if type_name == "integer":
        if "mask-length" in name:
            return 64 if "6" in name else 24
        return random.randint(1, 100)

    # --- 6. STRINGS: contextual values based on field name ---

    # IPv6 addresses
    if any(x in name for x in ["ipv6", "subnet6"]):
        if "subnet" in name:
            return "2001:db8:85a3::"
        # Multicast context: valid IPv6 multicast range (ff00::/8)
        if current_obj_type == "multicast-address-range":
            if "first" in name:
                return "ff05::1:1"
            if "last" in name:
                return "ff05::1:30"
            return "ff05::1:10"
        # Deterministic first/last to guarantee first < last
        if "first" in name:
            return "2001:db8:85a3::1000"
        if "last" in name:
            return "2001:db8:85a3::2000"
        val = seed if seed is not None else random.randint(0x1000, 0x4000)
        return f"2001:db8:85a3::{val:04x}"

    # IPv4 addresses / subnets
    if any(x in name for x in ["ip-address", "ipv4", "subnet", "first", "last"]):
        if "subnet" in name:
            return "10.100.0.0"
        # Multicast context: valid multicast range (224.x.x.x)
        if current_obj_type == "multicast-address-range":
            if "first" in name:
                return "224.0.1.10"
            if "last" in name:
                return "224.0.1.30"
            return "224.0.1.20"
        # Deterministic first/last to guarantee first < last
        if "first" in name:
            return "10.100.1.10"
        if "last" in name:
            return "10.100.1.30"
        return f"10.100.1.{random.randint(10, 200)}"

    # Netmasks (subnet-mask, ipv4-mask-wildcard, etc.)
    if "mask" in name and "length" not in name:
        if "wildcard" in name:
            return "0000:0000:0000:00ff::" if "6" in name else "0.0.0.255"
        return "ffff:ffff:ffff:ffff::" if "6" in name else "255.255.255.0"

    # Comments
    if "comments" in name:
        return "QA Automated Test Object"

    # Name: deferred to the test harness for top-level objects
    if name == "name":
        pass

    # Install-on
    if "install-on" in name:
        return "Policy Targets"

    # VPN-specific fields
    if name == "encryption-method":
        return "prefer ikev2 but support ikev1"
    if name == "encryption-suite":
        return random.choice(["suite-b-gcm-256", "custom", "vpn a", "vpn b"])
    if name == "vpn-routing":
        return "to center and to other satellites"
    if name == "tunnel-granularity":
        return "per_subnet"

    # Default string fallback
    return f"QA_{random.randint(1000, 9999)}"
