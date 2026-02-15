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
# Schema alignment table
# ---------------------------------------------------------------------------

def _gen_schema_table(
    title: str,
    actual_data: dict,
    schema_dict: dict | None,
    is_request: bool = True,
) -> list[str]:
    """Generate an HTML table comparing actual payload against API schema.

    Columns: Field | Actual Value | Type | Req? | Schema Description
    Rows are grouped: required fields first, then utilized optional,
    then unused schema fields, then extra fields not in schema.
    A coverage summary line is shown above the table.
    """
    schema = schema_dict or {}

    # Coverage statistics
    schema_keys = set(schema.keys())
    actual_keys = set(actual_data.keys())
    utilized = schema_keys & actual_keys
    not_used = schema_keys - actual_keys
    extra = actual_keys - schema_keys
    pct = (len(utilized) / len(schema_keys) * 100) if schema_keys else 0

    label = "sent" if is_request else "returned"
    lines: list[str] = [
        f"**{title}**",
        "",
        f"> **Coverage:** {len(utilized)}/{len(schema_keys)} schema fields "
        f"{label} ({pct:.0f}%)  ",
        f"> Utilized: **{len(utilized)}** &nbsp;|&nbsp; "
        f"Not {label}: **{len(not_used)}** &nbsp;|&nbsp; "
        f"Extra (not in schema): **{len(extra)}**",
        "",
    ]

    if not schema and not actual_data:
        lines.append("*No data available.*")
        return lines

    # Sort: required+sent → required+unsent → optional+sent → optional+unsent → extra
    def _sort_key(k: str) -> tuple:
        sch = schema.get(k)
        req = sch.get("required", False) if sch else False
        in_sch = k in schema
        in_act = k in actual_data
        return (
            0 if req else 1,
            0 if in_act else 1,
            0 if in_sch else 1,
            k,
        )

    all_keys = sorted(schema_keys | actual_keys, key=_sort_key)

    lines += [
        '<div style="overflow-x:auto; margin-bottom:20px;">',
        '<table style="width:100%; border-collapse:collapse; font-family:monospace; font-size:12px; border:1px solid #444;">',
        '  <thead>',
        '    <tr style="background:#2d2d2d; color:#f0f0f0;">',
        '      <th style="padding:8px; border:1px solid #555; width:4%;"></th>',
        '      <th style="padding:8px; border:1px solid #555; width:20%;">Field</th>',
        '      <th style="padding:8px; border:1px solid #555; width:30%;">Actual Value</th>',
        '      <th style="padding:8px; border:1px solid #555; width:8%;">Type</th>',
        '      <th style="padding:8px; border:1px solid #555; width:6%;">Req</th>',
        '      <th style="padding:8px; border:1px solid #555; width:32%;">Schema Description</th>',
        '    </tr>',
        '  </thead>',
        '  <tbody>',
    ]

    for k in all_keys:
        in_act = k in actual_data
        in_sch = k in schema
        sch = schema.get(k, {})

        # Row colour: green = utilized, grey = unused schema, yellow = extra
        if in_act and in_sch:
            bg = "#f0fff0"
        elif in_sch:
            bg = "#f8f8f8"
        else:
            bg = "#fffff0"

        # Actual value cell
        if in_act:
            v = json.dumps(actual_data[k], ensure_ascii=False)
            if len(v) > 120:
                v = v[:120] + "\u2026"
            val_html = (
                f'<code style="background:#e8e8e8; padding:2px 4px; '
                f'border-radius:3px; word-break:break-all;">{v}</code>'
            )
        else:
            tag = "not sent" if is_request else "absent"
            val_html = f'<span style="color:#bbb; font-style:italic;">({tag})</span>'

        # Type & required cells
        if in_sch:
            type_str = sch.get("type", "?")
            req = sch.get("required", False)
            req_html = (
                '<b style="color:#d9534f;">Yes</b>' if req
                else '<span style="color:#999;">No</span>'
            )
        else:
            type_str = "\u2014"
            req_html = '<span style="color:#888;">\u2014</span>'

        # Description cell — includes valid-values when present
        desc_parts: list[str] = []
        if in_sch:
            raw_desc = sch.get("description", "")
            if len(raw_desc) > 120:
                raw_desc = raw_desc[:120] + "\u2026"
            if raw_desc:
                desc_parts.append(raw_desc)

            vv = sch.get("valid-values")
            if vv:
                # Check if the sent value is valid
                invalid_flag = ""
                if in_act:
                    sent = actual_data[k]
                    if isinstance(sent, str) and sent not in vv:
                        invalid_flag = ' &#x274C; <b style="color:#d9534f;">sent value not in allowed list</b>'
                vv_str = ", ".join(f"<code>{v}</code>" for v in vv)
                desc_parts.append(
                    f'<br/><b>Allowed values ({len(vv)}):</b> {vv_str}{invalid_flag}'
                )
            desc = "".join(desc_parts) if desc_parts else ""
        else:
            desc = '<span style="color:#888;">(not in schema)</span>'

        # Field name with status indicator
        if in_act and in_sch:
            # If there are valid-values and the sent value is not in them, use warning
            vv = sch.get("valid-values")
            if vv and isinstance(actual_data.get(k), str) and actual_data[k] not in vv:
                indicator = "&#x274C;"
                bg = "#fff0f0"
            else:
                indicator = "&#x2705;"
        elif in_sch:
            indicator = "&#x25CB;"
        else:
            indicator = "&#x26A0;"

        lines.append(f'    <tr style="background:{bg};">')
        lines.append(
            f'      <td style="padding:6px 8px; border:1px solid #ddd; '
            f'vertical-align:top; text-align:center;">{indicator}</td>'
        )
        lines.append(
            f'      <td style="padding:6px 8px; border:1px solid #ddd; '
            f'vertical-align:top;"><b>{k}</b></td>'
        )
        lines.append(
            f'      <td style="padding:6px 8px; border:1px solid #ddd; '
            f'vertical-align:top;">{val_html}</td>'
        )
        lines.append(
            f'      <td style="padding:6px 8px; border:1px solid #ddd; '
            f'vertical-align:top; color:#555;">{type_str}</td>'
        )
        lines.append(
            f'      <td style="padding:6px 8px; border:1px solid #ddd; '
            f'vertical-align:top; text-align:center;">{req_html}</td>'
        )
        lines.append(
            f'      <td style="padding:6px 8px; border:1px solid #ddd; '
            f'vertical-align:top; font-size:11px; color:#555;"><i>{desc}</i></td>'
        )
        lines.append('    </tr>')

    lines += ['  </tbody>', '</table>', '</div>', ""]
    return lines


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

def export_markdown_report(results: list[dict], file_path: str, *, api_version: str = "") -> None:
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

    ver_label = f"v{api_version}" if api_version else "unknown"
    lines: list[str] = [
        "# API QA Performance Audit Report",
        f"**API Version:** {ver_label}  ",
        f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
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
        ]

        # Schema alignment table for ADD commands; plain JSON for others
        req_schema = res.get("request_schema")
        res_schema = res.get("response_schema")

        if command.startswith("add-") and req_schema:
            lines += _gen_schema_table(
                "Audit: Request vs. API Schema", payload, req_schema, is_request=True,
            )
            lines += _gen_schema_table(
                "Audit: Response vs. API Schema", response, res_schema, is_request=False,
            )
        else:
            lines += [
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

def export_examples(results: list[dict], base_dir: str, *, api_version: str = "") -> None:
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
        if not add_rec or not add_rec.get("success", False):
            continue  # Only export proven working payloads

        payload = _sanitize_payload(dict(add_rec["payload"]))
        dist_fields = labels.get((otype, var), [])

        # Professional name and comment
        pretty = otype.replace("-", " ").title().replace(" ", "_")
        ver_label = f"v{api_version}" if api_version else "latest"
        if dist_fields:
            tag = "-".join(dist_fields[:2])
            payload["name"] = f"Example_{pretty}_{tag}"
            payload["comments"] = (
                f"Full {otype} using {', '.join(dist_fields)} "
                f"(verified against API {ver_label})"
            )
        else:
            payload["name"] = f"Example_{pretty}_Object"
            payload["comments"] = (
                f"Full {otype} with all supported fields "
                f"(verified against API {ver_label})"
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
# Per-type reports (saved alongside examples)
# ---------------------------------------------------------------------------

def export_per_type_reports(results: list[dict], base_dir: str, *, api_version: str = "") -> None:
    """Generate a separate QA report and raw JSON for each object type.

    For every tested object type, creates two files inside its example
    directory:

    - ``QA_REPORT.md``   — Self-contained Markdown audit report covering
      all variants of that type.
    - ``QA_RAW_DATA.json`` — Raw request/response data for all lifecycle
      steps of that type.

    Args:
        results:  List of result dicts from lifecycle testing.
        base_dir: Examples base directory (e.g. ``reports/examples``).
    """
    if not results:
        log.warning("No results to export per-type reports.")
        return

    skip = _variants_to_skip(results)

    # Group results by object type
    by_type: dict[str, list[dict]] = {}
    for res in results:
        by_type.setdefault(res["type"], []).append(res)

    count = 0
    for obj_type, type_results in by_type.items():
        out_dir = os.path.join(base_dir, obj_type)
        os.makedirs(out_dir, exist_ok=True)

        # --- Per-type raw JSON ---
        filtered = [
            r for r in type_results if (r["type"], r["variant"]) not in skip
        ]
        raw_path = os.path.join(out_dir, "QA_RAW_DATA.json")
        with open(raw_path, "w", encoding="utf-8") as fh:
            json.dump(filtered, fh, indent=2)

        # --- Per-type Markdown report ---
        md_path = os.path.join(out_dir, "QA_REPORT.md")
        _write_per_type_markdown(obj_type, type_results, skip, md_path, api_version=api_version)
        count += 1

    log.info("Exported per-type reports for %d object types to %s", count, base_dir)


def _write_per_type_markdown(
    obj_type: str,
    type_results: list[dict],
    skip: set[tuple[str, int]],
    file_path: str,
    *,
    api_version: str = "",
) -> None:
    """Write a self-contained Markdown report for a single object type."""
    add_keys = _variant_add_keys(type_results, skip)
    labels = _variant_labels(add_keys)
    summary = _variant_summary(type_results, skip)

    ver_label = f"v{api_version}" if api_version else "unknown"
    lines: list[str] = [
        f"# QA Report: `{obj_type}`",
        f"**API Version:** {ver_label}  ",
        f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    # Summary table
    lines += [
        "## Summary",
        "",
        "| Variant | Status | Duration (s) | Distinguishing Fields |",
        "| :--- | :--- | :--- | :--- |",
    ]

    passed = 0
    total = 0
    for (otype, var), data in summary.items():
        if otype != obj_type:
            continue
        total += 1
        status = "PASSED" if data["success"] else "FAILED"
        if data["success"]:
            passed += 1
        label = labels.get((otype, var), "")
        if not label:
            label = "All fields (no alternatives)"
        lines.append(
            f"| {var} | {status} | {data['total_duration']:.2f} | {label} |"
        )

    lines += [
        "",
        f"**Result: {passed}/{total} variants passed**",
        "",
    ]

    # Detailed per-variant sections
    current_variant: int | None = None
    for res in type_results:
        variant = res.get("variant", 0)
        if (obj_type, variant) in skip:
            continue

        command = res.get("command", "")
        success = res.get("success", False)
        payload = res.get("payload", {})
        response = res.get("response", {})
        duration = res.get("duration", 0.0)

        # Variant header
        if variant != current_variant:
            if current_variant is not None:
                lines.append("</details>\n")
            current_variant = variant

            var_data = summary.get((obj_type, variant), {})
            var_status = "PASSED" if var_data.get("success") else "FAILED"
            total_dur = var_data.get("total_duration", 0.0)

            label = labels.get((obj_type, variant), "")
            if label and label != "Same fields":
                title = f"[{var_status}] Variant {variant} — {label} ({total_dur:.2f}s)"
            else:
                title = f"[{var_status}] Variant {variant} ({total_dur:.2f}s)"

            lines += [
                "---",
                f"<details>",
                f"<summary><b>{title}</b></summary>",
                "",
                "### Performance",
                "| Step | Status | Duration (s) |",
                "| :--- | :--- | :--- |",
            ]
            var_cmds = [
                r
                for r in type_results
                if r["variant"] == variant
                and (obj_type, variant) not in skip
            ]
            for vcmd in var_cmds:
                cst = "PASSED" if vcmd["success"] else "FAILED"
                lines.append(
                    f"| `{vcmd['command']}` | {cst} | {vcmd['duration']:.3f} |"
                )
            lines += ["", "### Details", ""]

        # Individual command
        status_label = "PASSED" if success else "FAILED"
        lines += [
            f"#### [{status_label}] `{command}` ({duration:.2f}s)",
            "",
        ]

        req_schema = res.get("request_schema")
        res_schema = res.get("response_schema")

        if command.startswith("add-") and req_schema:
            lines += _gen_schema_table(
                "Audit: Request vs. API Schema", payload, req_schema, is_request=True,
            )
            lines += _gen_schema_table(
                "Audit: Response vs. API Schema", response, res_schema, is_request=False,
            )
        else:
            lines += [
                "**Payload:**",
                "```json",
                json.dumps(payload, indent=2),
                "```",
                "",
                "**Response:**",
                "```json",
                json.dumps(response, indent=2),
                "```",
            ]

        if not success:
            errs = response.get("blocking-errors", response.get("errors", []))
            if errs:
                lines.append("\n**Errors:**")
                for e in errs:
                    msg = e.get("message", e) if isinstance(e, dict) else e
                    lines.append(f"- {msg}")

        lines.append("")

    if current_variant is not None:
        lines.append("</details>")

    with open(file_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


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
