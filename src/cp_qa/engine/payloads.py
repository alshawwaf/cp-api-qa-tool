"""Payload generation and co-requisite logic.

Builds a minimal set of "Full" test payloads that together cover 100 %
of the parameters for a given object type.  Mutually exclusive fields
(conflict groups) produce additional variant payloads, each swapping in
a different alternative.

Co-requisite logic ensures that dependent field pairs (e.g.
``ip-address-first`` / ``ip-address-last``) are always present together.
"""

from __future__ import annotations

from typing import Any

from cp_qa.engine.testdata import generate_test_data
from cp_qa.logging import get_logger

log = get_logger(__name__)


def generate_payloads(
    parameters: list[dict],
    current_obj_type: str = "",
    spec: dict | None = None,
) -> list[dict]:
    """Generate a minimal set of payloads covering 100 % of parameters.

    Strategy:
        1. Build a *master* payload with all default fields plus the
           first choice from each conflict group.
        2. For each alternative in each conflict group, create a
           variant that swaps it in and cleans up stale co-requisites.

    Args:
        parameters:       List of parameter info dicts (from
                         :func:`params.extract_params_from_obj`).
        current_obj_type: Top-level object type (for test data context).
        spec:             Parsed API spec (for sub-object building).

    Returns:
        List of payload dicts — one master + one per extra alternative.
    """
    # 1. Identify conflict groups
    groups: dict[str, list[dict]] = {}
    all_conflict_names: set[str] = set()

    for p in parameters:
        gid = p.get("group", "default")
        groups.setdefault(gid, []).append(p)
        if gid != "default":
            all_conflict_names.add(p["name"])

    # 2. Build the master payload
    master: dict[str, Any] = {}
    master_group_choices: dict[str, str] = {}

    for gid, members in groups.items():
        if gid == "default":
            for m in members:
                master[m["name"]] = generate_test_data(
                    m, current_obj_type=current_obj_type, spec=spec
                )
        else:
            chosen = members[0]
            master[chosen["name"]] = generate_test_data(
                chosen, current_obj_type=current_obj_type, spec=spec
            )
            master_group_choices[gid] = chosen["name"]

    # 3. Ensure first+last pairs are complete in the master
    apply_co_requisites(master, parameters, current_obj_type, spec)

    payloads: list[dict] = [master.copy()]

    # 4. Generate variants for each alternate choice in each group
    for gid, members in groups.items():
        if gid == "default" or len(members) <= 1:
            continue

        for i in range(1, len(members)):
            alt = members[i]
            variant = master.copy()

            # Remove ALL members of this conflict group
            for m in members:
                variant.pop(m["name"], None)

            # Remove stale co-requisites from the master's choice
            master_choice = master_group_choices.get(gid, "")
            remove_co_requisite(variant, master_choice)

            # Add the alternate choice
            variant[alt["name"]] = generate_test_data(
                alt, current_obj_type=current_obj_type, spec=spec
            )

            # Re-apply co-requisites for this variant
            apply_co_requisites(variant, parameters, current_obj_type, spec)

            payloads.append(variant)

    return payloads


def apply_co_requisites(
    payload: dict,
    parameters: list[dict],
    current_obj_type: str = "",
    spec: dict | None = None,
) -> None:
    """Ensure first/last pairs and subnet/mask pairs are complete.

    If a ``*-first`` field is present without its ``*-last`` counterpart
    (or vice-versa), the missing field is generated and added to the
    payload in-place.

    Args:
        payload:          The payload dict to fix (modified in-place).
        parameters:       Full parameter list (for generating missing values).
        current_obj_type: Top-level object type.
        spec:             Parsed API spec.
    """
    keys = list(payload.keys())
    for key in keys:
        name_low = key.lower()

        if "first" in name_low:
            complement = key.replace("first", "last").replace("First", "Last")
            if complement not in payload:
                for p in parameters:
                    if p["name"] == complement:
                        payload[complement] = generate_test_data(
                            p, current_obj_type=current_obj_type, spec=spec
                        )
                        break

        elif "last" in name_low:
            complement = key.replace("last", "first").replace("Last", "First")
            if complement not in payload:
                for p in parameters:
                    if p["name"] == complement:
                        payload[complement] = generate_test_data(
                            p, current_obj_type=current_obj_type, spec=spec
                        )
                        break


def remove_co_requisite(payload: dict, field_name: str) -> None:
    """Remove co-requisites of a field being swapped out.

    When swapping ``ip-address-first`` for ``ipv4-address-first``,
    the old ``ip-address-last`` must also be removed.

    Args:
        payload:    The payload dict (modified in-place).
        field_name: Name of the field being removed.
    """
    name_low = field_name.lower()
    if "first" in name_low:
        complement = field_name.replace("first", "last").replace("First", "Last")
        payload.pop(complement, None)
    elif "last" in name_low:
        complement = field_name.replace("last", "first").replace("Last", "First")
        payload.pop(complement, None)
