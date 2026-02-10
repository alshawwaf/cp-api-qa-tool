import argparse
import getpass
from api_client import API_client
from api_qa_engine import APIQAEngine
from logger_main import log

API_SPEC_URL = "https://sc1.checkpoint.com/documents/latest/APIs/data/v2.1/dynamic/apis.json"

def main():
    parser = argparse.ArgumentParser(description="Check Point API QA Tester (v2.1+)")
    parser.add_argument("-m", "--management", required=True, help="Management Server IP")
    parser.add_argument("-u", "--user", default="admin", help="Username")
    parser.add_argument("-p", "--password", help="Password (secure prompt if omitted)")
    parser.add_argument("-s", "--section", default="Network Objects", help="API Section to test")
    
    args = parser.parse_args()
    password = args.password or getpass.getpass(f"Password for {args.user}: ")

    # 0. Fresh Start: Wipe reports folder
    import shutil
    import os
    if os.path.exists('reports'):
        shutil.rmtree('reports')
    os.makedirs('reports', exist_ok=True)

    # 1. Initialize Client & Login
    client = API_client(args.management, args.user, password)
    sid, api_version = client.login()
    log.info(f"Authenticated to {args.management} (Detected API Version: {api_version})")

    # Construct dynamic spec URL: e.g. v2.1, v1.9, etc.
    dynamic_spec_url = f"https://sc1.checkpoint.com/documents/latest/APIs/data/v{api_version}/dynamic/apis.json"
    log.info(f"Using dynamic spec URL: {dynamic_spec_url}")

    try:
        # 2. Initialize QA Engine
        engine = APIQAEngine(client, dynamic_spec_url)
        if not engine.fetch_spec():
            return

        # 3. Filter Commands for the requested section
        log.info(f"Targeting section: {args.section}")
        cmds = engine.get_commands_by_section(args.section)
        
        # Manual mapping for "Network Objects" if dynamic detection is empty
        NETWORK_OBJECTS_TYPES = [
            # Core Network Objects (Phase 1 — verified)
            'host', 'network', 'group', 'address-range',
            'multicast-address-range', 'group-with-exclusion',
            'dns-domain', 'wildcard',
            # Network Objects (Phase 2)
            'security-zone', 'dynamic-object', 'tag',
            'time', 'time-group',
            'gsn-handover-group',
            'network-feed',
            # Gateways & Servers
            'simple-gateway', 'simple-cluster',
            'checkpoint-host', 'interoperable-device',
        ]

        # Identify object types in this section (look for add-X commands)
        target_types = []
        
        # If dynamic section match fails, and user asked for Network Objects, use manual list
        if not cmds and args.section.lower() == "network objects":
            log.info("Section metadata missing in spec, using manual mapping for 'Network Objects'")
            for obj_type in NETWORK_OBJECTS_TYPES:
                # Find the add-X command spec in the global command list
                for cmd in engine.spec.get('commands', []):
                    if cmd.get('name', {}).get('web') == f"add-{obj_type}":
                        target_types.append((obj_type, cmd))
                        break
        else:
            for cmd in cmds:
                name = cmd.get('name', {}).get('web', '')
                if name.startswith('add-'):
                    obj_type = name.replace('add-', '')
                    # For safety in the pilot, only allow known good types
                    if obj_type in NETWORK_OBJECTS_TYPES:
                        target_types.append((obj_type, cmd))

        log.info(f"Found {len(target_types)} target object types for QA: {[t[0] for t in target_types]}")

        # 4. Run Lifecycle Tests
        for obj_type, cmd_spec in target_types:
            engine.run_lifecycle_test(obj_type, cmd_spec)

        # 5. Export results to FIXED filenames to avoid confusion
        report_path = "reports/QA_RAW_DATA.json"
        md_report_path = "reports/QA_SUMMARY_REPORT.md"
        examples_dir = "reports/examples"
        engine.export_report(report_path)
        engine.export_markdown_report(md_report_path)
        engine.export_examples(examples_dir)

        log.info(f"QA Run complete. Reports saved to {report_path} and {md_report_path}")
        client.publish()

    finally:
        client.logout()

if __name__ == "__main__":
    main()
