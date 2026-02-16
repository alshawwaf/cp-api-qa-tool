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


# ---------------------------------------------------------------------------
# Certificate generation utility
# ---------------------------------------------------------------------------

def _generate_self_signed_cert_pem() -> str:
    """Generate a self-signed X.509 certificate in base64 format.

    Used for certificate-related types (custom-trusted-ca-certificate,
    external-trusted-ca, opsec-trusted-ca, outbound-inspection-certificate,
    server-certificate).
    """
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "QA Test CA"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "QA Tool"),
        ])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .sign(key, hashes.SHA256())
        )
        pem = cert.public_bytes(serialization.Encoding.PEM).decode("ascii")
        lines = pem.strip().split("\n")
        b64 = "".join(ln for ln in lines if not ln.startswith("-----"))
        return b64
    except ImportError:
        # Fallback: minimal DER-encoded self-signed cert in base64
        return (
            "MIIBkTCB+wIJAKHBfpHYsSkCMA0GCSqGSIb3DQEBCwUAMBExDzANBgNVBAMMBlFB"
            "IENBMB4XDTI0MDEwMTAwMDAwMFoXDTI1MDEwMTAwMDAwMFowETEPMA0GA1UEAwwG"
            "UUEgQ0EwXDANBgkqhkiG9w0BAQEFAANLADBIAkEA0Z3VS5JJcds3xf0GVVsYMHBi"
            "aPMhBRpmRKYGKgScbMRbNQtODmGNkMi1a+SLnFJHJIrYDqm7PMfZg0qBWBGOwIDAQAB"
            "MA0GCSqGSIb3DQEBCwUAA0EA"
        )


def _generate_self_signed_cert_pkcs12() -> str:
    """Generate a self-signed cert in PKCS12 format (base64).

    Server-certificate requires both cert + private key in PKCS12 format,
    with a password provided via base64-password.
    """
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives.serialization import pkcs12
        import datetime, base64

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "QA Test Server"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "QA Tool"),
        ])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .sign(key, hashes.SHA256())
        )
        p12 = pkcs12.serialize_key_and_certificates(
            b"QA Test Server", key, cert, None,
            serialization.BestAvailableEncryption(b"pass"),
        )
        return base64.b64encode(p12).decode("ascii")
    except (ImportError, Exception):
        return _generate_self_signed_cert_pem()  # fallback


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

    # Spec generator sometimes creates list-type fields as {} instead of []
    for _list_field in ("tags", "groups", "members"):
        if isinstance(payload.get(_list_field), dict):
            payload[_list_field] = []

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
                allowed = {"name", "ipv4-address", "ipv6-address", "subnet", "mask-length", "mask-length4"}
                for f in list(iface.keys()):
                    if f not in allowed:
                        iface.pop(f, None)
                # Ensure no conflict between ip-address and ipv4-address
                if "ip-address" in iface and "ipv4-address" in iface:
                    iface.pop("ip-address", None)

                # CRITICAL: For host, top-level address is REQUIRED on create.
                pass

            elif obj_type in ("simple-gateway", "simple-cluster"):
                # Gateways prefer 'ip-address' + 'mask-length'
                if "subnet" in iface:
                    iface["ip-address"] = iface.pop("subnet")
                if "subnet4" in iface:
                    iface["ip-address"] = iface.pop("subnet4")
                    iface.pop("mask-length4", None)
                iface.pop("subnet", None)
                iface.pop("ignore-warnings", None)
                iface.pop("ignore-errors", None)

            # 3. Final cleanup of unrecognized generic parameters
            iface.pop("subnet4", None)
            iface.pop("mask-length4", None)

            # 4. Disable anti-spoofing for gateways/clusters
            if obj_type.startswith("simple-gateway") or obj_type.startswith("simple-cluster"):
                 iface["anti-spoofing"] = False
                 iface.pop("anti-spoofing-settings", None)
                 for k in list(iface.keys()):
                     if "anti-spoofing" in k and k != "anti-spoofing":
                         iface.pop(k, None)

            for setting in ["topology-settings", "security-zone-settings"]:
                if setting in iface and isinstance(iface[setting], dict):
                    iface[setting].pop("name", None)

    # ------------------------------------------------------------------
    # Type-specific defaults
    # ------------------------------------------------------------------
    if obj_type == "time":
        payload["start-now"] = True
        payload["end-never"] = True
        payload["recurrence"] = {
            "pattern": "Weekly",
            "weekdays": ["Mon"],
        }
        payload["hours-ranges"] = [{"from": "00:00", "to": "23:59"}]

    elif obj_type == "network-feed":
        payload["feed-url"] = ("https://secureupdates.checkpoint.com/IP-list/TOR.txt")
        payload["feed-format"] = "Flat List"
        payload["feed-type"] = "IP Address"

    elif obj_type in ("simple-gateway", "simple-cluster", "checkpoint-host"):
        if "version" not in payload or not payload["version"]:
            payload["version"] = "R81.10"
        if "ipv4-address" not in payload:
            payload["ipv4-address"] = f"10.100.99.{random.randint(10, 200)}"
        _strip_conflicts(payload, {
            "visitor-mode-interface", "proxies", "sic",
            "hardware", "os-name",
        })
        if obj_type == "simple-cluster":
            payload.pop("interfaces", None)
            if isinstance(payload.get("tags"), dict):
                payload.pop("tags", None)
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
    nat = payload.get("nat-settings")
    if isinstance(nat, dict):
        if nat.get("method") == "hide" and nat.get("hide-behind") == "gateway":
            _strip_conflicts(nat, {"ip-address", "ipv4-address", "ipv6-address", "install-on"})
        nat.pop("install-on", None)

    def _surgical_cleanup(payload):
        # Blade booleans: set to False (safe)
        for blade in (
            "firewall", "ips", "anti-bot", "anti-virus", "application-control",
            "url-filtering", "content-awareness", "data-loss-prevention",
            "mobile-access", "vpn", "monitoring", "identity-awareness",
            "threat-emulation", "threat-extraction", "zero-phishing",
            "icap-server", "qos", "hit-count",
        ):
            if blade in payload:
                payload[blade] = False
        payload.pop("enable-https-inspection", None)
        payload.pop("https-inspection", None)
        if "interfaces" in payload and isinstance(payload["interfaces"], list):
            for iface in payload["interfaces"]:
                if isinstance(iface, dict):
                    _strip_conflicts(iface, {
                        "security-zone-settings", "topology-settings",
                        "anti-spoofing-settings", "tags", "groups", "domains-to-process"
                    })
        for key in list(payload.keys()):
            if key.endswith("-settings") or "-settings" in key:
                payload.pop(key, None)
        _strip_conflicts(payload, {
            "version", "one-time-password", "sic-name", "hardware", "os",
            "management-blades", "send-logs-to-server", "send-alerts-to-server",
            "send-logs-to-backup-server", "save-logs-locally",
            "communication-with-servers-behind-nat", "platform-portal-settings",
            "auto-generate-ip", "auto-topology-custom-recalculation-time",
            "auto-topology-use-custom-recalculation-time", "fetch-policy",
            "threat-prevention-mode",
        })
        payload.pop("nat-settings", None)

    if obj_type in ["simple-gateway", "simple-cluster", "checkpoint-host", "interoperable-device"]:
        _surgical_cleanup(payload)

    if obj_type == "lsv-profile":
        payload["certificate-authority"] = "internal_ca"
        _strip_conflicts(payload, {
            "shared-secret", "vpn-domain",
            "allowed-ip-addresses", "restrict-allowed-addresses",
        })

    if obj_type in ["interoperable-device", "simple-gateway", "simple-cluster", "checkpoint-host"]:
        if obj_type == "interoperable-device" and "interfaces" in payload:
            for iface in payload["interfaces"]:
                _strip_conflicts(iface, {"anti-spoofing", "anti-spoofing-settings", "topology", "topology-settings", "domains-to-process"})
        if obj_type == "checkpoint-host":
             payload.pop("logs-settings", None)
        if "ip-address" in payload and "ipv4-address" in payload:
            payload.pop("ip-address", None)

    # ------------------------------------------------------------------
    # Services
    # ------------------------------------------------------------------
    if obj_type == "service-tcp":
        if not payload.get("use-delayed-sync"):
            payload.pop("delayed-sync-value", None)
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
            "enable": True, "timeout": 600,
            "use-default-timeout": False, "default-timeout": 0,
        }
        payload["keep-connections-open-after-policy-installation"] = False
        payload["enable-tcp-resource"] = False

    elif obj_type == "service-udp":
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
            "enable": True, "timeout": 360,
            "use-default-timeout": False, "default-timeout": 0,
        }
        payload["keep-connections-open-after-policy-installation"] = False

    elif obj_type == "service-icmp":
        payload["icmp-type"] = 5
        payload["icmp-code"] = 7
        payload["keep-connections-open-after-policy-installation"] = False

    elif obj_type == "service-icmp6":
        payload["icmp-type"] = 128
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
            "enable": True, "timeout": 360,
            "use-default-timeout": False, "default-timeout": 0,
        }
        payload["keep-connections-open-after-policy-installation"] = False

    elif obj_type == "service-other":
        payload["ip-protocol"] = 51
        payload["protocol"] = ""
        payload["override-default-settings"] = False
        payload["session-timeout"] = 0
        payload["use-default-session-timeout"] = True
        payload["match-for-any"] = True
        payload["sync-connections-on-cluster"] = True
        payload["aggressive-aging"] = {
            "enable": True, "timeout": 360,
            "use-default-timeout": False, "default-timeout": 0,
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

    elif obj_type == "service-gtp":
        payload["interface-type"] = "gn"
        # Strip everything except name + interface-type — most fields need
        # other GTP features to be enabled first
        for k in list(payload.keys()):
            if k not in ("name", "interface-type",
                         "ignore-warnings", "ignore-errors"):
                payload.pop(k, None)

    # ------------------------------------------------------------------
    # Application & URL Filtering
    # ------------------------------------------------------------------
    elif obj_type == "application-site":
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
            {"name": "qa-test-observable", "ip-address": "198.51.100.99"}
        ]
        payload.pop("observables-raw-data", None)

    elif obj_type == "threat-ioc-feed":
        payload["feed-url"] = "https://secureupdates.checkpoint.com/IP-list/TOR.txt"
        payload["feed-type"] = "IP Address"
        payload["action"] = "Detect"
        # Strip everything except essentials — many fields have interdependencies
        for k in list(payload.keys()):
            if k not in ("name", "feed-url", "feed-type", "action",
                         "ignore-warnings", "ignore-errors"):
                payload.pop(k, None)

    elif obj_type == "threat-profile":
        # Strip everything except name and basic fields — sub-objects contain invalid refs
        for k in list(payload.keys()):
            if k not in ("name", "color", "comments", "tags",
                         "ignore-warnings", "ignore-errors"):
                payload.pop(k, None)

    # ------------------------------------------------------------------
    # VPN Communities
    # ------------------------------------------------------------------
    elif obj_type in ("vpn-community-meshed", "vpn-community-star"):
        _apply_vpn_community_defaults(obj_type, payload, spec, current_obj_type)

    # ------------------------------------------------------------------
    # Users & Authentication
    # ------------------------------------------------------------------
    elif obj_type == "user":
        payload["authentication-method"] = "check point password"
        payload["password"] = "QaUser1234!@#$"
        payload["email"] = "qa-test@example.com"
        # Strip everything except essentials — many fields cause validation errors
        for k in list(payload.keys()):
            if k not in ("name", "authentication-method", "password",
                         "email", "ignore-warnings", "ignore-errors"):
                payload.pop(k, None)

    elif obj_type == "user-group":
        payload["members"] = []
        if "email" in payload:
            payload["email"] = "qa@example.com"

    elif obj_type == "user-template":
        payload["authentication-method"] = "check point password"
        if "expiration-date" in payload:
            payload["expiration-date"] = "2026-12-31"
        _strip_conflicts(payload, {
            "connect-on-days", "connect-daily", "from-hour", "to-hour",
            "allowed-locations", "encryption", "phone-number",
            "template",
        })

    elif obj_type == "trusted-client":
        payload.setdefault("ipv4-address", f"10.100.3.{random.randint(10, 200)}")
        payload.setdefault("type", "any")

    elif obj_type == "administrator":
        payload.setdefault("authentication-method", "check point password")
        payload.setdefault("password", "QaAdmin1234!@#$")
        payload.setdefault("permissions-profile", "Read Only All")
        _strip_conflicts(payload, {"multi-domain-profile", "sic-name", "phone-number"})

    # ------------------------------------------------------------------
    # Data Loss Prevention
    # ------------------------------------------------------------------
    elif obj_type == "data-type-keywords":
        # keywords list: each entry is just a string, not a dict
        payload["keywords"] = ["qa-test-keyword", "qa-test-keyword-2"]
        _strip_conflicts(payload, {"data-match-command-line"})

    elif obj_type == "data-type-patterns":
        payload.setdefault("patterns", ["\\d{4}-\\d{4}"])

    elif obj_type == "data-type-weighted-keywords":
        payload.setdefault("weighted-keywords", [
            {"keyword": "qa-test", "weight": 10, "max-weight": 100}
        ])

    elif obj_type == "data-type-file-attributes":
        # Needs at least one file attribute selected — use match-by-file-name
        for k in list(payload.keys()):
            if k not in ("name", "description", "match-by-file-name",
                         "file-name-contains",
                         "ignore-warnings", "ignore-errors"):
                payload.pop(k, None)
        payload.setdefault("description", "QA test file attributes")
        payload["match-by-file-name"] = True
        payload["file-name-contains"] = "qa_test"

    elif obj_type == "data-type-group":
        payload.setdefault("members", [])

    elif obj_type == "data-type-compound-group":
        # Needs matched-groups or unmatched-groups with real members
        for k in list(payload.keys()):
            if k not in ("name", "description",
                         "ignore-warnings", "ignore-errors"):
                payload.pop(k, None)
        payload.setdefault("description", "QA compound group")

    elif obj_type == "data-type-traditional-group":
        # Needs data-types members — cannot be empty
        for k in list(payload.keys()):
            if k not in ("name", "description",
                         "ignore-warnings", "ignore-errors"):
                payload.pop(k, None)
        payload.setdefault("description", "QA traditional group")

    # ------------------------------------------------------------------
    # Certificates & PKI
    # ------------------------------------------------------------------
    elif obj_type == "external-trusted-ca":
        cert_b64 = _generate_self_signed_cert_pem()
        payload["base64-certificate"] = cert_b64
        _strip_conflicts(payload, {"crl-cache-method", "crl-cache-timeout"})

    elif obj_type == "custom-trusted-ca-certificate":
        cert_b64 = _generate_self_signed_cert_pem()
        payload["base64-certificate"] = cert_b64
        # Strip everything except name and cert
        for k in list(payload.keys()):
            if k not in ("name", "base64-certificate",
                         "ignore-warnings", "ignore-errors"):
                payload.pop(k, None)

    elif obj_type == "opsec-trusted-ca":
        cert_b64 = _generate_self_signed_cert_pem()
        payload["base64-certificate"] = cert_b64
        _strip_conflicts(payload, {
            "crl-cache-method", "crl-cache-timeout",
            "automatic-enrollment",
        })

    elif obj_type == "outbound-inspection-certificate":
        cert_b64 = _generate_self_signed_cert_pem()
        payload["base64-certificate"] = cert_b64
        payload["is-default"] = True
        # Cert name must start with letter, no special chars
        import re as _re
        name = payload.get("name", "QACert")
        name = _re.sub(r'[^a-zA-Z0-9]', '', name)
        if not name or not name[0].isalpha():
            name = "QACert" + name
        payload["name"] = name
        # Strip everything except name and cert
        for k in list(payload.keys()):
            if k not in ("name", "base64-certificate", "is-default",
                         "ignore-warnings", "ignore-errors"):
                payload.pop(k, None)

    elif obj_type == "server-certificate":
        cert_b64 = _generate_self_signed_cert_pkcs12()
        payload["base64-certificate"] = cert_b64
        payload["base64-password"] = "cGFzcw=="  # "pass" in base64
        # Cert name must start with letter, no underscores/dashes/spaces
        import re as _re
        name = payload.get("name", "QACert")
        name = _re.sub(r'[^a-zA-Z0-9]', '', name)
        if not name or not name[0].isalpha():
            name = "QACert" + name
        payload["name"] = name
        _strip_conflicts(payload, {
            "private-key", "passphrase", "tags", "color", "comments",
        })

    # ------------------------------------------------------------------
    # Auth Servers
    # ------------------------------------------------------------------
    elif obj_type == "radius-server":
        # server is a host object reference — injected by _inject_helpers
        payload["shared-secret"] = "QaRadiusSecret123!"
        # Strip everything except essentials — version/service are object refs
        for k in list(payload.keys()):
            if k not in ("name", "server", "shared-secret",
                         "ignore-warnings", "ignore-errors"):
                payload.pop(k, None)

    elif obj_type == "tacacs-server":
        # server is a host object reference — injected by _inject_helpers
        payload["server-type"] = "TACACS"
        payload["secret-key"] = "QaTacacsSecret123!"
        for k in list(payload.keys()):
            if k not in ("name", "server", "server-type", "secret-key",
                         "ignore-warnings", "ignore-errors"):
                payload.pop(k, None)

    elif obj_type == "radius-group":
        payload.setdefault("members", [])

    elif obj_type == "tacacs-group":
        payload.setdefault("members", [])

    # ------------------------------------------------------------------
    # Network — Extended
    # ------------------------------------------------------------------
    elif obj_type == "access-point-name":
        payload.setdefault("enforce-end-user-domain", False)
        _strip_conflicts(payload, {
            "end-user-domain", "block-traffic-other-end-user-domains",
            "block-traffic-this-end-user-domain",
        })

    elif obj_type == "dynamic-global-network-object":
        pass  # name-only

    elif obj_type == "network-probe":
        # Needs protocol + icmp-options or http-options + install-on
        payload["protocol"] = "icmp"
        payload["icmp-options"] = {"destination": f"10.100.5.{random.randint(10, 200)}"}
        payload["interval"] = 30
        payload["timeout"] = 10
        # install-on will be set to gateway in _inject_helpers
        for k in list(payload.keys()):
            if k not in ("name", "protocol", "icmp-options", "install-on",
                         "interval", "timeout",
                         "ignore-warnings", "ignore-errors"):
                payload.pop(k, None)

    elif obj_type == "updatable-object":
        pass  # read-heavy, may fail

    # ------------------------------------------------------------------
    # Services — Extended (Resources)
    # ------------------------------------------------------------------
    elif obj_type == "resource-cifs":
        payload.setdefault("allowed-disk-and-print-sharing", True)
        _strip_conflicts(payload, {"exception-track"})

    elif obj_type == "resource-ftp":
        payload["resource-matching-method"] = "get_and_put"
        _strip_conflicts(payload, {
            "cvp", "exception-track", "resources-path",
            "color", "comments", "tags",
        })

    elif obj_type == "resource-smtp":
        _strip_conflicts(payload, {"cvp", "exception-track", "match"})

    elif obj_type == "resource-tcp":
        # resource-type defaults to ufp (needs ufp-settings); use cvp with minimal settings
        payload["resource-type"] = "cvp"
        payload["cvp-settings"] = {"server": "localhost"}
        for k in list(payload.keys()):
            if k not in ("name", "resource-type", "cvp-settings",
                         "ignore-warnings", "ignore-errors"):
                payload.pop(k, None)

    elif obj_type == "resource-uri":
        payload["use-this-resource-to"] = "optimize_url_logging"
        _strip_conflicts(payload, {
            "cvp", "exception-track", "match-wildcards",
            "match-ufp", "action", "soap", "connection-methods",
            "uri-match-specification-type",
        })

    elif obj_type == "resource-mms":
        _strip_conflicts(payload, {"exception-track"})

    elif obj_type == "resource-uri-for-qos":
        _strip_conflicts(payload, {"exception-track"})

    elif obj_type == "scada-application":
        payload["primary-category"] = "SCADA"
        payload["url-list"] = ["scada://qa-test"]
        _strip_conflicts(payload, {
            "application-signature", "additional-categories",
            "description", "scada-properties",
            "category",
        })

    # ------------------------------------------------------------------
    # Logging & Monitoring
    # ------------------------------------------------------------------
    elif obj_type == "smtp-server":
        payload["server"] = f"10.100.4.{random.randint(10, 200)}"
        payload["port"] = 25
        _strip_conflicts(payload, {
            "authentication", "encryption", "username", "password",
            "domains-to-process", "tags",
        })

    elif obj_type == "syslog-server":
        payload["port"] = 514
        _strip_conflicts(payload, {"version", "domains-to-process"})

    elif obj_type == "log-exporter":
        payload["target-server"] = f"10.100.7.{random.randint(10, 200)}"
        payload["target-port"] = 514
        payload["protocol"] = "udp"
        payload["read-from"] = "fw-log-file"
        _strip_conflicts(payload, {
            "ca-certificate", "client-certificate",
            "enabled", "attachments", "data-manipulation",
            "domains-to-process",
        })

    elif obj_type == "smart-task":
        payload["enabled"] = False
        payload["action"] = {
            "send-web-request": {
                "url": "https://qa-webhook.example.com",
                "fingerprint": "",
                "override-proxy": False,
                "shared-secret": "",
            }
        }
        payload["trigger"] = "After Publish"
        for k in list(payload.keys()):
            if k not in ("name", "trigger", "enabled", "action",
                         "ignore-warnings", "ignore-errors"):
                payload.pop(k, None)

    # ------------------------------------------------------------------
    # Management & System
    # ------------------------------------------------------------------
    elif obj_type == "generic-object":
        payload["create"] = "com.checkpoint.objects.classes.dummy.CpmiAnyObject"
        # Strip everything except create and name
        for k in list(payload.keys()):
            if k not in ("name", "create", "ignore-warnings", "ignore-errors"):
                payload.pop(k, None)

    elif obj_type == "opsec-application":
        # host will be injected by _inject_helpers
        payload["cpmi"] = {
            "enabled": True,
            "use-administrator-credentials": False,
            "administrator-profile": "Super User",
        }
        payload["one-time-password"] = "OpsecPass1!"
        _strip_conflicts(payload, {"lea", "administrator-profile"})

    elif obj_type == "mobile-profile":
        _strip_conflicts(payload, {
            "applications", "client-customization", "data-leak-prevention",
            "harmony-mobile", "security", "domains-to-process",
        })

    elif obj_type == "limit":
        payload.setdefault("enable-download", True)
        payload.setdefault("download-rate", 1024)

    elif obj_type == "override-categorization":
        payload["url"] = "https://qa-override-example.com"
        payload["new-primary-category"] = "Anonymizer"
        _strip_conflicts(payload, {
            "url-defined-as-regular-expression", "risk",
            "additional-categories", "name",
        })

    elif obj_type == "exception-group":
        payload["apply-on"] = "manually-select-threat-rules"
        _strip_conflicts(payload, {
            "applied-profile", "applied-threat-rules",
        })

    elif obj_type == "gaia-best-practice":
        import base64
        payload["practice-script-base64"] = base64.b64encode(b"#!/bin/bash\necho OK").decode()
        payload["expected-output-base64"] = base64.b64encode(b"OK").decode()
        payload.setdefault("description", "QA test best practice")
        _strip_conflicts(payload, {
            "practice-script-path", "expected-output-text",
        })

    elif obj_type == "securemote-dns-server":
        payload["domains"] = [{"domain-suffix": ".example.com"}]
        _strip_conflicts(payload, {"domains-to-process"})

    # ------------------------------------------------------------------
    # Gateways — Extended
    # ------------------------------------------------------------------
    elif obj_type == "interface":
        # gateway-uid will be injected by _inject_helpers
        payload["name"] = payload.get("name", "eth0")
        payload["ipv4-address"] = f"10.200.0.{random.randint(10, 200)}"
        payload["ipv4-mask-length"] = 24
        _strip_conflicts(payload, {
            "anti-spoofing", "anti-spoofing-settings", "topology",
            "topology-settings", "security-zone-settings",
            "domains-to-process", "tags", "color", "comments",
            "cluster-members", "cluster-network-type", "dynamic-ip",
            "ipv4-network-mask", "ipv6-address", "ipv6-mask-length",
            "ipv6-network-mask", "ip-address", "mask-length",
            "monitored-by-cluster", "network-interface-type",
            "security-zone-settings",
        })

    elif obj_type == "multiple-key-exchanges":
        _strip_conflicts(payload, {
            "additional-key-exchange-1", "additional-key-exchange-2",
            "additional-key-exchange-3",
        })

    # ------------------------------------------------------------------
    # Policy & Rules
    # ------------------------------------------------------------------
    elif obj_type == "package":
        payload.setdefault("access", True)
        payload.setdefault("threat-prevention", False)
        _strip_conflicts(payload, {"installation-targets", "vpn-traditional-mode"})

    elif obj_type == "access-layer":
        # Strip everything except name — most fields cause validation errors
        for k in list(payload.keys()):
            if k not in ("name", "ignore-warnings", "ignore-errors"):
                payload.pop(k, None)

    elif obj_type == "access-rule":
        payload["position"] = "top"
        payload["action"] = "Accept"
        # Strip everything except essentials — many fields cause InvocationTargetException
        for k in list(payload.keys()):
            if k not in ("name", "position", "action", "layer",
                         "comments", "ignore-warnings", "ignore-errors"):
                payload.pop(k, None)

    elif obj_type == "access-section":
        payload["position"] = "top"
        _strip_conflicts(payload, {"tags"})

    elif obj_type == "nat-rule":
        payload["position"] = "top"
        payload["original-source"] = "Any"
        payload["original-destination"] = "Any"
        payload["original-service"] = "Any"
        payload["translated-source"] = "Original"
        payload["translated-destination"] = "Original"
        payload["translated-service"] = "Original"
        payload["method"] = "static"
        _strip_conflicts(payload, {
            "install-on", "enabled", "tags",
        })

    elif obj_type == "nat-section":
        payload["position"] = "top"
        _strip_conflicts(payload, {"tags"})

    elif obj_type == "threat-layer":
        _strip_conflicts(payload, {"add-default-rule"})

    elif obj_type == "threat-rule":
        payload["position"] = "top"
        # action is a profile reference — use built-in "Basic" profile
        payload["action"] = "Basic"
        payload.pop("track", None)
        _strip_conflicts(payload, {
            "destination", "destination-negate", "source", "source-negate",
            "service", "service-negate", "install-on",
            "protected-scope", "protected-scope-negate",
            "track-settings", "enabled", "tags",
        })

    elif obj_type == "threat-exception":
        payload["position"] = "top"
        # Only rule-uid OR exception-group, not both
        payload.pop("exception-group-uid", None)
        payload.pop("exception-group-name", None)
        payload.pop("rule-name", None)
        payload.pop("rule-number", None)
        # rule-uid is injected by _inject_helpers
        _strip_conflicts(payload, {
            "destination", "destination-negate", "source", "source-negate",
            "service", "service-negate", "install-on",
            "protected-scope", "protected-scope-negate",
            "protection-or-site", "track", "enabled", "tags", "action",
        })

    elif obj_type == "https-layer":
        pass  # name-only in most cases

    elif obj_type == "https-rule":
        payload["position"] = "top"
        payload["action"] = "bypass"
        _strip_conflicts(payload, {
            "certificate", "destination", "destination-negate",
            "source", "source-negate", "service", "service-negate",
            "install-on", "site-category", "site-category-negate",
            "enabled", "tags", "track",
        })

    elif obj_type == "https-section":
        payload["position"] = "top"
        _strip_conflicts(payload, {"tags"})

    elif obj_type == "mobile-access-rule":
        payload["position"] = "top"
        _strip_conflicts(payload, {
            "user-groups", "applications", "install-on",
            "enabled", "tags",
        })

    elif obj_type == "mobile-access-section":
        payload["position"] = "top"
        _strip_conflicts(payload, {"tags"})

    elif obj_type == "mobile-access-profile-rule":
        payload["position"] = "top"
        _strip_conflicts(payload, {
            "mobile-profile", "user-groups", "enabled", "tags",
        })

    elif obj_type == "mobile-access-profile-section":
        payload["position"] = "top"
        _strip_conflicts(payload, {"tags"})

    # ------------------------------------------------------------------
    # Data Center (infrastructure-dependent)
    # ------------------------------------------------------------------
    elif obj_type == "data-center-server":
        payload.setdefault("type", "generic")
        payload.setdefault("url", "https://qa-datacenter.example.com")
        _strip_conflicts(payload, {"authentication"})

    elif obj_type in ("data-center-object", "data-center-query"):
        pass  # needs real data center server

    # ------------------------------------------------------------------
    # MDS (infrastructure-dependent)
    # ------------------------------------------------------------------
    elif obj_type == "domain":
        payload.setdefault("servers", {})

    elif obj_type in ("domain-permissions-profile", "md-permissions-profile"):
        pass  # name-only

    elif obj_type == "mds":
        payload.setdefault("ipv4-address", f"10.100.9.{random.randint(10, 200)}")

    elif obj_type == "global-assignment":
        pass  # needs real domain refs

    # ------------------------------------------------------------------
    # External Auth (infrastructure-dependent)
    # ------------------------------------------------------------------
    elif obj_type == "azure-ad":
        payload.setdefault("azure-ad-name", "qa-azure-ad")
        payload.setdefault("application-id", "00000000-0000-0000-0000-000000000000")
        payload.setdefault("application-key", "QaKey123!")
        payload.setdefault("directory-id", "00000000-0000-0000-0000-000000000000")

    elif obj_type == "identity-provider":
        payload.setdefault("type", "saml")
        _strip_conflicts(payload, {"saml-settings"})

    elif obj_type == "idp-administrator-group":
        pass  # needs IdP

    elif obj_type == "ldap-group":
        pass  # needs LDAP

    elif obj_type == "securid-server":
        payload.setdefault("server", f"10.100.8.{random.randint(10, 200)}")

    # ------------------------------------------------------------------
    # LSM (infrastructure-dependent)
    # ------------------------------------------------------------------
    elif obj_type in ("lsm-cluster", "lsm-gateway"):
        payload.setdefault("security-profile", "")
        payload.setdefault("provisioning-state", "manual")
        _strip_conflicts(payload, {"dynamic-objects"})

    # ------------------------------------------------------------------
    # Other (infrastructure-dependent)
    # ------------------------------------------------------------------
    elif obj_type == "if-map-server":
        # host will be injected by _inject_helpers
        payload.setdefault("monitored-ips", [])
        _strip_conflicts(payload, {
            "server", "path",
            "query-whole-ranges", "authentication",
            "domains-to-process",
        })

    elif obj_type == "api-key":
        pass  # special handling

    elif obj_type == "repository-script":
        import base64 as _b64
        payload["script-body"] = "#!/bin/bash\necho QA test"
        payload.pop("script-body-base64", None)

    elif obj_type in ("central-license", "repository-package"):
        pass  # need infrastructure

    elif obj_type == "passcode-profile":
        _strip_conflicts(payload, {
            "allow-simple-passcode", "min-passcode-length",
            "require-alphanumeric-passcode", "min-passcode-complex-characters",
            "max-passcode-age", "passcode-history", "enable-inactivity-timeout",
            "max-inactivity-timeout", "enable-passcode-failed-attempts",
            "max-passcode-failed-attempts", "enable-auto-lock",
        })


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
    """Inject comprehensive defaults for VPN community objects."""
    safe_fields = {
        "name", "color", "comments", "ignore-warnings", "ignore-errors",
        "tags", "set-if-exists",
        "center-gateways", "satellite-gateways", "gateways",
        "encryption-method", "encryption-suite",
        "ike-phase-1", "ike-phase-2",
        "tunnel-granularity", "routing-mode", "link-selection-mode",
        "disable-nat", "use-shared-secret",
        "encrypted-traffic", "wire-mode",
    }
    if obj_type == "vpn-community-star":
        safe_fields |= {"mesh-center-gateways", "vpn-routing", "disable-nat-on"}

    payload["encryption-suite"] = "custom"
    payload["encryption-method"] = "prefer ikev2 but support ikev1"
    payload["ike-phase-1"] = {
        "encryption-algorithm": "aes-256",
        "data-integrity": "sha256",
        "diffie-hellman-group": "group-19",
        "ike-p1-rekey-time": 1440,
    }
    payload["ike-phase-2"] = {
        "encryption-algorithm": "aes-256",
        "data-integrity": "sha256",
        "ike-p2-use-pfs": True,
        "ike-p2-pfs-dh-grp": "group-19",
        "ike-p2-rekey-time": 3600,
    }
    payload["tunnel-granularity"] = "per_subnet"
    payload["routing-mode"] = "domain_based"
    payload["link-selection-mode"] = "legacy"
    payload["disable-nat"] = False
    payload["use-shared-secret"] = False

    if obj_type == "vpn-community-star":
        payload["vpn-routing"] = "to center and to other satellites"
        payload["mesh-center-gateways"] = False
        payload["disable-nat-on"] = "both center and satellite gateways"

    if obj_type == "vpn-community-star":
        payload.setdefault("center-gateways", [])
        payload.setdefault("satellite-gateways", [])
    elif obj_type == "vpn-community-meshed":
        payload.setdefault("gateways", [])

    payload["ignore-warnings"] = True
    payload.setdefault("encrypted-traffic", "any")
    payload.setdefault("wire-mode", "off")

    for key in list(payload.keys()):
        if key not in safe_fields:
            payload.pop(key, None)
