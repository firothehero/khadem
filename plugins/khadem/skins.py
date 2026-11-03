"""Install Khadem's CLI/TUI skin into the active home (user skins live in ``<home>/skins``).

The skin file is Khadem-managed: it is (re)written when missing or when its bytes differ from the
shipped copy, so an upgrade of the plugin upgrades the skin. Users customise a copy under another
name; ``display.skin`` is only set to ``khadem`` when unset (see defaults.py).
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SKIN_NAME = "khadem"
SHIPPED = Path(__file__).resolve().parent / "skins" / f"{SKIN_NAME}.yaml"


def install_skin(home: Path | None = None) -> bool:
    """Copy the shipped skin into ``<home>/skins/``; True when a write happened. Never raises."""
    try:
        if home is None:
            from hermes_constants import get_hermes_home

            home = get_hermes_home()
        target = Path(home) / "skins" / f"{SKIN_NAME}.yaml"
        shipped = SHIPPED.read_bytes()
        if target.is_file() and target.read_bytes() == shipped:
            return False
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(shipped)
        return True
    except Exception as exc:
        logger.debug("Khadem: skin install skipped: %s", exc)
        return False
