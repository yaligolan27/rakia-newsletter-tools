# -*- coding: utf-8 -*-
"""
בניית אתר הניוזלטר (לפרסום ב-Vercel דרך GitHub).
מבנה: site/ = ריפו סטטי — index.html (הגיליון האחרון), NNN/index.html (ארכיון),
archive/index.html (רשימת גיליונות), og_NNN.jpg (תמונת preview לוואטסאפ per גיליון).
שימוש:  python build_site.py            ← בונה את כל האתר מהגיליונות שב-content/
הפרסום עצמו (commit+push) נעשה ב-publish_site.py, רק אחרי אישור.
"""
import glob
import html
import json
import os
import re
import shutil

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")
CFG = json.load(open(os.path.join(HERE, "site_config.json"), encoding="utf-8"))
BASE = CFG["base_url"].rstrip("/")

FAVICON = ('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
           '<text y=".9em" font-size="90">🛰️</text></svg>')


def esc(s):
    return html.escape(str(s or ""), quote=True)


def issues():
    """כל הגיליונות לפי content/issue_NNN_v2.json, ממוינים עולה."""
    out = []
    for p in sorted(glob.glob(os.path.join(HERE, "content", "issue_*_v2.json"))):
        c = json.load(open(p, encoding="utf-8"))
        num = c["issue"]["number"]
        built = os.path.join(HERE, "output", f"newsletter_{num}_full.html")
        if os.path.exists(built):
            # כתובת הגיליון באתר = תאריך הגיליון (2026-08-27), לא מספר רץ
            slug = c["issue"].get("date_iso") or num
            out.append({"num": num, "slug": slug, "meta": c["issue"], "html_path": built})
    out.sort(key=lambda i: i["slug"])
    return out


DARK_FROM = "2026-08-27"  # מהגיליון הזה והלאה: שפת העיצוב של הפורום (שחור-כוכבים + גרדיאנט)


def og_image(iss):
    """תמונת preview 1200x630: hero + לוגו + כותרת הגיליון."""
    if iss["slug"] >= DARK_FROM:
        return og_image_dark(iss)
    img = Image.open(os.path.join(HERE, "assets", "img-hero.webp")).convert("RGB")
    w, h = img.size
    target = (1200, 630)
    scale = max(target[0] / w, target[1] / h)
    img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    left = (img.width - target[0]) // 2
    top = int((img.height - target[1]) * 0.35)
    img = img.crop((left, top, left + target[0], top + target[1]))
    shade = Image.new("L", target, 0)
    sd = ImageDraw.Draw(shade)
    for y in range(target[1]):
        sd.line([(0, y), (target[0], y)], fill=int(40 + 160 * (y / target[1]) ** 2))
    img = Image.composite(Image.new("RGB", target, (9, 27, 67)), img, shade.point(lambda v: v))
    d = ImageDraw.Draw(img)
    f_big = ImageFont.truetype(os.path.join(HERE, "assets", "fonts", "almoni-tzar-bold-aaa.otf"), 110)
    f_mid = ImageFont.truetype(os.path.join(HERE, "assets", "fonts", "almoni-regular-aaa.otf"), 44)
    f_small = ImageFont.truetype(os.path.join(HERE, "assets", "fonts", "almoni-tzar-medium-aaa.otf"), 34)

    def rtl(s):
        # Pillow ללא raqm מצייר גליפים בסדר לוגי — לעברית: היפוך מלא, ואז החזרת ריצות ספרות/לטינית
        vis = s[::-1]
        return re.sub(r"[0-9A-Za-z][0-9A-Za-z–.\-]*|[–]", lambda m: m.group(0)[::-1], vis)

    title = "השבוע בחלל"
    d.text((1160, 300), rtl(title), font=f_big, fill=(249, 253, 255), anchor="rs")
    sub = f"ניוזלטר תעשיית החלל · גיליון {iss['num']} · {iss['meta']['window_he']}"
    d.text((1160, 380), rtl(sub), font=f_mid, fill=(207, 217, 230), anchor="rs")
    d.text((1160, 445), rtl("משימת רקיע · הפורום הישראלי לחלל"), font=f_small, fill=(245, 130, 32), anchor="rs")
    logo = Image.open(os.path.join(HERE, "assets", "logo-rakia-white.png")).convert("RGBA")
    lw = 220
    logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    img.paste(logo, (60, 630 - logo.height - 46), logo)
    out = os.path.join(SITE, f"og_{iss['slug']}.jpg")
    img.save(out, "JPEG", quality=85)
    return out


def og_image_dark(iss):
    """og בשפת הפורום: רקע שחור-כוכבים, פס גרדיאנט ירוק→טורקיז→כחול, לוגו הפורום + רקיע."""
    target = (1200, 630)
    stars = Image.open(os.path.join(HERE, "assets", "bg-stars.jpg")).convert("RGB")
    img = stars.resize((1200, 1200), Image.LANCZOS).crop((0, 240, 1200, 870))
    d = ImageDraw.Draw(img)
    # פס גרדיאנט עליון דק
    c1, c2, c3 = (100, 226, 117), (17, 182, 188), (23, 118, 177)
    for x in range(1200):
        p = x / 1199
        if p < .5:
            q = p * 2
            c = tuple(int(c1[i] * (1 - q) + c2[i] * q) for i in range(3))
        else:
            q = (p - .5) * 2
            c = tuple(int(c2[i] * (1 - q) + c3[i] * q) for i in range(3))
        d.line([(x, 0), (x, 7)], fill=c)
    f_big = ImageFont.truetype(os.path.join(HERE, "assets", "fonts", "almoni-tzar-bold-aaa.otf"), 110)
    f_mid = ImageFont.truetype(os.path.join(HERE, "assets", "fonts", "almoni-regular-aaa.otf"), 44)
    f_small = ImageFont.truetype(os.path.join(HERE, "assets", "fonts", "almoni-tzar-medium-aaa.otf"), 34)

    def rtl(s):
        vis = s[::-1]
        return re.sub(r"[0-9A-Za-z][0-9A-Za-z–.\-]*|[–]", lambda m: m.group(0)[::-1], vis)

    # לוגו מנהלת החלל בגדול בצד שמאל (הוסר 31.8, הוחזר 25.9 לבקשת מאיה); הפורום + רקיע קטנים למטה
    isf_big = Image.open(os.path.join(HERE, "assets", "logo-minhelet-dark-bg.png")).convert("RGBA")
    bh = 340
    isf_big = isf_big.resize((int(isf_big.width * bh / isf_big.height), bh), Image.LANCZOS)
    img.paste(isf_big, (95, (630 - bh) // 2), isf_big)
    isf_small = Image.open(os.path.join(HERE, "assets", "logo-isf-light.png")).convert("RGBA")
    sh = 62
    isf_small = isf_small.resize((int(isf_small.width * sh / isf_small.height), sh), Image.LANCZOS)

    d.text((1140, 268), rtl("השבוע בחלל"), font=f_big, fill=(242, 246, 251), anchor="rs")
    # שורת המשנה חייבת להיכנס בין הלוגו (משמאל) לשוליים הימניים — טווח ארוך (כמו
    # "30 באוגוסט עד 5 בספטמבר") גלש על הלוגו בגיליון 004. מקטינים גופן, ואם עדיין
    # לא נכנס — משאירים רק את הטווח.
    max_w = 1140 - (95 + isf_big.width + 30)
    sub = f"ניוזלטר תעשיית החלל · {iss['meta']['window_he']}"
    f_sub = f_mid
    for size in range(44, 29, -2):
        f_sub = ImageFont.truetype(os.path.join(HERE, "assets", "fonts", "almoni-regular-aaa.otf"), size)
        if d.textlength(rtl(sub), font=f_sub) <= max_w:
            break
    else:
        sub = iss['meta']['window_he']
        f_sub = ImageFont.truetype(os.path.join(HERE, "assets", "fonts", "almoni-regular-aaa.otf"), 40)
    d.text((1140, 348), rtl(sub), font=f_sub, fill=(198, 208, 221), anchor="rs")
    d.text((1140, 413), rtl("הפורום הישראלי לחלל · משימת רקיע"), font=f_small, fill=(17, 182, 188), anchor="rs")
    rk = Image.open(os.path.join(HERE, "assets", "logo-rakia-dark-bg.png")).convert("RGBA")
    rh = 62
    rk = rk.resize((int(rk.width * rh / rk.height), rh), Image.LANCZOS)
    img.paste(rk, (1140 - rk.width, 630 - rh - 44), rk)
    img.paste(isf_small, (1140 - rk.width - 34 - isf_small.width, 630 - sh - 44), isf_small)
    out = os.path.join(SITE, f"og_{iss['slug']}.jpg")
    img.save(out, "JPEG", quality=85)
    return out


def with_meta(html_text, iss, canonical):
    """הזרקת תגיות og/canonical/favicon ל-head של גיליון."""
    m = iss["meta"]
    slug = iss["slug"]
    title = f"השבוע בחלל · {m['window_he']}"
    tags = f"""
<link rel="icon" href='{FAVICON}'>
<link rel="canonical" href="{canonical}">
<meta name="description" content="{esc(CFG['site_description'])}">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(CFG['site_description'])}">
<meta property="og:image" content="{BASE}/og_{slug}.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="{canonical}">
<meta property="og:locale" content="he_IL">
<meta name="twitter:card" content="summary_large_image">
"""
    return html_text.replace("</title>", "</title>" + tags, 1)


def redirect_page(target):
    return (f'<!DOCTYPE html><html lang="he"><head><meta charset="utf-8">'
            f'<meta http-equiv="refresh" content="0; url={target}">'
            f'<link rel="canonical" href="{target}">'
            f'<title>מעבר לגיליון</title></head>'
            f'<body><p>הגיליון עבר ל<a href="{target}">{target}</a></p>'
            f'<script>location.replace({json.dumps(target)})</script></body></html>')


def archive_page(all_issues):
    rows = "".join(
        f"""
    <a class="row" href="../{i['slug']}/">
      <span class="num">{esc(i['meta']['date_he'])}</span>
      <span class="win">{esc(i['meta']['window_he'])}</span>
    </a>"""
        for i in reversed(all_issues))
    return f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ארכיון — השבוע בחלל</title>
<link rel="icon" href='{FAVICON}'>
<style>
body{{margin:0;background:#000208;font-family:system-ui,sans-serif;color:#f2f6fb}}
.top{{background:#00040c;border-bottom:1px solid #ffffff1c;color:#f2f6fb;padding:34px 20px;text-align:center}}
.top h1{{margin:0;font-size:34px}}.top p{{margin:8px 0 0;color:#8b98ab}}
.top .bar{{height:4px;width:120px;margin:16px auto 0;border-radius:99px;background:linear-gradient(91deg,#64e275,#11b6bc,#1776b1)}}
.wrap{{max-width:640px;margin:26px auto;padding:0 16px}}
.row{{display:flex;justify-content:space-between;gap:12px;background:#0b1220;border-radius:14px;padding:16px 20px;margin-bottom:10px;text-decoration:none;color:#f2f6fb;border:1px solid #ffffff1c}}
.row:hover{{border-color:#11b6bc88;box-shadow:0 10px 24px #11b6bc22}}
.num{{font-weight:700}}.win{{color:#c6d0dd}}.date{{color:#8b98ab;font-size:14px}}
.back{{display:block;text-align:center;margin:18px 0;color:#11b6bc}}
</style>
</head>
<body>
<div class="top"><h1>השבוע בחלל · ארכיון</h1><p>כל הגיליונות של הניוזלטר השבועי · הפורום הישראלי לחלל</p><div class="bar"></div></div>
<div class="wrap">{rows}
<a class="back" href="../">→ לגיליון האחרון</a>
</div>
</body>
</html>"""


def main():
    os.makedirs(SITE, exist_ok=True)
    all_issues = issues()
    if not all_issues:
        raise SystemExit("לא נמצאו גיליונות בנויים (content/issue_*_v2.json + output/newsletter_*_full.html)")
    latest = all_issues[-1]
    for iss in all_issues:
        num, slug = iss["num"], iss["slug"]
        html_text = open(iss["html_path"], encoding="utf-8").read()
        os.makedirs(os.path.join(SITE, slug), exist_ok=True)
        with open(os.path.join(SITE, slug, "index.html"), "w", encoding="utf-8") as f:
            f.write(with_meta(html_text, iss, f"{BASE}/{slug}/"))
        og_image(iss)
        # כתובות ישנות (/002/) ממשיכות לעבוד — הפניה לכתובת התאריך
        if num != slug:
            os.makedirs(os.path.join(SITE, num), exist_ok=True)
            with open(os.path.join(SITE, num, "index.html"), "w", encoding="utf-8") as f:
                f.write(redirect_page(f"{BASE}/{slug}/"))
    latest_html = open(latest["html_path"], encoding="utf-8").read()
    latest_html = with_meta(latest_html, latest, f"{BASE}/")
    latest_html = latest_html.replace(f'content="{BASE}/og_{latest["slug"]}.jpg"', f'content="{BASE}/og.jpg"', 1)
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write(latest_html)
    shutil.copy(os.path.join(SITE, f"og_{latest['slug']}.jpg"), os.path.join(SITE, "og.jpg"))
    os.makedirs(os.path.join(SITE, "archive"), exist_ok=True)
    with open(os.path.join(SITE, "archive", "index.html"), "w", encoding="utf-8") as f:
        f.write(archive_page(all_issues))
    with open(os.path.join(SITE, "README.md"), "w", encoding="utf-8") as f:
        f.write("# השבוע בחלל — אתר הניוזלטר השבועי של רקיע\n\nנבנה אוטומטית מ-`tools/newsletter/build_site.py`. אל תערכו כאן ידנית.\n")
    print(json.dumps({"site": SITE, "issues": [i["slug"] for i in all_issues], "latest": latest["slug"], "base": BASE}, ensure_ascii=False))


if __name__ == "__main__":
    main()
