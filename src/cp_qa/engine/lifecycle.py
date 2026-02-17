"""CRUD lifecycle test execution.

Runs the full ``add -> set -> show -> delete`` lifecycle for each
variant of a given object type.  The ADD step uses an adaptive
self-healing loop that analyses API errors and auto-corrects the
payload up to :const:`~cp_qa.constants.MAX_RETRIES` times.

Only the **final** result (success or last failure) is recorded for
each variant, keeping reports clean.
"""

from __future__ import annotations

import random
import time
from typing import Any

from cp_qa.constants import MAX_RETRIES
from cp_qa.engine.autofix import auto_fix_payload
from cp_qa.engine.params import extract_params_from_obj
from cp_qa.engine.payloads import generate_payloads
from cp_qa.engine.spec import get_object_by_name, get_simplified_schema
from cp_qa.engine.type_defaults import apply_type_defaults
from cp_qa.logging import get_logger

log = get_logger(__name__)

# Types that require a ``publish`` between ADD→SET and SET→DELETE
_PUBLISH_BETWEEN_STEPS = {
    "vpn-community-meshed", "vpn-community-star",
    "wildcard", "gsn-handover-group",
    "simple-gateway", "simple-cluster",
    "threat-indicator",
    # Policy objects
    "package", "access-layer", "access-rule", "access-section",
    "nat-rule", "nat-section",
    "threat-layer", "threat-rule", "threat-exception",
    "https-layer", "https-rule", "https-section",
    "mobile-access-rule", "mobile-access-section",
    "mobile-access-profile-rule", "mobile-access-profile-section",
    "exception-group",
}

# Types that need a policy package helper
_NEEDS_PACKAGE_HELPER = {
    "access-rule", "access-section",
    "nat-rule", "nat-section",
    "threat-rule", "threat-exception",
    "https-rule", "https-section",
    "mobile-access-rule", "mobile-access-section",
    "mobile-access-profile-rule", "mobile-access-profile-section",
}

# Types that need a service-tcp helper
_NEEDS_SERVICE_TCP_HELPER = {
    "resource-cifs", "resource-ftp", "resource-smtp",
    "resource-uri", "resource-mms",
    "resource-uri-for-qos",
}

# Types that need layer/package ref in SET/SHOW/DELETE operations
_NEEDS_LAYER_IN_OPS = {
    "access-rule", "access-section",
}

# Types that have no SET command or non-standard SET semantics
_SKIP_SET = {
    "custom-trusted-ca-certificate", "external-trusted-ca",
    "opsec-trusted-ca", "outbound-inspection-certificate",
    "server-certificate",
    "generic-object",  # meta-API, non-standard SET schema
}

# Types with completely non-standard lifecycles (custom handlers)
_CUSTOM_LIFECYCLE = {
    "threat-protections",
    "web-console-statistics",
    "objects-batch",
    "rules-batch",
}

_MAX_STEP_RETRIES = 3  # Retries for SET / DELETE on transient errors


def _is_success(res: dict) -> bool:
    """Check whether an API response indicates success."""
    return (
        "uid" in res
        or res.get("code") == "success"
        or res.get("message") == "OK"
    )


def _is_transient(res: dict) -> bool:
    """Check whether an API error looks transient (worth retrying)."""
    msg = str(res.get("message", "")).lower()
    code = str(res.get("code", "")).lower()
    return any(x in msg or x in code for x in [
        "null pointer exception", "generic_server_error",
        "generic_error", "management server failed",
        "internal error", "runtime exception",
    ])


def _retry_command(
    client: Any,
    command: str,
    payload: dict,
    label: str = "",
    max_retries: int = _MAX_STEP_RETRIES,
) -> tuple[bool, dict, float]:
    """Execute a command with retries on transient errors.

    Handles both synchronous (uid in response) and asynchronous
    (task-id in response) commands automatically.

    Returns:
        ``(success, response_dict, total_duration)``
    """
    total_dur = 0.0
    res: dict = {}
    for attempt in range(1, max_retries + 1):
        if attempt > 1:
            log.info("  %s retry %d/%d after transient error...", label, attempt, max_retries)
            time.sleep(3)  # Brief pause before retry
        t_start = time.perf_counter()
        res = client.run_command(command, payload)
        dur = time.perf_counter() - t_start
        total_dur += dur
        success = _is_success(res)
        # Handle async tasks (e.g. simple-cluster SET returns task-id)
        if not success and "task-id" in res:
            poll_start = time.perf_counter()
            success, res = _poll_async_task(client, res["task-id"])
            total_dur += time.perf_counter() - poll_start
        if success:
            log.info("  %s: [%.2fs] PASS", label, total_dur)
            return True, res, total_dur
        # Handle "Unrecognized parameter" errors by stripping the field
        err_msg = str(res.get("message", ""))
        if "Unrecognized parameter" in err_msg:
            import re as _re
            m = _re.search(r"Unrecognized parameter \[(\S+)\]", err_msg)
            if m and m.group(1) in payload:
                payload.pop(m.group(1))
                log.info("  FIX: Stripped unrecognized '%s' from %s payload", m.group(1), label)
                continue
        if not _is_transient(res):
            break  # Non-transient error — no point retrying
    log.info("  %s: [%.2fs] %s", label, total_dur, "FAIL")
    return False, res, total_dur


def run_lifecycle_test(
    client: Any,
    spec: dict,
    results: list[dict],
    obj_type: str,
    add_cmd_spec: dict,
) -> bool:
    """Execute the adaptive CRUD lifecycle for every variant of *obj_type*.

    For each variant:
        1. Attempt ADD with the full payload.
        2. If it fails, analyse the error and auto-fix the payload.
        3. Retry up to :const:`MAX_RETRIES` times.
        4. On success, proceed with SET -> SHOW -> DELETE.
        5. Record only the final result for each step.

    Args:
        client:       Authenticated :class:`~cp_qa.client.APIClient` instance.
        spec:         Parsed API specification dictionary.
        results:      Shared results list — lifecycle results are appended here.
        obj_type:     Object type to test (e.g. ``"host"``, ``"network"``).
        add_cmd_spec: Command spec dict for the ``add-<type>`` command.

    Returns:
        ``True`` if the lifecycle completed (even if some variants failed).
    """
    # Dispatch non-standard types to their custom lifecycle handlers
    if obj_type in _CUSTOM_LIFECYCLE:
        handler = _CUSTOM_HANDLERS.get(obj_type)
        if handler:
            return handler(client, results, obj_type)
        log.warning("No custom handler for type '%s'", obj_type)
        return False

    current_obj_type = obj_type
    log.info("--- Starting exhaustive QA for object type: %s ---", obj_type)

    # Pre-create helper objects if needed
    helpers = _create_helpers(client, obj_type)

    request_obj_name = add_cmd_spec.get("request")
    obj_def = get_object_by_name(spec, request_obj_name)
    if not obj_def:
        log.warning(
            "Could not find request object definition for %s: %s",
            obj_type,
            request_obj_name,
        )
        return False

    parameters = extract_params_from_obj(obj_def)
    payload_variants = generate_payloads(
        parameters, current_obj_type=current_obj_type, spec=spec
    )

    # Capture simplified schemas for reporting
    req_schema = get_simplified_schema(spec, request_obj_name)
    res_schema = None
    response_obj_spec = add_cmd_spec.get("response", {}).get("on-success", {}).get("web", {}).get("object", {})
    response_obj_name = response_obj_spec.get("object-name")
    if response_obj_name:
        res_schema = get_simplified_schema(spec, response_obj_name)

    log.info(
        "Generated %d 'Full' test variants for %s.",
        len(payload_variants),
        obj_type,
    )

    for i, base_payload in enumerate(payload_variants):
        # Generate proper test ID based on object type
        test_id = _make_test_id(obj_type, i)
        base_payload["name"] = test_id

        log.info(
            "Testing Variant %d/%d: %s",
            i + 1,
            len(payload_variants),
            test_id,
        )

        # Apply type-specific defaults BEFORE first attempt
        apply_type_defaults(obj_type, base_payload, spec=spec, current_obj_type=current_obj_type)

        # Inject helper object references
        _inject_helpers(base_payload, obj_type, helpers)

        # === ADAPTIVE ADD WITH SELF-HEALING ===
        success, add_res, add_duration = _adaptive_add(
            client, obj_type, base_payload, parameters
        )

        if success:
            log.info("  ADD: [%.2fs] PASS", add_duration)
        else:
            log.error("  ADD: [%.2fs] FAIL", add_duration)

        results.append(
            {
                "type": obj_type,
                "variant": i,
                "command": f"add-{obj_type}",
                "payload": dict(base_payload),
                "response": add_res,
                "success": success,
                "duration": add_duration,
                "request_schema": req_schema,
                "response_schema": res_schema,
            }
        )

        if not success:
            log.error(
                "Add-%s EXHAUSTED retries for variant %d: %s",
                obj_type,
                i,
                add_res.get("message", add_res),
            )
            continue

        # Extract UID from ADD response for more reliable SET/SHOW/DELETE.
        # For async tasks the show-task response contains a top-level uid
        # that belongs to the *task*, not the created object.  Only trust
        # a uid that comes directly from a non-task ADD response.
        obj_uid = ""
        if "tasks" not in add_res:
            obj_uid = add_res.get("uid", "")
        else:
            # Async task — try to dig out the created object's UID
            tasks = add_res.get("tasks", [])
            if tasks and isinstance(tasks[0], dict):
                details = tasks[0].get("task-details", [])
                if details and isinstance(details[0], dict):
                    resp_msg = details[0].get("responseMessage", "")
                    if isinstance(resp_msg, str) and len(resp_msg) == 36:
                        obj_uid = resp_msg  # Sometimes the UID is here
        obj_ref = {"uid": obj_uid} if obj_uid else {"name": test_id}

        # Some types require a publish before SET/DELETE works
        if obj_type in _PUBLISH_BETWEEN_STEPS:
            log.info("  Publishing before SET (required for %s)...", obj_type)
            client.publish()
            time.sleep(2)  # Let server commit

        # Section/rule types need layer or package in SET/SHOW/DELETE
        layer_ref = {}
        if obj_type in _NEEDS_LAYER_IN_OPS and helpers.get("access-layer"):
            layer_ref["layer"] = helpers["access-layer"]
        elif obj_type in ("nat-rule", "nat-section") and helpers.get("package"):
            layer_ref["package"] = helpers["package"]
        elif obj_type in ("threat-rule", "threat-exception") and helpers.get("threat-layer"):
            layer_ref["layer"] = helpers["threat-layer"]
            if obj_type == "threat-exception" and helpers.get("threat-rule-uid"):
                layer_ref["rule-uid"] = helpers["threat-rule-uid"]
        elif obj_type in ("https-rule", "https-section") and helpers.get("https-layer"):
            layer_ref["layer"] = helpers["https-layer"]

        # === SET (with retry) ===
        if obj_type in _SKIP_SET:
            log.info("  SET: skipped (immutable type)")
            set_success, set_res, set_dur = True, {"message": "skipped"}, 0.0
        else:
            set_payload = {
                **obj_ref,
                **layer_ref,
                "comments": f"QA updated exhaustive variant {i}",
                "color": "orange",
                "ignore-warnings": True,
                "ignore-errors": True,
            }
            set_success, set_res, set_dur = _retry_command(
                client, f"set-{obj_type}", set_payload, label="SET"
            )

        results.append(
            {
                "type": obj_type,
                "variant": i,
                "command": f"set-{obj_type}",
                "payload": set_payload if obj_type not in _SKIP_SET else {},
                "response": set_res,
                "success": set_success,
                "duration": set_dur,
            }
        )

        # === SHOW ===
        log.info("  Executing SHOW verification...")
        t_start = time.perf_counter()
        show_res = client.run_command(
            f"show-{obj_type}", {**obj_ref, **layer_ref, "details-level": "full"}
        )
        show_dur = time.perf_counter() - t_start
        show_success = _is_success(show_res)
        log.info("  SHOW: [%.2fs] %s", show_dur, "PASS" if show_success else "FAIL")

        results.append(
            {
                "type": obj_type,
                "variant": i,
                "command": f"show-{obj_type}",
                "payload": obj_ref,
                "response": show_res,
                "success": show_success,
                "duration": show_dur,
            }
        )

        if obj_type in _PUBLISH_BETWEEN_STEPS:
            log.info("  Publishing before DELETE (required for %s)...", obj_type)
            client.publish()
            time.sleep(2)  # Let server commit

        # === DELETE (with retry) ===
        del_payload = {**obj_ref, **layer_ref, "ignore-warnings": True, "ignore-errors": True}
        del_success, del_res, del_dur = _retry_command(
            client, f"delete-{obj_type}", del_payload, label="DELETE"
        )

        results.append(
            {
                "type": obj_type,
                "variant": i,
                "command": f"delete-{obj_type}",
                "payload": del_payload,
                "response": del_res,
                "success": del_success,
                "duration": del_dur,
            }
        )

        total_dur = add_duration + set_dur + show_dur + del_dur
        log.info(
            "Finished lifecycle for %s (Completed in %.2fs)", test_id, total_dur
        )

    # Clean up helper objects
    _cleanup_helpers(client, helpers)

    return True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_test_id(obj_type: str, variant_index: int) -> str:
    """Generate a unique test object name."""
    rand = random.randint(100, 999)
    if obj_type == "dns-domain":
        return f".qa-domain-{variant_index}-{rand}.example.com"
    if obj_type in ("time", "time-group"):
        return f"QA_T{variant_index}_{rand}"
    return f"QA_{obj_type.upper()}_{variant_index}_{rand}"


def _create_helpers(
    client: Any, obj_type: str
) -> dict:
    """Pre-create helper objects needed by certain types.

    Returns:
        Dict of helper names keyed by role (e.g. ``"group"``, ``"gateway"``).
    """
    helpers: dict[str, str | None] = {}

    if obj_type == "group-with-exclusion":
        helpers["group"] = f"QA_HELPER_INCLUDE_{random.randint(1000, 9999)}"
        helpers["except_group"] = f"QA_HELPER_EXCEPT_{random.randint(1000, 9999)}"
        res1 = client.run_command("add-group", {"name": helpers["group"]})
        res2 = client.run_command("add-group", {"name": helpers["except_group"]})
        if "uid" in res1 and "uid" in res2:
            log.info(
                "  Created helper groups: include='%s', except='%s'",
                helpers["group"],
                helpers["except_group"],
            )
        else:
            log.warning("  Failed to create helper groups")
            helpers.clear()

    elif obj_type == "time-group":
        helpers["time"] = f"QA_HT{random.randint(100, 999)}"
        res = client.run_command(
            "add-time",
            {"name": helpers["time"], "start-now": "true", "end-never": "true"},
        )
        if "uid" in res:
            log.info("  Created helper time object: '%s'", helpers["time"])
        else:
            log.warning(
                "  Failed to create helper time object: %s",
                res.get("message", res),
            )
            helpers.clear()

    elif obj_type in ("vpn-community-meshed", "vpn-community-star"):
        rand = random.randint(100, 999)
        gw_name = f"QA_HELPER_GW_{rand}"
        interop_name = f"QA_HELPER_INTEROP_{rand}"

        # Create a simple-gateway with VPN enabled
        gw_res = client.run_command("add-simple-gateway", {
            "name": gw_name,
            "ipv4-address": f"10.100.99.{random.randint(10, 200)}",
            "version": "R81.10",
            "vpn": True,
            "ignore-warnings": True,
            "color": "sky blue",
            "comments": "QA helper gateway for VPN community test",
        })
        if "uid" in gw_res:
            helpers["gateway"] = gw_name
            log.info("  Created helper gateway: '%s'", gw_name)
        else:
            log.warning(
                "  Failed to create helper gateway: %s",
                gw_res.get("message", gw_res),
            )

        # Create an interoperable device
        interop_res = client.run_command("add-interoperable-device", {
            "name": interop_name,
            "ipv4-address": f"10.100.97.{random.randint(10, 200)}",
            "ignore-warnings": True,
            "color": "sky blue",
            "comments": "QA helper interop device for VPN community test",
        })
        if "uid" in interop_res:
            helpers["interop"] = interop_name
            log.info("  Created helper interop device: '%s'", interop_name)
        else:
            log.warning(
                "  Failed to create helper interop device: %s",
                interop_res.get("message", interop_res),
            )

        # Publish helpers so they are available for VPN community references
        if helpers.get("gateway") or helpers.get("interop"):
            client.publish()
            log.info("  Published VPN helper objects")

    elif obj_type == "resource-tcp":
        # resource-tcp needs an OPSEC application for cvp-settings.server
        helpers["host"] = f"QA_HELPER_HOST_{random.randint(1000, 9999)}"
        res = client.run_command("add-host", {
            "name": helpers["host"],
            "ipv4-address": f"10.100.6.{random.randint(10, 200)}",
        })
        if "uid" in res:
            client.publish()
            log.info("  Created helper host: '%s'", helpers["host"])
            # Now create opsec-application on top of the host
            helpers["opsec-app"] = f"QA_HELPER_OPSEC_{random.randint(1000, 9999)}"
            opsec_res = client.run_command("add-opsec-application", {
                "name": helpers["opsec-app"],
                "host": helpers["host"],
                "cpmi": {
                    "enabled": True,
                    "use-administrator-credentials": False,
                    "administrator-profile": "Super User",
                },
                "one-time-password": "OpsecPass1!",
                "ignore-warnings": True,
            })
            if "uid" in opsec_res:
                helpers["opsec-app-uid"] = opsec_res["uid"]
                client.publish()
                log.info("  Created helper opsec-app: '%s' (uid=%s)",
                         helpers["opsec-app"], opsec_res["uid"])
            else:
                log.warning("  Failed to create helper opsec-app: %s",
                            opsec_res.get("message", opsec_res))
                helpers.pop("opsec-app", None)
        else:
            log.warning("  Failed to create helper host: %s", res.get("message", res))
            helpers.clear()

    elif obj_type in ("opsec-application", "syslog-server", "if-map-server",
                       "radius-server", "tacacs-server", "securemote-dns-server"):
        helpers["host"] = f"QA_HELPER_HOST_{random.randint(1000, 9999)}"
        res = client.run_command("add-host", {
            "name": helpers["host"],
            "ipv4-address": f"10.100.6.{random.randint(10, 200)}",
        })
        if "uid" in res:
            client.publish()
            log.info("  Created helper host: '%s'", helpers["host"])
        else:
            log.warning("  Failed to create helper host: %s", res.get("message", res))
            helpers.clear()

    elif obj_type in _NEEDS_SERVICE_TCP_HELPER:
        helpers["service-tcp"] = f"QA_HELPER_SVC_{random.randint(1000, 9999)}"
        res = client.run_command("add-service-tcp", {
            "name": helpers["service-tcp"],
            "port": "9999",
            "ignore-warnings": True,
        })
        if "uid" in res:
            client.publish()
            log.info("  Created helper service-tcp: '%s'", helpers["service-tcp"])
        else:
            log.warning("  Failed to create helper service-tcp: %s", res.get("message", res))
            helpers.clear()

    elif obj_type in ("data-type-compound-group", "data-type-traditional-group"):
        helpers["data-type"] = f"QA_HELPER_DT_{random.randint(1000, 9999)}"
        res = client.run_command("add-data-type-keywords", {
            "name": helpers["data-type"],
            "keywords": ["qa-helper-keyword"],
            "ignore-warnings": True,
        })
        if "uid" in res:
            client.publish()
            log.info("  Created helper data-type: '%s'", helpers["data-type"])
        else:
            log.warning("  Failed to create helper data-type: %s", res.get("message", res))
            helpers.clear()

    elif obj_type in ("network-probe", "interface"):
        helpers["gateway"] = f"QA_HELPER_GW_{random.randint(1000, 9999)}"
        gw_res = client.run_command("add-simple-gateway", {
            "name": helpers["gateway"],
            "ipv4-address": f"10.100.99.{random.randint(10, 200)}",
            "version": "R81.10",
            "ignore-warnings": True,
        })
        if "uid" in gw_res:
            helpers["gateway_uid"] = gw_res["uid"]
            client.publish()
            log.info("  Created helper gateway: '%s'", helpers["gateway"])
        else:
            log.warning("  Failed to create helper gateway: %s", gw_res.get("message", gw_res))
            helpers.clear()

    elif obj_type == "multiple-key-exchanges":
        rand = random.randint(100, 999)
        gw_name = f"QA_HELPER_GW_{rand}"
        gw_res = client.run_command("add-simple-gateway", {
            "name": gw_name,
            "ipv4-address": f"10.100.99.{random.randint(10, 200)}",
            "version": "R81.10",
            "vpn": True,
            "ignore-warnings": True,
        })
        if "uid" in gw_res:
            helpers["gateway"] = gw_name
            client.publish()
            vpn_name = f"QA_HELPER_VPN_{rand}"
            vpn_res = client.run_command("add-vpn-community-meshed", {
                "name": vpn_name,
                "gateways": [gw_name],
                "encryption-suite": "custom",
                "encryption-method": "prefer ikev2 but support ikev1",
                "ike-phase-1": {
                    "encryption-algorithm": "aes-256",
                    "data-integrity": "sha256",
                    "diffie-hellman-group": "group-19",
                },
                "ike-phase-2": {
                    "encryption-algorithm": "aes-256",
                    "data-integrity": "sha256",
                    "ike-p2-use-pfs": True,
                    "ike-p2-pfs-dh-grp": "group-19",
                },
                "ignore-warnings": True,
            })
            if "uid" in vpn_res:
                helpers["vpn-community"] = vpn_name
                client.publish()
                log.info("  Created helper VPN community: '%s'", vpn_name)
            else:
                log.warning("  Failed to create helper VPN community: %s", vpn_res.get("message", vpn_res))
        else:
            log.warning("  Failed to create helper gateway for MKE: %s", gw_res.get("message", gw_res))
            helpers.clear()

    elif obj_type in _NEEDS_PACKAGE_HELPER:
        # Try using the built-in "Standard" package first — avoids rulebase creation issues
        show_pkg = client.run_command("show-package", {"name": "Standard", "details-level": "full"})
        if "uid" in show_pkg:
            helpers["package"] = "Standard"
            access_layers = show_pkg.get("access-layers", [])
            if access_layers and isinstance(access_layers, list):
                if isinstance(access_layers[0], dict):
                    helpers["access-layer"] = access_layers[0].get("name", "Network")
                else:
                    helpers["access-layer"] = str(access_layers[0]) if access_layers[0] else "Network"
            else:
                helpers["access-layer"] = "Network"

            threat_layers = show_pkg.get("threat-layers", [])
            if threat_layers and isinstance(threat_layers, list):
                if isinstance(threat_layers[0], dict):
                    helpers["threat-layer"] = threat_layers[0].get("name", "Standard Threat Prevention")
                elif isinstance(threat_layers[0], str):
                    helpers["threat-layer"] = threat_layers[0]

            log.info("  Using built-in package 'Standard' with access-layer '%s'",
                      helpers.get("access-layer", "?"))
        else:
            # Fallback: create a new package
            pkg_name = f"QA_HELPER_PKG_{random.randint(1000, 9999)}"
            pkg_res = client.run_command("add-package", {
                "name": pkg_name,
                "access": True,
                "threat-prevention": True,
                "ignore-warnings": True,
            })
            if "uid" in pkg_res:
                helpers["package"] = pkg_name
                access_layers = pkg_res.get("access-layers", [])
                if access_layers and isinstance(access_layers, list):
                    if isinstance(access_layers[0], dict):
                        helpers["access-layer"] = access_layers[0].get("name", f"{pkg_name} Network")
                    elif isinstance(access_layers[0], str):
                        helpers["access-layer"] = access_layers[0]
                    else:
                        helpers["access-layer"] = f"{pkg_name} Network"
                else:
                    helpers["access-layer"] = f"{pkg_name} Network"

                threat_layers = pkg_res.get("threat-layers", [])
                if threat_layers and isinstance(threat_layers, list):
                    if isinstance(threat_layers[0], dict):
                        helpers["threat-layer"] = threat_layers[0].get("name", f"{pkg_name} Threat Prevention")
                    elif isinstance(threat_layers[0], str):
                        helpers["threat-layer"] = threat_layers[0]

                client.publish()
                time.sleep(5)
                log.info("  Created helper package '%s' with access-layer '%s'",
                          pkg_name, helpers.get("access-layer", "?"))
            else:
                log.warning("  Failed to create helper package: %s", pkg_res.get("message", pkg_res))

        # Shared: create sub-helpers for threat/HTTPS types regardless of package source
        if helpers.get("package"):
            if obj_type in ("threat-rule", "threat-exception") and not helpers.get("threat-layer"):
                tl_name = f"QA_HELPER_TL_{random.randint(1000, 9999)}"
                tl_res = client.run_command("add-threat-layer", {
                    "name": tl_name,
                    "ignore-warnings": True,
                })
                if "uid" in tl_res:
                    helpers["threat-layer"] = tl_name
                    client.publish()
                    log.info("  Created helper threat-layer: '%s'", tl_name)

            if obj_type == "threat-exception" and helpers.get("threat-layer"):
                tr_name = f"QA_HELPER_TR_{random.randint(1000, 9999)}"
                tr_res = client.run_command("add-threat-rule", {
                    "name": tr_name,
                    "layer": helpers["threat-layer"],
                    "position": "top",
                    "ignore-warnings": True,
                })
                if "uid" in tr_res:
                    helpers["threat-rule"] = tr_name
                    helpers["threat-rule-uid"] = tr_res.get("uid", "")
                    client.publish()
                    log.info("  Created helper threat-rule: '%s'", tr_name)

            if obj_type in ("https-rule", "https-section"):
                hl_name = f"QA_HELPER_HL_{random.randint(1000, 9999)}"
                hl_res = client.run_command("add-https-layer", {
                    "name": hl_name,
                    "ignore-warnings": True,
                })
                if "uid" in hl_res:
                    helpers["https-layer"] = hl_name
                    client.publish()
                    log.info("  Created helper https-layer: '%s'", hl_name)

    return helpers


def _inject_helpers(
    payload: dict,
    obj_type: str,
    helpers: dict,
) -> None:
    """Inject helper object references into the payload."""
    if obj_type == "group-with-exclusion" and helpers.get("group") and helpers.get("except_group"):
        payload["include"] = helpers["group"]
        payload["except"] = helpers["except_group"]
        log.info(
            "  Injected include='%s', except='%s'",
            helpers["group"],
            helpers["except_group"],
        )
    elif obj_type == "time-group" and helpers.get("time"):
        payload["members"] = [helpers["time"]]
        log.info("  Injected time member='%s'", helpers["time"])
    elif obj_type == "vpn-community-meshed" and helpers.get("gateway"):
        gateways = []
        if helpers.get("gateway"):
            gateways.append(helpers["gateway"])
        if helpers.get("interop"):
            gateways.append(helpers["interop"])
        payload["gateways"] = gateways
        log.info("  Injected meshed gateways: %s", gateways)
    elif obj_type == "vpn-community-star" and helpers.get("gateway"):
        payload["center-gateways"] = [helpers["gateway"]]
        satellites = []
        if helpers.get("interop"):
            satellites.append(helpers["interop"])
        payload["satellite-gateways"] = satellites
        log.info(
            "  Injected star center='%s', satellites=%s",
            helpers["gateway"],
            satellites,
        )
    elif obj_type == "opsec-application" and helpers.get("host"):
        payload["host"] = helpers["host"]
        log.info("  Injected host='%s'", helpers["host"])
    elif obj_type in ("syslog-server", "if-map-server", "securemote-dns-server") and helpers.get("host"):
        payload["host"] = helpers["host"]
        log.info("  Injected host='%s'", helpers["host"])
    elif obj_type in ("radius-server", "tacacs-server") and helpers.get("host"):
        payload["server"] = helpers["host"]
        log.info("  Injected server='%s'", helpers["host"])
    elif obj_type == "resource-tcp" and helpers.get("opsec-app"):
        if "cvp-settings" not in payload:
            payload["cvp-settings"] = {}
        # Use UID if available (API requires OPSEC Application reference)
        ref = helpers.get("opsec-app-uid", helpers["opsec-app"])
        payload["cvp-settings"]["server"] = ref
        log.info("  Injected cvp-settings.server='%s'", ref)
    elif obj_type == "data-type-compound-group" and helpers.get("data-type"):
        payload["matched-groups"] = [helpers["data-type"]]
        log.info("  Injected matched-groups=['%s']", helpers["data-type"])
    elif obj_type == "data-type-traditional-group" and helpers.get("data-type"):
        payload["data-types"] = [helpers["data-type"]]
        log.info("  Injected data-types=['%s']", helpers["data-type"])
    elif obj_type in _NEEDS_SERVICE_TCP_HELPER and helpers.get("service-tcp"):
        payload["allowed-service"] = helpers["service-tcp"]
        log.info("  Injected allowed-service='%s'", helpers["service-tcp"])
    elif obj_type == "interface" and helpers.get("gateway_uid"):
        payload["gateway-uid"] = helpers["gateway_uid"]
        log.info("  Injected gateway-uid='%s'", helpers["gateway_uid"])
    elif obj_type == "network-probe" and helpers.get("gateway"):
        payload["install-on"] = [helpers["gateway"]]
        payload.pop("gateway", None)
        log.info("  Injected install-on=['%s']", helpers["gateway"])
    elif obj_type == "multiple-key-exchanges" and helpers.get("vpn-community"):
        payload["vpn-community"] = helpers["vpn-community"]
        log.info("  Injected vpn-community='%s'", helpers["vpn-community"])

    # Policy type injection
    elif obj_type in ("access-rule", "access-section") and helpers.get("access-layer"):
        payload["layer"] = helpers["access-layer"]
        log.info("  Injected layer='%s'", helpers["access-layer"])
    elif obj_type in ("nat-rule", "nat-section") and helpers.get("package"):
        payload["package"] = helpers["package"]
        log.info("  Injected package='%s'", helpers["package"])
    elif obj_type in ("threat-rule",) and helpers.get("threat-layer"):
        payload["layer"] = helpers["threat-layer"]
        log.info("  Injected layer='%s'", helpers["threat-layer"])
    elif obj_type == "threat-exception":
        if helpers.get("threat-rule-uid"):
            payload["rule-uid"] = helpers["threat-rule-uid"]
        if helpers.get("threat-layer"):
            payload["layer"] = helpers["threat-layer"]
        # Ensure no conflicting identifiers
        payload.pop("exception-group-uid", None)
        payload.pop("exception-group-name", None)
        payload.pop("rule-name", None)
        payload.pop("rule-number", None)
        log.info("  Injected threat-exception refs (rule-uid only)")
    elif obj_type in ("https-rule", "https-section") and helpers.get("https-layer"):
        payload["layer"] = helpers["https-layer"]
        log.info("  Injected layer='%s'", helpers["https-layer"])
    # mobile-access-rule/section don't accept 'layer' — they operate at package level


def _cleanup_helpers(client: Any, helpers: dict) -> None:
    """Delete helper objects created during the test."""
    if helpers.get("group"):
        client.run_command("delete-group", {"name": helpers["group"]})
        log.info("  Cleaned up helper group '%s'", helpers["group"])
    if helpers.get("except_group"):
        client.run_command("delete-group", {"name": helpers["except_group"]})
        log.info("  Cleaned up helper group '%s'", helpers["except_group"])
    if helpers.get("time"):
        client.run_command("delete-time", {"name": helpers["time"]})
        log.info("  Cleaned up helper time '%s'", helpers["time"])
    if helpers.get("opsec-app"):
        client.run_command("delete-opsec-application", {
            "name": helpers["opsec-app"], "ignore-warnings": True,
        })
        log.info("  Cleaned up helper opsec-app '%s'", helpers["opsec-app"])
    if helpers.get("host"):
        client.run_command("delete-host", {"name": helpers["host"]})
        log.info("  Cleaned up helper host '%s'", helpers["host"])
    if helpers.get("data-type"):
        client.run_command("delete-data-type-keywords", {"name": helpers["data-type"], "ignore-warnings": True})
        log.info("  Cleaned up helper data-type '%s'", helpers["data-type"])
    if helpers.get("service-tcp"):
        client.run_command("delete-service-tcp", {"name": helpers["service-tcp"], "ignore-warnings": True})
        log.info("  Cleaned up helper service-tcp '%s'", helpers["service-tcp"])
    if helpers.get("vpn-community"):
        client.run_command("delete-vpn-community-meshed", {"name": helpers["vpn-community"], "ignore-warnings": True})
        log.info("  Cleaned up helper VPN community '%s'", helpers["vpn-community"])
    # Package cascade-deletes layers, rules, and sections (don't delete built-in Standard)
    if helpers.get("package") and helpers["package"] != "Standard":
        client.run_command("delete-package", {"name": helpers["package"], "ignore-warnings": True, "ignore-errors": True})
        log.info("  Cleaned up helper package '%s' (cascade)", helpers["package"])
    if helpers.get("gateway"):
        client.run_command(
            "delete-simple-gateway",
            {"name": helpers["gateway"], "ignore-warnings": True},
        )
        log.info("  Cleaned up helper gateway '%s'", helpers["gateway"])
    if helpers.get("interop"):
        client.run_command(
            "delete-interoperable-device",
            {"name": helpers["interop"], "ignore-warnings": True},
        )
        log.info("  Cleaned up helper interop device '%s'", helpers["interop"])
    if helpers:
        client.publish()


def _adaptive_add(
    client: Any,
    obj_type: str,
    payload: dict,
    parameters: list[dict],
) -> tuple[bool, dict, float]:
    """Run the adaptive ADD loop with self-healing retries.

    Returns:
        ``(success, response_dict, duration_seconds)``
    """
    success = False
    attempt = 0
    add_res: dict = {}
    add_start = time.perf_counter()

    while not success and attempt < MAX_RETRIES:
        attempt += 1
        if attempt > 1:
            log.info("  Optimizing payload for accuracy (pass %d)...", attempt)

        add_res = client.run_command(f"add-{obj_type}", payload)
        success = "uid" in add_res or add_res.get("code") == "success"

        # Handle async tasks (e.g. simple-cluster returns task-id)
        if not success and "task-id" in add_res:
            success, add_res = _poll_async_task(client, add_res["task-id"])

        # Accept warnings as success
        if (
            not success
            and "warning" in str(add_res).lower()
            and "uid" in str(add_res)
        ):
            success = True
            break

        if success:
            break

        # === Auto-correction from error feedback ===
        error_msg = str(add_res.get("message", "")).lower()
        blocking_errors = add_res.get(
            "blocking-errors", add_res.get("errors", [])
        )
        all_errors = error_msg
        for be in blocking_errors:
            if isinstance(be, dict):
                all_errors += " " + str(be.get("message", "")).lower()
            else:
                all_errors += " " + str(be).lower()

        if not auto_fix_payload(payload, all_errors, parameters):
            break  # No known fix — stop retrying

    duration = time.perf_counter() - add_start
    return success, add_res, duration


def _poll_async_task(
    client: Any, task_id: str
) -> tuple[bool, dict]:
    """Poll an async task until completion (up to ~120 s).

    Returns:
        ``(success, response_dict)``
    """
    import time as _time

    log.info("  Async task %s — waiting for completion...", task_id)
    for _ in range(60):
        _time.sleep(2)
        task_res = client.run_command(
            "show-task", {"task-id": task_id, "details-level": "full"}
        )
        tasks = task_res.get("tasks", [])
        if tasks:
            status = tasks[0].get("status", "")
            if status == "succeeded":
                return True, task_res
            if status in ("failed", "partially succeeded"):
                detail = tasks[0].get("task-details", [{}])[0]
                desc = (
                    detail.get("statusDescription", "")
                    or detail.get("request-status-description", "")
                    or status
                )
                return False, {"message": desc}

    return False, {"message": "Async task timed out"}


# ===========================================================================
# Custom lifecycle handlers for non-standard types
# ===========================================================================

def _lifecycle_threat_protections(
    client: Any, results: list[dict], obj_type: str,
) -> bool:
    """Custom lifecycle for ``threat-protections``.

    Threat protections are built-in objects — they cannot be created or
    deleted.  The lifecycle is: SHOW (list) → pick one → SET (modify) →
    SHOW (verify) → SET (revert).
    """
    log.info("--- Custom lifecycle: threat-protections ---")

    # Step 1: SHOW (list existing protections)
    t0 = time.perf_counter()
    list_res = client.run_command("show-threat-protections", {
        "limit": 5, "details-level": "standard",
    })
    dur = time.perf_counter() - t0
    items = list_res.get("objects", [])
    show_ok = bool(items)
    log.info("  SHOW (list): [%.2fs] %s — %d protections found",
             dur, "PASS" if show_ok else "FAIL", len(items))
    results.append({
        "type": obj_type, "variant": 0,
        "command": "show-threat-protections",
        "payload": {"limit": 5, "details-level": "standard"},
        "response": list_res, "success": show_ok, "duration": dur,
    })
    if not show_ok:
        return True  # No protections available — nothing more to test

    # Pick the first protection
    target = items[0]
    target_uid = target.get("uid", "")
    target_name = target.get("name", target_uid)
    log.info("  Target protection: '%s' (uid=%s)", target_name, target_uid)

    # Step 2: SHOW (individual)
    t0 = time.perf_counter()
    show_res = client.run_command("show-threat-protection", {
        "uid": target_uid, "details-level": "full",
    })
    dur = time.perf_counter() - t0
    show1_ok = _is_success(show_res) or "name" in show_res
    log.info("  SHOW (single): [%.2fs] %s", dur, "PASS" if show1_ok else "FAIL")
    results.append({
        "type": obj_type, "variant": 0,
        "command": "show-threat-protection",
        "payload": {"uid": target_uid},
        "response": show_res, "success": show1_ok, "duration": dur,
    })

    # Step 3: SET (add a comment)
    original_comments = show_res.get("comments", "")
    set_payload = {
        "uid": target_uid,
        "comments": "QA lifecycle test — threat-protections",
    }
    set_ok, set_res, set_dur = _retry_command(
        client, "set-threat-protection", set_payload, label="SET",
    )
    results.append({
        "type": obj_type, "variant": 0,
        "command": "set-threat-protection",
        "payload": set_payload,
        "response": set_res, "success": set_ok, "duration": set_dur,
    })

    # Step 4: Revert the comment
    revert_payload = {"uid": target_uid, "comments": original_comments}
    rev_ok, rev_res, rev_dur = _retry_command(
        client, "set-threat-protection", revert_payload, label="SET-REVERT",
    )
    log.info("  SET-REVERT: [%.2fs] %s", rev_dur, "PASS" if rev_ok else "FAIL")

    log.info("--- threat-protections lifecycle complete ---")
    return True


def _lifecycle_web_console_statistics(
    client: Any, results: list[dict], obj_type: str,
) -> bool:
    """Custom lifecycle for ``web-console-statistics``.

    Only ADD (write) and SHOW (read) are supported — no SET or DELETE.
    """
    log.info("--- Custom lifecycle: web-console-statistics ---")
    rand = random.randint(1000, 9999)
    file_name = f"QA_stats_test_{rand}"

    # Step 1: ADD (write statistics)
    add_payload = {
        "file-name": file_name,
        "data": "qa_test_field1=value1",
        "field-names": "qa_test_field1",
        "override-file": True,
    }
    t0 = time.perf_counter()
    add_res = client.run_command("add-web-console-statistics", add_payload)
    dur = time.perf_counter() - t0
    add_ok = (add_res.get("code") == "success"
              or add_res.get("message") == "OK"
              or "statusCode" not in add_res)
    # The API returns ApiOkReply — check for absence of error
    if "message" in add_res and "error" in str(add_res.get("message", "")).lower():
        add_ok = False
    log.info("  ADD: [%.2fs] %s", dur, "PASS" if add_ok else "FAIL")
    results.append({
        "type": obj_type, "variant": 0,
        "command": "add-web-console-statistics",
        "payload": add_payload,
        "response": add_res, "success": add_ok, "duration": dur,
    })

    # Step 2: SHOW (read back)
    show_payload = {"file-name": file_name}
    t0 = time.perf_counter()
    show_res = client.run_command("show-web-console-statistics", show_payload)
    dur = time.perf_counter() - t0
    show_ok = "message" not in show_res or "error" not in str(show_res.get("message", "")).lower()
    log.info("  SHOW: [%.2fs] %s", dur, "PASS" if show_ok else "FAIL")
    results.append({
        "type": obj_type, "variant": 0,
        "command": "show-web-console-statistics",
        "payload": show_payload,
        "response": show_res, "success": show_ok, "duration": dur,
    })

    log.info("--- web-console-statistics lifecycle complete ---")
    return True


def _lifecycle_objects_batch(
    client: Any, results: list[dict], obj_type: str,
) -> bool:
    """Custom lifecycle for ``objects-batch``.

    Creates a batch of simple hosts, modifies them, then deletes them.
    All three commands are async (return task-id).
    """
    log.info("--- Custom lifecycle: objects-batch ---")
    rand = random.randint(1000, 9999)
    hosts = [
        {"name": f"QA_BATCH_H1_{rand}", "ip-address": f"10.200.{random.randint(1,254)}.1"},
        {"name": f"QA_BATCH_H2_{rand}", "ip-address": f"10.200.{random.randint(1,254)}.2"},
    ]

    # Step 1: ADD batch
    add_payload = {"objects": [{"type": "host", "list": hosts}]}
    t0 = time.perf_counter()
    add_res = client.run_command("add-objects-batch", add_payload)
    dur = time.perf_counter() - t0
    add_ok = _is_success(add_res)
    if not add_ok and "task-id" in add_res:
        poll_t0 = time.perf_counter()
        add_ok, add_res = _poll_async_task(client, add_res["task-id"])
        dur += time.perf_counter() - poll_t0
    # Also accept tasks list as success indicator
    if not add_ok and "tasks" in add_res:
        tasks = add_res.get("tasks", [])
        if tasks and tasks[0].get("status") == "succeeded":
            add_ok = True
    log.info("  ADD: [%.2fs] %s", dur, "PASS" if add_ok else "FAIL")
    results.append({
        "type": obj_type, "variant": 0,
        "command": "add-objects-batch",
        "payload": add_payload,
        "response": add_res, "success": add_ok, "duration": dur,
    })

    if not add_ok:
        log.error("  objects-batch ADD failed — skipping SET/DELETE")
        return True

    client.publish()
    time.sleep(2)

    # Step 2: SET batch
    set_hosts = [
        {"name": hosts[0]["name"], "comments": "QA batch set test", "color": "orange"},
        {"name": hosts[1]["name"], "comments": "QA batch set test", "color": "orange"},
    ]
    set_payload = {"objects": [{"type": "host", "list": set_hosts}]}
    t0 = time.perf_counter()
    set_res = client.run_command("set-objects-batch", set_payload)
    dur = time.perf_counter() - t0
    set_ok = _is_success(set_res)
    if not set_ok and "task-id" in set_res:
        poll_t0 = time.perf_counter()
        set_ok, set_res = _poll_async_task(client, set_res["task-id"])
        dur += time.perf_counter() - poll_t0
    if not set_ok and "tasks" in set_res:
        tasks = set_res.get("tasks", [])
        if tasks and tasks[0].get("status") == "succeeded":
            set_ok = True
    log.info("  SET: [%.2fs] %s", dur, "PASS" if set_ok else "FAIL")
    results.append({
        "type": obj_type, "variant": 0,
        "command": "set-objects-batch",
        "payload": set_payload,
        "response": set_res, "success": set_ok, "duration": dur,
    })

    client.publish()
    time.sleep(2)

    # Step 3: DELETE batch
    del_hosts = [{"name": h["name"]} for h in hosts]
    del_payload = {"objects": [{"type": "host", "list": del_hosts}]}
    t0 = time.perf_counter()
    del_res = client.run_command("delete-objects-batch", del_payload)
    dur = time.perf_counter() - t0
    del_ok = _is_success(del_res)
    if not del_ok and "task-id" in del_res:
        poll_t0 = time.perf_counter()
        del_ok, del_res = _poll_async_task(client, del_res["task-id"])
        dur += time.perf_counter() - poll_t0
    if not del_ok and "tasks" in del_res:
        tasks = del_res.get("tasks", [])
        if tasks and tasks[0].get("status") == "succeeded":
            del_ok = True
    log.info("  DELETE: [%.2fs] %s", dur, "PASS" if del_ok else "FAIL")
    results.append({
        "type": obj_type, "variant": 0,
        "command": "delete-objects-batch",
        "payload": del_payload,
        "response": del_res, "success": del_ok, "duration": dur,
    })

    client.publish()
    log.info("--- objects-batch lifecycle complete ---")
    return True


def _lifecycle_rules_batch(
    client: Any, results: list[dict], obj_type: str,
) -> bool:
    """Custom lifecycle for ``rules-batch``.

    Creates a batch of access rules in the Standard package, then deletes
    them.  Only ADD and DELETE are supported (no SET for rules-batch).
    """
    log.info("--- Custom lifecycle: rules-batch ---")

    # Find the access layer from the Standard package
    show_pkg = client.run_command("show-package", {
        "name": "Standard", "details-level": "full",
    })
    layer_name = "Network"
    if "uid" in show_pkg:
        al = show_pkg.get("access-layers", [])
        if al and isinstance(al, list):
            if isinstance(al[0], dict):
                layer_name = al[0].get("name", layer_name)
            elif isinstance(al[0], str):
                layer_name = al[0]
    log.info("  Using layer: '%s'", layer_name)

    rand = random.randint(1000, 9999)
    rule_names = [f"QA_BATCH_R1_{rand}", f"QA_BATCH_R2_{rand}"]
    rules = [
        {"name": rule_names[0], "action": "Drop"},
        {"name": rule_names[1], "action": "Accept"},
    ]

    # Step 1: ADD rules batch
    add_payload = {"objects": [{
        "layer": layer_name,
        "type": "access-rule",
        "first-position": "bottom",
        "list": rules,
    }]}
    t0 = time.perf_counter()
    add_res = client.run_command("add-rules-batch", add_payload)
    dur = time.perf_counter() - t0
    add_ok = _is_success(add_res)
    if not add_ok and "task-id" in add_res:
        poll_t0 = time.perf_counter()
        add_ok, add_res = _poll_async_task(client, add_res["task-id"])
        dur += time.perf_counter() - poll_t0
    if not add_ok and "tasks" in add_res:
        tasks = add_res.get("tasks", [])
        if tasks and tasks[0].get("status") == "succeeded":
            add_ok = True
    log.info("  ADD: [%.2fs] %s", dur, "PASS" if add_ok else "FAIL")
    results.append({
        "type": obj_type, "variant": 0,
        "command": "add-rules-batch",
        "payload": add_payload,
        "response": add_res, "success": add_ok, "duration": dur,
    })

    if not add_ok:
        log.error("  rules-batch ADD failed — skipping DELETE")
        return True

    client.publish()
    time.sleep(2)

    # Step 2: DELETE rules batch
    del_rules = [{"name": n, "layer": layer_name} for n in rule_names]
    del_payload = {"objects": [{
        "layer": layer_name,
        "type": "access-rule",
        "list": del_rules,
    }]}
    t0 = time.perf_counter()
    del_res = client.run_command("delete-rules-batch", del_payload)
    dur = time.perf_counter() - t0
    del_ok = _is_success(del_res)
    if not del_ok and "task-id" in del_res:
        poll_t0 = time.perf_counter()
        del_ok, del_res = _poll_async_task(client, del_res["task-id"])
        dur += time.perf_counter() - poll_t0
    if not del_ok and "tasks" in del_res:
        tasks = del_res.get("tasks", [])
        if tasks and tasks[0].get("status") == "succeeded":
            del_ok = True
    log.info("  DELETE: [%.2fs] %s", dur, "PASS" if del_ok else "FAIL")
    results.append({
        "type": obj_type, "variant": 0,
        "command": "delete-rules-batch",
        "payload": del_payload,
        "response": del_res, "success": del_ok, "duration": dur,
    })

    client.publish()
    log.info("--- rules-batch lifecycle complete ---")
    return True


# ---------------------------------------------------------------------------
# Custom handler dispatch table
# ---------------------------------------------------------------------------

_CUSTOM_HANDLERS: dict[str, Any] = {
    "threat-protections": _lifecycle_threat_protections,
    "web-console-statistics": _lifecycle_web_console_statistics,
    "objects-batch": _lifecycle_objects_batch,
    "rules-batch": _lifecycle_rules_batch,
}
