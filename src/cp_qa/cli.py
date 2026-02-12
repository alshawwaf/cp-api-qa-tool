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
    MANIFEST_PATH,
    NETWORK_OBJECTS_TYPES,
    QA_EXAMPLES_DIR,
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

    if not cmds and section.lower() == "network objects":
        log.info(
            "Section metadata missing in spec, using manual mapping "
            "for 'Network Objects'"
        )
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
    engine.export_examples(QA_EXAMPLES_DIR)
    engine.export_per_type_reports(QA_EXAMPLES_DIR)

    log.info(
        "QA Run complete. Reports saved to %s and %s",
        QA_RAW_DATA_PATH,
        QA_SUMMARY_REPORT_PATH,
    )
    log.info("Per-type reports saved alongside examples in %s", QA_EXAMPLES_DIR)
    client.publish()


def _run_demo_create(
    engine: APIQAEngine,
    client: APIClient,
    target_types: list[tuple[str, dict]],
) -> None:
    """Demo mode: create ALL objects, services, and policy."""
    manifest: list[dict] = []

    # Phase 1: Network objects
    log.info("=== PHASE 1: Network Objects ===")
    for obj_type, cmd_spec in target_types:
        entries = engine.run_demo_create(obj_type, cmd_spec)
        manifest.extend(entries)
    log.info("Publishing Phase 1...")
    client.publish()

    # Phase 2: Service objects
    log.info("=== PHASE 2: Service Objects ===")
    svc_entries = engine.create_demo_services()
    manifest.extend(svc_entries)
    log.info("Publishing Phase 2...")
    client.publish()

    # Phase 3: Policy package + recommended access rules
    log.info("=== PHASE 3: Recommended Policy ===")
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
    # Load .env if it exists
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
        default=None,
        help="MDS domain name (optional)",
    )
    conn.add_argument(
        "--api-key",
        default=None,
        help="API key for key-based authentication (replaces user/password)",
    )

    # --- Mode ---
    mode_grp = parser.add_argument_group("Mode")
    mode_grp.add_argument(
        "-s", "--section",
        default="Network Objects",
        help="API section to test (default: 'Network Objects')",
    )
    mode_grp.add_argument(
        "--mode",
        choices=["qa", "demo"],
        default="qa",
        help="qa = full CRUD lifecycle, demo = create-all / cleanup-all",
    )
    mode_grp.add_argument(
        "--action",
        choices=["create", "cleanup"],
        default="create",
        help="Demo mode action (default: create)",
    )
    mode_grp.add_argument(
        "--type",
        help="Only test this specific object type (e.g. host, network)",
    )

    # --- Debug ---
    debug_grp = parser.add_argument_group("Debug")
    debug_grp.add_argument(
        "--debug",
        action="store_true",
        help="Print DEBUG-level messages to the console",
    )
    debug_grp.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress INFO messages (only show warnings and errors)",
    )
    debug_grp.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate payloads and print them without calling the API",
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

    # Prepare report directories
    if args.mode == "qa":
        if not args.type:
            if os.path.exists("reports"):
                shutil.rmtree("reports")
            os.makedirs("reports", exist_ok=True)
        else:
            os.makedirs("reports/examples", exist_ok=True)
            type_dir = os.path.join("reports/examples", args.type)
            if os.path.exists(type_dir):
                shutil.rmtree(type_dir)
    else:
        os.makedirs("reports", exist_ok=True)

    # 1. Login
    client = APIClient(
        args.management, args.user, password,
        api_key=args.api_key, domain=args.domain,
    )

    # Determine spec URL: prioritize server-fetched after login
    local_spec = os.path.join(os.getcwd(), "openapi.json")
    
    # 1. Login (if not dry-run)
    api_version = "2.1" # Default fallback
    if not args.dry_run:
        sid, api_version = client.login()
        log.info(
            "Authenticated to %s (Detected API Version: %s)",
            args.management,
            api_version,
        )
        
        dynamic_spec_url = (
            f"https://sc1.checkpoint.com/documents/latest/APIs/"
            f"data/v{api_version}/dynamic/apis.json"
        )
        log.info("Using dynamic spec URL: %s", dynamic_spec_url)
    else:
        # Dry-run uses local spec if available, otherwise default URL
        if os.path.exists(local_spec):
            dynamic_spec_url = f"file:///{local_spec.replace(os.sep, '/')}"
            log.info("[DRY-RUN] Using local openapi.json: %s", dynamic_spec_url)
        else:
            dynamic_spec_url = API_SPEC_URL
            log.info("[DRY-RUN] Using default spec URL: %s", dynamic_spec_url)

    log.info("Final spec URL in use: %s", dynamic_spec_url)

    try:
        # 2. Initialise QA engine
        engine = APIQAEngine(client, dynamic_spec_url, api_version=api_version)
        if not engine.fetch_spec():
            return

        # 3. Resolve target object types
        log.info("Targeting section: %s", args.section)
        target_types = _resolve_target_types(engine, args.section)

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
            if args.dry_run:
                log.warning("--dry-run is only supported in QA mode.")
                return
            if args.action == "create":
                _run_demo_create(engine, client, target_types)
            elif args.action == "cleanup":
                _run_demo_cleanup(engine, client)

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
