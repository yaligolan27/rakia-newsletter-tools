# -*- coding: utf-8 -*-
"""
בניית גיליון הניוזלטר השבועי של רקיע מתוך קובץ תוכן JSON + נכסי העיצוב.
שימוש:  python build_newsletter.py content/issue_001.json
פלט:    output/newsletter_<num>_full.html      (קובץ עצמאי מלא, פונטים ותמונות מוטמעים)
        output/newsletter_<num>_artifact.html  (גרסה לפרסום כ-Artifact: ללא doctype/html/head/body)
        ../../ניוזלטר_שבועי_<num>.html          (עותק בתיקיית הפרויקט)
העיצוב נאמן לטמפלט Claude Design: template_reference.dc.html
"""
import base64
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
FONTS = os.path.join(ASSETS, "fonts")

MIME = {".otf": "font/otf", ".webp": "image/webp", ".png": "image/png",
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml"}


def data_uri(path):
    ext = os.path.splitext(path)[1].lower()
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{MIME[ext]};base64,{b64}"


def asset(name):
    return data_uri(os.path.join(ASSETS, name))


def esc(s):
    return html.escape(str(s or ""), quote=True)


def t(s):
    """esc + עטיפת טווחי מספרים (23–26.08, 2029-2033) ב-LTR כדי שלא יתהפכו ב-RTL."""
    return re.sub(r"(\d[\d.,:]*\s?[–-]\s?\d[\d.,:]*)",
                  r'<span dir="ltr">\1</span>', esc(s))


def isf_logo_ok():
    """לוגו הפורום מייצוא Claude Design הגיע ריק (image ללא href) — נכלל רק אם הוחלף בקובץ תקין."""
    try:
        with open(os.path.join(ASSETS, "logo-isf.svg"), encoding="utf-8", errors="ignore") as f:
            svg = f.read()
        return "<path" in svg or "data:image" in svg or "href=\"data:" in svg
    except OSError:
        return False


# תמונת אווירה לכל קטגוריית חדשות (מנכסי המותג — לא תמונות מהכתבות עצמן)
CATEGORY_IMG = {
    "שיגורים": "img-crew.png",
    "כלכלה ותעשייה": "img-industry.png",
    "מדיניות": "img-vision1.png",
    "ביטחון": "img-vision2.png",
    "חישה מרחוק": "img-education.png",
    "תקשורת לוויינית": "img-vision1.png",
    "חקר החלל": "img-crew.png",
}
IMG_POOL = ["img-crew.png", "img-industry.png", "img-vision1.png",
            "img-vision2.png", "img-education.png", "img-events.png"]
ACCENTS = ["#d54b63", "#f58220", "#4d77de"]

CHIP_ISRAEL = ("font-family:'Almoni Tzar'; font-weight:400; font-size:13.5px; line-height:1.6; "
               "color:#f9fdff; background:#1e273d; border-radius:3.8rem; padding:0 .85rem")
CHIP_INTL = ("font-family:'Almoni Tzar'; font-weight:400; font-size:13.5px; line-height:1.6; "
             "color:#111b32; background:#f0f6fa; border-radius:3.8rem; padding:0 .85rem")


def scope_chip(scope):
    style = CHIP_ISRAEL if "ישראל" in scope else CHIP_INTL
    return f'<span style="{style}">{esc(scope)}</span>'


def cta(text, color="#111b32"):
    return (f'<span style="display:inline-flex; align-items:center; gap:7px; padding-top:12px; '
            f'font-size:14.5px; font-weight:600; color:{color}">{esc(text)}'
            f'<span style="width:26px; height:1.5px; background:{color}; display:block"></span>'
            f'<span style="width:6px; height:6px; border-radius:20px; background:{color}; display:block"></span></span>')


def build(content):
    iss = content["issue"]
    ed = content.get("editorial") or {}
    stats = content.get("stats") or []
    opps = content["opportunities"]
    events = content.get("events") or []
    news = content["news"]

    fonts_css = "\n".join(
        f"@font-face{{font-family:'{fam}';src:url('{data_uri(os.path.join(FONTS, fn))}');"
        f"font-weight:{w};font-display:swap}}"
        for fam, fn, w in [
            ("Almoni", "almoni-light-aaa.otf", 300),
            ("Almoni", "almoni-regular-aaa.otf", 400),
            ("Almoni", "almoni-medium-aaa.otf", 500),
            ("Almoni", "almoni-bold-aaa.otf", 700),
            ("Almoni Tzar", "almoni-tzar-medium-aaa.otf", 500),
            ("Almoni Tzar", "almoni-tzar-bold-aaa.otf", 700),
        ])

    # ── במהדורה זו ──
    bullets = "".join(
        f'<div style="font-size:16px; font-weight:400; color:#111b32; display:flex; align-items:center; gap:8px">'
        f'<span style="width:6px; height:6px; border-radius:20px; background:{ACCENTS[i % len(ACCENTS)] if i != 1 else "#4d77de"}; display:block"></span>'
        f'{t(b["text"])}</div>'
        for i, b in enumerate(content.get("in_this_issue") or []))

    # ── דבר המערכת (ללא חתימה אישית — עד לאישור חתימה רשמית) ──
    editorial_html = ""
    if ed.get("text"):
        editorial_html = f"""
  <div style="padding:34px 32px 0">
    <div style="display:flex; gap:18px; align-items:flex-start">
      <div style="width:64px; height:64px; border-radius:50%; background:#111b32; display:flex; align-items:center; justify-content:center; flex:none">
        <img src="{asset('logo-rakia-white.png')}" alt="" style="width:40px; display:block" />
      </div>
      <div style="flex:1">
        <div style="display:flex; align-items:center; gap:10px; padding-bottom:6px">
          <span style="font-family:'Almoni Tzar'; font-weight:700; font-size:15px; letter-spacing:.16em; color:#111b32">דבר המערכת</span>
          <span style="flex:1; height:1.5px; background:#111b32; display:block; opacity:.25"></span>
        </div>
        <div style="font-size:16.5px; font-weight:300; line-height:1.55; color:#2b3547">{t(ed["text"])}</div>
        <div style="padding-top:10px; font-size:14.5px; font-weight:500; color:#111b32">מערכת הניוזלטר<span style="font-weight:300; color:#67717f"> · הפורום הישראלי לחלל</span></div>
      </div>
    </div>
  </div>"""

    # ── נתוני השבוע ──
    stats_html = ""
    if stats:
        cells = []
        for s in stats[:3]:
            suffix = (f'<span style="font-size:22px">{esc(s["suffix"])}</span>') if s.get("suffix") else ""
            cells.append(
                f'<div style="flex:1"><div dir="ltr" style="font-family:\'Almoni Tzar\'; font-weight:700; font-size:38px; line-height:1; color:#f9fdff; text-align:right">'
                f'{esc(s["value"])}{suffix}</div>'
                f'<div style="font-size:13.5px; font-weight:300; color:#a9b4c5; padding-top:4px">{t(s["label"])}</div></div>')
        sep = '<span style="width:1px; background:#ffffff26; display:block; margin:0 20px"></span>'
        stats_html = f"""
  <div style="padding:26px 32px 0">
    <div style="background:#111b32; border-radius:13px; padding:20px 24px 18px; display:flex; align-items:stretch; gap:0">{sep.join(cells)}</div>
  </div>"""

    # ── הזדמנויות ──
    large_imgs = ["img-industry.png", "img-events.png", "img-education.png"]
    large = []
    for i, o in enumerate(opps.get("large") or []):
        large.append(f"""
    <div style="background:#f0f6fa; border-radius:13px; padding:20px 22px; display:flex; gap:18px; align-items:flex-start">
      <div style="flex:1">
        <div style="display:flex; align-items:center; gap:8px; padding-bottom:9px">
          <span style="font-family:'Almoni Tzar'; font-weight:400; font-size:14px; line-height:1.6; color:#111b32; background:#f9fdff; border-radius:3.8rem; padding:0 1rem">{esc(o["type"])}</span>
          <span style="font-size:13px; font-weight:500; color:#d54b63">{esc(o["deadline_label"])}</span>
        </div>
        <div style="font-family:'Almoni Tzar'; font-weight:700; font-size:24px; line-height:1.1; color:#111b32">{esc(o["title"])}</div>
        <div style="font-size:15.5px; font-weight:300; line-height:1.5; color:#4a5464; padding-top:6px">{t(o["desc"])}</div>
        <a href="{esc(o["url"])}" target="_blank" rel="noopener" style="text-decoration:none">{cta(o.get("cta", "לפרטים"))}</a>
      </div>
      <div style="width:104px; height:104px; border-radius:9px; background-image:url('{asset(large_imgs[i % len(large_imgs)])}'); background-size:cover; background-position:center; flex:none"></div>
    </div>""")

    small = []
    for o in (opps.get("small") or [])[:2]:
        small.append(f"""
      <div style="flex:1; background:#f0f6fa; border-radius:13px; padding:18px 20px">
        <div style="font-family:'Almoni Tzar'; font-weight:400; font-size:14px; line-height:1.6; color:#111b32; background:#f9fdff; border-radius:3.8rem; padding:0 1rem; display:inline-block">{esc(o["type"])}</div>
        <div style="font-family:'Almoni Tzar'; font-weight:700; font-size:20px; line-height:1.12; color:#111b32; padding-top:10px">{esc(o["title"])}</div>
        <div style="font-size:14.5px; font-weight:300; line-height:1.45; color:#4a5464; padding-top:5px">{t(o["meta"])}</div>
        <a href="{esc(o["url"])}" target="_blank" rel="noopener" style="text-decoration:none">{cta(o.get("cta", "לפרטים"))}</a>
      </div>""")
    small_html = f'<div style="display:flex; gap:12px">{"".join(small)}</div>' if small else ""

    more = opps.get("more")
    more_html = ""
    if more and more.get("url"):
        more_html = (f'<a href="{esc(more["url"])}" target="_blank" rel="noopener" style="display:flex; align-items:center; justify-content:center; gap:8px; '
                     f'border:1.5px solid #111b32; border-radius:9rem; padding:.55rem 1.25rem; font-family:\'Almoni Tzar\'; '
                     f'font-weight:500; font-size:18px; color:#111b32; text-decoration:none; margin-top:6px">{esc(more["text"])}</a>')

    n_opps = len(opps.get("large") or []) + len(opps.get("small") or [])

    # ── לוח אירועים ──
    events_html = ""
    if events:
        rows = []
        for i, ev in enumerate(events):
            rows.append(f"""
      <a href="{esc(ev["url"])}" target="_blank" rel="noopener" style="display:flex; align-items:center; gap:16px; padding:12px 4px; border-bottom:1px solid #e4eaf0; text-decoration:none">
        <div style="width:52px; text-align:center; flex:none">
          <div style="font-family:'Almoni Tzar'; font-weight:700; font-size:26px; line-height:.95; color:#111b32">{esc(ev["day"])}</div>
          <div style="font-family:'Almoni Tzar'; font-weight:500; font-size:12px; letter-spacing:.14em; color:#67717f">{esc(ev["month_he"])}</div>
        </div>
        <span style="width:1.5px; height:32px; background:{ACCENTS[i % len(ACCENTS)]}; display:block; flex:none"></span>
        <div style="flex:1">
          <div style="font-family:'Almoni Tzar'; font-weight:700; font-size:19px; line-height:1.1; color:#111b32">{esc(ev["title"])}</div>
          <div style="font-size:14px; font-weight:300; color:#67717f; padding-top:2px">{t(ev["meta"])}</div>
        </div>
      </a>""")
        events_html = f"""
  <div style="padding:38px 32px 0">
    <div style="display:flex; align-items:center; gap:12px">
      <span style="font-family:'Almoni Tzar'; font-weight:700; font-size:19px; letter-spacing:.16em; color:#111b32">לוח אירועים · החודש הקרוב</span>
      <span style="flex:1; height:1.5px; background:linear-gradient(to left,#f58220,#d54b63,#3863cea8); display:block"></span>
    </div>
    <div style="padding-top:14px; display:flex; flex-direction:column">{"".join(rows)}</div>
  </div>"""

    # ── חדשות: כתבת מובילה ──
    lead = news["lead"]
    lead_html = f"""
  <div style="padding:22px 32px 0">
    <a href="{esc(lead["url"])}" target="_blank" rel="noopener" style="display:block; border-radius:13px; overflow:hidden; background:#111b32; text-decoration:none">
      <div style="height:230px; background-image:url('{asset('img-vision-home.jpg')}'); background-size:cover; background-position:center"></div>
      <div style="padding:20px 24px 22px">
        <div style="display:flex; align-items:center; gap:7px; padding-bottom:10px">
          <span style="font-family:'Almoni Tzar'; font-weight:400; font-size:13.5px; line-height:1.6; color:#111b32; background:#f9fdff; border-radius:3.8rem; padding:0 .85rem">{esc(lead["scope"])}</span>
          <span style="font-family:'Almoni Tzar'; font-weight:400; font-size:13.5px; line-height:1.6; color:#f9fdff; box-shadow:inset 0 0 0 1.5px #f9fdff; border-radius:3.8rem; padding:0 .85rem">{esc(lead["category"])}</span>
          <span style="font-size:12.5px; font-weight:300; color:#8f9bad">{esc(lead["date"])}</span>
        </div>
        <div style="font-family:'Almoni Tzar'; font-weight:700; font-size:30px; line-height:1.05; color:#f9fdff">{esc(lead["title"])}</div>
        <div style="font-size:15.5px; font-weight:300; line-height:1.5; color:#c3cddc; padding-top:8px">{t(lead["desc"])}</div>
        {cta("לכתבה המלאה", "#f9fdff")}
      </div>
    </a>
  </div>"""

    # ── חדשות: קטגוריות ──
    cats_html = []
    img_i = 0
    for cat in news.get("categories") or []:
        items_html = []
        for j, it in enumerate(cat["items"]):
            img = CATEGORY_IMG.get(cat["name"]) if j == 0 else None
            if not img:
                img = IMG_POOL[img_i % len(IMG_POOL)]
                img_i += 1
            items_html.append(f"""
    <a href="{esc(it["url"])}" target="_blank" rel="noopener" style="display:flex; gap:16px; align-items:flex-start; text-decoration:none">
      <div style="width:136px; height:96px; border-radius:9px; background-image:url('{asset(img)}'); background-size:cover; background-position:center; flex:none"></div>
      <div style="flex:1">
        <div style="display:flex; align-items:center; gap:7px; padding-bottom:5px">
          {scope_chip(it["scope"])}
          <span style="font-size:12.5px; font-weight:300; color:#7d8797">{esc(it["date_source"])}</span>
        </div>
        <div style="font-family:'Almoni Tzar'; font-weight:700; font-size:21px; line-height:1.1; color:#111b32">{esc(it["title"])}</div>
        <div style="font-size:15px; font-weight:300; line-height:1.45; color:#4a5464; padding-top:4px">{t(it["desc"])}</div>
      </div>
    </a>""")
        cats_html.append(f"""
  <div style="padding:30px 32px 0; display:flex; align-items:center; gap:12px">
    <span style="font-family:'Almoni Tzar'; font-weight:700; font-size:19px; letter-spacing:.16em; color:#111b32">{esc(cat["name"])}</span>
    <span style="flex:1; height:1.5px; background:linear-gradient(to left,#f58220,#d54b63,#3863cea8); display:block"></span>
  </div>
  <div style="padding:16px 32px 0; display:flex; flex-direction:column; gap:16px">{"".join(items_html)}</div>""")

    # ── בקצרה ──
    briefs_html = ""
    briefs = news.get("briefs") or []
    if briefs:
        rows = "".join(
            f'<a href="{esc(b["url"])}" target="_blank" rel="noopener" style="font-size:15.5px; font-weight:400; line-height:1.4; color:#111b32; display:flex; gap:9px; align-items:baseline; text-decoration:none">'
            f'<span style="width:6px; height:6px; border-radius:20px; background:#4d77de; display:block; flex:none"></span>{t(b["text"])}</a>'
            for b in briefs)
        briefs_html = f"""
  <div style="padding:28px 32px 0">
    <div style="background:#0c42780d; border-radius:13px; padding:18px 22px">
      <div style="font-family:'Almoni Tzar'; font-weight:700; font-size:16px; letter-spacing:.14em; color:#111b32; padding-bottom:10px">בקצרה</div>
      <div style="display:flex; flex-direction:column; gap:8px">{rows}</div>
    </div>
  </div>"""

    n_news = 1 + sum(len(c["items"]) for c in news.get("categories") or []) + len(briefs)

    if isf_logo_ok():
        isf_strip = (f'<img src="{asset("logo-isf.svg")}" alt="הפורום הישראלי לחלל" '
                     f'style="height:34px; display:block" />')
        isf_footer = ('<span style="width:1px; height:22px; background:#ffffff26; display:block"></span>'
                      f'<img src="{asset("logo-isf.svg")}" alt="הפורום הישראלי לחלל" style="height:26px; display:block" />')
    else:
        isf_strip = ""
        isf_footer = ""

    body = f"""
<div dir="rtl" lang="he" style="background:#dfe7ee; padding:32px 16px 56px; font-family:'Almoni',system-ui,sans-serif; -webkit-font-smoothing:antialiased">

<div style="max-width:640px; margin:0 auto; text-align:center; font-size:12px; color:#67717f; letter-spacing:.02em; padding-bottom:14px">
  הזדמנויות וחדשות תעשיית החלל
</div>

<div style="max-width:640px; margin:0 auto; background:#ffffff; border-radius:20px; overflow:hidden">

  <div style="background:#111b32; display:flex; align-items:center; justify-content:space-between; padding:18px 28px">
    <img src="{asset('logo-rakia-white.png')}" alt="משימת רקיע" style="height:26px; display:block" />
    <div style="display:flex; align-items:center; gap:10px">
      <span style="font-family:'Almoni Tzar'; font-weight:500; font-size:15px; letter-spacing:.18em; color:#f9fdff">ניוזלטר שבועי</span>
      <span style="width:1px; height:16px; background:#ffffff40; display:block"></span>
      <span style="font-size:13px; font-weight:300; color:#aab3c2">גיליון {esc(iss["number"])}</span>
    </div>
  </div>

  <div style="position:relative; height:290px; background-image:url('{asset('img-hero.webp')}'); background-size:cover; background-position:center 35%">
    <div style="position:absolute; inset:0; background:linear-gradient(0deg,#091b43f2 8%,#29468e66 62%,#0a142b73 100%)"></div>
    <div style="position:absolute; inset:0; display:flex; flex-direction:column; justify-content:flex-end; padding:0 32px 26px">
      <div style="display:flex; align-items:center; gap:10px; padding-bottom:10px">
        <span style="font-family:'Almoni Tzar'; font-weight:500; font-size:13px; letter-spacing:.24em; color:#f58220">סיכום השבוע</span>
        <span style="height:1.5px; width:56px; background:linear-gradient(to left,#f58220,#d54b63,#3863cea8); display:block"></span>
      </div>
      <div style="font-family:'Almoni Tzar'; font-weight:700; font-size:52px; line-height:.92; color:#f9fdff; max-width:460px; text-wrap:balance">חדשות והזדמנויות תעשיית החלל</div>
      <div style="font-size:16px; font-weight:300; color:#cfd9e6; padding-top:12px">{esc(iss["date_he"])} &nbsp;·&nbsp; {t(iss["window_he"])}</div>
    </div>
  </div>

  <div style="background:#f0f6fa; padding:22px 32px; display:flex; gap:28px; align-items:flex-start">
    <div style="font-family:'Almoni Tzar'; font-weight:700; font-size:15px; letter-spacing:.16em; color:#111b32; padding-top:3px; white-space:nowrap">במהדורה זו</div>
    <div style="display:flex; flex-direction:column; gap:7px; flex:1">{bullets}</div>
  </div>
{editorial_html}{stats_html}

  <div id="opps" style="padding:44px 32px 8px">
    <div style="display:flex; align-items:flex-end; gap:14px">
      <span style="font-family:'Almoni Tzar'; font-weight:700; font-size:34px; line-height:1; color:#111b32">הזדמנויות השבוע</span>
      <span style="flex:1; height:1.5px; background:#111b32; display:block; margin-bottom:9px"></span>
      <span style="width:6px; height:6px; border-radius:50%; background:#111b32; display:block; margin-bottom:6px"></span>
    </div>
    <div style="font-size:16px; font-weight:300; color:#4a5464; padding-top:8px; max-width:480px">קולות קוראים, אירועים, משלחות, וובינרים והכשרות שפורסמו לתעשיית החלל בשבוע האחרון.</div>
  </div>

  <div style="padding:22px 32px 8px; display:flex; flex-direction:column; gap:12px">{"".join(large)}{small_html}{more_html}
  </div>
{events_html}

  <div id="news" style="padding:44px 32px 0">
    <div style="display:flex; align-items:flex-end; gap:14px">
      <span style="font-family:'Almoni Tzar'; font-weight:700; font-size:34px; line-height:1; color:#111b32">חדשות החלל בשבוע האחרון</span>
      <span style="flex:1; height:1.5px; background:#111b32; display:block; margin-bottom:9px"></span>
      <span style="width:6px; height:6px; border-radius:50%; background:#111b32; display:block; margin-bottom:6px"></span>
    </div>
  </div>
{lead_html}{"".join(cats_html)}{briefs_html}

  <div style="padding:34px 32px 0">
    <div style="background:#f0f6fa; border-radius:13px; padding:18px 24px; display:flex; align-items:center; gap:22px">
      <div style="font-family:'Almoni Tzar'; font-weight:500; font-size:13px; letter-spacing:.16em; color:#67717f; white-space:nowrap">בשיתוף</div>
      <span style="width:1px; height:34px; background:#c9d6e2; display:block"></span>
      <div style="flex:1; display:flex; align-items:center; gap:26px">
        <img src="{asset('logo-minhelet.png')}" alt="מנהלת החלל" style="height:56px; margin:-8px 0; display:block; mix-blend-mode:multiply" />
        {isf_strip}<img src="{asset('logo-rakia-black.png')}" alt="משימת רקיע" style="height:30px; display:block" />
      </div>
    </div>
  </div>

  <div style="margin-top:44px; background:#111b32; padding:38px 32px 30px; position:relative; overflow:hidden">
    <div style="position:absolute; width:15rem; height:15rem; border-radius:50%; background:#3863cea8; filter:blur(90px); top:-90px; left:-60px"></div>
    <div style="position:absolute; width:13rem; height:13rem; border-radius:50%; background:#8245d063; filter:blur(90px); bottom:-110px; right:-40px"></div>
    <div style="position:relative">
      <div style="font-family:'Almoni Tzar'; font-weight:700; font-size:26px; line-height:1.05; color:#f9fdff; max-width:380px">רוצים לקבל את החדשות בקצב אחר?</div>
      <div style="font-size:15px; font-weight:300; color:#b9c4d4; padding-top:7px; max-width:400px">ניתן לעדכן את תדירות הניוזלטר בכל רגע דרך אזור הרישום באתר הפורום.</div>
      <div style="display:flex; gap:9px; padding-top:16px">
        <span style="font-family:'Almoni Tzar'; font-weight:500; font-size:17px; color:#f9fdff; border:1.5px solid #ffffff; border-radius:9rem; padding:.3125rem 1.25rem">יומי · 07:30</span>
        <span style="font-family:'Almoni Tzar'; font-weight:500; font-size:17px; color:#111b32; background:#f9fdff; border:1.5px solid #f9fdff; border-radius:9rem; padding:.3125rem 1.25rem">שבועי · חמישי 17:00</span>
        <span style="font-family:'Almoni Tzar'; font-weight:500; font-size:17px; color:#f9fdff; border:1.5px solid #ffffff; border-radius:9rem; padding:.3125rem 1.25rem">חודשי</span>
      </div>
      <div style="height:1px; background:#ffffff26; margin:28px 0 20px"></div>
      <div style="display:flex; align-items:center; justify-content:space-between; gap:20px">
        <div style="display:flex; align-items:center; gap:18px">
          <img src="{asset('logo-rakia-white.png')}" alt="משימת רקיע" style="height:24px; display:block" />{isf_footer}
        </div>
        <div style="display:flex; align-items:center; gap:10px">
          <a href="https://www.linkedin.com/company/rakia-mission" target="_blank" rel="noopener"><img src="{asset('social-linkedin.png')}" alt="LinkedIn" style="height:20px; display:block; opacity:.85" /></a>
          <a href="https://www.facebook.com/rakiamission" target="_blank" rel="noopener"><img src="{asset('social-facebook.png')}" alt="Facebook" style="height:20px; display:block; opacity:.85" /></a>
          <a href="https://www.instagram.com/rakiamission" target="_blank" rel="noopener"><img src="{asset('social-instagram.png')}" alt="Instagram" style="height:20px; display:block; opacity:.85" /></a>
          <a href="https://www.youtube.com/@rakiamission" target="_blank" rel="noopener"><img src="{asset('social-youtube.png')}" alt="YouTube" style="height:20px; display:block; opacity:.85" /></a>
        </div>
      </div>
      <div style="font-size:12.5px; font-weight:300; line-height:1.6; color:#8794a8; padding-top:20px">
        קיבלתם את המייל הזה משום שנרשמתם לניוזלטר של הפורום הישראלי לחלל, מיסודה של משימת רקיע.<br />
        עדכון העדפות &nbsp;·&nbsp; הסרה מרשימת התפוצה &nbsp;·&nbsp; משימת רקיע (ע״ר), תל אביב
      </div>
    </div>
  </div>

</div>
</div>"""

    head_css = f"""<style>
{fonts_css}
body{{margin:0;padding:0;background:#dfe7ee;font-family:'Almoni',system-ui,sans-serif}}
a{{color:#111b32}}
a:hover{{color:#d54b63}}
</style>"""

    title = f"ניוזלטר שבועי רקיע"
    full = (f"<!DOCTYPE html>\n<html lang=\"he\" dir=\"rtl\">\n<head>\n<meta charset=\"utf-8\">\n"
            f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            f"<title>{title} — גיליון {esc(iss['number'])}</title>\n{head_css}\n</head>\n<body>{body}</body>\n</html>")
    artifact = f"<title>{title}</title>\n{head_css}\n{body}"
    return full, artifact, {"opportunities": n_opps, "news_items": n_news, "events": len(events)}


def main():
    if len(sys.argv) < 2:
        print("usage: python build_newsletter.py content/issue_NNN.json")
        sys.exit(1)
    with open(os.path.join(HERE, sys.argv[1]) if not os.path.isabs(sys.argv[1]) else sys.argv[1],
              encoding="utf-8") as f:
        content = json.load(f)
    num = content["issue"]["number"]
    full, artifact, counts = build(content)
    outdir = os.path.join(HERE, "output")
    os.makedirs(outdir, exist_ok=True)
    p_full = os.path.join(outdir, f"newsletter_{num}_full.html")
    p_art = os.path.join(outdir, f"newsletter_{num}_artifact.html")
    with open(p_full, "w", encoding="utf-8") as f:
        f.write(full)
    with open(p_art, "w", encoding="utf-8") as f:
        f.write(artifact)
    proj_copy = os.path.abspath(os.path.join(HERE, "..", "..", f"ניוזלטר_שבועי_{num}.html"))
    with open(proj_copy, "w", encoding="utf-8") as f:
        f.write(full)
    print(json.dumps({"full": p_full, "artifact": p_art, "project_copy": proj_copy,
                      "counts": counts, "size_kb": round(len(full) / 1024)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
