---
name: arabic-nlp
description: "البرمجة مع النصوص العربية: التطبيع، البحث، الجذور، التعابير النمطية، الترتيب، والاتجاه في الواجهات — Arabic text processing for developers."
version: 1.0.0
author: Khadem
license: MIT
metadata:
  hermes:
    tags: [Arabic, NLP, regex, search, unicode, RTL, bidi]
    related_skills: [khadem:arabic-documents]
---

# معالجة النصوص العربية برمجياً

## التطبيع قبل البحث والمقارنة
استخدم أداة `arabic_text` بعملية `normalize` للنصوص القصيرة، وفي الشيفرة طبّق نفس المنطق:
- أزل التشكيل `[ً-ٰٟ]` والتطويل `ـ`.
- وحّد الألف `[أإآٱ]` → `ا`، و`ى` → `ي`، واختيارياً `ة` → `ه`.
- حوّل الأرقام المشرقية `٠-٩` والفارسية `۰-۹` إلى `0-9`.
- طبّع Unicode بـ NFKC أولاً (أشكال العرض مثل ﻻ تصبح لا).

## التعابير النمطية
- الحروف العربية: `[ء-ي]`؛ النطاق الأوسع: `[؀-ۿݐ-ݿࢠ-ࣿ]`.
- `\b` لا يعمل جيداً مع العربية في بعض المحركات؛ استخدم حدوداً صريحة `(?<![؀-ۿ])` و`(?![؀-ۿ])`.
- السوابق الشائعة: ال، و، ف، ب، ك، ل، وال، بال، كال، فال، لل؛ أزلها بحذر عند البحث.

## الجذور والتحليل الصرفي
- خفيف: `nltk.stem.isri.ISRIStemmer`.
- متقدّم: **CAMeL Tools** (`camel_tools`) للتحليل الصرفي، والتعرّف على اللهجات، والكيانات المسمّاة.
- نماذج: AraBERT / CAMeLBERT / MARBERT (للهجات ووسائل التواصل).

## البحث النصي
- SQLite FTS5: طبّع النص قبل الفهرسة واحفظ نسخة مطبّعة في عمود منفصل.
- PostgreSQL: أنشئ إعداد بحث مخصّص مع `unaccent` وقاموس عربي أو استخدم pg_trgm على النص المطبّع.
- Elasticsearch/OpenSearch: محلّل `arabic` المدمج (يشمل التطبيع والجذع الخفيف).

## الترتيب
استخدم ترتيباً مدركاً للّغة: Python `PyICU` (`icu.Collator.createInstance(icu.Locale("ar"))`)، JavaScript `new Intl.Collator("ar")`. الترتيب حسب نقاط Unicode يضع «أ» و«إ» في غير موضعهما.

## الواجهات (RTL)
- `dir="auto"` لحقول الإدخال والنصوص التي يكتبها المستخدم؛ `dir="rtl"` على `<html>` للواجهة العربية.
- خصائص CSS المنطقية: `margin-inline-start` بدل `margin-left`، `text-align: start`، `inset-inline-end`.
- اعزل الأرقام والشيفرات والروابط: `unicode-bidi: isolate` أو `<bdi>`.
- لا تستخدم `letter-spacing` أو `text-transform` على النص العربي.
- اقلب الأيقونات الاتجاهية (الأسهم) في RTL فقط، لا الشعارات أو أيقونات التشغيل.

## التنسيق المحلي
`Intl.NumberFormat("ar-SA")` و`Intl.DateTimeFormat("ar-SA-u-ca-islamic-umalqura")` للتاريخ الهجري في المتصفح؛ `ar-EG` للأرقام المشرقية، و`ar-u-nu-latn` للأرقام الغربية مع النص العربي.
