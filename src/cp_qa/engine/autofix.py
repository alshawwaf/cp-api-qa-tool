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
    if "ambiguous" in error_text and "ip address" in error_text:
        fixed = _fix_ambiguous_ip(payload) or fixed

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
