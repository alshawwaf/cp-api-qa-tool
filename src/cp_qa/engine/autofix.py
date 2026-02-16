"""Self-healing payload auto-correction.

When an API call fails, this module analyses the error message and
applies targeted fixes to the payload.  It handles:

- Missing co-requisite fields (e.g. ``mask-length`` for ``subnet``)
- Ambiguous IP address configurations (mixed generic + versioned fields)
- Invalid nested object references (``protected-by``, ``interfaces``)
- Type-specific validation errors (NAT conflicts, version strings)
- Domain name formatting (leading dot requirement)

The auto-fix loop runs up to :const:`~cp_qa.constants.MAX_RETRIES` times
in the lifecycle test, progressively stripping or correcting fields until
the API accepts the payload or all known fixes are exhausted.
"""

from __future__ import annotations

import random
import re

from cp_qa.logging import get_logger

log = get_logger(__name__)


def auto_fix_payload(
    payload: dict,
    error_text: str,
    parameters: list[dict],
) -> bool:
    """Analyse API error feedback and fix the payload in-place.

    Examines the (lowercased) error text for known patterns and applies
    the corresponding correction to the payload dictionary.

    Args:
        payload:    The API request payload to fix (modified in-place).
        error_text: Lowercase concatenation of all error messages
                    (including blocking-errors).
        parameters: The full parameter list from the spec, used for
                    generating replacement values.

    Returns:
        ``True`` if at least one fix was applied, ``False`` if no known
        fix matched the error.

    Note:
        The caller should retry the API call after a successful fix.
        Multiple fixes may be needed (run in a loop with max retries).
    """
    fixed = False

    # --- Transient server errors (NPE, generic_server_error) — retry ----
    if any(x in error_text for x in [
        "null pointer exception", "generic_server_error",
        "management server failed to execute command",
        "currently locked by another user",
    ]):
        log.info("  FIX: Transient server error detected — retrying unchanged payload")
        return True

    # --- Web Server must be true when config is populated ----------------
    if "web server" in error_text and "true" in error_text:
        if "host-servers" in payload and isinstance(payload["host-servers"], dict):
            payload["host-servers"]["web-server"] = True
            log.info("  FIX: Set host-servers.web-server = true")
            fixed = True

    # --- Invalid IPv4 netmask --------------------------------------------
    if "not a valid ipv4 netmask" in error_text:
        if "subnet-mask" in payload:
            payload["subnet-mask"] = "255.255.0.0"
            log.info("  FIX: Corrected subnet-mask to 255.255.0.0")
            fixed = True

    # --- Missing mask definition for subnet IPv4/IPv6 --------------------
    if "missing parameter" in error_text and "mask definition" in error_text:
        fixed = _fix_missing_mask(payload, error_text) or fixed

    # --- Ambiguous IP Address configuration ------------------------------
    if "ambiguous" in error_text and any(
        x in error_text for x in ["ip address", "ipv4 address", "ipv6 address"]
    ):
        fixed = _fix_ambiguous_ip(payload) or fixed

    # --- Ambiguous mask definition (subnet-mask vs mask-length) ----------
    if "ambiguous" in error_text and "mask definition" in error_text:
        fixed = _fix_ambiguous_mask(payload) or fixed

    # --- Requested object not found (bad references) ---------------------
    if "requested object" in error_text and "not found" in error_text:
        fixed = _fix_missing_references(payload) or fixed

    # --- Invalid parameter for groups ------------------------------------
    if (
        "invalid parameter" in error_text
        and "groups" in error_text
        and "invalid value" in error_text
    ):
        if "groups" in payload:
            del payload["groups"]
            log.info("  FIX: Removed 'groups' (not supported for this type)")
            fixed = True

    # --- Invalid version string ------------------------------------------
    if "invalid parameter" in error_text and "version" in error_text:
        payload["version"] = "R81.10"
        log.info("  FIX: Set version to 'R81.10'")
        fixed = True

    # --- vpn-domain-type should be manual ---------------------------------
    if "vpn-domain-type" in error_text and "manual" in error_text:
        if "vpn-settings" in payload and isinstance(payload["vpn-settings"], dict):
            payload["vpn-settings"]["vpn-domain-type"] = "manual"
            log.info("  FIX: Set vpn-settings.vpn-domain-type = 'manual'")
            fixed = True
        elif "vpn-settings" in payload:
            del payload["vpn-settings"]
            log.info("  FIX: Removed vpn-settings (vpn-domain-type conflict)")
            fixed = True

    # --- NAT hide-behind / generate-nat-rules conflict -------------------
    if "hide-behind" in error_text and "generate-nat-rules" in error_text:
        payload.pop("nat-settings", None)
        for f in list(payload.keys()):
            if "nat" in f.lower() or "hide-behind" in f.lower():
                del payload[f]
                log.info("  FIX: Removed '%s' (NAT conflict)", f)
        fixed = True

    # --- Nested value-not-valid errors -----------------------------------
    if "value is not valid" in error_text and not fixed:
        fixed = _fix_invalid_nested_value(payload, error_text) or fixed

    # --- Invalid interfaces format ---------------------------------------
    if (
        "parameter" in error_text
        and "interfaces" in error_text
        and "not valid" in error_text
    ):
        if "interfaces" in payload:
            del payload["interfaces"]
            log.info("  FIX: Removed 'interfaces' (format not compatible)")
            fixed = True

    # --- Domain name must start with '.' ---------------------------------
    if "domain name must start" in error_text:
        name = payload.get("name", "")
        if not name.startswith("."):
            payload["name"] = "." + name
            log.info("  FIX: Prepended '.' to domain name -> %s", payload["name"])
            fixed = True

    # --- Unrecognized parameter -------------------------------------------
    if "unrecognized parameter" in error_text:
        fixed = _fix_unrecognized_param(payload, error_text) or fixed

    # --- VPN community: encryption-suite must be "custom" for IKE phases --
    if "encryption-suite" in error_text or (
        "ike-phase" in error_text and "encryption" in error_text
    ):
        if "ike-phase-1" in payload or "ike-phase-2" in payload:
            payload["encryption-suite"] = "custom"
            log.info("  FIX: Forced encryption-suite='custom' for IKE phases")
            fixed = True

    # --- VPN community: strip advanced-settings/vpn-routing on error ------
    if ("advanced-settings" in error_text or "advanced-properties" in error_text) and not fixed:
        for f in ["advanced-settings", "advanced-properties", "vpn-routing"]:
            if f in payload:
                del payload[f]
                log.info("  FIX: Removed '%s' (VPN sub-object validation error)", f)
                fixed = True

    # --- VPN community: shared-secrets format issues ----------------------
    if "shared-secret" in error_text and not fixed:
        for f in ["shared-secrets", "shared-secret"]:
            if f in payload:
                del payload[f]
                log.info("  FIX: Removed '%s' (shared-secret validation error)", f)
                fixed = True

    # --- Address range is not valid (first > last) -----------------------
    if "address range is not valid" in error_text and not fixed:
        fixed = _fix_address_range_order(payload) or fixed

    # --- Mandatory / missing parameter -----------------------------------
    if "mandatory" in error_text and not fixed:
        match = re.search(r"parameter \[([^\]]+)\].*mandatory", error_text)
        if not match:
            match = re.search(r"mandatory.*parameter \[([^\]]+)\]", error_text)
        if match:
            field = match.group(1)
            if "password" in field or "secret" in field:
                payload[field] = "Qa1234!@#$"
            elif "address" in field:
                payload[field] = f"10.100.2.{random.randint(10, 200)}"
            elif "port" in field:
                payload[field] = 8080
            else:
                payload[field] = f"QA_{random.randint(1000, 9999)}"
            log.info("  FIX: Added mandatory field '%s'", field)
            fixed = True

    # --- "not supported" on this server version ---------------------------
    if "not supported" in error_text and "command" in error_text and not fixed:
        log.info("  FIX: Command not supported on this server version")
        return False  # Signal no fix possible

    # --- Generic validation failure (last resort) ------------------------
    if (
        "validation failed" in error_text
        and "blocking-error" in error_text
        and not fixed
    ):
        fixed = _fix_generic_validation(payload) or fixed

    return fixed


# ---------------------------------------------------------------------------
# Fix helpers
# ---------------------------------------------------------------------------

def _fix_missing_mask(payload: dict, error_text: str) -> bool:
    """Add missing mask-length fields for subnet definitions."""
    fixed = False

    if "ipv4" in error_text or "subnet4" in error_text or "subnet ipv4" in error_text:
        if "subnet4" in payload and "mask-length4" not in payload:
            payload["mask-length4"] = 24
            log.info("  FIX: Added mask-length4=24 for subnet4")
            fixed = True
        if (
            "subnet" in payload
            and "subnet4" not in payload
            and "mask-length6" in payload
        ):
            del payload["mask-length6"]
            if "mask-length" not in payload:
                payload["mask-length"] = 24
            log.info(
                "  FIX: Replaced mask-length6 with mask-length=24 for generic subnet"
            )
            fixed = True
        if (
            "mask-length" in payload
            and "subnet4" in payload
            and "mask-length4" not in payload
        ):
            del payload["mask-length"]
            payload["mask-length4"] = 24
            log.info("  FIX: Replaced generic mask-length with mask-length4=24")
            fixed = True

    if "ipv6" in error_text or "subnet6" in error_text or "subnet ipv6" in error_text:
        if "subnet6" in payload and "mask-length6" not in payload:
            payload["mask-length6"] = 64
            log.info("  FIX: Added mask-length6=64 for subnet6")
            fixed = True
        if "mask-length" in payload and "mask-length6" not in payload:
            del payload["mask-length"]
            payload["mask-length6"] = 64
            log.info("  FIX: Replaced generic mask-length with mask-length6=64")
            fixed = True

    return fixed


def _fix_ambiguous_ip(payload: dict) -> bool:
    """Resolve ambiguous IP address configuration (mixed generic + versioned)."""
    fixed = False
    ip_fields = [
        k
        for k in payload
        if "ip-address" in k.lower()
        or "ipv4-address" in k.lower()
        or "ipv6-address" in k.lower()
    ]

    has_standalone = "ip-address" in payload
    has_any_first_last = any(("first" in f or "last" in f) for f in ip_fields)

    # Case 1: standalone + first/last pair -> remove standalone
    if has_standalone and has_any_first_last:
        del payload["ip-address"]
        log.info("  FIX: Removed standalone 'ip-address' (keeping range pair)")
        fixed = True

    # Case 2: generic first/last + versioned fields -> remove generic pair
    elif "ip-address-first" in payload and "ip-address-last" in payload:
        versioned = [f for f in ip_fields if f.startswith(("ipv4-", "ipv6-"))]
        if versioned:
            payload.pop("ip-address-first", None)
            payload.pop("ip-address-last", None)
            log.info(
                "  FIX: Removed generic range (ip-address-first/last), "
                "keeping versioned fields"
            )
            fixed = True

    # Case 3: too many IP fields -> remove all generics
    if not fixed and len(ip_fields) > 2:
        for g in [
            f
            for f in ip_fields
            if f in ("ip-address", "ip-address-first", "ip-address-last")
        ]:
            if g in payload:
                del payload[g]
                log.info("  FIX: Removed generic '%s' to resolve ambiguity", g)
        fixed = True

    # Case 4: subnet field conflicts with IP address on non-network types
    if not fixed and "subnet" in payload and ip_fields:
        del payload["subnet"]
        log.info("  FIX: Removed 'subnet' (conflicts with IP address fields)")
        fixed = True

    return fixed


def _fix_missing_references(payload: dict) -> bool:
    """Remove fields that reference non-existent objects."""
    fixed = False

    # host-servers.web-server-config.protected-by
    if "host-servers" in payload and isinstance(payload["host-servers"], dict):
        wsc = payload["host-servers"].get("web-server-config", {})
        if isinstance(wsc, dict) and "protected-by" in wsc:
            del wsc["protected-by"]
            log.info(
                "  FIX: Removed host-servers.web-server-config.protected-by"
            )
            fixed = True

    # Interfaces with names treated as references
    if (
        "interfaces" in payload
        and isinstance(payload["interfaces"], list)
        and payload["interfaces"]
    ):
        payload["interfaces"] = []
        log.info("  FIX: Simplified interfaces to [] (name treated as reference)")
        fixed = True

    # String-valued reference fields (include, except, members)
    for field in ["include", "except", "members"]:
        if field in payload and isinstance(payload[field], str):
            del payload[field]
            log.info(
                "  FIX: Removed '%s' (referenced non-existent object)", field
            )
            fixed = True

    return fixed


def _fix_invalid_nested_value(payload: dict, error_text: str) -> bool:
    """Strip nested sub-trees that fail value validation."""
    fixed = False

    # Try to extract the root key from the full path in the error
    path_match = re.search(r"full path: ([\w.-]+)", error_text)
    if path_match:
        root_key = path_match.group(1).split(".")[0]
        if root_key in payload:
            del payload[root_key]
            log.info(
                "  FIX: Removed '%s' (nested value validation error)", root_key
            )
            fixed = True

    # Fallback: strip any complex dict-valued fields that aren't known good
    if not fixed:
        _KNOWN_GOOD_DICTS = {"nat-settings", "host-servers"}
        for k, v in list(payload.items()):
            if isinstance(v, dict) and k not in _KNOWN_GOOD_DICTS:
                del payload[k]
                log.info(
                    "  FIX: Removed complex field '%s' (nested validation error)",
                    k,
                )
                fixed = True
                break

    return fixed


def _fix_ambiguous_mask(payload: dict) -> bool:
    """Resolve ambiguous mask definitions (mixed mask types).

    The API rejects payloads that include multiple subnet/mask schemes
    simultaneously (e.g. ``subnet-mask`` alongside ``mask-length4``).
    This handler picks the most specific valid pair and removes the rest,
    both at the top level and inside nested ``interfaces[]`` sub-objects.
    """
    fixed = False

    # Top-level cleanup
    fixed = _clean_mask_fields(payload, "top-level") or fixed

    # Nested: fix inside interfaces[] sub-objects
    if "interfaces" in payload and isinstance(payload["interfaces"], list):
        for iface in payload["interfaces"]:
            if isinstance(iface, dict):
                fixed = _clean_mask_fields(iface, "interfaces[]") or fixed

    return fixed


def _clean_mask_fields(obj: dict, context: str) -> bool:
    """Remove conflicting mask fields from a single dict, keeping one valid pair."""
    fixed = False

    if "subnet4" in obj and "mask-length4" in obj:
        # Keep subnet4/mask-length4, remove everything else
        for f in ["subnet-mask", "subnet", "mask-length", "subnet6", "mask-length6"]:
            if f in obj:
                del obj[f]
                log.info("  FIX: Removed %s.%s (ambiguous with subnet4/mask-length4)", context, f)
                fixed = True
    elif "subnet" in obj and "mask-length" in obj:
        for f in ["subnet-mask", "subnet4", "mask-length4", "subnet6", "mask-length6"]:
            if f in obj:
                del obj[f]
                log.info("  FIX: Removed %s.%s (ambiguous with subnet/mask-length)", context, f)
                fixed = True
    elif "subnet-mask" in obj:
        for f in ["mask-length", "mask-length4", "subnet4", "mask-length6", "subnet6"]:
            if f in obj:
                del obj[f]
                log.info("  FIX: Removed %s.%s (ambiguous with subnet-mask)", context, f)
                fixed = True

    return fixed


def _fix_unrecognized_param(payload: dict, error_text: str) -> bool:
    """Remove parameters the API doesn't recognize for this object type."""
    fixed = False
    # Extract field name from "unrecognized parameter [field-name]"
    match = re.search(r"unrecognized parameter \[([^\]]+)\]", error_text)
    if match:
        field = match.group(1)
        if field in payload:
            del payload[field]
            log.info("  FIX: Removed unrecognized parameter '%s'", field)
            fixed = True
    return fixed


def _fix_generic_validation(payload: dict) -> bool:
    """Progressive fixes for generic 'validation failed' errors."""
    fixed = False

    # Remove details-level (common cause)
    if "details-level" in payload:
        del payload["details-level"]
        log.info("  FIX: Removed 'details-level' (validation issue)")
        return True

    # Swap first > last ordering
    for prefix in ["ip-address-", "ipv4-address-", "ipv6-address-"]:
        first_key = f"{prefix}first"
        last_key = f"{prefix}last"
        if first_key in payload and last_key in payload:
            if "." in str(payload[first_key]) and "." in str(payload[last_key]):
                f_parts = list(map(int, str(payload[first_key]).split(".")))
                l_parts = list(map(int, str(payload[last_key]).split(".")))
                if f_parts > l_parts:
                    payload[first_key], payload[last_key] = (
                        payload[last_key],
                        payload[first_key],
                    )
                    log.info(
                        "  FIX: Swapped %s/%s for correct ordering",
                        first_key,
                        last_key,
                    )
                    return True

    # dns-domain: strip to minimal payload
    if "is-sub-domain" in payload:
        payload["is-sub-domain"] = False
        for field in ["tags", "color", "comments"]:
            payload.pop(field, None)
        log.info("  FIX: Stripped dns-domain to minimal payload")
        return True

    # Remove non-essential fields one at a time (last resort)
    for field in ["set-if-exists", "color", "comments", "tags", "groups"]:
        if field in payload:
            del payload[field]
            log.info(
                "  FIX: Removed non-essential '%s' to resolve validation", field
            )
            return True

    return fixed


def _fix_address_range_order(payload: dict) -> bool:
    """Swap first/last address pairs when the range is invalid (first > last).

    Handles both IPv4 (dotted) and IPv6 (colon-hex) addresses.
    """
    fixed = False
    for prefix in ["ip-address-", "ipv4-address-", "ipv6-address-"]:
        first_key = f"{prefix}first"
        last_key = f"{prefix}last"
        if first_key not in payload or last_key not in payload:
            continue

        first_val = str(payload[first_key])
        last_val = str(payload[last_key])

        # IPv4 comparison
        if "." in first_val and "." in last_val:
            f_parts = list(map(int, first_val.split(".")))
            l_parts = list(map(int, last_val.split(".")))
            if f_parts > l_parts:
                payload[first_key], payload[last_key] = last_val, first_val
                log.info("  FIX: Swapped %s/%s (first > last)", first_key, last_key)
                fixed = True

        # IPv6 comparison (expand :: and compare)
        elif ":" in first_val and ":" in last_val:
            try:
                import ipaddress
                f_addr = ipaddress.IPv6Address(first_val)
                l_addr = ipaddress.IPv6Address(last_val)
                if f_addr > l_addr:
                    payload[first_key], payload[last_key] = last_val, first_val
                    log.info("  FIX: Swapped %s/%s (first > last)", first_key, last_key)
                    fixed = True
            except ValueError:
                pass

    return fixed
