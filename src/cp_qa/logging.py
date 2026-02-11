"""Logging configuration for cp-api-qa-tool.

Provides lazy-initialized, namespace-scoped logging that avoids
polluting the root logger or triggering side-effects on import.

Usage::

    from cp_qa.logging import get_logger
    log = get_logger(__name__)

    log.info("Connected to management server")
    log.debug("Full payload: %s", payload)

The first call to ``get_logger()`` initializes the logging subsystem
(creates the log directory, attaches file + console handlers). Subsequent
calls return child loggers under the ``cp_qa`` namespace.

Configuration:
    Call ``configure()`` *before* the first ``get_logger()`` to override
    defaults (log directory, verbosity, quiet mode).  The CLI entry point
    calls ``configure()`` based on ``--debug`` / ``--quiet`` flags.
"""

import logging
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------
_initialized: bool = False
_log_dir: str = "logs"
_console_level: int = logging.INFO


def configure(
    log_dir: str = "logs",
    debug: bool = False,
    quiet: bool = False,
) -> None:
    """Set logging preferences before the first ``get_logger()`` call.

    Args:
        log_dir:  Directory for the rotating log file.  Created if missing.
        debug:    If True, the console handler prints DEBUG-level messages.
        quiet:    If True, the console handler only prints WARNING and above.
                  ``debug`` takes precedence over ``quiet``.
    """
    global _log_dir, _console_level, _initialized

    _log_dir = log_dir

    if debug:
        _console_level = logging.DEBUG
    elif quiet:
        _console_level = logging.WARNING
    else:
        _console_level = logging.INFO

    # If already initialized, update the existing console handler level
    if _initialized:
        pkg_logger = logging.getLogger("cp_qa")
        for handler in pkg_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(
                handler, logging.FileHandler
            ):
                handler.setLevel(_console_level)


def _init_logging() -> None:
    """One-time setup of file and console handlers under the ``cp_qa`` logger.

    Called automatically by ``get_logger()`` on its first invocation.
    """
    global _initialized
    if _initialized:
        return

    # Ensure log directory exists
    Path(_log_dir).mkdir(parents=True, exist_ok=True)

    # --- File handler: captures everything at DEBUG level ---
    file_handler = logging.FileHandler(
        os.path.join(_log_dir, "api_qa.log"), mode="w", encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    # --- Console handler: respects debug / quiet configuration ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(_console_level)
    console_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))

    # Attach to the package-level logger (not root) to avoid
    # polluting third-party libraries like requests / urllib3.
    pkg_logger = logging.getLogger("cp_qa")
    pkg_logger.setLevel(logging.DEBUG)
    pkg_logger.addHandler(file_handler)
    pkg_logger.addHandler(console_handler)

    _initialized = True


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger scoped under the ``cp_qa`` namespace.

    Args:
        name: Logger name.  Typically ``__name__`` of the calling module.
              If the name does not start with ``cp_qa``, it is automatically
              prefixed (e.g. ``"testdata"`` becomes ``"cp_qa.testdata"``).

    Returns:
        A ``logging.Logger`` instance.
    """
    _init_logging()
    if name and not name.startswith("cp_qa"):
        name = f"cp_qa.{name}"
    return logging.getLogger(name or "cp_qa")
