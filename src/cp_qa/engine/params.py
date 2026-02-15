"""Parameter extraction from API specification object definitions.

Parses the ``fields``, ``required-fields``, and ``under-more-fields``
sections of a spec object definition into a normalised list of
parameter metadata dicts used by the payload generator.
"""

from __future__ import annotations

from typing import Any


def extract_params_from_obj(obj_def: dict) -> list[dict]:
    """Extract all fields with full type metadata from a spec object definition.

    Handles ``field-alternatives`` (mutually exclusive fields like
    ``ipv4-address`` vs ``ipv6-address``) by grouping them under a
    shared ``group`` ID so the payload generator can produce one
    variant per alternative.

    Args:
        obj_def: An object definition dict from the API spec
                 (e.g. the result of :func:`spec.get_object_by_name`).

    Returns:
        A list of parameter info dicts, each containing:

        - ``name`` (str): Field name.
        - ``mandatory`` (bool): Whether the field is required.
        - ``group`` (str): Conflict-group ID (``"default"`` if none).
        - ``types`` (list[dict]): Full type metadata from the spec.
    """
    params: list[dict] = []
    if not obj_def:
        return params

    # Walk all three field sections with their required status
    field_lists: list[tuple[list, bool]] = [
        (obj_def.get("fields", []), False),
        (obj_def.get("required-fields", []), True),
        (obj_def.get("under-more-fields", []), False),
    ]

    for field_list, is_required in field_lists:
        for field in field_list:
            fname = field.get("name")
            if not fname: continue

            param: dict[str, Any] = {
                "name": fname,
                "mandatory": is_required or field.get("required", False),
                "group": field.get("group", "default"),
                "types": field.get("types", [{"name": "string"}]),
                "description": field.get("description", ""),
            }
            params.append(param)

            # Handle mutually exclusive field-alternatives
            alternatives = field.get("field-alternatives", [])
            if alternatives:
                group_id = f"group_{fname}"
                param["group"] = group_id
                for alt in alternatives:
                    alt_param: dict[str, Any] = {
                        "name": alt.get("name"),
                        "mandatory": is_required,
                        "group": group_id,
                        "types": alt.get("types", [{"name": "string"}]),
                        "description": alt.get("description", ""),
                    }
                    params.append(alt_param)

    return params
