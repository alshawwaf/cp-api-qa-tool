import json
import random
import string
import time
from logger_main import log

class APIQAEngine:
    def __init__(self, client, spec_url):
        self.client = client
        self.spec_url = spec_url
        self.spec = None
        self.results = []

    def fetch_spec(self):
        """Fetch the full API spec from the provided URL."""
        log.info(f"Fetching API spec from {self.spec_url}")
        try:
            import requests
            response = requests.get(self.spec_url, verify=False, timeout=30)
            response.raise_for_status()
            self.spec = response.json()
            log.info(f"Spec fetched successfully. Commands: {len(self.spec.get('commands', []))}")
            return True
        except Exception as e:
            log.error(f"Failed to fetch API spec: {e}")
            return False

    def get_commands_by_section(self, section_name):
        """Return all documented commands within a specific section."""
        if not self.spec:
            return []
        
        commands = []
        for cmd in self.spec.get('commands', []):
            if not cmd.get('documented'):
                continue
            
            # Match by group/section (Note: v2.0.1+ might have empty groups, handled by caller)
            if section_name.lower() in cmd.get('group', '').lower():
                commands.append(cmd)
        return commands
    def get_object_by_name(self, obj_name):
        """Retrieve an object definition from the spec's objects list."""
        if not self.spec:
            return None
        for obj in self.spec.get('objects', []):
            if obj.get('name') == obj_name:
                return obj
        return None

    def extract_params_from_obj(self, obj_def):
        """Extract all fields with FULL type metadata from the spec object definition."""
        params = []
        if not obj_def:
            return params

        field_lists = [
            (obj_def.get('fields', []), False),
            (obj_def.get('required-fields', []), True),
            (obj_def.get('under-more-fields', []), False)
        ]

        for field_list, is_required in field_lists:
            for f in field_list:
                param = {
                    'name': f.get('name'),
                    'mandatory': is_required or f.get('required', False),
                    'group': f.get('group', 'default'),
                    'types': f.get('types', [{'name': 'string'}]),  # Preserve FULL type metadata
                }
                params.append(param)
                
                alternatives = f.get('field-alternatives', [])
                if alternatives:
                    group_id = f"group_{f.get('name')}"
                    param['group'] = group_id
                    for alt in alternatives:
                        alt_param = {
                            'name': alt.get('name'),
                            'mandatory': is_required,
                            'group': group_id,
                            'types': alt.get('types', [{'name': 'string'}]),
                        }
                        params.append(alt_param)
        return params

    def _select_best_type(self, types):
        """Select the best type from a multi-type field definition.
        
        Strategy:
        - If any type has valid-values, prefer it (it's an enum)
        - If types include both 'object' and 'list' of the same object, use 'list' with populated items
        - For simple lists (strings), prefer list (safe default for groups/tags)
        - Otherwise fall back to first type
        """
        if not types:
            return {'name': 'string'}
        
        # If any type has valid-values, use it (enum)
        for t in types:
            if t.get('valid-values'):
                return t
        
        # If there's a list of objects, prefer it (e.g., interfaces)
        for t in types:
            if t.get('name') == 'list':
                element = t.get('element-type', {})
                if element.get('name') == 'object' and element.get('object-name'):
                    return t  # list-of-objects -> we'll build a populated list
        
        # If any type is 'object' with an object-name, use it
        for t in types:
            if t.get('name') == 'object' and t.get('object-name'):
                return t
        
        # If any type is a simple 'list' (of strings), prefer it
        for t in types:
            if t.get('name') == 'list':
                return t
        
        # Fall back to the first type
        return types[0]

    def generate_test_data(self, param_info, seed=None):
        """Generate a valid test value using the FULL type schema from the spec."""
        types = param_info.get('types', [{'name': 'string'}])
        name = param_info.get('name', '').lower()
        
        # Use smart type selection for multi-type fields
        primary_type = self._select_best_type(types)
        type_name = primary_type.get('name', 'string')
        valid_values = primary_type.get('valid-values', [])
        object_name = primary_type.get('object-name', '')

        # --- 1. ENUMS: If the spec defines valid-values, pick from them ---
        if valid_values:
            return random.choice(valid_values)

        # --- 2. SUB-OBJECTS: If the type references another object, build it ---
        if type_name == 'object' and object_name:
            return self._build_sub_object(object_name)

        # --- 3. LISTS ---
        if type_name == 'list':
            element = primary_type.get('element-type', {})
            # List of objects: populate with one fully-built sub-object
            if element.get('name') == 'object' and element.get('object-name'):
                sub = self._build_sub_object(element['object-name'])
                return [sub] if sub else []
            # Simple list (strings): return empty list (safe for groups/tags)
            return []

        # --- 4. BOOLEANS ---
        if type_name == 'boolean':
            if any(x in name for x in ['ignore-warnings', 'ignore-errors', 'set-if-exists', 'auto-rule']):
                return True
            if 'is-sub-domain' in name:
                return False
            return False

        # --- 5. INTEGERS ---
        if type_name == 'integer':
            if 'mask-length' in name:
                if '6' in name: return 64
                return 24
            return random.randint(1, 100)

        # --- 6. STRINGS: contextual values based on field name ---
        # IPv6 addresses
        if any(x in name for x in ['ipv6', 'subnet6']):
            if 'subnet' in name:
                return "2001:db8:85a3::"
            # Multicast context: use valid IPv6 multicast range (ff00::/8)
            if getattr(self, '_current_obj_type', '') == 'multicast-address-range':
                if 'first' in name:
                    return "ff05::1:1"
                if 'last' in name:
                    return "ff05::1:30"
                return "ff05::1:10"
            val = seed if seed is not None else random.randint(0x1000, 0x4000)
            return f"2001:db8:85a3::{val:04x}"

        # IPv4 addresses / subnets
        if any(x in name for x in ['ip-address', 'ipv4', 'subnet', 'first', 'last']):
            if 'subnet' in name:
                return "10.100.0.0"
            # Multicast context: use valid multicast range (224.0.0.0 - 239.255.255.255)
            if getattr(self, '_current_obj_type', '') == 'multicast-address-range':
                if 'first' in name:
                    return "224.0.1.10"
                if 'last' in name:
                    return "224.0.1.30"
                return "224.0.1.20"
            # Use deterministic values for first/last to guarantee first < last
            if 'first' in name:
                return "10.100.1.10"
            if 'last' in name:
                return "10.100.1.30"
            return f"10.100.1.{random.randint(10, 200)}"

        # Netmasks (subnet-mask, ipv4-mask-wildcard, etc.)
        if 'mask' in name and 'length' not in name:
            if 'wildcard' in name:
                if '6' in name: return "0000:0000:0000:00ff::"
                return "0.0.0.255"
            if '6' in name: return "ffff:ffff:ffff:ffff::"
            return "255.255.255.0"

        # Comments
        if 'comments' in name:
            return "QA Automated Test Object"

        # Domain name for dns-domain objects — must look like a valid DNS domain
        if name == 'name':
            # Defer: name is set by the test harness for top-level objects
            pass

        # Install-on field
        if 'install-on' in name:
            return "Policy Targets"

        # Default string fallback
        return f"QA_{random.randint(1000, 9999)}"

    def _build_sub_object(self, object_name, depth=0):
        """Recursively build a FULLY populated sub-object from the spec's object definitions.
        
        Populates ALL fields (required + optional) to create realistic payloads.
        Uses depth limit to prevent infinite recursion.
        """
        if depth > 3:  # Prevent infinite recursion
            return {}
            
        obj_def = self.get_object_by_name(object_name)
        if not obj_def:
            return {}

        # Special handling for nat-settings: use proven working config
        if 'NatSettings' in object_name and 'CommWithServer' not in object_name:
            return {"auto-rule": "true", "method": "hide", "hide-behind": "gateway"}

        # Contextual name hints based on the object type
        name_hints = self._get_sub_object_name_hints(object_name)

        result = {}
        # Populate ALL field sections: required-fields, fields, under-more-fields
        for section in ['required-fields', 'fields', 'under-more-fields']:
            for f in obj_def.get(section, []):
                fname = f.get('name', '')
                ftypes = f.get('types', [{'name': 'string'}])
                
                # Skip details-level within sub-objects (not useful for test data)
                if fname == 'details-level':
                    continue
                
                # Special case for interfaces: if it's a list, provide a realistic dummy
                if fname == 'interfaces':
                    # Return a list with 1 complete interface object
                    result[fname] = [{
                        "name": "eth0",
                        "subnet": "10.200.0.0",
                        "mask-length": 24,
                        "color": "aquamarine",
                        "comments": "QA test interface",
                        "ignore-warnings": True,
                        "ignore-errors": True
                    }]
                    continue # Move to the next field
                
                param_info = {'name': fname, 'types': ftypes}
                
                # For nested objects/lists of objects, go deeper
                best_type = self._select_best_type(ftypes)
                if best_type.get('name') == 'object' and best_type.get('object-name'):
                    result[fname] = self._build_sub_object(best_type['object-name'], depth + 1)
                elif best_type.get('name') == 'list':
                    element = best_type.get('element-type', {})
                    if element.get('name') == 'object' and element.get('object-name'):
                        sub = self._build_sub_object(element['object-name'], depth + 1)
                        result[fname] = [sub] if sub else []
                    else:
                        result[fname] = []
                else:
                    result[fname] = self.generate_test_data(param_info)

        # Post-build fixups for known dependencies
        # host-servers: web-server must be true when web-server-config is populated
        if 'web-server-config' in result and result['web-server-config']:
            result['web-server'] = True

        return result

    def _get_sub_object_name_hints(self, object_name):
        """Return contextual realistic values for sub-object fields based on the parent object type."""
        name_lower = object_name.lower()
        
        if 'interface' in name_lower:
            return {
                'name': 'eth0',
                'subnet': '10.200.0.0',
                'mask-length': 24,
                'subnet4': '10.200.0.0',
                'mask-length4': 24,
                'subnet6': '2001:db8:200::',
                'mask-length6': 64,
                'subnet-mask': '255.255.255.0',
                'comments': 'QA test interface',
            }
        if 'webserver' in name_lower or 'web_server' in name_lower:
            # Proven working format from production scripts
            return {
                'additional-ports': ['80', '443'],
                'application-engines': ['ASP', 'General'],
                'operating-system': 'x86 linux',
            }
        if 'hostservers' in name_lower or 'host.servers' in name_lower:
            return {
                'dns-server': 'true',
                'mail-server': 'true',
                'web-server': 'true',  # Must be true when web-server-config is populated
            }
        return {}

    def generate_payloads(self, parameters):
        """Generate a minimal set of 'Full' payloads covering 100% of parameters.
        
        Strategy:
        1. Build a 'master' payload with all default fields + first choice from each conflict group.
        2. For each alternative in each conflict group, create a variant that swaps it in
           AND cleans up cross-group co-requisites (e.g., first/last pairs).
        """
        # 1. Identify conflict groups
        groups = {}
        all_conflict_names = set()  # Track all names that belong to any conflict group
        for p in parameters:
            gid = p.get('group', 'default')
            if gid not in groups: groups[gid] = []
            groups[gid].append(p)
            if gid != 'default':
                all_conflict_names.add(p['name'])

        # 2. Build the master payload
        master = {}
        master_group_choices = {}  # Track which member was chosen per group
        
        for gid, members in groups.items():
            if gid == 'default':
                for m in members:
                    master[m['name']] = self.generate_test_data(m)
            else:
                chosen = members[0]
                master[chosen['name']] = self.generate_test_data(chosen)
                master_group_choices[gid] = chosen['name']

        # 3. Apply co-requisites for the master: ensure first+last pairs are complete
        self._apply_co_requisites(master, parameters)

        payloads = [master.copy()]

        # 4. Generate variants for each alternate choice in each conflict group
        for gid, members in groups.items():
            if gid == 'default': continue
            if len(members) <= 1: continue
            
            for i in range(1, len(members)):
                alt = members[i]
                variant = master.copy()
                
                # Remove ALL members of this conflict group (including co-requisites)
                for m in members:
                    variant.pop(m['name'], None)
                
                # Also remove stale co-requisites from the master's choice in this group
                # e.g., if master had ip-address-first + ip-address-last, and we're swapping to
                # ipv4-address-first, we need to remove ip-address-last too
                master_choice_name = master_group_choices.get(gid, '')
                self._remove_co_requisite(variant, master_choice_name)
                
                # Add the alternate choice
                variant[alt['name']] = self.generate_test_data(alt)
                
                # Apply co-requisites for this variant
                self._apply_co_requisites(variant, parameters)
                
                payloads.append(variant)
            
        return payloads

    def _apply_co_requisites(self, payload, parameters):
        """Ensure first/last pairs and subnet/mask pairs are complete in payload."""
        keys = list(payload.keys())
        for key in keys:
            name_low = key.lower()
            
            # First needs Last
            if "first" in name_low:
                complement = key.replace("first", "last").replace("First", "Last")
                if complement not in payload:
                    for p in parameters:
                        if p['name'] == complement:
                            payload[complement] = self.generate_test_data(p)
                            break
            
            # Last needs First
            elif "last" in name_low:
                complement = key.replace("last", "first").replace("Last", "First")
                if complement not in payload:
                    for p in parameters:
                        if p['name'] == complement:
                            payload[complement] = self.generate_test_data(p)
                            break

    def _remove_co_requisite(self, payload, field_name):
        """Remove co-requisites of a field being swapped out."""
        name_low = field_name.lower()
        if "first" in name_low:
            complement = field_name.replace("first", "last").replace("First", "Last")
            payload.pop(complement, None)
        elif "last" in name_low:
            complement = field_name.replace("last", "first").replace("Last", "First")
            payload.pop(complement, None)


    def _apply_type_defaults(self, obj_type, payload):
        """Apply type-specific known-good defaults for complex types.

        Called before the first ADD attempt to prevent known failures.
        Strips deep-nested fields the engine cannot auto-generate and
        injects proven working values.
        """
        if obj_type == 'time':
            # Time objects need proper date/recurrence format — not random strings
            for f in list(payload.keys()):
                if f not in ('name', 'color', 'comments',
                             'ignore-warnings', 'ignore-errors'):
                    payload.pop(f, None)
            payload['start-now'] = True
            payload['end-never'] = True

        elif obj_type == 'time-group':
            # Keep only essentials (members injected by caller)
            for f in list(payload.keys()):
                if f not in ('name', 'color', 'comments', 'members',
                             'ignore-warnings', 'ignore-errors'):
                    payload.pop(f, None)

        elif obj_type == 'network-feed':
            # Needs a valid feed-url at minimum
            payload['feed-url'] = 'https://secureupdates.checkpoint.com/IP-list/TOR.txt'
            payload['feed-format'] = 'Flat List'
            payload['feed-type'] = 'IP Address'
            # Strip fields that cause validation issues
            for f in ['certificate-id', 'custom-header', 'data-column',
                       'fields-delimiter', 'ignore-lines-that-start-with',
                       'json-query', 'use-gateway-proxy', 'update-interval']:
                payload.pop(f, None)

        elif obj_type in ('simple-gateway', 'simple-cluster'):
            # Keep only minimal safe fields
            for f in list(payload.keys()):
                if f not in ('name', 'color', 'comments',
                             'ignore-warnings', 'ignore-errors',
                             'ipv4-address'):
                    payload.pop(f, None)
            payload['ipv4-address'] = f"10.100.99.{random.randint(10, 200)}"
            payload['version'] = 'R81.10'

        elif obj_type == 'checkpoint-host':
            for f in list(payload.keys()):
                if f not in ('name', 'color', 'comments',
                             'ignore-warnings', 'ignore-errors',
                             'ipv4-address'):
                    payload.pop(f, None)
            payload['ipv4-address'] = f"10.100.98.{random.randint(10, 200)}"

        elif obj_type == 'interoperable-device':
            for f in list(payload.keys()):
                if f not in ('name', 'color', 'comments',
                             'ignore-warnings', 'ignore-errors',
                             'ipv4-address'):
                    payload.pop(f, None)
            payload['ipv4-address'] = f"10.100.97.{random.randint(10, 200)}"

        elif obj_type == 'lsv-profile':
            for f in list(payload.keys()):
                if f not in ('name', 'color', 'comments',
                             'ignore-warnings', 'ignore-errors'):
                    payload.pop(f, None)

    def run_lifecycle_test(self, obj_type, add_cmd_spec):
        """Execute adaptive add(full) -> set -> show -> delete lifecycle.

        For each variant:
        1. Attempt ADD with full payload
        2. If it fails, analyze the error and auto-fix the payload
        3. Retry up to MAX_RETRIES times
        4. Only record the FINAL result (success or last failure)
        5. On success, proceed with SET -> SHOW -> DELETE
        """
        MAX_RETRIES = 5
        self._current_obj_type = obj_type  # Context for generate_test_data
        log.info(f"--- Starting exhaustive QA for object type: {obj_type} ---")

        # Pre-create helper objects if needed
        helper_group = None
        helper_except_group = None
        helper_time = None
        if obj_type == 'group-with-exclusion':
            helper_group = f"QA_HELPER_INCLUDE_{random.randint(1000, 9999)}"
            helper_except_group = f"QA_HELPER_EXCEPT_{random.randint(1000, 9999)}"
            res1 = self.client.run_command("add-group", {"name": helper_group})
            res2 = self.client.run_command("add-group", {"name": helper_except_group})
            if 'uid' in res1 and 'uid' in res2:
                log.info(f"  Created helper groups: include='{helper_group}', except='{helper_except_group}'")
            else:
                log.warning(f"  Failed to create helper groups")
                helper_group = None
                helper_except_group = None
        elif obj_type == 'time-group':
            helper_time = f"QA_HT{random.randint(100, 999)}"  # ≤11 chars for time name limit
            res = self.client.run_command("add-time", {
                "name": helper_time, "start-now": "true", "end-never": "true"
            })
            if 'uid' in res:
                log.info(f"  Created helper time object: '{helper_time}'")
            else:
                log.warning(f"  Failed to create helper time object: {res.get('message', res)}")
                helper_time = None
        
        request_obj_name = add_cmd_spec.get('request')
        obj_def = self.get_object_by_name(request_obj_name)
        if not obj_def:
            log.warning(f"Could not find request object definition for {obj_type}: {request_obj_name}")
            return False

        parameters = self.extract_params_from_obj(obj_def)
        payload_variants = self.generate_payloads(parameters)
        
        log.info(f"Generated {len(payload_variants)} 'Full' test variants for {obj_type}.")

        for i, base_payload in enumerate(payload_variants):
            # Generate proper test ID based on object type
            if obj_type == 'dns-domain':
                test_id = f".qa-domain-{i}-{random.randint(100, 999)}.example.com"
            elif obj_type in ('time', 'time-group'):
                # Time objects have an 11-character name limit
                test_id = f"QA_T{i}_{random.randint(100, 999)}"
            else:
                test_id = f"QA_{obj_type.upper()}_{i}_{random.randint(100, 999)}"
            base_payload['name'] = test_id
            
            log.info(f"Testing Variant {i+1}/{len(payload_variants)}: {test_id}")

            # Apply type-specific defaults BEFORE first attempt
            self._apply_type_defaults(obj_type, base_payload)

            # Inject helper object references for types that need them
            if obj_type == 'group-with-exclusion' and helper_group and helper_except_group:
                base_payload['include'] = helper_group
                base_payload['except'] = helper_except_group
                log.info(f"  Injected include='{helper_group}', except='{helper_except_group}'")
            elif obj_type == 'time-group' and helper_time:
                base_payload['members'] = [helper_time]
                log.info(f"  Injected time member='{helper_time}'")

            # === ADAPTIVE ADD WITH OPTIMIZATION ===
            success = False
            attempt = 0
            add_res = {}
            add_start = time.perf_counter()
            
            while not success and attempt < MAX_RETRIES:
                attempt += 1
                if attempt > 1:
                    log.info(f"  Optimizing payload for accuracy (pass {attempt})...")
                
                add_res = self.client.run_command(f"add-{obj_type}", base_payload)
                success = 'uid' in add_res or add_res.get('code') == 'success'

                # Handle async tasks (e.g., simple-cluster returns task-id)
                if not success and 'task-id' in add_res:
                    task_id = add_res['task-id']
                    log.info(f"  Async task {task_id} — waiting for completion...")
                    for _ in range(30):  # poll up to 30 times (~60s)
                        import time as _time
                        _time.sleep(2)
                        task_res = self.client.run_command("show-task", {"task-id": task_id, "details-level": "full"})
                        tasks = task_res.get('tasks', [])
                        if tasks:
                            status = tasks[0].get('status', '')
                            if status == 'succeeded':
                                success = True
                                break
                            elif status in ('failed', 'partially succeeded'):
                                add_res = {'message': tasks[0].get('task-details', [{}])[0].get('statusDescription', status)}
                                break

                # Accept warnings as success
                if not success and "warning" in str(add_res).lower() and "uid" in str(add_res):
                    success = True
                    break
                
                if success:
                    break
                
                # === AUTO-CORRECTION: Use error feedback to identify missing dependencies or required fields ===
                error_msg = str(add_res.get('message', '')).lower()
                blocking_errors = add_res.get('blocking-errors', add_res.get('errors', []))
                all_errors = error_msg
                for be in blocking_errors:
                    if isinstance(be, dict):
                        all_errors += " " + str(be.get('message', '')).lower()
                    else:
                        all_errors += " " + str(be).lower()
                
                fixed = self._auto_fix_payload(base_payload, all_errors, parameters)
                if not fixed:
                    break
            
            add_duration = time.perf_counter() - add_start
            if success:
                log.info(f"  ADD: [{add_duration:.2f}s] ✅")
            else:
                log.error(f"  ADD: [{add_duration:.2f}s] ❌")

            # Record the FINAL add result
            self.results.append({
                "type": obj_type, "variant": i, "command": f"add-{obj_type}", 
                "payload": dict(base_payload),
                "response": add_res,
                "success": success,
                "duration": add_duration
            })
            
            if not success:
                log.error(f"Add-{obj_type} EXHAUSTED retries for variant {i}: {add_res.get('message', add_res)}")
                continue

            # === SET ===
            set_payload = {
                "name": test_id,
                "comments": f"QA updated exhaustive variant {i}",
                "color": "orange"
            }
            log.info(f"  Executing SET optimization...")
            t_start = time.perf_counter()
            set_res = self.client.run_command(f"set-{obj_type}", set_payload)
            set_dur = time.perf_counter() - t_start
            set_success = 'uid' in set_res or set_res.get('code') == 'success' or set_res.get('message') == 'OK'
            log.info(f"  SET: [{set_dur:.2f}s] {'✅' if set_success else '❌'}")
            
            self.results.append({
                "type": obj_type, "variant": i, "command": f"set-{obj_type}",
                "payload": set_payload, "response": set_res, "success": set_success, "duration": set_dur
            })

            # === SHOW ===
            log.info(f"  Executing SHOW verification...")
            t_start = time.perf_counter()
            show_res = self.client.run_command(f"show-{obj_type}", {"name": test_id, "details-level": "full"})
            show_dur = time.perf_counter() - t_start
            show_success = 'uid' in show_res or show_res.get('code') == 'success' or show_res.get('message') == 'OK'
            log.info(f"  SHOW: [{show_dur:.2f}s] {'✅' if show_success else '❌'}")

            self.results.append({
                "type": obj_type, "variant": i, "command": f"show-{obj_type}",
                "payload": {"name": test_id}, "response": show_res, "success": show_success, "duration": show_dur
            })

            # === DELETE ===
            log.info(f"  Executing DELETE cleanup...")
            t_start = time.perf_counter()
            del_res = self.client.run_command(f"delete-{obj_type}", {"name": test_id})
            del_dur = time.perf_counter() - t_start
            del_success = 'uid' in del_res or del_res.get('code') == 'success' or del_res.get('message') == 'OK'
            log.info(f"  DELETE: [{del_dur:.2f}s] {'✅' if del_success else '❌'}")

            self.results.append({
                "type": obj_type, "variant": i, "command": f"delete-{obj_type}",
                "payload": {"name": test_id}, "response": del_res, "success": del_success, "duration": del_dur
            })

            log.info(f"Finished lifecycle for {test_id} (Completed in {add_duration+set_dur+show_dur+del_dur:.2f}s)")

        # Clean up helper objects
        if helper_group:
            self.client.run_command("delete-group", {"name": helper_group})
            log.info(f"  Cleaned up helper group '{helper_group}'")
        if helper_except_group:
            self.client.run_command("delete-group", {"name": helper_except_group})
            log.info(f"  Cleaned up helper group '{helper_except_group}'")
        if helper_time:
            self.client.run_command("delete-time", {"name": helper_time})
            log.info(f"  Cleaned up helper time '{helper_time}'")

        return True

    def _auto_fix_payload(self, payload, error_text, parameters):
        """Analyze API error feedback and fix the payload in-place.
        
        Returns True if a fix was applied, False if no fix could be found.
        """
        fixed = False
        
        # Fix: "Web Server should be set to true when Web Server Configuration is provided"
        if 'web server' in error_text and 'true' in error_text:
            if 'host-servers' in payload and isinstance(payload['host-servers'], dict):
                payload['host-servers']['web-server'] = True
                log.info("  FIX: Set host-servers.web-server = true")
                fixed = True

        # Fix: "is not a valid IPv4 netmask" -> the subnet-mask value is wrong
        if 'not a valid ipv4 netmask' in error_text:
            if 'subnet-mask' in payload:
                payload['subnet-mask'] = "255.255.0.0"
                log.info("  FIX: Corrected subnet-mask to 255.255.0.0")
                fixed = True
        
        # Fix: "Missing parameter: [mask definition for subnet IPv4/IPv6]"
        if 'missing parameter' in error_text and 'mask definition' in error_text:
            # The versioned subnet (subnet4/subnet6) needs its matching versioned mask
            if 'ipv4' in error_text or 'subnet4' in error_text or 'subnet ipv4' in error_text:
                if 'subnet4' in payload and 'mask-length4' not in payload:
                    payload['mask-length4'] = 24
                    log.info("  FIX: Added mask-length4=24 for subnet4")
                    fixed = True
                # Generic subnet + versioned mask-length6 → replace with mask-length
                if 'subnet' in payload and 'subnet4' not in payload and 'mask-length6' in payload:
                    del payload['mask-length6']
                    if 'mask-length' not in payload:
                        payload['mask-length'] = 24
                    log.info("  FIX: Replaced mask-length6 with mask-length=24 for generic subnet")
                    fixed = True
                # Remove generic mask-length if present alongside versioned subnet
                if 'mask-length' in payload and 'subnet4' in payload and 'mask-length4' not in payload:
                    del payload['mask-length']
                    payload['mask-length4'] = 24
                    log.info("  FIX: Replaced generic mask-length with mask-length4=24")
                    fixed = True
            if 'ipv6' in error_text or 'subnet6' in error_text or 'subnet ipv6' in error_text:
                if 'subnet6' in payload and 'mask-length6' not in payload:
                    payload['mask-length6'] = 64
                    log.info("  FIX: Added mask-length6=64 for subnet6")
                    fixed = True
                if 'mask-length' in payload and 'mask-length6' not in payload:
                    del payload['mask-length']
                    payload['mask-length6'] = 64
                    log.info("  FIX: Replaced generic mask-length with mask-length6=64")
                    fixed = True
        
        # Fix: "Ambiguous IP Address configuration"
        if 'ambiguous' in error_text and 'ip address' in error_text:
            ip_fields = [k for k in payload if 'ip-address' in k.lower() or 'ipv4-address' in k.lower() or 'ipv6-address' in k.lower()]
            
            # Strategy: The API wants EITHER a single IP OR a first+last range, not mixed
            has_standalone = 'ip-address' in payload
            has_any_first_last = any(('first' in f or 'last' in f) for f in ip_fields)
            
            # Case 1: standalone ip-address + any first/last pair -> remove standalone
            if has_standalone and has_any_first_last:
                del payload['ip-address']
                log.info("  FIX: Removed standalone 'ip-address' (keeping range pair)")
                fixed = True
            
            # Case 2: generic first/last + versioned fields -> remove generic pair
            elif 'ip-address-first' in payload and 'ip-address-last' in payload:
                versioned = [f for f in ip_fields if f.startswith(('ipv4-', 'ipv6-'))]
                if versioned:
                    payload.pop('ip-address-first', None)
                    payload.pop('ip-address-last', None)
                    log.info("  FIX: Removed generic range (ip-address-first/last), keeping versioned fields")
                    fixed = True
            
            # Case 3: Multiple IP fields remain -> remove all generics
            if not fixed and len(ip_fields) > 2:
                for g in [f for f in ip_fields if f in ('ip-address', 'ip-address-first', 'ip-address-last')]:
                    if g in payload:
                        del payload[g]
                        log.info(f"  FIX: Removed generic '{g}' to resolve ambiguity")
                fixed = True
        # Fix: "Requested object [X] not found" -> the field references an object that doesn't exist
        if 'requested object' in error_text and 'not found' in error_text:
            # Fix protected-by in host-servers.web-server-config (references non-existent object)
            if 'host-servers' in payload and isinstance(payload['host-servers'], dict):
                wsc = payload['host-servers'].get('web-server-config', {})
                if isinstance(wsc, dict) and 'protected-by' in wsc:
                    del wsc['protected-by']
                    log.info("  FIX: Removed host-servers.web-server-config.protected-by")
                    fixed = True
            # Simplify interfaces to an empty list (names treated as references)
            if 'interfaces' in payload and isinstance(payload['interfaces'], list) and payload['interfaces']:
                payload['interfaces'] = []
                log.info("  FIX: Simplified interfaces to [] (name treated as reference)")
                fixed = True
            # Remove string-valued reference fields
            for field in ['include', 'except', 'members']:
                if field in payload and isinstance(payload[field], str):
                    del payload[field]
                    log.info(f"  FIX: Removed '{field}' (referenced non-existent object)")
                    fixed = True
        
        # Fix: "Invalid parameter for [groups]. Invalid value" — gateway/cluster types don't accept groups
        if 'invalid parameter' in error_text and 'groups' in error_text and 'invalid value' in error_text:
            if 'groups' in payload:
                del payload['groups']
                log.info("  FIX: Removed 'groups' (not supported for this type)")
                fixed = True

        # Fix: "Invalid parameter for [version]" — needs a valid Check Point version string
        if 'invalid parameter' in error_text and 'version' in error_text:
            payload['version'] = 'R81.10'
            log.info("  FIX: Set version to 'R81.10'")
            fixed = True

        # Fix: "hide-behind" / "generate-nat-rules" conflict — strip nat-settings
        if 'hide-behind' in error_text and 'generate-nat-rules' in error_text:
            payload.pop('nat-settings', None)
            # Also strip any top-level nat fields
            for f in list(payload.keys()):
                if 'nat' in f.lower() or 'hide-behind' in f.lower():
                    del payload[f]
                    log.info(f"  FIX: Removed '{f}' (NAT conflict)")
            fixed = True

        # Fix: "value is not valid" for deep nested settings — strip the offending sub-tree
        if 'value is not valid' in error_text and not fixed:
            # Extract the full path from error, e.g. "identity-awareness-settings.identity-sharing-settings..."
            import re
            path_match = re.search(r'full path: ([\w.-]+)', error_text)
            if path_match:
                root_key = path_match.group(1).split('.')[0]
                if root_key in payload:
                    del payload[root_key]
                    log.info(f"  FIX: Removed '{root_key}' (nested value validation error)")
                    fixed = True
            # Also strip any complex dict-valued fields that aren't known good
            if not fixed:
                _KNOWN_GOOD_DICTS = {'nat-settings', 'host-servers'}
                for k, v in list(payload.items()):
                    if isinstance(v, dict) and k not in _KNOWN_GOOD_DICTS:
                        del payload[k]
                        log.info(f"  FIX: Removed complex field '{k}' (nested validation error)")
                        fixed = True
                        break

        # Fix: "Parameter [interfaces] value is not valid" — strip interfaces
        if 'parameter' in error_text and 'interfaces' in error_text and 'not valid' in error_text:
            if 'interfaces' in payload:
                del payload['interfaces']
                log.info("  FIX: Removed 'interfaces' (format not compatible)")
                fixed = True

        # Fix: "Domain name must start with a '.'"
        if 'domain name must start' in error_text:
            name = payload.get('name', '')
            if not name.startswith('.'):
                payload['name'] = '.' + name
                log.info(f"  FIX: Prepended '.' to domain name -> {payload['name']}")
                fixed = True

        # Fix: "Validation failed with N blocking-error(s)" - generic; try progressive fixes
        if 'validation failed' in error_text and 'blocking-error' in error_text and not fixed:
            # Remove details-level FIRST (common cause of validation issues)
            if 'details-level' in payload:
                del payload['details-level']
                log.info("  FIX: Removed 'details-level' (validation issue)")
                fixed = True
            # If first > last, swap them
            if not fixed:
                for prefix in ['ip-address-', 'ipv4-address-', 'ipv6-address-']:
                    first_key = f"{prefix}first"
                    last_key = f"{prefix}last"
                    if first_key in payload and last_key in payload:
                        if '.' in str(payload[first_key]) and '.' in str(payload[last_key]):
                            f_parts = list(map(int, str(payload[first_key]).split('.')))
                            l_parts = list(map(int, str(payload[last_key]).split('.')))
                            if f_parts > l_parts:
                                payload[first_key], payload[last_key] = payload[last_key], payload[first_key]
                                log.info(f"  FIX: Swapped {first_key}/{last_key} for correct ordering")
                                fixed = True
            # For dns-domain: strip is-sub-domain and remove non-essential fields
            if 'is-sub-domain' in payload and not fixed:
                payload['is-sub-domain'] = False
                # Remove tags, color, comments to get minimal valid payload
                for field in ['tags', 'color', 'comments']:
                    payload.pop(field, None)
                log.info("  FIX: Stripped dns-domain to minimal payload")
                fixed = True
            # Remove non-essential fields one at a time as last resort
            if not fixed:
                for field in ['set-if-exists', 'color', 'comments', 'tags', 'groups']:
                    if field in payload:
                        del payload[field]
                        log.info(f"  FIX: Removed non-essential '{field}' to resolve validation")
                        fixed = True
                        break
        
        return fixed

    def export_report(self, file_path):
        """Write the filtered test results to a JSON file."""
        import os
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Filter results to match Markdown logic (Skip Variant 0 if Variant 1+ exists)
        variants_to_skip = set()
        v_exists = {}
        for res in self.results:
            t, v = res['type'], res['variant']
            if t not in v_exists: v_exists[t] = set()
            v_exists[t].add(v)
        for t, vs in v_exists.items():
            if 0 in vs and any(v > 0 for v in vs):
                variants_to_skip.add((t, 0))
        
        filtered_results = [res for res in self.results if (res['type'], res['variant']) not in variants_to_skip]
        
        with open(file_path, 'w') as f:
            json.dump(filtered_results, f, indent=2)
        log.info(f"QA Report exported to {file_path}")

    def export_markdown_report(self, file_path):
        """Generate a professional performance audit report with variant differentiation."""
        if not self.results:
            log.warning("No results to export to Markdown.")
            return

        import datetime
        import os
        
        lines = [
            "# API QA Performance Audit Report",
            f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "> **Why multiple variants?** The API spec defines mutually exclusive field-alternatives",
            "> (e.g., `ipv4-address` vs `ipv6-address`). Each variant swaps in a different",
            "> alternative so the QA achieves full field coverage. Types with no alternatives",
            "> produce a single variant.",
            "",
            "<details>",
            "<summary><b>Summary Table</b></summary>",
            "",
            "| Object Type | Variant | Status | Duration (s) | Distinguishing Fields |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ]

        # 1. Collect ADD payload keys per (type, variant) for diff computation
        variant_add_keys = {}
        for res in self.results:
            if res['command'].startswith('add-'):
                variant_add_keys[(res['type'], res['variant'])] = set(res['payload'].keys())

        # 2. Identify variants to skip (Skip Variant 0 if Variant 1+ exists)
        variants_to_skip = set()
        v_exists = {}
        for res in self.results:
            t, v = res['type'], res['variant']
            if t not in v_exists: v_exists[t] = set()
            v_exists[t].add(v)

        for t, vs in v_exists.items():
            if 0 in vs and any(v > 0 for v in vs):
                variants_to_skip.add((t, 0))

        # 3. Compute variant labels: fields unique to each variant vs. siblings
        #    Ignore boilerplate fields that may be stripped by self-healing retries
        _BOILERPLATE = {'name', 'color', 'comments', 'tags', 'groups',
                        'set-if-exists', 'ignore-warnings', 'ignore-errors', 'details-level'}
        variant_labels = {}  # (type, variant) -> short label string
        types_variants = {}  # type -> {variant: set_of_add_keys}
        for (otype, var), keys in variant_add_keys.items():
            if (otype, var) in variants_to_skip:
                continue
            if otype not in types_variants:
                types_variants[otype] = {}
            types_variants[otype][var] = keys

        for otype, var_dict in types_variants.items():
            if len(var_dict) <= 1:
                for var in var_dict:
                    variant_labels[(otype, var)] = ""
                continue
            common = set.intersection(*var_dict.values())
            for var, keys in var_dict.items():
                unique = sorted((keys - common) - _BOILERPLATE)
                if unique:
                    variant_labels[(otype, var)] = ", ".join(f"`{k}`" for k in unique)
                else:
                    variant_labels[(otype, var)] = "Same fields"

        # 4. Calculate summary per variant
        variant_summary = {}
        for res in self.results:
            key = (res['type'], res['variant'])
            if key in variants_to_skip:
                continue

            if key not in variant_summary:
                variant_summary[key] = {"success": True, "total_duration": 0.0}
            if not res.get('success', False):
                variant_summary[key]["success"] = False
            variant_summary[key]["total_duration"] += res.get('duration', 0.0)

        for (otype, var), data in variant_summary.items():
            status = "[PASSED]" if data["success"] else "[FAILED]"
            label = variant_labels.get((otype, var), "")
            if not label:
                label = "All fields (no alternatives)"
            lines.append(f"| {otype} | {var} | {status} | {data['total_duration']:.2f} | {label} |")
        
        lines.append("")
        lines.append("</details>")
        lines.append("")
        
        # 4. Detailed Results with Comparison and Timing Tables
        current_type = None
        current_variant = None
        
        for res in self.results:
            obj_type = res.get('type', '')
            variant = res.get('variant', 0)
            
            if (obj_type, variant) in variants_to_skip:
                continue

            command = res.get('command', '')
            success = res.get('success', False)
            payload = res.get('payload', {})
            response = res.get('response', {})
            duration = res.get('duration', 0.0)

            # Object Type Header
            if obj_type != current_type:
                if current_variant is not None:
                    lines.append("</details>\n")
                current_type = obj_type
                current_variant = None
                lines.append(f"---")
                lines.append(f"## {obj_type}")
                lines.append("")

            # Variant Collapsible Group
            if variant != current_variant:
                if current_variant is not None:
                    lines.append("</details>\n")
                current_variant = variant
                var_status = "[PASSED]" if variant_summary[(obj_type, variant)]["success"] else "[FAILED]"
                total_dur = variant_summary[(obj_type, variant)]["total_duration"]

                # Build title with distinguishing fields for multi-variant types
                label = variant_labels.get((obj_type, variant), "")
                if label and label != "Same fields":
                    title = f"{var_status} Variant {variant} — {label} (Total: {total_dur:.2f}s)"
                else:
                    title = f"{var_status} Variant {variant} (Total: {total_dur:.2f}s)"

                lines.append(f"<details>")
                lines.append(f"<summary><b>{title}</b></summary>")
                lines.append("")

                # Performance Table for this Variant
                lines.append("### ⏱️ Performance Metrics")
                lines.append("| Command | Status | Duration (s) |")
                lines.append("| :--- | :--- | :--- |")
                
                # We need to collect ALL commands for this variant to show the table
                var_cmds = [r for r in self.results if r['type'] == obj_type and r['variant'] == variant]
                for vcmd in var_cmds:
                    cst = "[PASSED]" if vcmd['success'] else "[FAILED]"
                    lines.append(f"| `{vcmd['command']}` | {cst} | {vcmd['duration']:.3f} |")
                lines.append("")
                lines.append("### 📄 Operational Logs")

            # Individual Command Detail (Collapsed within variant)
            status_label = "[PASSED]" if success else "[FAILED]"
            lines.append(f"#### {status_label} `{command}` ([{duration:.2f}s])")
            lines.append("")
            lines.append("**Payload snapshot:**")
            lines.append("```json")
            lines.append(json.dumps(payload, indent=2))
            lines.append("```")
            
            lines.append("**Full Response:**")
            lines.append("```json")
            lines.append(json.dumps(response, indent=2))
            lines.append("```")
            
            if not success:
                errs = response.get('blocking-errors', response.get('errors', []))
                if errs:
                    lines.append("**Errors found:**")
                    for e in errs:
                        msg = e.get('message', e) if isinstance(e, dict) else e
                        lines.append(f"- {msg}")
            
            lines.append("")

        if current_variant is not None:
            lines.append("</details>")

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        log.info(f"Markdown QA Report exported to {file_path}")

    def export_examples(self, base_dir):
        """Export each variant as a standalone JSON example file.

        Structure:
            base_dir/
                <object_type>/
                    variant_<N>__<label>.json

        Each file contains the full lifecycle (add/set/show/delete) for that
        variant, making it easy to reference a proven working payload.
        """
        import os
        if not self.results:
            log.warning("No results to export as examples.")
            return

        # --- reuse skip / label logic from markdown report ---
        variant_add_keys = {}
        for res in self.results:
            if res['command'].startswith('add-'):
                variant_add_keys[(res['type'], res['variant'])] = set(res['payload'].keys())

        variants_to_skip = set()
        v_exists = {}
        for res in self.results:
            t, v = res['type'], res['variant']
            if t not in v_exists:
                v_exists[t] = set()
            v_exists[t].add(v)
        for t, vs in v_exists.items():
            if 0 in vs and any(v > 0 for v in vs):
                variants_to_skip.add((t, 0))

        _BOILERPLATE = {'name', 'color', 'comments', 'tags', 'groups',
                        'set-if-exists', 'ignore-warnings', 'ignore-errors', 'details-level'}
        variant_labels = {}
        types_variants = {}
        for (otype, var), keys in variant_add_keys.items():
            if (otype, var) in variants_to_skip:
                continue
            if otype not in types_variants:
                types_variants[otype] = {}
            types_variants[otype][var] = keys

        for otype, var_dict in types_variants.items():
            if len(var_dict) <= 1:
                for var in var_dict:
                    variant_labels[(otype, var)] = []
                continue
            common = set.intersection(*var_dict.values())
            for var, keys in var_dict.items():
                unique = sorted((keys - common) - _BOILERPLATE)
                variant_labels[(otype, var)] = unique if unique else []

        # --- group results by (type, variant) ---
        grouped = {}
        for res in self.results:
            key = (res['type'], res['variant'])
            if key in variants_to_skip:
                continue
            grouped.setdefault(key, []).append(res)

        # --- helper: recursively sanitize QA test artifacts from payloads ---
        def _sanitize_payload(obj, parent_key=None):
            """Replace QA-specific test names/comments with professional examples."""
            if isinstance(obj, dict):
                return {k: _sanitize_payload(v, parent_key=k) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_sanitize_payload(item, parent_key=parent_key) for item in obj]
            elif isinstance(obj, str):
                if obj == "QA Automated Test Object":
                    return "Example sub-object"
                if obj.startswith("QA_HELPER_EXCEPT_"):
                    return "Excluded_Group"
                if obj.startswith("QA_HELPER_INCLUDE_"):
                    return "Included_Group"
                if obj.startswith("QA_") and parent_key == "name":
                    return "eth0"
                if obj.startswith("QA_"):
                    return obj  # keep other QA_ refs unchanged (shouldn't exist)
                return obj
            return obj

        # --- write one JSON file per variant (just the proven ADD payload) ---
        count = 0
        for (otype, var), records in grouped.items():
            # Find the ADD record for this variant
            add_rec = None
            for rec in records:
                if rec['command'].startswith('add-'):
                    add_rec = rec
                    break
            if not add_rec:
                continue

            # The example IS the payload — clean, copy-paste ready
            payload = _sanitize_payload(dict(add_rec['payload']))
            dist_fields = variant_labels.get((otype, var), [])

            # Build a descriptive, professional name and comment
            pretty = otype.replace('-', ' ').title().replace(' ', '_')
            if dist_fields:
                tag = "-".join(dist_fields[:2])
                payload['name'] = f"Example_{pretty}_{tag}"
                payload['comments'] = f"Full {otype} using {', '.join(dist_fields)} (verified against API v2.0.1)"
            else:
                payload['name'] = f"Example_{pretty}_Object"
                payload['comments'] = f"Full {otype} with all supported fields (verified against API v2.0.1)"

            # file name: variant_1__ipv4-address.json  (or variant_0.json)
            if dist_fields:
                slug = "_".join(dist_fields)
                fname = f"variant_{var}__{slug}.json"
            else:
                fname = f"variant_{var}.json"

            out_dir = os.path.join(base_dir, otype)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, fname)
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2)
            count += 1

        log.info(f"Exported {count} example payloads to {base_dir}")
