"""cp-api-qa-tool: Self-healing QA engine for Check Point Management API.

This package provides automated CRUD lifecycle testing for Check Point
Management API objects. It dynamically parses the official API specification,
generates exhaustive payloads covering every field and variant, and produces
professional reports with copy-paste ready examples.

Key capabilities:
    - Self-healing engine that analyzes API errors and auto-corrects payloads
    - Full add -> set -> show -> delete lifecycle testing per object type
    - Demo mode to create all object types at once for policy building
    - Variant coverage for mutually exclusive field-alternatives
    - Dynamic versioning based on the Management Server's API version
    - Professional Markdown audit reports and JSON example export

Usage:
    After installation (``pip install -e .``), run from the command line::

        cp-qa -m <MGMT_IP> -u <USER> -p <PASSWORD>

    Or import the engine directly::

        from cp_qa.engine import APIQAEngine
        from cp_qa.client import APIClient
"""

__version__ = "1.0.0"
__author__ = "Check Point API QA Tool Contributors"
