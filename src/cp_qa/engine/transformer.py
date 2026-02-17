"""Universal show-to-add payload transformer.

Given any ``show-*`` API response and the object type, produces an
``add-*`` payload by intersecting the response fields with the
``add-*`` request schema from the API specification.  Type-specific
overrides handle field renames, nested object flattening, and other
known mismatches.

The pipeline has three layers:

1. **Spec intersection** — keep only fields present in the add-* request
   schema (~70 % of fields resolved automatically).
2. **Universal transforms** — strip read-only fields, rename known
   aliases, flatten nested object references.
3. **Type-specific overrides** — small per-type functions that handle
   the remaining ~15 % of edge cases.
"""

from __future__ import annotations

from typing import Any

from cp_qa.engine.params import extract_params_from_obj
from cp_qa.engine.spec import get_object_by_name
from cp_qa.logging import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Shared constants (also imported by capture.py)
# ---------------------------------------------------------------------------

#: Domain names that belong to Check Point built-in objects.
BUILTIN_DOMAINS: frozenset[str] = frozenset({
    "Check Point Data",
    "APPI Data",
    "IPS Data",
    "Check Point",
})

#: Object names treated as wildcards ("any").
ANY_NAMES: frozenset[str] = frozenset({
    "any", "all", "all_users", "all ip and non-ip traffic",
})

#: Well-known Check Point built-in object UIDs -> human-readable names.
WELLKNOWN_UIDS: dict[str, str] = {
    # Actions
    "6c488338-8eec-4103-ad21-cd461ac2c472": "Accept",
    "6c488338-8eec-4103-ad21-cd461ac2c473": "Drop",
    "6c488338-8eec-4103-ad21-cd461ac2c474": "Reject",
    "6c488338-8eec-4103-ad21-cd461ac2c476": "Accept",
    "ea28da66-c5ed-11e2-bc66-aa5c6188709b": "Apply Layer",
    # Track types
    "598ead32-aa42-4615-90ed-f51a5928d41d": "Log",
    "29e53e3d-23bf-48fe-b6b1-d59bd88036f9": "None",
    "902d7be8-c6ef-445d-aaba-d8da6ae3e22c": "Extended Log",
    "cce0fa3f-b6bb-4e9b-b6e6-97af04042af3": "Detailed Log",
    "a5e4b1e5-4dfc-41e1-8e94-f8b13eb81cbf": "Full Log",
    "91a5e99e-4c50-4ad5-9996-2d5ace39b892": "Alert",
    # Common built-in objects
    "97aeb369-9aea-11d5-bd16-0090272ccb30": "Any",
}

# ---------------------------------------------------------------------------
# Layer 1: Spec-based field intersection
# ---------------------------------------------------------------------------

#: Cache add-request field sets per object type to avoid repeated lookups.
_add_fields_cache: dict[str, set[str] | None] = {}


def get_add_request_fields(spec: dict, obj_type: str) -> set[str] | None:
    """Return the set of field names valid for ``add-<type>``.

    Looks up the ``add-<type>`` command in the spec, finds its request
    object definition, and returns all field names from that schema.
    Results are cached per *obj_type*.
    """
    if obj_type in _add_fields_cache:
        return _add_fields_cache[obj_type]

    result: set[str] | None = None
    add_cmd = f"add-{obj_type}"

    for cmd in spec.get("commands", []):
        if cmd.get("name", {}).get("web") == add_cmd:
            request_obj_name = cmd.get("request")
            if not request_obj_name:
                break
            obj_def = get_object_by_name(spec, request_obj_name)
            if obj_def:
                params = extract_params_from_obj(obj_def)
                result = {p["name"] for p in params}
            break

    _add_fields_cache[obj_type] = result
    return result


# ---------------------------------------------------------------------------
# Layer 2: Universal transforms
# ---------------------------------------------------------------------------

#: Fields that are ALWAYS read-only in show-* responses.
UNIVERSAL_READONLY_FIELDS: frozenset[str] = frozenset({
    "uid", "type", "domain", "meta-info", "read-only", "creator",
    "last-modifier", "last-modify-time", "creation-time",
    "icon", "tags",
})

#: Known field renames: show-* key -> add-* key (None = drop).
FIELD_RENAMES: dict[str, str | None] = {
    "subnet": "subnet4",
    "mask-length": "mask-length4",
    "subnet-mask": None,
}

#: Fields that hold nested object references needing flattening.
NESTED_OBJECT_FIELDS: frozenset[str] = frozenset({
    "members", "include", "except",
    "center-gateways", "satellite-gateways",
    "data-types",
    "primary-category",
})


def is_builtin(obj: dict) -> bool:
    """Return True if *obj* is a Check Point built-in (not user-created)."""
    if not isinstance(obj, dict):
        return True
    name = obj.get("name", "").lower()
    if name in ANY_NAMES or not name:
        return True
    domain = obj.get("domain", {})
    if isinstance(domain, dict):
        return domain.get("name", "") in BUILTIN_DOMAINS
    meta = obj.get("meta-info", {})
    if isinstance(meta, dict) and meta.get("creator") in ("System",):
        return True
    return False


def flatten_object_ref(
    value: Any,
    obj_registry: dict[str, dict] | None = None,
) -> Any:
    """Convert a nested object reference to a name string.

    - ``{"name": "foo", "uid": "...", "type": "host"}`` -> ``"foo"``
    - ``[{"name": "a"}, {"name": "b"}]`` -> ``["a", "b"]``
    - ``"any"`` -> ``"any"``
    - UID string -> resolved via *obj_registry* or returned as-is.
    """
    if isinstance(value, dict):
        name = value.get("name", "")
        if name.lower() in ANY_NAMES:
            return "any"
        return name or value.get("uid", "")

    if isinstance(value, list):
        names: list[str] = []
        for item in value:
            flat = flatten_object_ref(item, obj_registry)
            if isinstance(flat, str):
                if flat.lower() in ANY_NAMES:
                    return "any"
                if flat:
                    names.append(flat)
        if not names:
            return "any"
        return names[0] if len(names) == 1 else names

    if isinstance(value, str):
        if value.lower() in ANY_NAMES:
            return "any"
        if obj_registry and value in obj_registry:
            return obj_registry[value].get("name", value)
        if value in WELLKNOWN_UIDS:
            return WELLKNOWN_UIDS[value]
        return value

    return value


# ---------------------------------------------------------------------------
# Layer 3: Type-specific overrides
# ---------------------------------------------------------------------------

def _override_host(payload: dict, show: dict, **kw: Any) -> None:
    """Host: clean NAT settings, strip interfaces."""
    nat = show.get("nat-settings", {})
    if isinstance(nat, dict) and nat.get("auto-rule"):
        clean_nat: dict[str, Any] = {
            "auto-rule": True,
            "method": nat.get("method", "static"),
        }
        if nat.get("ipv4-address"):
            clean_nat["ipv4-address"] = nat["ipv4-address"]
        if nat.get("ipv6-address"):
            clean_nat["ipv6-address"] = nat["ipv6-address"]
        payload["nat-settings"] = clean_nat
    else:
        payload.pop("nat-settings", None)
    payload.pop("interfaces", None)


def _override_network(payload: dict, show: dict, **kw: Any) -> None:
    """Network: field renames subnet->subnet4, mask-length->mask-length4."""
    if "subnet4" not in payload and "subnet" in show:
        payload["subnet4"] = show["subnet"]
    if "mask-length4" not in payload and "mask-length" in show:
        payload["mask-length4"] = show["mask-length"]
    payload.pop("subnet", None)
    payload.pop("mask-length", None)
    payload.pop("subnet-mask", None)


def _override_address_range(payload: dict, show: dict, **kw: Any) -> None:
    """Address-range: ensure first/last address fields are present."""
    for f in ("ipv4-address-first", "ipv4-address-last",
              "ipv6-address-first", "ipv6-address-last"):
        if f in show and f not in payload:
            payload[f] = show[f]


def _override_group(payload: dict, show: dict, **kw: Any) -> None:
    """Group: flatten members list to names."""
    members = show.get("members", [])
    if isinstance(members, list):
        names = [
            flatten_object_ref(m) for m in members
            if isinstance(m, dict) and not is_builtin(m)
        ]
        payload["members"] = [n for n in names if n and n != "any"]
    if not payload.get("members"):
        payload.pop("members", None)


def _override_group_with_exclusion(
    payload: dict, show: dict, **kw: Any,
) -> None:
    """Group-with-exclusion: flatten include/except refs."""
    inc = show.get("include", {})
    if isinstance(inc, dict):
        payload["include"] = inc.get("name", "")
    exc = show.get("except", {})
    if isinstance(exc, dict):
        payload["except"] = exc.get("name", "")


def _override_service_tcp(payload: dict, show: dict, **kw: Any) -> None:
    """Service-TCP: port string, aggressive-aging structure."""
    if "port" in show:
        payload["port"] = str(show["port"])
    aging = show.get("aggressive-aging", {})
    if isinstance(aging, dict) and aging.get("enable"):
        payload["aggressive-aging"] = {
            "enable": True,
            "timeout": aging.get("timeout", 600),
            "use-default-timeout": aging.get("use-default-timeout", False),
            "default-timeout": aging.get("default-timeout", 0),
        }
    else:
        payload.pop("aggressive-aging", None)


def _override_service_udp(payload: dict, show: dict, **kw: Any) -> None:
    """Service-UDP: same port handling as TCP."""
    if "port" in show:
        payload["port"] = str(show["port"])
    aging = show.get("aggressive-aging", {})
    if isinstance(aging, dict) and aging.get("enable"):
        payload["aggressive-aging"] = {
            "enable": True,
            "timeout": aging.get("timeout", 600),
            "use-default-timeout": aging.get("use-default-timeout", False),
            "default-timeout": aging.get("default-timeout", 0),
        }
    else:
        payload.pop("aggressive-aging", None)


def _override_service_group(payload: dict, show: dict, **kw: Any) -> None:
    """Service-group: flatten members to names."""
    reg = kw.get("obj_registry") or {}
    members = show.get("members", [])
    if isinstance(members, list):
        names = [flatten_object_ref(m, reg) for m in members]
        payload["members"] = [n for n in names if n]


def _override_gateway(payload: dict, show: dict, **kw: Any) -> None:
    """Simple-gateway: keep only essential fields + interfaces."""
    _KEEP = {
        "name", "ipv4-address", "ipv6-address", "color", "comments",
        "firewall", "vpn", "application-control", "url-filtering",
        "content-awareness", "ips", "anti-bot", "anti-virus",
        "interfaces", "one-time-password", "version",
        "ignore-warnings", "ignore-errors",
    }
    for k in list(payload.keys()):
        if k not in _KEEP:
            payload.pop(k, None)
    # Normalize interfaces
    raw_ifaces = show.get("interfaces", [])
    if isinstance(raw_ifaces, dict):
        raw_ifaces = raw_ifaces.get("objects", raw_ifaces.get("add", []))
    if isinstance(raw_ifaces, list) and raw_ifaces:
        clean_ifaces = []
        for iface in raw_ifaces:
            if not isinstance(iface, dict):
                continue
            clean_ifaces.append({
                "name": iface.get("name", ""),
                "ipv4-address": iface.get("ipv4-address", ""),
                "ipv4-network-mask": iface.get("ipv4-network-mask",
                                                iface.get("subnet-mask", "")),
                "topology": iface.get("topology", "automatic"),
                "anti-spoofing": iface.get("anti-spoofing", False),
            })
        payload["interfaces"] = clean_ifaces


def _override_vpn_community(payload: dict, show: dict, **kw: Any) -> None:
    """VPN community: flatten gateway lists."""
    reg = kw.get("obj_registry") or {}
    for field in ("center-gateways", "satellite-gateways"):
        refs = show.get(field, [])
        if isinstance(refs, list):
            payload[field] = [flatten_object_ref(r, reg) for r in refs]


def _override_application_site(
    payload: dict, show: dict, **kw: Any,
) -> None:
    """Application-site: flatten primary-category, handle url-list."""
    cat = show.get("primary-category", {})
    if isinstance(cat, dict):
        payload["primary-category"] = cat.get("name", "")
    urls = show.get("url-list", [])
    if isinstance(urls, list):
        payload["url-list"] = urls


def _override_access_rule(payload: dict, show: dict, **kw: Any) -> None:
    """Access-rule: flatten action/track/source/dest/service, add position."""
    reg = kw.get("obj_registry") or {}

    # Action
    action = show.get("action", {})
    if isinstance(action, dict):
        aname = action.get("name", "Drop")
        if "inner" in aname.lower() or aname.lower() == "apply layer":
            payload["action"] = "Apply Layer"
        else:
            payload["action"] = aname
    elif isinstance(action, str):
        payload["action"] = WELLKNOWN_UIDS.get(action, action)

    # Track
    track = show.get("track", {})
    if isinstance(track, dict):
        t = track.get("type", {})
        if isinstance(t, dict):
            tname = t.get("name") or WELLKNOWN_UIDS.get(t.get("uid", ""), "Log")
            payload["track"] = {"type": tname}
        elif isinstance(t, str):
            payload["track"] = {"type": WELLKNOWN_UIDS.get(t, t)}
        else:
            payload["track"] = {"type": "Log"}
    else:
        payload["track"] = {"type": "Log"}

    # Source / destination / service / time — flatten to names
    for field in ("source", "destination", "service", "install-on",
                  "vpn", "content", "time"):
        if field in show:
            payload[field] = flatten_object_ref(show[field], reg)

    # Inline layer — resolve UID to name via registry
    il = show.get("inline-layer")
    if isinstance(il, dict):
        payload["inline-layer"] = il.get("name", "")
    elif isinstance(il, str) and il:
        if reg and il in reg:
            payload["inline-layer"] = reg[il].get("name", il)
        else:
            payload["inline-layer"] = WELLKNOWN_UIDS.get(il, il)

    # Position (show-* never returns this; add-* requires it)
    payload["position"] = payload.get("position", "bottom")

    # Strip fields that shouldn't be on rules
    for f in ("uid", "type", "rule-number", "enabled", "hits",
              "comments-uuid", "domain"):
        payload.pop(f, None)


def _override_access_section(payload: dict, show: dict, **kw: Any) -> None:
    """Access-section: add position."""
    payload["position"] = payload.get("position", "bottom")


def _override_nat_rule(payload: dict, show: dict, **kw: Any) -> None:
    """NAT rule: flatten original/translated refs, add position + method."""
    reg = kw.get("obj_registry") or {}
    for field in ("original-source", "original-destination",
                  "original-service", "translated-source",
                  "translated-destination", "translated-service"):
        val = show.get(field, {})
        if isinstance(val, dict):
            name = val.get("name", "")
            if name.lower() in ANY_NAMES or name.lower() == "original":
                payload[field] = name.capitalize() if name.lower() == "original" else "any"
            else:
                payload[field] = name
        elif isinstance(val, str):
            payload[field] = flatten_object_ref(val, reg)

    payload["position"] = payload.get("position", "bottom")
    if "method" in show:
        payload["method"] = show["method"]
    for f in ("uid", "type", "rule-number", "enabled", "hits",
              "comments-uuid", "domain", "auto-generated"):
        payload.pop(f, None)


def _override_threat_rule(payload: dict, show: dict, **kw: Any) -> None:
    """Threat rule: flatten protected-scope, action, track."""
    reg = kw.get("obj_registry") or {}
    for field in ("source", "destination", "service",
                  "protected-scope", "install-on"):
        if field in show:
            payload[field] = flatten_object_ref(show[field], reg)

    action = show.get("action", {})
    if isinstance(action, dict):
        payload["action"] = action.get("name", "Detect")

    track = show.get("track", {})
    if isinstance(track, dict):
        payload["track"] = track.get("name", "Log")

    payload["position"] = payload.get("position", "bottom")
    for f in ("uid", "type", "rule-number", "enabled", "hits",
              "comments-uuid", "domain"):
        payload.pop(f, None)


#: Dispatch table: object type -> override function.
_TYPE_OVERRIDES: dict[str, Any] = {
    "host": _override_host,
    "network": _override_network,
    "address-range": _override_address_range,
    "group": _override_group,
    "group-with-exclusion": _override_group_with_exclusion,
    "service-tcp": _override_service_tcp,
    "service-udp": _override_service_udp,
    "service-group": _override_service_group,
    "simple-gateway": _override_gateway,
    "simple-cluster": _override_gateway,
    "vpn-community-meshed": _override_vpn_community,
    "vpn-community-star": _override_vpn_community,
    "application-site": _override_application_site,
    "access-rule": _override_access_rule,
    "access-section": _override_access_section,
    "nat-rule": _override_nat_rule,
    "threat-rule": _override_threat_rule,
}


# ---------------------------------------------------------------------------
# Deep-flatten helper
# ---------------------------------------------------------------------------

def _is_object_ref(val: Any) -> bool:
    """Return True if *val* looks like a CP object reference dict."""
    return (isinstance(val, dict)
            and "uid" in val
            and ("name" in val or "type" in val))


def _deep_flatten_refs(
    data: dict | list,
    obj_registry: dict[str, dict] | None = None,
) -> None:
    """Recursively flatten nested object-reference dicts to name strings.

    Modifies *data* in-place.  Any dict value that looks like a CP object
    reference (has ``uid`` + ``name``/``type``) is replaced with the name
    string.  Lists of such dicts are replaced with lists of names.
    """
    if isinstance(data, dict):
        for key in list(data.keys()):
            val = data[key]
            if _is_object_ref(val):
                data[key] = flatten_object_ref(val, obj_registry)
            elif isinstance(val, list):
                new_list: list[Any] = []
                any_flattened = False
                for item in val:
                    if _is_object_ref(item):
                        flat = flatten_object_ref(item, obj_registry)
                        new_list.append(flat)
                        any_flattened = True
                    elif isinstance(item, str):
                        resolved = None
                        if obj_registry and item in obj_registry:
                            resolved = obj_registry[item].get("name", item)
                        elif item in WELLKNOWN_UIDS:
                            resolved = WELLKNOWN_UIDS[item]
                        if resolved:
                            new_list.append(resolved)
                            any_flattened = True
                        else:
                            new_list.append(item)
                    elif isinstance(item, dict):
                        _deep_flatten_refs(item, obj_registry)
                        new_list.append(item)
                    else:
                        new_list.append(item)
                if any_flattened:
                    data[key] = new_list
            elif isinstance(val, dict):
                _deep_flatten_refs(val, obj_registry)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def transform_show_to_add(
    obj_type: str,
    show_response: dict,
    spec: dict,
    obj_registry: dict[str, dict] | None = None,
) -> dict | None:
    """Transform a ``show-*`` response into an ``add-*`` payload.

    Pipeline:

    1. Get valid ``add-*`` fields from spec (spec intersection).
    2. Strip universal read-only fields.
    3. Apply field renames (``subnet`` -> ``subnet4``, etc.).
    4. Flatten nested objects (object dicts -> names).
    5. Apply type-specific overrides.
    6. Final validation pass.

    Args:
        obj_type:      CP object type (e.g. ``"host"``, ``"network"``).
        show_response: Full ``show-*`` API response dict.
        spec:          Parsed API specification.
        obj_registry:  Optional UID->object dict for resolving references.

    Returns:
        Clean ``add-*`` payload dict, or ``None`` if transformation fails.
    """
    if not show_response or not show_response.get("name"):
        return None

    # --- Layer 1: Spec intersection ---
    valid_fields = get_add_request_fields(spec, obj_type)

    if valid_fields:
        # Start with fields present in both show response and add-request schema
        payload = {
            k: v for k, v in show_response.items()
            if k in valid_fields
        }
    else:
        # Spec not available for this type — copy everything, rely on
        # Layer 2 + 3 to clean up.
        payload = dict(show_response)

    # --- Layer 2: Universal transforms ---

    # 2a. Strip read-only fields
    for f in UNIVERSAL_READONLY_FIELDS:
        payload.pop(f, None)

    # 2b. Field renames
    for old_name, new_name in FIELD_RENAMES.items():
        if old_name in payload:
            val = payload.pop(old_name)
            if new_name is not None and new_name not in payload:
                payload[new_name] = val

    # 2c. Flatten nested object references
    for field in NESTED_OBJECT_FIELDS:
        if field in payload:
            payload[field] = flatten_object_ref(
                payload[field], obj_registry,
            )

    # --- Layer 3: Type-specific overrides ---
    override_fn = _TYPE_OVERRIDES.get(obj_type)
    if override_fn:
        override_fn(payload, show_response, obj_registry=obj_registry)

    # --- Layer 3b: Deep-flatten any remaining nested object references ---
    # Recursively convert dicts with {uid, name, type} into just the name
    # string, catching deeply nested references missed by field-level passes.
    _deep_flatten_refs(payload, obj_registry)

    # --- Layer 4: Final cleanup ---
    # Remove None / empty-string values (except for fields where "" is valid)
    for k in list(payload.keys()):
        v = payload[k]
        if v is None:
            del payload[k]
        elif v == "" and k != "comments":
            del payload[k]

    # Ensure name is present
    if "name" not in payload:
        payload["name"] = show_response.get("name", "")
    if not payload.get("name"):
        return None

    return payload
