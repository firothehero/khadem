"""خادم branding over the bundled Arabic catalogs, computed at load time.

Upstream owns ``locales/ar.yaml`` / ``locales/ar.tui.yaml`` and keeps translating new strings. Editing
those files would conflict on every sync, so Khadem never touches them: at plugin load we read whatever
upstream currently ships, rewrite the product name, and register only the changed keys as a pack layer
(packs sit above the bundled catalog). New upstream strings are branded automatically.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping

ARABIC_NAME = "خادم"
LATIN_NAME = "Khadem"

# Product-name spellings only. Lowercase ``hermes`` (CLI commands, paths, env vars such as
# HERMES_HOME) and camelCase identifiers are deliberately left alone: they must keep working.
# Latin-only lookarounds (not \b): Arabic prefixes attach directly ("وHermes", "لـHermes") and must
# still match, while camelCase/snake identifiers (runHermesModel, hermes_home) must not.
_BRAND_RE = re.compile(r"(?<![A-Za-z0-9_])(?:Hermes(?: Agent| One)?|هيرميس|هيرمس)(?![A-Za-z0-9_-])")


def brand_text(text: str, name: str = ARABIC_NAME) -> str:
    """Replace the Hermes product name with Khadem's, leaving commands/paths/identifiers intact."""
    return _BRAND_RE.sub(name, text)


def branded_changes(messages: Mapping[str, str], name: str = ARABIC_NAME) -> dict[str, str]:
    """Only the entries whose text changes under :func:`brand_text` (a minimal pack layer)."""
    out: dict[str, str] = {}
    for key, value in messages.items():
        if isinstance(value, str):
            branded = brand_text(value, name)
            if branded != value:
                out[key] = branded
    return out


def bundled_catalog(locales_dir: Path, lang: str, surface: str = "core") -> dict[str, str]:
    """Flat catalog of the upstream-bundled ``<lang>[.<surface>].yaml`` (empty if absent)."""
    from agent.i18n_layers import parse_locale_file

    name = f"{lang}.yaml" if surface == "core" else f"{lang}.{surface}.yaml"
    path = Path(locales_dir) / name
    return parse_locale_file(path) if path.is_file() else {}
