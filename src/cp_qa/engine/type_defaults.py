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
    # Universal fix: Ensure interfaces don't contain ambiguous or invalid parameters
    log.info(f"DEBUG: apply_type_defaults called for {obj_type}. Payload keys: {list(payload.keys())}")
    
    # NUCLEAR OPTION: Remove interfaces from gateways to bypass validation hell
    if obj_type in ("simple-gateway", "simple-cluster") and "interfaces" in payload:
        log.info(f"DEBUG: Nuclear option - removing interfaces from {obj_type}")
        payload.pop("interfaces", None)

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

            # 2. Type-specific parameter stripping
            if obj_type == "host":
                # Hosts do NOT support ip-address, topology, anti-spoofing, etc.
                for f in ["ip-address", "topology", "topology-settings", "anti-spoofing", "anti-spoofing-settings", "security-zone", "security-zone-settings"]:
                    iface.pop(f, None)
                # Hosts prefer 'subnet' + 'mask-length'
                if "subnet4" in iface:
                    iface["subnet"] = iface.pop("subnet4")
                    iface["mask-length"] = iface.pop("mask-length4", 24)
            
            elif obj_type in ("simple-gateway", "simple-cluster"):
                # Gateways prefer 'ip-address' + 'mask-length'
                if "subnet" in iface:
                    iface["ip-address"] = iface.pop("subnet")
                if "subnet4" in iface:
                    iface["ip-address"] = iface.pop("subnet4")
                    iface.pop("mask-length4", None)
                # Gateways do NOT support 'subnet' as a direct field (it's ambiguous)
                iface.pop("subnet", None)
                
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
        # Time objects need proper date/recurrence format — not random strings
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors"},
        )
        payload["start-now"] = True
        payload["end-never"] = True

    elif obj_type == "time-group":
        _keep_only(
            payload,
            {
                "name", "color", "comments", "members",
                "ignore-warnings", "ignore-errors",
            },
        )

    elif obj_type == "network-feed":
        # Needs a valid feed-url at minimum
        payload["feed-url"] = (
            "https://secureupdates.checkpoint.com/IP-list/TOR.txt"
        )
        payload["feed-format"] = "Flat List"
        payload["feed-type"] = "IP Address"
        for f in [
            "certificate-id", "custom-header", "data-column",
            "fields-delimiter", "ignore-lines-that-start-with",
            "json-query", "use-gateway-proxy", "update-interval",
        ]:
            payload.pop(f, None)

    elif obj_type in ("simple-gateway", "simple-cluster"):
        _keep_only(
            payload,
            {
                "name", "color", "comments",
                "ignore-warnings", "ignore-errors", "ipv4-address", "vpn",
                "version",
            },
        )
        payload["ipv4-address"] = f"10.100.99.{random.randint(10, 200)}"
        if "version" not in payload:
            payload["version"] = "R81.10"
        payload["vpn"] = True
        payload["ignore-warnings"] = True

    elif obj_type == "checkpoint-host":
        _keep_only(
            payload,
            {
                "name", "color", "comments",
                "ignore-warnings", "ignore-errors", "ipv4-address",
                "host-servers"
            },
        )
        # Remove nat-settings to avoid complex validation errors in demo
        payload.pop("nat-settings", None)
        payload["ipv4-address"] = f"10.100.98.{random.randint(10, 200)}"

    elif obj_type.startswith("simple-gateway") or obj_type.startswith("simple-cluster"):
         # Fix visitor mode error
         payload.pop("visitor-mode-interface", None)
         # Disable mobile access to avoid dependency on visitor mode
         payload["mobile-access"] = False
         
    elif obj_type == "interoperable-device":
        _keep_only(
            payload,
            {
                "name", "color", "comments",
                "ignore-warnings", "ignore-errors", "ipv4-address",
            },
        )
        payload["ipv4-address"] = f"10.100.97.{random.randint(10, 200)}"

    elif obj_type == "lsv-profile":
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors",
             "certificate-authority", "restrict-allowed-addresses",
             "allowed-ip-addresses"},
        )
        # certificate-authority is required — use the built-in ICA
        payload["certificate-authority"] = "internal_ca"
        payload["restrict-allowed-addresses"] = False
        payload["allowed-ip-addresses"] = []

    # ------------------------------------------------------------------
    # Services
    # ------------------------------------------------------------------
    elif obj_type == "service-tcp":
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors",
             "port", "source-port",
             "protocol",
             "session-timeout", "use-default-session-timeout",
             "match-for-any", "match-by-protocol-signature",
             "override-default-settings",
             "keep-connections-open-after-policy-installation",
             "sync-connections-on-cluster",
             "use-delayed-sync", "delayed-sync-value",
             "aggressive-aging",
             "enable-tcp-resource"},
        )
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
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors",
             "port", "source-port",
             "protocol",
             "session-timeout", "use-default-session-timeout",
             "accept-replies",
             "match-for-any", "match-by-protocol-signature",
             "override-default-settings",
             "keep-connections-open-after-policy-installation",
             "sync-connections-on-cluster",
             "aggressive-aging"},
        )
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
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors",
             "icmp-type", "icmp-code",
             "keep-connections-open-after-policy-installation"},
        )
        payload["icmp-type"] = 5    # Redirect
        payload["icmp-code"] = 7
        payload["keep-connections-open-after-policy-installation"] = False

    elif obj_type == "service-icmp6":
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors",
             "icmp-type", "icmp-code",
             "keep-connections-open-after-policy-installation"},
        )
        payload["icmp-type"] = 128  # Echo Request (ICMPv6)
        payload["icmp-code"] = 0
        payload["keep-connections-open-after-policy-installation"] = False

    elif obj_type == "service-sctp":
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors",
             "port", "source-port",
             "session-timeout", "use-default-session-timeout",
             "match-for-any",
             "keep-connections-open-after-policy-installation",
             "sync-connections-on-cluster",
             "aggressive-aging"},
        )
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
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors",
             "ip-protocol", "match", "action",
             "accept-replies",
             "override-default-settings",
             "session-timeout", "use-default-session-timeout",
             "match-for-any",
             "keep-connections-open-after-policy-installation",
             "sync-connections-on-cluster",
             "aggressive-aging"},
        )
        payload["ip-protocol"] = 51  # AH (Authentication Header)
        payload["accept-replies"] = False
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
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors",
             "interface-uuid",
             "keep-connections-open-after-policy-installation"},
        )
        payload["interface-uuid"] = "97aeb460-9aea-11d5-bd16-0090272ccb30"
        payload["keep-connections-open-after-policy-installation"] = False

    elif obj_type == "service-rpc":
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors",
             "program-number",
             "keep-connections-open-after-policy-installation"},
        )
        payload["program-number"] = 5669
        payload["keep-connections-open-after-policy-installation"] = False

    elif obj_type == "service-compound-tcp":
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors",
             "compound-service",
             "keep-connections-open-after-policy-installation"},
        )
        # compound-service enum: pointcast | netcaster | backweb | cdf
        payload["compound-service"] = "pointcast"
        payload["keep-connections-open-after-policy-installation"] = False

    elif obj_type == "service-citrix-tcp":
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors",
             "application"},
        )
        payload.setdefault("application", "My Citrix Application")

    elif obj_type == "service-group":
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors",
             "members"},
        )
        # Empty group is valid — members reference existing services
        payload.pop("members", None)

    # ------------------------------------------------------------------
    # Application & URL Filtering
    # ------------------------------------------------------------------
    elif obj_type == "application-site":
        # application-signature and url-list are MUTUALLY EXCLUSIVE — use url-list only
        payload.pop("application-signature", None)
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors",
             "primary-category", "url-list",
             "additional-categories", "description",
             "urls-defined-as-regular-expression"},
        )
        payload["primary-category"] = "Custom_Application_Site"
        payload["url-list"] = ["https://qa-test-example.com"]
        payload["additional-categories"] = []
        payload["description"] = "QA test application site"
        payload["urls-defined-as-regular-expression"] = False

    elif obj_type == "application-site-category":
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors",
             "description"},
        )
        payload["description"] = "QA test application site category"

    elif obj_type == "application-site-group":
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors",
             "members"},
        )
        # Empty group is valid — members reference existing app sites
        payload.pop("members", None)

    # ------------------------------------------------------------------
    # Identity & Access
    # ------------------------------------------------------------------
    elif obj_type == "access-role":
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors",
             "machines", "networks", "remote-access-clients", "users"},
        )
        # Use built-in "Any" for all reference fields
        payload["machines"] = "Any"
        payload["networks"] = "Any"
        payload["remote-access-clients"] = "Any"
        payload["users"] = "Any"

    elif obj_type == "identity-tag":
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors",
             "external-identifier"},
        )
        payload.setdefault("external-identifier", "qa-test-identity-tag")

    # ------------------------------------------------------------------
    # Threat Prevention
    # ------------------------------------------------------------------
    elif obj_type == "threat-indicator":
        _keep_only(
            payload,
            {"name", "color", "comments", "ignore-warnings", "ignore-errors",
             "action", "profile-overrides"},
        )
        # action enum: Inactive | Ask | Prevent | Detect
        payload["action"] = "Detect"
        # profile-overrides: override threat prevention profiles per indicator
        payload["profile-overrides"] = []
        # observables: list of indicator data (IP-based observable)
        # Must NOT coexist with observables-raw-data
        payload["observables"] = [
            {
                "name": "qa-test-observable",
                "ip-address": "198.51.100.99",
            }
        ]

    # ------------------------------------------------------------------
    # VPN Communities
    # ------------------------------------------------------------------
    elif obj_type in ("vpn-community-meshed", "vpn-community-star"):
        _apply_vpn_community_defaults(obj_type, payload, spec, current_obj_type)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _keep_only(payload: dict, allowed: set[str]) -> None:
    """Remove all keys from *payload* that are not in *allowed*."""
    for key in list(payload.keys()):
        if key not in allowed:
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

    # Strip everything not in safe_fields
    for key in list(payload.keys()):
        if key not in safe_fields:
            payload.pop(key, None)
