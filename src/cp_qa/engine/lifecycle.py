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
        # For async tasks (simple-cluster), the UID may be nested in task details.
        obj_uid = add_res.get("uid", "")
        if not obj_uid:
            # Try to extract from async task result
            tasks = add_res.get("tasks", [])
            if tasks and isinstance(tasks[0], dict):
                details = tasks[0].get("task-details", [])
                if details and isinstance(details[0], dict):
                    obj_uid = details[0].get("uid", "")
        obj_ref = {"uid": obj_uid} if obj_uid else {"name": test_id}

        # Some types require a publish before SET/DELETE works
        # (VPN communities, wildcard, gsn-handover-group, gateways, clusters)
        if obj_type in _PUBLISH_BETWEEN_STEPS:
            log.info("  Publishing before SET (required for %s)...", obj_type)
            client.publish()
            time.sleep(2)  # Let server commit

        # === SET (with retry) ===
        set_payload = {
            **obj_ref,
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
                "payload": set_payload,
                "response": set_res,
                "success": set_success,
                "duration": set_dur,
            }
        )

        # === SHOW ===
        log.info("  Executing SHOW verification...")
        t_start = time.perf_counter()
        show_res = client.run_command(
            f"show-{obj_type}", {**obj_ref, "details-level": "full"}
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
        del_payload = {**obj_ref, "ignore-warnings": True, "ignore-errors": True}
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
