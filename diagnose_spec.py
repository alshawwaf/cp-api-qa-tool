import requests
import json

SPEC_URL = "https://sc1.checkpoint.com/documents/latest/APIs/data/v2.0.1/dynamic/apis.json"

def diagnose():
    try:
        r = requests.get(SPEC_URL, verify=False)
        data = r.json()
        
        target = "com.checkpoint.management.web_api.core.handler.objects.network_objects.network.NetworkRequestNew"
        
        objs = data.get('objects', [])
        for obj in objs:
            if obj.get('name') == target:
                print(f"Full object JSON: {target}")
                print(json.dumps(obj, indent=2))
                return
        print(f"Object {target} not found.")
                
        print("--- Unique Groups ---")
        for g in sorted(groups):
            print(g)
            
        print("\n--- Unique Sections ---")
        for s in sorted(sections):
            print(s)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    diagnose()
