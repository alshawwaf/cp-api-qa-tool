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
from cp_qa.engine.spec import get_object_by_name
from cp_qa.engine.type_defaults import apply_type_defaults
from cp_qa.logging import get_logger

log = get_logger(__name__)


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
    helper_group, helper_except_group, helper_time = _create_helpers(
        client, obj_type
    )

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
        _inject_helpers(
            base_payload, obj_type, helper_group, helper_except_group, helper_time
        )

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

        # === SET ===
        set_payload = {
            "name": test_id,
            "comments": f"QA updated exhaustive variant {i}",
            "color": "orange",
        }
        log.info("  Executing SET optimization...")
        t_start = time.perf_counter()
        set_res = client.run_command(f"set-{obj_type}", set_payload)
        set_dur = time.perf_counter() - t_start
        set_success = (
            "uid" in set_res
            or set_res.get("code") == "success"
            or set_res.get("message") == "OK"
        )
        log.info("  SET: [%.2fs] %s", set_dur, "PASS" if set_success else "FAIL")

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
            f"show-{obj_type}", {"name": test_id, "details-level": "full"}
        )
        show_dur = time.perf_counter() - t_start
        show_success = (
            "uid" in show_res
            or show_res.get("code") == "success"
            or show_res.get("message") == "OK"
        )
        log.info("  SHOW: [%.2fs] %s", show_dur, "PASS" if show_success else "FAIL")

        results.append(
            {
                "type": obj_type,
                "variant": i,
                "command": f"show-{obj_type}",
                "payload": {"name": test_id},
                "response": show_res,
                "success": show_success,
                "duration": show_dur,
            }
        )

        # === DELETE ===
        log.info("  Executing DELETE cleanup...")
        t_start = time.perf_counter()
        del_res = client.run_command(f"delete-{obj_type}", {"name": test_id})
        del_dur = time.perf_counter() - t_start
        del_success = (
            "uid" in del_res
            or del_res.get("code") == "success"
            or del_res.get("message") == "OK"
        )
        log.info("  DELETE: [%.2fs] %s", del_dur, "PASS" if del_success else "FAIL")

        results.append(
            {
                "type": obj_type,
                "variant": i,
                "command": f"delete-{obj_type}",
                "payload": {"name": test_id},
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
    _cleanup_helpers(client, helper_group, helper_except_group, helper_time)

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
) -> tuple[str | None, str | None, str | None]:
    """Pre-create helper objects needed by certain types."""
    helper_group = helper_except_group = helper_time = None

    if obj_type == "group-with-exclusion":
        helper_group = f"QA_HELPER_INCLUDE_{random.randint(1000, 9999)}"
        helper_except_group = f"QA_HELPER_EXCEPT_{random.randint(1000, 9999)}"
        res1 = client.run_command("add-group", {"name": helper_group})
        res2 = client.run_command("add-group", {"name": helper_except_group})
        if "uid" in res1 and "uid" in res2:
            log.info(
                "  Created helper groups: include='%s', except='%s'",
                helper_group,
                helper_except_group,
            )
        else:
            log.warning("  Failed to create helper groups")
            helper_group = helper_except_group = None

    elif obj_type == "time-group":
        helper_time = f"QA_HT{random.randint(100, 999)}"
        res = client.run_command(
            "add-time",
            {"name": helper_time, "start-now": "true", "end-never": "true"},
        )
        if "uid" in res:
            log.info("  Created helper time object: '%s'", helper_time)
        else:
            log.warning(
                "  Failed to create helper time object: %s",
                res.get("message", res),
            )
            helper_time = None

    return helper_group, helper_except_group, helper_time


def _inject_helpers(
    payload: dict,
    obj_type: str,
    helper_group: str | None,
    helper_except_group: str | None,
    helper_time: str | None,
) -> None:
    """Inject helper object references into the payload."""
    if obj_type == "group-with-exclusion" and helper_group and helper_except_group:
        payload["include"] = helper_group
        payload["except"] = helper_except_group
        log.info(
            "  Injected include='%s', except='%s'",
            helper_group,
            helper_except_group,
        )
    elif obj_type == "time-group" and helper_time:
        payload["members"] = [helper_time]
        log.info("  Injected time member='%s'", helper_time)


def _cleanup_helpers(
    client: Any,
    helper_group: str | None,
    helper_except_group: str | None,
    helper_time: str | None,
) -> None:
    """Delete helper objects created during the test."""
    if helper_group:
        client.run_command("delete-group", {"name": helper_group})
        log.info("  Cleaned up helper group '%s'", helper_group)
    if helper_except_group:
        client.run_command("delete-group", {"name": helper_except_group})
        log.info("  Cleaned up helper group '%s'", helper_except_group)
    if helper_time:
        client.run_command("delete-time", {"name": helper_time})
        log.info("  Cleaned up helper time '%s'", helper_time)


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
    """Poll an async task until completion (up to ~60 s).

    Returns:
        ``(success, response_dict)``
    """
    import time as _time

    log.info("  Async task %s — waiting for completion...", task_id)
    for _ in range(30):
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
                desc = (
                    tasks[0]
                    .get("task-details", [{}])[0]
                    .get("statusDescription", status)
                )
                return False, {"message": desc}

    return False, {"message": "Async task timed out"}
