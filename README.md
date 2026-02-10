# Check Point API QA Tool

A self-healing QA engine that validates Check Point Management API objects through automated CRUD lifecycle testing. It dynamically parses the official API specification, generates exhaustive payloads covering every field and variant, and produces professional reports with copy-paste ready examples.

## Highlights

- **Self-Healing Engine** — Analyzes API error responses in real-time and auto-corrects payloads (up to 5 retries per variant) to achieve maximum pass rate.
- **Full CRUD Lifecycle** — Every object type is tested through `add` -> `set` -> `show` -> `delete`, verifying the complete roundtrip.
- **Variant Coverage** — Automatically detects mutually exclusive field-alternatives (e.g. `ipv4-address` vs `ipv6-address`) and generates a variant for each to cover 100% of the API surface.
- **Dynamic Versioning** — Detects the Management Server's API version at login and fetches the matching specification (v1.x / v2.x).
- **Professional Reporting** — Generates a Markdown audit report with per-variant timing, a summary table, and distinguishing field labels.
- **Example Export** — Outputs clean, standalone JSON payloads for every tested variant, ready to copy-paste into scripts or Ansible playbooks.

## Supported Object Types (19)

| Category | Types |
| :--- | :--- |
| **Network Objects** | host, network, wildcard, group, address-range, multicast-address-range, group-with-exclusion, dns-domain |
| **Extended Objects** | security-zone, dynamic-object, tag, time, time-group, gsn-handover-group, network-feed |
| **Gateways & Servers** | simple-gateway, simple-cluster, checkpoint-host, interoperable-device |

## Installation

```bash
git clone https://github.com/alshawwaf/cp-api-qa-tool.git
cd cp-api-qa-tool
pip install -r requirements.txt
```

## Usage

```bash
python api_qa_tester.py -m <MGMT_IP> -u <USER> -p <PASSWORD>
```

| Flag | Description | Default |
| :--- | :--- | :--- |
| `-m, --management` | Management Server IP | *(required)* |
| `-u, --user` | Username | `admin` |
| `-p, --password` | Password (prompted securely if omitted) | |
| `-s, --section` | API section to test | `Network Objects` |

## Output

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
    simple-gateway/
      variant_1.json
    ...
```

Each example file contains the exact proven `add-<type>` payload with professional naming and comments — ready for direct use.

## Diagnostic Utility

Inspect the raw field schema for any API object type:

```bash
python diagnose_fields.py HostRequestNew
python diagnose_fields.py NetworkRequestNew
```

## Requirements

- Python 3.8+
- Network access to Check Point Management Server (HTTPS/443)
- Network access to `sc1.checkpoint.com` (API spec download)

> [!IMPORTANT]
> This tool creates and deletes objects during testing. Use in **lab/QA environments only** — never run against production management servers.

## License

MIT
