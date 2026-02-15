"""API specification fetching and lookup.

Downloads the Check Point Management API specification (a large JSON
document) from ``sc1.checkpoint.com`` and provides helpers to look up
command definitions and object schemas by name or section.
"""

from __future__ import annotations

from typing import Any

import requests

from cp_qa.logging import get_logger

log = get_logger(__name__)


def fetch_spec(spec_url: str, headers: dict | None = None) -> dict | None:
    """Download and parse the API specification JSON.

    Supports both legacy apis.json and new OpenAPI 3.0 (openapi.json) formats.

    Args:
        spec_url: URL to the spec file (can be file:///... or https://...).
        headers: Optional dictionary of HTTP headers (e.g. for authentication).

    Returns:
        Parsed specification dictionary in the internal apis.json format.
    """
    log.info("Fetching API spec from %s", spec_url)
    try:
        if spec_url.startswith("file:///"):
            import json
            from urllib.parse import unquote
            path = unquote(spec_url[len("file:///") :])
            if ":" not in path and not path.startswith("/"):
                 # Handle relative-ish paths on some OSs if needed, though usually it's absolute
                 pass
            with open(path, "r", encoding="utf-8") as f:
                spec = json.load(f)
        else:
            response = requests.get(spec_url, verify=False, timeout=30, headers=headers)
            response.raise_for_status()
            spec = response.json()

        # Detect format
        if "openapi" in spec:
            log.info("Detected OpenAPI 3.0 format. Converting to internal spec...")
            spec = _convert_openapi_to_apis_json(spec)

        log.info(
            "Spec loaded successfully. Commands: %d, Objects: %d",
            len(spec.get("commands", [])),
            len(spec.get("objects", [])),
        )
        return spec
    except Exception as exc:
        log.error("Failed to fetch API spec: %s", exc)
        return None


def reconstruct_full_spec(base_url: str, version: str) -> dict | None:
    """Reconstruct the full API spec by merging dynamic, static, and content files.
    
    This follows the methodology of cp-docs-to-swagger to bridge the gap
    between server-filtered specs and public documentation.
    """
    v_full = f"v{version}" if not version.startswith("v") else version
    parts = v_full.replace("v", "").split(".")
    v_short = f"v{parts[0]}.{parts[1]}" if len(parts) >= 2 else f"v{parts[0]}"
    
    # Tier 1 & 2: SC1 Paths
    variations = [v_full, v_short]
    
    log.info("--- Reconstruction: Aggregating Documentation Sources ---")
    
    dynamic_spec = None
    static_spec = None
    content_data = None
    
    for v in variations:
        data_url = f"https://sc1.checkpoint.com/documents/latest/APIs/data/{v}/"
        log.info("Trying SC1 path: %s", data_url)
        
        dynamic_url = f"{data_url}dynamic/apis.json"
        dynamic_spec = fetch_spec(dynamic_url)
        if dynamic_spec:
             static_url = f"{data_url}static_content/apis.json"
             content_url = f"{data_url}dynamic/content.json"
             static_spec = fetch_spec(static_url)
             content_data = fetch_spec(content_url)
             break

    # Tier 3: Swagger Proxy (Pre-reconstructed / Processed)
    if not dynamic_spec:
        log.warning("SC1 paths failed. Trying swagger.ai.alshawwaf.ca as documentation source...")
        swagger_url = f"https://swagger.ai.alshawwaf.ca/openapi.json?api_type=management&api_version={v_full}"
        dynamic_spec = fetch_spec(swagger_url)
        if dynamic_spec:
            log.info("Successfully loaded pre-processed spec from swagger proxy.")
            return dynamic_spec

    if not dynamic_spec:
        log.error("Reconstruction failed: All documentation sources are unreachable.")
        return None

    # 2. Map static objects for fast lookup
    static_objects = {obj["name"]: obj for obj in static_spec.get("objects", [])} if static_spec else {}
    
    # 3. Merge Objects: Overlay static details (descriptions/types) onto dynamic schemas
    for dyn_obj in dynamic_spec.get("objects", []):
        name = dyn_obj["name"]
        if name in static_objects:
            _merge_object_fields(dyn_obj, static_objects[name])
            
    # 4. Add missing static-only objects
    dyn_obj_names = {obj["name"] for obj in dynamic_spec.get("objects", [])}
    for name, st_obj in static_objects.items():
        if name not in dyn_obj_names:
            dynamic_spec["objects"].append(st_obj)
            
    # 5. Hierarchy Enrichment
    if content_data and "commands" in content_data:
        _enrich_groups_from_content(dynamic_spec, content_data)

    log.info("Reconstruction COMPLETE. Total Objects: %d", len(dynamic_spec["objects"]))
    return dynamic_spec


def _merge_object_fields(target: dict, source: dict):
    """Merge field definitions from source into target, preferring source for metadata."""
    target_fields = {f["name"]: f for f in target.get("fields", [])}
    
    # Check all 3 potential field lists in source
    for section in ["fields", "required-fields", "under-more-fields"]:
        for sf in source.get(section, []):
            fname = sf.get("name")
            if not fname: continue
            
            if fname in target_fields:
                # Update existing field with better documentation/types if available
                tf = target_fields[fname]
                if sf.get("description"): tf["description"] = sf["description"]
                if sf.get("field-alternatives"): tf["field-alternatives"] = sf["field-alternatives"]
                # etc.
            else:
                # Add "hidden" fields (under-more-fields etc.) to the primary list
                target["fields"].append(sf)


def _enrich_groups_from_content(spec: dict, content: dict):
    """Use content hierarchy to assign proper public-facing groups to commands."""
    content_cmds = {c["name"]["web"]: c for c in content.get("commands", []) if "name" in c and "web" in c["name"]}
    for d_cmd in spec.get("commands", []):
        web_name = d_cmd.get("name", {}).get("web")
        if web_name in content_cmds:
            # Prefer content hierarchy group (it matches the sidebar)
            d_cmd["group"] = content_cmds[web_name].get("group", d_cmd["group"])


def _convert_openapi_to_apis_json(openapi: dict) -> dict:
    """Translate OpenAPI 3.0 spec to the legacy apis.json format."""
    commands = []
    objects_map = {}

    # 1. Map paths to commands
    for path, methods in openapi.get("paths", {}).items():
        # Clean path to get command name (e.g. /add-host -> add-host)
        cmd_name = path.lstrip("/")
        if not cmd_name or "/" in cmd_name:
             continue # Skip complex paths or root
             
        post = methods.get("post")
        if not post:
            continue
            
        group = post.get("tags", ["General"])[0]
        
        # Extract request schema
        request_obj_name = None
        req_body = post.get("requestBody", {})
        content = req_body.get("content", {}).get("application/json", {})
        schema = content.get("schema")
        
        if schema:
            if "$ref" in schema:
                request_obj_name = schema["$ref"].split("/")[-1]
            else:
                # Create a synthetic object name for inline schemas
                request_obj_name = f"{cmd_name}Request"
                _extract_object_info(request_obj_name, schema, objects_map)
                
        commands.append({
            "name": {"web": cmd_name, "api": cmd_name},
            "group": group,
            "request": request_obj_name,
            "documented": True
        })

    # 2. Map components/schemas to objects
    schemas = openapi.get("components", {}).get("schemas", {})
    for name, schema in schemas.items():
        _extract_object_info(name, schema, objects_map)

    return {"commands": commands, "objects": list(objects_map.values())}


def _extract_object_info(name: str, schema: dict, objects_map: dict):
    """Convert an OpenAPI schema object to the internal objects format."""
    if name in objects_map:
        return

    obj_type = schema.get("type", "object")
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    fields = []
    for prop_name, prop_data in properties.items():
        t_name = prop_data.get("type")
        if not t_name and "$ref" in prop_data:
            t_name = "object"
        t_name = t_name or "string"
        
        # Internal type mapping
        internal_type = t_name
        if t_name == "array": internal_type = "list"
        if t_name == "integer": internal_type = "number"
            
        type_dict = {"name": internal_type}
        
        # Handle Arrays/Lists
        if internal_type == "list":
            items = prop_data.get("items", {})
            element_type = items.get("type")
            
            # If type is missing but ref is present, it's likely an object
            if not element_type and "$ref" in items:
                element_type = "object"
            
            element_type = element_type or "string"
            type_dict["element-type"] = {"name": element_type}
            
            if element_type == "object" and "$ref" in items:
                type_dict["element-type"]["object-name"] = items["$ref"].split("/")[-1]

        # Handle Nested Objects
        elif internal_type == "object":
            if "$ref" in prop_data:
                type_dict["object-name"] = prop_data["$ref"].split("/")[-1]
            elif "properties" in prop_data:
                # Synthetic name for anonymous inline objects
                type_dict["object-name"] = f"{name}_{prop_name}_Type"
                _extract_object_info(type_dict["object-name"], prop_data, objects_map)
        
        # If type is string but has a $ref (sometimes happens with polymorphic fields)
        elif internal_type == "string" and "$ref" in prop_data:
            type_dict["name"] = "object"
            type_dict["object-name"] = prop_data["$ref"].split("/")[-1]

        field = {
            "name": prop_name,
            "types": [type_dict],
            "description": prop_data.get("description", "")
        }
        
        # Handle Enums
        if "enum" in prop_data:
            field["allowed-values"] = prop_data["enum"]
            type_dict["valid-values"] = prop_data["enum"]
            
        # Handle field-alternatives (oneOf / anyOf)
        if "oneOf" in prop_data or "anyOf" in prop_data:
            alts = prop_data.get("oneOf") or prop_data.get("anyOf")
            field_alts = []
            for alt in alts:
                alt_t_name = alt.get("type")
                if not alt_t_name and "$ref" in alt:
                    alt_t_name = "object"
                alt_t_name = alt_t_name or "string"
                
                # Map alt types too
                if alt_t_name == "array": alt_t_name = "list"
                if alt_t_name == "integer": alt_t_name = "number"
                
                alt_type_dict = {"name": alt_t_name}
                
                alt_name = alt.get("name")
                if "$ref" in alt:
                    ref_name = alt["$ref"].split("/")[-1]
                    alt_name = alt_name or ref_name
                    if alt_t_name == "object":
                         alt_type_dict["object-name"] = ref_name
                
                if alt_name:
                    field_alts.append({
                        "name": alt_name,
                        "types": [alt_type_dict]
                    })
            if field_alts:
                field["field-alternatives"] = field_alts
                
        fields.append(field)

    objects_map[name] = {
        "name": name,
        "type": obj_type,
        "fields": fields,
        "required-fields": required
    }


def get_commands_by_section(spec: dict, section_name: str) -> list[dict]:
    """Return all documented commands within a specific section.

    Args:
        spec:         Parsed API specification dictionary.
        section_name: Section/group name to filter by (case-insensitive
                      substring match against the command's ``group`` field).

    Returns:
        List of command definition dicts matching the section.
    """
    if not spec:
        return []

    commands: list[dict] = []
    for cmd in spec.get("commands", []):
        if not cmd.get("documented"):
            continue
        if section_name.lower() in cmd.get("group", "").lower():
            commands.append(cmd)
    return commands


def get_object_by_name(spec: dict, obj_name: str) -> dict | None:
    """Retrieve an object definition from the spec's ``objects`` list.

    Args:
        spec:     Parsed API specification dictionary.
        obj_name: Exact object schema name (e.g. ``"HostRequestNew"``).

    Returns:
        The matching object dict, or ``None`` if not found.
    """
    if not spec:
        return None
    for obj in spec.get("objects", []):
        if obj.get("name") == obj_name:
            return obj
    return None


def get_simplified_schema(spec: dict, obj_name: str) -> dict[str, Any] | None:
    """Return a concise, human-readable summary of an object's schema.

    Processes ``fields``, ``parameters``, ``required-fields``, and
    ``under-more-fields`` sections.  Handles ``required-fields`` being
    either a list of field dicts (native apis.json) or a list of field
    name strings (OpenAPI-converted specs).

    Args:
        spec:     Parsed API specification dictionary.
        obj_name: Name of the object schema (request or response).

    Returns:
        Simplified dictionary mapping field names to
        ``{type, required, description}``.
    """
    obj_def = get_object_by_name(spec, obj_name)
    if not obj_def:
        return None

    simplified: dict[str, dict] = {}

    # "required-fields" can be a list of strings (OpenAPI-converted) or
    # a list of field dicts (native apis.json).  Separate them.
    required_names: set[str] = set()
    req_field_dicts: list[dict] = []
    for item in obj_def.get("required-fields", []):
        if isinstance(item, str):
            required_names.add(item)
        elif isinstance(item, dict):
            req_field_dicts.append(item)
            name = item.get("name")
            if name:
                required_names.add(name)

    def _process_param_list(params: list[dict]) -> None:
        for param in params:
            if not isinstance(param, dict):
                continue
            name = param.get("name")
            if not name:
                continue

            # Extract type and valid-values from 'types' list
            type_str = param.get("type")
            valid_values: list = []
            types = param.get("types", [])
            if not type_str and types:
                type_str = "/".join(t.get("name", "unknown") for t in types)
            if not type_str:
                type_str = "unknown"
            for t in types:
                vv = t.get("valid-values")
                if vv:
                    valid_values = vv
                    break
            # Also check top-level allowed-values
            if not valid_values:
                valid_values = param.get("allowed-values", [])

            entry: dict[str, Any] = {
                "type": type_str,
                "required": (
                    param.get("mandatory", param.get("required", False))
                    or name in required_names
                ),
                "description": param.get("description", ""),
            }
            if valid_values:
                entry["valid-values"] = valid_values
            simplified[name] = entry

            # Handle field alternatives (e.g. ipv4-address vs ipv6-address)
            alts = param.get("field-alternatives", [])
            if alts:
                _process_param_list(alts)

    # Process all field sections
    if "fields" in obj_def:
        _process_param_list(obj_def["fields"])

    if "parameters" in obj_def:
        _process_param_list(obj_def["parameters"])

    if req_field_dicts:
        _process_param_list(req_field_dicts)

    if "under-more-fields" in obj_def:
        _process_param_list(obj_def["under-more-fields"])

    return simplified
