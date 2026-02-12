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
    # Services
    "service-tcp",
    "service-udp",
    "service-icmp",
    "service-icmp6",
    "service-sctp",
    "service-other",
    "service-dce-rpc",
    "service-rpc",
    "service-compound-tcp",
    "service-citrix-tcp",
    "service-group",
    # Application & URL Filtering
    "application-site",
    "application-site-category",
    "application-site-group",
    # Identity & Access
    "access-role",
    "identity-tag",
    # Threat Prevention
    "threat-indicator",
    # Gateways & Servers
    "simple-gateway",
    "simple-cluster",
    "checkpoint-host",
    "interoperable-device",
    "lsv-profile",
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
    # Groups (before their members)
    "application-site-group",
    "service-group",
    "vpn-community-meshed",
    "vpn-community-star",
    "group-with-exclusion",
    "time-group",
    "group",
    "gsn-handover-group",
    # Core network objects
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
    # Services
    "service-tcp",
    "service-udp",
    "service-icmp",
    "service-icmp6",
    "service-other",
    "service-sctp",
    "service-dce-rpc",
    "service-rpc",
    "service-compound-tcp",
    "service-citrix-tcp",
    # Application & URL Filtering
    "application-site",
    "application-site-category",
    # Identity & Access
    "access-role",
    "identity-tag",
    # Threat Prevention
    "threat-indicator",
    # Gateways & Servers
    "simple-gateway",
    "simple-cluster",
    "checkpoint-host",
    "interoperable-device",
    "lsv-profile",
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
    # Groups (before their members)
    ("application-site-groups", "application-site-group"),
    ("service-groups", "service-group"),
    # VPN communities
    ("vpn-communities-meshed", "vpn-community-meshed"),
    ("vpn-communities-star", "vpn-community-star"),
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
    ("services-tcp", "service-tcp"),
    ("services-udp", "service-udp"),
    ("services-icmp", "service-icmp"),
    ("services-icmp6", "service-icmp6"),
    ("services-other", "service-other"),
    ("services-sctp", "service-sctp"),
    ("services-dce-rpc", "service-dce-rpc"),
    ("services-rpc", "service-rpc"),
    ("services-compound-tcp", "service-compound-tcp"),
    ("services-citrix-tcp", "service-citrix-tcp"),
    # Application & URL Filtering
    ("application-sites", "application-site"),
    ("application-site-categories", "application-site-category"),
    # Identity & Access
    ("access-roles", "access-role"),
    ("identity-tags", "identity-tag"),
    # Threat Prevention
    ("threat-indicators", "threat-indicator"),
    # Gateways & servers
    ("simple-gateways", "simple-gateway"),
    ("simple-clusters", "simple-cluster"),
    ("checkpoint-hosts", "checkpoint-host"),
    ("interoperable-devices", "interoperable-device"),
    ("lsv-profiles", "lsv-profile"),
]
