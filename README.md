# Check Point API QA Tool

A self-healing QA engine that validates Check Point Management API objects through automated CRUD lifecycle testing. It dynamically parses the official API specification, generates exhaustive payloads covering every field and variant, and produces professional reports with copy-paste ready examples.

## Highlights

- **Self-Healing Engine** — Analyzes API error responses in real-time and auto-corrects payloads (up to 5 retries per variant) to achieve maximum pass rate.
- **Full CRUD Lifecycle** — Every object type is tested through `add` -> `set` -> `show` -> `delete`, verifying the complete roundtrip.
- **Demo Mode** — Create all object types at once for policy building, then clean up with a single command.
- **Variant Coverage** — Automatically detects mutually exclusive field-alternatives (e.g. `ipv4-address` vs `ipv6-address`) and generates a variant for each to cover 100% of the API surface.
- **Dynamic Versioning** — Automatically detects the Management Server's version at login (e.g., R81.20 vs R82) and fetches the matching **v2.x** or **v1.x** dynamic specification from `sc1.checkpoint.com` to ensure schema accuracy.
- **Professional Reporting** — Generates a Markdown audit report with per-variant timing, a summary table, and distinguishing field labels.
- **Example Export** — Outputs clean, standalone JSON payloads for every tested variant, ready to copy-paste into scripts or Ansible playbooks.
- **Debug Options** — `--debug` for verbose console output, `--dry-run` to inspect generated payloads without calling the API.

<details>
<summary><b>What is Self-Healing? (Click to expand)</b></summary>

In the context of the **Check Point API QA Tool**, "self-healing" refers to the tool's ability to automatically detect, analyze, and resolve API validation errors during the object creation process without requiring user intervention.

Instead of simply failing when the Management Server returns an error, the engine uses an **adaptive feedback loop** to "fix" the request on the fly.

### How it Works (The Technical Logic)

The core logic resides in `src/cp_qa/engine/autofix.py` and `lifecycle.py`. Here is the step-by-step flow:

1.  **Initial Attempt**: The tool sends a comprehensive "Full" payload to the API (e.g., `add-host`).
2.  **Error Analysis**: If the API returns an error (like `Invalid parameter` or `Missing mask definition`), the tool captures the exact error text.
3.  **Pattern Matching**: The `auto_fix_payload` function runs a battery of regex and string checks against that error.
4.  **In-Place Correction**: If a known issue is identified, the tool modifies the JSON payload in memory to resolve the conflict.
5.  **Re-Try**: The tool immediately retries the corrected payload. This loop repeats up to **5 times** (`MAX_RETRIES`) per object.

### Real-World Examples

During deployment, the self-healing engine handles several complex scenarios:

*   **Co-requisite Fields**: Automatically injecting a default `mask-length` (e.g., 24 for IPv4) if the server complains it's missing.
*   **Parameter Sanitization**: Stripping platform-unsupported fields (like `visitor-mode-interface`) that are found in the specification but rejected by specific server versions.
*   **VPN Protocol Logic**: Catching validation failures and forcing required settings like `encryption-suite: custom` when IKE parameters are present.
*   **IP Ambiguity**: Automatically dropping redundant generic `ip-address` fields if they conflict with versioned `ipv4-address` fields.

### Why It Matters
Check Point API requirements can vary significantly between R80.x, R81.x, and R82. The self-healing engine allows the tool to be **version-agnostic**—it adaptiveley discovers what the specific server requires and adjusts its payloads to match.
</details>

## Supported Object Types (21)

| Category | Types |
| :--- | :--- |
| **Network Objects** | host, network, wildcard, group, address-range, multicast-address-range, group-with-exclusion, dns-domain |
| **Extended Objects** | security-zone, dynamic-object, tag, time, time-group, gsn-handover-group, network-feed |
| **Gateways & Servers** | simple-gateway, simple-cluster, checkpoint-host, interoperable-device |
| **VPN Communities** | vpn-community-meshed, vpn-community-star |

## Installation

```bash
git clone https://github.com/alshawwaf/cp-api-qa-tool.git
cd cp-api-qa-tool

# Install as editable package (recommended for development)
pip install -e .

# Or install normally
pip install .

# After installation, the cp-qa command is available:
cp-qa --help
```

Alternatively, install dependencies only (without the `cp-qa` command):

```bash
pip install -r requirements.txt
```

## Usage

### QA Mode (default)

Runs the full `add -> set -> show -> delete` lifecycle for every object type and generates reports:

```bash
cp-qa -m <MGMT_IP> -u <USER> -p <PASSWORD>
```

### Demo Mode

Creates all object types on the management server and leaves them in place for policy building. A manifest file tracks everything for later cleanup.

```bash
# 1. Create all demo objects + recommended policy
cp-qa -m <MGMT_IP> -u <USER> --mode demo --action create

# 2. Build your Access Policy in SmartConsole using the DEMO_* objects

# 3. Clean up everything
cp-qa -m <MGMT_IP> -u <USER> --mode demo --action cleanup
```

Objects are created with a `DEMO_` prefix (e.g., `DEMO_HOST_1`, `DEMO_NETWORK_1`) and published immediately. The manifest is saved to `output/demo_manifest.json`.

### Debug Options

```bash
# Verbose debug output (all log levels printed to console)
cp-qa -m <MGMT_IP> -u <USER> --debug

# Dry-run: generate payloads and print them without calling the API
cp-qa -m <MGMT_IP> -u <USER> --dry-run --type host

# Test a single object type
cp-qa -m <MGMT_IP> -u <USER> --type network

# Quiet mode (only warnings and errors)
cp-qa -m <MGMT_IP> -u <USER> --quiet
```

### CLI Flags

Every flag can also be set via environment variable (in `config/.env`). CLI flags override `.env` values.

| Flag | Env Variable | Description | Default |
| :--- | :--- | :--- | :--- |
| `-m, --management` | `CP_MGMT_SERVER` | Management Server IP | *(required)* |
| `-u, --user` | `CP_MGMT_USER` | Username | `admin` |
| `-p, --password` | `CP_MGMT_PASSWORD` | Password (prompted if omitted) | |
| `-d, --domain` | `CP_MGMT_DOMAIN` | MDS domain name | |
| `--api-key` | `CP_MGMT_API_KEY` | API key for key-based auth | |
| `--api-version` | `CP_API_VERSION` | Override auto-detected spec version | |
| `-s, --section` | `CP_QA_SECTION` | API section to test | `Network Objects` |
| `--mode` | `CP_QA_MODE` | `qa` or `demo` | `qa` |
| `--action` | `CP_QA_ACTION` | Demo action: `create` / `cleanup` / `push-blueprint` | `create` |
| `--blueprint` | `CP_BLUEPRINT_PATH` | Custom blueprint JSON path | `blueprints/demo_policy_blueprint.json` |
| `--type` | `CP_QA_TYPE` | Only test a specific object type | |
| `--debug` | `CP_QA_DEBUG` | Verbose debug output (`true`/`false`) | `false` |
| `--quiet` | `CP_QA_QUIET` | Suppress INFO messages (`true`/`false`) | `false` |
| `--dry-run` | `CP_QA_DRY_RUN` | Generate payloads without API calls (`true`/`false`) | `false` |
| `--version` | | Show version and exit | |

## Output

### QA Mode

```
output/
  QA_SUMMARY_REPORT.md        # Markdown audit report with timing & variant analysis
  QA_RAW_DATA.json             # Full request/response data for every lifecycle step
  payloads/
    host/
      variant_1__ipv4-address.json
      variant_2__ipv6-address.json
      QA_REPORT.md             # Per-type audit report
      QA_RAW_DATA.json         # Per-type raw data
    network/
      variant_1__mask-length_mask-length4_subnet4.json
      ...
```

### Demo Mode

```
output/
  demo_manifest.json           # Tracks all created objects for cleanup

blueprints/
  demo_policy_blueprint.json   # Portable policy template (tracked in git)
```

Each payload file contains the exact proven `add-<type>` payload with professional naming and comments — ready for direct use.

## Project Structure

```
cp-api-qa-tool/
├── pyproject.toml                  # Package metadata + cp-qa entry point
├── requirements.txt                # Dependencies
├── README.md
├── .gitignore
├── src/
│   └── cp_qa/                      # Installable Python package
│       ├── __init__.py             # Package version + docstring
│       ├── client.py               # Check Point API client (login/logout/publish)
│       ├── logging.py              # Lazy-init logger (no side-effects on import)
│       ├── constants.py            # Shared constants & supported object types
│       ├── cli.py                  # CLI entry point (cp-qa command)
│       └── engine/                 # QA engine (split from monolithic original)
│           ├── __init__.py         # APIQAEngine facade class
│           ├── spec.py             # API spec fetching & lookup
│           ├── params.py           # Parameter extraction from spec objects
│           ├── testdata.py         # Test data generation & sub-object building
│           ├── payloads.py         # Payload generation & co-requisite logic
│           ├── type_defaults.py    # Type-specific known-good defaults
│           ├── autofix.py          # Self-healing payload auto-correction
│           ├── lifecycle.py        # CRUD lifecycle test execution
│           ├── reports.py          # JSON/Markdown/payload export
│           └── demo.py             # Demo create/cleanup/services/policy
├── blueprints/                     # Portable policy templates (tracked in git)
│   └── demo_policy_blueprint.json  # Default demo policy blueprint
├── config/                         # Configuration & credentials
│   ├── .env                       # Your local config (git-ignored)
│   └── .env.example               # Template with all supported variables
└── tests/                          # Placeholder for future tests
    └── __init__.py
```

All CLI flags can be configured via environment variables in `config/.env`. See `config/.env.example` for the full list.

## Development

```bash
git clone https://github.com/alshawwaf/cp-api-qa-tool.git
cd cp-api-qa-tool
pip install -e ".[dev]"
```

## Requirements

- Python 3.8+
- Network access to Check Point Management Server (HTTPS/443)
- Network access to `sc1.checkpoint.com` (API spec download)

> [!IMPORTANT]
> This tool creates and deletes objects during testing. Use in **lab/QA environments only** — never run against production management servers.

<details>
<summary><b>Demo Policy Blueprint: Push from JSON (Click to expand)</b></summary>

### Overview

The demo mode includes a **blueprint system** that stores the entire demo policy topology as a portable JSON file at `blueprints/demo_policy_blueprint.json`. This file serves as both a backup and a deployment source — you can push the full policy to any Check Point Management Server directly from the blueprint.

### What the Blueprint Contains

The blueprint defines a realistic enterprise firewall topology based on the [Ansible Dynamic Policy Demo](https://github.com/alshawwaf/Ansible_Projects/tree/main/Dynamic%20Policy%20Demo) project:

| Category | Objects |
|:---|:---|
| **Hosts** (6) | DNS servers (8.8.8.8, 8.8.4.4), Jump Host, Kali Linux, Windows Client (with static NAT), Windows Server (with static NAT) |
| **Networks** (5) | LAN (10.1.1.0/24), DMZ (10.1.2.0/24), Mgmt (10.1.3.0/24), IoT (10.1.4.0/24), External (203.0.113.0/24) |
| **Groups** (1) | Internal Networks (all 4 internal subnets) |
| **Network Feeds** (4) | Internal DNS, Public DNS, Attackers, Targets |
| **Gateway** (1) | DEMO_GW — perimeter firewall (10.1.3.1) |
| **Services** (6) | HTTP, HTTPS, SSH, DNS, ICMP Echo, LDAP/RPC |
| **Service Groups** (3) | Web (HTTP+HTTPS), LDAP_All (LDAP+RPC+DCE-RPC), Mail (SMTP+POP3+IMAP) |
| **Policy Package** | DEMO_Policy with Network layer + inline DNS layer |
| **Access Rules** (10) | Silent Drop, CP Updates, Mgmt Access, Stealth, DNS Inspection (inline), Outbound, Mail, LDAP, DMZ Inbound, Cleanup |
| **Sections** (5) | Management, DNS, Network Traffic, DMZ, Clean up rule |

### Deploying from the Blueprint

```bash
# Deploy the default blueprint
cp-qa -m <MGMT_IP> -u admin --mode demo --action push-blueprint

# Deploy a custom blueprint
cp-qa -m <MGMT_IP> -u admin --mode demo --action push-blueprint --blueprint path/to/my_policy.json

# Clean up everything (same as regular demo cleanup)
cp-qa -m <MGMT_IP> -u admin --mode demo --action cleanup
```

### Creating Your Own Blueprint

The blueprint JSON has three top-level sections: `topology`, `services`, and `policy`. You can edit the file directly to customize the demo environment:

```json
{
  "topology": {
    "hosts": [ { "name": "...", "ipv4-address": "...", "color": "..." } ],
    "networks": [ { "name": "...", "subnet4": "...", "mask-length4": 24 } ],
    "groups": [ { "name": "...", "members": ["..."] } ],
    "network-feeds": [ { "name": "...", "feed-url": "...", "feed-format": "Flat List" } ],
    "gateways": [ { "name": "...", "ipv4-address": "...", "firewall": true } ]
  },
  "services": {
    "individual": [ { "name": "...", "type": "service-tcp", "port": "80" } ],
    "groups": [ { "name": "...", "members": ["..."] } ]
  },
  "policy": {
    "package": { "name": "...", "access": true, "threat-prevention": false },
    "inline-layers": [ { "name": "...", "rules": [ ... ] } ],
    "network-layer": {
      "sections": [
        { "section": "Section Name", "rules": [ { "name": "...", "source": "...", "action": "Accept" } ] }
      ]
    }
  }
}
```

All objects must use the `DEMO_` prefix to be discoverable by the cleanup command.

### Differences: `create` vs `push-blueprint`

| | `--action create` | `--action push-blueprint` |
|:---|:---|:---|
| **Source** | Hardcoded in `demo.py` | Reads from JSON file |
| **Customizable** | Requires code changes | Edit the JSON file |
| **Portable** | No | Yes — share/version the JSON |
| **Same topology** | Yes (default blueprint matches) | Yes (or your custom version) |

</details>

## License

MIT
