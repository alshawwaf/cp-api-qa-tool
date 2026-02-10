# API QA Performance Audit Report
Generated: 2026-02-10 11:29:28

> **Why multiple variants?** The API spec defines mutually exclusive field-alternatives
> (e.g., `ipv4-address` vs `ipv6-address`). Each variant swaps in a different
> alternative so the QA achieves full field coverage. Types with no alternatives
> produce a single variant.

<details>
<summary><b>Summary Table</b></summary>

| Object Type | Variant | Status | Duration (s) | Distinguishing Fields |
| :--- | :--- | :--- | :--- | :--- |
| host | 1 | [PASSED] | 1.97 | `ipv4-address` |
| host | 2 | [PASSED] | 1.08 | `ipv6-address` |
| network | 1 | [PASSED] | 1.71 | `mask-length`, `mask-length4`, `subnet4` |
| network | 2 | [PASSED] | 1.87 | `mask-length`, `mask-length6`, `subnet6` |
| network | 3 | [PASSED] | 1.82 | `mask-length4`, `subnet` |
| network | 4 | [PASSED] | 1.90 | `mask-length`, `subnet` |
| network | 5 | [PASSED] | 1.58 | `subnet`, `subnet-mask` |
| group | 0 | [PASSED] | 0.36 | All fields (no alternatives) |
| address-range | 1 | [PASSED] | 1.53 | `ipv4-address-first`, `ipv4-address-last` |
| address-range | 2 | [PASSED] | 1.44 | `ipv6-address-first`, `ipv6-address-last` |
| address-range | 3 | [PASSED] | 1.45 | `ipv4-address-first`, `ipv4-address-last` |
| address-range | 4 | [PASSED] | 1.66 | `ipv6-address-first`, `ipv6-address-last` |
| multicast-address-range | 1 | [PASSED] | 0.97 | `ipv4-address` |
| multicast-address-range | 2 | [PASSED] | 0.31 | `ip-address-first`, `ip-address-last`, `ipv6-address` |
| multicast-address-range | 3 | [PASSED] | 0.37 | `ipv4-address-first`, `ipv4-address-last` |
| multicast-address-range | 4 | [PASSED] | 0.33 | `ip-address`, `ipv6-address-first`, `ipv6-address-last` |
| multicast-address-range | 5 | [PASSED] | 0.41 | `ipv4-address-first`, `ipv4-address-last` |
| multicast-address-range | 6 | [PASSED] | 0.39 | `ip-address`, `ipv6-address-first`, `ipv6-address-last` |
| group-with-exclusion | 0 | [PASSED] | 0.49 | All fields (no alternatives) |
| dns-domain | 0 | [PASSED] | 0.29 | All fields (no alternatives) |
| wildcard | 0 | [PASSED] | 0.31 | All fields (no alternatives) |
| security-zone | 0 | [PASSED] | 0.28 | All fields (no alternatives) |
| dynamic-object | 0 | [PASSED] | 0.30 | All fields (no alternatives) |
| tag | 0 | [PASSED] | 0.30 | All fields (no alternatives) |
| time | 0 | [PASSED] | 0.82 | All fields (no alternatives) |
| time-group | 0 | [PASSED] | 1.07 | All fields (no alternatives) |
| gsn-handover-group | 0 | [PASSED] | 0.32 | All fields (no alternatives) |
| network-feed | 0 | [PASSED] | 0.32 | All fields (no alternatives) |
| simple-gateway | 1 | [PASSED] | 3.47 | Same fields |
| simple-gateway | 2 | [PASSED] | 14.54 | Same fields |
| simple-gateway | 3 | [PASSED] | 3.79 | Same fields |
| simple-cluster | 1 | [FAILED] | 4.23 | Same fields |
| simple-cluster | 2 | [FAILED] | 2.18 | Same fields |
| checkpoint-host | 1 | [PASSED] | 1.09 | Same fields |
| checkpoint-host | 2 | [PASSED] | 1.12 | Same fields |
| interoperable-device | 1 | [PASSED] | 0.43 | Same fields |
| interoperable-device | 2 | [PASSED] | 0.45 | Same fields |

</details>

---
## host

<details>
<summary><b>[PASSED] Variant 1 — `ipv4-address` (Total: 1.97s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-host` | [PASSED] | 1.263 |
| `set-host` | [PASSED] | 0.182 |
| `show-host` | [PASSED] | 0.077 |
| `delete-host` | [PASSED] | 0.449 |

### 📄 Operational Logs
#### [PASSED] `add-host` ([1.26s])

**Payload snapshot:**
```json
{
  "interfaces": [
    {
      "name": "QA_3684",
      "subnet": "10.100.0.0",
      "mask-length": 24,
      "color": "magenta",
      "comments": "QA Automated Test Object",
      "ignore-warnings": true,
      "ignore-errors": true
    }
  ],
  "nat-settings": {
    "auto-rule": "true",
    "method": "hide",
    "hide-behind": "gateway"
  },
  "host-servers": {
    "dns-server": false,
    "mail-server": false,
    "web-server": true,
    "web-server-config": {
      "additional-ports": [],
      "application-engines": [],
      "listen-standard-port": false,
      "operating-system": "sparc solaris"
    }
  },
  "name": "QA_HOST_1_572",
  "set-if-exists": true,
  "color": "forest green",
  "comments": "QA Automated Test Object",
  "details-level": "standard",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv4-address": "10.100.1.64"
}
```
**Full Response:**
```json
{
  "uid": "e038dff3-db95-45ef-8c09-39bba09c0163",
  "name": "QA_HOST_1_572",
  "type": "host",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address": "10.100.1.64",
  "host-servers": {
    "web-server": true,
    "mail-server": false,
    "dns-server": false,
    "web-server-config": {
      "application-engines": [],
      "listen-standard-port": false,
      "operating-system": "sparc solaris",
      "protected-by": "97aeb368-9aea-11d5-bd16-0090272ccb30"
    }
  },
  "interfaces": [
    {
      "uid": "3182df7f-e8bb-4522-89f5-2ae97e71fdf4",
      "name": "QA_3684",
      "type": "CpmiInterface",
      "domain": {
        "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
        "name": "SMC User",
        "domain-type": "domain"
      },
      "subnet4": "10.100.0.0",
      "mask-length4": 24,
      "subnet-mask": "255.255.255.0",
      "comments": "QA Automated Test Object",
      "color": "magenta",
      "icon": "Unknown",
      "tags": []
    }
  ],
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "forest green",
  "icon": "Objects/host",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732713989,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732713989,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-host` ([0.18s])

**Payload snapshot:**
```json
{
  "name": "QA_HOST_1_572",
  "comments": "QA updated exhaustive variant 1",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "e038dff3-db95-45ef-8c09-39bba09c0163",
  "name": "QA_HOST_1_572",
  "type": "host",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address": "10.100.1.64",
  "host-servers": {
    "web-server": true,
    "mail-server": false,
    "dns-server": false,
    "web-server-config": {
      "application-engines": [],
      "listen-standard-port": false,
      "additional-ports": [],
      "operating-system": "sparc solaris",
      "protected-by": "97aeb368-9aea-11d5-bd16-0090272ccb30"
    }
  },
  "interfaces": [
    {
      "uid": "3182df7f-e8bb-4522-89f5-2ae97e71fdf4",
      "name": "QA_3684",
      "type": "CpmiInterface",
      "domain": {
        "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
        "name": "SMC User",
        "domain-type": "domain"
      },
      "subnet4": "10.100.0.0",
      "mask-length4": 24,
      "subnet-mask": "255.255.255.0",
      "comments": "QA Automated Test Object",
      "color": "magenta",
      "icon": "Unknown",
      "tags": []
    }
  ],
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 1",
  "color": "orange",
  "icon": "Objects/host",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732715204,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732713989,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-host` ([0.08s])

**Payload snapshot:**
```json
{
  "name": "QA_HOST_1_572"
}
```
**Full Response:**
```json
{
  "uid": "e038dff3-db95-45ef-8c09-39bba09c0163",
  "name": "QA_HOST_1_572",
  "type": "host",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address": "10.100.1.64",
  "host-servers": {
    "web-server": true,
    "mail-server": false,
    "dns-server": false,
    "web-server-config": {
      "application-engines": [],
      "listen-standard-port": false,
      "additional-ports": [],
      "operating-system": "sparc solaris",
      "protected-by": "97aeb368-9aea-11d5-bd16-0090272ccb30"
    }
  },
  "interfaces": [
    {
      "uid": "3182df7f-e8bb-4522-89f5-2ae97e71fdf4",
      "name": "QA_3684",
      "type": "CpmiInterface",
      "domain": {
        "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
        "name": "SMC User",
        "domain-type": "domain"
      },
      "subnet4": "10.100.0.0",
      "mask-length4": 24,
      "subnet-mask": "255.255.255.0",
      "comments": "QA Automated Test Object",
      "color": "magenta",
      "icon": "Unknown",
      "tags": []
    }
  ],
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 1",
  "color": "orange",
  "icon": "Objects/host",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732715204,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732713989,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-host` ([0.45s])

**Payload snapshot:**
```json
{
  "name": "QA_HOST_1_572"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

<details>
<summary><b>[PASSED] Variant 2 — `ipv6-address` (Total: 1.08s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-host` | [PASSED] | 0.550 |
| `set-host` | [PASSED] | 0.112 |
| `show-host` | [PASSED] | 0.070 |
| `delete-host` | [PASSED] | 0.347 |

### 📄 Operational Logs
#### [PASSED] `add-host` ([0.55s])

**Payload snapshot:**
```json
{
  "interfaces": [
    {
      "name": "QA_3684",
      "subnet": "10.100.0.0",
      "mask-length": 24,
      "color": "magenta",
      "comments": "QA Automated Test Object",
      "ignore-warnings": true,
      "ignore-errors": true
    }
  ],
  "nat-settings": {
    "auto-rule": "true",
    "method": "hide",
    "hide-behind": "gateway"
  },
  "host-servers": {
    "dns-server": false,
    "mail-server": false,
    "web-server": true,
    "web-server-config": {
      "additional-ports": [],
      "application-engines": [],
      "listen-standard-port": false,
      "operating-system": "sparc solaris"
    }
  },
  "name": "QA_HOST_2_125",
  "set-if-exists": true,
  "color": "forest green",
  "comments": "QA Automated Test Object",
  "details-level": "standard",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv6-address": "2001:db8:85a3::2262"
}
```
**Full Response:**
```json
{
  "uid": "b3a9c92c-17c6-464e-b7f3-751b90840a13",
  "name": "QA_HOST_2_125",
  "type": "host",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv6-address": "2001:db8:85a3::2262",
  "host-servers": {
    "web-server": true,
    "mail-server": false,
    "dns-server": false,
    "web-server-config": {
      "application-engines": [],
      "listen-standard-port": false,
      "operating-system": "sparc solaris",
      "protected-by": "97aeb368-9aea-11d5-bd16-0090272ccb30"
    }
  },
  "interfaces": [
    {
      "uid": "ce9327e9-cb8a-46e5-9b0f-8dcb5cc351c0",
      "name": "QA_3684",
      "type": "CpmiInterface",
      "domain": {
        "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
        "name": "SMC User",
        "domain-type": "domain"
      },
      "subnet4": "10.100.0.0",
      "mask-length4": 24,
      "subnet-mask": "255.255.255.0",
      "comments": "QA Automated Test Object",
      "color": "magenta",
      "icon": "Unknown",
      "tags": []
    }
  ],
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "forest green",
  "icon": "Objects/host",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732715923,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732715923,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-host` ([0.11s])

**Payload snapshot:**
```json
{
  "name": "QA_HOST_2_125",
  "comments": "QA updated exhaustive variant 2",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "b3a9c92c-17c6-464e-b7f3-751b90840a13",
  "name": "QA_HOST_2_125",
  "type": "host",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv6-address": "2001:db8:85a3::2262",
  "host-servers": {
    "web-server": true,
    "mail-server": false,
    "dns-server": false,
    "web-server-config": {
      "application-engines": [],
      "listen-standard-port": false,
      "additional-ports": [],
      "operating-system": "sparc solaris",
      "protected-by": "97aeb368-9aea-11d5-bd16-0090272ccb30"
    }
  },
  "interfaces": [
    {
      "uid": "ce9327e9-cb8a-46e5-9b0f-8dcb5cc351c0",
      "name": "QA_3684",
      "type": "CpmiInterface",
      "domain": {
        "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
        "name": "SMC User",
        "domain-type": "domain"
      },
      "subnet4": "10.100.0.0",
      "mask-length4": 24,
      "subnet-mask": "255.255.255.0",
      "comments": "QA Automated Test Object",
      "color": "magenta",
      "icon": "Unknown",
      "tags": []
    }
  ],
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 2",
  "color": "orange",
  "icon": "Objects/host",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732716453,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732715923,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-host` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_HOST_2_125"
}
```
**Full Response:**
```json
{
  "uid": "b3a9c92c-17c6-464e-b7f3-751b90840a13",
  "name": "QA_HOST_2_125",
  "type": "host",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv6-address": "2001:db8:85a3::2262",
  "host-servers": {
    "web-server": true,
    "mail-server": false,
    "dns-server": false,
    "web-server-config": {
      "application-engines": [],
      "listen-standard-port": false,
      "additional-ports": [],
      "operating-system": "sparc solaris",
      "protected-by": "97aeb368-9aea-11d5-bd16-0090272ccb30"
    }
  },
  "interfaces": [
    {
      "uid": "ce9327e9-cb8a-46e5-9b0f-8dcb5cc351c0",
      "name": "QA_3684",
      "type": "CpmiInterface",
      "domain": {
        "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
        "name": "SMC User",
        "domain-type": "domain"
      },
      "subnet4": "10.100.0.0",
      "mask-length4": 24,
      "subnet-mask": "255.255.255.0",
      "comments": "QA Automated Test Object",
      "color": "magenta",
      "icon": "Unknown",
      "tags": []
    }
  ],
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 2",
  "color": "orange",
  "icon": "Objects/host",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732716453,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732715923,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-host` ([0.35s])

**Payload snapshot:**
```json
{
  "name": "QA_HOST_2_125"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

---
## network

<details>
<summary><b>[PASSED] Variant 1 — `mask-length`, `mask-length4`, `subnet4` (Total: 1.71s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-network` | [PASSED] | 0.757 |
| `set-network` | [PASSED] | 0.085 |
| `show-network` | [PASSED] | 0.071 |
| `delete-network` | [PASSED] | 0.796 |

### 📄 Operational Logs
#### [PASSED] `add-network` ([0.76s])

**Payload snapshot:**
```json
{
  "nat-settings": {
    "auto-rule": "true",
    "method": "hide",
    "hide-behind": "gateway"
  },
  "broadcast": "allow",
  "name": "QA_NETWORK_1_168",
  "set-if-exists": true,
  "color": "violet red",
  "comments": "QA Automated Test Object",
  "details-level": "full",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true,
  "mask-length": 24,
  "subnet4": "10.100.0.0",
  "mask-length4": 24
}
```
**Full Response:**
```json
{
  "uid": "9d88232b-b0fd-45c8-8923-02c60571e325",
  "name": "QA_NETWORK_1_168",
  "type": "network",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "broadcast": "allow",
  "subnet4": "10.100.0.0",
  "mask-length4": 24,
  "subnet-mask": "255.255.255.0",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "violet red",
  "icon": "NetworkObjects/network",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732718275,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732718275,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-network` ([0.08s])

**Payload snapshot:**
```json
{
  "name": "QA_NETWORK_1_168",
  "comments": "QA updated exhaustive variant 1",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "9d88232b-b0fd-45c8-8923-02c60571e325",
  "name": "QA_NETWORK_1_168",
  "type": "network",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "broadcast": "allow",
  "subnet4": "10.100.0.0",
  "mask-length4": 24,
  "subnet-mask": "255.255.255.0",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 1",
  "color": "orange",
  "icon": "NetworkObjects/network",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732718960,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732718275,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-network` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_NETWORK_1_168"
}
```
**Full Response:**
```json
{
  "uid": "9d88232b-b0fd-45c8-8923-02c60571e325",
  "name": "QA_NETWORK_1_168",
  "type": "network",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "broadcast": "allow",
  "subnet4": "10.100.0.0",
  "mask-length4": 24,
  "subnet-mask": "255.255.255.0",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 1",
  "color": "orange",
  "icon": "NetworkObjects/network",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732718960,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732718275,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-network` ([0.80s])

**Payload snapshot:**
```json
{
  "name": "QA_NETWORK_1_168"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

<details>
<summary><b>[PASSED] Variant 2 — `mask-length`, `mask-length6`, `subnet6` (Total: 1.87s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-network` | [PASSED] | 0.997 |
| `set-network` | [PASSED] | 0.085 |
| `show-network` | [PASSED] | 0.070 |
| `delete-network` | [PASSED] | 0.719 |

### 📄 Operational Logs
#### [PASSED] `add-network` ([1.00s])

**Payload snapshot:**
```json
{
  "nat-settings": {
    "auto-rule": "true",
    "method": "hide",
    "hide-behind": "gateway"
  },
  "broadcast": "allow",
  "name": "QA_NETWORK_2_858",
  "set-if-exists": true,
  "color": "violet red",
  "comments": "QA Automated Test Object",
  "details-level": "full",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true,
  "mask-length": 24,
  "subnet6": "2001:db8:85a3::",
  "mask-length6": 64
}
```
**Full Response:**
```json
{
  "uid": "4f2bf3cf-c0b7-4872-8e6a-072506e0cbe8",
  "name": "QA_NETWORK_2_858",
  "type": "network",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "broadcast": "allow",
  "subnet6": "2001:db8:85a3::",
  "mask-length6": 64,
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "violet red",
  "icon": "NetworkObjects/network",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732719981,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732719981,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-network` ([0.09s])

**Payload snapshot:**
```json
{
  "name": "QA_NETWORK_2_858",
  "comments": "QA updated exhaustive variant 2",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "4f2bf3cf-c0b7-4872-8e6a-072506e0cbe8",
  "name": "QA_NETWORK_2_858",
  "type": "network",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "broadcast": "allow",
  "subnet6": "2001:db8:85a3::",
  "mask-length6": 64,
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 2",
  "color": "orange",
  "icon": "NetworkObjects/network",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732720913,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732719981,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-network` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_NETWORK_2_858"
}
```
**Full Response:**
```json
{
  "uid": "4f2bf3cf-c0b7-4872-8e6a-072506e0cbe8",
  "name": "QA_NETWORK_2_858",
  "type": "network",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "broadcast": "allow",
  "subnet6": "2001:db8:85a3::",
  "mask-length6": 64,
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 2",
  "color": "orange",
  "icon": "NetworkObjects/network",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732720913,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732719981,
      "iso-8601": "2026-02-10T09:11-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-network` ([0.72s])

**Payload snapshot:**
```json
{
  "name": "QA_NETWORK_2_858"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

<details>
<summary><b>[PASSED] Variant 3 — `mask-length4`, `subnet` (Total: 1.82s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-network` | [PASSED] | 1.073 |
| `set-network` | [PASSED] | 0.119 |
| `show-network` | [PASSED] | 0.063 |
| `delete-network` | [PASSED] | 0.563 |

### 📄 Operational Logs
#### [PASSED] `add-network` ([1.07s])

**Payload snapshot:**
```json
{
  "nat-settings": {
    "auto-rule": "true",
    "method": "hide",
    "hide-behind": "gateway"
  },
  "broadcast": "allow",
  "name": "QA_NETWORK_3_204",
  "set-if-exists": true,
  "color": "violet red",
  "comments": "QA Automated Test Object",
  "details-level": "full",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true,
  "subnet": "10.100.0.0",
  "mask-length4": 24
}
```
**Full Response:**
```json
{
  "uid": "52a0005e-46d9-41ca-bd93-7c81025c280f",
  "name": "QA_NETWORK_3_204",
  "type": "network",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "broadcast": "allow",
  "subnet4": "10.100.0.0",
  "mask-length4": 24,
  "subnet-mask": "255.255.255.0",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "violet red",
  "icon": "NetworkObjects/network",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732721789,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732721789,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-network` ([0.12s])

**Payload snapshot:**
```json
{
  "name": "QA_NETWORK_3_204",
  "comments": "QA updated exhaustive variant 3",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "52a0005e-46d9-41ca-bd93-7c81025c280f",
  "name": "QA_NETWORK_3_204",
  "type": "network",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "broadcast": "allow",
  "subnet4": "10.100.0.0",
  "mask-length4": 24,
  "subnet-mask": "255.255.255.0",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 3",
  "color": "orange",
  "icon": "NetworkObjects/network",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732722867,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732721789,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-network` ([0.06s])

**Payload snapshot:**
```json
{
  "name": "QA_NETWORK_3_204"
}
```
**Full Response:**
```json
{
  "uid": "52a0005e-46d9-41ca-bd93-7c81025c280f",
  "name": "QA_NETWORK_3_204",
  "type": "network",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "broadcast": "allow",
  "subnet4": "10.100.0.0",
  "mask-length4": 24,
  "subnet-mask": "255.255.255.0",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 3",
  "color": "orange",
  "icon": "NetworkObjects/network",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732722867,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732721789,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-network` ([0.56s])

**Payload snapshot:**
```json
{
  "name": "QA_NETWORK_3_204"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

<details>
<summary><b>[PASSED] Variant 4 — `mask-length`, `subnet` (Total: 1.90s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-network` | [PASSED] | 1.191 |
| `set-network` | [PASSED] | 0.111 |
| `show-network` | [PASSED] | 0.070 |
| `delete-network` | [PASSED] | 0.531 |

### 📄 Operational Logs
#### [PASSED] `add-network` ([1.19s])

**Payload snapshot:**
```json
{
  "nat-settings": {
    "auto-rule": "true",
    "method": "hide",
    "hide-behind": "gateway"
  },
  "broadcast": "allow",
  "name": "QA_NETWORK_4_388",
  "set-if-exists": true,
  "color": "violet red",
  "comments": "QA Automated Test Object",
  "details-level": "full",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true,
  "subnet": "10.100.0.0",
  "mask-length": 24
}
```
**Full Response:**
```json
{
  "uid": "1d3b2f8f-6825-4fd2-ac18-24b142b0c5b3",
  "name": "QA_NETWORK_4_388",
  "type": "network",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "broadcast": "allow",
  "subnet4": "10.100.0.0",
  "mask-length4": 24,
  "subnet-mask": "255.255.255.0",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "violet red",
  "icon": "NetworkObjects/network",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732723711,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732723711,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-network` ([0.11s])

**Payload snapshot:**
```json
{
  "name": "QA_NETWORK_4_388",
  "comments": "QA updated exhaustive variant 4",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "1d3b2f8f-6825-4fd2-ac18-24b142b0c5b3",
  "name": "QA_NETWORK_4_388",
  "type": "network",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "broadcast": "allow",
  "subnet4": "10.100.0.0",
  "mask-length4": 24,
  "subnet-mask": "255.255.255.0",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 4",
  "color": "orange",
  "icon": "NetworkObjects/network",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732724810,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732723711,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-network` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_NETWORK_4_388"
}
```
**Full Response:**
```json
{
  "uid": "1d3b2f8f-6825-4fd2-ac18-24b142b0c5b3",
  "name": "QA_NETWORK_4_388",
  "type": "network",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "broadcast": "allow",
  "subnet4": "10.100.0.0",
  "mask-length4": 24,
  "subnet-mask": "255.255.255.0",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 4",
  "color": "orange",
  "icon": "NetworkObjects/network",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732724810,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732723711,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-network` ([0.53s])

**Payload snapshot:**
```json
{
  "name": "QA_NETWORK_4_388"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

<details>
<summary><b>[PASSED] Variant 5 — `subnet`, `subnet-mask` (Total: 1.58s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-network` | [PASSED] | 0.929 |
| `set-network` | [PASSED] | 0.098 |
| `show-network` | [PASSED] | 0.069 |
| `delete-network` | [PASSED] | 0.480 |

### 📄 Operational Logs
#### [PASSED] `add-network` ([0.93s])

**Payload snapshot:**
```json
{
  "nat-settings": {
    "auto-rule": "true",
    "method": "hide",
    "hide-behind": "gateway"
  },
  "broadcast": "allow",
  "name": "QA_NETWORK_5_708",
  "set-if-exists": true,
  "color": "violet red",
  "comments": "QA Automated Test Object",
  "details-level": "full",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true,
  "subnet": "10.100.0.0",
  "subnet-mask": "255.255.0.0"
}
```
**Full Response:**
```json
{
  "uid": "91c45e4b-2d2e-4ec9-bd1e-d24afc00109f",
  "name": "QA_NETWORK_5_708",
  "type": "network",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "broadcast": "allow",
  "subnet4": "10.100.0.0",
  "mask-length4": 16,
  "subnet-mask": "255.255.0.0",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "violet red",
  "icon": "NetworkObjects/network",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732725573,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732725573,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-network` ([0.10s])

**Payload snapshot:**
```json
{
  "name": "QA_NETWORK_5_708",
  "comments": "QA updated exhaustive variant 5",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "91c45e4b-2d2e-4ec9-bd1e-d24afc00109f",
  "name": "QA_NETWORK_5_708",
  "type": "network",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "broadcast": "allow",
  "subnet4": "10.100.0.0",
  "mask-length4": 16,
  "subnet-mask": "255.255.0.0",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 5",
  "color": "orange",
  "icon": "NetworkObjects/network",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732726439,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732725573,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-network` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_NETWORK_5_708"
}
```
**Full Response:**
```json
{
  "uid": "91c45e4b-2d2e-4ec9-bd1e-d24afc00109f",
  "name": "QA_NETWORK_5_708",
  "type": "network",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "broadcast": "allow",
  "subnet4": "10.100.0.0",
  "mask-length4": 16,
  "subnet-mask": "255.255.0.0",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 5",
  "color": "orange",
  "icon": "NetworkObjects/network",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732726439,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732725573,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-network` ([0.48s])

**Payload snapshot:**
```json
{
  "name": "QA_NETWORK_5_708"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

---
## group

<details>
<summary><b>[PASSED] Variant 0 (Total: 0.36s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-group` | [PASSED] | 0.082 |
| `set-group` | [PASSED] | 0.080 |
| `show-group` | [PASSED] | 0.064 |
| `delete-group` | [PASSED] | 0.137 |

### 📄 Operational Logs
#### [PASSED] `add-group` ([0.08s])

**Payload snapshot:**
```json
{
  "members": [],
  "name": "QA_GROUP_0_699",
  "color": "dark gold",
  "comments": "QA Automated Test Object",
  "details-level": "standard",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true
}
```
**Full Response:**
```json
{
  "uid": "dce63f21-5918-47f0-b4c6-5ee0f5292fd0",
  "name": "QA_GROUP_0_699",
  "type": "group",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "members": [],
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "dark gold",
  "icon": "General/group",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732727089,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732727089,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-group` ([0.08s])

**Payload snapshot:**
```json
{
  "name": "QA_GROUP_0_699",
  "comments": "QA updated exhaustive variant 0",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "dce63f21-5918-47f0-b4c6-5ee0f5292fd0",
  "name": "QA_GROUP_0_699",
  "type": "group",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "members": [],
  "groups": [],
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "General/group",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732727169,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732727089,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-group` ([0.06s])

**Payload snapshot:**
```json
{
  "name": "QA_GROUP_0_699"
}
```
**Full Response:**
```json
{
  "uid": "dce63f21-5918-47f0-b4c6-5ee0f5292fd0",
  "name": "QA_GROUP_0_699",
  "type": "group",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "members": [],
  "groups": [],
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "General/group",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732727169,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732727089,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-group` ([0.14s])

**Payload snapshot:**
```json
{
  "name": "QA_GROUP_0_699"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

---
## address-range

<details>
<summary><b>[PASSED] Variant 1 — `ipv4-address-first`, `ipv4-address-last` (Total: 1.53s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-address-range` | [PASSED] | 0.758 |
| `set-address-range` | [PASSED] | 0.091 |
| `show-address-range` | [PASSED] | 0.065 |
| `delete-address-range` | [PASSED] | 0.619 |

### 📄 Operational Logs
#### [PASSED] `add-address-range` ([0.76s])

**Payload snapshot:**
```json
{
  "nat-settings": {
    "auto-rule": "true",
    "method": "hide",
    "hide-behind": "gateway"
  },
  "name": "QA_ADDRESS-RANGE_1_742",
  "set-if-exists": true,
  "color": "dark orange",
  "comments": "QA Automated Test Object",
  "details-level": "uid",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv4-address-first": "10.100.1.10",
  "ipv4-address-last": "10.100.1.30"
}
```
**Full Response:**
```json
{
  "uid": "12e1aac8-b4f5-4db2-b2a8-896472f2093f",
  "name": "QA_ADDRESS-RANGE_1_742",
  "type": "address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "10.100.1.10",
  "ipv4-address-last": "10.100.1.30",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "dark orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732729276,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732729276,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-address-range` ([0.09s])

**Payload snapshot:**
```json
{
  "name": "QA_ADDRESS-RANGE_1_742",
  "comments": "QA updated exhaustive variant 1",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "12e1aac8-b4f5-4db2-b2a8-896472f2093f",
  "name": "QA_ADDRESS-RANGE_1_742",
  "type": "address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "10.100.1.10",
  "ipv4-address-last": "10.100.1.30",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 1",
  "color": "orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732730032,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732729276,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-address-range` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_ADDRESS-RANGE_1_742"
}
```
**Full Response:**
```json
{
  "uid": "12e1aac8-b4f5-4db2-b2a8-896472f2093f",
  "name": "QA_ADDRESS-RANGE_1_742",
  "type": "address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "10.100.1.10",
  "ipv4-address-last": "10.100.1.30",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 1",
  "color": "orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732730032,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732729276,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-address-range` ([0.62s])

**Payload snapshot:**
```json
{
  "name": "QA_ADDRESS-RANGE_1_742"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

<details>
<summary><b>[PASSED] Variant 2 — `ipv6-address-first`, `ipv6-address-last` (Total: 1.44s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-address-range` | [PASSED] | 0.684 |
| `set-address-range` | [PASSED] | 0.159 |
| `show-address-range` | [PASSED] | 0.075 |
| `delete-address-range` | [PASSED] | 0.518 |

### 📄 Operational Logs
#### [PASSED] `add-address-range` ([0.68s])

**Payload snapshot:**
```json
{
  "nat-settings": {
    "auto-rule": "true",
    "method": "hide",
    "hide-behind": "gateway"
  },
  "name": "QA_ADDRESS-RANGE_2_715",
  "set-if-exists": true,
  "color": "dark orange",
  "comments": "QA Automated Test Object",
  "details-level": "uid",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv6-address-first": "2001:db8:85a3::3a31",
  "ipv6-address-last": "2001:db8:85a3::3f1d"
}
```
**Full Response:**
```json
{
  "uid": "4dd0b7f0-351d-4867-b657-4d0b4b8b407e",
  "name": "QA_ADDRESS-RANGE_2_715",
  "type": "address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv6-address-first": "2001:db8:85a3::3a31",
  "ipv6-address-last": "2001:db8:85a3::3f1d",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "dark orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732730813,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732730813,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-address-range` ([0.16s])

**Payload snapshot:**
```json
{
  "name": "QA_ADDRESS-RANGE_2_715",
  "comments": "QA updated exhaustive variant 2",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "4dd0b7f0-351d-4867-b657-4d0b4b8b407e",
  "name": "QA_ADDRESS-RANGE_2_715",
  "type": "address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv6-address-first": "2001:db8:85a3::3a31",
  "ipv6-address-last": "2001:db8:85a3::3f1d",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 2",
  "color": "orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732731500,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732730813,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-address-range` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_ADDRESS-RANGE_2_715"
}
```
**Full Response:**
```json
{
  "uid": "4dd0b7f0-351d-4867-b657-4d0b4b8b407e",
  "name": "QA_ADDRESS-RANGE_2_715",
  "type": "address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv6-address-first": "2001:db8:85a3::3a31",
  "ipv6-address-last": "2001:db8:85a3::3f1d",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 2",
  "color": "orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732731500,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732730813,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-address-range` ([0.52s])

**Payload snapshot:**
```json
{
  "name": "QA_ADDRESS-RANGE_2_715"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

<details>
<summary><b>[PASSED] Variant 3 — `ipv4-address-first`, `ipv4-address-last` (Total: 1.45s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-address-range` | [PASSED] | 0.672 |
| `set-address-range` | [PASSED] | 0.088 |
| `show-address-range` | [PASSED] | 0.067 |
| `delete-address-range` | [PASSED] | 0.619 |

### 📄 Operational Logs
#### [PASSED] `add-address-range` ([0.67s])

**Payload snapshot:**
```json
{
  "nat-settings": {
    "auto-rule": "true",
    "method": "hide",
    "hide-behind": "gateway"
  },
  "name": "QA_ADDRESS-RANGE_3_130",
  "set-if-exists": true,
  "color": "dark orange",
  "comments": "QA Automated Test Object",
  "details-level": "uid",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv4-address-last": "10.100.1.30",
  "ipv4-address-first": "10.100.1.10"
}
```
**Full Response:**
```json
{
  "uid": "0e7415ce-53cd-4aaf-a145-a5ed039d2a41",
  "name": "QA_ADDRESS-RANGE_3_130",
  "type": "address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "10.100.1.10",
  "ipv4-address-last": "10.100.1.30",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "dark orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732732255,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732732255,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-address-range` ([0.09s])

**Payload snapshot:**
```json
{
  "name": "QA_ADDRESS-RANGE_3_130",
  "comments": "QA updated exhaustive variant 3",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "0e7415ce-53cd-4aaf-a145-a5ed039d2a41",
  "name": "QA_ADDRESS-RANGE_3_130",
  "type": "address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "10.100.1.10",
  "ipv4-address-last": "10.100.1.30",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 3",
  "color": "orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732732920,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732732255,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-address-range` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_ADDRESS-RANGE_3_130"
}
```
**Full Response:**
```json
{
  "uid": "0e7415ce-53cd-4aaf-a145-a5ed039d2a41",
  "name": "QA_ADDRESS-RANGE_3_130",
  "type": "address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "10.100.1.10",
  "ipv4-address-last": "10.100.1.30",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 3",
  "color": "orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732732920,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732732255,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-address-range` ([0.62s])

**Payload snapshot:**
```json
{
  "name": "QA_ADDRESS-RANGE_3_130"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

<details>
<summary><b>[PASSED] Variant 4 — `ipv6-address-first`, `ipv6-address-last` (Total: 1.66s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-address-range` | [PASSED] | 0.766 |
| `set-address-range` | [PASSED] | 0.146 |
| `show-address-range` | [PASSED] | 0.097 |
| `delete-address-range` | [PASSED] | 0.651 |

### 📄 Operational Logs
#### [PASSED] `add-address-range` ([0.77s])

**Payload snapshot:**
```json
{
  "nat-settings": {
    "auto-rule": "true",
    "method": "hide",
    "hide-behind": "gateway"
  },
  "name": "QA_ADDRESS-RANGE_4_212",
  "set-if-exists": true,
  "color": "dark orange",
  "comments": "QA Automated Test Object",
  "details-level": "uid",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv6-address-last": "2001:db8:85a3::3c45",
  "ipv6-address-first": "2001:db8:85a3::358e"
}
```
**Full Response:**
```json
{
  "uid": "8c8ac189-8113-4de5-aec2-1d56bf0eb993",
  "name": "QA_ADDRESS-RANGE_4_212",
  "type": "address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv6-address-first": "2001:db8:85a3::358e",
  "ipv6-address-last": "2001:db8:85a3::3c45",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "dark orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732733723,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732733723,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-address-range` ([0.15s])

**Payload snapshot:**
```json
{
  "name": "QA_ADDRESS-RANGE_4_212",
  "comments": "QA updated exhaustive variant 4",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "8c8ac189-8113-4de5-aec2-1d56bf0eb993",
  "name": "QA_ADDRESS-RANGE_4_212",
  "type": "address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv6-address-first": "2001:db8:85a3::358e",
  "ipv6-address-last": "2001:db8:85a3::3c45",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 4",
  "color": "orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732734496,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732733723,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-address-range` ([0.10s])

**Payload snapshot:**
```json
{
  "name": "QA_ADDRESS-RANGE_4_212"
}
```
**Full Response:**
```json
{
  "uid": "8c8ac189-8113-4de5-aec2-1d56bf0eb993",
  "name": "QA_ADDRESS-RANGE_4_212",
  "type": "address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv6-address-first": "2001:db8:85a3::358e",
  "ipv6-address-last": "2001:db8:85a3::3c45",
  "nat-settings": {
    "auto-rule": true,
    "hide-behind": "gateway",
    "install-on": "All",
    "method": "hide"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 4",
  "color": "orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732734496,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732733723,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-address-range` ([0.65s])

**Payload snapshot:**
```json
{
  "name": "QA_ADDRESS-RANGE_4_212"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

---
## multicast-address-range

<details>
<summary><b>[PASSED] Variant 1 — `ipv4-address` (Total: 0.97s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-multicast-address-range` | [PASSED] | 0.742 |
| `set-multicast-address-range` | [PASSED] | 0.080 |
| `show-multicast-address-range` | [PASSED] | 0.063 |
| `delete-multicast-address-range` | [PASSED] | 0.082 |

### 📄 Operational Logs
#### [PASSED] `add-multicast-address-range` ([0.74s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_1_591",
  "set-if-exists": true,
  "color": "forest green",
  "comments": "QA Automated Test Object",
  "details-level": "uid",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv4-address": "224.0.1.20"
}
```
**Full Response:**
```json
{
  "uid": "3ef4214a-c8e3-4098-b7eb-ba0e562a7ce7",
  "name": "QA_MULTICAST-ADDRESS-RANGE_1_591",
  "type": "multicast-address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "224.0.1.20",
  "ipv4-address-last": "224.0.1.20",
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "forest green",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732736542,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732736542,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-multicast-address-range` ([0.08s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_1_591",
  "comments": "QA updated exhaustive variant 1",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "3ef4214a-c8e3-4098-b7eb-ba0e562a7ce7",
  "name": "QA_MULTICAST-ADDRESS-RANGE_1_591",
  "type": "multicast-address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "224.0.1.20",
  "ipv4-address-last": "224.0.1.20",
  "groups": [],
  "comments": "QA updated exhaustive variant 1",
  "color": "orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732736622,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732736542,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-multicast-address-range` ([0.06s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_1_591"
}
```
**Full Response:**
```json
{
  "uid": "3ef4214a-c8e3-4098-b7eb-ba0e562a7ce7",
  "name": "QA_MULTICAST-ADDRESS-RANGE_1_591",
  "type": "multicast-address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "224.0.1.20",
  "ipv4-address-last": "224.0.1.20",
  "groups": [],
  "comments": "QA updated exhaustive variant 1",
  "color": "orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732736622,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732736542,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-multicast-address-range` ([0.08s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_1_591"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

<details>
<summary><b>[PASSED] Variant 2 — `ip-address-first`, `ip-address-last`, `ipv6-address` (Total: 0.31s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-multicast-address-range` | [PASSED] | 0.080 |
| `set-multicast-address-range` | [PASSED] | 0.079 |
| `show-multicast-address-range` | [PASSED] | 0.065 |
| `delete-multicast-address-range` | [PASSED] | 0.085 |

### 📄 Operational Logs
#### [PASSED] `add-multicast-address-range` ([0.08s])

**Payload snapshot:**
```json
{
  "ip-address-first": "224.0.1.10",
  "ip-address-last": "224.0.1.30",
  "name": "QA_MULTICAST-ADDRESS-RANGE_2_600",
  "set-if-exists": true,
  "color": "forest green",
  "comments": "QA Automated Test Object",
  "details-level": "uid",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv6-address": "ff05::1:10"
}
```
**Full Response:**
```json
{
  "uid": "1e67edfe-a900-41db-926e-057175691b56",
  "name": "QA_MULTICAST-ADDRESS-RANGE_2_600",
  "type": "multicast-address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "224.0.1.10",
  "ipv6-address-first": "ff05::1:10",
  "ipv4-address-last": "224.0.1.30",
  "ipv6-address-last": "ff05::1:10",
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "forest green",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732736851,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732736851,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-multicast-address-range` ([0.08s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_2_600",
  "comments": "QA updated exhaustive variant 2",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "1e67edfe-a900-41db-926e-057175691b56",
  "name": "QA_MULTICAST-ADDRESS-RANGE_2_600",
  "type": "multicast-address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "224.0.1.10",
  "ipv6-address-first": "ff05::1:10",
  "ipv4-address-last": "224.0.1.30",
  "ipv6-address-last": "ff05::1:10",
  "groups": [],
  "comments": "QA updated exhaustive variant 2",
  "color": "orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732736929,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732736851,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-multicast-address-range` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_2_600"
}
```
**Full Response:**
```json
{
  "uid": "1e67edfe-a900-41db-926e-057175691b56",
  "name": "QA_MULTICAST-ADDRESS-RANGE_2_600",
  "type": "multicast-address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "224.0.1.10",
  "ipv6-address-first": "ff05::1:10",
  "ipv4-address-last": "224.0.1.30",
  "ipv6-address-last": "ff05::1:10",
  "groups": [],
  "comments": "QA updated exhaustive variant 2",
  "color": "orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732736929,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732736851,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-multicast-address-range` ([0.08s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_2_600"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

<details>
<summary><b>[PASSED] Variant 3 — `ipv4-address-first`, `ipv4-address-last` (Total: 0.37s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-multicast-address-range` | [PASSED] | 0.139 |
| `set-multicast-address-range` | [PASSED] | 0.081 |
| `show-multicast-address-range` | [PASSED] | 0.066 |
| `delete-multicast-address-range` | [PASSED] | 0.082 |

### 📄 Operational Logs
#### [PASSED] `add-multicast-address-range` ([0.14s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_3_634",
  "set-if-exists": true,
  "color": "forest green",
  "comments": "QA Automated Test Object",
  "details-level": "uid",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv4-address-first": "224.0.1.10",
  "ipv4-address-last": "224.0.1.30"
}
```
**Full Response:**
```json
{
  "uid": "4cd63c24-801f-437d-a422-48b84a27fd41",
  "name": "QA_MULTICAST-ADDRESS-RANGE_3_634",
  "type": "multicast-address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "224.0.1.10",
  "ipv4-address-last": "224.0.1.30",
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "forest green",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732737221,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732737221,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-multicast-address-range` ([0.08s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_3_634",
  "comments": "QA updated exhaustive variant 3",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "4cd63c24-801f-437d-a422-48b84a27fd41",
  "name": "QA_MULTICAST-ADDRESS-RANGE_3_634",
  "type": "multicast-address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "224.0.1.10",
  "ipv4-address-last": "224.0.1.30",
  "groups": [],
  "comments": "QA updated exhaustive variant 3",
  "color": "orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732737299,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732737221,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-multicast-address-range` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_3_634"
}
```
**Full Response:**
```json
{
  "uid": "4cd63c24-801f-437d-a422-48b84a27fd41",
  "name": "QA_MULTICAST-ADDRESS-RANGE_3_634",
  "type": "multicast-address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "224.0.1.10",
  "ipv4-address-last": "224.0.1.30",
  "groups": [],
  "comments": "QA updated exhaustive variant 3",
  "color": "orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732737299,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732737221,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-multicast-address-range` ([0.08s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_3_634"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

<details>
<summary><b>[PASSED] Variant 4 — `ip-address`, `ipv6-address-first`, `ipv6-address-last` (Total: 0.33s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-multicast-address-range` | [PASSED] | 0.086 |
| `set-multicast-address-range` | [PASSED] | 0.082 |
| `show-multicast-address-range` | [PASSED] | 0.072 |
| `delete-multicast-address-range` | [PASSED] | 0.094 |

### 📄 Operational Logs
#### [PASSED] `add-multicast-address-range` ([0.09s])

**Payload snapshot:**
```json
{
  "ip-address": "224.0.1.20",
  "name": "QA_MULTICAST-ADDRESS-RANGE_4_436",
  "set-if-exists": true,
  "color": "forest green",
  "comments": "QA Automated Test Object",
  "details-level": "uid",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv6-address-first": "ff05::1:1",
  "ipv6-address-last": "ff05::1:30"
}
```
**Full Response:**
```json
{
  "uid": "b518b2de-e90c-4d16-a01f-053d578abd7e",
  "name": "QA_MULTICAST-ADDRESS-RANGE_4_436",
  "type": "multicast-address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "224.0.1.20",
  "ipv6-address-first": "ff05::1:1",
  "ipv4-address-last": "224.0.1.20",
  "ipv6-address-last": "ff05::1:30",
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "forest green",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732737532,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732737532,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-multicast-address-range` ([0.08s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_4_436",
  "comments": "QA updated exhaustive variant 4",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "b518b2de-e90c-4d16-a01f-053d578abd7e",
  "name": "QA_MULTICAST-ADDRESS-RANGE_4_436",
  "type": "multicast-address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "224.0.1.20",
  "ipv6-address-first": "ff05::1:1",
  "ipv4-address-last": "224.0.1.20",
  "ipv6-address-last": "ff05::1:30",
  "groups": [],
  "comments": "QA updated exhaustive variant 4",
  "color": "orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732737616,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732737532,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-multicast-address-range` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_4_436"
}
```
**Full Response:**
```json
{
  "uid": "b518b2de-e90c-4d16-a01f-053d578abd7e",
  "name": "QA_MULTICAST-ADDRESS-RANGE_4_436",
  "type": "multicast-address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "224.0.1.20",
  "ipv6-address-first": "ff05::1:1",
  "ipv4-address-last": "224.0.1.20",
  "ipv6-address-last": "ff05::1:30",
  "groups": [],
  "comments": "QA updated exhaustive variant 4",
  "color": "orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732737616,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732737532,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-multicast-address-range` ([0.09s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_4_436"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

<details>
<summary><b>[PASSED] Variant 5 — `ipv4-address-first`, `ipv4-address-last` (Total: 0.41s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-multicast-address-range` | [PASSED] | 0.148 |
| `set-multicast-address-range` | [PASSED] | 0.084 |
| `show-multicast-address-range` | [PASSED] | 0.074 |
| `delete-multicast-address-range` | [PASSED] | 0.105 |

### 📄 Operational Logs
#### [PASSED] `add-multicast-address-range` ([0.15s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_5_460",
  "set-if-exists": true,
  "color": "forest green",
  "comments": "QA Automated Test Object",
  "details-level": "uid",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv4-address-last": "224.0.1.30",
  "ipv4-address-first": "224.0.1.10"
}
```
**Full Response:**
```json
{
  "uid": "0f27fde3-7ff2-4651-a1bc-fbf25b238ddf",
  "name": "QA_MULTICAST-ADDRESS-RANGE_5_460",
  "type": "multicast-address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "224.0.1.10",
  "ipv4-address-last": "224.0.1.30",
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "forest green",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732737931,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732737931,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-multicast-address-range` ([0.08s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_5_460",
  "comments": "QA updated exhaustive variant 5",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "0f27fde3-7ff2-4651-a1bc-fbf25b238ddf",
  "name": "QA_MULTICAST-ADDRESS-RANGE_5_460",
  "type": "multicast-address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "224.0.1.10",
  "ipv4-address-last": "224.0.1.30",
  "groups": [],
  "comments": "QA updated exhaustive variant 5",
  "color": "orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732738008,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732737931,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-multicast-address-range` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_5_460"
}
```
**Full Response:**
```json
{
  "uid": "0f27fde3-7ff2-4651-a1bc-fbf25b238ddf",
  "name": "QA_MULTICAST-ADDRESS-RANGE_5_460",
  "type": "multicast-address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "224.0.1.10",
  "ipv4-address-last": "224.0.1.30",
  "groups": [],
  "comments": "QA updated exhaustive variant 5",
  "color": "orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732738008,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732737931,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-multicast-address-range` ([0.10s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_5_460"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

<details>
<summary><b>[PASSED] Variant 6 — `ip-address`, `ipv6-address-first`, `ipv6-address-last` (Total: 0.39s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-multicast-address-range` | [PASSED] | 0.082 |
| `set-multicast-address-range` | [PASSED] | 0.083 |
| `show-multicast-address-range` | [PASSED] | 0.072 |
| `delete-multicast-address-range` | [PASSED] | 0.149 |

### 📄 Operational Logs
#### [PASSED] `add-multicast-address-range` ([0.08s])

**Payload snapshot:**
```json
{
  "ip-address": "224.0.1.20",
  "name": "QA_MULTICAST-ADDRESS-RANGE_6_299",
  "set-if-exists": true,
  "color": "forest green",
  "comments": "QA Automated Test Object",
  "details-level": "uid",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv6-address-last": "ff05::1:30",
  "ipv6-address-first": "ff05::1:1"
}
```
**Full Response:**
```json
{
  "uid": "919338a9-0ea1-4d42-becc-050f71f569c8",
  "name": "QA_MULTICAST-ADDRESS-RANGE_6_299",
  "type": "multicast-address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "224.0.1.20",
  "ipv6-address-first": "ff05::1:1",
  "ipv4-address-last": "224.0.1.20",
  "ipv6-address-last": "ff05::1:30",
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "forest green",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732738279,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732738279,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-multicast-address-range` ([0.08s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_6_299",
  "comments": "QA updated exhaustive variant 6",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "919338a9-0ea1-4d42-becc-050f71f569c8",
  "name": "QA_MULTICAST-ADDRESS-RANGE_6_299",
  "type": "multicast-address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "224.0.1.20",
  "ipv6-address-first": "ff05::1:1",
  "ipv4-address-last": "224.0.1.20",
  "ipv6-address-last": "ff05::1:30",
  "groups": [],
  "comments": "QA updated exhaustive variant 6",
  "color": "orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732738359,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732738279,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-multicast-address-range` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_6_299"
}
```
**Full Response:**
```json
{
  "uid": "919338a9-0ea1-4d42-becc-050f71f569c8",
  "name": "QA_MULTICAST-ADDRESS-RANGE_6_299",
  "type": "multicast-address-range",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address-first": "224.0.1.20",
  "ipv6-address-first": "ff05::1:1",
  "ipv4-address-last": "224.0.1.20",
  "ipv6-address-last": "ff05::1:30",
  "groups": [],
  "comments": "QA updated exhaustive variant 6",
  "color": "orange",
  "icon": "Objects/ip",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732738359,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732738279,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-multicast-address-range` ([0.15s])

**Payload snapshot:**
```json
{
  "name": "QA_MULTICAST-ADDRESS-RANGE_6_299"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

---
## group-with-exclusion

<details>
<summary><b>[PASSED] Variant 0 (Total: 0.49s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-group-with-exclusion` | [PASSED] | 0.165 |
| `set-group-with-exclusion` | [PASSED] | 0.092 |
| `show-group-with-exclusion` | [PASSED] | 0.097 |
| `delete-group-with-exclusion` | [PASSED] | 0.132 |

### 📄 Operational Logs
#### [PASSED] `add-group-with-exclusion` ([0.16s])

**Payload snapshot:**
```json
{
  "name": "QA_GROUP-WITH-EXCLUSION_0_387",
  "except": "QA_HELPER_EXCEPT_5153",
  "include": "QA_HELPER_INCLUDE_8207",
  "color": "forest green",
  "comments": "QA Automated Test Object",
  "details-level": "uid",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true
}
```
**Full Response:**
```json
{
  "uid": "565b178c-0152-4e1f-a9d2-2c0a4bcee6c3",
  "name": "QA_GROUP-WITH-EXCLUSION_0_387",
  "type": "group-with-exclusion",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "include": "4c5b5480-9ace-4374-8292-4d716d2b1568",
  "except": "f5495720-21b4-4398-93b5-b53241dca942",
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "forest green",
  "icon": "General/group",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732738859,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732738859,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-group-with-exclusion` ([0.09s])

**Payload snapshot:**
```json
{
  "name": "QA_GROUP-WITH-EXCLUSION_0_387",
  "comments": "QA updated exhaustive variant 0",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "565b178c-0152-4e1f-a9d2-2c0a4bcee6c3",
  "name": "QA_GROUP-WITH-EXCLUSION_0_387",
  "type": "group-with-exclusion",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "include": {
    "uid": "4c5b5480-9ace-4374-8292-4d716d2b1568",
    "name": "QA_HELPER_INCLUDE_8207",
    "type": "group",
    "domain": {
      "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
      "name": "SMC User",
      "domain-type": "domain"
    },
    "icon": "General/group",
    "color": "black"
  },
  "except": {
    "uid": "f5495720-21b4-4398-93b5-b53241dca942",
    "name": "QA_HELPER_EXCEPT_5153",
    "type": "group",
    "domain": {
      "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
      "name": "SMC User",
      "domain-type": "domain"
    },
    "icon": "General/group",
    "color": "black"
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "General/group",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732738993,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732738859,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-group-with-exclusion` ([0.10s])

**Payload snapshot:**
```json
{
  "name": "QA_GROUP-WITH-EXCLUSION_0_387"
}
```
**Full Response:**
```json
{
  "uid": "565b178c-0152-4e1f-a9d2-2c0a4bcee6c3",
  "name": "QA_GROUP-WITH-EXCLUSION_0_387",
  "type": "group-with-exclusion",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "include": {
    "uid": "4c5b5480-9ace-4374-8292-4d716d2b1568",
    "name": "QA_HELPER_INCLUDE_8207",
    "type": "group",
    "domain": {
      "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
      "name": "SMC User",
      "domain-type": "domain"
    },
    "members": [],
    "groups": [],
    "comments": "",
    "color": "black",
    "icon": "General/group",
    "tags": [],
    "meta-info": {
      "lock": "locked by current session",
      "validation-state": "ok",
      "last-modify-time": {
        "posix": 1770732738665,
        "iso-8601": "2026-02-10T09:12-0500"
      },
      "last-modifier": "admin",
      "creation-time": {
        "posix": 1770732738665,
        "iso-8601": "2026-02-10T09:12-0500"
      },
      "creator": "admin"
    },
    "read-only": false,
    "available-actions": {
      "edit": "true",
      "delete": "true",
      "clone": "true"
    }
  },
  "except": {
    "uid": "f5495720-21b4-4398-93b5-b53241dca942",
    "name": "QA_HELPER_EXCEPT_5153",
    "type": "group",
    "domain": {
      "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
      "name": "SMC User",
      "domain-type": "domain"
    },
    "members": [],
    "groups": [],
    "comments": "",
    "color": "black",
    "icon": "General/group",
    "tags": [],
    "meta-info": {
      "lock": "locked by current session",
      "validation-state": "ok",
      "last-modify-time": {
        "posix": 1770732738746,
        "iso-8601": "2026-02-10T09:12-0500"
      },
      "last-modifier": "admin",
      "creation-time": {
        "posix": 1770732738746,
        "iso-8601": "2026-02-10T09:12-0500"
      },
      "creator": "admin"
    },
    "read-only": false,
    "available-actions": {
      "edit": "true",
      "delete": "true",
      "clone": "true"
    }
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "General/group",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732738993,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732738859,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-group-with-exclusion` ([0.13s])

**Payload snapshot:**
```json
{
  "name": "QA_GROUP-WITH-EXCLUSION_0_387"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

---
## dns-domain

<details>
<summary><b>[PASSED] Variant 0 (Total: 0.29s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-dns-domain` | [PASSED] | 0.067 |
| `set-dns-domain` | [PASSED] | 0.075 |
| `show-dns-domain` | [PASSED] | 0.062 |
| `delete-dns-domain` | [PASSED] | 0.084 |

### 📄 Operational Logs
#### [PASSED] `add-dns-domain` ([0.07s])

**Payload snapshot:**
```json
{
  "name": ".qa-domain-0-630.example.com",
  "is-sub-domain": false,
  "color": "dark green",
  "comments": "QA Automated Test Object",
  "details-level": "standard",
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true
}
```
**Full Response:**
```json
{
  "uid": "8ef650bd-05ce-4586-bbe2-7930c45579b8",
  "name": ".qa-domain-0-630.example.com",
  "type": "dns-domain",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "is-sub-domain": false,
  "comments": "QA Automated Test Object",
  "color": "dark green",
  "icon": "Objects/domain",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732739500,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732739500,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-dns-domain` ([0.07s])

**Payload snapshot:**
```json
{
  "name": ".qa-domain-0-630.example.com",
  "comments": "QA updated exhaustive variant 0",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "8ef650bd-05ce-4586-bbe2-7930c45579b8",
  "name": ".qa-domain-0-630.example.com",
  "type": "dns-domain",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "is-sub-domain": false,
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "Objects/domain",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732739568,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732739500,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-dns-domain` ([0.06s])

**Payload snapshot:**
```json
{
  "name": ".qa-domain-0-630.example.com"
}
```
**Full Response:**
```json
{
  "uid": "8ef650bd-05ce-4586-bbe2-7930c45579b8",
  "name": ".qa-domain-0-630.example.com",
  "type": "dns-domain",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "is-sub-domain": false,
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "Objects/domain",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732739568,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732739500,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-dns-domain` ([0.08s])

**Payload snapshot:**
```json
{
  "name": ".qa-domain-0-630.example.com"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

---
## wildcard

<details>
<summary><b>[PASSED] Variant 0 (Total: 0.31s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-wildcard` | [PASSED] | 0.075 |
| `set-wildcard` | [PASSED] | 0.078 |
| `show-wildcard` | [PASSED] | 0.067 |
| `delete-wildcard` | [PASSED] | 0.091 |

### 📄 Operational Logs
#### [PASSED] `add-wildcard` ([0.07s])

**Payload snapshot:**
```json
{
  "ipv4-address": "10.100.1.11",
  "ipv4-mask-wildcard": "10.100.1.67",
  "ipv6-address": "2001:db8:85a3::19a6",
  "ipv6-mask-wildcard": "2001:db8:85a3::1b0e",
  "name": "QA_WILDCARD_0_646",
  "color": "firebrick",
  "comments": "QA Automated Test Object",
  "details-level": "standard",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true
}
```
**Full Response:**
```json
{
  "uid": "1fe109fd-b5b8-49cc-9946-27d7002308f2",
  "name": "QA_WILDCARD_0_646",
  "type": "wildcard",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address": "10.100.1.11",
  "ipv6-address": "2001:db8:85a3::19a6",
  "ipv4-mask-wildcard": "10.100.1.67",
  "ipv6-mask-wildcard": "2001:db8:85a3::1b0e",
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "firebrick",
  "icon": "NetworkObjects/WildcardObject",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732739788,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732739788,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-wildcard` ([0.08s])

**Payload snapshot:**
```json
{
  "name": "QA_WILDCARD_0_646",
  "comments": "QA updated exhaustive variant 0",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "1fe109fd-b5b8-49cc-9946-27d7002308f2",
  "name": "QA_WILDCARD_0_646",
  "type": "wildcard",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address": "10.100.1.11",
  "ipv6-address": "2001:db8:85a3::19a6",
  "ipv4-mask-wildcard": "10.100.1.67",
  "ipv6-mask-wildcard": "2001:db8:85a3::1b0e",
  "groups": [],
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "NetworkObjects/WildcardObject",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732739868,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732739788,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-wildcard` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_WILDCARD_0_646"
}
```
**Full Response:**
```json
{
  "uid": "1fe109fd-b5b8-49cc-9946-27d7002308f2",
  "name": "QA_WILDCARD_0_646",
  "type": "wildcard",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address": "10.100.1.11",
  "ipv6-address": "2001:db8:85a3::19a6",
  "ipv4-mask-wildcard": "10.100.1.67",
  "ipv6-mask-wildcard": "2001:db8:85a3::1b0e",
  "groups": [],
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "NetworkObjects/WildcardObject",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732739868,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732739788,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-wildcard` ([0.09s])

**Payload snapshot:**
```json
{
  "name": "QA_WILDCARD_0_646"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

---
## security-zone

<details>
<summary><b>[PASSED] Variant 0 (Total: 0.28s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-security-zone` | [PASSED] | 0.071 |
| `set-security-zone` | [PASSED] | 0.070 |
| `show-security-zone` | [PASSED] | 0.059 |
| `delete-security-zone` | [PASSED] | 0.078 |

### 📄 Operational Logs
#### [PASSED] `add-security-zone` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_SECURITY-ZONE_0_348",
  "color": "cyan",
  "comments": "QA Automated Test Object",
  "details-level": "standard",
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true
}
```
**Full Response:**
```json
{
  "uid": "8ecf7a66-e2e3-4950-820d-d49b642b0fff",
  "name": "QA_SECURITY-ZONE_0_348",
  "type": "security-zone",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "comments": "QA Automated Test Object",
  "color": "cyan",
  "icon": "NetworkObjects/zone",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732740104,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732740104,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-security-zone` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_SECURITY-ZONE_0_348",
  "comments": "QA updated exhaustive variant 0",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "8ecf7a66-e2e3-4950-820d-d49b642b0fff",
  "name": "QA_SECURITY-ZONE_0_348",
  "type": "security-zone",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "NetworkObjects/zone",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732740176,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732740104,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-security-zone` ([0.06s])

**Payload snapshot:**
```json
{
  "name": "QA_SECURITY-ZONE_0_348"
}
```
**Full Response:**
```json
{
  "uid": "8ecf7a66-e2e3-4950-820d-d49b642b0fff",
  "name": "QA_SECURITY-ZONE_0_348",
  "type": "security-zone",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "NetworkObjects/zone",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732740176,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732740104,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-security-zone` ([0.08s])

**Payload snapshot:**
```json
{
  "name": "QA_SECURITY-ZONE_0_348"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

---
## dynamic-object

<details>
<summary><b>[PASSED] Variant 0 (Total: 0.30s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-dynamic-object` | [PASSED] | 0.072 |
| `set-dynamic-object` | [PASSED] | 0.084 |
| `show-dynamic-object` | [PASSED] | 0.061 |
| `delete-dynamic-object` | [PASSED] | 0.085 |

### 📄 Operational Logs
#### [PASSED] `add-dynamic-object` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_DYNAMIC-OBJECT_0_235",
  "color": "firebrick",
  "comments": "QA Automated Test Object",
  "details-level": "full",
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true
}
```
**Full Response:**
```json
{
  "uid": "859bac55-edcb-44f4-9e97-539c48403ee5",
  "name": "QA_DYNAMIC-OBJECT_0_235",
  "type": "dynamic-object",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "comments": "QA Automated Test Object",
  "color": "firebrick",
  "icon": "NetworkObjects/dynamicObject",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732740387,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732740387,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-dynamic-object` ([0.08s])

**Payload snapshot:**
```json
{
  "name": "QA_DYNAMIC-OBJECT_0_235",
  "comments": "QA updated exhaustive variant 0",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "859bac55-edcb-44f4-9e97-539c48403ee5",
  "name": "QA_DYNAMIC-OBJECT_0_235",
  "type": "dynamic-object",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "NetworkObjects/dynamicObject",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732740469,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732740387,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-dynamic-object` ([0.06s])

**Payload snapshot:**
```json
{
  "name": "QA_DYNAMIC-OBJECT_0_235"
}
```
**Full Response:**
```json
{
  "uid": "859bac55-edcb-44f4-9e97-539c48403ee5",
  "name": "QA_DYNAMIC-OBJECT_0_235",
  "type": "dynamic-object",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "NetworkObjects/dynamicObject",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732740469,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732740387,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-dynamic-object` ([0.09s])

**Payload snapshot:**
```json
{
  "name": "QA_DYNAMIC-OBJECT_0_235"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

---
## tag

<details>
<summary><b>[PASSED] Variant 0 (Total: 0.30s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-tag` | [PASSED] | 0.067 |
| `set-tag` | [PASSED] | 0.082 |
| `show-tag` | [PASSED] | 0.060 |
| `delete-tag` | [PASSED] | 0.088 |

### 📄 Operational Logs
#### [PASSED] `add-tag` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_TAG_0_482",
  "color": "coral",
  "comments": "QA Automated Test Object",
  "details-level": "standard",
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true
}
```
**Full Response:**
```json
{
  "uid": "8ebaaa6b-448b-437d-8609-024acf9e9c45",
  "name": "QA_TAG_0_482",
  "type": "tag",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "comments": "QA Automated Test Object",
  "color": "coral",
  "icon": "Tags/Tag",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732740685,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732740685,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-tag` ([0.08s])

**Payload snapshot:**
```json
{
  "name": "QA_TAG_0_482",
  "comments": "QA updated exhaustive variant 0",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "8ebaaa6b-448b-437d-8609-024acf9e9c45",
  "name": "QA_TAG_0_482",
  "type": "tag",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "Tags/Tag",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732740762,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732740685,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-tag` ([0.06s])

**Payload snapshot:**
```json
{
  "name": "QA_TAG_0_482"
}
```
**Full Response:**
```json
{
  "uid": "8ebaaa6b-448b-437d-8609-024acf9e9c45",
  "name": "QA_TAG_0_482",
  "type": "tag",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "Tags/Tag",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732740762,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732740685,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-tag` ([0.09s])

**Payload snapshot:**
```json
{
  "name": "QA_TAG_0_482"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

---
## time

<details>
<summary><b>[PASSED] Variant 0 (Total: 0.82s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-time` | [PASSED] | 0.079 |
| `set-time` | [PASSED] | 0.594 |
| `show-time` | [PASSED] | 0.069 |
| `delete-time` | [PASSED] | 0.075 |

### 📄 Operational Logs
#### [PASSED] `add-time` ([0.08s])

**Payload snapshot:**
```json
{
  "name": "QA_T0_393",
  "color": "olive",
  "comments": "QA Automated Test Object",
  "ignore-warnings": true,
  "ignore-errors": true,
  "start-now": true,
  "end-never": true
}
```
**Full Response:**
```json
{
  "uid": "8caf639e-45c3-4ac4-b7b3-c97eb7159e0b",
  "name": "QA_T0_393",
  "type": "time",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "start-now": true,
  "start": {
    "time": "00:00",
    "iso-8601": "1970-01-01T00:00:00",
    "date": "01-Jan-1970",
    "posix": 0
  },
  "end-never": true,
  "end": {
    "time": "00:00",
    "iso-8601": "1970-01-01T00:00:00",
    "date": "01-Jan-1970",
    "posix": 0
  },
  "recurrence": {
    "pattern": "Daily",
    "month": "Any"
  },
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "olive",
  "icon": "Objects/time",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732740993,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732740993,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-time` ([0.59s])

**Payload snapshot:**
```json
{
  "name": "QA_T0_393",
  "comments": "QA updated exhaustive variant 0",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "8caf639e-45c3-4ac4-b7b3-c97eb7159e0b",
  "name": "QA_T0_393",
  "type": "time",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "start-now": true,
  "start": {
    "time": "00:00",
    "iso-8601": "1970-01-01T00:00:00",
    "date": "01-Jan-1970",
    "posix": 0
  },
  "end-never": true,
  "end": {
    "time": "00:00",
    "iso-8601": "1970-01-01T00:00:00",
    "date": "01-Jan-1970",
    "posix": 0
  },
  "recurrence": {
    "pattern": "Daily",
    "weekdays": [],
    "month": "Any",
    "days": []
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "Objects/time",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732741581,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732740993,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-time` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_T0_393"
}
```
**Full Response:**
```json
{
  "uid": "8caf639e-45c3-4ac4-b7b3-c97eb7159e0b",
  "name": "QA_T0_393",
  "type": "time",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "start-now": true,
  "start": {
    "time": "00:00",
    "iso-8601": "1970-01-01T00:00:00",
    "date": "01-Jan-1970",
    "posix": 0
  },
  "end-never": true,
  "end": {
    "time": "00:00",
    "iso-8601": "1970-01-01T00:00:00",
    "date": "01-Jan-1970",
    "posix": 0
  },
  "recurrence": {
    "pattern": "Daily",
    "weekdays": [],
    "month": "Any",
    "days": []
  },
  "groups": [],
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "Objects/time",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732741581,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732740993,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-time` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_T0_393"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

---
## time-group

<details>
<summary><b>[PASSED] Variant 0 (Total: 1.07s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-time-group` | [PASSED] | 0.249 |
| `set-time-group` | [PASSED] | 0.650 |
| `show-time-group` | [PASSED] | 0.082 |
| `delete-time-group` | [PASSED] | 0.088 |

### 📄 Operational Logs
#### [PASSED] `add-time-group` ([0.25s])

**Payload snapshot:**
```json
{
  "members": [
    "QA_HT665"
  ],
  "name": "QA_T0_760",
  "color": "purple",
  "comments": "QA Automated Test Object",
  "ignore-warnings": true,
  "ignore-errors": true
}
```
**Full Response:**
```json
{
  "uid": "04dc9dfe-f70f-4194-bd99-b04c9660549a",
  "name": "QA_T0_760",
  "type": "time-group",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "members": [
    {
      "uid": "b980d3f6-3438-4378-a525-dac50583fbae",
      "name": "QA_HT665",
      "type": "time",
      "domain": {
        "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
        "name": "SMC User",
        "domain-type": "domain"
      },
      "icon": "Objects/time",
      "color": "black"
    }
  ],
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "purple",
  "icon": "General/group",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732741961,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732741961,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-time-group` ([0.65s])

**Payload snapshot:**
```json
{
  "name": "QA_T0_760",
  "comments": "QA updated exhaustive variant 0",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "04dc9dfe-f70f-4194-bd99-b04c9660549a",
  "name": "QA_T0_760",
  "type": "time-group",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "members": [
    {
      "uid": "b980d3f6-3438-4378-a525-dac50583fbae",
      "name": "QA_HT665",
      "type": "time",
      "domain": {
        "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
        "name": "SMC User",
        "domain-type": "domain"
      },
      "icon": "Objects/time",
      "color": "black"
    }
  ],
  "groups": [],
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "General/group",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732742708,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732741961,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-time-group` ([0.08s])

**Payload snapshot:**
```json
{
  "name": "QA_T0_760"
}
```
**Full Response:**
```json
{
  "uid": "04dc9dfe-f70f-4194-bd99-b04c9660549a",
  "name": "QA_T0_760",
  "type": "time-group",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "members": [
    {
      "uid": "b980d3f6-3438-4378-a525-dac50583fbae",
      "name": "QA_HT665",
      "type": "time",
      "domain": {
        "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
        "name": "SMC User",
        "domain-type": "domain"
      },
      "start-now": true,
      "start": {
        "time": "00:00",
        "iso-8601": "1970-01-01T00:00:00",
        "date": "01-Jan-1970",
        "posix": 0
      },
      "end-never": true,
      "end": {
        "time": "00:00",
        "iso-8601": "1970-01-01T00:00:00",
        "date": "01-Jan-1970",
        "posix": 0
      },
      "recurrence": {
        "pattern": "Daily",
        "weekdays": [],
        "month": "Any",
        "days": []
      },
      "groups": [
        "04dc9dfe-f70f-4194-bd99-b04c9660549a"
      ],
      "comments": "",
      "color": "black",
      "icon": "Objects/time",
      "tags": [],
      "meta-info": {
        "lock": "locked by current session",
        "validation-state": "ok",
        "last-modify-time": {
          "posix": 1770732741809,
          "iso-8601": "2026-02-10T09:12-0500"
        },
        "last-modifier": "admin",
        "creation-time": {
          "posix": 1770732741809,
          "iso-8601": "2026-02-10T09:12-0500"
        },
        "creator": "admin"
      },
      "read-only": false,
      "available-actions": {
        "edit": "true",
        "delete": "true",
        "clone": "true"
      }
    }
  ],
  "groups": [],
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "General/group",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732742708,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732741961,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-time-group` ([0.09s])

**Payload snapshot:**
```json
{
  "name": "QA_T0_760"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

---
## gsn-handover-group

<details>
<summary><b>[PASSED] Variant 0 (Total: 0.32s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-gsn-handover-group` | [PASSED] | 0.087 |
| `set-gsn-handover-group` | [PASSED] | 0.083 |
| `show-gsn-handover-group` | [PASSED] | 0.063 |
| `delete-gsn-handover-group` | [PASSED] | 0.090 |

### 📄 Operational Logs
#### [PASSED] `add-gsn-handover-group` ([0.09s])

**Payload snapshot:**
```json
{
  "enforce-gtp": false,
  "gtp-rate": 58,
  "members": [],
  "name": "QA_GSN-HANDOVER-GROUP_0_730",
  "set-if-exists": true,
  "color": "khaki",
  "comments": "QA Automated Test Object",
  "details-level": "standard",
  "groups": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true
}
```
**Full Response:**
```json
{
  "uid": "372b68a7-32a6-496f-be7b-1c744e6bc0fe",
  "name": "QA_GSN-HANDOVER-GROUP_0_730",
  "type": "gsn-handover-group",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "members": [],
  "enforce-gtp": false,
  "gtp-rate": 58,
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "khaki",
  "icon": "General/group",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732743051,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732743051,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `set-gsn-handover-group` ([0.08s])

**Payload snapshot:**
```json
{
  "name": "QA_GSN-HANDOVER-GROUP_0_730",
  "comments": "QA updated exhaustive variant 0",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "372b68a7-32a6-496f-be7b-1c744e6bc0fe",
  "name": "QA_GSN-HANDOVER-GROUP_0_730",
  "type": "gsn-handover-group",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "members": [],
  "enforce-gtp": false,
  "gtp-rate": 58,
  "groups": [],
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "General/group",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732743129,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732743051,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {}
}
```

#### [PASSED] `show-gsn-handover-group` ([0.06s])

**Payload snapshot:**
```json
{
  "name": "QA_GSN-HANDOVER-GROUP_0_730"
}
```
**Full Response:**
```json
{
  "uid": "372b68a7-32a6-496f-be7b-1c744e6bc0fe",
  "name": "QA_GSN-HANDOVER-GROUP_0_730",
  "type": "gsn-handover-group",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "members": [],
  "enforce-gtp": false,
  "gtp-rate": 58,
  "groups": [],
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "General/group",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732743129,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732743051,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "true"
  }
}
```

#### [PASSED] `delete-gsn-handover-group` ([0.09s])

**Payload snapshot:**
```json
{
  "name": "QA_GSN-HANDOVER-GROUP_0_730"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

---
## network-feed

<details>
<summary><b>[PASSED] Variant 0 (Total: 0.32s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-network-feed` | [PASSED] | 0.075 |
| `set-network-feed` | [PASSED] | 0.095 |
| `show-network-feed` | [PASSED] | 0.059 |
| `delete-network-feed` | [PASSED] | 0.088 |

### 📄 Operational Logs
#### [PASSED] `add-network-feed` ([0.08s])

**Payload snapshot:**
```json
{
  "feed-format": "Flat List",
  "feed-type": "IP Address",
  "password": "QA_7867",
  "username": "QA_2485",
  "name": "QA_NETWORK-FEED_0_107",
  "feed-url": "https://secureupdates.checkpoint.com/IP-list/TOR.txt",
  "color": "dark green",
  "comments": "QA Automated Test Object",
  "details-level": "uid",
  "domains-to-process": [],
  "tags": [],
  "ignore-warnings": true,
  "ignore-errors": true
}
```
**Full Response:**
```json
{
  "uid": "b807fb77-589f-45df-a81a-4d1398e88d41",
  "name": "QA_NETWORK-FEED_0_107",
  "type": "network-feed",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "update-interval": 60,
  "data-column": 1,
  "feed-format": "Flat List",
  "feed-type": "IP Address",
  "custom-headers": [],
  "feed-url": "https://secureupdates.checkpoint.com/IP-list/TOR.txt",
  "username": "QA_2485",
  "ignore-lines-that-start-with": "#",
  "fields-delimiter": "\n",
  "use-gateway-proxy": true,
  "comments": "QA Automated Test Object",
  "color": "dark green",
  "icon": "NetworkObjects/NetworkFeed",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732743365,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732743365,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {
    "clone": "not_supported"
  }
}
```

#### [PASSED] `set-network-feed` ([0.09s])

**Payload snapshot:**
```json
{
  "name": "QA_NETWORK-FEED_0_107",
  "comments": "QA updated exhaustive variant 0",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "b807fb77-589f-45df-a81a-4d1398e88d41",
  "name": "QA_NETWORK-FEED_0_107",
  "type": "network-feed",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "update-interval": 60,
  "data-column": 1,
  "feed-format": "Flat List",
  "feed-type": "IP Address",
  "custom-headers": [],
  "feed-url": "https://secureupdates.checkpoint.com/IP-list/TOR.txt",
  "username": "QA_2485",
  "ignore-lines-that-start-with": "#",
  "fields-delimiter": "\n",
  "use-gateway-proxy": true,
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "NetworkObjects/NetworkFeed",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732743453,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732743365,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {
    "clone": "not_supported"
  }
}
```

#### [PASSED] `show-network-feed` ([0.06s])

**Payload snapshot:**
```json
{
  "name": "QA_NETWORK-FEED_0_107"
}
```
**Full Response:**
```json
{
  "uid": "b807fb77-589f-45df-a81a-4d1398e88d41",
  "name": "QA_NETWORK-FEED_0_107",
  "type": "network-feed",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "update-interval": 60,
  "data-column": 1,
  "feed-format": "Flat List",
  "feed-type": "IP Address",
  "custom-headers": [],
  "feed-url": "https://secureupdates.checkpoint.com/IP-list/TOR.txt",
  "username": "QA_2485",
  "ignore-lines-that-start-with": "#",
  "fields-delimiter": "\n",
  "use-gateway-proxy": true,
  "comments": "QA updated exhaustive variant 0",
  "color": "orange",
  "icon": "NetworkObjects/NetworkFeed",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732743453,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732743365,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "not_supported"
  }
}
```

#### [PASSED] `delete-network-feed` ([0.09s])

**Payload snapshot:**
```json
{
  "name": "QA_NETWORK-FEED_0_107"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

---
## simple-gateway

<details>
<summary><b>[PASSED] Variant 1 (Total: 3.47s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-simple-gateway` | [PASSED] | 2.512 |
| `set-simple-gateway` | [PASSED] | 0.377 |
| `show-simple-gateway` | [PASSED] | 0.121 |
| `delete-simple-gateway` | [PASSED] | 0.460 |

### 📄 Operational Logs
#### [PASSED] `add-simple-gateway` ([2.51s])

**Payload snapshot:**
```json
{
  "name": "QA_SIMPLE-GATEWAY_1_719",
  "color": "coral",
  "comments": "QA Automated Test Object",
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv4-address": "10.100.99.125",
  "version": "R81.10"
}
```
**Full Response:**
```json
{
  "uid": "8b0ae7bc-329b-4d6f-858e-ab24a0fdb12e",
  "name": "QA_SIMPLE-GATEWAY_1_719",
  "type": "simple-gateway",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "platform": "open server",
  "interfaces": [],
  "https-inspection": {
    "deployment-mode": "full",
    "bypass-on-failure": {
      "profile-value": true,
      "override-profile": false
    },
    "site-categorization-allow-mode": {
      "profile-value": "hold",
      "override-profile": false
    },
    "deny-untrusted-server-cert": {
      "profile-value": false,
      "override-profile": false
    },
    "deny-revoked-server-cert": {
      "profile-value": true,
      "override-profile": false
    },
    "deny-expired-server-cert": {
      "profile-value": false,
      "override-profile": false
    }
  },
  "ipv4-address": "10.100.99.125",
  "dynamic-ip": false,
  "version": "R81.10",
  "os-name": "Gaia",
  "hardware": "Open server",
  "sic-name": "",
  "sic-state": "uninitialized",
  "network-policy-management": false,
  "log-server": false,
  "firewall": true,
  "firewall-settings": {
    "auto-maximum-limit-for-concurrent-connections": true,
    "maximum-limit-for-concurrent-connections": 25000,
    "auto-calculate-connections-hash-table-size-and-memory-pool": true,
    "connections-hash-size": 131072,
    "memory-pool-size": 6,
    "maximum-memory-pool-size": 30
  },
  "vpn": false,
  "externally-managed": false,
  "policy-server": false,
  "mobile-access": false,
  "legacy-url-filtering": false,
  "monitoring": false,
  "anti-spam-and-email-security": false,
  "application-control": false,
  "url-filtering": false,
  "threat-prevention-mode": "custom",
  "ips": false,
  "threat-emulation": false,
  "threat-extraction": false,
  "data-loss-prevention": false,
  "qos": false,
  "anti-bot": false,
  "anti-virus": false,
  "content-awareness": false,
  "zero-phishing": false,
  "save-logs-locally": false,
  "send-alerts-to-server": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "send-logs-to-server": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "send-logs-to-backup-server": [],
  "logs-settings": {
    "rotate-log-by-file-size": false,
    "rotate-log-file-size-threshold": 1000,
    "rotate-log-on-schedule": false,
    "alert-when-free-disk-space-below-metrics": "mbytes",
    "alert-when-free-disk-space-below": true,
    "alert-when-free-disk-space-below-threshold": 3000,
    "alert-when-free-disk-space-below-type": "popup alert",
    "delete-when-free-disk-space-below-metrics": "mbytes",
    "delete-when-free-disk-space-below": true,
    "delete-when-free-disk-space-below-threshold": 5000,
    "before-delete-keep-logs-from-the-last-days": false,
    "before-delete-keep-logs-from-the-last-days-threshold": 3664,
    "before-delete-run-script": false,
    "before-delete-run-script-command": "",
    "stop-logging-when-free-disk-space-below-metrics": "mbytes",
    "stop-logging-when-free-disk-space-below": true,
    "stop-logging-when-free-disk-space-below-threshold": 100,
    "reject-connections-when-free-disk-space-below-threshold": false,
    "reserve-for-packet-capture-metrics": "mbytes",
    "reserve-for-packet-capture-threshold": 500,
    "delete-index-files-when-index-size-above-metrics": "mbytes",
    "delete-index-files-when-index-size-above": false,
    "delete-index-files-when-index-size-above-threshold": 100000,
    "delete-index-files-older-than-days": false,
    "delete-index-files-older-than-days-threshold": 14,
    "forward-logs-to-log-server": false,
    "perform-log-rotate-before-log-forwarding": false,
    "update-account-log-every": 3600,
    "detect-new-citrix-ica-application-names": false,
    "turn-on-qos-logging": true,
    "distribute-logs-between-all-active-servers": false
  },
  "identity-awareness": false,
  "platform-portal-settings": {
    "enabled": true,
    "portal-web-settings": {
      "main-url": "https://10.100.99.125/",
      "ip-address": "10.100.99.125"
    },
    "accessibility": {
      "allow-access-from": "RULE_BASE"
    }
  },
  "proxy-settings": {
    "use-custom-proxy": false
  },
  "nat-hide-internal-interfaces": false,
  "nat-settings": {
    "auto-rule": false
  },
  "fetch-policy": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "advanced-settings": {
    "sam": {
      "forward-to-other-sam-servers": false,
      "use-early-versions": {
        "enabled": false
      },
      "purge-sam-file": {
        "enabled": false,
        "purge-when-size-reaches-to": 100
      }
    },
    "connection-persistence": "rematch-connections"
  },
  "hit-count": true,
  "enable-https-inspection": false,
  "application-control-and-url-filtering-settings": {
    "global-settings-mode": "use_global_settings"
  },
  "zero-phishing-settings": {
    "gateway-fqdn-mode": "automatic"
  },
  "ips-update-policy": "gateway automatic update",
  "auto-topology-use-custom-recalculation-time": false,
  "auto-topology-custom-recalculation-time": 10,
  "rtm-traffic-report": false,
  "rtm-counters-report": true,
  "rtm-traffic-report-per-connection": false,
  "communication-with-servers-behind-nat": {
    "override-profile": false
  },
  "interfaces-topology-settings": "per interface",
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "coral",
  "icon": "NetworkObjects/gateway",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732750815,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732750815,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {
    "clone": "not_supported"
  }
}
```

#### [PASSED] `set-simple-gateway` ([0.38s])

**Payload snapshot:**
```json
{
  "name": "QA_SIMPLE-GATEWAY_1_719",
  "comments": "QA updated exhaustive variant 1",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "8b0ae7bc-329b-4d6f-858e-ab24a0fdb12e",
  "name": "QA_SIMPLE-GATEWAY_1_719",
  "type": "simple-gateway",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "platform": "open server",
  "interfaces": [],
  "https-inspection": {
    "outbound-certificate": {
      "profile-value": "",
      "override-profile": false
    },
    "deployment-mode": "full",
    "bypass-on-failure": {
      "profile-value": true,
      "override-profile": false
    },
    "site-categorization-allow-mode": {
      "profile-value": "hold",
      "override-profile": false
    },
    "deny-untrusted-server-cert": {
      "profile-value": false,
      "override-profile": false
    },
    "deny-revoked-server-cert": {
      "profile-value": true,
      "override-profile": false
    },
    "deny-expired-server-cert": {
      "profile-value": false,
      "override-profile": false
    }
  },
  "ipv4-address": "10.100.99.125",
  "dynamic-ip": false,
  "version": "R81.10",
  "os-name": "Gaia",
  "hardware": "Open server",
  "sic-name": "",
  "sic-state": "uninitialized",
  "network-policy-management": false,
  "log-server": false,
  "firewall": true,
  "firewall-settings": {
    "auto-maximum-limit-for-concurrent-connections": true,
    "maximum-limit-for-concurrent-connections": 25000,
    "auto-calculate-connections-hash-table-size-and-memory-pool": true,
    "connections-hash-size": 131072,
    "memory-pool-size": 6,
    "maximum-memory-pool-size": 30
  },
  "vpn": false,
  "externally-managed": false,
  "policy-server": false,
  "mobile-access": false,
  "legacy-url-filtering": false,
  "monitoring": false,
  "anti-spam-and-email-security": false,
  "application-control": false,
  "url-filtering": false,
  "threat-prevention-mode": "custom",
  "ips": false,
  "threat-emulation": false,
  "threat-extraction": false,
  "data-loss-prevention": false,
  "qos": false,
  "anti-bot": false,
  "anti-virus": false,
  "content-awareness": false,
  "zero-phishing": false,
  "save-logs-locally": false,
  "send-alerts-to-server": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "send-logs-to-server": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "send-logs-to-backup-server": [],
  "logs-settings": {
    "rotate-log-by-file-size": false,
    "rotate-log-file-size-threshold": 1000,
    "rotate-log-on-schedule": false,
    "alert-when-free-disk-space-below-metrics": "mbytes",
    "alert-when-free-disk-space-below": true,
    "alert-when-free-disk-space-below-threshold": 3000,
    "alert-when-free-disk-space-below-type": "popup alert",
    "delete-when-free-disk-space-below-metrics": "mbytes",
    "delete-when-free-disk-space-below": true,
    "delete-when-free-disk-space-below-threshold": 5000,
    "before-delete-keep-logs-from-the-last-days": false,
    "before-delete-keep-logs-from-the-last-days-threshold": 3664,
    "before-delete-run-script": false,
    "before-delete-run-script-command": "",
    "stop-logging-when-free-disk-space-below-metrics": "mbytes",
    "stop-logging-when-free-disk-space-below": true,
    "stop-logging-when-free-disk-space-below-threshold": 100,
    "reject-connections-when-free-disk-space-below-threshold": false,
    "reserve-for-packet-capture-metrics": "mbytes",
    "reserve-for-packet-capture-threshold": 500,
    "delete-index-files-when-index-size-above-metrics": "mbytes",
    "delete-index-files-when-index-size-above": false,
    "delete-index-files-when-index-size-above-threshold": 100000,
    "delete-index-files-older-than-days": false,
    "delete-index-files-older-than-days-threshold": 14,
    "forward-logs-to-log-server": false,
    "perform-log-rotate-before-log-forwarding": false,
    "update-account-log-every": 3600,
    "detect-new-citrix-ica-application-names": false,
    "turn-on-qos-logging": true,
    "distribute-logs-between-all-active-servers": false
  },
  "identity-awareness": false,
  "platform-portal-settings": {
    "enabled": true,
    "portal-web-settings": {
      "main-url": "https://10.100.99.125/",
      "ip-address": "10.100.99.125",
      "aliases": []
    },
    "accessibility": {
      "allow-access-from": "RULE_BASE"
    }
  },
  "proxy-settings": {
    "use-custom-proxy": false
  },
  "nat-hide-internal-interfaces": false,
  "nat-settings": {
    "auto-rule": false
  },
  "fetch-policy": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "advanced-settings": {
    "sam": {
      "forward-to-other-sam-servers": false,
      "use-early-versions": {
        "enabled": false
      },
      "purge-sam-file": {
        "enabled": false,
        "purge-when-size-reaches-to": 100
      }
    },
    "connection-persistence": "rematch-connections"
  },
  "hit-count": true,
  "enable-https-inspection": false,
  "application-control-and-url-filtering-settings": {
    "global-settings-mode": "use_global_settings"
  },
  "zero-phishing-settings": {
    "gateway-fqdn-mode": "automatic"
  },
  "ips-update-policy": "gateway automatic update",
  "auto-topology-use-custom-recalculation-time": false,
  "auto-topology-custom-recalculation-time": 10,
  "rtm-traffic-report": false,
  "rtm-counters-report": true,
  "rtm-traffic-report-per-connection": false,
  "communication-with-servers-behind-nat": {
    "override-profile": false
  },
  "interfaces-topology-settings": "per interface",
  "groups": [],
  "comments": "QA updated exhaustive variant 1",
  "color": "orange",
  "icon": "NetworkObjects/gateway",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732751326,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732750815,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {
    "clone": "not_supported"
  }
}
```

#### [PASSED] `show-simple-gateway` ([0.12s])

**Payload snapshot:**
```json
{
  "name": "QA_SIMPLE-GATEWAY_1_719"
}
```
**Full Response:**
```json
{
  "uid": "8b0ae7bc-329b-4d6f-858e-ab24a0fdb12e",
  "name": "QA_SIMPLE-GATEWAY_1_719",
  "type": "simple-gateway",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "platform": "open server",
  "interfaces": [],
  "https-inspection": {
    "outbound-certificate": {
      "profile-value": "",
      "override-profile": false
    },
    "deployment-mode": "full",
    "bypass-on-failure": {
      "profile-value": true,
      "override-profile": false
    },
    "site-categorization-allow-mode": {
      "profile-value": "hold",
      "override-profile": false
    },
    "deny-untrusted-server-cert": {
      "profile-value": false,
      "override-profile": false
    },
    "deny-revoked-server-cert": {
      "profile-value": true,
      "override-profile": false
    },
    "deny-expired-server-cert": {
      "profile-value": false,
      "override-profile": false
    }
  },
  "ipv4-address": "10.100.99.125",
  "dynamic-ip": false,
  "version": "R81.10",
  "os-name": "Gaia",
  "hardware": "Open server",
  "sic-name": "",
  "sic-state": "uninitialized",
  "network-policy-management": false,
  "log-server": false,
  "firewall": true,
  "firewall-settings": {
    "auto-maximum-limit-for-concurrent-connections": true,
    "maximum-limit-for-concurrent-connections": 25000,
    "auto-calculate-connections-hash-table-size-and-memory-pool": true,
    "connections-hash-size": 131072,
    "memory-pool-size": 6,
    "maximum-memory-pool-size": 30
  },
  "vpn": false,
  "externally-managed": false,
  "policy-server": false,
  "mobile-access": false,
  "legacy-url-filtering": false,
  "monitoring": false,
  "anti-spam-and-email-security": false,
  "application-control": false,
  "url-filtering": false,
  "threat-prevention-mode": "custom",
  "ips": false,
  "threat-emulation": false,
  "threat-extraction": false,
  "data-loss-prevention": false,
  "qos": false,
  "anti-bot": false,
  "anti-virus": false,
  "content-awareness": false,
  "zero-phishing": false,
  "save-logs-locally": false,
  "send-alerts-to-server": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "send-logs-to-server": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "send-logs-to-backup-server": [],
  "logs-settings": {
    "rotate-log-by-file-size": false,
    "rotate-log-file-size-threshold": 1000,
    "rotate-log-on-schedule": false,
    "alert-when-free-disk-space-below-metrics": "mbytes",
    "alert-when-free-disk-space-below": true,
    "alert-when-free-disk-space-below-threshold": 3000,
    "alert-when-free-disk-space-below-type": "popup alert",
    "delete-when-free-disk-space-below-metrics": "mbytes",
    "delete-when-free-disk-space-below": true,
    "delete-when-free-disk-space-below-threshold": 5000,
    "before-delete-keep-logs-from-the-last-days": false,
    "before-delete-keep-logs-from-the-last-days-threshold": 3664,
    "before-delete-run-script": false,
    "before-delete-run-script-command": "",
    "stop-logging-when-free-disk-space-below-metrics": "mbytes",
    "stop-logging-when-free-disk-space-below": true,
    "stop-logging-when-free-disk-space-below-threshold": 100,
    "reject-connections-when-free-disk-space-below-threshold": false,
    "reserve-for-packet-capture-metrics": "mbytes",
    "reserve-for-packet-capture-threshold": 500,
    "delete-index-files-when-index-size-above-metrics": "mbytes",
    "delete-index-files-when-index-size-above": false,
    "delete-index-files-when-index-size-above-threshold": 100000,
    "delete-index-files-older-than-days": false,
    "delete-index-files-older-than-days-threshold": 14,
    "forward-logs-to-log-server": false,
    "perform-log-rotate-before-log-forwarding": false,
    "update-account-log-every": 3600,
    "detect-new-citrix-ica-application-names": false,
    "turn-on-qos-logging": true,
    "distribute-logs-between-all-active-servers": false
  },
  "identity-awareness": false,
  "platform-portal-settings": {
    "enabled": true,
    "portal-web-settings": {
      "main-url": "https://10.100.99.125/",
      "ip-address": "10.100.99.125",
      "aliases": []
    },
    "accessibility": {
      "allow-access-from": "RULE_BASE"
    }
  },
  "proxy-settings": {
    "use-custom-proxy": false
  },
  "nat-hide-internal-interfaces": false,
  "nat-settings": {
    "auto-rule": false
  },
  "fetch-policy": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "hit-count": true,
  "enable-https-inspection": false,
  "application-control-and-url-filtering-settings": {
    "global-settings-mode": "use_global_settings"
  },
  "zero-phishing-settings": {
    "gateway-fqdn-mode": "automatic"
  },
  "ips-update-policy": "gateway automatic update",
  "auto-topology-use-custom-recalculation-time": false,
  "auto-topology-custom-recalculation-time": 10,
  "rtm-traffic-report": false,
  "rtm-counters-report": true,
  "rtm-traffic-report-per-connection": false,
  "communication-with-servers-behind-nat": {
    "override-profile": false
  },
  "interfaces-topology-settings": "per interface",
  "groups": [],
  "comments": "QA updated exhaustive variant 1",
  "color": "orange",
  "icon": "NetworkObjects/gateway",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732751326,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732750815,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "not_supported"
  }
}
```

#### [PASSED] `delete-simple-gateway` ([0.46s])

**Payload snapshot:**
```json
{
  "name": "QA_SIMPLE-GATEWAY_1_719"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

<details>
<summary><b>[PASSED] Variant 2 (Total: 14.54s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-simple-gateway` | [PASSED] | 3.959 |
| `set-simple-gateway` | [PASSED] | 10.017 |
| `show-simple-gateway` | [PASSED] | 0.124 |
| `delete-simple-gateway` | [PASSED] | 0.441 |

### 📄 Operational Logs
#### [PASSED] `add-simple-gateway` ([3.96s])

**Payload snapshot:**
```json
{
  "name": "QA_SIMPLE-GATEWAY_2_778",
  "color": "coral",
  "comments": "QA Automated Test Object",
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv4-address": "10.100.99.175",
  "version": "R81.10"
}
```
**Full Response:**
```json
{
  "uid": "bda9cd60-12da-4987-a428-1fc4507d8117",
  "name": "QA_SIMPLE-GATEWAY_2_778",
  "type": "simple-gateway",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "platform": "open server",
  "interfaces": [],
  "https-inspection": {
    "deployment-mode": "full",
    "bypass-on-failure": {
      "profile-value": true,
      "override-profile": false
    },
    "site-categorization-allow-mode": {
      "profile-value": "hold",
      "override-profile": false
    },
    "deny-untrusted-server-cert": {
      "profile-value": false,
      "override-profile": false
    },
    "deny-revoked-server-cert": {
      "profile-value": true,
      "override-profile": false
    },
    "deny-expired-server-cert": {
      "profile-value": false,
      "override-profile": false
    }
  },
  "ipv4-address": "10.100.99.175",
  "dynamic-ip": false,
  "version": "R81.10",
  "os-name": "Gaia",
  "hardware": "Open server",
  "sic-name": "",
  "sic-state": "uninitialized",
  "network-policy-management": false,
  "log-server": false,
  "firewall": true,
  "firewall-settings": {
    "auto-maximum-limit-for-concurrent-connections": true,
    "maximum-limit-for-concurrent-connections": 25000,
    "auto-calculate-connections-hash-table-size-and-memory-pool": true,
    "connections-hash-size": 131072,
    "memory-pool-size": 6,
    "maximum-memory-pool-size": 30
  },
  "vpn": false,
  "externally-managed": false,
  "policy-server": false,
  "mobile-access": false,
  "legacy-url-filtering": false,
  "monitoring": false,
  "anti-spam-and-email-security": false,
  "application-control": false,
  "url-filtering": false,
  "threat-prevention-mode": "custom",
  "ips": false,
  "threat-emulation": false,
  "threat-extraction": false,
  "data-loss-prevention": false,
  "qos": false,
  "anti-bot": false,
  "anti-virus": false,
  "content-awareness": false,
  "zero-phishing": false,
  "save-logs-locally": false,
  "send-alerts-to-server": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "send-logs-to-server": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "send-logs-to-backup-server": [],
  "logs-settings": {
    "rotate-log-by-file-size": false,
    "rotate-log-file-size-threshold": 1000,
    "rotate-log-on-schedule": false,
    "alert-when-free-disk-space-below-metrics": "mbytes",
    "alert-when-free-disk-space-below": true,
    "alert-when-free-disk-space-below-threshold": 3000,
    "alert-when-free-disk-space-below-type": "popup alert",
    "delete-when-free-disk-space-below-metrics": "mbytes",
    "delete-when-free-disk-space-below": true,
    "delete-when-free-disk-space-below-threshold": 5000,
    "before-delete-keep-logs-from-the-last-days": false,
    "before-delete-keep-logs-from-the-last-days-threshold": 3664,
    "before-delete-run-script": false,
    "before-delete-run-script-command": "",
    "stop-logging-when-free-disk-space-below-metrics": "mbytes",
    "stop-logging-when-free-disk-space-below": true,
    "stop-logging-when-free-disk-space-below-threshold": 100,
    "reject-connections-when-free-disk-space-below-threshold": false,
    "reserve-for-packet-capture-metrics": "mbytes",
    "reserve-for-packet-capture-threshold": 500,
    "delete-index-files-when-index-size-above-metrics": "mbytes",
    "delete-index-files-when-index-size-above": false,
    "delete-index-files-when-index-size-above-threshold": 100000,
    "delete-index-files-older-than-days": false,
    "delete-index-files-older-than-days-threshold": 14,
    "forward-logs-to-log-server": false,
    "perform-log-rotate-before-log-forwarding": false,
    "update-account-log-every": 3600,
    "detect-new-citrix-ica-application-names": false,
    "turn-on-qos-logging": true,
    "distribute-logs-between-all-active-servers": false
  },
  "identity-awareness": false,
  "platform-portal-settings": {
    "enabled": true,
    "portal-web-settings": {
      "main-url": "https://10.100.99.175/",
      "ip-address": "10.100.99.175"
    },
    "accessibility": {
      "allow-access-from": "RULE_BASE"
    }
  },
  "proxy-settings": {
    "use-custom-proxy": false
  },
  "nat-hide-internal-interfaces": false,
  "nat-settings": {
    "auto-rule": false
  },
  "fetch-policy": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "advanced-settings": {
    "sam": {
      "forward-to-other-sam-servers": false,
      "use-early-versions": {
        "enabled": false
      },
      "purge-sam-file": {
        "enabled": false,
        "purge-when-size-reaches-to": 100
      }
    },
    "connection-persistence": "rematch-connections"
  },
  "hit-count": true,
  "enable-https-inspection": false,
  "application-control-and-url-filtering-settings": {
    "global-settings-mode": "use_global_settings"
  },
  "zero-phishing-settings": {
    "gateway-fqdn-mode": "automatic"
  },
  "ips-update-policy": "gateway automatic update",
  "auto-topology-use-custom-recalculation-time": false,
  "auto-topology-custom-recalculation-time": 10,
  "rtm-traffic-report": false,
  "rtm-counters-report": true,
  "rtm-traffic-report-per-connection": false,
  "communication-with-servers-behind-nat": {
    "override-profile": false
  },
  "interfaces-topology-settings": "per interface",
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "coral",
  "icon": "NetworkObjects/gateway",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732755428,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732755428,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {
    "clone": "not_supported"
  }
}
```

#### [PASSED] `set-simple-gateway` ([10.02s])

**Payload snapshot:**
```json
{
  "name": "QA_SIMPLE-GATEWAY_2_778",
  "comments": "QA updated exhaustive variant 2",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "bda9cd60-12da-4987-a428-1fc4507d8117",
  "name": "QA_SIMPLE-GATEWAY_2_778",
  "type": "simple-gateway",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "platform": "open server",
  "interfaces": [],
  "https-inspection": {
    "outbound-certificate": {
      "profile-value": "",
      "override-profile": false
    },
    "deployment-mode": "full",
    "bypass-on-failure": {
      "profile-value": true,
      "override-profile": false
    },
    "site-categorization-allow-mode": {
      "profile-value": "hold",
      "override-profile": false
    },
    "deny-untrusted-server-cert": {
      "profile-value": false,
      "override-profile": false
    },
    "deny-revoked-server-cert": {
      "profile-value": true,
      "override-profile": false
    },
    "deny-expired-server-cert": {
      "profile-value": false,
      "override-profile": false
    }
  },
  "ipv4-address": "10.100.99.175",
  "dynamic-ip": false,
  "version": "R81.10",
  "os-name": "Gaia",
  "hardware": "Open server",
  "sic-name": "",
  "sic-state": "uninitialized",
  "network-policy-management": false,
  "log-server": false,
  "firewall": true,
  "firewall-settings": {
    "auto-maximum-limit-for-concurrent-connections": true,
    "maximum-limit-for-concurrent-connections": 25000,
    "auto-calculate-connections-hash-table-size-and-memory-pool": true,
    "connections-hash-size": 131072,
    "memory-pool-size": 6,
    "maximum-memory-pool-size": 30
  },
  "vpn": false,
  "externally-managed": false,
  "policy-server": false,
  "mobile-access": false,
  "legacy-url-filtering": false,
  "monitoring": false,
  "anti-spam-and-email-security": false,
  "application-control": false,
  "url-filtering": false,
  "threat-prevention-mode": "custom",
  "ips": false,
  "threat-emulation": false,
  "threat-extraction": false,
  "data-loss-prevention": false,
  "qos": false,
  "anti-bot": false,
  "anti-virus": false,
  "content-awareness": false,
  "zero-phishing": false,
  "save-logs-locally": false,
  "send-alerts-to-server": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "send-logs-to-server": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "send-logs-to-backup-server": [],
  "logs-settings": {
    "rotate-log-by-file-size": false,
    "rotate-log-file-size-threshold": 1000,
    "rotate-log-on-schedule": false,
    "alert-when-free-disk-space-below-metrics": "mbytes",
    "alert-when-free-disk-space-below": true,
    "alert-when-free-disk-space-below-threshold": 3000,
    "alert-when-free-disk-space-below-type": "popup alert",
    "delete-when-free-disk-space-below-metrics": "mbytes",
    "delete-when-free-disk-space-below": true,
    "delete-when-free-disk-space-below-threshold": 5000,
    "before-delete-keep-logs-from-the-last-days": false,
    "before-delete-keep-logs-from-the-last-days-threshold": 3664,
    "before-delete-run-script": false,
    "before-delete-run-script-command": "",
    "stop-logging-when-free-disk-space-below-metrics": "mbytes",
    "stop-logging-when-free-disk-space-below": true,
    "stop-logging-when-free-disk-space-below-threshold": 100,
    "reject-connections-when-free-disk-space-below-threshold": false,
    "reserve-for-packet-capture-metrics": "mbytes",
    "reserve-for-packet-capture-threshold": 500,
    "delete-index-files-when-index-size-above-metrics": "mbytes",
    "delete-index-files-when-index-size-above": false,
    "delete-index-files-when-index-size-above-threshold": 100000,
    "delete-index-files-older-than-days": false,
    "delete-index-files-older-than-days-threshold": 14,
    "forward-logs-to-log-server": false,
    "perform-log-rotate-before-log-forwarding": false,
    "update-account-log-every": 3600,
    "detect-new-citrix-ica-application-names": false,
    "turn-on-qos-logging": true,
    "distribute-logs-between-all-active-servers": false
  },
  "identity-awareness": false,
  "platform-portal-settings": {
    "enabled": true,
    "portal-web-settings": {
      "main-url": "https://10.100.99.175/",
      "ip-address": "10.100.99.175",
      "aliases": []
    },
    "accessibility": {
      "allow-access-from": "RULE_BASE"
    }
  },
  "proxy-settings": {
    "use-custom-proxy": false
  },
  "nat-hide-internal-interfaces": false,
  "nat-settings": {
    "auto-rule": false
  },
  "fetch-policy": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "advanced-settings": {
    "sam": {
      "forward-to-other-sam-servers": false,
      "use-early-versions": {
        "enabled": false
      },
      "purge-sam-file": {
        "enabled": false,
        "purge-when-size-reaches-to": 100
      }
    },
    "connection-persistence": "rematch-connections"
  },
  "hit-count": true,
  "enable-https-inspection": false,
  "application-control-and-url-filtering-settings": {
    "global-settings-mode": "use_global_settings"
  },
  "zero-phishing-settings": {
    "gateway-fqdn-mode": "automatic"
  },
  "ips-update-policy": "gateway automatic update",
  "auto-topology-use-custom-recalculation-time": false,
  "auto-topology-custom-recalculation-time": 10,
  "rtm-traffic-report": false,
  "rtm-counters-report": true,
  "rtm-traffic-report-per-connection": false,
  "communication-with-servers-behind-nat": {
    "override-profile": false
  },
  "interfaces-topology-settings": "per interface",
  "groups": [],
  "comments": "QA updated exhaustive variant 2",
  "color": "orange",
  "icon": "NetworkObjects/gateway",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732765963,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732755428,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {
    "clone": "not_supported"
  }
}
```

#### [PASSED] `show-simple-gateway` ([0.12s])

**Payload snapshot:**
```json
{
  "name": "QA_SIMPLE-GATEWAY_2_778"
}
```
**Full Response:**
```json
{
  "uid": "bda9cd60-12da-4987-a428-1fc4507d8117",
  "name": "QA_SIMPLE-GATEWAY_2_778",
  "type": "simple-gateway",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "platform": "open server",
  "interfaces": [],
  "https-inspection": {
    "outbound-certificate": {
      "profile-value": "",
      "override-profile": false
    },
    "deployment-mode": "full",
    "bypass-on-failure": {
      "profile-value": true,
      "override-profile": false
    },
    "site-categorization-allow-mode": {
      "profile-value": "hold",
      "override-profile": false
    },
    "deny-untrusted-server-cert": {
      "profile-value": false,
      "override-profile": false
    },
    "deny-revoked-server-cert": {
      "profile-value": true,
      "override-profile": false
    },
    "deny-expired-server-cert": {
      "profile-value": false,
      "override-profile": false
    }
  },
  "ipv4-address": "10.100.99.175",
  "dynamic-ip": false,
  "version": "R81.10",
  "os-name": "Gaia",
  "hardware": "Open server",
  "sic-name": "",
  "sic-state": "uninitialized",
  "network-policy-management": false,
  "log-server": false,
  "firewall": true,
  "firewall-settings": {
    "auto-maximum-limit-for-concurrent-connections": true,
    "maximum-limit-for-concurrent-connections": 25000,
    "auto-calculate-connections-hash-table-size-and-memory-pool": true,
    "connections-hash-size": 131072,
    "memory-pool-size": 6,
    "maximum-memory-pool-size": 30
  },
  "vpn": false,
  "externally-managed": false,
  "policy-server": false,
  "mobile-access": false,
  "legacy-url-filtering": false,
  "monitoring": false,
  "anti-spam-and-email-security": false,
  "application-control": false,
  "url-filtering": false,
  "threat-prevention-mode": "custom",
  "ips": false,
  "threat-emulation": false,
  "threat-extraction": false,
  "data-loss-prevention": false,
  "qos": false,
  "anti-bot": false,
  "anti-virus": false,
  "content-awareness": false,
  "zero-phishing": false,
  "save-logs-locally": false,
  "send-alerts-to-server": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "send-logs-to-server": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "send-logs-to-backup-server": [],
  "logs-settings": {
    "rotate-log-by-file-size": false,
    "rotate-log-file-size-threshold": 1000,
    "rotate-log-on-schedule": false,
    "alert-when-free-disk-space-below-metrics": "mbytes",
    "alert-when-free-disk-space-below": true,
    "alert-when-free-disk-space-below-threshold": 3000,
    "alert-when-free-disk-space-below-type": "popup alert",
    "delete-when-free-disk-space-below-metrics": "mbytes",
    "delete-when-free-disk-space-below": true,
    "delete-when-free-disk-space-below-threshold": 5000,
    "before-delete-keep-logs-from-the-last-days": false,
    "before-delete-keep-logs-from-the-last-days-threshold": 3664,
    "before-delete-run-script": false,
    "before-delete-run-script-command": "",
    "stop-logging-when-free-disk-space-below-metrics": "mbytes",
    "stop-logging-when-free-disk-space-below": true,
    "stop-logging-when-free-disk-space-below-threshold": 100,
    "reject-connections-when-free-disk-space-below-threshold": false,
    "reserve-for-packet-capture-metrics": "mbytes",
    "reserve-for-packet-capture-threshold": 500,
    "delete-index-files-when-index-size-above-metrics": "mbytes",
    "delete-index-files-when-index-size-above": false,
    "delete-index-files-when-index-size-above-threshold": 100000,
    "delete-index-files-older-than-days": false,
    "delete-index-files-older-than-days-threshold": 14,
    "forward-logs-to-log-server": false,
    "perform-log-rotate-before-log-forwarding": false,
    "update-account-log-every": 3600,
    "detect-new-citrix-ica-application-names": false,
    "turn-on-qos-logging": true,
    "distribute-logs-between-all-active-servers": false
  },
  "identity-awareness": false,
  "platform-portal-settings": {
    "enabled": true,
    "portal-web-settings": {
      "main-url": "https://10.100.99.175/",
      "ip-address": "10.100.99.175",
      "aliases": []
    },
    "accessibility": {
      "allow-access-from": "RULE_BASE"
    }
  },
  "proxy-settings": {
    "use-custom-proxy": false
  },
  "nat-hide-internal-interfaces": false,
  "nat-settings": {
    "auto-rule": false
  },
  "fetch-policy": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "hit-count": true,
  "enable-https-inspection": false,
  "application-control-and-url-filtering-settings": {
    "global-settings-mode": "use_global_settings"
  },
  "zero-phishing-settings": {
    "gateway-fqdn-mode": "automatic"
  },
  "ips-update-policy": "gateway automatic update",
  "auto-topology-use-custom-recalculation-time": false,
  "auto-topology-custom-recalculation-time": 10,
  "rtm-traffic-report": false,
  "rtm-counters-report": true,
  "rtm-traffic-report-per-connection": false,
  "communication-with-servers-behind-nat": {
    "override-profile": false
  },
  "interfaces-topology-settings": "per interface",
  "groups": [],
  "comments": "QA updated exhaustive variant 2",
  "color": "orange",
  "icon": "NetworkObjects/gateway",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732765963,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732755428,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "not_supported"
  }
}
```

#### [PASSED] `delete-simple-gateway` ([0.44s])

**Payload snapshot:**
```json
{
  "name": "QA_SIMPLE-GATEWAY_2_778"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

<details>
<summary><b>[PASSED] Variant 3 (Total: 3.79s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-simple-gateway` | [PASSED] | 2.808 |
| `set-simple-gateway` | [PASSED] | 0.424 |
| `show-simple-gateway` | [PASSED] | 0.109 |
| `delete-simple-gateway` | [PASSED] | 0.452 |

### 📄 Operational Logs
#### [PASSED] `add-simple-gateway` ([2.81s])

**Payload snapshot:**
```json
{
  "name": "QA_SIMPLE-GATEWAY_3_398",
  "color": "coral",
  "comments": "QA Automated Test Object",
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv4-address": "10.100.99.136",
  "version": "R81.10"
}
```
**Full Response:**
```json
{
  "uid": "fda896ef-7909-466b-ba29-853a1e4f4bcc",
  "name": "QA_SIMPLE-GATEWAY_3_398",
  "type": "simple-gateway",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "platform": "open server",
  "interfaces": [],
  "https-inspection": {
    "deployment-mode": "full",
    "bypass-on-failure": {
      "profile-value": true,
      "override-profile": false
    },
    "site-categorization-allow-mode": {
      "profile-value": "hold",
      "override-profile": false
    },
    "deny-untrusted-server-cert": {
      "profile-value": false,
      "override-profile": false
    },
    "deny-revoked-server-cert": {
      "profile-value": true,
      "override-profile": false
    },
    "deny-expired-server-cert": {
      "profile-value": false,
      "override-profile": false
    }
  },
  "ipv4-address": "10.100.99.136",
  "dynamic-ip": false,
  "version": "R81.10",
  "os-name": "Gaia",
  "hardware": "Open server",
  "sic-name": "",
  "sic-state": "uninitialized",
  "network-policy-management": false,
  "log-server": false,
  "firewall": true,
  "firewall-settings": {
    "auto-maximum-limit-for-concurrent-connections": true,
    "maximum-limit-for-concurrent-connections": 25000,
    "auto-calculate-connections-hash-table-size-and-memory-pool": true,
    "connections-hash-size": 131072,
    "memory-pool-size": 6,
    "maximum-memory-pool-size": 30
  },
  "vpn": false,
  "externally-managed": false,
  "policy-server": false,
  "mobile-access": false,
  "legacy-url-filtering": false,
  "monitoring": false,
  "anti-spam-and-email-security": false,
  "application-control": false,
  "url-filtering": false,
  "threat-prevention-mode": "custom",
  "ips": false,
  "threat-emulation": false,
  "threat-extraction": false,
  "data-loss-prevention": false,
  "qos": false,
  "anti-bot": false,
  "anti-virus": false,
  "content-awareness": false,
  "zero-phishing": false,
  "save-logs-locally": false,
  "send-alerts-to-server": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "send-logs-to-server": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "send-logs-to-backup-server": [],
  "logs-settings": {
    "rotate-log-by-file-size": false,
    "rotate-log-file-size-threshold": 1000,
    "rotate-log-on-schedule": false,
    "alert-when-free-disk-space-below-metrics": "mbytes",
    "alert-when-free-disk-space-below": true,
    "alert-when-free-disk-space-below-threshold": 3000,
    "alert-when-free-disk-space-below-type": "popup alert",
    "delete-when-free-disk-space-below-metrics": "mbytes",
    "delete-when-free-disk-space-below": true,
    "delete-when-free-disk-space-below-threshold": 5000,
    "before-delete-keep-logs-from-the-last-days": false,
    "before-delete-keep-logs-from-the-last-days-threshold": 3664,
    "before-delete-run-script": false,
    "before-delete-run-script-command": "",
    "stop-logging-when-free-disk-space-below-metrics": "mbytes",
    "stop-logging-when-free-disk-space-below": true,
    "stop-logging-when-free-disk-space-below-threshold": 100,
    "reject-connections-when-free-disk-space-below-threshold": false,
    "reserve-for-packet-capture-metrics": "mbytes",
    "reserve-for-packet-capture-threshold": 500,
    "delete-index-files-when-index-size-above-metrics": "mbytes",
    "delete-index-files-when-index-size-above": false,
    "delete-index-files-when-index-size-above-threshold": 100000,
    "delete-index-files-older-than-days": false,
    "delete-index-files-older-than-days-threshold": 14,
    "forward-logs-to-log-server": false,
    "perform-log-rotate-before-log-forwarding": false,
    "update-account-log-every": 3600,
    "detect-new-citrix-ica-application-names": false,
    "turn-on-qos-logging": true,
    "distribute-logs-between-all-active-servers": false
  },
  "identity-awareness": false,
  "platform-portal-settings": {
    "enabled": true,
    "portal-web-settings": {
      "main-url": "https://10.100.99.136/",
      "ip-address": "10.100.99.136"
    },
    "accessibility": {
      "allow-access-from": "RULE_BASE"
    }
  },
  "proxy-settings": {
    "use-custom-proxy": false
  },
  "nat-hide-internal-interfaces": false,
  "nat-settings": {
    "auto-rule": false
  },
  "fetch-policy": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "advanced-settings": {
    "sam": {
      "forward-to-other-sam-servers": false,
      "use-early-versions": {
        "enabled": false
      },
      "purge-sam-file": {
        "enabled": false,
        "purge-when-size-reaches-to": 100
      }
    },
    "connection-persistence": "rematch-connections"
  },
  "hit-count": true,
  "enable-https-inspection": false,
  "application-control-and-url-filtering-settings": {
    "global-settings-mode": "use_global_settings"
  },
  "zero-phishing-settings": {
    "gateway-fqdn-mode": "automatic"
  },
  "ips-update-policy": "gateway automatic update",
  "auto-topology-use-custom-recalculation-time": false,
  "auto-topology-custom-recalculation-time": 10,
  "rtm-traffic-report": false,
  "rtm-counters-report": true,
  "rtm-traffic-report-per-connection": false,
  "communication-with-servers-behind-nat": {
    "override-profile": false
  },
  "interfaces-topology-settings": "per interface",
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "coral",
  "icon": "NetworkObjects/gateway",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732769109,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732769109,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {
    "clone": "not_supported"
  }
}
```

#### [PASSED] `set-simple-gateway` ([0.42s])

**Payload snapshot:**
```json
{
  "name": "QA_SIMPLE-GATEWAY_3_398",
  "comments": "QA updated exhaustive variant 3",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "fda896ef-7909-466b-ba29-853a1e4f4bcc",
  "name": "QA_SIMPLE-GATEWAY_3_398",
  "type": "simple-gateway",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "platform": "open server",
  "interfaces": [],
  "https-inspection": {
    "outbound-certificate": {
      "profile-value": "",
      "override-profile": false
    },
    "deployment-mode": "full",
    "bypass-on-failure": {
      "profile-value": true,
      "override-profile": false
    },
    "site-categorization-allow-mode": {
      "profile-value": "hold",
      "override-profile": false
    },
    "deny-untrusted-server-cert": {
      "profile-value": false,
      "override-profile": false
    },
    "deny-revoked-server-cert": {
      "profile-value": true,
      "override-profile": false
    },
    "deny-expired-server-cert": {
      "profile-value": false,
      "override-profile": false
    }
  },
  "ipv4-address": "10.100.99.136",
  "dynamic-ip": false,
  "version": "R81.10",
  "os-name": "Gaia",
  "hardware": "Open server",
  "sic-name": "",
  "sic-state": "uninitialized",
  "network-policy-management": false,
  "log-server": false,
  "firewall": true,
  "firewall-settings": {
    "auto-maximum-limit-for-concurrent-connections": true,
    "maximum-limit-for-concurrent-connections": 25000,
    "auto-calculate-connections-hash-table-size-and-memory-pool": true,
    "connections-hash-size": 131072,
    "memory-pool-size": 6,
    "maximum-memory-pool-size": 30
  },
  "vpn": false,
  "externally-managed": false,
  "policy-server": false,
  "mobile-access": false,
  "legacy-url-filtering": false,
  "monitoring": false,
  "anti-spam-and-email-security": false,
  "application-control": false,
  "url-filtering": false,
  "threat-prevention-mode": "custom",
  "ips": false,
  "threat-emulation": false,
  "threat-extraction": false,
  "data-loss-prevention": false,
  "qos": false,
  "anti-bot": false,
  "anti-virus": false,
  "content-awareness": false,
  "zero-phishing": false,
  "save-logs-locally": false,
  "send-alerts-to-server": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "send-logs-to-server": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "send-logs-to-backup-server": [],
  "logs-settings": {
    "rotate-log-by-file-size": false,
    "rotate-log-file-size-threshold": 1000,
    "rotate-log-on-schedule": false,
    "alert-when-free-disk-space-below-metrics": "mbytes",
    "alert-when-free-disk-space-below": true,
    "alert-when-free-disk-space-below-threshold": 3000,
    "alert-when-free-disk-space-below-type": "popup alert",
    "delete-when-free-disk-space-below-metrics": "mbytes",
    "delete-when-free-disk-space-below": true,
    "delete-when-free-disk-space-below-threshold": 5000,
    "before-delete-keep-logs-from-the-last-days": false,
    "before-delete-keep-logs-from-the-last-days-threshold": 3664,
    "before-delete-run-script": false,
    "before-delete-run-script-command": "",
    "stop-logging-when-free-disk-space-below-metrics": "mbytes",
    "stop-logging-when-free-disk-space-below": true,
    "stop-logging-when-free-disk-space-below-threshold": 100,
    "reject-connections-when-free-disk-space-below-threshold": false,
    "reserve-for-packet-capture-metrics": "mbytes",
    "reserve-for-packet-capture-threshold": 500,
    "delete-index-files-when-index-size-above-metrics": "mbytes",
    "delete-index-files-when-index-size-above": false,
    "delete-index-files-when-index-size-above-threshold": 100000,
    "delete-index-files-older-than-days": false,
    "delete-index-files-older-than-days-threshold": 14,
    "forward-logs-to-log-server": false,
    "perform-log-rotate-before-log-forwarding": false,
    "update-account-log-every": 3600,
    "detect-new-citrix-ica-application-names": false,
    "turn-on-qos-logging": true,
    "distribute-logs-between-all-active-servers": false
  },
  "identity-awareness": false,
  "platform-portal-settings": {
    "enabled": true,
    "portal-web-settings": {
      "main-url": "https://10.100.99.136/",
      "ip-address": "10.100.99.136",
      "aliases": []
    },
    "accessibility": {
      "allow-access-from": "RULE_BASE"
    }
  },
  "proxy-settings": {
    "use-custom-proxy": false
  },
  "nat-hide-internal-interfaces": false,
  "nat-settings": {
    "auto-rule": false
  },
  "fetch-policy": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "advanced-settings": {
    "sam": {
      "forward-to-other-sam-servers": false,
      "use-early-versions": {
        "enabled": false
      },
      "purge-sam-file": {
        "enabled": false,
        "purge-when-size-reaches-to": 100
      }
    },
    "connection-persistence": "rematch-connections"
  },
  "hit-count": true,
  "enable-https-inspection": false,
  "application-control-and-url-filtering-settings": {
    "global-settings-mode": "use_global_settings"
  },
  "zero-phishing-settings": {
    "gateway-fqdn-mode": "automatic"
  },
  "ips-update-policy": "gateway automatic update",
  "auto-topology-use-custom-recalculation-time": false,
  "auto-topology-custom-recalculation-time": 10,
  "rtm-traffic-report": false,
  "rtm-counters-report": true,
  "rtm-traffic-report-per-connection": false,
  "communication-with-servers-behind-nat": {
    "override-profile": false
  },
  "interfaces-topology-settings": "per interface",
  "groups": [],
  "comments": "QA updated exhaustive variant 3",
  "color": "orange",
  "icon": "NetworkObjects/gateway",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732769624,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732769109,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {
    "clone": "not_supported"
  }
}
```

#### [PASSED] `show-simple-gateway` ([0.11s])

**Payload snapshot:**
```json
{
  "name": "QA_SIMPLE-GATEWAY_3_398"
}
```
**Full Response:**
```json
{
  "uid": "fda896ef-7909-466b-ba29-853a1e4f4bcc",
  "name": "QA_SIMPLE-GATEWAY_3_398",
  "type": "simple-gateway",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "platform": "open server",
  "interfaces": [],
  "https-inspection": {
    "outbound-certificate": {
      "profile-value": "",
      "override-profile": false
    },
    "deployment-mode": "full",
    "bypass-on-failure": {
      "profile-value": true,
      "override-profile": false
    },
    "site-categorization-allow-mode": {
      "profile-value": "hold",
      "override-profile": false
    },
    "deny-untrusted-server-cert": {
      "profile-value": false,
      "override-profile": false
    },
    "deny-revoked-server-cert": {
      "profile-value": true,
      "override-profile": false
    },
    "deny-expired-server-cert": {
      "profile-value": false,
      "override-profile": false
    }
  },
  "ipv4-address": "10.100.99.136",
  "dynamic-ip": false,
  "version": "R81.10",
  "os-name": "Gaia",
  "hardware": "Open server",
  "sic-name": "",
  "sic-state": "uninitialized",
  "network-policy-management": false,
  "log-server": false,
  "firewall": true,
  "firewall-settings": {
    "auto-maximum-limit-for-concurrent-connections": true,
    "maximum-limit-for-concurrent-connections": 25000,
    "auto-calculate-connections-hash-table-size-and-memory-pool": true,
    "connections-hash-size": 131072,
    "memory-pool-size": 6,
    "maximum-memory-pool-size": 30
  },
  "vpn": false,
  "externally-managed": false,
  "policy-server": false,
  "mobile-access": false,
  "legacy-url-filtering": false,
  "monitoring": false,
  "anti-spam-and-email-security": false,
  "application-control": false,
  "url-filtering": false,
  "threat-prevention-mode": "custom",
  "ips": false,
  "threat-emulation": false,
  "threat-extraction": false,
  "data-loss-prevention": false,
  "qos": false,
  "anti-bot": false,
  "anti-virus": false,
  "content-awareness": false,
  "zero-phishing": false,
  "save-logs-locally": false,
  "send-alerts-to-server": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "send-logs-to-server": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "send-logs-to-backup-server": [],
  "logs-settings": {
    "rotate-log-by-file-size": false,
    "rotate-log-file-size-threshold": 1000,
    "rotate-log-on-schedule": false,
    "alert-when-free-disk-space-below-metrics": "mbytes",
    "alert-when-free-disk-space-below": true,
    "alert-when-free-disk-space-below-threshold": 3000,
    "alert-when-free-disk-space-below-type": "popup alert",
    "delete-when-free-disk-space-below-metrics": "mbytes",
    "delete-when-free-disk-space-below": true,
    "delete-when-free-disk-space-below-threshold": 5000,
    "before-delete-keep-logs-from-the-last-days": false,
    "before-delete-keep-logs-from-the-last-days-threshold": 3664,
    "before-delete-run-script": false,
    "before-delete-run-script-command": "",
    "stop-logging-when-free-disk-space-below-metrics": "mbytes",
    "stop-logging-when-free-disk-space-below": true,
    "stop-logging-when-free-disk-space-below-threshold": 100,
    "reject-connections-when-free-disk-space-below-threshold": false,
    "reserve-for-packet-capture-metrics": "mbytes",
    "reserve-for-packet-capture-threshold": 500,
    "delete-index-files-when-index-size-above-metrics": "mbytes",
    "delete-index-files-when-index-size-above": false,
    "delete-index-files-when-index-size-above-threshold": 100000,
    "delete-index-files-older-than-days": false,
    "delete-index-files-older-than-days-threshold": 14,
    "forward-logs-to-log-server": false,
    "perform-log-rotate-before-log-forwarding": false,
    "update-account-log-every": 3600,
    "detect-new-citrix-ica-application-names": false,
    "turn-on-qos-logging": true,
    "distribute-logs-between-all-active-servers": false
  },
  "identity-awareness": false,
  "platform-portal-settings": {
    "enabled": true,
    "portal-web-settings": {
      "main-url": "https://10.100.99.136/",
      "ip-address": "10.100.99.136",
      "aliases": []
    },
    "accessibility": {
      "allow-access-from": "RULE_BASE"
    }
  },
  "proxy-settings": {
    "use-custom-proxy": false
  },
  "nat-hide-internal-interfaces": false,
  "nat-settings": {
    "auto-rule": false
  },
  "fetch-policy": [
    "B25-EVAL-CM-CPT9x01"
  ],
  "hit-count": true,
  "enable-https-inspection": false,
  "application-control-and-url-filtering-settings": {
    "global-settings-mode": "use_global_settings"
  },
  "zero-phishing-settings": {
    "gateway-fqdn-mode": "automatic"
  },
  "ips-update-policy": "gateway automatic update",
  "auto-topology-use-custom-recalculation-time": false,
  "auto-topology-custom-recalculation-time": 10,
  "rtm-traffic-report": false,
  "rtm-counters-report": true,
  "rtm-traffic-report-per-connection": false,
  "communication-with-servers-behind-nat": {
    "override-profile": false
  },
  "interfaces-topology-settings": "per interface",
  "groups": [],
  "comments": "QA updated exhaustive variant 3",
  "color": "orange",
  "icon": "NetworkObjects/gateway",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732769624,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732769109,
      "iso-8601": "2026-02-10T09:12-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "not_supported"
  }
}
```

#### [PASSED] `delete-simple-gateway` ([0.45s])

**Payload snapshot:**
```json
{
  "name": "QA_SIMPLE-GATEWAY_3_398"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

---
## simple-cluster

<details>
<summary><b>[FAILED] Variant 1 (Total: 4.23s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-simple-cluster` | [FAILED] | 4.227 |

### 📄 Operational Logs
#### [FAILED] `add-simple-cluster` ([4.23s])

**Payload snapshot:**
```json
{
  "name": "QA_SIMPLE-CLUSTER_1_484",
  "color": "crete blue",
  "comments": "QA Automated Test Object",
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv4-address": "10.100.99.10",
  "version": "R81.10"
}
```
**Full Response:**
```json
{
  "message": "failed"
}
```

</details>

<details>
<summary><b>[FAILED] Variant 2 (Total: 2.18s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-simple-cluster` | [FAILED] | 2.177 |

### 📄 Operational Logs
#### [FAILED] `add-simple-cluster` ([2.18s])

**Payload snapshot:**
```json
{
  "name": "QA_SIMPLE-CLUSTER_2_351",
  "color": "crete blue",
  "comments": "QA Automated Test Object",
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv4-address": "10.100.99.81",
  "version": "R81.10"
}
```
**Full Response:**
```json
{
  "message": "failed"
}
```

</details>

---
## checkpoint-host

<details>
<summary><b>[PASSED] Variant 1 (Total: 1.09s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-checkpoint-host` | [PASSED] | 0.346 |
| `set-checkpoint-host` | [PASSED] | 0.245 |
| `show-checkpoint-host` | [PASSED] | 0.082 |
| `delete-checkpoint-host` | [PASSED] | 0.420 |

### 📄 Operational Logs
#### [PASSED] `add-checkpoint-host` ([0.35s])

**Payload snapshot:**
```json
{
  "name": "QA_CHECKPOINT-HOST_1_244",
  "color": "dark gray",
  "comments": "QA Automated Test Object",
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv4-address": "10.100.98.84"
}
```
**Full Response:**
```json
{
  "uid": "5456da99-24fb-4366-9408-7076c14c3380",
  "name": "QA_CHECKPOINT-HOST_1_244",
  "type": "checkpoint-host",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "nat-settings": {
    "enable-address-translation": false
  },
  "ipv4-address": "10.100.98.84",
  "interfaces": [],
  "version": "R82",
  "os": "Gaia",
  "hardware": "Open server",
  "sic-state": "uninitialized",
  "management-blades": {
    "network-policy-management": false,
    "user-directory": false,
    "compliance": false,
    "logging-and-status": false,
    "smart-event-server": false,
    "smart-event-correlation": false,
    "endpoint-policy": false,
    "secondary": true,
    "identity-logging": false
  },
  "firewall": false,
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "dark gray",
  "icon": "NetworkObjects/gateway",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732782032,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732782032,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {
    "clone": "not_supported"
  }
}
```

#### [PASSED] `set-checkpoint-host` ([0.25s])

**Payload snapshot:**
```json
{
  "name": "QA_CHECKPOINT-HOST_1_244",
  "comments": "QA updated exhaustive variant 1",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "5456da99-24fb-4366-9408-7076c14c3380",
  "name": "QA_CHECKPOINT-HOST_1_244",
  "type": "checkpoint-host",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "nat-settings": {
    "enable-address-translation": false
  },
  "ipv4-address": "10.100.98.84",
  "interfaces": [],
  "version": "R82",
  "os": "Gaia",
  "hardware": "Open server",
  "sic-state": "uninitialized",
  "management-blades": {
    "network-policy-management": false,
    "user-directory": false,
    "compliance": false,
    "logging-and-status": false,
    "smart-event-server": false,
    "smart-event-correlation": false,
    "endpoint-policy": false,
    "secondary": true,
    "identity-logging": false
  },
  "firewall": false,
  "groups": [],
  "comments": "QA updated exhaustive variant 1",
  "color": "orange",
  "icon": "NetworkObjects/gateway",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732782378,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732782032,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {
    "clone": "not_supported"
  }
}
```

#### [PASSED] `show-checkpoint-host` ([0.08s])

**Payload snapshot:**
```json
{
  "name": "QA_CHECKPOINT-HOST_1_244"
}
```
**Full Response:**
```json
{
  "uid": "5456da99-24fb-4366-9408-7076c14c3380",
  "name": "QA_CHECKPOINT-HOST_1_244",
  "type": "checkpoint-host",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "nat-settings": {
    "enable-address-translation": false
  },
  "ipv4-address": "10.100.98.84",
  "interfaces": [],
  "version": "R82",
  "os": "Gaia",
  "hardware": "Open server",
  "sic-state": "uninitialized",
  "management-blades": {
    "network-policy-management": false,
    "user-directory": false,
    "compliance": false,
    "logging-and-status": false,
    "smart-event-server": false,
    "smart-event-correlation": false,
    "endpoint-policy": false,
    "secondary": true,
    "identity-logging": false
  },
  "firewall": false,
  "groups": [],
  "comments": "QA updated exhaustive variant 1",
  "color": "orange",
  "icon": "NetworkObjects/gateway",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732782378,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732782032,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "not_supported"
  }
}
```

#### [PASSED] `delete-checkpoint-host` ([0.42s])

**Payload snapshot:**
```json
{
  "name": "QA_CHECKPOINT-HOST_1_244"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

<details>
<summary><b>[PASSED] Variant 2 (Total: 1.12s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-checkpoint-host` | [PASSED] | 0.417 |
| `set-checkpoint-host` | [PASSED] | 0.352 |
| `show-checkpoint-host` | [PASSED] | 0.069 |
| `delete-checkpoint-host` | [PASSED] | 0.285 |

### 📄 Operational Logs
#### [PASSED] `add-checkpoint-host` ([0.42s])

**Payload snapshot:**
```json
{
  "name": "QA_CHECKPOINT-HOST_2_160",
  "color": "dark gray",
  "comments": "QA Automated Test Object",
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv4-address": "10.100.98.94"
}
```
**Full Response:**
```json
{
  "uid": "08cdb0f8-d108-40a9-a5e4-543362e74d45",
  "name": "QA_CHECKPOINT-HOST_2_160",
  "type": "checkpoint-host",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "nat-settings": {
    "enable-address-translation": false
  },
  "ipv4-address": "10.100.98.94",
  "interfaces": [],
  "version": "R82",
  "os": "Gaia",
  "hardware": "Open server",
  "sic-state": "uninitialized",
  "management-blades": {
    "network-policy-management": false,
    "user-directory": false,
    "compliance": false,
    "logging-and-status": false,
    "smart-event-server": false,
    "smart-event-correlation": false,
    "endpoint-policy": false,
    "secondary": true,
    "identity-logging": false
  },
  "firewall": false,
  "groups": [],
  "comments": "QA Automated Test Object",
  "color": "dark gray",
  "icon": "NetworkObjects/gateway",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732783152,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732783152,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {
    "clone": "not_supported"
  }
}
```

#### [PASSED] `set-checkpoint-host` ([0.35s])

**Payload snapshot:**
```json
{
  "name": "QA_CHECKPOINT-HOST_2_160",
  "comments": "QA updated exhaustive variant 2",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "08cdb0f8-d108-40a9-a5e4-543362e74d45",
  "name": "QA_CHECKPOINT-HOST_2_160",
  "type": "checkpoint-host",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "nat-settings": {
    "enable-address-translation": false
  },
  "ipv4-address": "10.100.98.94",
  "interfaces": [],
  "version": "R82",
  "os": "Gaia",
  "hardware": "Open server",
  "sic-state": "uninitialized",
  "management-blades": {
    "network-policy-management": false,
    "user-directory": false,
    "compliance": false,
    "logging-and-status": false,
    "smart-event-server": false,
    "smart-event-correlation": false,
    "endpoint-policy": false,
    "secondary": true,
    "identity-logging": false
  },
  "firewall": false,
  "groups": [],
  "comments": "QA updated exhaustive variant 2",
  "color": "orange",
  "icon": "NetworkObjects/gateway",
  "tags": [],
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732783540,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732783152,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {
    "clone": "not_supported"
  }
}
```

#### [PASSED] `show-checkpoint-host` ([0.07s])

**Payload snapshot:**
```json
{
  "name": "QA_CHECKPOINT-HOST_2_160"
}
```
**Full Response:**
```json
{
  "uid": "08cdb0f8-d108-40a9-a5e4-543362e74d45",
  "name": "QA_CHECKPOINT-HOST_2_160",
  "type": "checkpoint-host",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "nat-settings": {
    "enable-address-translation": false
  },
  "ipv4-address": "10.100.98.94",
  "interfaces": [],
  "version": "R82",
  "os": "Gaia",
  "hardware": "Open server",
  "sic-state": "uninitialized",
  "management-blades": {
    "network-policy-management": false,
    "user-directory": false,
    "compliance": false,
    "logging-and-status": false,
    "smart-event-server": false,
    "smart-event-correlation": false,
    "endpoint-policy": false,
    "secondary": true,
    "identity-logging": false
  },
  "firewall": false,
  "groups": [],
  "comments": "QA updated exhaustive variant 2",
  "color": "orange",
  "icon": "NetworkObjects/gateway",
  "tags": [],
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732783540,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732783152,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "not_supported"
  }
}
```

#### [PASSED] `delete-checkpoint-host` ([0.29s])

**Payload snapshot:**
```json
{
  "name": "QA_CHECKPOINT-HOST_2_160"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

---
## interoperable-device

<details>
<summary><b>[PASSED] Variant 1 (Total: 0.43s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-interoperable-device` | [PASSED] | 0.145 |
| `set-interoperable-device` | [PASSED] | 0.098 |
| `show-interoperable-device` | [PASSED] | 0.065 |
| `delete-interoperable-device` | [PASSED] | 0.120 |

### 📄 Operational Logs
#### [PASSED] `add-interoperable-device` ([0.15s])

**Payload snapshot:**
```json
{
  "name": "QA_INTEROPERABLE-DEVICE_1_324",
  "color": "lemon chiffon",
  "comments": "QA Automated Test Object",
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv4-address": "10.100.97.108"
}
```
**Full Response:**
```json
{
  "uid": "fd0b153b-5d2c-4dba-84e9-faafdd113608",
  "name": "QA_INTEROPERABLE-DEVICE_1_324",
  "type": "interoperable-device",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address": "10.100.97.108",
  "interfaces": [],
  "vpn-settings": {
    "vpn-domain-type": "addresses_behind_gw",
    "vpn-domain-exclude-external-ip-addresses": false
  },
  "groups": [],
  "tags": [],
  "comments": "QA Automated Test Object",
  "color": "lemon chiffon",
  "icon": "NetworkObjects/gateway",
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732784747,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732784747,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {
    "clone": "not_supported"
  }
}
```

#### [PASSED] `set-interoperable-device` ([0.10s])

**Payload snapshot:**
```json
{
  "name": "QA_INTEROPERABLE-DEVICE_1_324",
  "comments": "QA updated exhaustive variant 1",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "fd0b153b-5d2c-4dba-84e9-faafdd113608",
  "name": "QA_INTEROPERABLE-DEVICE_1_324",
  "type": "interoperable-device",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address": "10.100.97.108",
  "interfaces": [],
  "vpn-settings": {
    "vpn-domain-type": "addresses_behind_gw",
    "vpn-domain-exclude-external-ip-addresses": false
  },
  "groups": [],
  "tags": [],
  "comments": "QA updated exhaustive variant 1",
  "color": "orange",
  "icon": "NetworkObjects/gateway",
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732784870,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732784747,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {
    "clone": "not_supported"
  }
}
```

#### [PASSED] `show-interoperable-device` ([0.06s])

**Payload snapshot:**
```json
{
  "name": "QA_INTEROPERABLE-DEVICE_1_324"
}
```
**Full Response:**
```json
{
  "uid": "fd0b153b-5d2c-4dba-84e9-faafdd113608",
  "name": "QA_INTEROPERABLE-DEVICE_1_324",
  "type": "interoperable-device",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address": "10.100.97.108",
  "interfaces": [],
  "vpn-settings": {
    "vpn-domain-type": "addresses_behind_gw",
    "vpn-domain-exclude-external-ip-addresses": false
  },
  "groups": [],
  "tags": [],
  "comments": "QA updated exhaustive variant 1",
  "color": "orange",
  "icon": "NetworkObjects/gateway",
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732784870,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732784747,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "not_supported"
  }
}
```

#### [PASSED] `delete-interoperable-device` ([0.12s])

**Payload snapshot:**
```json
{
  "name": "QA_INTEROPERABLE-DEVICE_1_324"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>

<details>
<summary><b>[PASSED] Variant 2 (Total: 0.45s)</b></summary>

### ⏱️ Performance Metrics
| Command | Status | Duration (s) |
| :--- | :--- | :--- |
| `add-interoperable-device` | [PASSED] | 0.206 |
| `set-interoperable-device` | [PASSED] | 0.090 |
| `show-interoperable-device` | [PASSED] | 0.063 |
| `delete-interoperable-device` | [PASSED] | 0.094 |

### 📄 Operational Logs
#### [PASSED] `add-interoperable-device` ([0.21s])

**Payload snapshot:**
```json
{
  "name": "QA_INTEROPERABLE-DEVICE_2_403",
  "color": "lemon chiffon",
  "comments": "QA Automated Test Object",
  "ignore-warnings": true,
  "ignore-errors": true,
  "ipv4-address": "10.100.97.45"
}
```
**Full Response:**
```json
{
  "uid": "b241b326-0763-4324-bbb9-0bb65c08a0ff",
  "name": "QA_INTEROPERABLE-DEVICE_2_403",
  "type": "interoperable-device",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address": "10.100.97.45",
  "interfaces": [],
  "vpn-settings": {
    "vpn-domain-type": "addresses_behind_gw",
    "vpn-domain-exclude-external-ip-addresses": false
  },
  "groups": [],
  "tags": [],
  "comments": "QA Automated Test Object",
  "color": "lemon chiffon",
  "icon": "NetworkObjects/gateway",
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732785206,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732785206,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {
    "clone": "not_supported"
  }
}
```

#### [PASSED] `set-interoperable-device` ([0.09s])

**Payload snapshot:**
```json
{
  "name": "QA_INTEROPERABLE-DEVICE_2_403",
  "comments": "QA updated exhaustive variant 2",
  "color": "orange"
}
```
**Full Response:**
```json
{
  "uid": "b241b326-0763-4324-bbb9-0bb65c08a0ff",
  "name": "QA_INTEROPERABLE-DEVICE_2_403",
  "type": "interoperable-device",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address": "10.100.97.45",
  "interfaces": [],
  "vpn-settings": {
    "vpn-domain-type": "addresses_behind_gw",
    "vpn-domain-exclude-external-ip-addresses": false
  },
  "groups": [],
  "tags": [],
  "comments": "QA updated exhaustive variant 2",
  "color": "orange",
  "icon": "NetworkObjects/gateway",
  "meta-info": {
    "lock": "unlocked",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732785355,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732785206,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "creator": "admin"
  },
  "read-only": true,
  "available-actions": {
    "clone": "not_supported"
  }
}
```

#### [PASSED] `show-interoperable-device` ([0.06s])

**Payload snapshot:**
```json
{
  "name": "QA_INTEROPERABLE-DEVICE_2_403"
}
```
**Full Response:**
```json
{
  "uid": "b241b326-0763-4324-bbb9-0bb65c08a0ff",
  "name": "QA_INTEROPERABLE-DEVICE_2_403",
  "type": "interoperable-device",
  "domain": {
    "uid": "41e821a0-3720-11e3-aa6e-0800200c9fde",
    "name": "SMC User",
    "domain-type": "domain"
  },
  "ipv4-address": "10.100.97.45",
  "interfaces": [],
  "vpn-settings": {
    "vpn-domain-type": "addresses_behind_gw",
    "vpn-domain-exclude-external-ip-addresses": false
  },
  "groups": [],
  "tags": [],
  "comments": "QA updated exhaustive variant 2",
  "color": "orange",
  "icon": "NetworkObjects/gateway",
  "meta-info": {
    "lock": "locked by current session",
    "validation-state": "ok",
    "last-modify-time": {
      "posix": 1770732785355,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "last-modifier": "admin",
    "creation-time": {
      "posix": 1770732785206,
      "iso-8601": "2026-02-10T09:13-0500"
    },
    "creator": "admin"
  },
  "read-only": false,
  "available-actions": {
    "edit": "true",
    "delete": "true",
    "clone": "not_supported"
  }
}
```

#### [PASSED] `delete-interoperable-device` ([0.09s])

**Payload snapshot:**
```json
{
  "name": "QA_INTEROPERABLE-DEVICE_2_403"
}
```
**Full Response:**
```json
{
  "message": "OK"
}
```

</details>