#!/usr/bin/env python3
"""Clean deploy: wipe all DEMO_ objects then create a fresh demo with policy.

This is a standalone diagnostic script that bypasses the main QA engine
to perform a direct, step-by-step deploy.  Useful when the engine-based
demo mode encounters issues and you need fine-grained control.

Usage::

    python scripts/clean_deploy.py -m 10.0.0.1 -u admin -p <password>
    python scripts/clean_deploy.py -m 10.0.0.1 -u admin  # prompts for password

Environment variables (fallbacks when flags are omitted):
    CP_MGMT_SERVER    Management Server IP
    CP_MGMT_USER      Username (default: admin)
    CP_MGMT_PASSWORD  Password (prompted if not set)
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import signal
import sys
import time

import requests

requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]

# Allow clean Ctrl+C
signal.signal(signal.SIGINT, signal.SIG_DFL)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Wipe all DEMO_ objects and deploy a fresh demo environment",
    )
    parser.add_argument(
        "-m", "--management",
        default=os.environ.get("CP_MGMT_SERVER"),
        help="Management Server IP (or set CP_MGMT_SERVER)",
    )
    parser.add_argument(
        "-u", "--user",
        default=os.environ.get("CP_MGMT_USER", "admin"),
        help="Username (default: admin, or set CP_MGMT_USER)",
    )
    parser.add_argument(
        "-p", "--password",
        default=os.environ.get("CP_MGMT_PASSWORD"),
        help="Password (or set CP_MGMT_PASSWORD; prompted if omitted)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print full API responses for debugging",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def api(base_url: str, sid: str, cmd: str, payload: dict | None = None) -> tuple[int, dict]:
    """Execute a single API command and return (status_code, body)."""
    headers = {"Content-Type": "application/json", "X-chkp-sid": sid}
    resp = requests.post(
        base_url + cmd,
        json=payload or {},
        headers=headers,
        verify=False,
        timeout=300,
    )
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, {"message": resp.text[:200]}


def publish(base_url: str, sid: str) -> bool:
    """Publish pending changes, polling for async task completion."""
    code, body = api(base_url, sid, "publish")
    if code == 200 and isinstance(body, dict) and body.get("task-id"):
        task_id = body["task-id"]
        for _ in range(60):
            time.sleep(2)
            _, tr = api(base_url, sid, "show-task", {"task-id": task_id, "details-level": "full"})
            tasks = tr.get("tasks", []) if isinstance(tr, dict) else []
            if tasks and tasks[0].get("status") in ("succeeded", "failed"):
                ok = tasks[0]["status"] == "succeeded"
                print(f"  Publish {'OK' if ok else 'FAILED'}")
                return ok
        print("  Publish timed out")
        return False
    elif code == 200:
        print("  Publish OK")
        return True
    else:
        errors = body.get("errors", []) if isinstance(body, dict) else []
        err_msgs = [e.get("message", "") for e in errors if isinstance(e, dict)]
        print(f"  Publish FAILED ({code}): {'; '.join(err_msgs) or str(body)[:200]}")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    if not args.management:
        print("Error: --management is required (or set CP_MGMT_SERVER)", file=sys.stderr)
        sys.exit(1)

    password = args.password or getpass.getpass(f"Password for {args.user}: ")
    base_url = f"https://{args.management}/web_api/"

    # ======== STEP 1: Login + Discard ========
    print("=" * 60)
    print("STEP 1: Login + Discard")
    _, lr = api(base_url, "", "login", {"user": args.user, "password": password})
    sid = lr["sid"]
    print(f"  SID: {sid[:16]}...")
    api(base_url, sid, "discard")
    print("  Session discarded")

    # ======== STEP 2: Find and delete ALL DEMO_ objects ========
    print("\nSTEP 2: Find and delete ALL DEMO_ objects")

    search_types = [
        ("packages", "package", "delete-package"),
        ("service-groups", "service-group", "delete-service-group"),
        ("groups-with-exclusion", None, None),
        ("vpn-communities-meshed", "vpn-community-meshed", "delete-vpn-community-meshed"),
        ("vpn-communities-star", "vpn-community-star", "delete-vpn-community-star"),
        ("time-groups", "time-group", "delete-time-group"),
        ("groups", "group", "delete-group"),
        ("hosts", "host", "delete-host"),
        ("networks", "network", "delete-network"),
        ("wildcards", "wildcard", "delete-wildcard"),
        ("address-ranges", "address-range", "delete-address-range"),
        ("multicast-address-ranges", "multicast-address-range", "delete-multicast-address-range"),
        ("dns-domains", "dns-domain", "delete-dns-domain"),
        ("security-zones", "security-zone", "delete-security-zone"),
        ("dynamic-objects", "dynamic-object", "delete-dynamic-object"),
        ("tags", "tag", "delete-tag"),
        ("times", "time", "delete-time"),
        ("network-feeds", "network-feed", "delete-network-feed"),
        ("services-tcp", "service-tcp", "delete-service-tcp"),
        ("services-udp", "service-udp", "delete-service-udp"),
        ("services-icmp", "service-icmp", "delete-service-icmp"),
        ("simple-gateways", "simple-gateway", "delete-simple-gateway"),
        ("simple-clusters", "simple-cluster", "delete-simple-cluster"),
        ("checkpoint-hosts", "checkpoint-host", "delete-checkpoint-host"),
        ("gsn-handover-groups", "gsn-handover-group", "delete-gsn-handover-group"),
        ("interoperable-devices", "interoperable-device", "delete-interoperable-device"),
    ]

    total_deleted = 0
    for show_cmd, obj_type, del_cmd in search_types:
        if obj_type is None:
            continue

        cmds_to_try = [f"show-{show_cmd}", f"show-{obj_type}s", f"show-{obj_type}"]
        for cmd in cmds_to_try:
            try:
                _, res = api(base_url, sid, cmd, {"limit": 100, "details-level": "standard"})
                if not isinstance(res, dict):
                    continue

                obj_list = []
                for key in ["objects", "packages", "vpn-communities"]:
                    if key in res:
                        obj_list = res[key]
                        break

                if not obj_list:
                    continue

                for o in obj_list:
                    name = o.get("name", "") if isinstance(o, dict) else ""
                    uid = o.get("uid", "") if isinstance(o, dict) else ""

                    if name.startswith("DEMO_") or name.startswith(".demo"):
                        _, dr = api(base_url, sid, del_cmd, {"uid": uid, "ignore-warnings": True, "ignore-errors": True})
                        ok = isinstance(dr, dict) and ("uid" in dr or dr.get("message") == "OK")
                        status = "OK" if ok else f"FAIL {dr.get('message', '')[:60]}"
                        print(f"  {status} delete {obj_type}: {name}")
                        if ok:
                            total_deleted += 1
            except Exception:
                pass

    print(f"\n  Deleted {total_deleted} objects")
    if total_deleted > 0:
        print("  Publishing deletions...")
        publish(base_url, sid)

    # ======== STEP 3: Verify clean state ========
    print("\nSTEP 3: Verify clean state")
    clean = True
    for show_cmd, obj_type, _ in search_types:
        if obj_type is None:
            continue
        cmds_to_try = [f"show-{show_cmd}", f"show-{obj_type}s", f"show-{obj_type}"]
        for cmd in cmds_to_try:
            try:
                _, res = api(base_url, sid, cmd, {"limit": 100, "details-level": "standard"})
                if not isinstance(res, dict):
                    continue

                obj_list = []
                for key in ["objects", "packages", "vpn-communities"]:
                    if key in res:
                        obj_list = res[key]
                        break

                demos = [
                    o.get("name")
                    for o in obj_list
                    if isinstance(o, dict)
                    and (o.get("name", "").startswith("DEMO_") or o.get("name", "").startswith(".demo"))
                ]
                if demos:
                    print(f"  WARNING: Still found {obj_type}: {demos}")
                    clean = False
                    break
            except Exception:
                pass

    if clean:
        print("  Server is clean — no DEMO_ objects found")
    else:
        print("  Some objects remain. Aborting deploy.")
        api(base_url, sid, "logout")
        sys.exit(1)

    # ======== STEP 4: Create network objects ========
    print("\n" + "=" * 60)
    print("STEP 4: Create network objects (one at a time + publish)")

    create_objects = [
        ("add-host", "host", {"name": "DEMO_HOST_1", "ip-address": "10.100.1.134",
         "color": "blue", "comments": "Demo host", "ignore-warnings": True, "ignore-errors": True}),
        ("add-network", "network", {"name": "DEMO_NETWORK_1", "subnet": "10.100.0.0", "mask-length": 24,
         "color": "green", "comments": "Demo network", "ignore-warnings": True, "ignore-errors": True}),
        ("add-group", "group", {"name": "DEMO_GROUP_1", "color": "red",
         "comments": "Demo group", "ignore-warnings": True, "ignore-errors": True}),
        ("add-address-range", "address-range", {"name": "DEMO_ADDRESS_RANGE_1",
         "ip-address-first": "10.100.1.10", "ip-address-last": "10.100.1.30",
         "color": "orange", "comments": "Demo address range", "ignore-warnings": True, "ignore-errors": True}),
        ("add-multicast-address-range", "multicast-address-range", {"name": "DEMO_MULTICAST_ADDRESS_RANGE_1",
         "ip-address-first": "224.0.1.10", "ip-address-last": "224.0.1.30",
         "color": "cyan", "comments": "Demo multicast range", "ignore-warnings": True, "ignore-errors": True}),
        ("add-dns-domain", "dns-domain", {"name": ".demo.example.com", "is-sub-domain": False,
         "color": "dark green", "comments": "Demo DNS domain", "ignore-warnings": True, "ignore-errors": True}),
        ("add-wildcard", "wildcard", {"name": "DEMO_WILDCARD_1",
         "ipv4-address": "10.100.1.0", "ipv4-mask-wildcard": "0.0.0.255",
         "color": "yellow", "comments": "Demo wildcard", "ignore-warnings": True, "ignore-errors": True}),
        ("add-security-zone", "security-zone", {"name": "DEMO_SECURITY_ZONE_1",
         "color": "magenta", "comments": "Demo security zone", "ignore-warnings": True, "ignore-errors": True}),
        ("add-dynamic-object", "dynamic-object", {"name": "DEMO_DYNAMIC_OBJECT_1",
         "color": "coral", "comments": "Demo dynamic object", "ignore-warnings": True, "ignore-errors": True}),
        ("add-tag", "tag", {"name": "DEMO_TAG_1", "color": "pink",
         "comments": "Demo tag", "ignore-warnings": True, "ignore-errors": True}),
        ("add-time", "time", {"name": "DEMO_TIME_1", "start-now": True, "end-never": True,
         "color": "orchid", "comments": "Demo time object", "ignore-warnings": True, "ignore-errors": True}),
        ("add-network-feed", "network-feed", {"name": "DEMO_NETWORK_FEED_1",
         "feed-url": "https://secureupdates.checkpoint.com/IP-list/TOR.txt",
         "feed-format": "Flat List", "feed-type": "IP Address",
         "color": "gold", "comments": "Demo TOR exit nodes feed", "ignore-warnings": True, "ignore-errors": True}),
        ("add-simple-gateway", "simple-gateway", {"name": "DEMO_SIMPLE_GATEWAY_1",
         "ipv4-address": "10.100.99.160", "version": "R81.10", "vpn": True,
         "color": "red", "comments": "Demo gateway", "ignore-warnings": True, "ignore-errors": True}),
        ("add-checkpoint-host", "checkpoint-host", {"name": "DEMO_CHECKPOINT_HOST_1",
         "ipv4-address": "10.100.98.188",
         "color": "magenta", "comments": "Demo checkpoint host", "ignore-warnings": True, "ignore-errors": True}),
        ("add-interoperable-device", "interoperable-device", {"name": "DEMO_INTEROPERABLE_DEVICE_1",
         "ipv4-address": "10.100.97.164",
         "color": "dark blue", "comments": "Demo interop device", "ignore-warnings": True, "ignore-errors": True}),
    ]

    manifest = []
    for cmd, otype, payload in create_objects:
        name = payload["name"]
        print(f"  {otype}: {name}... ", end="", flush=True)
        code, body = api(base_url, sid, cmd, payload)
        if isinstance(body, dict) and "uid" in body:
            print(f"OK (uid: {body['uid'][:10]})")
            manifest.append({"type": otype, "name": name, "uid": body["uid"]})
        else:
            msg = body.get("message", body) if isinstance(body, dict) else body
            print(f"FAIL {str(msg)[:80]}")

    print(f"\n  Created {len(manifest)}/{len(create_objects)} objects")
    print("  Publishing infrastructure...")
    pub_ok = publish(base_url, sid)
    if not pub_ok:
        print("  Publish failed! Stopping.")
        api(base_url, sid, "logout")
        sys.exit(1)

    # ======== STEP 4.5: VPN communities ========
    print("\nSTEP 4.5: Create VPN communities (after infra publish)")
    vpn_communities = [
        ("add-vpn-community-meshed", "vpn-community-meshed", {"name": "DEMO_VPN_MESH",
         "gateways": ["DEMO_SIMPLE_GATEWAY_1"], "encryption-method": "prefer ikev2 but support ikev1",
         "encryption-suite": "custom", "color": "blue",
         "comments": "Demo meshed VPN", "ignore-warnings": True, "ignore-errors": True}),
        ("add-vpn-community-star", "vpn-community-star", {"name": "DEMO_VPN_STAR",
         "center-gateways": ["DEMO_SIMPLE_GATEWAY_1"], "satellite-gateways": ["DEMO_INTEROPERABLE_DEVICE_1"],
         "encryption-method": "prefer ikev2 but support ikev1", "encryption-suite": "custom",
         "color": "blue", "comments": "Demo star VPN", "ignore-warnings": True, "ignore-errors": True}),
    ]

    for cmd, otype, payload in vpn_communities:
        name = payload["name"]
        print(f"  {otype}: {name}... ", end="", flush=True)
        code, body = api(base_url, sid, cmd, payload)
        if isinstance(body, dict) and "uid" in body:
            print("OK")
            manifest.append({"type": otype, "name": name, "uid": body["uid"]})
        else:
            msg = body.get("message", body) if isinstance(body, dict) else body
            print(f"FAIL {str(msg)[:80]}")

    print("  Publishing VPN communities...")
    publish(base_url, sid)

    # ======== STEP 5: Services ========
    print("\nSTEP 5: Create service objects")

    services = [
        ("add-service-tcp", "service-tcp", {"name": "DEMO_SVC_HTTP", "port": "80", "color": "red",
         "comments": "Demo HTTP", "ignore-warnings": True}),
        ("add-service-tcp", "service-tcp", {"name": "DEMO_SVC_HTTPS", "port": "443", "color": "red",
         "comments": "Demo HTTPS", "ignore-warnings": True}),
        ("add-service-tcp", "service-tcp", {"name": "DEMO_SVC_SSH", "port": "22", "color": "orange",
         "comments": "Demo SSH", "ignore-warnings": True}),
        ("add-service-tcp", "service-tcp", {"name": "DEMO_SVC_SMTP", "port": "25", "color": "yellow",
         "comments": "Demo SMTP", "ignore-warnings": True}),
        ("add-service-udp", "service-udp", {"name": "DEMO_SVC_DNS", "port": "53", "color": "blue",
         "comments": "Demo DNS", "ignore-warnings": True}),
        ("add-service-icmp", "service-icmp", {"name": "DEMO_SVC_PING", "icmp-type": 8, "color": "aquamarine",
         "comments": "Demo ICMP Echo", "ignore-warnings": True}),
    ]

    for cmd, otype, payload in services:
        name = payload["name"]
        print(f"  {otype}: {name}... ", end="", flush=True)
        code, body = api(base_url, sid, cmd, payload)
        if isinstance(body, dict) and "uid" in body:
            print("OK")
            manifest.append({"type": otype, "name": name, "uid": body["uid"]})
        else:
            msg = body.get("message", body) if isinstance(body, dict) else body
            print(f"FAIL {str(msg)[:80]}")

    # Service group
    print(f"  service-group: DEMO_SVC_WEB_GROUP... ", end="", flush=True)
    code, body = api(base_url, sid, "add-service-group", {
        "name": "DEMO_SVC_WEB_GROUP",
        "members": ["DEMO_SVC_HTTP", "DEMO_SVC_HTTPS"], "color": "red",
        "comments": "Demo web services", "ignore-warnings": True,
    })
    if isinstance(body, dict) and "uid" in body:
        print("OK")
        manifest.append({"type": "service-group", "name": "DEMO_SVC_WEB_GROUP", "uid": body["uid"]})
    else:
        print(f"FAIL {body.get('message', '')[:80]}")

    print("  Publishing services...")
    pub_ok = publish(base_url, sid)
    if not pub_ok:
        print("  Publish failed! Stopping.")
        api(base_url, sid, "logout")
        sys.exit(1)

    # ======== STEP 6: Policy package ========
    print("\nSTEP 6: Create policy package")
    code, body = api(base_url, sid, "add-package", {
        "name": "DEMO_Policy", "access": True,
        "threat-prevention": False,
        "comments": "CP recommended policy — API QA Tool demo",
    })
    if isinstance(body, dict) and "uid" in body:
        print("  DEMO_Policy created")
        manifest.append({"type": "package", "name": "DEMO_Policy", "uid": body["uid"]})
    else:
        print(f"  FAIL {body.get('message', '')[:100]}")
        api(base_url, sid, "logout")
        sys.exit(1)

    print("  Publishing package...")
    pub_ok = publish(base_url, sid)
    if not pub_ok:
        print("  Publish failed!")
        api(base_url, sid, "logout")
        sys.exit(1)

    # ======== STEP 7: Access rules ========
    print("\nSTEP 7: Create access rules (CP recommended policy)")

    layer = "DEMO_Policy Network"
    rules = [
        {"name": "Management Access", "source": "DEMO_NETWORK_1", "destination": "DEMO_CHECKPOINT_HOST_1",
         "service": ["DEMO_SVC_HTTPS", "DEMO_SVC_SSH"], "action": "Accept",
         "track": {"type": "Log"}, "comments": "Allow management access — CP Best Practice"},
        {"name": "Stealth Rule", "source": "Any", "destination": "DEMO_SIMPLE_GATEWAY_1",
         "service": "Any", "action": "Drop",
         "track": {"type": "Log"}, "comments": "Block direct gateway access — CP Best Practice"},
        {"name": "DNS Resolution", "source": "DEMO_GROUP_1", "destination": ".demo.example.com",
         "service": "DEMO_SVC_DNS", "action": "Accept",
         "track": {"type": "Log"}, "comments": "Allow internal DNS resolution"},
        {"name": "Outbound Web Access", "source": "DEMO_NETWORK_1", "destination": "Any",
         "service": "DEMO_SVC_WEB_GROUP", "action": "Accept",
         "track": {"type": "Log"}, "comments": "Allow outbound web traffic"},
        {"name": "Inbound Web Services", "source": "Any", "destination": "DEMO_HOST_1",
         "service": ["DEMO_SVC_HTTP", "DEMO_SVC_HTTPS"], "action": "Accept",
         "track": {"type": "Log"}, "comments": "Allow inbound web to server"},
        {"name": "Internal Network Access", "source": "DEMO_ADDRESS_RANGE_1", "destination": "DEMO_NETWORK_1",
         "service": "Any", "action": "Accept",
         "track": {"type": "Log"}, "comments": "Internal range to network access"},
        {"name": "Zone-Based Access", "source": "DEMO_SECURITY_ZONE_1", "destination": "DEMO_WILDCARD_1",
         "service": "Any", "action": "Accept",
         "track": {"type": "Log"}, "comments": "Zone-based firewall policy"},
        {"name": "Dynamic Object Access", "source": "DEMO_DYNAMIC_OBJECT_1", "destination": "DEMO_NETWORK_1",
         "service": "DEMO_SVC_WEB_GROUP", "action": "Accept",
         "track": {"type": "Log"}, "comments": "Dynamic object-based access"},
        {"name": "VPN Interop Access", "source": "DEMO_INTEROPERABLE_DEVICE_1", "destination": "DEMO_NETWORK_1",
         "service": "Any", "action": "Accept",
         "track": {"type": "Log"}, "comments": "VPN interoperability traffic"},
        {"name": "Threat Feed Block", "source": "DEMO_NETWORK_FEED_1", "destination": "Any",
         "service": "Any", "action": "Drop",
         "track": {"type": "Log"}, "comments": "Block known malicious IPs (TOR exit nodes)"},
        {"name": "Time-Restricted SSH", "source": "Any", "destination": "DEMO_HOST_1",
         "service": "DEMO_SVC_SSH", "action": "Accept",
         "track": {"type": "Log"}, "time": "DEMO_TIME_1", "comments": "Time-restricted SSH access"},
        {"name": "Multicast Traffic", "source": "Any", "destination": "DEMO_MULTICAST_ADDRESS_RANGE_1",
         "service": "Any", "action": "Accept",
         "track": {"type": "Log"}, "comments": "Allow multicast traffic"},
        {"name": "VPN Community Access", "source": "DEMO_NETWORK_1", "destination": "DEMO_HOST_1",
         "service": "Any", "action": "Accept",
         "vpn": "DEMO_VPN_STAR", "track": {"type": "Log"}, "comments": "Rule using VPN community"},
        {"name": "Cleanup Rule", "source": "Any", "destination": "Any",
         "service": "Any", "action": "Drop",
         "track": {"type": "Log"}, "comments": "Drop and log all unmatched traffic — CP Best Practice"},
    ]

    rule_count = 0
    for r in rules:
        r["layer"] = layer
        r["position"] = "bottom"
        rname = r["name"]
        print(f"  Rule: {rname}... ", end="", flush=True)
        code, body = api(base_url, sid, "add-access-rule", r)
        if isinstance(body, dict) and "uid" in body:
            print("OK")
            rule_count += 1
        else:
            msg = body.get("message", body) if isinstance(body, dict) else body
            print(f"FAIL {str(msg)[:80]}")

    print(f"\n  Created {rule_count}/{len(rules)} rules")
    print("  Publishing rules...")
    publish(base_url, sid)

    # ======== STEP 8: Save manifest ========
    print("\n" + "=" * 60)
    print("STEP 8: Save manifest")
    os.makedirs("reports", exist_ok=True)
    with open("reports/demo_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"  Saved {len(manifest)} entries to reports/demo_manifest.json")

    api(base_url, sid, "logout")
    print(f"\n{'=' * 60}")
    print(f"DEPLOY COMPLETE: {len(manifest)} objects + {rule_count} rules")
    print(f"Policy: DEMO_Policy -> 'DEMO_Policy Network' layer")
    print(f"Cleanup: cp-qa -m {args.management} -u {args.user} --mode demo --action cleanup")


if __name__ == "__main__":
    main()
