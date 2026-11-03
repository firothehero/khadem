"""Arabic language utilities for Khadem: normalization, digits, amounts in words (تفقيط), Hijri dates.

Pure Python, no dependencies. Hijri conversion uses the official Umm al-Qura calendar (vendored table,
1343–1500 AH ≈ 1924–2077) and the tabular Islamic calendar outside that range — results say which.
"""

from __future__ import annotations

import datetime as _dt
import re
import unicodedata
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Optional

# ── normalization ─────────────────────────────────────────────────────────────────────────────

_DIACRITICS_RE = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭ]")
_TATWEEL = "ـ"
_ALEF_RE = re.compile("[آأإٱٲٳ]")  # آ أ إ ٱ ٲ ٳ → ا
_ARABIC_LETTER_RE = re.compile("[ء-يٮ-ۓۺ-ۿ]")
_WORD_RE = re.compile(r"[\w؀-ۿ]+", re.UNICODE)

EASTERN_DIGITS = "٠١٢٣٤٥٦٧٨٩"
PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
WESTERN_DIGITS = "0123456789"
_TO_WESTERN = str.maketrans(EASTERN_DIGITS + PERSIAN_DIGITS + "٫٬", WESTERN_DIGITS * 2 + ".,")
_TO_EASTERN = str.maketrans(WESTERN_DIGITS + PERSIAN_DIGITS, EASTERN_DIGITS * 2)


def strip_diacritics(text: str) -> str:
    """Remove tashkeel (harakat, tanween, shadda, sukun, dagger alef, Quranic marks) and tatweel."""
    return _DIACRITICS_RE.sub("", text).replace(_TATWEEL, "")


def normalize(text: str, *, alef: bool = True, yaa: bool = True, taa_marbuta: bool = False,
              hamza: bool = False, diacritics: bool = True) -> str:
    """Search-style normalization: unify alef forms, ى→ي, optionally ة→ه and ؤ/ئ→و/ي, strip marks."""
    text = unicodedata.normalize("NFKC", text)
    if diacritics:
        text = strip_diacritics(text)
    if alef:
        text = _ALEF_RE.sub("ا", text)
    if yaa:
        text = text.replace("ى", "ي")
    if taa_marbuta:
        text = text.replace("ة", "ه")
    if hamza:
        text = text.replace("ؤ", "و").replace("ئ", "ي")
    return re.sub(r"[ \t]+", " ", text).strip()


def to_western_digits(text: str) -> str:
    return text.translate(_TO_WESTERN)


def to_eastern_digits(text: str) -> str:
    """Western/Persian digits → Arabic-Indic (٠-٩); also uses the Arabic decimal and thousands marks."""
    out = re.sub(r"(?<=\d)\.(?=\d)", "٫", text)
    out = re.sub(r"(?<=\d),(?=\d{3})", "٬", out)
    return out.translate(_TO_EASTERN)


def text_stats(text: str) -> dict[str, Any]:
    words = _WORD_RE.findall(text)
    letters = [c for c in text if c.isalpha()]
    arabic = [c for c in letters if _ARABIC_LETTER_RE.match(c)]
    return {
        "characters": len(text),
        "words": len(words),
        "arabic_letter_ratio": round(len(arabic) / len(letters), 3) if letters else 0.0,
        "has_diacritics": bool(_DIACRITICS_RE.search(text)),
        # ~180 wpm is a common silent-reading estimate for Arabic prose.
        "reading_minutes": round(len(words) / 180, 1),
        "direction": "rtl" if letters and len(arabic) / len(letters) >= 0.5 else "ltr",
    }


# ── numbers to words (تفقيط) ──────────────────────────────────────────────────────────────────

_ONES_M = ["", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة", "عشرة"]
_ONES_F = ["", "واحدة", "اثنتان", "ثلاث", "أربع", "خمس", "ست", "سبع", "ثماني", "تسع", "عشر"]
_TEENS_M = ["", "أحد عشر", "اثنا عشر", "ثلاثة عشر", "أربعة عشر", "خمسة عشر", "ستة عشر", "سبعة عشر",
            "ثمانية عشر", "تسعة عشر"]
_TEENS_F = ["", "إحدى عشرة", "اثنتا عشرة", "ثلاث عشرة", "أربع عشرة", "خمس عشرة", "ست عشرة", "سبع عشرة",
            "ثماني عشرة", "تسع عشرة"]
_TENS = ["", "عشرة", "عشرون", "ثلاثون", "أربعون", "خمسون", "ستون", "سبعون", "ثمانون", "تسعون"]
_HUNDREDS = ["", "مائة", "مئتان", "ثلاثمائة", "أربعمائة", "خمسمائة", "ستمائة", "سبعمائة", "ثمانمائة",
             "تسعمائة"]
# (singular, dual, plural 3–10, accusative singular 11–99)
_SCALES = [
    ("ألف", "ألفان", "آلاف", "ألفاً"),
    ("مليون", "مليونان", "ملايين", "مليوناً"),
    ("مليار", "ملياران", "مليارات", "ملياراً"),
    ("تريليون", "تريليونان", "تريليونات", "تريليوناً"),
]


def _below_thousand(n: int, feminine: bool = False) -> str:
    """1–999 in words; ``feminine`` agrees the units with a feminine counted noun."""
    parts: list[str] = []
    hundreds, rest = divmod(n, 100)
    if hundreds:
        parts.append(_HUNDREDS[hundreds])
    if rest:
        ones = _ONES_F if feminine else _ONES_M
        if rest <= 10:
            word = ones[rest] if rest < 10 else ("عشر" if feminine else "عشرة")
        elif rest < 20:
            word = (_TEENS_F if feminine else _TEENS_M)[rest - 10]
        else:
            tens, unit = divmod(rest, 10)
            if unit:
                unit_word = ("إحدى" if feminine else "واحد") if unit == 1 else ones[unit]
                word = f"{unit_word} و{_TENS[tens]}"
            else:
                word = _TENS[tens]
        parts.append(word)
    return " و".join(parts)


def _scale_phrase(count: int, forms: tuple[str, str, str, str]) -> str:
    singular, dual, plural, accusative = forms
    if count == 1:
        return singular
    if count == 2:
        return dual
    if count <= 10:
        return f"{_below_thousand(count)} {plural}"
    tail = count % 100
    if 3 <= tail <= 10:
        return f"{_below_thousand(count)} {plural}"
    if 11 <= tail <= 99:
        return f"{_below_thousand(count)} {accusative}"
    return f"{_below_thousand(count)} {singular}"


def number_to_words(n: int, feminine: bool = False) -> str:
    """Integer → Arabic words, e.g. 3521 → «ثلاثة آلاف وخمسمائة وواحد وعشرون». Up to < 10^15."""
    if not isinstance(n, int):
        raise TypeError("number_to_words expects an int")
    if n < 0:
        return f"سالب {number_to_words(-n, feminine)}"
    if n == 0:
        return "صفر"
    if n >= 10 ** 15:
        raise ValueError("number too large (max 999 trillion)")
    groups: list[int] = []
    while n:
        n, g = divmod(n, 1000)
        groups.append(g)
    parts: list[str] = []
    for idx in range(len(groups) - 1, -1, -1):
        g = groups[idx]
        if not g:
            continue
        parts.append(_below_thousand(g, feminine) if idx == 0 else _scale_phrase(g, _SCALES[idx - 1]))
    return " و".join(parts)


# code: (major forms, major feminine, minor forms, minor feminine, minor units per major)
# forms = (singular, dual, plural 3–10, accusative 11–99)
CURRENCIES: dict[str, tuple[tuple[str, str, str, str], bool, tuple[str, str, str, str], bool, int]] = {
    "SAR": (("ريال", "ريالان", "ريالات", "ريالاً"), False, ("هللة", "هللتان", "هللات", "هللة"), True, 100),
    "AED": (("درهم", "درهمان", "دراهم", "درهماً"), False, ("فلس", "فلسان", "فلوس", "فلساً"), False, 100),
    "QAR": (("ريال", "ريالان", "ريالات", "ريالاً"), False, ("درهم", "درهمان", "دراهم", "درهماً"), False, 100),
    "KWD": (("دينار", "ديناران", "دنانير", "ديناراً"), False, ("فلس", "فلسان", "فلوس", "فلساً"), False, 1000),
    "BHD": (("دينار", "ديناران", "دنانير", "ديناراً"), False, ("فلس", "فلسان", "فلوس", "فلساً"), False, 1000),
    "OMR": (("ريال", "ريالان", "ريالات", "ريالاً"), False, ("بيسة", "بيستان", "بيسات", "بيسة"), True, 1000),
    "JOD": (("دينار", "ديناران", "دنانير", "ديناراً"), False, ("فلس", "فلسان", "فلوس", "فلساً"), False, 1000),
    "IQD": (("دينار", "ديناران", "دنانير", "ديناراً"), False, ("فلس", "فلسان", "فلوس", "فلساً"), False, 1000),
    "TND": (("دينار", "ديناران", "دنانير", "ديناراً"), False, ("مليم", "مليمان", "مليمات", "مليماً"), False, 1000),
    "LYD": (("دينار", "ديناران", "دنانير", "ديناراً"), False, ("درهم", "درهمان", "دراهم", "درهماً"), False, 1000),
    "EGP": (("جنيه", "جنيهان", "جنيهات", "جنيهاً"), False, ("قرش", "قرشان", "قروش", "قرشاً"), False, 100),
    "SDG": (("جنيه", "جنيهان", "جنيهات", "جنيهاً"), False, ("قرش", "قرشان", "قروش", "قرشاً"), False, 100),
    "MAD": (("درهم", "درهمان", "دراهم", "درهماً"), False, ("سنتيم", "سنتيمان", "سنتيمات", "سنتيماً"), False, 100),
    "DZD": (("دينار", "ديناران", "دنانير", "ديناراً"), False, ("سنتيم", "سنتيمان", "سنتيمات", "سنتيماً"), False, 100),
    "LBP": (("ليرة", "ليرتان", "ليرات", "ليرة"), True, ("قرش", "قرشان", "قروش", "قرشاً"), False, 100),
    "SYP": (("ليرة", "ليرتان", "ليرات", "ليرة"), True, ("قرش", "قرشان", "قروش", "قرشاً"), False, 100),
    "YER": (("ريال", "ريالان", "ريالات", "ريالاً"), False, ("فلس", "فلسان", "فلوس", "فلساً"), False, 100),
    "USD": (("دولار", "دولاران", "دولارات", "دولاراً"), False, ("سنت", "سنتان", "سنتات", "سنتاً"), False, 100),
    "EUR": (("يورو", "يوروان", "يوروهات", "يورو"), False, ("سنت", "سنتان", "سنتات", "سنتاً"), False, 100),
    "GBP": (("جنيه", "جنيهان", "جنيهات", "جنيهاً"), False, ("بنس", "بنسان", "بنسات", "بنساً"), False, 100),
}


def _counted(n: int, forms: tuple[str, str, str, str], feminine: bool) -> str:
    """A count with its noun: 1 → «ريال واحد», 2 → «ريالان», 5 → «خمسة ريالات», 25 → «خمسة وعشرون ريالاً»."""
    singular, dual, plural, accusative = forms
    if n == 1:
        return f"{singular} {'واحدة' if feminine else 'واحد'}"
    if n == 2:
        return dual
    words = number_to_words(n, feminine)
    tail = n % 100
    if 3 <= tail <= 10:
        return f"{words} {plural}"
    if 11 <= tail <= 99:
        return f"{words} {accusative}"
    return f"{words} {singular}"


def amount_to_words(amount: Any, currency: str = "SAR", *, cheque: bool = True) -> str:
    """Money in words for cheques/invoices: «فقط ألف ومئتان وخمسون ريالاً وخمس وعشرون هللة لا غير»."""
    code = (currency or "").upper()
    if code not in CURRENCIES:
        raise ValueError(f"unsupported currency {currency!r}; one of {', '.join(sorted(CURRENCIES))}")
    major_forms, major_f, minor_forms, minor_f, per = CURRENCIES[code]
    try:
        value = Decimal(to_western_digits(str(amount)).replace(",", ""))
    except InvalidOperation as exc:
        raise ValueError(f"not a number: {amount!r}") from exc
    if value < 0:
        raise ValueError("amount must not be negative")
    places = len(str(per)) - 1
    value = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    major = int(value)
    minor = int((value - major) * per)
    parts = []
    if major or not minor:
        parts.append(_counted(major, major_forms, major_f) if major else f"صفر {major_forms[0]}")
    if minor:
        parts.append(_counted(minor, minor_forms, minor_f))
    text = " و".join(parts)
    return f"فقط {text} لا غير" if cheque else text


# ── Hijri calendar ────────────────────────────────────────────────────────────────────────────

HIJRI_MONTHS = ["محرم", "صفر", "ربيع الأول", "ربيع الآخر", "جمادى الأولى", "جمادى الآخرة", "رجب", "شعبان",
                "رمضان", "شوال", "ذو القعدة", "ذو الحجة"]
GREGORIAN_MONTHS = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر",
                    "أكتوبر", "نوفمبر", "ديسمبر"]
GREGORIAN_MONTHS_LEVANT = ["كانون الثاني", "شباط", "آذار", "نيسان", "أيار", "حزيران", "تموز", "آب", "أيلول",
                           "تشرين الأول", "تشرين الثاني", "كانون الأول"]
WEEKDAYS = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]  # date.weekday() order

_ISLAMIC_EPOCH = 1948439.5  # civil (Friday) epoch, Julian Day of 1 Muharram 1 AH


def _gregorian_to_jd(y: int, m: int, d: int) -> float:
    return _dt.date(y, m, d).toordinal() + 1721424.5


def _jd_to_gregorian(jd: float) -> _dt.date:
    return _dt.date.fromordinal(int(jd - 1721424.5))


def _tabular_to_hijri(day: _dt.date) -> tuple[int, int, int]:
    jd = int(_gregorian_to_jd(day.year, day.month, day.day)) + 0.5
    year = int((30 * (jd - _ISLAMIC_EPOCH) + 10646) // 10631)
    month = min(12, int(-(-(jd - (29 + _tabular_hijri_to_jd(year, 1, 1))) // 29.5)) + 1)
    d = int(jd - _tabular_hijri_to_jd(year, month, 1)) + 1
    return year, month, d


def _tabular_hijri_to_jd(y: int, m: int, d: int) -> float:
    return (d + -(-(29.5 * (m - 1)) // 1) + (y - 1) * 354 + (3 + 11 * y) // 30 + _ISLAMIC_EPOCH) - 1


_JDN_ORDINAL_OFFSET = 1721425  # JDN(date) = date.toordinal() + 1721425
_RJD_OFFSET = 2400000  # Reduced Julian Day = JDN - 2400000
_TABULAR = "tabular (outside Umm al-Qura range; ±1–2 days)"


def _uaq_to_hijri(day: _dt.date) -> Optional[tuple[int, int, int]]:
    from bisect import bisect_right

    from . import ummalqura as uaq

    rjd = day.toordinal() + _JDN_ORDINAL_OFFSET - _RJD_OFFSET
    starts = uaq.MONTH_STARTS
    if not starts[0] <= rjd < starts[-1]:
        return None
    idx = bisect_right(starts, rjd) - 1
    total = idx + uaq.HIJRI_OFFSET
    return total // 12 + 1, total % 12 + 1, rjd - starts[idx] + 1


def _uaq_from_hijri(y: int, m: int, d: int) -> Optional[_dt.date]:
    from . import ummalqura as uaq

    idx = (y - 1) * 12 + (m - 1) - uaq.HIJRI_OFFSET
    if not 0 <= idx < len(uaq.MONTH_STARTS) - 1:
        return None
    if d > uaq.MONTH_STARTS[idx + 1] - uaq.MONTH_STARTS[idx]:
        raise ValueError(f"{HIJRI_MONTHS[m - 1]} {y} has only "
                         f"{uaq.MONTH_STARTS[idx + 1] - uaq.MONTH_STARTS[idx]} days")
    return _dt.date.fromordinal(uaq.MONTH_STARTS[idx] + d - 1 + _RJD_OFFSET - _JDN_ORDINAL_OFFSET)


def to_hijri(day: _dt.date) -> dict[str, Any]:
    """Gregorian → Hijri: the official Umm al-Qura calendar for 1343–1500 AH, tabular outside it."""
    found = _uaq_to_hijri(day)
    method = "umm_al_qura" if found else _TABULAR
    y, m, d = found or _tabular_to_hijri(day)
    return {
        "year": y, "month": m, "day": d, "month_name": HIJRI_MONTHS[m - 1],
        "weekday": WEEKDAYS[day.weekday()],
        "formatted": f"{WEEKDAYS[day.weekday()]} {d} {HIJRI_MONTHS[m - 1]} {y}هـ",
        "method": method,
    }


def from_hijri(y: int, m: int, d: int) -> dict[str, Any]:
    if not (1 <= m <= 12 and 1 <= d <= 31 and y >= 1):  # one historical UAQ month has 31 days
        raise ValueError("invalid Hijri date")
    day = _uaq_from_hijri(y, m, d)
    method = "umm_al_qura"
    if day is None:
        day = _jd_to_gregorian(_tabular_hijri_to_jd(y, m, d))
        method = _TABULAR
    return {"date": day.isoformat(), "formatted": format_gregorian(day), "weekday": WEEKDAYS[day.weekday()],
            "method": method}


def format_gregorian(day: _dt.date, levant: bool = False) -> str:
    months = GREGORIAN_MONTHS_LEVANT if levant else GREGORIAN_MONTHS
    return f"{WEEKDAYS[day.weekday()]} {day.day} {months[day.month - 1]} {day.year}م"


def today_line(today: Optional[_dt.date] = None) -> str:
    """«الاثنين 2 نوفمبر 2026م — الموافق 21 جمادى الأولى 1448هـ» for the persona section."""
    day = today or _dt.date.today()
    h = to_hijri(day)
    return f"{format_gregorian(day)} — الموافق {h['day']} {h['month_name']} {h['year']}هـ"
