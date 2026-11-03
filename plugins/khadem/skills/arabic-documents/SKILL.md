---
name: arabic-documents
description: "إنشاء مستندات عربية صحيحة الاتجاه (RTL): Word وPDF وHTML وExcel وPowerPoint وصور، مع تشكيل الحروف والخطوط العربية — Arabic RTL documents."
version: 1.0.0
author: Khadem
license: MIT
metadata:
  hermes:
    tags: [Arabic, RTL, docx, pdf, pptx, xlsx, html, fonts, مستندات]
    related_skills: [khadem:arabic-writing]
---

# المستندات العربية (من اليمين إلى اليسار)

أكثر الأخطاء شيوعاً في المستندات العربية: الحروف منفصلة (غير مُشكَّلة/موصولة)، الاتجاه من اليسار، علامات الترقيم في الطرف الخطأ، وخط لا يدعم العربية. اتبع ما يلي لكل صيغة، وتحقّق من الناتج دائماً (حوّله إلى صورة وافحصه إن أمكن).

## الخطوط
استخدم خطاً يدعم العربية: **Noto Naskh Arabic** (قراءة نصوص طويلة)، **Noto Sans Arabic / IBM Plex Sans Arabic / Cairo / Tajawal** (واجهات وعناوين)، **Amiri** (طابع كلاسيكي). على لينكس: `fc-list :lang=ar` لمعرفة المتاح؛ وإن لم يوجد نزّل Noto من Google Fonts.

## HTML / Markdown → PDF (الطريقة الأسهل والأجمل)
```html
<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<style>
  body { font-family: "Noto Naskh Arabic", "Amiri", serif; line-height: 1.9; font-size: 16px; }
  code, pre { direction: ltr; unicode-bidi: isolate; font-family: monospace; }
  table { border-collapse: collapse; } td, th { padding: 6px 10px; text-align: start; }
</style></head><body>…</body></html>
```
حوّله بـ Chromium/Playwright (`page.pdf()`) أو WeasyPrint؛ كلاهما يُشكّل العربية تلقائياً. **لا تستخدم `letter-spacing` مع العربية** فهو يفصل الحروف.

## Word (python-docx)
python-docx لا يضبط الاتجاه تلقائياً؛ اضبطه لكل فقرة ولكل مقطع:
```python
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def rtl_paragraph(p, font="Noto Naskh Arabic", size=None):
    pPr = p._p.get_or_add_pPr()
    bidi = OxmlElement("w:bidi"); bidi.set(qn("w:val"), "1"); pPr.append(bidi)
    p.alignment = 2  # WD_ALIGN_PARAGRAPH.RIGHT
    for run in p.runs:
        rPr = run._r.get_or_add_rPr()
        rtl = OxmlElement("w:rtl"); rtl.set(qn("w:val"), "1"); rPr.append(rtl)
        fonts = rPr.find(qn("w:rFonts"))
        if fonts is None:  # lxml elements are falsy when childless, so never use `or` here
            fonts = OxmlElement("w:rFonts"); rPr.append(fonts)
        fonts.set(qn("w:cs"), font); fonts.set(qn("w:ascii"), font); fonts.set(qn("w:hAnsi"), font)
        if size: run.font.size = size  # also set w:szCs for complex-script size
doc = Document(); p = doc.add_paragraph("مرحباً بكم"); rtl_paragraph(p); doc.save("out.docx")
```
للجداول: أضف `<w:bidiVisual/>` إلى `tblPr` ليبدأ العمود الأول من اليمين.

## PDF مباشرة (ReportLab / FPDF)
هذه المكتبات **لا تُشكّل العربية**؛ مرّر النص أولاً عبر `arabic_reshaper` ثم `python-bidi`:
```python
import arabic_reshaper
from bidi.algorithm import get_display
visual = get_display(arabic_reshaper.reshape("مرحباً بالعالم"))
```
وسجّل خطاً عربياً TTF. يُفضَّل مسار HTML → PDF أعلاه كلما أمكن.

## Excel (openpyxl)
```python
ws.sheet_view.rightToLeft = True
from openpyxl.styles import Alignment, Font
cell.alignment = Alignment(horizontal="right", readingOrder=2)
cell.font = Font(name="Arial")  # أو أي خط يدعم العربية
```

## PowerPoint (python-pptx)
اضبط `algn="r"` و`rtl="1"` على `a:pPr` لكل فقرة، واختر خطاً عربياً في `a:cs` داخل `a:rPr`.

## الصور (Pillow)
Pillow مع libraqm يُشكّل العربية: `ImageFont.truetype(font, size, layout_engine=ImageFont.Layout.RAQM)` و`draw.text(..., direction="rtl", language="ar")`. بدون raqm استخدم `arabic_reshaper` + `get_display`.

## قائمة تحقق قبل التسليم
- [ ] الحروف موصولة (لا «م ر ح ب ا»).
- [ ] الاتجاه RTL والمحاذاة يميناً، والجداول تبدأ من اليمين.
- [ ] الأرقام والشيفرات والروابط معزولة LTR وتُقرأ صحيحة.
- [ ] الخط عربي وواضح، وارتفاع السطر مريح (1.6–2.0).
