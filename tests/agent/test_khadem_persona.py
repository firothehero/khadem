"""Khadem: the Arabic persona is layered after the base identity only under the ar locale."""

from types import SimpleNamespace

import agent.system_prompt as sp


def _agent():
    return SimpleNamespace(load_soul_identity=True, skip_context_files=False)


def _patch(monkeypatch, lang, soul):
    monkeypatch.setattr(sp, "get_language", lambda: lang)
    monkeypatch.setattr(sp, "_agent_home", lambda agent: None)
    monkeypatch.setattr(sp._pb, "load_soul_md", lambda *a, **k: soul)


def test_arabic_locale_appends_persona_after_soul(monkeypatch):
    _patch(monkeypatch, "ar", "SOUL")
    parts, soul_loaded = sp._identity_parts(_agent(), None)
    assert parts == ["SOUL", sp.KHADEM_PERSONA_AR]
    assert soul_loaded is True


def test_arabic_locale_appends_persona_after_default_identity(monkeypatch):
    _patch(monkeypatch, "ar", None)
    parts, soul_loaded = sp._identity_parts(_agent(), None)
    assert parts == [sp.DEFAULT_AGENT_IDENTITY, sp.KHADEM_PERSONA_AR]
    assert soul_loaded is False


def test_other_locales_unchanged(monkeypatch):
    _patch(monkeypatch, "en", None)
    assert sp._identity_parts(_agent(), None) == ([sp.DEFAULT_AGENT_IDENTITY], False)
