#!/usr/bin/env python3
"""Diagnostic script: create objects one at a time with publish after each.

Used to isolate the root cause of publish failures (409 conflicts, stale
locks, etc.) by creating and publishing objects sequentially.  Each step
reports success or failure individually.

Usage::

    python scripts/demo_diagnostic.py -m 10.0.0.1 -u admin -p <password>
    python scripts/demo_diagnostic.py -m 10.0.0.1 -u admin  # prompts

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
import sys
import time

import requests

requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create demo objects one at a time to diagnose publish issues",
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
    ct = resp.headers.get("content-type", "")
    if ct.startswith("application/json"):
        return resp.status_code, resp.json()
    return resp.status_code, {"message": resp.text[:200]}


def publish(base_url: str, sid: str) -> bool:
    """Publish pending changes, polling for async task completion."""
    code, body = api(base_url, sid, "publish")
    if code == 200:
        task_id = body.get("task-id") if isinstance(body, dict) else None
        if task_id:
            for _ in range(60):
                time.sleep(2)
                _, task_res = api(base_url, sid, "show-task", {"task-id": task_id, "details-level": "full"})
                tasks = task_res.get("tasks", []) if isinstance(task_res, dict) else []
                if tasks and tasks[0].get("status") in ("succeeded", "failed"):
                    status = tasks[0]["status"]
                    print(f"    Publish task {status}")
                    return status == "succeeded"
            print("    Publish task timed out")
            return False
        print(f"    Publish OK (no task-id)")
        return True
    else:
        print(f"    PUBLISH FAILED {code}: {json.dumps(body, indent=2)[:300] if isinstance(body, dict) else str(body)[:300]}")
        return False


def delete_obj(base_url: str, sid: str, obj_type: str, name: str) -> bool:
    """Attempt to delete an object by name."""
    code, body = api(base_url, sid, f"delete-{obj_type}", {"name": name, "ignore-warnings": True, "ignore-errors": True})
    return isinstance(body, dict) and ("uid" in body or body.get("message") == "OK")


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

    # === STEP 1: LOGIN ===
    print("=" * 60)
    print("STEP 1: Login")
    code, body = api(base_url, "", "login", {"user": args.user, "password": password})
    sid = body["sid"]
    print(f"  SID: {sid[:20]}...")

    # === STEP 2: DISCARD + DELETE EVERYTHING ===
    print("\n" + "=" * 60)
    print("STEP 2: Discard all sessions and delete existing demo objects")

    api(base_url, sid, "discard")
    print("  Discarded own session")

    demo_objects = [
        ("package", "DEMO_Policy"),
        ("service-group", "DEMO_SVC_WEB_GROUP"),
        ("service-tcp", "DEMO_SVC_HTTP"),
        ("service-tcp", "DEMO_SVC_HTTPS"),
        ("service-tcp", "DEMO_SVC_SSH"),
        ("service-tcp", "DEMO_SVC_SMTP"),
        ("service-udp", "DEMO_SVC_DNS"),
        ("service-icmp", "DEMO_SVC_PING"),
        ("group", "DEMO_GROUP_1"),
        ("host", "DEMO_HOST_1"),
        ("network", "DEMO_NETWORK_1"),
        ("wildcard", "DEMO_WILDCARD_1"),
        ("address-range", "DEMO_ADDRESS_RANGE_1"),
        ("multicast-address-range", "DEMO_MULTICAST_ADDRESS_RANGE_1"),
        ("dns-domain", ".demo-dns-domain-1.example.com"),
        ("security-zone", "DEMO_SECURITY_ZONE_1"),
        ("dynamic-object", "DEMO_DYNAMIC_OBJECT_1"),
        ("tag", "DEMO_TAG_1"),
        ("network-feed", "DEMO_NETWORK_FEED_1"),
        ("gsn-handover-group", "DEMO_GSN_HANDOVER_GROUP_1"),
        ("simple-gateway", "DEMO_SIMPLE_GATEWAY_1"),
        ("simple-cluster", "DEMO_SIMPLE_CLUSTER_1"),
        ("checkpoint-host", "DEMO_CHECKPOINT_HOST_1"),
        ("interoperable-device", "DEMO_INTEROPERABLE_DEVICE_1"),
    ]

    for otype, oname in demo_objects:
        delete_obj(base_url, sid, otype, oname)

    # Search for remaining DEMO_ objects
    for prefix_type in ["group", "time"]:
        _, show_res = api(base_url, sid, f"show-{prefix_type}s", {"limit": 50, "filter": "DEMO_"})
        if isinstance(show_res, dict):
            for obj in show_res.get("objects", []):
                n = obj.get("name", "")
                if n.startswith("DEMO_"):
                    delete_obj(base_url, sid, prefix_type, n)
                    print(f"  Cleaned leftover: {prefix_type} {n}")

    print("  Publishing cleanup...")
    publish(base_url, sid)

    # Verify clean state
    print("  Verifying clean state...")
    for prefix_type in ["host", "network", "group", "service-tcp", "service-udp"]:
        _, show_res = api(base_url, sid, f"show-{prefix_type}s", {"limit": 50, "filter": "DEMO_"})
        if isinstance(show_res, dict):
            objs = [
                o.get("name")
                for o in show_res.get("objects", [])
                if o.get("name", "").startswith("DEMO_")
            ]
            if objs:
                print(f"  WARNING: Still found {prefix_type}: {objs}")
            else:
                print(f"  No {prefix_type} objects with DEMO_ prefix")

    # === STEP 3: CREATE ONE AT A TIME ===
    print("\n" + "=" * 60)
    print("STEP 3: Create objects one at a time, publish after each")

    test_objects = [
        ("add-host", "host", {"name": "DEMO_HOST_1", "ip-address": "10.100.1.134",
                               "ignore-warnings": True, "ignore-errors": True}),
        ("add-network", "network", {"name": "DEMO_NETWORK_1", "subnet": "10.100.0.0",
                                     "mask-length": 24, "ignore-warnings": True, "ignore-errors": True}),
        ("add-group", "group", {"name": "DEMO_GROUP_1", "ignore-warnings": True, "ignore-errors": True}),
        ("add-address-range", "address-range", {"name": "DEMO_ADDRESS_RANGE_1",
                                                 "ip-address-first": "10.100.1.10", "ip-address-last": "10.100.1.30",
                                                 "ignore-warnings": True, "ignore-errors": True}),
        ("add-wildcard", "wildcard", {"name": "DEMO_WILDCARD_1",
                                       "ipv4-address": "10.100.1.82", "ipv4-mask-wildcard": "0.0.0.255",
                                       "ignore-warnings": True, "ignore-errors": True}),
        ("add-dns-domain", "dns-domain", {"name": ".demo.example.com", "is-sub-domain": False,
                                           "ignore-warnings": True, "ignore-errors": True}),
        ("add-security-zone", "security-zone", {"name": "DEMO_SECURITY_ZONE_1",
                                                 "ignore-warnings": True, "ignore-errors": True}),
        ("add-dynamic-object", "dynamic-object", {"name": "DEMO_DYNAMIC_OBJECT_1",
                                                   "ignore-warnings": True, "ignore-errors": True}),
        ("add-tag", "tag", {"name": "DEMO_TAG_1", "ignore-warnings": True, "ignore-errors": True}),
        ("add-time", "time", {"name": "DEMO_TIME_1", "start-now": True, "end-never": True,
                               "ignore-warnings": True, "ignore-errors": True}),
    ]

    created = []
    for cmd, otype, payload in test_objects:
        print(f"\n  Creating {otype}: {payload['name']}...")
        code, body = api(base_url, sid, cmd, payload)
        if isinstance(body, dict) and "uid" in body:
            print(f"    OK Created (uid: {body['uid'][:12]}...)")
            created.append((otype, payload["name"]))
        else:
            msg = body.get("message", body) if isinstance(body, dict) else body
            print(f"    FAILED ({code}): {str(msg)[:200]}")
            continue

        print(f"    Publishing...")
        if not publish(base_url, sid):
            print(f"    PUBLISH FAILED AFTER CREATING {payload['name']}")
            _, sess = api(base_url, sid, "show-session", {})
            if isinstance(sess, dict):
                print(f"    Session state: changes={sess.get('changes-count')}")

    # === STEP 4: SERVICES ===
    print("\n" + "=" * 60)
    print("STEP 4: Create services")

    services = [
        ("add-service-tcp", "service-tcp", {"name": "DEMO_SVC_HTTP", "port": "80",
                                             "ignore-warnings": True, "ignore-errors": True}),
        ("add-service-tcp", "service-tcp", {"name": "DEMO_SVC_HTTPS", "port": "443",
                                             "ignore-warnings": True, "ignore-errors": True}),
        ("add-service-tcp", "service-tcp", {"name": "DEMO_SVC_SSH", "port": "22",
                                             "ignore-warnings": True, "ignore-errors": True}),
        ("add-service-udp", "service-udp", {"name": "DEMO_SVC_DNS", "port": "53",
                                             "ignore-warnings": True, "ignore-errors": True}),
    ]

    for cmd, otype, payload in services:
        print(f"\n  Creating {otype}: {payload['name']}...")
        code, body = api(base_url, sid, cmd, payload)
        if isinstance(body, dict) and "uid" in body:
            print(f"    OK Created")
            created.append((otype, payload["name"]))
        else:
            msg = body.get("message", body) if isinstance(body, dict) else body
            print(f"    FAILED ({code}): {str(msg)[:200]}")
            continue
        print(f"    Publishing...")
        if not publish(base_url, sid):
            print(f"    PUBLISH FAILED AFTER CREATING {payload['name']}")

    # === STEP 5: POLICY ===
    print("\n" + "=" * 60)
    print("STEP 5: Create policy package")

    code, body = api(base_url, sid, "add-package", {"name": "DEMO_Policy", "access": True, "threat-prevention": False})
    if isinstance(body, dict) and "uid" in body:
        print(f"  Policy package created")
        created.append(("package", "DEMO_Policy"))
        print(f"  Publishing...")
        publish(base_url, sid)
    else:
        print(f"  Package failed: {body}")

    # === STEP 6: RULES ===
    print("\n" + "=" * 60)
    print("STEP 6: Create access rules one by one")

    layer = "DEMO_Policy Network"
    rules = [
        {"name": "Mgmt Access", "layer": layer, "position": "bottom",
         "source": "DEMO_NETWORK_1", "destination": "Any",
         "service": ["DEMO_SVC_HTTPS", "DEMO_SVC_SSH"], "action": "Accept",
         "track": {"type": "Log"}, "comments": "Management access"},
        {"name": "Stealth Rule", "layer": layer, "position": "bottom",
         "source": "Any", "destination": "Any",
         "service": "Any", "action": "Drop",
         "track": {"type": "Log"}, "comments": "Stealth rule"},
        {"name": "DNS Rule", "layer": layer, "position": "bottom",
         "source": "DEMO_GROUP_1", "destination": ".demo.example.com",
         "service": "DEMO_SVC_DNS", "action": "Accept",
         "track": {"type": "Log"}, "comments": "DNS resolution"},
        {"name": "Cleanup Rule", "layer": layer, "position": "bottom",
         "source": "Any", "destination": "Any",
         "service": "Any", "action": "Drop",
         "track": {"type": "Log"}, "comments": "Cleanup rule"},
    ]

    for rule in rules:
        rname = rule["name"]
        print(f"\n  Adding rule: {rname}...")
        code, body = api(base_url, sid, "add-access-rule", rule)
        if isinstance(body, dict) and "uid" in body:
            print(f"    OK Rule created")
        else:
            msg = body.get("message", body) if isinstance(body, dict) else body
            print(f"    FAILED ({code}): {str(msg)[:200]}")
            continue
        print(f"    Publishing...")
        if not publish(base_url, sid):
            print(f"    PUBLISH FAILED AFTER RULE: {rname}")

    # === DONE ===
    print("\n" + "=" * 60)
    print(f"DONE. Created {len(created)} objects total.")
    api(base_url, sid, "logout")
    print("Logged out.")


if __name__ == "__main__":
    main()
