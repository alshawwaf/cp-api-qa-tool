import os
import json
from cp_qa.client import APIClient
from cp_qa.logging import configure
from dotenv import load_dotenv

def diag():
    configure(debug=False)
    load_dotenv('config/.env')
    
    mgmt = os.environ.get('CP_MGMT_SERVER')
    user = os.environ.get('CP_MGMT_USER')
    pwd = os.environ.get('CP_MGMT_PASSWORD')
    
    print(f"Connecting to {mgmt} as {user}...")
    client = APIClient(mgmt, user, pwd)
    
    try:
        client.login()
        print("Login successful.")
        
        # 1. Check Package
        pkg = client.run_command('show-package', {'name': 'DEMO_Policy', 'details-level': 'full'})
        print("\n--- PACKAGE INFO ---")
        print(f"Name: {pkg.get('name')}")
        print(f"UID: {pkg.get('uid')}")
        
        layers = pkg.get('access-layers', [])
        print(f"\nAccess Layers ({len(layers)}):")
        for l in layers:
            print(f"  - {l.get('name')} (UID: {l.get('uid')})")
            
            # 2. Check rules in each layer
            rb = client.run_command('show-access-rulebase', {
                'name': l.get('name'), 
                'details-level': 'standard',
                'limit': 20
            })
            rules = rb.get('rulebase', [])
            print(f"    Rules found: {len(rules)}")
            for i, rule in enumerate(rules):
                print(f"      Rule {i+1}: {rule.get('name', 'unnamed')}")

    except Exception as e:
        print(f"Error during diagnostic: {e}")
    finally:
        try:
            client.logout()
        except:
            pass

if __name__ == "__main__":
    diag()
