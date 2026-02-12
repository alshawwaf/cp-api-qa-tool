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


def fetch_spec(spec_url: str) -> dict | None:
    """Download and parse the API specification JSON.

    Supports both legacy apis.json and new OpenAPI 3.0 (openapi.json) formats.

    Args:
        spec_url: URL to the spec file (can be file:///... or https://...).

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
            response = requests.get(spec_url, verify=False, timeout=30)
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
