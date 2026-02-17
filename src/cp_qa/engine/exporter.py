"""Full SMS export: read all objects and policies, produce import-ready JSON.

Connects to a live SMS, enumerates all user-created objects across all
supported types, transforms each into an ``add-*`` payload using the
universal transformer, and serialises the result as an ordered command list.

Usage (via CLI)::

    cp-qa -m 10.1.1.100 -u admin --mode demo --action export-config
    cp-qa ... --action export-config --export-path exports/my_backup.json
"""

from __future__ import annotations

import datetime
import json
import os
from typing import Any, Callable

from cp_qa.constants import CLEANUP_ORDER, DISCOVERABLE_TYPES
from cp_qa.engine.transformer import (
    is_builtin,
    transform_show_to_add,
)
from cp_qa.logging import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Types to skip during export
# ---------------------------------------------------------------------------

#: Types that cannot be exported on a standard single-domain SMS or are
#: read-only / batch-only / sub-object types.
EXPORT_SKIP_TYPES: frozenset[str] = frozenset({
    # Infrastructure-dependent
    "data-center-server", "data-center-object", "data-center-query",
    "domain", "domain-permissions-profile", "md-permissions-profile",
    "mds", "global-assignment",
    "azure-ad", "identity-provider", "idp-administrator-group",
    "ldap-group", "securid-server",
    "lsm-cluster", "lsm-gateway",
    "central-license", "repository-package", "repository-script",
    "api-key",
    # Read-only / system-managed
    "updatable-object", "gaia-best-practice",
    # Non-standard lifecycle (not real add-* types)
    "threat-protections", "web-console-statistics",
    "objects-batch", "rules-batch",
    # Sub-objects (exported as part of their parent)
    "interface", "multiple-key-exchanges",
    # SMS itself
    "checkpoint-host",
    # Policy rule/section types (exported via rulebase, not show-<plural>)
    "access-rule", "access-section", "nat-rule", "nat-section",
    "threat-rule", "threat-exception",
    "https-rule", "https-section",
    "mobile-access-rule", "mobile-access-section",
    "mobile-access-profile-rule", "mobile-access-profile-section",
    # Layers are exported as part of packages
    "access-layer", "threat-layer", "https-layer",
    # Package is exported separately
    "package",
})

# ---------------------------------------------------------------------------
# Creation order (reverse of CLEANUP_ORDER)
# ---------------------------------------------------------------------------

#: Object types in dependency order — items created first have no
#: unsatisfied dependencies.  Derived from reversing CLEANUP_ORDER.
CREATION_ORDER: list[str] = list(reversed(CLEANUP_ORDER))


def _type_sort_key(obj_type: str) -> int:
    """Return a sort index for *obj_type* based on CREATION_ORDER."""
    try:
        return CREATION_ORDER.index(obj_type)
    except ValueError:
        return len(CREATION_ORDER)


# ---------------------------------------------------------------------------
# Object enumeration
# ---------------------------------------------------------------------------

def _paginated_show(
    client: Any,
    show_cmd: str,
    page_size: int = 100,
    details_level: str = "full",
) -> list[dict]:
    """Fetch all objects from a paginated ``show-*`` command."""
    all_objects: list[dict] = []
    offset = 0

    while True:
        res = client.run_command(show_cmd, {
            "limit": page_size,
            "offset": offset,
            "details-level": details_level,
        })
        objects = res.get("objects", res.get("packages", []))
        if not objects:
            break
        all_objects.extend(objects)
        total = res.get("total", len(objects))
        offset += page_size
        if offset >= total:
            break

    return all_objects


def _enumerate_objects(
    client: Any,
    plural_cmd: str,
    obj_type: str,
    spec: dict,
    obj_registry: dict[str, dict],
    progress: Callable | None = None,
) -> list[dict]:
    """Fetch and transform all user-created objects of a given type.

    Returns a list of ``{"command": "add-<type>", "payload": {...}}`` dicts.
    """
    show_cmd = f"show-{plural_cmd}"
    commands: list[dict] = []

    try:
        objects = _paginated_show(client, show_cmd)
    except Exception as exc:
        log.warning("  SKIP %s: %s", show_cmd, exc)
        return commands

    for obj in objects:
        # Register ALL objects (including built-in) for reference resolution.
        # Other objects may reference built-in services, hosts, etc. by UID.
        uid = obj.get("uid")
        if uid:
            obj_registry[uid] = obj

        if is_builtin(obj):
            continue

        # Skip system-created defaults (exist on every fresh SMS)
        meta = obj.get("meta-info", {})
        if isinstance(meta, dict) and meta.get("creator") == "System":
            continue

        payload = transform_show_to_add(obj_type, obj, spec, obj_registry)
        if payload:
            commands.append({
                "command": f"add-{obj_type}",
                "payload": payload,
            })

    if commands and progress:
        progress(obj_type, len(commands))

    return commands


# ---------------------------------------------------------------------------
# Policy export
# ---------------------------------------------------------------------------

def _export_rulebase(
    client: Any,
    layer_name: str,
    rulebase_cmd: str,
    rule_type: str,
    section_type: str,
    spec: dict,
    obj_registry: dict[str, dict],
) -> tuple[list[dict], list[str]]:
    """Export all rules from a single layer.

    Returns:
        Tuple of (commands_list, discovered_inline_layer_names).
    """
    commands: list[dict] = []
    inline_layers: list[str] = []
    offset = 0
    page_size = 100

    while True:
        res = client.run_command(rulebase_cmd, {
            "name": layer_name,
            "offset": offset,
            "limit": page_size,
            "use-object-dictionary": True,
            "details-level": "full",
        })

        # Populate object registry from the objects-dictionary
        for obj in res.get("objects-dictionary", []):
            uid = obj.get("uid")
            if uid:
                obj_registry[uid] = obj

        rulebase = res.get("rulebase", [])
        for item in rulebase:
            _process_rulebase_item(
                item, layer_name, rule_type, section_type,
                spec, obj_registry, commands, inline_layers,
            )

        total = res.get("total", 0)
        offset += page_size
        if offset >= total or not rulebase:
            break

    return commands, inline_layers


def _process_rulebase_item(
    item: dict,
    layer_name: str,
    rule_type: str,
    section_type: str,
    spec: dict,
    obj_registry: dict[str, dict],
    commands: list[dict],
    inline_layers: list[str],
) -> None:
    """Process a single rulebase item (rule or section)."""
    item_type = item.get("type", "")

    if item_type == section_type:
        # Section header
        section_name = item.get("name", "")
        if section_name:
            commands.append({
                "command": f"add-{section_type}",
                "payload": {
                    "layer": layer_name,
                    "name": section_name,
                    "position": "bottom",
                },
            })
        # Process rules inside this section
        for rule in item.get("rulebase", []):
            _process_rulebase_item(
                rule, layer_name, rule_type, section_type,
                spec, obj_registry, commands, inline_layers,
            )

    elif item_type == rule_type:
        payload = transform_show_to_add(
            rule_type, item, spec, obj_registry,
        )
        if payload:
            payload["layer"] = layer_name
            payload["position"] = "bottom"
            commands.append({
                "command": f"add-{rule_type}",
                "payload": payload,
            })

            # Discover inline layers
            il = item.get("inline-layer")
            if isinstance(il, dict) and il.get("name"):
                inline_layers.append(il["name"])
            elif isinstance(il, str) and il:
                inline_layers.append(il)


def _export_policy_packages(
    client: Any,
    spec: dict,
    obj_registry: dict[str, dict],
    package_names: list[str] | None = None,
) -> list[dict]:
    """Export policy packages with all layers and rules."""
    commands: list[dict] = []

    # Get all packages
    if package_names:
        packages = []
        for pname in package_names:
            pkg = client.run_command("show-package", {
                "name": pname, "details-level": "full",
            })
            if "uid" in pkg:
                packages.append(pkg)
    else:
        packages = _paginated_show(client, "show-packages", details_level="full")

    for pkg in packages:
        pkg_name = pkg.get("name", "")
        if not pkg_name or is_builtin(pkg):
            continue

        log.info("  Exporting package: %s", pkg_name)

        # Package command
        pkg_payload: dict[str, Any] = {
            "name": pkg_name,
            "access": pkg.get("access", True),
            "threat-prevention": pkg.get("threat-prevention", False),
        }
        comments = pkg.get("comments", "")
        if comments:
            pkg_payload["comments"] = comments
        commands.append({"command": "add-package", "payload": pkg_payload})

        # --- Access layers ---
        layer_names = _extract_layer_names_from_package(pkg)
        all_inline_layers: list[str] = []

        for layer_name in layer_names:
            # Layer settings
            layer_info = client.run_command("show-access-layer", {
                "name": layer_name, "details-level": "full",
            })
            if "uid" not in layer_info:
                continue

            # Export layer settings if non-default
            layer_settings: dict[str, Any] = {}
            for setting in ("applications-and-url-filtering",
                            "content-awareness", "mobile-access"):
                if layer_info.get(setting):
                    layer_settings[setting] = True
            if layer_settings:
                commands.append({
                    "command": "set-access-layer",
                    "payload": {"name": layer_name, **layer_settings,
                                "ignore-warnings": True},
                })

            # Access rules
            rule_cmds, inline_names = _export_rulebase(
                client, layer_name,
                "show-access-rulebase", "access-rule", "access-section",
                spec, obj_registry,
            )
            commands.extend(rule_cmds)
            all_inline_layers.extend(inline_names)
            log.info("    Access layer '%s': %d items", layer_name, len(rule_cmds))

        # --- Inline layers ---
        for il_ref in dict.fromkeys(all_inline_layers):  # deduplicate, preserve order
            il_info = client.run_command("show-access-layer", {
                "name": il_ref, "details-level": "full",
            })
            if "uid" not in il_info:
                continue

            # Resolve the actual name (il_ref may be a UID)
            il_name = il_info.get("name", il_ref)

            # Register the layer in obj_registry so rules can resolve it
            il_uid = il_info.get("uid", il_ref)
            obj_registry[il_uid] = il_info

            il_payload: dict[str, Any] = {
                "name": il_name,
                "add-default-rule": False,
            }
            for f in ("color", "comments"):
                if il_info.get(f):
                    il_payload[f] = il_info[f]
            ica = il_info.get("implicit-cleanup-action")
            if ica:
                il_payload["implicit-cleanup-action"] = ica
            commands.append({"command": "add-access-layer", "payload": il_payload})

            # Inline layer rules (use resolved name for the layer reference)
            il_rule_cmds, _ = _export_rulebase(
                client, il_name,
                "show-access-rulebase", "access-rule", "access-section",
                spec, obj_registry,
            )
            commands.extend(il_rule_cmds)
            log.info("    Inline layer '%s': %d items", il_name, len(il_rule_cmds))

        # --- NAT rules ---
        try:
            nat_cmds, _ = _export_rulebase(
                client, f"{pkg_name} Network",
                "show-nat-rulebase", "nat-rule", "nat-section",
                spec, obj_registry,
            )
            # Filter out auto-generated NAT rules
            nat_cmds = [
                c for c in nat_cmds
                if not c["payload"].get("auto-generated", False)
            ]
            commands.extend(nat_cmds)
            if nat_cmds:
                log.info("    NAT rules: %d", len(nat_cmds))
        except Exception as exc:
            log.warning("    Could not export NAT rules: %s", exc)

        # --- Threat prevention ---
        if pkg.get("threat-prevention"):
            try:
                tp_layers = pkg.get("threat-layers", {})
                if isinstance(tp_layers, dict):
                    tp_layers = tp_layers.get("objects", tp_layers.get("add", []))
                if isinstance(tp_layers, list):
                    for tl in tp_layers:
                        tl_name = tl.get("name", "") if isinstance(tl, dict) else str(tl)
                        if not tl_name:
                            continue
                        tp_cmds, _ = _export_rulebase(
                            client, tl_name,
                            "show-threat-rulebase", "threat-rule", "threat-rule",
                            spec, obj_registry,
                        )
                        commands.extend(tp_cmds)
                        if tp_cmds:
                            log.info("    Threat layer '%s': %d rules", tl_name, len(tp_cmds))
            except Exception as exc:
                log.warning("    Could not export threat rules: %s", exc)

    return commands


def _extract_layer_names_from_package(pkg: dict) -> list[str]:
    """Extract access layer names from a show-package response."""
    layers = pkg.get("access-layers", [])
    if isinstance(layers, dict):
        layers = layers.get("objects", layers.get("add", []))
    if not isinstance(layers, list):
        return []
    names: list[str] = []
    for layer in layers:
        if isinstance(layer, dict):
            name = layer.get("name", "")
            if name:
                names.append(name)
        elif isinstance(layer, str):
            names.append(layer)
    return names


# ---------------------------------------------------------------------------
# CLI command generation (mgmt_cli batch files)
# ---------------------------------------------------------------------------

#: Publish phase boundaries — types in each phase must be published together
#: before the next phase can reference them.
_CLI_PUBLISH_PHASES: list[set[str]] = [
    # Phase 1: Core objects
    {"host", "network", "address-range", "dns-domain", "wildcard",
     "security-zone", "dynamic-object", "tag", "time", "time-group",
     "multicast-address-range", "access-point-name", "gsn-handover-group"},
    # Phase 2: Groups
    {"group", "group-with-exclusion", "network-feed"},
    # Phase 3: Services
    {"service-tcp", "service-udp", "service-icmp", "service-icmp6",
     "service-sctp", "service-other", "service-dce-rpc", "service-rpc",
     "service-compound-tcp", "service-citrix-tcp", "service-gtp",
     "scada-application"},
    # Phase 4: Service groups & applications
    {"service-group", "application-site", "application-site-category",
     "application-site-group"},
    # Phase 5: Identity, threat, users, auth, DLP, VPN, resources, gateways
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
     "server-certificate", "generic-object", "interoperable-device",
     "simple-gateway", "simple-cluster"},
    # Phase 6: Policy
    {"package", "set-access-layer", "access-layer", "threat-layer",
     "https-layer", "access-section", "access-rule", "nat-section",
     "nat-rule", "threat-rule", "threat-exception", "https-rule",
     "https-section", "mobile-access-rule", "mobile-access-section"},
]


def _cli_phase_for_type(obj_type: str) -> int:
    """Return the publish phase index for a given object type."""
    for i, phase_set in enumerate(_CLI_PUBLISH_PHASES):
        if obj_type in phase_set:
            return i
    return len(_CLI_PUBLISH_PHASES)


def _flatten_to_cli_args(
    data: dict,
    prefix: str = "",
) -> list[str]:
    """Flatten a payload dict into mgmt_cli positional arguments.

    Uses Check Point's dot-notation for nested fields and numbered
    notation for lists::

        {"track": {"type": "Log"}}           → track.type "Log"
        {"source": ["a", "b"]}               → source.1 "a" source.2 "b"
        {"interfaces": [{"name": "eth0"}]}    → interfaces.1.name "eth0"
    """
    parts: list[str] = []

    for key, val in data.items():
        full_key = f"{prefix}.{key}" if prefix else key

        if val is None:
            continue
        elif isinstance(val, bool):
            parts.append(f"{full_key} {str(val).lower()}")
        elif isinstance(val, (int, float)):
            parts.append(f"{full_key} {val}")
        elif isinstance(val, str):
            if val == "":
                continue
            # Quote strings
            escaped = val.replace("\\", "\\\\").replace('"', '\\"')
            parts.append(f'{full_key} "{escaped}"')
        elif isinstance(val, dict):
            if not val:
                continue
            parts.extend(_flatten_to_cli_args(val, prefix=full_key))
        elif isinstance(val, list):
            if not val:
                continue
            for i, item in enumerate(val, start=1):
                idx_key = f"{full_key}.{i}"
                if isinstance(item, dict):
                    parts.extend(_flatten_to_cli_args(item, prefix=idx_key))
                elif isinstance(item, str):
                    escaped = item.replace("\\", "\\\\").replace('"', '\\"')
                    parts.append(f'{idx_key} "{escaped}"')
                elif isinstance(item, bool):
                    parts.append(f"{idx_key} {str(item).lower()}")
                elif isinstance(item, (int, float)):
                    parts.append(f"{idx_key} {item}")

    return parts


def export_cli_commands(
    commands: list[dict],
    output_dir: str,
) -> None:
    """Write mgmt_cli batch files grouped by object type.

    Creates one ``.txt`` file per object type containing ready-to-paste
    ``mgmt_cli`` commands, plus a master ``00_run_all.txt`` that lists
    the files in dependency order with publish commands between phases.

    Args:
        commands:   The command list from the JSON export.
        output_dir: Directory to write CLI files into.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Group commands by type
    type_commands: dict[str, list[str]] = {}
    for cmd in commands:
        command_name = cmd["command"]
        payload = cmd["payload"]
        obj_type = command_name.replace("add-", "").replace("set-", "")

        args = _flatten_to_cli_args(payload)
        line = f"mgmt_cli {command_name} {' '.join(args)} ignore-warnings true --format json"
        type_commands.setdefault(obj_type, []).append(line)

    # Write per-type files
    written_files: dict[str, str] = {}  # type -> filename
    for obj_type, lines in type_commands.items():
        # Sanitize filename
        filename = f"{obj_type}.txt"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(f"# {obj_type} — {len(lines)} commands\n")
            fh.write(f"# Generated by CP API QA Tool export\n\n")
            for line in lines:
                fh.write(line + "\n")
        written_files[obj_type] = filename

    # Build master run-all file with publish phases
    master_path = os.path.join(output_dir, "00_run_all.txt")
    with open(master_path, "w", encoding="utf-8") as fh:
        fh.write("# Full SMS import — run commands in dependency order\n")
        fh.write("# Generated by CP API QA Tool export\n")
        fh.write("#\n")
        fh.write("# Copy-paste each section into a terminal connected to mgmt_cli,\n")
        fh.write("# or source the individual .txt files.\n")
        fh.write("# Make sure to run 'mgmt_cli publish' between phases.\n\n")
        fh.write("# === Login ===\n")
        fh.write('mgmt_cli login user <USERNAME> password <PASSWORD> --format json\n\n')

        # Collect types by phase
        phase_types: dict[int, list[str]] = {}
        for obj_type in written_files:
            phase = _cli_phase_for_type(obj_type)
            phase_types.setdefault(phase, []).append(obj_type)

        for phase_idx in sorted(phase_types.keys()):
            types_in_phase = phase_types[phase_idx]
            fh.write(f"# === Phase {phase_idx + 1} ===\n")
            for obj_type in types_in_phase:
                fh.write(f"# {obj_type} ({len(type_commands[obj_type])} commands)\n")
                for line in type_commands[obj_type]:
                    fh.write(line + "\n")
            fh.write("\nmgmt_cli publish --format json\n\n")

        fh.write("# === Logout ===\n")
        fh.write("mgmt_cli logout --format json\n")

    log.info("CLI commands written to: %s (%d files)", output_dir, len(written_files))


def _mgmt_cli_to_clish(line: str) -> str:
    """Convert a mgmt_cli command line to Gaia clish (mgmt) syntax.

    Transformations:
    - ``mgmt_cli add-host ...`` → ``mgmt add host ...``
    - Removes ``--format json``
    """
    line = line.replace("--format json", "").rstrip()
    # mgmt_cli add-host → mgmt add host  (split verb-type hyphen)
    line = line.replace("mgmt_cli ", "mgmt ", 1)
    # Split "add-host" → "add host", "set-access-layer" → "set access-layer"
    parts = line.split(" ", 2)  # ["mgmt", "add-host", "name ..."]
    if len(parts) >= 2:
        verb_type = parts[1]
        for verb in ("add-", "set-", "show-", "delete-"):
            if verb_type.startswith(verb):
                parts[1] = verb.rstrip("-") + " " + verb_type[len(verb):]
                break
        line = " ".join(parts)
    return line


def export_clish_commands(
    commands: list[dict],
    output_dir: str,
) -> None:
    """Write Gaia clish batch files grouped by object type.

    Same structure as :func:`export_cli_commands` but uses Gaia clish
    ``mgmt`` syntax instead of ``mgmt_cli``.

    Args:
        commands:   The command list from the JSON export.
        output_dir: Directory to write clish files into.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Group commands by type
    type_commands: dict[str, list[str]] = {}
    for cmd in commands:
        command_name = cmd["command"]
        payload = cmd["payload"]
        obj_type = command_name.replace("add-", "").replace("set-", "")

        args = _flatten_to_cli_args(payload)
        mgmt_line = f"mgmt_cli {command_name} {' '.join(args)} ignore-warnings true --format json"
        clish_line = _mgmt_cli_to_clish(mgmt_line)
        type_commands.setdefault(obj_type, []).append(clish_line)

    # Write per-type files
    written_files: dict[str, str] = {}
    for obj_type, lines in type_commands.items():
        filename = f"{obj_type}.txt"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(f"# {obj_type} — {len(lines)} commands\n")
            fh.write("# Generated by CP API QA Tool export (Gaia clish)\n\n")
            for line in lines:
                fh.write(line + "\n")
        written_files[obj_type] = filename

    # Build master run-all file
    master_path = os.path.join(output_dir, "00_run_all.txt")
    with open(master_path, "w", encoding="utf-8") as fh:
        fh.write("# Full SMS import — Gaia clish commands in dependency order\n")
        fh.write("# Generated by CP API QA Tool export\n")
        fh.write("#\n")
        fh.write("# Run these commands in Gaia clish (not expert mode).\n")
        fh.write("# Make sure to run 'mgmt publish' between phases.\n\n")
        fh.write("# === Login ===\n")
        fh.write("mgmt login user <USERNAME>\n\n")

        # Collect types by phase
        phase_types: dict[int, list[str]] = {}
        for obj_type in written_files:
            phase = _cli_phase_for_type(obj_type)
            phase_types.setdefault(phase, []).append(obj_type)

        for phase_idx in sorted(phase_types.keys()):
            types_in_phase = phase_types[phase_idx]
            fh.write(f"# === Phase {phase_idx + 1} ===\n")
            for obj_type in types_in_phase:
                fh.write(f"# {obj_type} ({len(type_commands[obj_type])} commands)\n")
                for line in type_commands[obj_type]:
                    fh.write(line + "\n")
            fh.write("\nmgmt publish\n\n")

        fh.write("# === Logout ===\n")
        fh.write("mgmt logout\n")

    log.info("Clish commands written to: %s (%d files)", output_dir, len(written_files))


# ---------------------------------------------------------------------------
# Main export function
# ---------------------------------------------------------------------------

def export_full_sms(
    client: Any,
    spec: dict,
    package_names: list[str] | None = None,
    output_path: str = "exports/sms_export.json",
    progress_callback: Callable | None = None,
) -> dict:
    """Export all user-created objects and policies from an SMS.

    Steps:

    1. Enumerate all user-created objects (paginated show-* for each type).
    2. Transform each into an add-* command using the universal transformer.
    3. Export policy packages with layers, rules, NAT, threat prevention.
    4. Order commands by dependency.
    5. Write output JSON.

    Args:
        client:            Authenticated API client.
        spec:              Parsed API specification.
        package_names:     Policy packages to export (``None`` = all).
        output_path:       Destination JSON file path.
        progress_callback: Optional ``callback(type_name, count)``.

    Returns:
        Export metadata dict with statistics.
    """
    obj_registry: dict[str, dict] = {}
    object_commands: list[dict] = []
    policy_commands: list[dict] = []

    # --- Phase 1: Enumerate all objects ---
    log.info("=== Phase 1: Enumerating objects ===")

    # Build a lookup: singular type -> plural command
    type_to_plural: dict[str, str] = {
        singular: plural for plural, singular in DISCOVERABLE_TYPES
    }

    # Walk types in creation order
    exported_types: set[str] = set()
    for obj_type in CREATION_ORDER:
        if obj_type in EXPORT_SKIP_TYPES:
            continue
        plural = type_to_plural.get(obj_type)
        if not plural:
            continue
        if obj_type in exported_types:
            continue
        exported_types.add(obj_type)

        cmds = _enumerate_objects(
            client, plural, obj_type, spec, obj_registry,
            progress_callback,
        )
        object_commands.extend(cmds)

    # Catch any types in DISCOVERABLE_TYPES not in CREATION_ORDER
    for plural, singular in DISCOVERABLE_TYPES:
        if singular in exported_types or singular in EXPORT_SKIP_TYPES:
            continue
        cmds = _enumerate_objects(
            client, plural, singular, spec, obj_registry,
            progress_callback,
        )
        object_commands.extend(cmds)

    log.info("  Total objects exported: %d", len(object_commands))

    # --- Phase 2: Export policies ---
    log.info("=== Phase 2: Exporting policies ===")
    policy_commands = _export_policy_packages(
        client, spec, obj_registry, package_names,
    )
    log.info("  Total policy commands: %d", len(policy_commands))

    # --- Phase 3: Assemble and write ---
    all_commands = object_commands + policy_commands

    # Sort object commands by creation order (policy commands stay in order)
    def _cmd_sort_key(cmd: dict) -> int:
        obj_type = cmd["command"].replace("add-", "").replace("set-", "")
        return _type_sort_key(obj_type)

    object_commands.sort(key=_cmd_sort_key)
    all_commands = object_commands + policy_commands

    server_addr = getattr(client, "server", "unknown")
    if hasattr(client, "api_server_url"):
        server_addr = client.api_server_url.replace("https://", "").split("/")[0]

    doc = {
        "_meta": {
            "format_version": "1.0",
            "exported": datetime.datetime.now().isoformat(),
            "source_server": server_addr,
            "total_commands": len(all_commands),
            "total_objects": len(object_commands),
            "total_policy": len(policy_commands),
            "note": "Generated by CP API QA Tool export. "
                    "Import with --action import-config.",
        },
        "commands": all_commands,
    }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)

    log.info("Export written to: %s (%d commands)", output_path, len(all_commands))

    # --- Phase 4: Generate CLI batch files ---
    base_dir = os.path.dirname(output_path) or "."
    cli_dir = os.path.join(base_dir, "mgmt_cli")
    export_cli_commands(all_commands, cli_dir)

    clish_dir = os.path.join(base_dir, "gaia_clish")
    export_clish_commands(all_commands, clish_dir)

    return {
        "total_commands": len(all_commands),
        "total_objects": len(object_commands),
        "total_policy": len(policy_commands),
        "output_path": output_path,
    }
