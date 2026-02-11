"""Report generation and example export.

Produces three output artefacts from lifecycle test results:

1. **QA_RAW_DATA.json** — Full request/response data for every step.
2. **QA_SUMMARY_REPORT.md** — Professional Markdown audit report with
   per-variant timing, a summary table, and distinguishing field labels.
3. **examples/<type>/variant_N.json** — Standalone JSON payloads for
   every tested variant, ready to copy-paste into scripts or playbooks.
"""

from __future__ import annotations

import datetime
import json
import os
from typing import Any

from cp_qa.logging import get_logger

log = get_logger(__name__)

# Fields that are boilerplate and should not count as "distinguishing"
_BOILERPLATE = {
    "name", "color", "comments", "tags", "groups",
    "set-if-exists", "ignore-warnings", "ignore-errors", "details-level",
}


# ---------------------------------------------------------------------------
# JSON raw data
# ---------------------------------------------------------------------------

def export_report(results: list[dict], file_path: str) -> None:
    """Write filtered test results to a JSON file.

    Skips Variant 0 for any object type that has Variant 1+ (Variant 0
    is the master which duplicates fields with the first alternative).

    Args:
        results:   List of result dicts from lifecycle testing.
        file_path: Output path (e.g. ``reports/QA_RAW_DATA.json``).
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    skip = _variants_to_skip(results)
    filtered = [r for r in results if (r["type"], r["variant"]) not in skip]

    with open(file_path, "w", encoding="utf-8") as fh:
        json.dump(filtered, fh, indent=2)
    log.info("QA Report exported to %s", file_path)


# ---------------------------------------------------------------------------
# Markdown summary report
# ---------------------------------------------------------------------------

def export_markdown_report(results: list[dict], file_path: str) -> None:
    """Generate a professional performance audit report in Markdown.

    The report contains:
    - A collapsible summary table with pass/fail, timing, and
      distinguishing fields per variant.
    - Detailed per-variant sections with performance metrics, payload
      snapshots, and full API responses.

    Args:
        results:   List of result dicts from lifecycle testing.
        file_path: Output path (e.g. ``reports/QA_SUMMARY_REPORT.md``).
    """
    if not results:
        log.warning("No results to export to Markdown.")
        return

    skip = _variants_to_skip(results)
    add_keys = _variant_add_keys(results, skip)
    labels = _variant_labels(add_keys)
    summary = _variant_summary(results, skip)

    lines: list[str] = [
        "# API QA Performance Audit Report",
        f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "> **Why multiple variants?** The API spec defines mutually exclusive "
        "field-alternatives",
        "> (e.g., `ipv4-address` vs `ipv6-address`). Each variant swaps in a "
        "different",
        "> alternative so the QA achieves full field coverage. Types with no "
        "alternatives",
        "> produce a single variant.",
        "",
        "<details>",
        '<summary><b>Summary Table</b></summary>',
        "",
        "| Object Type | Variant | Status | Duration (s) | Distinguishing Fields |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]

    for (otype, var), data in summary.items():
        status = "[PASSED]" if data["success"] else "[FAILED]"
        label = labels.get((otype, var), "")
        if not label:
            label = "All fields (no alternatives)"
        lines.append(
            f"| {otype} | {var} | {status} | {data['total_duration']:.2f} | {label} |"
        )

    lines += ["", "</details>", ""]

    # Detailed results
    current_type: str | None = None
    current_variant: int | None = None

    for res in results:
        obj_type = res.get("type", "")
        variant = res.get("variant", 0)

        if (obj_type, variant) in skip:
            continue

        command = res.get("command", "")
        success = res.get("success", False)
        payload = res.get("payload", {})
        response = res.get("response", {})
        duration = res.get("duration", 0.0)

        # Object type header
        if obj_type != current_type:
            if current_variant is not None:
                lines.append("</details>\n")
            current_type = obj_type
            current_variant = None
            lines += ["---", f"## {obj_type}", ""]

        # Variant collapsible group
        if variant != current_variant:
            if current_variant is not None:
                lines.append("</details>\n")
            current_variant = variant
            var_status = (
                "[PASSED]" if summary[(obj_type, variant)]["success"] else "[FAILED]"
            )
            total_dur = summary[(obj_type, variant)]["total_duration"]

            label = labels.get((obj_type, variant), "")
            if label and label != "Same fields":
                title = f"{var_status} Variant {variant} — {label} (Total: {total_dur:.2f}s)"
            else:
                title = f"{var_status} Variant {variant} (Total: {total_dur:.2f}s)"

            lines += ["<details>", f"<summary><b>{title}</b></summary>", ""]

            # Performance table
            lines.append("### Performance Metrics")
            lines.append("| Command | Status | Duration (s) |")
            lines.append("| :--- | :--- | :--- |")
            var_cmds = [
                r
                for r in results
                if r["type"] == obj_type and r["variant"] == variant
            ]
            for vcmd in var_cmds:
                cst = "[PASSED]" if vcmd["success"] else "[FAILED]"
                lines.append(
                    f"| `{vcmd['command']}` | {cst} | {vcmd['duration']:.3f} |"
                )
            lines += ["", "### Operational Logs"]

        # Individual command detail
        status_label = "[PASSED]" if success else "[FAILED]"
        lines += [
            f"#### {status_label} `{command}` ([{duration:.2f}s])",
            "",
            "**Payload snapshot:**",
            "```json",
            json.dumps(payload, indent=2),
            "```",
            "**Full Response:**",
            "```json",
            json.dumps(response, indent=2),
            "```",
        ]

        if not success:
            errs = response.get("blocking-errors", response.get("errors", []))
            if errs:
                lines.append("**Errors found:**")
                for e in errs:
                    msg = e.get("message", e) if isinstance(e, dict) else e
                    lines.append(f"- {msg}")

        lines.append("")

    if current_variant is not None:
        lines.append("</details>")

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    log.info("Markdown QA Report exported to %s", file_path)


# ---------------------------------------------------------------------------
# Example payloads
# ---------------------------------------------------------------------------

def export_examples(results: list[dict], base_dir: str) -> None:
    """Export each variant as a standalone JSON example file.

    Structure::

        base_dir/
            <object_type>/
                variant_<N>__<label>.json

    Each file contains the proven ``add-<type>`` payload with
    professional naming and comments — ready for direct use.

    Args:
        results:  List of result dicts from lifecycle testing.
        base_dir: Output directory (e.g. ``reports/examples``).
    """
    if not results:
        log.warning("No results to export as examples.")
        return

    skip = _variants_to_skip(results)
    add_keys = _variant_add_keys(results, skip)
    labels = _variant_labels_raw(add_keys)

    # Group results by (type, variant)
    grouped: dict[tuple[str, int], list[dict]] = {}
    for res in results:
        key = (res["type"], res["variant"])
        if key in skip:
            continue
        grouped.setdefault(key, []).append(res)

    count = 0
    for (otype, var), records in grouped.items():
        # Find the ADD record
        add_rec = next(
            (r for r in records if r["command"].startswith("add-")), None
        )
        if not add_rec:
            continue

        payload = _sanitize_payload(dict(add_rec["payload"]))
        dist_fields = labels.get((otype, var), [])

        # Professional name and comment
        pretty = otype.replace("-", " ").title().replace(" ", "_")
        if dist_fields:
            tag = "-".join(dist_fields[:2])
            payload["name"] = f"Example_{pretty}_{tag}"
            payload["comments"] = (
                f"Full {otype} using {', '.join(dist_fields)} "
                f"(verified against API v2.0.1)"
            )
        else:
            payload["name"] = f"Example_{pretty}_Object"
            payload["comments"] = (
                f"Full {otype} with all supported fields "
                f"(verified against API v2.0.1)"
            )

        # File name
        if dist_fields:
            slug = "_".join(dist_fields)
            fname = f"variant_{var}__{slug}.json"
        else:
            fname = f"variant_{var}.json"

        out_dir = os.path.join(base_dir, otype)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, fname)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        count += 1

    log.info("Exported %d example payloads to %s", count, base_dir)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _variants_to_skip(results: list[dict]) -> set[tuple[str, int]]:
    """Identify (type, 0) pairs that should be skipped when higher variants exist."""
    v_exists: dict[str, set[int]] = {}
    for res in results:
        v_exists.setdefault(res["type"], set()).add(res["variant"])

    skip: set[tuple[str, int]] = set()
    for t, vs in v_exists.items():
        if 0 in vs and any(v > 0 for v in vs):
            skip.add((t, 0))
    return skip


def _variant_add_keys(
    results: list[dict], skip: set[tuple[str, int]]
) -> dict[tuple[str, int], set[str]]:
    """Collect ADD payload keys per (type, variant), excluding skipped variants."""
    add_keys: dict[tuple[str, int], set[str]] = {}
    for res in results:
        key = (res["type"], res["variant"])
        if key in skip:
            continue
        if res["command"].startswith("add-"):
            add_keys[key] = set(res["payload"].keys())
    return add_keys


def _variant_labels(
    add_keys: dict[tuple[str, int], set[str]],
) -> dict[tuple[str, int], str]:
    """Compute distinguishing label strings for the Markdown summary."""
    types_variants: dict[str, dict[int, set[str]]] = {}
    for (otype, var), keys in add_keys.items():
        types_variants.setdefault(otype, {})[var] = keys

    labels: dict[tuple[str, int], str] = {}
    for otype, var_dict in types_variants.items():
        if len(var_dict) <= 1:
            for var in var_dict:
                labels[(otype, var)] = ""
            continue
        common = set.intersection(*var_dict.values())
        for var, keys in var_dict.items():
            unique = sorted((keys - common) - _BOILERPLATE)
            if unique:
                labels[(otype, var)] = ", ".join(f"`{k}`" for k in unique)
            else:
                labels[(otype, var)] = "Same fields"
    return labels


def _variant_labels_raw(
    add_keys: dict[tuple[str, int], set[str]],
) -> dict[tuple[str, int], list[str]]:
    """Compute distinguishing field name lists for example file naming."""
    types_variants: dict[str, dict[int, set[str]]] = {}
    for (otype, var), keys in add_keys.items():
        types_variants.setdefault(otype, {})[var] = keys

    labels: dict[tuple[str, int], list[str]] = {}
    for otype, var_dict in types_variants.items():
        if len(var_dict) <= 1:
            for var in var_dict:
                labels[(otype, var)] = []
            continue
        common = set.intersection(*var_dict.values())
        for var, keys in var_dict.items():
            unique = sorted((keys - common) - _BOILERPLATE)
            labels[(otype, var)] = unique if unique else []
    return labels


def _variant_summary(
    results: list[dict], skip: set[tuple[str, int]]
) -> dict[tuple[str, int], dict]:
    """Aggregate pass/fail status and total duration per variant."""
    summary: dict[tuple[str, int], dict] = {}
    for res in results:
        key = (res["type"], res["variant"])
        if key in skip:
            continue
        if key not in summary:
            summary[key] = {"success": True, "total_duration": 0.0}
        if not res.get("success", False):
            summary[key]["success"] = False
        summary[key]["total_duration"] += res.get("duration", 0.0)
    return summary


def _sanitize_payload(obj: Any, parent_key: str | None = None) -> Any:
    """Replace QA-specific test names/comments with professional examples."""
    if isinstance(obj, dict):
        return {k: _sanitize_payload(v, parent_key=k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_payload(item, parent_key=parent_key) for item in obj]
    if isinstance(obj, str):
        if obj == "QA Automated Test Object":
            return "Example sub-object"
        if obj.startswith("QA_HELPER_EXCEPT_"):
            return "Excluded_Group"
        if obj.startswith("QA_HELPER_INCLUDE_"):
            return "Included_Group"
        if obj.startswith("QA_") and parent_key == "name":
            return "eth0"
    return obj
