"""Demo mode operations: create, cleanup, topology, services, and policy.

Demo mode creates a realistic lab topology based on the Ansible Dynamic
Policy Demo project — hosts, networks, groups, feeds, services, and a
multi-layer access policy.  Everything is tracked in a manifest file for
later cleanup.

Usage (via CLI)::

    cp-qa -m 10.0.0.1 -u admin --mode demo --action create
    cp-qa -m 10.0.0.1 -u admin --mode demo --action cleanup
"""

from __future__ import annotations

import random
import time as _time
from typing import Any

from cp_qa.constants import (
    CLEANUP_ORDER,
    DISCOVERABLE_PREFIXES,
    DISCOVERABLE_TYPES,
    MAX_RETRIES,
)
from cp_qa.engine.autofix import auto_fix_payload
from cp_qa.engine.params import extract_params_from_obj
from cp_qa.engine.payloads import generate_payloads
from cp_qa.engine.spec import get_object_by_name
from cp_qa.engine.type_defaults import apply_type_defaults
from cp_qa.logging import get_logger

log = get_logger(__name__)


# =========================================================================
# Demo create
# =========================================================================

def run_demo_create(
    client: Any,
    spec: dict,
    obj_type: str,
    add_cmd_spec: dict,
) -> list[dict]:
    """Create one representative object for demo purposes (ADD only).

    Uses the same adaptive self-healing as the QA lifecycle but only
    performs the ADD step.

    Args:
        client:       Authenticated API client.
        spec:         Parsed API specification.
        obj_type:     Object type to create (e.g. ``"host"``).
        add_cmd_spec: Command spec dict for ``add-<type>``.

    Returns:
        List of manifest entries:
        ``[{"type": str, "name": str, "uid": str, "payload": dict}]``
    """
    current_obj_type = obj_type
    log.info("--- DEMO CREATE: %s ---", obj_type)

    # Pre-create helper objects if needed
    helper_group, helper_except_group, helper_time = _create_demo_helpers(
        client, obj_type
    )

    request_obj_name = add_cmd_spec.get("request")
    obj_def = get_object_by_name(spec, request_obj_name)
    if not obj_def:
        log.warning(
            "Could not find request object definition for %s: %s",
            obj_type,
            request_obj_name,
        )
        return []

    parameters = extract_params_from_obj(obj_def)
    payload_variants = generate_payloads(
        parameters, current_obj_type=current_obj_type, spec=spec
    )
    master_payload = payload_variants[0]

    # Deterministic demo name
    demo_name = _make_demo_name(obj_type)
    master_payload["name"] = demo_name

    # Apply type-specific defaults
    apply_type_defaults(
        obj_type, master_payload, spec=spec, current_obj_type=current_obj_type
    )

    # Inject helpers
    _inject_demo_helpers(
        master_payload,
        obj_type,
        helper_group,
        helper_except_group,
        helper_time,
    )

    # === Adaptive ADD with self-healing ===
    success, add_res = _adaptive_demo_add(
        client, obj_type, master_payload, parameters
    )

    manifest_entries: list[dict] = []

    if success:
        uid = add_res.get("uid", "")
        log.info("  PASS Created %s (uid: %s)", demo_name, uid)
        manifest_entries.append(
            {
                "type": obj_type,
                "name": demo_name,
                "uid": uid,
                "payload": dict(master_payload),
            }
        )
    else:
        log.error(
            "  FAIL Failed to create %s: %s",
            demo_name,
            add_res.get("message", add_res),
        )

    # Track helper objects in the manifest for cleanup
    if helper_group:
        manifest_entries.append(
            {"type": "group", "name": helper_group, "uid": "", "payload": {}}
        )
    if helper_except_group:
        manifest_entries.append(
            {"type": "group", "name": helper_except_group, "uid": "", "payload": {}}
        )
    if helper_time:
        manifest_entries.append(
            {"type": "time", "name": helper_time, "uid": "", "payload": {}}
        )

    return manifest_entries


# =========================================================================
# Demo cleanup
# =========================================================================

def run_demo_cleanup(client: Any, manifest: list[dict]) -> dict:
    """Delete all objects in *manifest* in reverse dependency order.

    Args:
        client:   Authenticated API client.
        manifest: List of ``{"type": str, "name": str, ...}`` dicts.

    Returns:
        ``{"deleted": int, "failed": int}``
    """
    log.info("--- DEMO CLEANUP: %d objects to delete ---", len(manifest))

    by_type: dict[str, list[dict]] = {}
    for entry in manifest:
        by_type.setdefault(entry["type"], []).append(entry)

    deleted = 0
    failed = 0
    batch_count = 0
    first_batch = {"package", "service-group", "service-tcp", "service-udp", "service-icmp"}

    # Delete in dependency order
    for obj_type in CLEANUP_ORDER:
        if obj_type not in by_type:
            continue
        for entry in by_type[obj_type]:
            name = entry["name"]
            log.info("  Deleting %s: %s...", obj_type, name)
            res = client.run_command(
                f"delete-{obj_type}",
                {"name": name, "ignore-warnings": True, "ignore-errors": True},
            )
            ok = (
                "uid" in res
                or res.get("code") == "success"
                or res.get("message") == "OK"
            )
            if ok:
                log.info("    PASS Deleted %s", name)
                deleted += 1
                batch_count += 1
            else:
                log.warning(
                    "    FAIL Failed to delete %s: %s",
                    name,
                    res.get("message", res),
                )
                failed += 1

        # Publish after the first batch (policy + services)
        if obj_type in first_batch and batch_count > 0:
            remaining_first = [
                t
                for t in CLEANUP_ORDER
                if t in first_batch
                and t in by_type
                and CLEANUP_ORDER.index(t) > CLEANUP_ORDER.index(obj_type)
            ]
            if not remaining_first:
                log.info(
                    "  Publishing batch (policy + services: %d deletions)...",
                    batch_count,
                )
                client.publish()
                batch_count = 0

    # Safety net: handle types not in CLEANUP_ORDER
    for obj_type, entries in by_type.items():
        if obj_type in CLEANUP_ORDER:
            continue
        for entry in entries:
            name = entry["name"]
            log.info("  Deleting (unordered) %s: %s...", obj_type, name)
            res = client.run_command(
                f"delete-{obj_type}",
                {"name": name, "ignore-warnings": True, "ignore-errors": True},
            )
            ok = (
                "uid" in res
                or res.get("code") == "success"
                or res.get("message") == "OK"
            )
            if ok:
                deleted += 1
            else:
                failed += 1

    log.info("DEMO CLEANUP complete: %d deleted, %d failed", deleted, failed)
    return {"deleted": deleted, "failed": failed}


# =========================================================================
# Server-side discovery
# =========================================================================

def discover_demo_objects(client: Any) -> list[dict]:
    """Sweep the server for all objects matching known prefixes.

    Queries every type in :data:`DISCOVERABLE_TYPES` with each prefix
    in :data:`DISCOVERABLE_PREFIXES`.  Returns a manifest-compatible
    list so discovered objects can be fed directly into
    :func:`run_demo_cleanup`.

    Args:
        client: Authenticated API client.

    Returns:
        List of ``{"type": str, "name": str, "uid": str}`` dicts,
        ordered to match :data:`DISCOVERABLE_TYPES` (dependency-safe).
    """
    found: list[dict] = []
    seen: set[str] = set()  # (type, name) dedup

    for plural, singular in DISCOVERABLE_TYPES:
        show_cmd = f"show-{plural}"
        for prefix in DISCOVERABLE_PREFIXES:
            res = client.run_command(show_cmd, {"limit": 50, "filter": prefix})

            # show-<type>s returns "objects"; show-packages returns "packages"
            items = res.get("objects", res.get("packages", []))
            if not isinstance(items, list):
                continue

            for obj in items:
                name = obj.get("name", "")
                uid = obj.get("uid", "")
                if not name.startswith(prefix):
                    continue
                key = (singular, name)
                if key in seen:
                    continue
                seen.add(key)
                found.append({"type": singular, "name": name, "uid": uid})
                log.debug("  Discovered %s: %s", singular, name)

    log.info("Server-side discovery found %d objects", len(found))
    return found


# =========================================================================
# Demo services
# =========================================================================

def create_demo_topology(client: Any) -> list[dict]:
    """Create realistic network topology objects for the demo environment.

    Based on the Dynamic Policy Demo Ansible project — creates hosts,
    networks, groups, network feeds, and a gateway that form a coherent
    lab topology.

    Args:
        client: Authenticated API client.

    Returns:
        List of manifest entries for all created topology objects.
    """
    log.info("--- DEMO: Creating network topology ---")
    manifest_entries: list[dict] = []

    # --- Hosts (SMS is a pre-existing checkpoint-host, not created here) ---
    hosts = [
        {
            "cmd": "add-host",
            "type": "host",
            "payload": {
                "name": "DNS_8_8_4_4",
                "ipv4-address": "8.8.4.4",
                "color": "blue",
                "comments": "Google Public DNS (secondary)",
                "ignore-warnings": True,
            },
        },
        {
            "cmd": "add-host",
            "type": "host",
            "payload": {
                "name": "DNS_8_8_8_8",
                "ipv4-address": "8.8.8.8",
                "color": "blue",
                "comments": "Google Public DNS (primary)",
                "ignore-warnings": True,
            },
        },
        {
            "cmd": "add-host",
            "type": "host",
            "payload": {
                "name": "jump_host",
                "ipv4-address": "10.1.1.200",
                "color": "green",
                "comments": "Management jump host",
                "ignore-warnings": True,
            },
        },
        {
            "cmd": "add-host",
            "type": "host",
            "payload": {
                "name": "kali_linux",
                "ipv4-address": "203.0.113.5",
                "color": "red",
                "comments": "External pentesting host",
                "ignore-warnings": True,
            },
        },
        {
            "cmd": "add-host",
            "type": "host",
            "payload": {
                "name": "win_client",
                "ipv4-address": "10.1.1.222",
                "color": "cyan",
                "comments": "Windows workstation (static NAT to 203.0.113.222)",
                "nat-settings": {
                    "auto-rule": True,
                    "method": "static",
                    "ipv4-address": "203.0.113.222",
                },
                "ignore-warnings": True,
            },
        },
        {
            "cmd": "add-host",
            "type": "host",
            "payload": {
                "name": "win_server",
                "ipv4-address": "10.1.2.250",
                "color": "orange",
                "comments": "Windows server in DMZ (static NAT to 203.0.113.250)",
                "nat-settings": {
                    "auto-rule": True,
                    "method": "static",
                    "ipv4-address": "203.0.113.250",
                },
                "ignore-warnings": True,
            },
        },
    ]

    for obj in hosts:
        manifest_entries.extend(_add_demo_object(client, obj))

    log.info("  Publishing hosts...")
    client.publish()

    # --- Networks ---
    networks = [
        {
            "cmd": "add-network",
            "type": "network",
            "payload": {
                "name": "net_10_1_1_0_24",
                "subnet4": "10.1.1.0",
                "mask-length4": 24,
                "color": "forest green",
                "comments": "LAN — Users (10.1.1.0/24)",
                "ignore-warnings": True,
                "ignore-errors": True,
            },
        },
        {
            "cmd": "add-network",
            "type": "network",
            "payload": {
                "name": "net_10_1_2_0_24",
                "subnet4": "10.1.2.0",
                "mask-length4": 24,
                "color": "dark green",
                "comments": "DMZ — Servers (10.1.2.0/24)",
                "ignore-warnings": True,
                "ignore-errors": True,
            },
        },
        {
            "cmd": "add-network",
            "type": "network",
            "payload": {
                "name": "net_10_1_3_0_24",
                "subnet4": "10.1.3.0",
                "mask-length4": 24,
                "color": "sea green",
                "comments": "Management Network (10.1.3.0/24)",
                "ignore-warnings": True,
                "ignore-errors": True,
            },
        },
        {
            "cmd": "add-network",
            "type": "network",
            "payload": {
                "name": "net_10_1_4_0_24",
                "subnet4": "10.1.4.0",
                "mask-length4": 24,
                "color": "olive",
                "comments": "IoT / Guest Network (10.1.4.0/24)",
                "ignore-warnings": True,
                "ignore-errors": True,
            },
        },
        {
            "cmd": "add-network",
            "type": "network",
            "payload": {
                "name": "net_203_0_113_0_24",
                "subnet4": "203.0.113.0",
                "mask-length4": 24,
                "color": "red",
                "comments": "External / WAN (203.0.113.0/24)",
                "ignore-warnings": True,
                "ignore-errors": True,
            },
        },
    ]

    for obj in networks:
        manifest_entries.extend(_add_demo_object(client, obj))

    log.info("  Publishing networks...")
    client.publish()

    # --- Group ---
    grp = {
        "cmd": "add-group",
        "type": "group",
        "payload": {
            "name": "internal_nets",
            "members": [
                "net_10_1_1_0_24",
                "net_10_1_2_0_24",
                "net_10_1_3_0_24",
                "net_10_1_4_0_24",
            ],
            "color": "forest green",
            "comments": "All internal networks",
            "ignore-warnings": True,
        },
    }
    manifest_entries.extend(_add_demo_object(client, grp))

    # --- Network Feeds ---
    feeds = [
        {
            "cmd": "add-network-feed",
            "type": "network-feed",
            "payload": {
                "name": "internal_DNS_feed_json",
                "feed-url": "http://10.1.1.200:5000/get-json",
                "feed-format": "JSON",
                "feed-type": "IP Address",
                "color": "blue",
                "comments": "Internal DNS server addresses (JSON feed from jump_host)",
                "ignore-warnings": True,
                "ignore-errors": True,
            },
        },
        {
            "cmd": "add-network-feed",
            "type": "network-feed",
            "payload": {
                "name": "public_DNS_feed_list",
                "feed-url": "http://10.1.1.200:5000/get-list",
                "feed-format": "Flat List",
                "feed-type": "IP Address",
                "color": "blue",
                "comments": "Public DNS resolvers",
                "ignore-warnings": True,
                "ignore-errors": True,
            },
        },
        {
            "cmd": "add-network-feed",
            "type": "network-feed",
            "payload": {
                "name": "attackers_feed_list",
                "feed-url": "http://10.1.1.200:5000/get-attacker",
                "feed-format": "Flat List",
                "feed-type": "IP Address",
                "color": "red",
                "comments": "Known attacker IPs",
                "ignore-warnings": True,
                "ignore-errors": True,
            },
        },
        {
            "cmd": "add-network-feed",
            "type": "network-feed",
            "payload": {
                "name": "targets_feed_list",
                "feed-url": "http://10.1.1.200:5000/get-target",
                "feed-format": "Flat List",
                "feed-type": "IP Address",
                "color": "orange",
                "comments": "Protected target IPs",
                "ignore-warnings": True,
                "ignore-errors": True,
            },
        },
    ]

    for obj in feeds:
        manifest_entries.extend(_add_demo_object(client, obj))

    # --- Gateway ---
    gw = {
        "cmd": "add-simple-gateway",
        "type": "simple-gateway",
        "payload": {
            "name": "GW",
            "ipv4-address": "10.1.1.81",
            "color": "dark blue",
            "comments": "Perimeter gateway",
            "firewall": True,
            "vpn": True,
            "application-control": True,
            "url-filtering": True,
            "interfaces": [
                {"name": "eth0", "ipv4-address": "10.1.1.81", "ipv4-network-mask": "255.255.255.0", "topology": "internal", "anti-spoofing": True},
                {"name": "eth1", "ipv4-address": "10.1.2.81", "ipv4-network-mask": "255.255.255.0", "topology": "internal", "anti-spoofing": True},
                {"name": "eth2", "ipv4-address": "10.1.3.81", "ipv4-network-mask": "255.255.255.0", "topology": "internal", "anti-spoofing": True},
                {"name": "eth3", "ipv4-address": "10.1.4.81", "ipv4-network-mask": "255.255.255.0", "topology": "internal", "anti-spoofing": True},
                {"name": "eth4", "ipv4-address": "203.0.113.81", "ipv4-network-mask": "255.255.255.0", "topology": "external", "anti-spoofing": True},
            ],
            "ignore-warnings": True,
            "ignore-errors": True,
        },
    }
    manifest_entries.extend(_add_demo_object(client, gw))

    log.info("  Publishing topology...")
    client.publish()

    created = len([e for e in manifest_entries if e.get("uid")])
    log.info("Topology complete: %d objects created", created)
    return manifest_entries


def create_demo_services(client: Any) -> list[dict]:
    """Create service objects for the demo policy.

    Creates individual TCP/UDP/ICMP services and service groups that
    mirror the Ansible Dynamic Policy Demo topology.

    Args:
        client: Authenticated API client.

    Returns:
        List of manifest entries for created services.
    """
    log.info("--- DEMO: Creating service objects ---")

    # Only one custom service — everything else uses built-in CP services
    services = [
        {
            "cmd": "add-service-tcp",
            "type": "service-tcp",
            "payload": {
                "name": "LDAP_TCP_135",
                "port": "135",
                "comments": "LDAP / RPC Endpoint Mapper",
                "color": "purple",
                "ignore-warnings": True,
            },
        },
    ]

    manifest_entries: list[dict] = []
    for svc in services:
        manifest_entries.extend(_add_demo_object(client, svc))

    # Service groups — mix of custom service and built-in CP services
    groups = [
        {
            "cmd": "add-service-group",
            "type": "service-group",
            "payload": {
                "name": "LDAP_all",
                "members": [
                    "ldap",
                    "ldap-ssl",
                    "ldap_udp",
                    "microsoft-ds",
                    "microsoft-ds-udp",
                    "Kerberos_v5_TCP",
                    "Kerberos_v5_UDP",
                    "LDAP_TCP_135",
                ],
                "comments": "LDAP + Kerberos + RPC services",
                "color": "purple",
                "ignore-warnings": True,
                "ignore-errors": True,
            },
        },
        {
            "cmd": "add-service-group",
            "type": "service-group",
            "payload": {
                "name": "mail_services",
                "members": [
                    "pop-2",
                    "pop-3",
                    "POP3S",
                    "imap",
                    "IMAP-SSL",
                    "smtp",
                    "SMTPS",
                ],
                "comments": "Mail services (POP + IMAP + SMTP)",
                "color": "yellow",
                "ignore-warnings": True,
                "ignore-errors": True,
            },
        },
    ]

    for grp in groups:
        manifest_entries.extend(_add_demo_object(client, grp))

    log.info("Services created: %d", len(manifest_entries))
    return manifest_entries


# =========================================================================
# Demo policy
# =========================================================================

def create_demo_policy(client: Any, manifest: list[dict]) -> list[dict]:
    """Create a realistic security policy based on the Ansible Dynamic Policy Demo.

    Creates a policy package with:
    - Network layer with 5 sections and 10 rules
    - Inline DNS layer with 3 rules
    All rules reference the topology objects created by
    :func:`create_demo_topology` and :func:`create_demo_services`.

    Args:
        client:   Authenticated API client.
        manifest: Current manifest (unused — objects are referenced by name).

    Returns:
        List of manifest entries for the policy package.
    """
    log.info("--- DEMO: Creating security policy ---")

    # --- Package (with retry for transient server errors) ---


    # --- Create or find existing package (try show-package first) ---
    pkg_name = "Standard"
    pkg_created = False
    res: dict = {}

    # Check if package already exists
    res = client.run_command("show-package", {
        "name": pkg_name, "details-level": "full",
    })
    if "uid" in res:
        log.info("  Using existing package: %s", pkg_name)
    else:
        for attempt in range(3):
            res = client.run_command(
                "add-package",
                {
                    "name": pkg_name,
                    "comments": "Training Lab Policy — configured by CP API QA Tool",
                    "access": True,
                    "threat-prevention": False,
                    "ignore-warnings": True,
                },
            )
            if "uid" in res:
                pkg_created = True
                break
            msg = str(res.get("message", ""))
            transient = any(
                t in msg.lower()
                for t in ("failed to execute", "rev_constraint", "null pointer",
                           "eclipselink", "invocationtargetexception")
            )
            if transient and attempt < 2:
                log.warning("  RETRY package (attempt %d): %s", attempt + 1, msg)
                _time.sleep(5)
                continue
            break

    if "uid" not in res:
        log.error(
            "Failed to create/find policy package: %s", res.get("message", res)
        )
        return []

    if pkg_created:
        log.info("  PASS Policy package created: %s", pkg_name)

    # Extract the Network access layer name
    access_layers = res.get("access-layers", [])
    if isinstance(access_layers, dict):
        access_layers = access_layers.get("add", access_layers.get("objects", []))
        if not isinstance(access_layers, list):
            access_layers = [access_layers] if isinstance(access_layers, dict) else []
    layer_name = None
    if isinstance(access_layers, list) and access_layers:
        first = access_layers[0]
        layer_name = first.get("name") if isinstance(first, dict) else None
    if not layer_name:
        for candidate in [f"{pkg_name} Network", "Network", pkg_name]:
            check = client.run_command("show-access-layer", {"name": candidate})
            if "uid" in check:
                layer_name = candidate
                break
        if not layer_name:
            layer_name = f"{pkg_name} Network"
    log.info("  Using access layer: %s", layer_name)

    manifest_entries: list[dict] = []
    if pkg_created:
        manifest_entries.append(
            {"type": "package", "name": pkg_name, "uid": res["uid"], "payload": {}}
        )

    # Publish package first (separate session avoids rev_constraint DB error)
    client.publish()

    # Enable Application Control + URL Filtering on the access layer
    set_res = client.run_command("set-access-layer", {
        "name": layer_name,
        "applications-and-url-filtering": True,
        "ignore-warnings": True,
    })
    if "uid" in set_res:
        log.info("  Layer settings: applications-and-url-filtering enabled")
    else:
        log.warning("  Could not enable AppControl+URLFiltering: %s", set_res.get("message", ""))
    client.publish()

    # Delete the default "Cleanup rule" that Check Point auto-creates at
    # position 1 (Drop/Any/Any, Track: None).  If left in place it blocks
    # all traffic before our custom rules are evaluated.
    log.info("  Removing default Cleanup rule from %s...", layer_name)
    try:
        rb = client.run_command("show-access-rulebase", {
            "name": layer_name, "limit": 10, "use-object-dictionary": False,
        })
        for obj in rb.get("rulebase", []):
            if obj.get("type") == "access-rule" and obj.get("name") == "Cleanup rule":
                client.run_command("delete-access-rule", {
                    "uid": obj["uid"], "layer": layer_name,
                })
                log.info("    Deleted default Cleanup rule (uid: %s)", obj["uid"])
                break
        client.publish()
    except Exception as exc:
        log.warning("  Could not remove default Cleanup rule: %s", exc)

    # --- Inline DNS Layer (after publish, with retry) ---
    dns_layer_name = "DNS_Layer"
    dns_layer_ok = False
    for attempt in range(3):
        res = client.run_command(
            "add-access-layer",
            {
                "name": dns_layer_name,
                "add-default-rule": False,
                "implicit-cleanup-action": "drop",
                "comments": "Inline DNS inspection layer",
                "color": "blue",
                "ignore-warnings": True,
            },
        )
        if "uid" in res:
            log.info("  PASS Inline layer: %s", dns_layer_name)
            manifest_entries.append(
                {"type": "access-layer", "name": dns_layer_name, "uid": res["uid"], "payload": {}}
            )
            dns_layer_ok = True
            break
        msg = str(res.get("message", ""))
        if attempt < 2:
            log.warning("  RETRY DNS layer (attempt %d): %s", attempt + 1, msg)
            _time.sleep(3)
            continue
        log.error("  FAIL Inline layer %s: %s", dns_layer_name, msg)

    client.publish()

    # --- DNS Layer rules ---
    dns_rules = [
        {
            "name": "Internal DNS Server",
            "layer": dns_layer_name,
            "position": "top",
            "source": ["net_203_0_113_0_24", "internal_nets"],
            "destination": "internal_DNS_feed_json",
            "service": "any",
            "action": "Accept",
            "track": {"type": "Log"},
            "comments": "Allow specified networks to reach internal DNS servers",
        },
        {
            "name": "Public DNS Servers",
            "layer": dns_layer_name,
            "position": "bottom",
            "source": ["win_client", "GW", "SMS", "win_server"],
            "destination": "public_DNS_feed_list",
            "service": "any",
            "action": "Accept",
            "track": {"type": "Log"},
            "comments": "Allow specified hosts to reach public DNS resolvers",
        },
        {
            "name": "DNS log and drop",
            "layer": dns_layer_name,
            "position": "bottom",
            "source": "any",
            "destination": "any",
            "service": "any",
            "action": "Drop",
            "track": {"type": "Log"},
            "comments": "Drop and log all other DNS traffic",
        },
    ]

    if dns_layer_ok:
        dns_created = _add_rules(client, dns_rules, "DNS Layer")
    else:
        dns_created = 0
        log.warning("  Skipping DNS rules — layer creation failed")
    client.publish()

    # --- Network Layer: sections + rules (all use position: bottom) ---
    net_items: list[dict] = [
        # ── Section: Management ──
        {
            "_section": True,
            "name": "Management",
            "layer": layer_name,
            "position": "bottom",
        },
        {
            "name": "Sillent Drop",
            "layer": layer_name,
            "position": "bottom",
            "source": "any",
            "destination": "any",
            "service": ["bootp", "NBT", "nbsession", "nbname", "nbdatagram"],
            "action": "Drop",
            "track": {"type": "None"},
            "comments": "Silently drop noisy broadcast traffic",
        },
        {
            "name": "CP Updates",
            "layer": layer_name,
            "position": "bottom",
            "source": ["GW", "SMS"],
            "destination": "any",
            "service": ["http", "https", "HTTP_and_HTTPS_proxy"],
            "action": "Accept",
            "track": {"type": "Log"},
            "comments": "Allow gateway and SMS to fetch updates",
        },
        {
            "name": "Management",
            "layer": layer_name,
            "position": "bottom",
            "source": ["jump_host", "win_client", "SMS", "GW"],
            "destination": ["GW", "SMS"],
            "service": ["ssh_version_2", "https"],
            "action": "Accept",
            "track": {"type": "Log"},
            "comments": "Allow management access to gateway and SMS",
        },
        {
            "name": "Stealth Rule",
            "layer": layer_name,
            "position": "bottom",
            "source": "any",
            "destination": "GW",
            "service": "any",
            "action": "Drop",
            "track": {"type": "Log"},
            "comments": "Block all other direct access to gateway",
        },
        # ── Section: DNS (only if inline layer was created) ──
        *(
            [
                {
                    "_section": True,
                    "name": "DNS",
                    "layer": layer_name,
                    "position": "bottom",
                },
                {
                    "name": "DNS Layer",
                    "layer": layer_name,
                    "position": "bottom",
                    "source": "any",
                    "destination": "any",
                    "service": "dns",
                    "action": "Apply Layer",
                    "inline-layer": dns_layer_name,
                    "track": {"type": "None"},
                    "comments": "Inspect DNS traffic via inline DNS layer",
                },
            ]
            if dns_layer_ok
            else []
        ),
        # ── Section: Network Traffic ──
        {
            "_section": True,
            "name": "Network Traffic",
            "layer": layer_name,
            "position": "bottom",
        },
        {
            "name": "Outbound Traffic",
            "layer": layer_name,
            "position": "bottom",
            "source": ["net_10_1_1_0_24", "net_10_1_2_0_24", "net_10_1_3_0_24"],
            "destination": "any",
            "service": ["http", "https", "HTTP_and_HTTPS_proxy", "icmp-requests", "quic"],
            "action": "Accept",
            "track": {"type": "Log"},
            "comments": "Allow outbound web and ICMP from internal networks",
        },
        {
            "name": "Mail Services",
            "layer": layer_name,
            "position": "bottom",
            "source": ["net_10_1_1_0_24", "net_10_1_2_0_24", "jump_host"],
            "destination": "any",
            "service": "mail_services",
            "action": "Accept",
            "track": {"type": "Log"},
            "comments": "Allow outbound mail traffic",
        },
        {
            "name": "LDAP Services",
            "layer": layer_name,
            "position": "bottom",
            "source": ["win_client", "SMS"],
            "destination": "win_server",
            "service": ["LDAP_all", "ntp", "tcp-high-ports"],
            "action": "Accept",
            "track": {"type": "Log"},
            "comments": "Allow LDAP/NTP/RPC between client and server",
        },
        # ── Section: DMZ ──
        {
            "_section": True,
            "name": "DMZ",
            "layer": layer_name,
            "position": "bottom",
        },
        {
            "name": "DMZ Inbound",
            "layer": layer_name,
            "position": "bottom",
            "source": "attackers_feed_list",
            "destination": "targets_feed_list",
            "service": "any",
            "action": "Drop",
            "track": {"type": "Log"},
            "ignore-errors": True,
            "comments": "Block known attackers from targets (R82: dynamic_layer, R81.10: Drop)",
        },
        # ── Section: Clean up rule ──
        {
            "_section": True,
            "name": "Clean up rule",
            "layer": layer_name,
            "position": "bottom",
        },
        {
            "name": "Cleanup Rule",
            "layer": layer_name,
            "position": "bottom",
            "source": "any",
            "destination": "any",
            "service": "any",
            "action": "Drop",
            "track": {"type": "Log"},
            "comments": "Drop and log all unmatched traffic",
        },
    ]

    net_created = _add_rules(client, net_items, "Network Layer")

    total = dns_created + net_created
    log.info(
        "Policy complete: %d rules/sections created in '%s'",
        total,
        pkg_name,
    )
    return manifest_entries


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _add_demo_object(client: Any, obj_def: dict, retries: int = 2) -> list[dict]:
    """Create a single demo object and return manifest entries.

    Retries on transient server errors (NPE, generic_server_error).

    Args:
        client:  Authenticated API client.
        obj_def: Dict with ``cmd``, ``type``, and ``payload`` keys.
        retries: Number of retries for transient errors.

    Returns:
        List containing one manifest entry on success, empty on failure.
    """


    cmd = obj_def["cmd"]
    obj_type = obj_def["type"]
    payload = obj_def["payload"]
    name = payload["name"]

    for attempt in range(1 + retries):
        res = client.run_command(cmd, payload)
        if "uid" in res:
            log.info("  PASS %s (%s)", name, obj_type)
            return [
                {
                    "type": obj_type,
                    "name": name,
                    "uid": res["uid"],
                    "payload": dict(payload),
                }
            ]

        msg = str(res.get("message", ""))
        ml = msg.lower()
        transient = (
            "failed to execute" in ml
            or "null pointer" in ml
            or "hv000028" in ml
            or "rev_constraint" in ml
            or "eclipselink" in ml
            or "invocationtargetexception" in ml
            or "generic_server_error" in str(res.get("code", "")).lower()
        )
        if transient and attempt < retries:
            log.warning("  RETRY %s (attempt %d): %s", name, attempt + 1, msg)
            _time.sleep(3)
            continue

        log.error("  FAIL %s: %s", name, res.get("message", res))
        return []

    return []


def _add_rules(client: Any, items: list[dict], label: str) -> int:
    """Add access rules and sections from a definition list.

    Each item is either a section (``_section: True``) or a rule.

    Args:
        client: Authenticated API client.
        items:  List of section/rule dicts.
        label:  Label for log messages.

    Returns:
        Number of successfully created items.
    """
    created = 0
    for i, item in enumerate(items):
        item_copy = dict(item)
        is_section = item_copy.pop("_section", False)

        if is_section:
            cmd = "add-access-section"
            tag = f"{label} \u00a7  {item_copy['name']}"
        else:
            cmd = "add-access-rule"
            item_copy["ignore-warnings"] = True
            tag = f"{label} #{i + 1:2d} {item_copy['name']}"

        # Retry loop for transient server errors
        for attempt in range(3):
            res = client.run_command(cmd, item_copy)
            if "uid" in res:
                log.info("  PASS %s", tag)
                created += 1
                break
            msg = str(res.get("message", ""))
            transient = any(
                t in msg.lower()
                for t in ("failed to execute", "null pointer", "invocationtargetexception",
                          "rev_constraint", "eclipselink")
            )
            if transient and attempt < 2:
                log.warning("  RETRY %s (attempt %d): %s", tag, attempt + 1, msg)
                _time.sleep(3)
                continue
            log.warning("  FAIL %s \u2014 %s", tag, msg)
            break
    return created


def _make_demo_name(obj_type: str) -> str:
    """Generate a deterministic demo object name."""
    if obj_type == "dns-domain":
        return f".demo-{obj_type}-1.example.com"
    if obj_type in ("time", "time-group"):
        return f"DEMO_T_{random.randint(100, 999)}"
    return f"DEMO_{obj_type.upper().replace('-', '_')}_1"


def _create_demo_helpers(
    client: Any, obj_type: str
) -> tuple[str | None, str | None, str | None]:
    """Pre-create helper objects for types that need them."""
    helper_group = helper_except_group = helper_time = None

    if obj_type == "group-with-exclusion":
        helper_group = f"DEMO_INCLUDE_{random.randint(1000, 9999)}"
        helper_except_group = f"DEMO_EXCEPT_{random.randint(1000, 9999)}"
        res1 = client.run_command("add-group", {"name": helper_group})
        res2 = client.run_command("add-group", {"name": helper_except_group})
        if "uid" not in res1 or "uid" not in res2:
            log.warning("  Failed to create helper groups for %s", obj_type)
            helper_group = helper_except_group = None
        else:
            log.info(
                "  Created helper groups: include='%s', except='%s'",
                helper_group,
                helper_except_group,
            )
    elif obj_type == "time-group":
        helper_time = f"DEMO_T{random.randint(100, 999)}"
        res = client.run_command(
            "add-time",
            {"name": helper_time, "start-now": "true", "end-never": "true"},
        )
        if "uid" not in res:
            log.warning(
                "  Failed to create helper time: %s",
                res.get("message", res),
            )
            helper_time = None
        else:
            log.info("  Created helper time object: '%s'", helper_time)

    return helper_group, helper_except_group, helper_time


def _inject_demo_helpers(
    payload: dict,
    obj_type: str,
    helper_group: str | None,
    helper_except_group: str | None,
    helper_time: str | None,
) -> None:
    """Inject helper object references into the demo payload."""
    if obj_type == "group-with-exclusion" and helper_group and helper_except_group:
        payload["include"] = helper_group
        payload["except"] = helper_except_group
    elif obj_type == "time-group" and helper_time:
        payload["members"] = [helper_time]
    elif obj_type == "vpn-community-star":
        payload["center-gateways"] = ["DEMO_SIMPLE_GATEWAY_1"]
        payload["satellite-gateways"] = ["DEMO_INTEROPERABLE_DEVICE_1"]
    elif obj_type == "vpn-community-meshed":
        payload["gateways"] = [
            "DEMO_SIMPLE_GATEWAY_1",
            "DEMO_INTEROPERABLE_DEVICE_1",
        ]


def _adaptive_demo_add(
    client: Any,
    obj_type: str,
    payload: dict,
    parameters: list[dict],
) -> tuple[bool, dict]:
    """Adaptive ADD with self-healing for demo mode.

    Returns:
        ``(success, response_dict)``
    """
    success = False
    attempt = 0
    add_res: dict = {}

    while not success and attempt < MAX_RETRIES:
        attempt += 1
        if attempt > 1:
            log.info("  Optimizing payload (pass %d)...", attempt)

        add_res = client.run_command(f"add-{obj_type}", payload)
        success = "uid" in add_res or add_res.get("code") == "success"

        # Handle async tasks
        if not success and "task-id" in add_res:
            task_id = add_res["task-id"]
            log.info("  Async task %s — waiting...", task_id)
            for _ in range(30):
            

                _time.sleep(2)
                task_res = client.run_command(
                    "show-task",
                    {"task-id": task_id, "details-level": "full"},
                )
                tasks = task_res.get("tasks", [])
                if tasks:
                    status = tasks[0].get("status", "")
                    if status == "succeeded":
                        success = True
                        break
                    if status in ("failed", "partially succeeded"):
                        add_res = {
                            "message": tasks[0]
                            .get("task-details", [{}])[0]
                            .get("statusDescription", status)
                        }
                        break

        if (
            not success
            and "warning" in str(add_res).lower()
            and "uid" in str(add_res)
        ):
            success = True
            break

        if success:
            break

        # Auto-correction
        error_msg = str(add_res.get("message", "")).lower()
        blocking_errors = add_res.get(
            "blocking-errors", add_res.get("errors", [])
        )
        all_errors = error_msg
        for be in blocking_errors:
            if isinstance(be, dict):
                all_errors += " " + str(be.get("message", "")).lower()
            else:
                all_errors += " " + str(be).lower()

        if not auto_fix_payload(payload, all_errors, parameters):
            break

    return success, add_res
