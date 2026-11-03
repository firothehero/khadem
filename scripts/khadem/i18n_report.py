#!/usr/bin/env python3
"""Khadem Arabic coverage report for the agent (core + TUI catalogs).

Run from the repo root inside the project environment:  python scripts/khadem/i18n_report.py [--strict]

* lists English keys upstream has not translated into Arabic yet (they fall back to English until
  upstream or Khadem translates them — add Khadem translations in plugins/khadem/locales/ar[.tui].yaml);
* lists Khadem overrides whose key no longer exists upstream (stale after a sync — delete them);
* lists branded strings (what the خادم layer rewrites).
``--strict`` exits 1 when any Arabic gap or stale override exists (CI uses it as a warning gate).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from agent.i18n_layers import parse_locale_file  # noqa: E402
from plugins.khadem import branding  # noqa: E402

LOCALES = ROOT / "locales"
KHADEM_LOCALES = ROOT / "plugins" / "khadem" / "locales"


def _english(surface: str) -> dict[str, str]:
    if surface == "core":
        return parse_locale_file(LOCALES / "en.yaml")
    keys = json.loads((LOCALES / "_keys.tui.json").read_text(encoding="utf-8"))
    return {k: "" for k in (keys if isinstance(keys, list) else keys.keys())}


def _load(path: Path) -> dict[str, str]:
    return parse_locale_file(path) if path.is_file() else {}


def main() -> int:
    strict = "--strict" in sys.argv
    problems = 0
    for surface, ar_name in (("core", "ar.yaml"), ("tui", "ar.tui.yaml")):
        en = _english(surface)
        ar = _load(LOCALES / ar_name)
        own = _load(KHADEM_LOCALES / ar_name)
        missing = sorted(set(en) - set(ar) - set(own))
        stale = sorted(set(own) - set(en))
        branded = branding.branded_changes(ar)
        print(f"[{surface}] english={len(en)} arabic={len(ar)} khadem_overrides={len(own)} "
              f"branded={len(branded)} missing={len(missing)} stale_overrides={len(stale)}")
        for key in missing[:200]:
            print(f"  missing  {key}")
        for key in stale:
            print(f"  stale    {key}")
        problems += len(missing) + len(stale)
    return 1 if strict and problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
