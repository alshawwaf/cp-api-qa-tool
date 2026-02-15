"""QA engine facade — public API for lifecycle testing and demo mode.

The :class:`APIQAEngine` class composes all engine submodules and
maintains shared state (API client, spec, results).  External code
should interact with this class rather than the submodules directly.

Usage::

    from cp_qa.engine import APIQAEngine
    from cp_qa.client import APIClient

    client = APIClient("10.0.0.1", "admin", "secret")
    client.login()

    engine = APIQAEngine(client, spec_url)
    engine.fetch_spec()
    engine.run_lifecycle_test("host", add_cmd_spec)
    engine.export_report("reports/QA_RAW_DATA.json")
"""

from __future__ import annotations

from typing import Any

from cp_qa.engine import demo, lifecycle, reports, spec
from cp_qa.logging import get_logger

log = get_logger(__name__)


class APIQAEngine:
    """Facade class that composes all engine submodules.

    Holds shared state and delegates to pure functions in submodules,
    keeping the public API identical to the original monolithic class.

    Attributes:
        client:  Authenticated :class:`~cp_qa.client.APIClient`.
        spec:    Parsed API specification dict (populated by :meth:`fetch_spec`).
        results: Accumulated lifecycle test results.
    """

    def __init__(self, client: Any, spec_url: str, api_version: str = "",
                 version_source: str = "auto") -> None:
        """Initialise the engine.

        Args:
            client:         An authenticated API client instance.
            spec_url:       URL to the Check Point API specification JSON.
            api_version:    Detected API version string (e.g. ``"2.0.1"``).
            version_source: ``"auto"`` (server-detected) or ``"user"`` (CLI override).
        """
        self.client = client
        self.spec_url = spec_url
        self.api_version = api_version
        self.version_source = version_source
        self.spec: dict | None = None
        self.results: list[dict] = []
        self._current_obj_type: str = ""

    # ------------------------------------------------------------------
    # Spec operations
    # ------------------------------------------------------------------

    def fetch_spec(self) -> bool:
        """Download and parse the API specification.

        Returns:
            ``True`` on success, ``False`` on failure.
        """
        self.spec = spec.fetch_spec(self.spec_url, headers=getattr(self.client, "headers", None))
        return self.spec is not None

    def reconstruct_full_spec(self, base_url: str, version: str) -> dict | None:
        """Reconstruct the full API spec from multiple sources."""
        self.spec = spec.reconstruct_full_spec(base_url, version)
        return self.spec

    def get_commands_by_section(self, section_name: str) -> list[dict]:
        """Return all documented commands within a specific section.

        Args:
            section_name: Section/group name to filter by.

        Returns:
            List of command definition dicts.
        """
        return spec.get_commands_by_section(self.spec, section_name)

    def get_object_by_name(self, obj_name: str) -> dict | None:
        """Retrieve an object definition from the spec.

        Args:
            obj_name: Exact object schema name.

        Returns:
            The matching object dict, or ``None``.
        """
        return spec.get_object_by_name(self.spec, obj_name)

    # ------------------------------------------------------------------
    # QA lifecycle
    # ------------------------------------------------------------------

    def run_lifecycle_test(self, obj_type: str, add_cmd_spec: dict) -> bool:
        """Run the full add -> set -> show -> delete lifecycle for *obj_type*.

        Results are appended to :attr:`results`.

        Args:
            obj_type:     Object type to test.
            add_cmd_spec: Command spec dict for ``add-<type>``.

        Returns:
            ``True`` if the lifecycle completed.
        """
        self._current_obj_type = obj_type
        return lifecycle.run_lifecycle_test(
            self.client, self.spec, self.results, obj_type, add_cmd_spec
        )

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    def export_report(self, file_path: str) -> None:
        """Write the raw test results to a JSON file.

        Args:
            file_path: Output path.
        """
        reports.export_report(self.results, file_path)

    def export_markdown_report(self, file_path: str) -> None:
        """Generate a Markdown performance audit report.

        Args:
            file_path: Output path.
        """
        reports.export_markdown_report(self.results, file_path, api_version=self.api_version, version_source=self.version_source)

    def export_examples(self, base_dir: str) -> None:
        """Export standalone JSON example files per variant.

        Args:
            base_dir: Output directory.
        """
        reports.export_examples(self.results, base_dir, api_version=self.api_version, version_source=self.version_source)

    def export_per_type_reports(self, base_dir: str) -> None:
        """Generate a separate QA report and raw JSON for each object type.

        Each type gets ``QA_REPORT.md`` and ``QA_RAW_DATA.json`` saved
        alongside its example payloads.

        Args:
            base_dir: Examples base directory (e.g. ``reports/examples``).
        """
        reports.export_per_type_reports(self.results, base_dir, api_version=self.api_version, version_source=self.version_source)

    # ------------------------------------------------------------------
    # Demo mode
    # ------------------------------------------------------------------

    def run_demo_create(self, obj_type: str, add_cmd_spec: dict) -> list[dict]:
        """Create one representative demo object (ADD only).

        Args:
            obj_type:     Object type to create.
            add_cmd_spec: Command spec dict for ``add-<type>``.

        Returns:
            List of manifest entries.
        """
        self._current_obj_type = obj_type
        return demo.run_demo_create(
            self.client, self.spec, obj_type, add_cmd_spec
        )

    def run_demo_cleanup(self, manifest: list[dict]) -> dict:
        """Delete all objects listed in the manifest.

        Args:
            manifest: List of manifest entry dicts.

        Returns:
            ``{"deleted": int, "failed": int}``
        """
        return demo.run_demo_cleanup(self.client, manifest)

    def create_demo_services(self) -> list[dict]:
        """Create service objects for the demo policy.

        Returns:
            List of manifest entries.
        """
        return demo.create_demo_services(self.client)

    def create_demo_policy(self, manifest: list[dict]) -> list[dict]:
        """Create a recommended security policy using demo objects.

        Args:
            manifest: Current manifest with all created objects.

        Returns:
            List of manifest entries for the policy package.
        """
        return demo.create_demo_policy(self.client, manifest)

    def discover_demo_objects(self) -> list[dict]:
        """Sweep the server for all objects matching known prefixes.

        Queries every supported type for objects whose name starts with
        ``DEMO_`` or ``QA_``.  Returns a manifest-compatible list.

        Returns:
            List of ``{"type": str, "name": str, "uid": str}`` dicts.
        """
        return demo.discover_demo_objects(self.client)
