"""Capture a live policy from an SMS and produce a deployable blueprint.

Connects to a running Security Management Server, reads the full policy
package (rules, sections, inline layers) and all referenced objects,
then returns a blueprint dict that can be deployed on a fresh SMS via
``--action push-blueprint``.

Usage (via CLI)::

    cp-qa -m 10.1.1.100 -u admin --mode demo --action capture-blueprint
    cp-qa -m 10.1.1.100 -u admin --mode demo --action capture-blueprint --blueprint blueprints/my_policy.json
"""

from __future__ import annotations

import datetime
from typing import Any

from cp_qa.logging import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Domain names that belong to Check Point built-in objects.
_BUILTIN_DOMAINS = frozenset({
    "Check Point Data",
    "APPI Data",
    "IPS Data",
    "Check Point",
})

#: Object names that are always treated as "any" (wildcard).
_ANY_NAMES = frozenset({"any", "all", "all_users", "all ip and non-ip traffic"})

#: Well-known Check Point built-in object UIDs → human-readable names.
#: Used as a fallback when the objects-dictionary is missing an entry.
_WELLKNOWN_UIDS: dict[str, str] = {
    # Actions
    "6c488338-8eec-4103-ad21-cd461ac2c472": "Accept",
    "6c488338-8eec-4103-ad21-cd461ac2c473": "Drop",
    "6c488338-8eec-4103-ad21-cd461ac2c474": "Reject",
    "6c488338-8eec-4103-ad21-cd461ac2c476": "Accept",   # Accept (alternate UID variant)
    "ea28da66-c5ed-11e2-bc66-aa5c6188709b": "Apply Layer",
    # Track types
    "598ead32-aa42-4615-90ed-f51a5928d41d": "Log",
    "29e53e3d-23bf-48fe-b6b1-d59bd88036f9": "None",
    "902d7be8-c6ef-445d-aaba-d8da6ae3e22c": "Extended Log",
    "cce0fa3f-b6bb-4e9b-b6e6-97af04042af3": "Detailed Log",
    "a5e4b1e5-4dfc-41e1-8e94-f8b13eb81cbf": "Full Log",
    "91a5e99e-4c50-4ad5-9996-2d5ace39b892": "Alert",
}


# ===========================================================================
# Main entry point
# ===========================================================================

def capture_policy_blueprint(client: Any, package_name: str = "Standard") -> dict:
    """Pull a full policy from a live SMS and return a deployable blueprint.

    Fetches the named policy package, all its access layers (including inline
    layers referenced by ``Apply Layer`` rules), and every object referenced
    in any rule.  Gateways and SMTP servers are pulled separately.

    Args:
        client:       Authenticated API client.
        package_name: Name of the policy package to capture.

    Returns:
        Blueprint dict matching the ``push-blueprint`` JSON format,
        or an empty dict if the package is not found.
    """
    log.info("=== CAPTURE: package='%s' ===", package_name)

    # uid -> full object dict (populated progressively)
    obj_reg: dict[str, dict] = {}

    # ------------------------------------------------------------------
    # 1. Package
    # ------------------------------------------------------------------
    pkg = client.run_command("show-package", {
        "name": package_name,
        "details-level": "full",
    })
    if "uid" not in pkg:
        log.error("Package '%s' not found: %s", package_name, pkg.get("message", pkg))
        return {}
    log.info("  Package uid: %s", pkg["uid"])

    # ------------------------------------------------------------------
    # 2. Access layers from package
    # ------------------------------------------------------------------
    layer_names = _extract_layer_names(pkg)
    log.info("  Access layers: %s", layer_names)

    # ------------------------------------------------------------------
    # 3. Fetch rulebase for each access layer
    # ------------------------------------------------------------------
    layer_rulebases: dict[str, list] = {}
    layer_settings_map: dict[str, dict] = {}
    inline_layer_names: set[str] = set()

    for lname in layer_names:
        log.info("  Fetching layer: %s", lname)
        ls = client.run_command("show-access-layer", {
            "name": lname, "details-level": "full",
        })
        layer_settings_map[lname] = ls

        items = _fetch_rulebase(client, lname, obj_reg)
        layer_rulebases[lname] = items
        log.info("    %d top-level items", len(items))

        for item in items:
            _collect_inline_layer_names(item, inline_layer_names)

    # ------------------------------------------------------------------
    # 4. Fetch inline layers discovered in the rulebase
    # ------------------------------------------------------------------
    inline_rulebases: dict[str, list] = {}
    inline_settings_map: dict[str, dict] = {}

    for il_key in inline_layer_names:
        log.info("  Fetching inline layer: %s", il_key)
        ils = client.run_command("show-access-layer", {
            "name": il_key, "details-level": "full",
        })
        inline_settings_map[il_key] = ils
        # Register the actual layer name so UID→name lookup works in rules
        actual_name = ils.get("name", il_key)
        obj_reg.setdefault(il_key, {})["name"] = actual_name
        obj_reg[il_key]["type"] = "access-layer"
        items = _fetch_rulebase(client, il_key, obj_reg)
        inline_rulebases[il_key] = items
        log.info("    %d items in inline layer '%s'", len(items), actual_name)

    # ------------------------------------------------------------------
    # 5. Pull gateways explicitly (may not be in rule references)
    # ------------------------------------------------------------------
    gw_res = client.run_command("show-simple-gateways", {
        "limit": 50, "details-level": "full",
    })
    gateways_raw = gw_res.get("objects", [])
    log.info("  Gateways: %d", len(gateways_raw))

    # ------------------------------------------------------------------
    # 6. Pull SMTP servers (management alerting / log forwarding)
    # ------------------------------------------------------------------
    smtp_res = client.run_command("show-smtp-servers", {
        "limit": 50, "details-level": "full",
    })
    smtp_servers_raw = smtp_res.get("objects", [])
    log.info("  SMTP servers: %d", len(smtp_servers_raw))

    # ------------------------------------------------------------------
    # 7. Classify all objects in the registry
    # ------------------------------------------------------------------
    classified = _classify_objects(obj_reg)
    total_objs = sum(len(v) for v in classified.values())
    log.info("  Classified objects: %d custom", total_objs)

    # ------------------------------------------------------------------
    # 7b. Resolve member UIDs for groups and service-groups that are not
    #     yet in obj_reg (group members only appear in the group, not in
    #     any rule directly, so the objects-dictionary may not include them).
    # ------------------------------------------------------------------
    missing_uids: set[str] = set()
    for gt in ("group", "service-group"):
        for obj in classified.get(gt, []):
            for m in obj.get("members", []):
                if isinstance(m, str) and m not in obj_reg:
                    missing_uids.add(m)
    if missing_uids:
        log.info("  Resolving %d group-member UIDs via show-object...", len(missing_uids))
        for uid in missing_uids:
            res = client.run_command("show-object", {"uid": uid, "details-level": "standard"})
            obj_data = res.get("object", {})
            if obj_data.get("uid"):
                obj_reg[obj_data["uid"]] = obj_data

    # ------------------------------------------------------------------
    # 8. Build and return the blueprint
    # ------------------------------------------------------------------
    blueprint = _build_blueprint(
        package_name=package_name,
        pkg=pkg,
        layer_names=layer_names,
        layer_settings_map=layer_settings_map,
        layer_rulebases=layer_rulebases,
        inline_layer_names=inline_layer_names,
        inline_settings_map=inline_settings_map,
        inline_rulebases=inline_rulebases,
        classified=classified,
        gateways_raw=gateways_raw,
        smtp_servers_raw=smtp_servers_raw,
        obj_reg=obj_reg,
    )
    log.info("=== CAPTURE COMPLETE ===")
    return blueprint


# ===========================================================================
# Rulebase fetch helpers
# ===========================================================================

def _extract_layer_names(pkg: dict) -> list[str]:
    """Extract access layer names from a ``show-package`` response."""
    raw = pkg.get("access-layers", [])
    if isinstance(raw, dict):
        raw = raw.get("objects", raw.get("add", []))
        if not isinstance(raw, list):
            raw = [raw] if isinstance(raw, dict) else []
    names: list[str] = []
    for layer in raw:
        if isinstance(layer, dict):
            n = layer.get("name") or layer.get("uid", "")
        else:
            n = str(layer)
        if n:
            names.append(n)
    return names


def _fetch_rulebase(client: Any, layer_name: str, obj_reg: dict) -> list:
    """Fetch all items in a layer rulebase (handles pagination).

    All inline objects found in rules are registered in ``obj_reg``.
    The ``objects-dictionary`` from each page supplements the registry.
    """
    items: list[dict] = []
    offset = 0
    page_size = 100

    while True:
        rb = client.run_command("show-access-rulebase", {
            "name": layer_name,
            "offset": offset,
            "limit": page_size,
            "details-level": "full",
            "use-object-dictionary": True,
        })

        # Register objects from the per-page dictionary
        for o in rb.get("objects-dictionary", []):
            uid = o.get("uid")
            if uid:
                obj_reg[uid] = o

        # Also walk each rule to register inline objects
        for item in rb.get("rulebase", []):
            _register_rule_objects(item, obj_reg)

        rulebase = rb.get("rulebase", [])
        items.extend(rulebase)

        total = rb.get("total", 0)
        offset += page_size
        if offset >= total or not rulebase:
            break

    return items


def _register_rule_objects(item: dict, obj_reg: dict) -> None:
    """Recursively register every object referenced in a rule or section."""
    for field in ("source", "destination", "service"):
        refs = item.get(field, [])
        if not isinstance(refs, list):
            refs = [refs]
        for ref in refs:
            if isinstance(ref, dict):
                uid = ref.get("uid")
                if uid:
                    obj_reg[uid] = ref

    # Action object
    action = item.get("action", {})
    if isinstance(action, dict):
        uid = action.get("uid")
        if uid:
            obj_reg[uid] = action

    # Inline layer
    il = item.get("inline-layer", {})
    if isinstance(il, dict):
        uid = il.get("uid")
        if uid:
            obj_reg[uid] = il

    # Recurse into nested section rulebase
    for rule in item.get("rulebase", []):
        _register_rule_objects(rule, obj_reg)


def _collect_inline_layer_names(item: dict, names: set) -> None:
    """Walk items and collect inline layer names from Apply Layer rules."""
    if item.get("type") == "access-rule":
        il = item.get("inline-layer")
        if isinstance(il, dict) and il.get("name"):
            names.add(il["name"])
        elif isinstance(il, str) and il:
            names.add(il)
    elif item.get("type") == "access-section":
        for rule in item.get("rulebase", []):
            _collect_inline_layer_names(rule, names)


# ===========================================================================
# Object resolution helpers
# ===========================================================================

def _is_builtin(obj: dict) -> bool:
    """Return True if *obj* is a Check Point built-in (not user-created)."""
    if not isinstance(obj, dict):
        return True
    name = obj.get("name", "").lower()
    if name in _ANY_NAMES or not name:
        return True
    domain = obj.get("domain", {})
    if isinstance(domain, dict):
        return domain.get("name", "") in _BUILTIN_DOMAINS
    return False


def _get_name(ref: Any, obj_reg: dict) -> str:
    """Return the object name from an inline dict or a UID string."""
    if isinstance(ref, dict):
        return ref.get("name", ref.get("uid", ""))
    if isinstance(ref, str):
        return obj_reg.get(ref, {}).get("name", ref)
    return ""


def _resolve_refs(refs: Any, obj_reg: dict) -> Any:
    """Resolve a list of object references to "any", a name, or a name list."""
    if isinstance(refs, str):
        return "any" if refs.lower() in _ANY_NAMES else refs

    if not isinstance(refs, list):
        refs = [refs] if refs else []

    names: list[str] = []
    for ref in refs:
        name = _get_name(ref, obj_reg)
        if name.lower() in _ANY_NAMES:
            return "any"
        if name:
            names.append(name)

    if not names:
        return "any"
    return names[0] if len(names) == 1 else names


def _get_action_name(rule: dict, obj_reg: dict) -> str:
    """Extract the action name from a raw rule dict.

    Handles both inline object dicts (``details-level: full``) and plain
    UID strings (when the API returns references without expanding them).
    Falls back to :data:`_WELLKNOWN_UIDS` for standard CP action UIDs.
    """
    action = rule.get("action", {})
    if isinstance(action, dict):
        name = action.get("name", "")
    elif isinstance(action, str):
        # UID string — resolve via registry then wellknown table
        name = obj_reg.get(action, {}).get("name") or _WELLKNOWN_UIDS.get(action, "")
    else:
        name = ""
    if "inner" in name.lower() or name.lower() == "apply layer":
        return "Apply Layer"
    return name if name else "Drop"


def _get_track_name(rule: dict, obj_reg: dict) -> str:
    """Extract the track type name from a raw rule dict.

    Handles both inline track dicts and plain UID strings.
    """
    track = rule.get("track", {})
    if isinstance(track, str):
        # UID string — resolve via registry then wellknown table
        return (obj_reg.get(track, {}).get("name")
                or _WELLKNOWN_UIDS.get(track, "Log"))
    if isinstance(track, dict):
        t = track.get("type", {})
        if isinstance(t, dict):
            name = t.get("name", "")
            if not name:
                tuid = t.get("uid", "")
                name = (obj_reg.get(tuid, {}).get("name")
                        or _WELLKNOWN_UIDS.get(tuid, "Log"))
            return name if name else "Log"
        if isinstance(t, str):
            return t
    return "Log"


def _get_inline_layer_name(rule: dict, obj_reg: dict) -> str | None:
    """Return the inline layer name for an Apply Layer rule."""
    il = rule.get("inline-layer")
    if not il:
        return None
    if isinstance(il, dict):
        return il.get("name") or None
    if isinstance(il, str):
        return obj_reg.get(il, {}).get("name", il)
    return None


def _rule_to_blueprint(rule: dict, obj_reg: dict,
                       *, is_inline_layer: bool = False) -> dict | None:
    """Convert a raw ``access-rule`` response dict to blueprint format.

    Returns ``None`` for the auto-generated default Cleanup rule (any/any/Drop)
    in the **main** network layer only.  Inside inline layers the user may
    intentionally place cleanup rules (e.g. Dynamic_AI_Layer), so they are
    always preserved.
    """
    if rule.get("type") != "access-rule":
        return None

    name = rule.get("name", "")
    src = _resolve_refs(rule.get("source", []), obj_reg)
    dst = _resolve_refs(rule.get("destination", []), obj_reg)

    action = _get_action_name(rule, obj_reg)
    track = _get_track_name(rule, obj_reg)

    # Skip the auto-generated CP cleanup rule in the MAIN layer only:
    # name="Cleanup rule", any->any, Drop, track=None.
    # Inside inline layers these rules are intentional — keep them.
    if (not is_inline_layer
            and name == "Cleanup rule" and src == "any" and dst == "any"
            and action == "Drop" and track.lower() in ("none", "")):
        return None

    bp: dict = {
        "name": name,
        "source": src,
        "destination": dst,
        "service": _resolve_refs(rule.get("service", []), obj_reg),
        "action": action,
        "track": track,
    }

    if action == "Apply Layer":
        il_name = _get_inline_layer_name(rule, obj_reg)
        if il_name:
            bp["inline-layer"] = il_name

    comments = rule.get("comments", "")
    if comments:
        bp["comments"] = comments

    if not rule.get("enabled", True):
        bp["enabled"] = False

    if rule.get("ignore-errors"):
        bp["ignore-errors"] = True

    return bp


# ===========================================================================
# Object classification
# ===========================================================================

def _classify_objects(obj_reg: dict) -> dict:
    """Group all registered objects by their API type (custom objects only).

    Excludes built-in Check Point objects (domain = ``"Check Point Data"``
    etc.) and deduplicates by (type, name).
    """
    classified: dict[str, list] = {
        "host": [],
        "network": [],
        "group": [],
        "address-range": [],
        "network-feed": [],
        "service-tcp": [],
        "service-udp": [],
        "service-icmp": [],
        "service-icmp6": [],
        "service-other": [],
        "service-sctp": [],
        "service-group": [],
    }

    seen: set[tuple] = set()

    for uid, obj in obj_reg.items():
        if _is_builtin(obj):
            continue
        obj_type = obj.get("type", "")
        name = obj.get("name", "")
        if not name or not obj_type or obj_type not in classified:
            continue
        key = (obj_type, name)
        if key in seen:
            continue
        seen.add(key)
        classified[obj_type].append(obj)

    return classified


# ===========================================================================
# Blueprint assembly
# ===========================================================================

def _build_blueprint(
    package_name: str,
    pkg: dict,
    layer_names: list,
    layer_settings_map: dict,
    layer_rulebases: dict,
    inline_layer_names: set,
    inline_settings_map: dict,
    inline_rulebases: dict,
    classified: dict,
    gateways_raw: list,
    smtp_servers_raw: list,
    obj_reg: dict,
) -> dict:
    """Assemble all captured data into the push-blueprint JSON structure."""

    # --- topology.hosts ---
    hosts = []
    for h in classified["host"]:
        bp: dict = {
            "name": h.get("name", ""),
            "ipv4-address": h.get("ipv4-address", ""),
        }
        if h.get("ipv6-address"):
            bp["ipv6-address"] = h["ipv6-address"]
        for f in ("color", "comments"):
            if h.get(f):
                bp[f] = h[f]
        nat = h.get("nat-settings", {})
        if isinstance(nat, dict) and nat.get("auto-rule"):
            bp["nat-settings"] = {
                "auto-rule": nat["auto-rule"],
                "method": nat.get("method", "static"),
            }
            if nat.get("ipv4-address"):
                bp["nat-settings"]["ipv4-address"] = nat["ipv4-address"]
        hosts.append(bp)

    # --- topology.networks ---
    networks = []
    for n in classified["network"]:
        bp = {
            "name": n.get("name", ""),
            "subnet4": n.get("subnet4", n.get("subnet", "")),
            "mask-length4": n.get("mask-length4", n.get("mask-length", 24)),
        }
        for f in ("color", "comments"):
            if n.get(f):
                bp[f] = n[f]
        networks.append(bp)

    # --- topology.groups ---
    groups = []
    for g in classified["group"]:
        members = [_get_name(m, obj_reg) for m in g.get("members", [])
                   if _get_name(m, obj_reg)]
        bp = {"name": g.get("name", ""), "members": members}
        for f in ("color", "comments"):
            if g.get(f):
                bp[f] = g[f]
        groups.append(bp)

    # --- topology.network-feeds ---
    feeds = []
    for f in classified["network-feed"]:
        bp = {
            "name": f.get("name", ""),
            "feed-url": f.get("feed-url", ""),
            "feed-format": f.get("feed-format", "Flat List"),
            "feed-type": f.get("feed-type", "IP Address"),
        }
        for field in ("color", "comments"):
            if f.get(field):
                bp[field] = f[field]
        feeds.append(bp)

    # --- topology.gateways ---
    gateways = []
    for gw in gateways_raw:
        if _is_builtin(gw):
            continue
        ifaces = []
        for iface in gw.get("interfaces", []):
            ibp: dict = {
                "name": iface.get("name", ""),
                "ipv4-address": iface.get("ipv4-address", ""),
                "ipv4-network-mask": iface.get("ipv4-network-mask", "255.255.255.0"),
                "topology": iface.get("topology", "internal"),
            }
            if iface.get("anti-spoofing"):
                ibp["anti-spoofing"] = True
            ifaces.append(ibp)

        gwbp: dict = {
            "name": gw.get("name", ""),
            "ipv4-address": gw.get("ipv4-address", ""),
        }
        for f in ("color", "comments"):
            if gw.get(f):
                gwbp[f] = gw[f]
        for blade in ("firewall", "vpn", "application-control", "url-filtering",
                      "content-awareness", "ips", "anti-bot", "anti-virus"):
            if blade in gw:
                gwbp[blade] = gw[blade]
        if ifaces:
            gwbp["interfaces"] = ifaces
        gateways.append(gwbp)

    # --- services.individual ---
    svc_individual: list[dict] = []
    for svc_type in ("service-tcp", "service-udp", "service-icmp",
                     "service-icmp6", "service-other", "service-sctp"):
        for svc in classified.get(svc_type, []):
            bp = {"name": svc.get("name", ""), "type": svc_type}
            for f in ("port", "source-port", "protocol", "icmp-type", "icmp-code",
                      "color", "comments", "match-for-any", "aggressive-aging"):
                if svc.get(f) is not None:
                    bp[f] = svc[f]
            svc_individual.append(bp)

    # --- services.groups ---
    svc_groups: list[dict] = []
    for sg in classified.get("service-group", []):
        members = [_get_name(m, obj_reg) for m in sg.get("members", [])
                   if _get_name(m, obj_reg)]
        bp = {"name": sg.get("name", ""), "members": members}
        for f in ("color", "comments"):
            if sg.get(f):
                bp[f] = sg[f]
        svc_groups.append(bp)

    # --- management.smtp-servers ---
    smtp_servers: list[dict] = []
    for smtp in smtp_servers_raw:
        if _is_builtin(smtp):
            continue
        bp = {"name": smtp.get("name", "")}
        for f in ("server", "port", "authentication", "encryption",
                  "sender", "color", "comments"):
            if smtp.get(f) is not None:
                bp[f] = smtp[f]
        smtp_servers.append(bp)

    # --- policy.package ---
    pkg_settings = {
        "name": package_name,
        "access": pkg.get("access", True),
        "threat-prevention": pkg.get("threat-prevention", False),
        "comments": pkg.get("comments",
                            "Policy captured by CP API QA Tool"),
    }

    # --- policy.layer-settings ---
    layer_settings: dict = {}
    if layer_names:
        ls = layer_settings_map.get(layer_names[0], {})
        if ls.get("applications-and-url-filtering"):
            layer_settings["applications-and-url-filtering"] = True
        if ls.get("mobile-access"):
            layer_settings["mobile-access"] = True

    # --- policy.inline-layers ---
    inline_layers: list[dict] = []
    for il_key in sorted(inline_layer_names):
        ils = inline_settings_map.get(il_key, {})
        il_items = inline_rulebases.get(il_key, [])
        # Use the actual human-readable name, not a UID key
        actual_il_name = ils.get("name", il_key)

        il_rules: list[dict] = []
        for item in il_items:
            if item.get("type") == "access-rule":
                r = _rule_to_blueprint(item, obj_reg, is_inline_layer=True)
                if r:
                    il_rules.append(r)
            elif item.get("type") == "access-section":
                for rule in item.get("rulebase", []):
                    if rule.get("type") == "access-rule":
                        r = _rule_to_blueprint(rule, obj_reg,
                                               is_inline_layer=True)
                        if r:
                            il_rules.append(r)

        il_bp: dict = {"name": actual_il_name}
        if ils.get("implicit-cleanup-action"):
            il_bp["implicit-cleanup-action"] = ils["implicit-cleanup-action"]
        il_bp["add-default-rule"] = ils.get("add-default-rule", False)
        if ils.get("color"):
            il_bp["color"] = ils["color"]
        if ils.get("comments"):
            il_bp["comments"] = ils["comments"]
        il_bp["rules"] = il_rules
        inline_layers.append(il_bp)

    # --- policy.network-layer ---
    net_layer_name = layer_names[0] if layer_names else f"{package_name} Network"
    sections: list[dict] = []

    for item in layer_rulebases.get(net_layer_name, []):
        if item.get("type") == "access-section":
            s_rules: list[dict] = []
            for rule in item.get("rulebase", []):
                if rule.get("type") == "access-rule":
                    r = _rule_to_blueprint(rule, obj_reg)
                    if r:
                        s_rules.append(r)
            sections.append({
                "section": item.get("name", ""),
                "rules": s_rules,
            })
        elif item.get("type") == "access-rule":
            # Rule outside any section — append to a synthetic empty section
            r = _rule_to_blueprint(item, obj_reg)
            if r:
                if not sections or sections[-1].get("section") != "":
                    sections.append({"section": "", "rules": []})
                sections[-1]["rules"].append(r)

    # --- Assemble ---
    blueprint: dict = {
        "_meta": {
            "description": f"Policy blueprint captured from package '{package_name}'",
            "captured": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "server_compatibility": "R81.10+ (API v2.0.1+)",
            "note": (
                "Generated by CP API QA Tool capture-blueprint. "
                "Built-in Check Point objects are excluded — they already "
                "exist on any SMS. SMS checkpoint-host is not recreated."
            ),
        },
        "topology": {
            "hosts": hosts,
            "networks": networks,
            "groups": groups,
            "network-feeds": feeds,
            "gateways": gateways,
        },
        "services": {
            "individual": svc_individual,
            "groups": svc_groups,
        },
        "policy": {
            "package": pkg_settings,
            "layer-settings": layer_settings,
            "inline-layers": inline_layers,
            "network-layer": {
                "name": net_layer_name,
                "sections": sections,
            },
        },
    }

    if smtp_servers:
        blueprint["management"] = {"smtp-servers": smtp_servers}

    return blueprint
