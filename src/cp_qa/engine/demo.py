"""Demo mode operations: create, cleanup, services, and policy.

Demo mode creates one representative object for every supported type,
a set of service objects, and a Check Point recommended security policy.
Everything is tracked in a manifest file for later cleanup.

Usage (via CLI)::

    cp-qa -m 10.0.0.1 -u admin --mode demo --action create
    cp-qa -m 10.0.0.1 -u admin --mode demo --action cleanup
"""

from __future__ import annotations

import random
import time
from typing import Any

from cp_qa.constants import (
    CLEANUP_ORDER,
    DEMO_PREFIX,
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

def create_demo_services(client: Any) -> list[dict]:
    """Create service objects for the demo policy.

    Creates TCP, UDP, ICMP services and a service group.

    Args:
        client: Authenticated API client.

    Returns:
        List of manifest entries for created services.
    """
    log.info("--- DEMO: Creating service objects ---")

    services = [
        {
            "cmd": "add-service-tcp",
            "type": "service-tcp",
            "payload": {
                "name": "DEMO_SVC_HTTP",
                "port": "80",
                "comments": "HTTP service",
                "color": "red",
                "ignore-warnings": True,
            },
        },
        {
            "cmd": "add-service-tcp",
            "type": "service-tcp",
            "payload": {
                "name": "DEMO_SVC_HTTPS",
                "port": "443",
                "comments": "HTTPS service",
                "color": "red",
                "ignore-warnings": True,
            },
        },
        {
            "cmd": "add-service-tcp",
            "type": "service-tcp",
            "payload": {
                "name": "DEMO_SVC_SSH",
                "port": "22",
                "comments": "SSH service",
                "color": "orange",
                "ignore-warnings": True,
            },
        },
        {
            "cmd": "add-service-tcp",
            "type": "service-tcp",
            "payload": {
                "name": "DEMO_SVC_SMTP",
                "port": "25",
                "comments": "SMTP service",
                "color": "yellow",
                "ignore-warnings": True,
            },
        },
        {
            "cmd": "add-service-udp",
            "type": "service-udp",
            "payload": {
                "name": "DEMO_SVC_DNS",
                "port": "53",
                "comments": "DNS service",
                "color": "blue",
                "ignore-warnings": True,
            },
        },
        {
            "cmd": "add-service-icmp",
            "type": "service-icmp",
            "payload": {
                "name": "DEMO_SVC_PING",
                "icmp-type": 8,
                "comments": "ICMP Echo Request",
                "color": "aquamarine",
                "ignore-warnings": True,
            },
        },
    ]

    manifest_entries: list[dict] = []
    for svc in services:
        res = client.run_command(svc["cmd"], svc["payload"])
        name = svc["payload"]["name"]
        if "uid" in res:
            log.info("  PASS %s (%s)", name, svc["type"])
            manifest_entries.append(
                {
                    "type": svc["type"],
                    "name": name,
                    "uid": res["uid"],
                    "payload": svc["payload"],
                }
            )
        else:
            log.error("  FAIL %s: %s", name, res.get("message", res))

    # Service group
    grp_payload = {
        "name": "DEMO_SVC_WEB_GROUP",
        "members": ["DEMO_SVC_HTTP", "DEMO_SVC_HTTPS"],
        "comments": "Web services group",
        "color": "red",
        "ignore-warnings": True,
    }
    res = client.run_command("add-service-group", grp_payload)
    if "uid" in res:
        log.info("  PASS DEMO_SVC_WEB_GROUP (service-group)")
        manifest_entries.append(
            {
                "type": "service-group",
                "name": "DEMO_SVC_WEB_GROUP",
                "uid": res["uid"],
                "payload": grp_payload,
            }
        )
    else:
        log.error(
            "  FAIL DEMO_SVC_WEB_GROUP: %s", res.get("message", res)
        )

    log.info("Services created: %d", len(manifest_entries))
    return manifest_entries


# =========================================================================
# Demo policy
# =========================================================================

def create_demo_policy(client: Any, manifest: list[dict]) -> list[dict]:
    """Create a Check Point recommended security policy using all demo objects.

    Creates a policy package and populates it with access rules that
    follow Check Point best practices (management access, stealth rule,
    cleanup rule, etc.).

    Args:
        client:   Authenticated API client.
        manifest: Current manifest with all created objects and services.

    Returns:
        List of manifest entries for the policy package.
    """
    log.info("--- DEMO: Creating recommended policy ---")

    pkg_name = "DEMO_Policy"
    res = client.run_command(
        "add-package",
        {
            "name": pkg_name,
            "comments": "Check Point recommended policy — created by CP API QA Tool",
            "access": True,
            "threat-prevention": False,
        },
    )
    if "uid" not in res:
        log.error(
            "Failed to create policy package: %s", res.get("message", res)
        )
        return []

    log.info("  PASS Policy package: %s", pkg_name)
    
    # Ensure package is published so layers are fully initialized
    client.publish()
    
    # Extract the actual access layer name from the created package
    # Check Point usually creates 'PackageName Network' but we should be sure.
    access_layers = res.get("access-layers", [])
    if access_layers and isinstance(access_layers, list):
        layer_name = access_layers[0].get("name", f"{pkg_name} Network")
    else:
        layer_name = f"{pkg_name} Network"
        
    log.info("  Using access layer: %s", layer_name)

    manifest_entries = [
        {"type": "package", "name": pkg_name, "uid": res["uid"], "payload": {}}
    ]

    # Build lookup: type -> first object name
    obj_lookup: dict[str, str] = {}
    for entry in manifest:
        t = entry["type"]
        if entry.get("uid") and t not in obj_lookup:
            obj_lookup[t] = entry["name"]

    def obj(type_name: str, fallback: str = "any") -> str:
        return obj_lookup.get(type_name, fallback)

    # Check Point recommended access rules
    rules = [
        {
            "name": "Management Access",
            "source": obj("network"),
            "destination": obj("checkpoint-host"),
            "service": ["DEMO_SVC_HTTPS", "DEMO_SVC_SSH"],
            "action": "Accept",
            "track": {"type": "Log"},
            "comments": "Allow management access to SMS — CP Best Practice",
        },
        {
            "name": "Stealth Rule",
            "source": "any",
            "destination": obj("simple-gateway"),
            "service": "any",
            "action": "Drop",
            "track": {"type": "Log"},
            "comments": "Block direct access to gateway — CP Best Practice",
        },
        {
            "name": "DNS Resolution",
            "source": obj("group"),
            "destination": obj("dns-domain", "any"),
            "service": "DEMO_SVC_DNS",
            "action": "Accept",
            "track": {"type": "Log"},
            "comments": "Allow internal DNS resolution",
        },
        {
            "name": "Outbound Web Access",
            "source": obj("network"),
            "destination": "any",
            "service": "DEMO_SVC_WEB_GROUP",
            "action": "Accept",
            "track": {"type": "Log"},
            "comments": "Allow outbound web traffic from internal network",
        },
        {
            "name": "Inbound Web Services",
            "source": "any",
            "destination": obj("host"),
            "service": ["DEMO_SVC_HTTP", "DEMO_SVC_HTTPS"],
            "action": "Accept",
            "track": {"type": "Log"},
            "comments": "Allow inbound web traffic to published server",
        },
        {
            "name": "Internal Network Access",
            "source": obj("address-range"),
            "destination": obj("network"),
            "service": "any",
            "action": "Accept",
            "track": {"type": "Log"},
            "comments": "Allow internal address range communication",
        },
        {
            "name": "Zone-Based Access",
            "source": obj("security-zone"),
            "destination": obj("wildcard"),
            "service": "any",
            "action": "Accept",
            "track": {"type": "Log"},
            "comments": "Zone-based firewall policy",
        },
        {
            "name": "Dynamic Object Access",
            "source": obj("dynamic-object"),
            "destination": obj("network"),
            "service": "DEMO_SVC_WEB_GROUP",
            "action": "Accept",
            "track": {"type": "Log"},
            "comments": "Dynamic object-based network access",
        },
        {
            "name": "Exclusion Group Block",
            "source": obj("group-with-exclusion"),
            "destination": "any",
            "service": "any",
            "action": "Drop",
            "track": {"type": "Log"},
            "comments": "Block traffic from excluded group members",
        },
        {
            "name": "VPN Interop Access",
            "source": obj("interoperable-device"),
            "destination": obj("network"),
            "service": "any",
            "action": "Accept",
            "track": {"type": "Log"},
            "comments": "VPN interoperability traffic",
        },
        {
            "name": "Threat Feed Block",
            "source": obj("network-feed"),
            "destination": "any",
            "service": "any",
            "action": "Drop",
            "track": {"type": "Log"},
            "comments": "Block known malicious IPs (TOR exit nodes)",
        },
        {
            "name": "Time-Restricted SSH",
            "source": "any",
            "destination": obj("host"),
            "service": "DEMO_SVC_SSH",
            "action": "Accept",
            "track": {"type": "Log"},
            "time": obj("time"),
            "comments": "Time-restricted SSH access",
        },
        {
            "name": "Multicast Traffic",
            "source": "any",
            "destination": obj("multicast-address-range"),
            "service": "any",
            "action": "Accept",
            "track": {"type": "Log"},
            "comments": "Allow multicast traffic",
        },
        {
            "name": "Cleanup Rule",
            "source": "any",
            "destination": "any",
            "service": "any",
            "action": "Drop",
            "track": {"type": "Log"},
            "comments": "Drop and log all unmatched traffic — CP Best Practice",
        },
    ]

    created_rules = 0
    for i, rule_def in enumerate(rules):
        rule_def["layer"] = layer_name
        rule_def["position"] = "bottom"
        res = client.run_command("add-access-rule", rule_def)
        rname = rule_def["name"]
        if "uid" in res:
            log.info("  PASS Rule %2d: %s", i + 1, rname)
            created_rules += 1
        else:
            log.warning(
                "  FAIL Rule %2d: %s — %s",
                i + 1,
                rname,
                res.get("message", res),
            )

    log.info(
        "Policy complete: %d/%d rules created in '%s'",
        created_rules,
        len(rules),
        layer_name,
    )
    return manifest_entries


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

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
                import time as _time

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
