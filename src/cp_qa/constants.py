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
    "service-gtp",
    # Application & URL Filtering
    "application-site",
    "application-site-category",
    "application-site-group",
    # Identity & Access
    "access-role",
    "identity-tag",
    # Threat Prevention
    "threat-indicator",
    "threat-ioc-feed",
    "threat-profile",
    # Gateways & Servers
    "simple-gateway",
    "checkpoint-host",
    "interoperable-device",
    # VPN Communities
    "vpn-community-meshed",
    "vpn-community-star",
    # Users & Authentication
    "user",
    "user-group",
    "user-template",
    "trusted-client",
    "passcode-profile",
    "administrator",
    # Data Loss Prevention
    "data-type-keywords",
    "data-type-patterns",
    "data-type-file-attributes",
    "data-type-group",
    "data-type-weighted-keywords",
    "data-type-compound-group",
    "data-type-traditional-group",
    # Certificates & PKI
    "custom-trusted-ca-certificate",
    "external-trusted-ca",
    "opsec-trusted-ca",
    "outbound-inspection-certificate",
    "server-certificate",
    # Auth Servers
    "radius-server",
    "tacacs-server",
    "radius-group",
    "tacacs-group",
    # Network — Extended
    "access-point-name",
    "dynamic-global-network-object",
    "network-probe",
    "updatable-object",
    # Services — Extended
    "resource-cifs",
    "resource-ftp",
    "resource-smtp",
    "resource-tcp",
    "resource-uri",
    "resource-mms",
    "resource-uri-for-qos",
    "scada-application",
    # Logging & Monitoring
    "smtp-server",
    "syslog-server",
    "log-exporter",
    "smart-task",
    # Management & System
    "generic-object",
    "opsec-application",
    "mobile-profile",
    "limit",
    "override-categorization",
    "exception-group",
    "gaia-best-practice",
    "securemote-dns-server",
    # Gateways — Extended
    "interface",
    "multiple-key-exchanges",
    # Policy & Rules
    "package",
    "access-layer",
    "access-rule",
    "access-section",
    "nat-rule",
    "nat-section",
    "threat-layer",
    "threat-rule",
    "threat-exception",
    "https-layer",
    "https-rule",
    "https-section",
    "mobile-access-rule",
    "mobile-access-section",
    "mobile-access-profile-rule",
    "mobile-access-profile-section",
    # Data Center Integration (infrastructure-dependent)
    "data-center-server",
    "data-center-object",
    "data-center-query",
    # MDS (Multi-Domain, infrastructure-dependent)
    "domain",
    "domain-permissions-profile",
    "md-permissions-profile",
    "mds",
    "global-assignment",
    # External Auth (infrastructure-dependent)
    "azure-ad",
    "identity-provider",
    "idp-administrator-group",
    "ldap-group",
    "securid-server",
    # LSM (infrastructure-dependent)
    "lsm-cluster",
    "lsm-gateway",
    # Other (infrastructure-dependent)
    "if-map-server",
    "central-license",
    "repository-package",
    "repository-script",
    "api-key",
    # Known-slow types (run last to avoid blocking other tests)
    "simple-cluster",
    "lsv-profile",
]

# ---------------------------------------------------------------------------
# Cleanup dependency ordering
# ---------------------------------------------------------------------------

#: Deletion order for demo cleanup.  Objects earlier in this list are
#: deleted **first** — dependents before the objects they reference.
CLEANUP_ORDER: list[str] = [
    "package",  # cascade-deletes all rules + layers
    # Policy objects (if not inside a package)
    "exception-group",
    "access-layer",
    "threat-layer",
    "https-layer",
    # Groups (before their members)
    "application-site-group",
    "service-group",
    "vpn-community-meshed",
    "vpn-community-star",
    "group-with-exclusion",
    "time-group",
    "group",
    "gsn-handover-group",
    # DLP groups before DLP members
    "data-type-compound-group",
    "data-type-traditional-group",
    "data-type-group",
    "data-type-keywords",
    "data-type-patterns",
    "data-type-file-attributes",
    "data-type-weighted-keywords",
    # User groups before users
    "user-group",
    "user",
    "user-template",
    "administrator",
    "trusted-client",
    "passcode-profile",
    # Auth groups before auth servers
    "radius-group",
    "tacacs-group",
    "radius-server",
    "tacacs-server",
    # Resources (before their service-tcp dependencies)
    "resource-cifs",
    "resource-ftp",
    "resource-smtp",
    "resource-tcp",
    "resource-uri",
    "resource-mms",
    "resource-uri-for-qos",
    # Core network objects
    "host",
    "network",
    "wildcard",
    "address-range",
    "multicast-address-range",
    "dns-domain",
    "security-zone",
    "dynamic-object",
    "dynamic-global-network-object",
    "tag",
    "time",
    "network-feed",
    "access-point-name",
    "updatable-object",
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
    "service-gtp",
    "scada-application",
    # Application & URL Filtering
    "application-site",
    "application-site-category",
    # Identity & Access
    "access-role",
    "identity-tag",
    "idp-administrator-group",
    # Threat Prevention
    "threat-indicator",
    "threat-ioc-feed",
    "threat-profile",
    # Certificates
    "custom-trusted-ca-certificate",
    "external-trusted-ca",
    "opsec-trusted-ca",
    "outbound-inspection-certificate",
    "server-certificate",
    # Logging & Monitoring
    "smtp-server",
    "syslog-server",
    "log-exporter",
    "smart-task",
    "network-probe",
    # Management
    "generic-object",
    "opsec-application",
    "mobile-profile",
    "limit",
    "override-categorization",
    "gaia-best-practice",
    "securemote-dns-server",
    # Gateways — Extended
    "interface",
    "multiple-key-exchanges",
    # Gateways & Servers
    "simple-gateway",
    "simple-cluster",
    "checkpoint-host",
    "interoperable-device",
    "lsv-profile",
    # Data Center
    "data-center-query",
    "data-center-object",
    "data-center-server",
    # MDS
    "global-assignment",
    "domain",
    "domain-permissions-profile",
    "md-permissions-profile",
    "mds",
    # External Auth
    "azure-ad",
    "identity-provider",
    "ldap-group",
    "securid-server",
    # LSM
    "lsm-cluster",
    "lsm-gateway",
    # Other
    "if-map-server",
    "central-license",
    "repository-package",
    "repository-script",
    "api-key",
]

# ---------------------------------------------------------------------------
# Server-side discovery: plural "show" command -> singular type
# ---------------------------------------------------------------------------

#: Mapping of ``show-<plural>`` commands to singular type names.
#: Used by ``discover_demo_objects()`` to sweep the server for leftover
#: objects whose names match a known prefix (DEMO_, QA_, etc.).
#: Note: Rule/section types use singular show commands and are cleaned
#: up via package cascade deletion, so they are not listed here.
DISCOVERABLE_TYPES: list[tuple[str, str]] = [
    # Policy & rules (must be deleted first)
    ("packages", "package"),
    ("exception-groups", "exception-group"),
    ("access-layers", "access-layer"),
    ("threat-layers", "threat-layer"),
    ("https-layers", "https-layer"),
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
    # DLP
    ("data-type-compound-groups", "data-type-compound-group"),
    ("data-type-traditional-groups", "data-type-traditional-group"),
    ("data-type-groups", "data-type-group"),
    ("data-type-keywords", "data-type-keywords"),
    ("data-type-patterns", "data-type-patterns"),
    ("data-type-file-attributes", "data-type-file-attributes"),
    ("data-type-weighted-keywords", "data-type-weighted-keywords"),
    # Users & Auth
    ("user-groups", "user-group"),
    ("users", "user"),
    ("user-templates", "user-template"),
    ("administrators", "administrator"),
    ("trusted-clients", "trusted-client"),
    ("passcode-profiles", "passcode-profile"),
    # Auth groups / servers
    ("radius-groups", "radius-group"),
    ("tacacs-groups", "tacacs-group"),
    ("radius-servers", "radius-server"),
    ("tacacs-servers", "tacacs-server"),
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
    ("dynamic-global-network-objects", "dynamic-global-network-object"),
    ("tags", "tag"),
    ("times", "time"),
    ("network-feeds", "network-feed"),
    ("access-point-names", "access-point-name"),
    ("updatable-objects", "updatable-object"),
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
    ("service-gtp", "service-gtp"),
    ("scada-applications", "scada-application"),
    # Application & URL Filtering
    ("application-sites", "application-site"),
    ("application-site-categories", "application-site-category"),
    # Identity & Access
    ("access-roles", "access-role"),
    ("identity-tags", "identity-tag"),
    ("idp-administrator-groups", "idp-administrator-group"),
    # Threat Prevention
    ("threat-indicators", "threat-indicator"),
    ("threat-ioc-feeds", "threat-ioc-feed"),
    ("threat-profiles", "threat-profile"),
    # Certificates
    ("custom-trusted-ca-certificates", "custom-trusted-ca-certificate"),
    ("external-trusted-cas", "external-trusted-ca"),
    ("opsec-trusted-cas", "opsec-trusted-ca"),
    ("outbound-inspection-certificates", "outbound-inspection-certificate"),
    ("server-certificates", "server-certificate"),
    # Logging & Monitoring
    ("smtp-servers", "smtp-server"),
    ("syslog-servers", "syslog-server"),
    ("log-exporters", "log-exporter"),
    ("smart-tasks", "smart-task"),
    ("network-probes", "network-probe"),
    # Management
    ("generic-objects", "generic-object"),
    ("opsec-applications", "opsec-application"),
    ("mobile-profiles", "mobile-profile"),
    ("limits", "limit"),
    ("override-categorizations", "override-categorization"),
    ("gaia-best-practices", "gaia-best-practice"),
    ("securemote-dns-servers", "securemote-dns-server"),
    # Gateways & servers
    ("simple-gateways", "simple-gateway"),
    ("simple-clusters", "simple-cluster"),
    ("checkpoint-hosts", "checkpoint-host"),
    ("interoperable-devices", "interoperable-device"),
    ("lsv-profiles", "lsv-profile"),
    # Data Center
    ("data-center-servers", "data-center-server"),
    ("data-center-objects", "data-center-object"),
    # MDS
    ("domains", "domain"),
    ("domain-permissions-profiles", "domain-permissions-profile"),
    ("md-permissions-profiles", "md-permissions-profile"),
    ("mdss", "mds"),
    ("global-assignments", "global-assignment"),
    # External Auth
    ("azure-ads", "azure-ad"),
    ("identity-providers", "identity-provider"),
    ("ldap-groups", "ldap-group"),
    ("securid-servers", "securid-server"),
    # LSM
    ("lsm-clusters", "lsm-cluster"),
    ("lsm-gateways", "lsm-gateway"),
    # Other
    ("if-map-servers", "if-map-server"),
    ("central-licenses", "central-license"),
    ("repository-packages", "repository-package"),
    ("repository-scripts", "repository-script"),
]
