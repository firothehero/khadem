"""Arabic-first defaults, applied once per home without editing upstream config defaults.

A key is only written when the user's raw config.yaml does not set it, so an explicit choice
(``display.language: en``) always wins and later syncs of upstream defaults are irrelevant.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Mapping

logger = logging.getLogger(__name__)

ARABIC_DEFAULTS: Mapping[str, Any] = {
    "display.language": "ar",  # UI strings: approvals, gateway replies, TUI, tips
    "stt.language": "ar",  # voice-memo transcription hint
}


def _has(raw: Mapping[str, Any], dotted: str) -> bool:
    node: Any = raw
    for part in dotted.split("."):
        if not isinstance(node, Mapping) or part not in node:
            return False
        node = node[part]
    return True


def missing_defaults(raw: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in ARABIC_DEFAULTS.items() if not _has(raw, k)}


def apply_arabic_defaults() -> dict[str, Any]:
    """Write the missing Arabic defaults into the active home's config.yaml. Never raises."""
    if os.getenv("KHADEM_NO_ARABIC_DEFAULTS", "").strip().lower() in {"1", "true", "yes"}:
        return {}
    try:
        from hermes_cli.config import get_config_path, is_managed, read_raw_config_readonly
        from hermes_cli.config_backend import write_config_keys

        from hermes_cli.config_backend import get_config_backend

        # Local homes only: a remote/managed config is owned by its operator, not by this client.
        if is_managed() or getattr(get_config_backend(), "name", "file") != "file":
            return {}
        updates = missing_defaults(read_raw_config_readonly() or {})
        if not updates:
            return {}
        write_config_keys(get_config_path(), updates)
        from agent.i18n import reset_language_cache

        reset_language_cache()
        logger.info("Khadem: applied Arabic defaults %s", sorted(updates))
        return updates
    except Exception as exc:  # never break plugin load over a defaults write
        logger.debug("Khadem: Arabic defaults skipped: %s", exc)
        return {}
