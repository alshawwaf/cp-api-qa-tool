# Known Limitations: Infrastructure-Dependent API Types

**Generated:** 2026-02-16
**Server:** R81.10 (API v2.0.1) — Standard single-domain SMS
**Coverage:** 108/134 types PASS (81%) | 26 types require external infrastructure

## Summary

The following 26 Check Point Management API types cannot be tested on a
standard single-domain Security Management Server (SMS). Each requires
specific infrastructure that is not present in a typical lab environment.

## Infrastructure-Dependent Types

| # | Type | Category | Required Infrastructure |
|:--|:-----|:---------|:----------------------|
| | **Multi-Domain Server (7)** | | |
| 1 | `trusted-client` | MDS | Multi-Domain Server — `err_inappropriate_domain_type` |
| 2 | `administrator` | MDS | Multi-Domain Server — `err_inappropriate_domain_type` |
| 3 | `domain` | MDS | MDS domain management |
| 4 | `domain-permissions-profile` | MDS | MDS permission profiles |
| 5 | `md-permissions-profile` | MDS | Multi-domain permission profiles |
| 6 | `mds` | MDS | MDS server object management |
| 7 | `global-assignment` | MDS | Cross-domain policy assignment |
| | **Data Center / Cloud (3)** | | |
| 8 | `data-center-server` | Cloud | AWS / Azure / GCP / VMware credentials |
| 9 | `data-center-object` | Cloud | Active `data-center-server` connection |
| 10 | `data-center-query` | Cloud | Active `data-center-server` connection |
| | **External Identity / Auth (5)** | | |
| 11 | `azure-ad` | Ext Auth | Azure AD tenant + credentials |
| 12 | `identity-provider` | Ext Auth | SAML / OIDC IdP endpoint |
| 13 | `idp-administrator-group` | Ext Auth | Active `identity-provider` |
| 14 | `ldap-group` | Ext Auth | LDAP / Active Directory server |
| 15 | `securid-server` | Ext Auth | RSA SecurID appliance |
| | **Large Scale Management (2)** | | |
| 16 | `lsm-cluster` | LSM | LSM-enabled management + provisioning profiles |
| 17 | `lsm-gateway` | LSM | LSM-enabled management + provisioning profiles |
| | **Network Extended (2)** | | |
| 18 | `dynamic-global-network-object` | Network | External dynamic IP feed infrastructure |
| 19 | `updatable-object` | Network | Read-only system objects (no ADD command) |
| | **VPN / Remote Access (1)** | | |
| 20 | `securemote-dns-server` | VPN | VPN Remote Access blade + Mobile Access |
| | **Gateway OS (1)** | | |
| 21 | `gaia-best-practice` | Gaia | Gaia OS running on managed gateway |
| | **Other Infrastructure (5)** | | |
| 22 | `if-map-server` | IF-MAP | IF-MAP metadata sharing server |
| 23 | `central-license` | Licensing | SmartUpdate licensing infrastructure |
| 24 | `repository-package` | SmartUpdate | Software package distribution repository |
| 25 | `repository-script` | SmartUpdate | Script distribution repository |
| 26 | `api-key` | Management | API key provisioning context |

## Verified PASS Types (108)

All 108 types below pass lifecycle testing on a standard single-domain
SMS lab.  Most run the standard ADD / SET / SHOW / DELETE cycle; four
non-standard types use custom lifecycle handlers (see note below):

| Category | Types |
|:---------|:------|
| Core Network (14) | `host`, `network`, `group`, `address-range`, `multicast-address-range`, `group-with-exclusion`, `dns-domain`, `wildcard`, `security-zone`, `dynamic-object`, `tag`, `time`, `time-group`, `gsn-handover-group` |
| Network Extended (2) | `network-feed`, `access-point-name` |
| Services (12) | `service-tcp`, `service-udp`, `service-icmp`, `service-icmp6`, `service-sctp`, `service-other`, `service-dce-rpc`, `service-rpc`, `service-compound-tcp`, `service-citrix-tcp`, `service-group`, `service-gtp` |
| Applications (4) | `application-site`, `application-site-category`, `application-site-group`, `scada-application` |
| Identity (2) | `access-role`, `identity-tag` |
| Threat Prevention (3) | `threat-indicator`, `threat-ioc-feed`, `threat-profile` |
| Gateways (5) | `simple-gateway`, `simple-cluster`, `checkpoint-host`, `interoperable-device`, `lsv-profile` |
| VPN (2) | `vpn-community-meshed`, `vpn-community-star` |
| Users (4) | `user`, `user-group`, `user-template`, `passcode-profile` |
| DLP (7) | `data-type-keywords`, `data-type-patterns`, `data-type-file-attributes`, `data-type-group`, `data-type-weighted-keywords`, `data-type-compound-group`, `data-type-traditional-group` |
| Certificates (5) | `custom-trusted-ca-certificate`, `external-trusted-ca`, `opsec-trusted-ca`, `outbound-inspection-certificate`, `server-certificate` |
| Auth Servers (4) | `radius-server`, `tacacs-server`, `radius-group`, `tacacs-group` |
| Resources (7) | `resource-cifs`, `resource-ftp`, `resource-smtp`, `resource-tcp`, `resource-uri`, `resource-mms`, `resource-uri-for-qos` |
| Logging (4) | `smtp-server`, `syslog-server`, `log-exporter`, `smart-task` |
| Management (7) | `generic-object`, `opsec-application`, `mobile-profile`, `limit`, `override-categorization`, `exception-group`, `network-probe` |
| Gateway Extended (2) | `interface`, `multiple-key-exchanges` |
| Policy Stack (19) | `package`, `access-layer`, `access-rule`, `access-section`, `nat-rule`, `nat-section`, `threat-layer`, `threat-rule`, `threat-exception`, `https-layer`, `https-rule`, `https-section`, `mobile-access-rule`, `mobile-access-section`, `mobile-access-profile-rule`, `mobile-access-profile-section` |
| Batch / Non-Standard (4) | `threat-protections`, `web-console-statistics`, `objects-batch`, `rules-batch` |

**Notes:**

- Certificate types (`custom-trusted-ca-certificate`, `external-trusted-ca`,
  `opsec-trusted-ca`, `outbound-inspection-certificate`, `server-certificate`) and
  `generic-object` skip the SET step (immutable types / non-standard schema) but
  pass ADD, SHOW, and DELETE.
- **Non-standard lifecycle types** use custom handlers instead of the standard
  CRUD cycle:
  - `threat-protections` — built-in objects; lifecycle is SHOW → SET → SHOW → revert
    (no ADD/DELETE since protections are system-managed).
  - `web-console-statistics` — ADD (write) and SHOW (read) only; no SET or DELETE.
  - `objects-batch` — batch ADD → SET → DELETE of multiple objects in one call (async).
  - `rules-batch` — batch ADD → DELETE of rules in a layer (async; no SET).
