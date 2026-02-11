#!/usr/bin/env python3
"""Diagnose: dump full field metadata for a given API object.

Fetches the Check Point Management API specification and prints the
complete field schema for any object type — useful for understanding
what fields are available, their types, allowed values, and
field-alternatives (mutually exclusive options).

Usage::

    python scripts/diagnose_fields.py HostRequestNew
    python scripts/diagnose_fields.py NetworkRequestNew --spec-url <url>

Environment variables:
    CP_API_SPEC_URL  Override the default spec URL.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import requests

requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]

DEFAULT_SPEC_URL = (
    "https://sc1.checkpoint.com/documents/latest/APIs/"
    "data/v2.1/dynamic/apis.json"
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Inspect raw field schema for a Check Point API object type",
        epilog=(
            "Examples:\n"
            "  python scripts/diagnose_fields.py HostRequestNew\n"
            "  python scripts/diagnose_fields.py NetworkRequestNew\n"
            "  python scripts/diagnose_fields.py --list\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Object name to inspect (e.g. HostRequestNew). "
        "Case-insensitive substring match.",
    )
    parser.add_argument(
        "--spec-url",
        default=os.environ.get("CP_API_SPEC_URL", DEFAULT_SPEC_URL),
        help="API specification URL (default: latest v2.1)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_objects",
        help="List all object names in the spec and exit",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print full JSON for matched objects (verbose)",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point."""
    args = parse_args()

    if not args.target and not args.list_objects:
        print("Error: provide an object name or use --list", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching spec from {args.spec_url} ...")
    resp = requests.get(args.spec_url, verify=False, timeout=60)
    resp.raise_for_status()
    spec = resp.json()
    objects = spec.get("objects", [])
    print(f"Spec loaded: {len(objects)} object definitions\n")

    # --list mode
    if args.list_objects:
        for obj in objects:
            print(f"  {obj.get('name', '?')}")
        return

    # Search for matching objects
    target = args.target.lower()
    matched = False
    for obj in objects:
        obj_name = obj.get("name", "")
        if target not in obj_name.lower():
            continue

        matched = True
        print(f"\n{'=' * 60}")
        print(f"OBJECT: {obj_name}")
        print(f"{'=' * 60}")

        if args.debug:
            print(json.dumps(obj, indent=2))
            continue

        for section in ["required-fields", "fields", "under-more-fields"]:
            fields = obj.get(section, [])
            if not fields:
                continue
            print(f"\n--- {section} ({len(fields)} fields) ---")
            for f in fields:
                name = f.get("name", "?")
                types = f.get("types", [])
                alts = f.get("field-alternatives", [])
                allowed = f.get("allowed-values", [])
                print(f"  {name}:")
                print(f"    types: {json.dumps(types)}")
                if allowed:
                    print(f"    allowed-values: {allowed}")
                if alts:
                    for a in alts:
                        print(
                            f"    ALT -> {a.get('name')}: "
                            f"types={json.dumps(a.get('types', []))}"
                        )
        print()

        # Stop on exact match
        if target == obj_name.lower():
            break

    if not matched:
        print(f"No objects matching '{args.target}' found in the spec.")
        sys.exit(1)


if __name__ == "__main__":
    main()
