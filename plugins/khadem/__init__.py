"""Khadem (خادم): the Arabic-first layer of this Hermes Agent distribution.

Everything Khadem changes lives in this plugin so the fork can merge upstream Hermes at any time:

* ``branding``  — rebrands upstream's own Arabic catalogs (core + TUI) to خادم as a pack layer;
* ``locales/``  — Khadem's Arabic gap-fills/stylistic overrides (applied above upstream);
* ``persona``   — the Khadem identity as a plugin system-prompt section;
* ``defaults``  — Arabic-by-default settings written once into config.yaml when unset;
* ``tools``     — ``arabic_text`` and ``hijri_date``;
* ``skills/``   — Arabic skills, loaded with ``skill_view("khadem:<name>")``.

See KHADEM.md at the repository root.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from . import branding, defaults, persona, tools

logger = logging.getLogger(__name__)

PLUGIN_DIR = Path(__file__).resolve().parent
SKILLS_DIR = PLUGIN_DIR / "skills"
LOCALES_DIR = PLUGIN_DIR / "locales"
SURFACES = ("core", "tui")


def skill_names() -> list[str]:
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(p.name for p in SKILLS_DIR.iterdir() if (p / "SKILL.md").is_file())


def _register_locales(ctx) -> None:
    from agent.i18n import _locales_dir

    bundled_dir = _locales_dir()
    for surface in SURFACES:
        changes = branding.branded_changes(branding.bundled_catalog(bundled_dir, "ar", surface))
        if changes:
            ctx.register_locale("ar", changes, surface=surface, endonym="العربية", rtl=True)
    # Khadem's own Arabic layer last so it wins over both upstream and the branding layer.
    for surface in SURFACES:
        own = LOCALES_DIR / ("ar.yaml" if surface == "core" else f"ar.{surface}.yaml")
        if own.is_file():
            ctx.register_locale("ar", own, surface=surface, endonym="العربية", rtl=True)


def _truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def khadem_active() -> bool:
    """Khadem is on by default. ``KHADEM_DISABLE=1`` turns it off; under pytest it stays inert unless
    ``KHADEM_FORCE=1`` so upstream's own test-suite keeps testing upstream behaviour unchanged
    (Khadem's tests opt in). ``PYTEST_VERSION`` is set by pytest >= 8.2 for the whole run."""
    if _truthy("KHADEM_DISABLE"):
        return False
    if os.getenv("PYTEST_VERSION") and not _truthy("KHADEM_FORCE"):
        return False
    return True


def register(ctx) -> None:
    if not khadem_active():
        logger.debug("Khadem: inactive (KHADEM_DISABLE, or pytest without KHADEM_FORCE)")
        return
    try:
        _register_locales(ctx)
    except Exception as exc:  # branding must never stop the agent from loading
        logger.warning("Khadem: Arabic locale layer skipped: %s", exc)

    names = skill_names()
    ctx.register_system_prompt_section("khadem.persona", persona.section(names))

    ctx.register_tool(name="arabic_text", toolset="khadem", schema=tools.ARABIC_TEXT_SCHEMA,
                      handler=tools.arabic_text, description="Arabic text utilities", emoji="🔤")
    ctx.register_tool(name="hijri_date", toolset="khadem", schema=tools.HIJRI_DATE_SCHEMA,
                      handler=tools.hijri_date, description="Hijri ↔ Gregorian dates", emoji="🌙")

    for name in names:
        ctx.register_skill(name, SKILLS_DIR / name / "SKILL.md")

    defaults.apply_arabic_defaults()
