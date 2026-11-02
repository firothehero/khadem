"""Khadem (خادم) plugin: Arabic engine, branding layer, persona, defaults and bundled auto-load.

These tests are the contract that keeps Khadem working across upstream syncs: they read whatever
upstream currently ships (catalogs, plugin API) instead of pinning upstream content.
"""

from __future__ import annotations

import datetime as dt
import json

import pytest

from plugins.khadem import arabic, branding, defaults, persona, tools


@pytest.fixture(autouse=True)
def _isolate_env(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.delenv("HERMES_LANGUAGE", raising=False)
    monkeypatch.delenv("KHADEM_NO_ARABIC_DEFAULTS", raising=False)
    monkeypatch.delenv("KHADEM_DISABLE", raising=False)
    monkeypatch.setenv("KHADEM_FORCE", "1")  # the plugin is inert under pytest unless forced
    yield home


# ── Arabic engine ────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("n, words", [
    (0, "صفر"), (1, "واحد"), (2, "اثنان"), (11, "أحد عشر"), (12, "اثنا عشر"), (21, "واحد وعشرون"),
    (100, "مائة"), (200, "مئتان"), (345, "ثلاثمائة وخمسة وأربعون"), (1000, "ألف"), (2000, "ألفان"),
    (3000, "ثلاثة آلاف"), (11000, "أحد عشر ألفاً"), (103000, "مائة وثلاثة آلاف"),
    (2_500_000, "مليونان وخمسمائة ألف"),
    (1_234_567, "مليون ومئتان وأربعة وثلاثون ألفاً وخمسمائة وسبعة وستون"),
])
def test_number_to_words(n, words):
    assert arabic.number_to_words(n) == words


def test_number_to_words_feminine():
    assert arabic.number_to_words(21, feminine=True) == "إحدى وعشرون"
    assert arabic.number_to_words(13, feminine=True) == "ثلاث عشرة"


@pytest.mark.parametrize("amount, code, text", [
    ("1250.25", "SAR", "فقط ألف ومئتان وخمسون ريالاً وخمس وعشرون هللة لا غير"),
    ("1", "SAR", "فقط ريال واحد لا غير"),
    ("2", "AED", "فقط درهمان لا غير"),
    ("5", "KWD", "فقط خمسة دنانير لا غير"),
    ("15.750", "KWD", "فقط خمسة عشر ديناراً وسبعمائة وخمسون فلساً لا غير"),
    ("٣", "LBP", "فقط ثلاث ليرات لا غير"),
])
def test_amount_to_words(amount, code, text):
    assert arabic.amount_to_words(amount, code) == text


def test_amount_to_words_rejects_unknown_currency():
    with pytest.raises(ValueError):
        arabic.amount_to_words("1", "XXX")


def test_normalize_and_digits():
    assert arabic.normalize("أَحْمَدُ إلى ـالمستشفى") == "احمد الي المستشفي"
    assert arabic.to_eastern_digits("1,250.75") == "١٬٢٥٠٫٧٥"
    assert arabic.to_western_digits("١٢٣٫٥ و۴") == "123.5 و4"
    assert arabic.text_stats("مرحبا بالعالم")["direction"] == "rtl"


@pytest.mark.parametrize("greg, hijri", [
    (dt.date(2025, 3, 1), (1446, 9, 1)),     # 1 Ramadan 1446
    (dt.date(2024, 6, 15), (1445, 12, 9)),   # Arafah 1445
    (dt.date(2026, 11, 2), (1448, 5, 22)),
])
def test_hijri_round_trip(greg, hijri):
    h = arabic.to_hijri(greg)
    assert (h["year"], h["month"], h["day"]) == hijri
    assert h["method"] == "umm_al_qura"
    assert arabic.from_hijri(*hijri)["date"] == greg.isoformat()


def test_hijri_outside_table_falls_back_to_tabular():
    assert arabic.to_hijri(dt.date(1900, 1, 1))["method"].startswith("tabular")


def test_tool_handlers_return_json():
    out = json.loads(tools.arabic_text({"operation": "amount_to_words", "text": "100", "currency": "EGP"}))
    assert out == {"ok": True, "result": "فقط مائة جنيه لا غير"}
    out = json.loads(tools.hijri_date({"direction": "to_gregorian", "date": "١٤٤٦-٠٩-٠١"}))
    assert out["result"]["date"] == "2025-03-01"
    assert json.loads(tools.arabic_text({"operation": "nope", "text": ""}))["ok"] is False


# ── branding ─────────────────────────────────────────────────────────────────────────────────

def test_brand_text_keeps_commands_paths_and_identifiers():
    src = "شغّل `hermes model` في Hermes Agent؛ HERMES_HOME و~/.hermes وrunHermesModel وHermes One"
    out = branding.brand_text(src)
    assert "hermes model" in out and "HERMES_HOME" in out and "~/.hermes" in out
    assert "runHermesModel" in out
    assert "Hermes" not in out.replace("runHermesModel", "")
    assert out.count("خادم") == 2


def test_upstream_arabic_catalogs_still_exist_and_get_branded():
    """Fails loudly if a sync moves/renames upstream's Arabic catalogs (the branding source)."""
    from agent.i18n import _locales_dir

    core = branding.bundled_catalog(_locales_dir(), "ar")
    assert len(core) > 1000, "upstream locales/ar.yaml missing or shrunk"
    changes = branding.branded_changes(core)
    assert changes and all("خادم" in v for v in changes.values())


# ── persona + defaults ───────────────────────────────────────────────────────────────────────

def test_persona_render():
    ar = persona.render("ar", ["arabic-writing"], dt.date(2025, 3, 1))
    assert "أنت **خادم**" in ar and "`khadem:arabic-writing`" in ar and "1 رمضان 1446هـ" in ar
    assert "You are **Khadem**" in persona.render("en", [])
    assert len(ar) < 4000  # plugin prompt-section cap


def test_defaults_only_fill_unset_keys():
    assert defaults.missing_defaults({"display": {"language": "en"}}) == {"stt.language": "ar"}
    assert defaults.missing_defaults({"display": {"language": "fr"}, "stt": {"language": ""}}) == {}


# ── bundled auto-load through the real plugin manager ────────────────────────────────────────

def test_khadem_autoloads_and_makes_the_agent_arabic(_isolate_env):
    from agent import i18n
    from hermes_cli import plugins as pmod

    mgr = pmod.PluginManager()
    try:
        mgr.discover_and_load()
        loaded = mgr._plugins["khadem"]
        assert loaded.manifest.source == "bundled"
        assert loaded.enabled and not loaded.error, loaded.error

        cfg = (_isolate_env / "config.yaml").read_text(encoding="utf-8")
        assert "language: ar" in cfg
        i18n.reset_language_cache()
        assert i18n.get_language() == "ar"

        # A string upstream translated with "Hermes" now reads خادم.
        from agent.i18n import _locales_dir
        key = next(iter(branding.branded_changes(branding.bundled_catalog(_locales_dir(), "ar"))))
        assert "خادم" in i18n.t(key, lang="ar")

        assert {"arabic_text", "hijri_date"} <= set(loaded.tools_registered)
        section = mgr._system_prompt_sections["khadem.persona"]
        assert "خادم" in section.content({})
    finally:
        mgr.unload()


def test_explicit_user_language_wins(_isolate_env):
    (_isolate_env / "config.yaml").write_text("display:\n  language: en\n", encoding="utf-8")
    from hermes_cli import plugins as pmod

    mgr = pmod.PluginManager()
    try:
        mgr.discover_and_load()
        cfg = (_isolate_env / "config.yaml").read_text(encoding="utf-8")
        assert "language: en" in cfg.split("stt")[0]
    finally:
        mgr.unload()


def test_inert_under_pytest_without_force_and_when_disabled(_isolate_env, monkeypatch):
    """Upstream's own tests must see stock Hermes; KHADEM_DISABLE turns Khadem off anywhere."""
    from plugins import khadem

    monkeypatch.delenv("KHADEM_FORCE")
    assert khadem.khadem_active() is False
    monkeypatch.setenv("KHADEM_FORCE", "1")
    assert khadem.khadem_active() is True
    monkeypatch.setenv("KHADEM_DISABLE", "1")
    assert khadem.khadem_active() is False


# ── upstream seams: the non-public core surfaces Khadem relies on (see KHADEM.md) ────────────

@pytest.mark.parametrize("module, attr", [
    ("agent.i18n", "_locales_dir"),
    ("agent.i18n", "get_language"),
    ("agent.i18n", "reset_language_cache"),
    ("agent.i18n_layers", "parse_locale_file"),
    ("hermes_cli.config", "read_raw_config_readonly"),
    ("hermes_cli.config", "get_config_path"),
    ("hermes_cli.config", "is_managed"),
    ("hermes_cli.config_backend", "write_config_keys"),
    ("hermes_cli.config_backend", "get_config_backend"),
])
def test_upstream_seam_exists(module, attr):
    """If an upstream sync renames one of these, this fails before users notice anything."""
    import importlib

    assert callable(getattr(importlib.import_module(module), attr))


def test_plugin_api_surface_exists():
    from hermes_cli.plugins import PluginContext

    for name in ("register_locale", "register_system_prompt_section", "register_tool", "register_skill"):
        assert callable(getattr(PluginContext, name)), name
