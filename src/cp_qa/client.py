"""Check Point Management API client.

Provides a thin wrapper around the Check Point Web API (HTTPS/JSON)
for session management (login / logout / publish) and arbitrary
command execution.

Usage::

    from cp_qa.client import APIClient

    client = APIClient("10.0.0.1", "admin", "secret")
    sid, api_version = client.login()
    result = client.run_command("show-host", {"name": "my-host"})
    client.publish()
    client.logout()

Note:
    TLS certificate verification is **disabled** because Check Point
    Management Servers typically use self-signed certificates.
"""

from __future__ import annotations

import time as _time

import requests

# Suppress InsecureRequestWarning for self-signed certificates
requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]

from cp_qa.logging import get_logger

log = get_logger(__name__)


class APIClient:
    """Stateful HTTP client for the Check Point Management Web API.

    Maintains an authenticated session (SID) in the ``X-chkp-sid``
    header after a successful :meth:`login`.

    Attributes:
        api_server_url: Base URL for API requests (e.g. ``https://10.0.0.1/web_api/``).
        user:           Username used for authentication.
        domain:         MDS domain name, if applicable.
        headers:        HTTP headers sent with every request (includes SID after login).
    """

    def __init__(
        self,
        api_server: str,
        user: str,
        password: str,
        api_key: str | None = None,
        domain: str | None = None,
    ) -> None:
        """Initialize the client.

        Args:
            api_server: Management Server IP or hostname.
            user:       Username for ``login`` (ignored when *api_key* is provided).
            password:   Password for ``login`` (ignored when *api_key* is provided).
            api_key:    Optional API key for key-based authentication.
            domain:     Optional MDS domain name.
        """
        self.user = user
        self.password = password
        self.api_key = api_key
        self.domain = domain
        self.headers: dict[str, str] = {"Content-Type": "application/json"}
        self.api_server_url = f"https://{api_server}/web_api/"

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def login(self) -> tuple[str, str]:
        """Authenticate with the Management Server.

        Returns:
            A ``(sid, api_version)`` tuple.  The SID is also stored
            internally in ``self.headers`` for subsequent requests.

        Raises:
            SystemExit: If the login request fails (non-200 status).
        """
        payload: dict = {"user": self.user, "password": self.password}

        if self.domain is not None:
            payload["domain"] = self.domain

        # API-key authentication replaces user/password
        if self.api_key is not None:
            payload["api-key"] = self.api_key
            del payload["user"]
            del payload["password"]

        response = requests.post(
            self.api_server_url + "login",
            headers=self.headers,
            json=payload,
            verify=False,
        )

        if response.status_code != 200:
            log.critical("Login failed: %s", response.text)
            exit(1)

        data = response.json()
        sid: str = data["sid"]
        api_version: str = data.get("api-server-version", "")
        self.headers["X-chkp-sid"] = sid
        log.info("Login successful, SID: %s, API Version: %s", sid, api_version)
        return sid, api_version

    def logout(self) -> None:
        """Terminate the authenticated session.

        Raises:
            SystemExit: If the logout request fails (non-200 status).
        """
        response = requests.post(
            self.api_server_url + "logout",
            headers=self.headers,
            json={},
            verify=False,
        )

        if response.status_code != 200:
            log.critical("Logout failed: %s", response.text)
            exit(1)

        log.info("Logout successful")

    def publish(self) -> None:
        """Publish pending changes to the management database.

        Retries once (2 attempts total) with a 5-second back-off on failure.
        """
        for attempt in range(1, 3):
            try:
                response = requests.post(
                    self.api_server_url + "publish",
                    headers=self.headers,
                    json={},
                    verify=False,
                    timeout=120,
                )
                code = response.status_code
                body = response.text

                if code == 200:
                    log.info("Publish successful")
                    return
                else:
                    log.warning("Publish returned %d: %s", code, body[:300])
                    if attempt < 2:
                        log.info("Retrying publish in 5 s ...")
                        _time.sleep(5)

            except Exception as exc:
                log.warning("Publish error: %s", exc)
                if attempt < 2:
                    _time.sleep(5)

        log.error("Publish failed after 2 attempts")

    # ------------------------------------------------------------------
    # Command execution
    # ------------------------------------------------------------------

    def run_command(self, command: str, payload: dict) -> dict:
        """Execute an arbitrary Management API command.

        Args:
            command:  API command name (e.g. ``"add-host"``, ``"show-network"``).
            payload:  JSON-serialisable request body.

        Returns:
            Parsed JSON response as a dictionary.
        """
        response = requests.post(
            self.api_server_url + command,
            headers=self.headers,
            json=payload,
            verify=False,
            timeout=300,
        )
        return response.json()
