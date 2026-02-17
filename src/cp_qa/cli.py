"""Command-line interface for cp-api-qa-tool.

Entry point for the ``cp-qa`` console command (registered via
``pyproject.toml``).  Orchestrates login, spec fetching, and
dispatching to QA or demo mode.

Usage::

    # QA mode (default) — full CRUD lifecycle
    cp-qa -m 10.0.0.1 -u admin

    # Demo mode — create all object types for policy building
    cp-qa -m 10.0.0.1 -u admin --mode demo --action create

    # Demo cleanup
    cp-qa -m 10.0.0.1 -u admin --mode demo --action cleanup

    # Debug output (all log levels printed to console)
    cp-qa -m 10.0.0.1 -u admin --debug

    # Dry-run — generate payloads without calling the API
    cp-qa -m 10.0.0.1 -u admin --dry-run --type host
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import shutil

from cp_qa import __version__
from cp_qa.client import APIClient
from cp_qa.constants import (
    API_SPEC_URL,
    DEFAULT_BLUEPRINT_PATH,
    DEFAULT_EXPORT_PATH,
    MANIFEST_PATH,
    NETWORK_OBJECTS_TYPES,
    QA_PAYLOADS_DIR,
    QA_RAW_DATA_PATH,
    QA_SUMMARY_REPORT_PATH,
)
from cp_qa.engine import APIQAEngine
from cp_qa.logging import configure as configure_logging
from cp_qa.logging import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Target resolution
# ---------------------------------------------------------------------------

def _resolve_target_types(
    engine: APIQAEngine, section: str
) -> list[tuple[str, dict]]:
    """Identify ``(obj_type, cmd_spec)`` pairs for a given section.

    Falls back to the manual :const:`NETWORK_OBJECTS_TYPES` list when
    section metadata is missing from the spec (common with v2.0.1+).

    Args:
        engine:  Initialised QA engine with a fetched spec.
        section: Section name to search (e.g. ``"Network Objects"``).

    Returns:
        List of ``(object_type_str, command_spec_dict)`` tuples.
    """
    cmds = engine.get_commands_by_section(section)
    target_types: list[tuple[str, dict]] = []

    is_all = section.lower() == "all"
    
    if is_all or (not cmds and section.lower() == "network objects"):
        if not is_all:
            log.info(
                "Section metadata missing in spec, using manual mapping "
                "for 'Network Objects'"
            )
        else:
            log.info("Targeting ALL supported object types across all sections")
            
        for obj_type in NETWORK_OBJECTS_TYPES:
            for cmd in engine.spec.get("commands", []):
                if cmd.get("name", {}).get("web") == f"add-{obj_type}":
                    target_types.append((obj_type, cmd))
                    break
    else:
        for cmd in cmds:
            name = cmd.get("name", {}).get("web", "")
            if name.startswith("add-"):
                obj_type = name.replace("add-", "")
                if obj_type in NETWORK_OBJECTS_TYPES:
                    target_types.append((obj_type, cmd))

    return target_types


# ---------------------------------------------------------------------------
# Mode handlers
# ---------------------------------------------------------------------------

def _run_qa_mode(
    engine: APIQAEngine,
    client: APIClient,
    target_types: list[tuple[str, dict]],
    dry_run: bool = False,
) -> None:
    """QA lifecycle: add -> set -> show -> delete per object type.

    Args:
        engine:       Initialised QA engine.
        client:       Authenticated API client.
        target_types: Object types to test.
        dry_run:      If True, only generate payloads without API calls.
    """
    if dry_run:
        _dry_run_payloads(engine, target_types)
        return

    for obj_type, cmd_spec in target_types:
        engine.run_lifecycle_test(obj_type, cmd_spec)

    engine.export_report(QA_RAW_DATA_PATH)
    engine.export_markdown_report(QA_SUMMARY_REPORT_PATH)
    engine.export_examples(QA_PAYLOADS_DIR)
    engine.export_per_type_reports(QA_PAYLOADS_DIR)

    log.info(
        "QA Run complete. Reports saved to %s and %s",
        QA_RAW_DATA_PATH,
        QA_SUMMARY_REPORT_PATH,
    )
    log.info("Per-type reports saved alongside payloads in %s", QA_PAYLOADS_DIR)
    client.publish()


def _run_demo_create(
    engine: APIQAEngine,
    client: APIClient,
    target_types: list[tuple[str, dict]],
) -> None:
    """Demo mode: create realistic topology, services, and policy.

    Based on the Ansible Dynamic Policy Demo project.  Creates a
    coherent lab environment with hosts, networks, groups, feeds,
    gateway, services, and a multi-layer access policy.
    """
    manifest: list[dict] = []

    # Phase 1: Network topology (hosts, networks, groups, feeds, gateway)
    log.info("=== PHASE 1: Network Topology ===")
    topo_entries = engine.create_demo_topology()
    manifest.extend(topo_entries)

    # Phase 2: Service objects + service groups
    log.info("=== PHASE 2: Service Objects ===")
    svc_entries = engine.create_demo_services()
    manifest.extend(svc_entries)
    log.info("Publishing Phase 2...")
    client.publish()

    # Phase 3: Policy package + DNS layer + Network layer rules
    log.info("=== PHASE 3: Security Policy ===")
    policy_entries = engine.create_demo_policy(manifest)
    manifest.extend(policy_entries)
    log.info("Publishing Phase 3...")
    client.publish()

    # Save manifest
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    obj_count = len([e for e in manifest if e.get("uid")])
    log.info("DEMO CREATE complete: %d objects created", obj_count)
    log.info("Manifest saved to %s", MANIFEST_PATH)
    log.info("Objects + policy are now available on the management server.")
    log.info("Run with '--mode demo --action cleanup' to delete everything.")


def _run_demo_cleanup(engine: APIQAEngine, client: APIClient) -> None:
    """Demo mode: delete everything created by demo/QA runs.

    Uses a two-phase approach:
      1. Load the manifest (if present) as the primary deletion list.
      2. Run a server-side discovery sweep for any DEMO_/QA_ objects
         not covered by the manifest (orphaned services, helpers, etc.).

    Retries up to 3 passes for stubborn objects.
    """
    # --- Phase 1: Load manifest (if available) ---
    manifest: list[dict] = []
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        log.info(
            "Loaded manifest with %d entries from %s",
            len(manifest),
            MANIFEST_PATH,
        )
    else:
        log.info("No manifest found — will use server-side discovery only.")

    # --- Phase 2: Server-side discovery sweep ---
    log.info("Running server-side discovery sweep...")
    discovered = engine.discover_demo_objects()

    # Merge: add any discovered objects not already in the manifest
    manifest_keys: set[tuple[str, str]] = {
        (e["type"], e["name"]) for e in manifest
    }
    merged_count = 0
    for entry in discovered:
        key = (entry["type"], entry["name"])
        if key not in manifest_keys:
            manifest.append(entry)
            manifest_keys.add(key)
            merged_count += 1
    if merged_count:
        log.info(
            "Discovery found %d additional objects not in manifest",
            merged_count,
        )

    if not manifest:
        log.info("Nothing to clean up — server is already clean.")
        return

    log.info("Total objects to delete: %d", len(manifest))

    # Discard other sessions to release object locks
    log.info("Discarding other sessions to release locks...")
    try:
        my_sid = client.headers.get("X-chkp-sid", "")
        sessions_res = client.run_command(
            "show-sessions", {"details-level": "full", "limit": 50}
        )
        for s in sessions_res.get("objects", []):
            if not isinstance(s, dict):
                continue
            s_uid = s.get("uid", "")
            if s_uid and s_uid != my_sid:
                try:
                    client.run_command("discard", {"uid": s_uid})
                    log.info("  Discarded session %s...", s_uid[:12])
                except Exception:
                    pass
    except Exception as exc:
        log.warning("  Could not enumerate sessions: %s", exc)

    # Discard own pending changes from previous runs
    try:
        client.run_command("discard", {})
        log.info("  Discarded own pending changes.")
    except Exception:
        pass

    # Protect infrastructure objects that cannot be safely recreated via API.
    # Gateways require interface topology + anti-spoofing that the API can't
    # fully automate, and checkpoint-host is the SMS itself.
    _PROTECTED_TYPES = {"simple-gateway", "simple-cluster", "checkpoint-host"}
    protected = [e for e in manifest if e["type"] in _PROTECTED_TYPES]
    if protected:
        log.info(
            "Protecting %d infrastructure objects from deletion: %s",
            len(protected),
            ", ".join(f'{e["name"]} ({e["type"]})' for e in protected),
        )
    manifest = [e for e in manifest if e["type"] not in _PROTECTED_TYPES]

    # Delete with retry (up to 3 passes)
    remaining = list(manifest)
    for pass_num in range(1, 4):
        if not remaining:
            break

        log.info("--- Cleanup pass %d (%d objects) ---", pass_num, len(remaining))
        result = engine.run_demo_cleanup(remaining)
        client.publish()

        if result["failed"] == 0:
            remaining = []
            break

        # Rebuild remaining from failures
        deleted_names: set[str] = set()
        for entry in remaining:
            name = entry["name"]
            obj_type = entry["type"]
            show_cmd = (
                "show-package" if obj_type == "package" else f"show-{obj_type}"
            )
            check = client.run_command(show_cmd, {"name": name})
            if "uid" not in check:
                deleted_names.add(name)

        remaining = [e for e in remaining if e["name"] not in deleted_names]
        if remaining:
            log.info("  %d objects still remain, retrying...", len(remaining))

    # Final verification sweep
    leftover = engine.discover_demo_objects()
    if leftover:
        log.warning(
            "%d objects still found on server after cleanup:", len(leftover)
        )
        for entry in leftover:
            log.warning("  %s: %s", entry["type"], entry["name"])
    else:
        log.info("Verification complete — server is clean.")

    # Remove manifest if cleanup succeeded
    if not remaining and os.path.exists(MANIFEST_PATH):
        os.remove(MANIFEST_PATH)
        log.info("Manifest removed. All demo objects have been cleaned up.")
    elif remaining:
        with open(MANIFEST_PATH, "w", encoding="utf-8") as fh:
            json.dump(remaining, fh, indent=2)
        log.warning(
            "%d objects could not be deleted. Manifest updated for retry.",
            len(remaining),
        )


def _run_push_blueprint(
    engine: APIQAEngine, client: APIClient, blueprint_path: str
) -> None:
    """Deploy a demo policy from a JSON blueprint file.

    Reads the blueprint and creates all topology objects, services, and
    policy rules on the management server.  Re-uses the same helper
    functions as ``--action create`` but sources everything from the
    JSON file instead of hardcoded definitions in demo.py.
    """
    if not os.path.exists(blueprint_path):
        log.error("Blueprint file not found: %s", blueprint_path)
        return

    with open(blueprint_path, "r", encoding="utf-8") as fh:
        bp = json.load(fh)

    log.info("Loaded blueprint from %s", blueprint_path)
    manifest: list[dict] = []

    from cp_qa.engine.demo import _add_demo_object, _add_rules
    import time as _time

    def _add_or_skip(obj_type: str, add_cmd: str, show_cmd: str,
                     payload: dict) -> list[dict]:
        """Add an object, or skip if it already exists on the server."""
        name = payload.get("name", "")
        existing = client.run_command(show_cmd, {"name": name})
        if "uid" in existing:
            log.info("  EXISTS %s (%s) — skipped", name, obj_type)
            return [{"type": obj_type, "name": name,
                     "uid": existing["uid"], "payload": {}}]
        obj = {"cmd": add_cmd, "type": obj_type, "payload": payload}
        return _add_demo_object(client, obj)

    # --- Phase 1: Topology ---
    topo = bp.get("topology", {})

    # Hosts
    for h in topo.get("hosts", []):
        payload = dict(h, **{"ignore-warnings": True})
        manifest.extend(_add_or_skip("host", "add-host", "show-host", payload))
    if topo.get("hosts"):
        client.publish()

    # Networks
    for n in topo.get("networks", []):
        payload = dict(n, **{"ignore-warnings": True, "ignore-errors": True})
        manifest.extend(_add_or_skip("network", "add-network", "show-network", payload))
    if topo.get("networks"):
        client.publish()

    # Groups
    for g in topo.get("groups", []):
        payload = dict(g, **{"ignore-warnings": True})
        manifest.extend(_add_or_skip("group", "add-group", "show-group", payload))

    # Network feeds
    for f in topo.get("network-feeds", []):
        payload = dict(f, **{"ignore-warnings": True, "ignore-errors": True})
        manifest.extend(_add_or_skip("network-feed", "add-network-feed",
                                     "show-network-feed", payload))

    # Gateways — never add pre-existing gateways to the manifest because
    # the API cannot fully recreate them (interface topology + anti-spoofing).
    for gw in topo.get("gateways", []):
        gw_name = gw.get("name", "")
        existing_gw = client.run_command("show-simple-gateway", {"name": gw_name})
        if "uid" in existing_gw:
            log.info("  EXISTS %s (simple-gateway) — skipped (protected)", gw_name)
        else:
            payload = dict(gw, **{"ignore-warnings": True, "ignore-errors": True})
            obj = {"cmd": "add-simple-gateway", "type": "simple-gateway", "payload": payload}
            manifest.extend(_add_demo_object(client, obj))

    client.publish()
    log.info("Topology deployed: %d objects", len(manifest))

    # --- Phase 2: Services ---
    svcs = bp.get("services", {})
    svc_count = 0

    type_cmd_map = {
        "service-tcp": "add-service-tcp",
        "service-udp": "add-service-udp",
        "service-icmp": "add-service-icmp",
        "service-sctp": "add-service-sctp",
        "service-other": "add-service-other",
    }
    type_show_map = {
        "service-tcp": "show-service-tcp",
        "service-udp": "show-service-udp",
        "service-icmp": "show-service-icmp",
        "service-sctp": "show-service-sctp",
        "service-other": "show-service-other",
    }
    for s in svcs.get("individual", []):
        svc_type = s.pop("type", "service-tcp")
        cmd = type_cmd_map.get(svc_type, f"add-{svc_type}")
        show_cmd = type_show_map.get(svc_type, f"show-{svc_type}")
        payload = dict(s, **{"ignore-warnings": True})
        s["type"] = svc_type  # restore for future reads
        manifest.extend(_add_or_skip(svc_type, cmd, show_cmd, payload))
        svc_count += 1

    for sg in svcs.get("groups", []):
        payload = dict(sg, **{"ignore-warnings": True, "ignore-errors": True})
        manifest.extend(_add_or_skip("service-group", "add-service-group",
                                      "show-service-group", payload))
        svc_count += 1

    client.publish()
    log.info("Services deployed: %d objects", svc_count)

    # --- Phase 3: Policy ---
    pol = bp.get("policy", {})
    pkg_def = pol.get("package", {})
    if not pkg_def:
        log.info("No policy section in blueprint — done.")
        _save_manifest(manifest)
        return

    # Create or find existing package (try show-package first)
    pkg_name = pkg_def["name"]
    pkg_created = False
    res: dict = {}

    # Check if package already exists
    res = client.run_command("show-package", {
        "name": pkg_name, "details-level": "full",
    })
    if "uid" in res:
        log.info("  Using existing package: %s", pkg_name)
    else:
        # Package doesn't exist — create it
        for attempt in range(3):
            res = client.run_command("add-package", {
                **pkg_def,
                "ignore-warnings": True,
            })
            if "uid" in res:
                pkg_created = True
                break
            msg = str(res.get("message", ""))
            if attempt < 2:
                log.warning("  RETRY package (attempt %d): %s", attempt + 1, msg)
                _time.sleep(5)
    if "uid" not in res:
        log.error("Failed to create/find package: %s", res.get("message", res))
        _save_manifest(manifest)
        return
    if pkg_created:
        log.info("  PASS Package created: %s", pkg_name)
        manifest.append({"type": "package", "name": pkg_name, "uid": res["uid"], "payload": {}})

    # Extract network layer name (handles both add-package and show-package)
    layers = res.get("access-layers", [])
    if isinstance(layers, dict):
        layers = layers.get("add", layers.get("objects", []))
        if not isinstance(layers, list):
            layers = [layers] if isinstance(layers, dict) else []
    net_layer = None
    if isinstance(layers, list) and layers:
        first = layers[0]
        net_layer = first.get("name") if isinstance(first, dict) else None
    if not net_layer:
        # Try common layer names for existing packages
        for candidate in [f"{pkg_name} Network", "Network", pkg_name]:
            check = client.run_command("show-access-layer", {"name": candidate})
            if "uid" in check:
                net_layer = candidate
                break
        if not net_layer:
            net_layer = f"{pkg_name} Network"
    log.info("  Using access layer: %s", net_layer)
    client.publish()

    # Apply layer settings (e.g. applications-and-url-filtering)
    layer_settings = pol.get("layer-settings", {})
    if layer_settings:
        set_res = client.run_command("set-access-layer", {
            "name": net_layer,
            **layer_settings,
            "ignore-warnings": True,
        })
        if "uid" in set_res:
            log.info("  Layer settings applied: %s", list(layer_settings.keys()))
        else:
            log.warning("  Could not apply layer settings: %s", set_res.get("message", ""))
        client.publish()

    # Delete the default "Cleanup rule" that Check Point auto-creates at
    # position 1 (Drop/Any/Any, Track: None).  If left in place it blocks
    # all traffic before our custom rules are evaluated.
    log.info("  Removing default Cleanup rule from %s...", net_layer)
    try:
        rb = client.run_command("show-access-rulebase", {
            "name": net_layer, "limit": 10, "use-object-dictionary": False,
        })
        for obj in rb.get("rulebase", []):
            if obj.get("type") == "access-rule" and obj.get("name") == "Cleanup rule":
                client.run_command("delete-access-rule", {
                    "uid": obj["uid"], "layer": net_layer,
                })
                log.info("    Deleted default Cleanup rule (uid: %s)", obj["uid"])
                break
        client.publish()
    except Exception as exc:
        log.warning("  Could not remove default Cleanup rule: %s", exc)

    # Create inline layers (skip if they already exist)
    for il in pol.get("inline-layers", []):
        il_name = il["name"]
        existing_il = client.run_command("show-access-layer", {"name": il_name})
        if "uid" in existing_il:
            log.info("  EXISTS inline layer: %s — skipped", il_name)
            manifest.append({"type": "access-layer", "name": il_name,
                             "uid": existing_il["uid"], "payload": {}})
        else:
            for attempt in range(3):
                il_payload = {
                    "name": il_name,
                    "add-default-rule": il.get("add-default-rule", True),
                    "color": il.get("color", "blue"),
                    "comments": il.get("comments", ""),
                    "ignore-warnings": True,
                }
                if "implicit-cleanup-action" in il:
                    il_payload["implicit-cleanup-action"] = il["implicit-cleanup-action"]
                il_res = client.run_command("add-access-layer", il_payload)
                if "uid" in il_res:
                    log.info("  PASS Inline layer: %s", il_name)
                    manifest.append({"type": "access-layer", "name": il_name,
                                     "uid": il_res["uid"], "payload": {}})
                    break
                if attempt < 2:
                    log.warning("  RETRY layer %s (attempt %d)", il_name, attempt + 1)
                    _time.sleep(3)
                else:
                    log.error("  FAIL Inline layer %s: %s", il_name, il_res.get("message", ""))

            client.publish()

            # Add rules for this inline layer (only if layer was just created)
            rules = []
            for r in il.get("rules", []):
                rules.append({
                    **{k: v for k, v in r.items() if k != "track"},
                    "layer": il_name,
                    "position": "bottom",
                    "track": {"type": r.get("track", "Log")},
                })
            if rules:
                _add_rules(client, rules, il_name)
                client.publish()

    # Network layer sections + rules (skip if rulebase already populated)
    net_layer_def = pol.get("network-layer", {})
    skip_rules = False
    if net_layer_def.get("sections"):
        rb_check = client.run_command("show-access-rulebase", {
            "name": net_layer, "limit": 5, "use-object-dictionary": False,
        })
        rb_objects = rb_check.get("rulebase", [])
        # If rulebase has access-section objects, rules are already deployed
        has_sections = any(
            obj.get("type") == "access-section" for obj in rb_objects
        )
        if has_sections:
            log.info("  Network layer already has sections — skipping rule creation")
            skip_rules = True

    if not skip_rules:
        net_items: list[dict] = []
        for section in net_layer_def.get("sections", []):
            net_items.append({
                "_section": True,
                "name": section["section"],
                "layer": net_layer,
                "position": "bottom",
            })
            for r in section.get("rules", []):
                item: dict = {
                    "name": r["name"],
                    "layer": net_layer,
                    "position": "bottom",
                    "source": r.get("source", "any"),
                    "destination": r.get("destination", "any"),
                    "service": r.get("service", "any"),
                    "action": r.get("action", "Drop"),
                    "track": {"type": r.get("track", "Log")},
                    "comments": r.get("comments", ""),
                }
                if "inline-layer" in r:
                    item["inline-layer"] = r["inline-layer"]
                if "ignore-errors" in r:
                    item["ignore-errors"] = r["ignore-errors"]
                net_items.append(item)

        if net_items:
            created = _add_rules(client, net_items, "Network Layer")
            log.info("Network layer: %d items created", created)

    client.publish()
    _save_manifest(manifest)
    log.info("Blueprint deployment complete.")
    log.info("Run with '--mode demo --action cleanup' to remove everything.")


def _run_capture_blueprint(engine: APIQAEngine, output_path: str) -> None:
    """Capture the live policy from the SMS and write a deployable blueprint.

    Reads the ``Standard`` policy package (all layers, sections, rules) and
    every object referenced in the rulebase, then writes a JSON blueprint
    file that can be re-deployed on any SMS via ``--action push-blueprint``.

    Args:
        engine:      Initialised :class:`APIQAEngine`.
        output_path: Destination path for the captured blueprint JSON.
    """
    log.info("=== CAPTURE BLUEPRINT: pulling from live SMS ===")

    blueprint = engine.capture_policy_blueprint(package_name="Standard")
    if not blueprint:
        log.error("Capture returned empty blueprint — check connection and package name.")
        return

    # Count objects for the summary log
    topo = blueprint.get("topology", {})
    svcs = blueprint.get("services", {})
    pol = blueprint.get("policy", {})
    net_sections = pol.get("network-layer", {}).get("sections", [])
    net_rules = sum(len(s.get("rules", [])) for s in net_sections)
    il_rules = sum(
        len(il.get("rules", [])) for il in pol.get("inline-layers", [])
    )

    log.info(
        "  Captured: %d hosts, %d networks, %d groups, %d feeds, %d gateways",
        len(topo.get("hosts", [])), len(topo.get("networks", [])),
        len(topo.get("groups", [])), len(topo.get("network-feeds", [])),
        len(topo.get("gateways", [])),
    )
    log.info(
        "  Services: %d individual, %d groups",
        len(svcs.get("individual", [])), len(svcs.get("groups", [])),
    )
    log.info(
        "  Policy: %d inline layers, %d inline rules, %d network rules across %d sections",
        len(pol.get("inline-layers", [])), il_rules, net_rules, len(net_sections),
    )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(blueprint, fh, indent=2)

    log.info("Blueprint written to: %s", output_path)
    log.info("Deploy with: cp-qa -m <server> -u admin --mode demo --action push-blueprint --blueprint %s", output_path)


def _run_export_config(engine: APIQAEngine, output_path: str) -> None:
    """Export all user-created objects and policies from the SMS.

    Enumerates every supported object type, transforms each into a
    ready-to-import ``add-*`` payload, and writes the result to a JSON
    file that can be replayed via ``--action import-config``.

    Args:
        engine:      Initialised :class:`APIQAEngine`.
        output_path: Destination path for the export JSON.
    """
    log.info("=== EXPORT CONFIG: reading from live SMS ===")
    result = engine.export_full_config(output_path=output_path)
    total = result.get("total_commands", 0)
    if total:
        log.info("Export complete: %d commands written to %s", total, output_path)
        log.info(
            "Import with: cp-qa -m <server> -u admin --mode demo "
            "--action import-config --export-path %s",
            output_path,
        )
    else:
        log.warning("Export produced 0 commands — check connection and server state.")


def _run_import_config(
    engine: APIQAEngine, config_path: str, dry_run: bool = False,
) -> None:
    """Import objects and policies from an export file.

    Replays ``add-*`` commands with idempotency checks (skips objects
    that already exist) and publishes between dependency phases.

    Args:
        engine:      Initialised :class:`APIQAEngine`.
        config_path: Path to the export JSON file.
        dry_run:     If True, validate without making API calls.
    """
    log.info("=== IMPORT CONFIG: replaying from %s ===", config_path)
    stats = engine.import_config(config_path=config_path, dry_run=dry_run)
    log.info(
        "Import result: %d created, %d skipped, %d failed",
        stats.get("created", 0),
        stats.get("skipped", 0),
        stats.get("failed", 0),
    )


def _save_manifest(manifest: list[dict]) -> None:
    """Save manifest to disk."""
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    count = len([e for e in manifest if e.get("uid")])
    log.info("Manifest saved (%d objects) to %s", count, MANIFEST_PATH)


def _dry_run_payloads(
    engine: APIQAEngine, target_types: list[tuple[str, dict]]
) -> None:
    """Generate and display payloads without calling the API.

    Useful for inspecting what the engine *would* send.
    """
    from cp_qa.engine.params import extract_params_from_obj
    from cp_qa.engine.payloads import generate_payloads
    from cp_qa.engine.spec import get_object_by_name
    from cp_qa.engine.type_defaults import apply_type_defaults

    for obj_type, cmd_spec in target_types:
        request_obj_name = cmd_spec.get("request")
        obj_def = get_object_by_name(engine.spec, request_obj_name)
        if not obj_def:
            log.warning("Could not find definition for %s", request_obj_name)
            continue

        parameters = extract_params_from_obj(obj_def)
        variants = generate_payloads(
            parameters, current_obj_type=obj_type, spec=engine.spec
        )

        for i, payload in enumerate(variants):
            payload["name"] = f"DRY_RUN_{obj_type.upper()}_{i}"
            apply_type_defaults(obj_type, payload, spec=engine.spec, current_obj_type=obj_type)

            log.info(
                "[DRY-RUN] %s variant %d:\n%s",
                obj_type,
                i,
                json.dumps(payload, indent=2),
            )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def load_env_file(path: str) -> None:
    """Load key=value pairs from a file into os.environ."""
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
        log.info("Loaded environment variables from %s", path)
    except Exception as e:
        log.warning("Failed to load .env file: %s", e)

def main() -> None:
    """Parse arguments and run the requested mode."""
    # Load .env if it exists (check config/ first, then root)
    if os.path.exists("config/.env"):
        load_env_file("config/.env")
    else:
        load_env_file(".env")

    parser = argparse.ArgumentParser(
        prog="cp-qa",
        description="Check Point API QA Tool (v%(prog)s) — "
        "self-healing CRUD lifecycle testing for the Management API",
        epilog=(
            "Examples:\n"
            "  cp-qa -m 10.0.0.1 -u admin                          # QA mode\n"
            "  cp-qa -m 10.0.0.1 -u admin --mode demo --action create\n"
            "  cp-qa -m 10.0.0.1 -u admin --mode demo --action cleanup\n"
            "  cp-qa -m 10.0.0.1 -u admin --mode demo --action push-blueprint\n"
            "  cp-qa ... --action push-blueprint --blueprint my_policy.json\n"
            "  cp-qa -m 10.0.0.1 -u admin --mode demo --action capture-blueprint\n"
            "  cp-qa ... --action capture-blueprint --blueprint blueprints/my_capture.json\n"
            "  cp-qa -m 10.0.0.1 -u admin --mode demo --action export-config\n"
            "  cp-qa ... --action export-config --export-path exports/my_backup.json\n"
            "  cp-qa ... --action import-config --export-path exports/my_backup.json\n"
            "  cp-qa -m 10.0.0.1 -u admin --debug                  # Verbose\n"
            "  cp-qa -m 10.0.0.1 -u admin --dry-run --type host    # No API calls\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # --- Connection ---
    conn = parser.add_argument_group("Connection")
    conn.add_argument(
        "-m", "--management",
        required=not os.environ.get("CP_MGMT_SERVER"),
        default=os.environ.get("CP_MGMT_SERVER"),
        help="Management Server IP or hostname (or set CP_MGMT_SERVER)",
    )
    conn.add_argument(
        "-u", "--user",
        default=os.environ.get("CP_MGMT_USER", "admin"),
        help="Username (default: admin, or set CP_MGMT_USER)",
    )
    conn.add_argument(
        "-p", "--password",
        help="Password (prompted securely if omitted)",
    )
    conn.add_argument(
        "-d", "--domain",
        default=os.environ.get("CP_MGMT_DOMAIN"),
        help="MDS domain name (or set CP_MGMT_DOMAIN)",
    )
    conn.add_argument(
        "--api-key",
        default=os.environ.get("CP_MGMT_API_KEY"),
        help="API key for key-based authentication (or set CP_MGMT_API_KEY)",
    )
    conn.add_argument(
        "--api-version",
        default=os.environ.get("CP_API_VERSION"),
        help="Override auto-detected API spec version (or set CP_API_VERSION)",
    )

    # --- Mode ---
    mode_grp = parser.add_argument_group("Mode")
    mode_grp.add_argument(
        "-s", "--section",
        default=os.environ.get("CP_QA_SECTION"),
        help="API section to test (or set CP_QA_SECTION; e.g. 'Network Objects', 'all')",
    )
    mode_grp.add_argument(
        "--mode",
        choices=["qa", "demo"],
        default=os.environ.get("CP_QA_MODE", "qa"),
        help="qa = full CRUD lifecycle, demo = create-all / cleanup-all (or set CP_QA_MODE)",
    )
    mode_grp.add_argument(
        "--action",
        choices=["create", "cleanup", "push-blueprint", "capture-blueprint",
                 "export-config", "import-config"],
        default=os.environ.get("CP_QA_ACTION", "create"),
        help="Demo mode action (or set CP_QA_ACTION)",
    )
    mode_grp.add_argument(
        "--blueprint",
        default=os.environ.get("CP_BLUEPRINT_PATH"),
        help="Path to demo policy blueprint JSON (or set CP_BLUEPRINT_PATH)",
    )
    mode_grp.add_argument(
        "--export-path",
        default=os.environ.get("CP_EXPORT_PATH"),
        help="Path for export/import JSON file (or set CP_EXPORT_PATH)",
    )
    mode_grp.add_argument(
        "--type",
        default=os.environ.get("CP_QA_TYPE"),
        help="Only test this specific object type (or set CP_QA_TYPE)",
    )

    # --- Debug ---
    _env_bool = lambda k: os.environ.get(k, "").lower() in ("1", "true", "yes")
    debug_grp = parser.add_argument_group("Debug")
    debug_grp.add_argument(
        "--debug",
        action="store_true",
        default=_env_bool("CP_QA_DEBUG"),
        help="Print DEBUG-level messages (or set CP_QA_DEBUG=true)",
    )
    debug_grp.add_argument(
        "--quiet",
        action="store_true",
        default=_env_bool("CP_QA_QUIET"),
        help="Suppress INFO messages (or set CP_QA_QUIET=true)",
    )
    debug_grp.add_argument(
        "--dry-run",
        action="store_true",
        default=_env_bool("CP_QA_DRY_RUN"),
        help="Generate payloads without calling the API (or set CP_QA_DRY_RUN=true)",
    )

    # --- Meta ---
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args()

    # Configure logging before anything else
    configure_logging(debug=args.debug, quiet=args.quiet)

    password = args.password or os.environ.get("CP_MGMT_PASSWORD") or (
        None if (args.api_key or args.dry_run) else getpass.getpass(f"Password for {args.user}: ")
    )

    # Prepare output directories
    if args.mode == "qa":
        if not args.type:
            if os.path.exists("output"):
                shutil.rmtree("output")
            os.makedirs("output", exist_ok=True)
        else:
            os.makedirs(QA_PAYLOADS_DIR, exist_ok=True)
            type_dir = os.path.join(QA_PAYLOADS_DIR, args.type)
            if os.path.exists(type_dir):
                shutil.rmtree(type_dir)
    else:
        os.makedirs("output", exist_ok=True)

    # 1. Login
    client = APIClient(
        args.management, args.user, password,
        api_key=args.api_key, domain=args.domain,
    )

    # Determine spec URL: prioritize server-fetched after login
    local_spec = os.path.join(os.getcwd(), "config", "openapi.json")
    if not os.path.exists(local_spec):
        local_spec = os.path.join(os.getcwd(), "openapi.json")
    
    # 1. Login (if not dry-run) / Spec Fetching
    api_version = "2.0"
    engine: APIQAEngine | None = None
    
    version_source = "auto"
    if not args.dry_run:
        sid, api_version = client.login()
        if args.api_version:
            log.info(
                "Authenticated to %s (server=%s, overriding to user-specified=%s)",
                args.management, api_version, args.api_version,
            )
            api_version = args.api_version
            version_source = "user"
        else:
            log.info("Authenticated to %s (Detected API Version: %s)", args.management, api_version)

        # Use documentation reconstruction (static + dynamic) if possible
        spec_url_base = f"https://sc1.checkpoint.com/documents/latest/APIs/data/v{api_version}/"
        engine = APIQAEngine(client, spec_url_base, api_version=api_version, version_source=version_source)
        engine.spec = engine.reconstruct_full_spec(spec_url_base, api_version)
        
        if not engine.spec:
             log.warning("Falling back to server-provided dynamic spec.")
             dynamic_spec_url = f"https://{args.management}/web_api/v{api_version}/apis.json"
             engine.spec_url = dynamic_spec_url
             if not engine.fetch_spec():
                 log.error("Failed to fetch API spec from server.")
                 return
        log.info("Final spec URL in use: %s", engine.spec_url)
    else:
        if args.api_version:
            api_version = args.api_version
            version_source = "user"
            log.info("[DRY-RUN] Using user-specified API version: %s", api_version)
        # Dry-run uses local spec if available, otherwise default URL
        if os.path.exists(local_spec):
            spec_url = f"file:///{local_spec.replace(os.sep, '/')}"
            log.info("[DRY-RUN] Using local openapi.json: %s", spec_url)
        else:
            spec_url = API_SPEC_URL
            log.info("[DRY-RUN] Using default spec URL: %s", spec_url)

        engine = APIQAEngine(client, spec_url, api_version=api_version, version_source=version_source)
        if not engine.fetch_spec():
            return

    try:
        # 3. Resolve target object types
        section = args.section
        if not section:
            # Default: 'all' for demo mode, 'Network Objects' for QA mode
            section = "all" if args.mode == "demo" else "Network Objects"
            
        log.info("Targeting section: %s", section)
        target_types = _resolve_target_types(engine, section)

        if args.type:
            target_types = [t for t in target_types if t[0] == args.type]
            if not target_types:
                log.error(
                    "Type '%s' not found in supported types for section '%s'",
                    args.type,
                    args.section,
                )
                return

        log.info(
            "Found %d target object types: %s",
            len(target_types),
            [t[0] for t in target_types],
        )

        # 4. Execute
        if args.mode == "qa":
            _run_qa_mode(engine, client, target_types, dry_run=args.dry_run)
        elif args.mode == "demo":
            if args.dry_run and args.action not in ("import-config",):
                log.warning("--dry-run is only supported in QA mode and import-config.")
                return
            if args.action == "create":
                _run_demo_create(engine, client, target_types)
            elif args.action == "cleanup":
                _run_demo_cleanup(engine, client)
            elif args.action == "push-blueprint":
                bp_path = args.blueprint or DEFAULT_BLUEPRINT_PATH
                _run_push_blueprint(engine, client, bp_path)
            elif args.action == "capture-blueprint":
                bp_path = args.blueprint or DEFAULT_BLUEPRINT_PATH
                _run_capture_blueprint(engine, bp_path)
            elif args.action == "export-config":
                exp_path = args.export_path or DEFAULT_EXPORT_PATH
                _run_export_config(engine, exp_path)
            elif args.action == "import-config":
                exp_path = args.export_path or DEFAULT_EXPORT_PATH
                _run_import_config(engine, exp_path, dry_run=args.dry_run)

    finally:
        if not args.dry_run:
            # Always discard pending changes before logout to avoid
            # leaving orphan sessions with uncommitted state.
            try:
                client.run_command("discard", {})
            except Exception:
                pass
            client.logout()


if __name__ == "__main__":
    main()
