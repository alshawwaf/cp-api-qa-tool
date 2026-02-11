"""Shared constants for the cp-api-qa-tool package.

Centralises configuration values, supported object types, and
dependency-ordering lists that are referenced by multiple modules.
"""

# ---------------------------------------------------------------------------
# API specification
# ---------------------------------------------------------------------------

#: Default API spec URL.  Overridden at runtime using the version detected
#: during login (e.g. ``v2.1`` -> ``…/data/v2.1/dynamic/apis.json``).
API_SPEC_URL = (
    "https://sc1.checkpoint.com/documents/latest/APIs/data/v2.1/dynamic/apis.json"
)

# ---------------------------------------------------------------------------
# Report / manifest paths (relative to CWD)
# ---------------------------------------------------------------------------

MANIFEST_PATH = "reports/demo_manifest.json"
QA_RAW_DATA_PATH = "reports/QA_RAW_DATA.json"
QA_SUMMARY_REPORT_PATH = "reports/QA_SUMMARY_REPORT.md"
QA_EXAMPLES_DIR = "reports/examples"

# ---------------------------------------------------------------------------
# Self-healing retry budget
# ---------------------------------------------------------------------------

#: Maximum number of auto-fix retries per variant during lifecycle testing.
MAX_RETRIES = 5

# ---------------------------------------------------------------------------
# Supported object types
# ---------------------------------------------------------------------------

#: Object types supported for both QA and demo modes, grouped by category.
NETWORK_OBJECTS_TYPES: list[str] = [
    # Core Network Objects
    "host",
    "network",
    "group",
    "address-range",
    "multicast-address-range",
    "group-with-exclusion",
    "dns-domain",
    "wildcard",
    # Extended Objects
    "security-zone",
    "dynamic-object",
    "tag",
    "time",
    "time-group",
    "gsn-handover-group",
    "network-feed",
    # Gateways & Servers
    "simple-gateway",
    "simple-cluster",
    "checkpoint-host",
    "interoperable-device",
    # VPN Communities
    "vpn-community-meshed",
    "vpn-community-star",
]

# ---------------------------------------------------------------------------
# Cleanup dependency ordering
# ---------------------------------------------------------------------------

#: Deletion order for demo cleanup.  Objects earlier in this list are
#: deleted **first** — dependents before the objects they reference.
CLEANUP_ORDER: list[str] = [
    "package",  # cascade-deletes all rules + layers
    "service-group",  # before individual services
    "vpn-community-meshed",
    "vpn-community-star",
    "group-with-exclusion",  # depends on groups
    "time-group",  # depends on time objects
    "group",  # depends on hosts/networks/ranges
    "gsn-handover-group",
    "host",
    "network",
    "wildcard",
    "address-range",
    "multicast-address-range",
    "dns-domain",
    "security-zone",
    "dynamic-object",
    "tag",
    "time",
    "network-feed",
    "service-tcp",
    "service-udp",
    "service-icmp",
    "simple-gateway",
    "simple-cluster",
    "checkpoint-host",
    "interoperable-device",
]
