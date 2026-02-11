# Check Point API QA Tool

A self-healing QA engine that validates Check Point Management API objects through automated CRUD lifecycle testing. It dynamically parses the official API specification, generates exhaustive payloads covering every field and variant, and produces professional reports with copy-paste ready examples.

## Highlights

- **Self-Healing Engine** — Analyzes API error responses in real-time and auto-corrects payloads (up to 5 retries per variant) to achieve maximum pass rate.
- **Full CRUD Lifecycle** — Every object type is tested through `add` -> `set` -> `show` -> `delete`, verifying the complete roundtrip.
- **Demo Mode** — Create all object types at once for policy building, then clean up with a single command.
- **Variant Coverage** — Automatically detects mutually exclusive field-alternatives (e.g. `ipv4-address` vs `ipv6-address`) and generates a variant for each to cover 100% of the API surface.
- **Dynamic Versioning** — Detects the Management Server's API version at login and fetches the matching specification (v1.x / v2.x).
- **Professional Reporting** — Generates a Markdown audit report with per-variant timing, a summary table, and distinguishing field labels.
- **Example Export** — Outputs clean, standalone JSON payloads for every tested variant, ready to copy-paste into scripts or Ansible playbooks.
- **Debug Options** — `--debug` for verbose console output, `--dry-run` to inspect generated payloads without calling the API.

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

Objects are created with a `DEMO_` prefix (e.g., `DEMO_HOST_1`, `DEMO_NETWORK_1`) and published immediately. The manifest is saved to `reports/demo_manifest.json`.

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

| Flag | Description | Default |
| :--- | :--- | :--- |
| `-m, --management` | Management Server IP | *(required)* |
| `-u, --user` | Username | `admin` |
| `-p, --password` | Password (prompted securely if omitted) | |
| `-d, --domain` | MDS domain name | |
| `--api-key` | API key for key-based authentication | |
| `-s, --section` | API section to test | `Network Objects` |
| `--mode` | `qa` (full CRUD lifecycle) or `demo` (create-all / cleanup-all) | `qa` |
| `--action` | Demo mode action: `create` or `cleanup` | `create` |
| `--type` | Only test a specific object type (e.g. `host`) | |
| `--debug` | Print DEBUG-level messages to the console | |
| `--quiet` | Suppress INFO messages (warnings and errors only) | |
| `--dry-run` | Generate payloads without calling the API | |
| `--version` | Show version and exit | |

## Output

### QA Mode

```
reports/
  QA_SUMMARY_REPORT.md        # Markdown audit report with timing & variant analysis
  QA_RAW_DATA.json             # Full request/response data for every lifecycle step
  examples/
    host/
      variant_1__ipv4-address.json
      variant_2__ipv6-address.json
    network/
      variant_1__mask-length_mask-length4_subnet4.json
      ...
```

### Demo Mode

```
reports/
  demo_manifest.json           # Tracks all created objects for cleanup
```

Each example file contains the exact proven `add-<type>` payload with professional naming and comments — ready for direct use.

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
│           ├── reports.py          # JSON/Markdown/example export
│           └── demo.py             # Demo create/cleanup/services/policy
├── scripts/                        # Standalone diagnostic utilities
│   ├── diagnose_fields.py          # Inspect raw field schema for any API object
│   ├── clean_deploy.py             # Direct deploy script (bypasses engine)
│   └── demo_diagnostic.py          # Step-by-step diagnostic for publish issues
└── tests/                          # Placeholder for future tests
    └── __init__.py
```

## Diagnostic Scripts

Located in `scripts/` — standalone utilities for debugging and inspection:

```bash
# Inspect the raw field schema for any API object type
python scripts/diagnose_fields.py HostRequestNew
python scripts/diagnose_fields.py NetworkRequestNew --spec-url <url>
python scripts/diagnose_fields.py --list  # List all object names

# Direct deploy script (bypasses the main engine)
python scripts/clean_deploy.py -m <MGMT_IP> -u admin

# Step-by-step diagnostic for publish issues
python scripts/demo_diagnostic.py -m <MGMT_IP> -u admin
```

Credentials can also be passed via environment variables: `CP_MGMT_SERVER`, `CP_MGMT_USER`, `CP_MGMT_PASSWORD`.

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

## License

MIT
