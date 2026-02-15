"""Type-specific known-good payload defaults.

Some object types (time, network-feed, simple-gateway, etc.) require
very specific field combinations that the generic payload generator
cannot infer.  This module applies proven-working overrides **before**
the first API call to prevent known failures.

Called by :func:`lifecycle.run_lifecycle_test` and
:func:`demo.run_demo_create` before the adaptive ADD loop.
"""

from __future__ import annotations

import random

from cp_qa.logging import get_logger

log = get_logger(__name__)


def apply_type_defaults(
    obj_type: str,
    payload: dict,
    spec: dict | None = None,
    current_obj_type: str = "",
) -> None:
    """Apply type-specific known-good defaults to *payload* in-place.

    Args:
        obj_type:         The Check Point object type (e.g. ``"time"``).
        payload:          Request payload dict (modified in-place).
        spec:             Parsed API spec (needed for VPN community sub-objects).
        current_obj_type: Top-level object type context for test-data generation.
    """
    log.info(f"DEBUG: apply_type_defaults called for {obj_type}. Payload keys: {list(payload.keys())}")
    
    # details-level is a session-level parameter; sending it on create causes
    # validation failures on some types — strip universally
    if obj_type != "session":
        payload.pop("details-level", None)

    # ------------------------------------------------------------------
    # Universal Interface Normalization
    # ------------------------------------------------------------------
    if "interfaces" in payload and isinstance(payload["interfaces"], list):
        for iface in payload["interfaces"]:
            if not isinstance(iface, dict):
                continue
            
            # 1. Parameter Normalization
            if "subnet" in iface and "ip-address" in iface:
                iface.pop("subnet", None) # Prefer ip-address for gateways
            if "subnet-mask" in iface and "mask-length" in iface:
                iface.pop("subnet-mask", None)
            
            # Debug logging
            log.info(f"DEBUG: Processing iface for {obj_type}: {list(iface.keys())}")

            if obj_type == "host":
                # Host interfaces are very restricted. Keep ONLY name and IPv4/IPv6.
                # Actually, if we send interfaces, the server might REQUIRE subnet/mask.
                allowed = {"name", "ipv4-address", "ipv6-address", "subnet", "mask-length", "mask-length4"}
                for f in list(iface.keys()):
                    if f not in allowed:
                        iface.pop(f, None)
                # Ensure no conflict between ip-address and ipv4-address
                if "ip-address" in iface and "ipv4-address" in iface:
                    iface.pop("ip-address", None)
                
                # CRITICAL: For host, top-level address is REQUIRED on create.
                # Do NOT pop it from payload.
                pass
            
            elif obj_type in ("simple-gateway", "simple-cluster"):
                # Gateways prefer 'ip-address' + 'mask-length'
                if "subnet" in iface:
                    iface["ip-address"] = iface.pop("subnet")
                if "subnet4" in iface:
                    iface["ip-address"] = iface.pop("subnet4")
                    iface.pop("mask-length4", None)
                # Gateways do NOT support 'subnet' as a direct field (it's ambiguous)
                iface.pop("subnet", None)
                # Gateways do NOT support ignore-warnings/errors inside the interfaces list
                iface.pop("ignore-warnings", None)
                iface.pop("ignore-errors", None)
                
            # 3. Final cleanup of unrecognized generic parameters
            iface.pop("subnet4", None)
            iface.pop("mask-length4", None)

            # 4. Remove 'name' and 'subnet' from sub-settings, OR just disable AS for demo simplicity
            if obj_type.startswith("simple-gateway") or obj_type.startswith("simple-cluster"):
                 # Force disable anti-spoofing to avoid parameter hell
                 iface["anti-spoofing"] = False
                 iface.pop("anti-spoofing-settings", None)
                 # Double check no leakage
                 for k in list(iface.keys()):
                     if "anti-spoofing" in k and k != "anti-spoofing":
                         iface.pop(k, None)

            for setting in ["topology-settings", "security-zone-settings"]:
                if setting in iface and isinstance(iface[setting], dict):
                    iface[setting].pop("name", None)
    
    if obj_type == "time":
        # Time objects need specific toggle consistency
        payload["start-now"] = True
        payload["end-never"] = True
        # Safe recurrence (single weekly pattern avoids server NPE)
        payload["recurrence"] = {
            "pattern": "Weekly",
            "weekdays": ["Mon"],
        }
        payload["hours-ranges"] = [{"from": "00:00", "to": "23:59"}]

    elif obj_type == "network-feed":
        # Needs a valid feed-url at minimum
        payload["feed-url"] = ("https://secureupdates.checkpoint.com/IP-list/TOR.txt")
        payload["feed-format"] = "Flat List"
        payload["feed-type"] = "IP Address"

    elif obj_type in ("simple-gateway", "simple-cluster", "checkpoint-host"):
        # STRATEGY CHANGE: "Greedy" mode. We no longer strip 80% of fields.
        # We only fix required operational parameters.
        if "version" not in payload or not payload["version"]:
            payload["version"] = "R81.10"

        # Ensure name/ipv4 are set if missing from gen
        if "ipv4-address" not in payload:
            payload["ipv4-address"] = f"10.100.99.{random.randint(10, 200)}"

        # Blacklist unhandled complex fields that cause immediate rejection in basic labs
        _strip_conflicts(payload, {
            "visitor-mode-interface", # Depends on complex topology
            "proxies",                # Requires existing proxy objects
            "sic",                    # Logic handled via 'one-time-password'
            "hardware",               # Validation is vary strict on hardware strings
            "os-name",                # Validation is vary strict on OS strings
        })

        # Clusters use member-based topology, not direct interfaces
        if obj_type == "simple-cluster":
            payload.pop("interfaces", None)
            # Tags generated as {} (dict) instead of [] (list) — remove to avoid type error
            if isinstance(payload.get("tags"), dict):
                payload.pop("tags", None)
            # Members need minimal fields; strip nested interfaces and bad sub-params
            if "members" in payload and isinstance(payload["members"], list):
                clean_members = []
                for m in payload["members"]:
                    if not isinstance(m, dict):
                        continue
                    cm = {
                        "name": m.get("name", m.get("new-name", f"member_{random.randint(100,999)}")),
                        "ip-address": m.get("ip-address", f"10.100.1.{random.randint(10,200)}"),
                        "one-time-password": "vpn123!@#",
                    }
                    clean_members.append(cm)
                payload["members"] = clean_members if clean_members else []

    # ------------------------------------------------------------------
    # Universal Optimization
    # ------------------------------------------------------------------
    # 1. NAT conflict resolution: if hiding behind gateway, don't send IP in NAT
    nat = payload.get("nat-settings")
    if isinstance(nat, dict):
        if nat.get("method") == "hide" and nat.get("hide-behind") == "gateway":
            _strip_conflicts(nat, {"ip-address", "ipv4-address", "ipv6-address", "install-on"})
        # 2. General 'install-on' stripping to avoid environment-specific reference errors
        nat.pop("install-on", None)
        # 3. Gateway/Cluster specific NAT unrecognized parameter fix (auto-rule is top-level only)
    # 3.1 Surgical cleanup for nested operational fields
    def _surgical_cleanup(payload):
        # 0. Blade booleans: set to False (safe — proves API accepts the field
        #    without activating the blade or triggering prerequisite checks)
        for blade in (
            "firewall", "ips", "anti-bot", "anti-virus", "application-control",
            "url-filtering", "content-awareness", "data-loss-prevention",
            "mobile-access", "vpn", "monitoring", "identity-awareness",
            "threat-emulation", "threat-extraction", "zero-phishing",
            "icap-server", "qos", "hit-count",
        ):
            if blade in payload:
                payload[blade] = False

        # enable-https-inspection requires an outbound certificate even
        # when set to False — must be stripped entirely
        payload.pop("enable-https-inspection", None)
        payload.pop("https-inspection", None)

        # 1. Nested interfaces: remove complex settings that conflict on creation
        if "interfaces" in payload and isinstance(payload["interfaces"], list):
            for iface in payload["interfaces"]:
                if isinstance(iface, dict):
                    _strip_conflicts(iface, {
                        "security-zone-settings", "topology-settings",
                        "anti-spoofing-settings", "tags", "groups", "domains-to-process"
                    })

        # 2. Settings objects: strip all *-settings (deep dependency chains)
        for key in list(payload.keys()):
            if key.endswith("-settings") or "-settings" in key:
                payload.pop(key, None)

        # 3. Operational fields requiring external prerequisites
        _strip_conflicts(payload, {
            "version",                 # API rejects version on ADD even with valid values
            "one-time-password",       # SIC initialization requires manual pairing
            "sic-name",                # SIC trust requires established SIC
            "hardware",                # strict hardware string validation
            "os",                      # strict OS string validation
            "management-blades",       # nested blade objects with dependencies
            "send-logs-to-server",     # references log-server objects
            "send-alerts-to-server",   # references alert-server objects
            "send-logs-to-backup-server",  # references backup-server objects
            "save-logs-locally",       # may conflict with log-server settings
            "communication-with-servers-behind-nat",  # requires NAT topology
            "platform-portal-settings",  # requires portal infrastructure
            "auto-generate-ip",        # conflicts with explicit IP assignment
            "auto-topology-custom-recalculation-time",
            "auto-topology-use-custom-recalculation-time",
            "fetch-policy",            # references policy objects
        })

        # NAT has complex dependency chains — strip entirely
        payload.pop("nat-settings", None)

    if obj_type in ["simple-gateway", "simple-cluster", "checkpoint-host", "interoperable-device"]:
        _surgical_cleanup(payload)

    # 4. LSV profile cleanup
    if obj_type == "lsv-profile":
        # LSV profiles require a CA, but one CA can only handle one profile.
        # We try 'internal_ca' as default.
        payload["certificate-authority"] = "internal_ca"
        _strip_conflicts(payload, {
            "shared-secret", "vpn-domain",
            "allowed-ip-addresses", "restrict-allowed-addresses",
        })

    # 5. Interoperable Device / Gateway IP Fix
    if obj_type in ["interoperable-device", "simple-gateway", "simple-cluster", "checkpoint-host"]:
        # Interoperable devices have VERY minimal interfaces
        if obj_type == "interoperable-device" and "interfaces" in payload:
            for iface in payload["interfaces"]:
                _strip_conflicts(iface, {"anti-spoofing", "anti-spoofing-settings", "topology", "topology-settings", "domains-to-process"})
        
        # Checkpoint hosts don't like logs-settings without blades
        if obj_type == "checkpoint-host":
             payload.pop("logs-settings", None)

        if "ip-address" in payload and "ipv4-address" in payload:
            payload.pop("ip-address", None)

    # ------------------------------------------------------------------
    # Services
    # ------------------------------------------------------------------
    # Services
    # ------------------------------------------------------------------
    elif obj_type == "service-tcp":
        # Greedy mode: Remove only fields that strictly conflict
        if not payload.get("use-delayed-sync"):
            payload.pop("delayed-sync-value", None)
        if not payload.get("override-default-settings"):
            # If not overriding, don't send individual default-destined fields
            pass
        payload["port"] = "9090"
        payload["source-port"] = ">0"
        payload["protocol"] = ""
        payload["sync-connections-on-cluster"] = True
        payload["match-by-protocol-signature"] = False
        payload["override-default-settings"] = False
        payload["session-timeout"] = 3600
        payload["use-default-session-timeout"] = True
        payload["match-for-any"] = False
        payload["use-delayed-sync"] = False
        payload["delayed-sync-value"] = ""
        payload["aggressive-aging"] = {
            "enable": True,
            "timeout": 600,
            "use-default-timeout": False,
            "default-timeout": 0,
        }
        payload["keep-connections-open-after-policy-installation"] = False
        payload["enable-tcp-resource"] = False

    elif obj_type == "service-udp":
        # Greedy mode
        payload["port"] = "5060"
        payload["source-port"] = ">0"
        payload["protocol"] = ""
        payload["accept-replies"] = False
        payload["match-by-protocol-signature"] = False
        payload["override-default-settings"] = False
        payload["session-timeout"] = 0
        payload["use-default-session-timeout"] = True
        payload["match-for-any"] = True
        payload["sync-connections-on-cluster"] = True
        payload["aggressive-aging"] = {
            "enable": True,
            "timeout": 360,
            "use-default-timeout": False,
            "default-timeout": 0,
        }
        payload["keep-connections-open-after-policy-installation"] = False

    elif obj_type == "service-icmp":
        payload["icmp-type"] = 5    # Redirect
        payload["icmp-code"] = 7
        payload["keep-connections-open-after-policy-installation"] = False

    elif obj_type == "service-icmp6":
        payload["icmp-type"] = 128  # Echo Request (ICMPv6)
        payload["icmp-code"] = 0
        payload["keep-connections-open-after-policy-installation"] = False

    elif obj_type == "service-sctp":
        payload["port"] = "5669"
        payload["source-port"] = ">0"
        payload["session-timeout"] = 0
        payload["use-default-session-timeout"] = True
        payload["match-for-any"] = True
        payload["sync-connections-on-cluster"] = True
        payload["aggressive-aging"] = {
            "enable": True,
            "timeout": 360,
            "use-default-timeout": False,
            "default-timeout": 0,
        }
        payload["keep-connections-open-after-policy-installation"] = False

    elif obj_type == "service-other":
        payload["ip-protocol"] = 51  # AH (Authentication Header)
        # protocol field MUST NOT be a standard manual label like "TCP"
        payload["protocol"] = ""
        payload["override-default-settings"] = False
        payload["session-timeout"] = 0
        payload["use-default-session-timeout"] = True
        payload["match-for-any"] = True
        payload["sync-connections-on-cluster"] = True
        payload["aggressive-aging"] = {
            "enable": True,
            "timeout": 360,
            "use-default-timeout": False,
            "default-timeout": 0,
        }
        payload["keep-connections-open-after-policy-installation"] = False

    elif obj_type == "service-dce-rpc":
        payload["interface-uuid"] = "97aeb460-9aea-11d5-bd16-0090272ccb30"
        payload["keep-connections-open-after-policy-installation"] = False

    elif obj_type == "service-rpc":
        payload["program-number"] = 5669
        payload["keep-connections-open-after-policy-installation"] = False

    elif obj_type == "service-compound-tcp":
        payload["compound-service"] = "pointcast"
    elif obj_type == "service-citrix-tcp":
        payload.setdefault("application", "My Citrix Application")

    elif obj_type == "service-group":
        payload["members"] = []

    # ------------------------------------------------------------------
    # Application & URL Filtering
    # ------------------------------------------------------------------
    elif obj_type == "application-site":
        # application-signature and url-list are MUTUALLY EXCLUSIVE — use url-list only
        payload.pop("application-signature", None)
        payload["primary-category"] = "Custom_Application_Site"
        payload["url-list"] = ["https://qa-test-example.com"]
        payload["additional-categories"] = []
        payload["description"] = "QA test application site"
        payload["urls-defined-as-regular-expression"] = False

    elif obj_type == "application-site-group":
        payload["members"] = []

    # ------------------------------------------------------------------
    # Identity & Access
    # ------------------------------------------------------------------
    elif obj_type == "access-role":
        payload["machines"] = "any"
        payload["networks"] = "any"
        payload["remote-access-clients"] = "any"
        payload["users"] = "any"
    elif obj_type == "identity-tag":
        payload.setdefault("external-identifier", "qa-test-identity-tag")

    # ------------------------------------------------------------------
    # Threat Prevention
    # ------------------------------------------------------------------
    elif obj_type == "threat-indicator":
        payload["action"] = "Detect"
        payload["profile-overrides"] = []
        payload["observables"] = [
            {
                "name": "qa-test-observable",
                "ip-address": "198.51.100.99",
            }
        ]
        payload.pop("observables-raw-data", None)

    # ------------------------------------------------------------------
    # VPN Communities
    # ------------------------------------------------------------------
    elif obj_type in ("vpn-community-meshed", "vpn-community-star"):
        _apply_vpn_community_defaults(obj_type, payload, spec, current_obj_type)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_conflicts(payload: dict, problematic: set[str]) -> None:
    """Remove specific keys from *payload* that are known to fail."""
    for key in problematic:
        payload.pop(key, None)


def _apply_vpn_community_defaults(
    obj_type: str,
    payload: dict,
    spec: dict | None,
    current_obj_type: str,
) -> None:
    """Inject comprehensive defaults for VPN community objects.

    Populates every safe scalar field with valid values drawn from the
    OpenAPI spec and Check Point documentation.  Fields that reference
    external objects (shared-secrets, override-interfaces, granular-encryptions,
    etc.) are intentionally omitted because the referenced objects would
    need to exist first.
    """
    # --- Fields safe to send (no external object references) ---
    safe_fields = {
        "name", "color", "comments", "ignore-warnings", "ignore-errors",
        "tags", "set-if-exists",
        # Gateway lists (populated by _inject_helpers)
        "center-gateways", "satellite-gateways", "gateways",
        # Encryption & IKE
        "encryption-method", "encryption-suite",
        "ike-phase-1", "ike-phase-2",
        # Tunnel & routing
        "tunnel-granularity", "routing-mode", "link-selection-mode",
        # NAT
        "disable-nat",
        # Shared secret toggle (boolean, no references)
        "use-shared-secret",
        # Traffic & tunnel booleans/enums (no external refs)
        "encrypted-traffic", "wire-mode",
    }

    # Star-only fields
    if obj_type == "vpn-community-star":
        safe_fields |= {
            "mesh-center-gateways", "vpn-routing", "disable-nat-on",
        }

    # ------------------------------------------------------------------
    # Encryption settings (enum values from OpenAPI spec)
    # ------------------------------------------------------------------
    # encryption-suite must be "custom" to allow IKE phase customisation
    payload["encryption-suite"] = "custom"

    # Valid: prefer ikev2 but support ikev1 | ikev2 only
    #        | ikev1 for ipv4 and ikev2 for ipv6 only
    payload["encryption-method"] = "prefer ikev2 but support ikev1"

    # ------------------------------------------------------------------
    # IKE Phase 1  (only when encryption-suite == "custom")
    # Valid algorithms from spec:
    #   encryption-algorithm: aes-128, aes-256
    #   data-integrity:       sha1, sha256, sha384
    #   diffie-hellman-group: group-2, group-15, group-19
    # ------------------------------------------------------------------
    payload["ike-phase-1"] = {
        "encryption-algorithm": "aes-256",
        "data-integrity": "sha256",
        "diffie-hellman-group": "group-19",
        "ike-p1-rekey-time": 1440,
    }

    # ------------------------------------------------------------------
    # IKE Phase 2  (only when encryption-suite == "custom")
    # Valid algorithms from spec:
    #   encryption-algorithm: aes-128, aes-256, aes-gcm-128, aes-xcbc
    #   data-integrity:       sha1, sha256, sha384, aes-xcbc
    #   ike-p2-pfs-dh-grp:   group-15, group-19
    # ------------------------------------------------------------------
    payload["ike-phase-2"] = {
        "encryption-algorithm": "aes-256",
        "data-integrity": "sha256",
        "ike-p2-use-pfs": True,
        "ike-p2-pfs-dh-grp": "group-19",
        "ike-p2-rekey-time": 3600,
    }

    # ------------------------------------------------------------------
    # Tunnel & routing (enum values from spec)
    # ------------------------------------------------------------------
    # tunnel-granularity: per_host | per_subnet | universal
    payload["tunnel-granularity"] = "per_subnet"

    # routing-mode: domain_based | route_based
    payload["routing-mode"] = "domain_based"

    # link-selection-mode: enhanced | legacy
    payload["link-selection-mode"] = "legacy"

    # ------------------------------------------------------------------
    # NAT & shared secret
    # ------------------------------------------------------------------
    payload["disable-nat"] = False
    payload["use-shared-secret"] = False

    # ------------------------------------------------------------------
    # Star-only fields
    # ------------------------------------------------------------------
    if obj_type == "vpn-community-star":
        # vpn-routing: to center only | to center and to other satellites
        #              | to center other satellites and internet
        payload["vpn-routing"] = "to center and to other satellites"
        payload["mesh-center-gateways"] = False
        # disable-nat-on: satellite gateways only
        #                 | both center and satellite gateways
        payload["disable-nat-on"] = "both center and satellite gateways"

    # ------------------------------------------------------------------
    # Gateway lists — placeholders overridden by _inject_helpers()
    # ------------------------------------------------------------------
    if obj_type == "vpn-community-star":
        payload.setdefault("center-gateways", [])
        payload.setdefault("satellite-gateways", [])
    elif obj_type == "vpn-community-meshed":
        payload.setdefault("gateways", [])

    payload["ignore-warnings"] = True

    # Traffic & tunnel settings (safe booleans/enums)
    payload.setdefault("encrypted-traffic", "any")
    payload.setdefault("wire-mode", "off")

    # Strip everything not in safe_fields
    for key in list(payload.keys()):
        if key not in safe_fields:
            payload.pop(key, None)
