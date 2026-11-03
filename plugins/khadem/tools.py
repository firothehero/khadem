"""Tool schemas + handlers for Khadem's Arabic tools (``arabic_text``, ``hijri_date``)."""

from __future__ import annotations

import datetime as _dt
import json
from typing import Any

from . import arabic

ARABIC_TEXT_SCHEMA = {
    "name": "arabic_text",
    "description": (
        "Arabic text utilities. operation=normalize (search-style: unify alef/yaa, strip tashkeel; "
        "options taa_marbuta, hamza), strip_diacritics, to_eastern_digits (0-9 → ٠-٩), to_western_digits, "
        "number_to_words (integer → Arabic words, feminine option), amount_to_words (money in words for "
        "cheques/invoices — تفقيط — with currency code such as SAR, AED, KWD, EGP, USD), stats (words, "
        "Arabic ratio, diacritics, direction, reading time). Use it instead of hand-writing these "
        "transformations: Arabic number grammar is easy to get wrong."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["normalize", "strip_diacritics", "to_eastern_digits", "to_western_digits",
                         "number_to_words", "amount_to_words", "stats"],
            },
            "text": {"type": "string", "description": "Input text, or the number/amount as a string."},
            "currency": {"type": "string", "description": "ISO code for amount_to_words (default SAR).",
                         "enum": sorted(arabic.CURRENCIES)},
            "cheque": {"type": "boolean", "description": "amount_to_words: wrap as «فقط … لا غير» (default true)."},
            "feminine": {"type": "boolean", "description": "number_to_words: agree with a feminine noun."},
            "taa_marbuta": {"type": "boolean", "description": "normalize: also map ة → ه."},
            "hamza": {"type": "boolean", "description": "normalize: also map ؤ → و and ئ → ي."},
        },
        "required": ["operation", "text"],
    },
}

HIJRI_DATE_SCHEMA = {
    "name": "hijri_date",
    "description": (
        "Convert dates between the Gregorian and Hijri (Islamic) calendars with Arabic month and weekday "
        "names. direction=to_hijri takes date=YYYY-MM-DD (default today); direction=to_gregorian takes "
        "date=YYYY-MM-DD as a Hijri date (e.g. 1447-09-01 for 1 Ramadan 1447). Uses Umm al-Qura when "
        "available; otherwise the tabular calendar, reported in `method`."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "direction": {"type": "string", "enum": ["to_hijri", "to_gregorian"]},
            "date": {"type": "string", "description": "YYYY-MM-DD (Arabic-Indic digits accepted)."},
        },
        "required": ["direction"],
    },
}


def _ok(result: Any) -> str:
    return json.dumps({"ok": True, "result": result}, ensure_ascii=False)


def _err(message: str) -> str:
    return json.dumps({"ok": False, "error": message}, ensure_ascii=False)


def _parse_ymd(value: str) -> tuple[int, int, int]:
    parts = arabic.to_western_digits(value.strip()).replace("/", "-").split("-")
    if len(parts) != 3:
        raise ValueError("date must be YYYY-MM-DD")
    y, m, d = (int(p) for p in parts)
    return y, m, d


def arabic_text(args: dict[str, Any], **_kw: Any) -> str:
    op = args.get("operation")
    text = str(args.get("text", ""))
    try:
        if op == "normalize":
            return _ok(arabic.normalize(text, taa_marbuta=bool(args.get("taa_marbuta")),
                                        hamza=bool(args.get("hamza"))))
        if op == "strip_diacritics":
            return _ok(arabic.strip_diacritics(text))
        if op == "to_eastern_digits":
            return _ok(arabic.to_eastern_digits(text))
        if op == "to_western_digits":
            return _ok(arabic.to_western_digits(text))
        if op == "number_to_words":
            n = int(arabic.to_western_digits(text).replace(",", "").strip())
            return _ok(arabic.number_to_words(n, feminine=bool(args.get("feminine"))))
        if op == "amount_to_words":
            cheque = args.get("cheque")
            return _ok(arabic.amount_to_words(text, args.get("currency") or "SAR",
                                              cheque=True if cheque is None else bool(cheque)))
        if op == "stats":
            return _ok(arabic.text_stats(text))
        return _err(f"unknown operation {op!r}")
    except (ValueError, TypeError) as exc:
        return _err(str(exc))


def hijri_date(args: dict[str, Any], **_kw: Any) -> str:
    direction = args.get("direction")
    raw = (args.get("date") or "").strip()
    try:
        if direction == "to_hijri":
            day = _dt.date(*_parse_ymd(raw)) if raw else _dt.date.today()
            result = arabic.to_hijri(day)
            result["gregorian"] = arabic.format_gregorian(day)
            return _ok(result)
        if direction == "to_gregorian":
            if not raw:
                return _err("date (Hijri YYYY-MM-DD) is required for to_gregorian")
            return _ok(arabic.from_hijri(*_parse_ymd(raw)))
        return _err(f"unknown direction {direction!r}")
    except (ValueError, TypeError) as exc:
        return _err(str(exc))
