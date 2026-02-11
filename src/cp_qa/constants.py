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
# Naming prefixes
# ---------------------------------------------------------------------------

#: Prefix used for all demo-created objects.
DEMO_PREFIX = "DEMO_"

#: All prefixes to search for during discovery cleanup.
DISCOVERABLE_PREFIXES: list[str] = ["DEMO_", "QA_"]

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
    "service-other",
    "service-sctp",
    "simple-gateway",
    "simple-cluster",
    "checkpoint-host",
    "interoperable-device",
]

# ---------------------------------------------------------------------------
# Server-side discovery: plural "show" command -> singular type
# ---------------------------------------------------------------------------

#: Mapping of ``show-<plural>`` commands to singular type names.
#: Used by ``discover_demo_objects()`` to sweep the server for leftover
#: objects whose names match a known prefix (DEMO_, QA_, etc.).
DISCOVERABLE_TYPES: list[tuple[str, str]] = [
    # Policy & rules (must be deleted first)
    ("packages", "package"),
    # Service groups (before individual services)
    ("service-groups", "service-group"),
    # VPN communities
    ("vpn-communities-meshed", "vpn-community-meshed"),
    ("vpn-communities-star", "vpn-community-star"),
    # Groups (before their members)
    ("groups-with-exclusion", "group-with-exclusion"),
    ("time-groups", "time-group"),
    ("groups", "group"),
    ("gsn-handover-groups", "gsn-handover-group"),
    # Core network objects
    ("hosts", "host"),
    ("networks", "network"),
    ("wildcards", "wildcard"),
    ("address-ranges", "address-range"),
    ("multicast-address-ranges", "multicast-address-range"),
    ("dns-domains", "dns-domain"),
    # Extended objects
    ("security-zones", "security-zone"),
    ("dynamic-objects", "dynamic-object"),
    ("tags", "tag"),
    ("times", "time"),
    ("network-feeds", "network-feed"),
    # Services
    ("service-tcps", "service-tcp"),
    ("service-udps", "service-udp"),
    ("service-icmps", "service-icmp"),
    ("services-other", "service-other"),
    ("services-sctp", "service-sctp"),
    # Gateways & servers
    ("simple-gateways", "simple-gateway"),
    ("simple-clusters", "simple-cluster"),
    ("checkpoint-hosts", "checkpoint-host"),
    ("interoperable-devices", "interoperable-device"),
]
