"""Diagnose: dump full field metadata for a given object to understand schema."""
import requests, json, sys
requests.packages.urllib3.disable_warnings()

SPEC_URL = "https://sc1.checkpoint.com/documents/latest/APIs/data/v2.0.1/dynamic/apis.json"
TARGET = sys.argv[1] if len(sys.argv) > 1 else "HostRequestNew"

r = requests.get(SPEC_URL, verify=False, timeout=60)
spec = r.json()

# Find the target object
for obj in spec.get('objects', []):
    if TARGET.lower() in obj.get('name', '').lower():
        print(f"\n=== OBJECT: {obj['name']} ===")
        for section in ['required-fields', 'fields', 'under-more-fields']:
            fields = obj.get(section, [])
            if fields:
                print(f"\n--- {section} ({len(fields)} fields) ---")
                for f in fields:
                    name = f.get('name', '?')
                    types = f.get('types', [])
                    alts = f.get('field-alternatives', [])
                    allowed = f.get('allowed-values', [])
                    print(f"  {name}:")
                    print(f"    types: {json.dumps(types)}")
                    if allowed: print(f"    allowed-values: {allowed}")
                    if alts:
                        for a in alts:
                            print(f"    ALT -> {a.get('name')}: types={json.dumps(a.get('types', []))}")
        print()
        if TARGET.lower() == obj.get('name', '').lower():
            break
