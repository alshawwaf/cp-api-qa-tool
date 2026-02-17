"""Import configuration from an export JSON file.

Reads the export document produced by :mod:`exporter` and replays each
``add-*`` command on the target SMS with idempotency (skip if object
already exists) and dependency-aware publish phasing.

Usage (via CLI)::

    cp-qa -m 10.2.2.200 -u admin --mode demo --action import-config \\
        --export-path exports/sms_export.json
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

from cp_qa.logging import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Publish phases — group types that must be published together so that
# later commands can reference objects from earlier phases.
# ---------------------------------------------------------------------------

_PUBLISH_PHASES: list[set[str]] = [
    # Phase 1: Core objects (no dependencies)
    {"host", "network", "address-range", "dns-domain", "wildcard",
     "security-zone", "dynamic-object", "tag", "time", "time-group",
     "multicast-address-range", "access-point-name", "gsn-handover-group"},
    # Phase 2: Groups (reference phase 1)
    {"group", "group-with-exclusion", "network-feed"},
    # Phase 3: Services
    {"service-tcp", "service-udp", "service-icmp", "service-icmp6",
     "service-sctp", "service-other", "service-dce-rpc", "service-rpc",
     "service-compound-tcp", "service-citrix-tcp", "service-gtp",
     "scada-application"},
    # Phase 4: Service groups & applications
    {"service-group", "application-site", "application-site-category",
     "application-site-group"},
    # Phase 5: Identity, threat, users, auth, DLP, VPN, resources
    {"access-role", "identity-tag", "threat-indicator", "threat-ioc-feed",
     "threat-profile", "user", "user-group", "user-template",
     "administrator", "trusted-client", "passcode-profile",
     "radius-server", "tacacs-server", "radius-group", "tacacs-group",
     "data-type-keywords", "data-type-patterns", "data-type-file-attributes",
     "data-type-group", "data-type-weighted-keywords",
     "data-type-compound-group", "data-type-traditional-group",
     "vpn-community-meshed", "vpn-community-star",
     "resource-cifs", "resource-ftp", "resource-smtp", "resource-tcp",
     "resource-uri", "resource-mms", "resource-uri-for-qos",
     "exception-group", "smtp-server", "syslog-server", "log-exporter",
     "smart-task", "network-probe", "opsec-application",
     "mobile-profile", "limit", "override-categorization",
     "custom-trusted-ca-certificate", "external-trusted-ca",
     "opsec-trusted-ca", "outbound-inspection-certificate",
     "server-certificate", "generic-object", "interoperable-device"},
    # Phase 6: Gateways
    {"simple-gateway", "simple-cluster"},
    # Phase 7: Policy (packages, layers, rules, sections, NAT, threat)
    {"package", "access-layer", "threat-layer", "https-layer",
     "access-section", "access-rule", "nat-section", "nat-rule",
     "threat-rule", "threat-exception", "https-rule", "https-section",
     "mobile-access-rule", "mobile-access-section"},
]

#: Protected types — warn but don't add to cleanup manifests.
_PROTECTED_TYPES: frozenset[str] = frozenset({
    "simple-gateway", "simple-cluster", "checkpoint-host",
})

#: Commands that cannot be checked with show-<type> by name.
_NO_SHOW_CHECK: frozenset[str] = frozenset({
    "set-access-layer",
})


def _cmd_to_type(command: str) -> str:
    """Extract the object type from a command name."""
    return command.replace("add-", "").replace("set-", "").replace("delete-", "")


def _get_phase(obj_type: str) -> int:
    """Return the publish phase index for an object type."""
    for i, phase_set in enumerate(_PUBLISH_PHASES):
        if obj_type in phase_set:
            return i
    return len(_PUBLISH_PHASES)


def _is_transient_error(msg: str) -> bool:
    """Return True if the error message suggests a transient issue."""
    lower = msg.lower()
    return any(s in lower for s in (
        "runtime error",
        "try again",
        "temporarily",
        "timed out",
        "failed to execute",
    ))


def _import_single_command(
    client: Any,
    command: str,
    payload: dict,
    stats: dict,
) -> bool:
    """Execute a single import command with idempotency.

    Checks if the object exists first (``show-<type>``), skips if found.
    Retries on transient errors.
    """
    obj_type = _cmd_to_type(command)
    name = payload.get("name", "")

    # Commands like set-access-layer are always executed (no idempotency check)
    if command in _NO_SHOW_CHECK:
        res = client.run_command(command, {
            **payload, "ignore-warnings": True,
        })
        if "uid" in res or res.get("code") == "success":
            log.info("  SET %s (%s)", name, command)
            stats["created"] += 1
            return True
        log.warning("  FAIL %s (%s): %s", name, command, res.get("message", ""))
        stats["failed"] += 1
        stats["errors"].append({"command": command, "name": name,
                                "error": str(res.get("message", ""))})
        return False

    # Idempotency check
    show_cmd = f"show-{obj_type}"
    if name:
        existing = client.run_command(show_cmd, {"name": name})
        if "uid" in existing:
            log.info("  EXISTS %s (%s) — skipped", name, obj_type)
            stats["skipped"] += 1
            return True

    # Execute the add-* command with retry
    for attempt in range(3):
        res = client.run_command(command, {
            **payload,
            "ignore-warnings": True,
            "ignore-errors": True,
        })
        if "uid" in res or res.get("code") == "success":
            log.info("  CREATED %s (%s)", name, obj_type)
            stats["created"] += 1
            return True

        msg = str(res.get("message", ""))
        if _is_transient_error(msg) and attempt < 2:
            log.warning("  RETRY %s (%s) attempt %d: %s",
                        name, obj_type, attempt + 1, msg)
            time.sleep(3)
            continue

        log.warning("  FAIL %s (%s): %s", name, obj_type, msg)
        stats["failed"] += 1
        stats["errors"].append({"command": command, "name": name, "error": msg})
        return False

    return False


# ---------------------------------------------------------------------------
# Main import function
# ---------------------------------------------------------------------------

def import_config(
    client: Any,
    config_path: str,
    dry_run: bool = False,
) -> dict:
    """Import all objects and policies from an export file.

    Steps:

    1. Load and validate the export JSON.
    2. Group commands by publish phase.
    3. For each phase, execute commands with idempotency checks.
    4. Publish after each phase.
    5. Return statistics.

    Args:
        client:      Authenticated API client.
        config_path: Path to the export JSON file.
        dry_run:     If True, validate without making API calls.

    Returns:
        ``{"created": int, "skipped": int, "failed": int, "errors": list}``
    """
    if not os.path.exists(config_path):
        log.error("Export file not found: %s", config_path)
        return {"created": 0, "skipped": 0, "failed": 0, "errors": []}

    with open(config_path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)

    meta = doc.get("_meta", {})
    commands = doc.get("commands", [])
    log.info("Loaded export: %d commands from %s (exported %s)",
             len(commands), meta.get("source_server", "?"),
             meta.get("exported", "?"))

    if dry_run:
        log.info("[DRY-RUN] Would execute %d commands. Skipping.", len(commands))
        return {"created": 0, "skipped": 0, "failed": 0, "errors": [],
                "dry_run": True, "total": len(commands)}

    stats: dict[str, Any] = {
        "created": 0,
        "skipped": 0,
        "failed": 0,
        "errors": [],
    }

    # Group commands by phase
    phase_buckets: dict[int, list[dict]] = {}
    for cmd in commands:
        obj_type = _cmd_to_type(cmd["command"])
        phase = _get_phase(obj_type)
        phase_buckets.setdefault(phase, []).append(cmd)

    # Execute phase by phase
    for phase_idx in sorted(phase_buckets.keys()):
        phase_cmds = phase_buckets[phase_idx]
        phase_label = f"Phase {phase_idx + 1}"
        types_in_phase = {_cmd_to_type(c["command"]) for c in phase_cmds}
        log.info("--- %s: %d commands (%s) ---",
                 phase_label, len(phase_cmds),
                 ", ".join(sorted(types_in_phase)))

        for cmd in phase_cmds:
            _import_single_command(
                client, cmd["command"], cmd["payload"], stats,
            )

        # Publish after each phase
        try:
            client.publish()
            log.info("  Published %s", phase_label)
        except Exception as exc:
            log.warning("  Publish failed for %s: %s", phase_label, exc)

    log.info("Import complete: %d created, %d skipped, %d failed",
             stats["created"], stats["skipped"], stats["failed"])
    if stats["errors"]:
        log.warning("Errors:")
        for err in stats["errors"][:20]:
            log.warning("  %s %s: %s", err["command"], err["name"], err["error"])
        if len(stats["errors"]) > 20:
            log.warning("  ... and %d more", len(stats["errors"]) - 20)

    return stats
