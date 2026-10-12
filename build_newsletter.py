# -*- coding: utf-8 -*-
"""
בניית הניוזלטר השבועי — גרסה 3: שפת העיצוב של הפורום הישראלי לחלל (25.8.2026).
שימוש:  python build_newsletter.py content/issue_NNN_v2.json
פלט:    output/newsletter_<num>_full.html + output/newsletter_<num>_artifact.html + עותק בשורש הפרויקט.
שפת עיצוב: israelspaceforum.com — רקע שחור-כוכבים, גרדיאנט ירוק→טורקיז→כחול
(#64E275→#11B6BC→#1776B1), Almoni. לוגואים בטופבר (מימין לשמאל): הפורום, מפא"ת, רקיע, ספייס קמפוס.
מבנה: הירו (+כפתור קיצור לחדשות) → סטטיסטיקות → אירועי הפורום (עד שתאריכם עובר) →
הזדמנויות → לוח אירועים → חדשות → סרטונים. אין "דבר המערכת" (הוסר לפי משוב 25.8).
"""
import base64
import html
import json
import os
import re
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
FONTS = os.path.join(ASSETS, "fonts")

MIME = {".otf": "font/otf", ".webp": "image/webp", ".png": "image/png",
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml"}


def data_uri(path):
    ext = os.path.splitext(path)[1].lower()
    with open(path, "rb") as f:
        return f"data:{MIME[ext]};base64,{base64.b64encode(f.read()).decode('ascii')}"


def esc(s):
    return html.escape(str(s or ""), quote=True)


def t(s):
    """esc + עטיפת טווחי מספרים ב-LTR נגד היפוך bidi."""
    return re.sub(r"(\d[\d.,:]*\s?[–-]\s?\d[\d.,:]*)", r'<span dir="ltr">\1</span>', esc(s))


def il_time(net_iso):
    """מועד ISO (UTC, Z) → 'DD.MM · HH:MM' בשעון ישראל (fallback: UTC+3 אם אין tzdata)."""
    from datetime import datetime, timezone, timedelta
    dt = datetime.fromisoformat(net_iso.replace("Z", "+00:00"))
    try:
        from zoneinfo import ZoneInfo
        loc = dt.astimezone(ZoneInfo("Asia/Jerusalem"))
    except Exception:
        loc = dt.astimezone(timezone(timedelta(hours=3)))
    return loc.strftime("%d.%m · %H:%M")


CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#000208; --surf:#0b1220; --surf2:#101a2c;
  --tx:#f2f6fb; --tx2:#c6d0dd; --mut:#96a3b6; --mut2:#a7b3c4;
  --line:#ffffff1c;
  --g1:#64e275; --g2:#11b6bc; --g3:#1776b1;
  --grad:linear-gradient(91deg,#64e275,#11b6bc,#1776b1);
}
html{scroll-behavior:smooth;scroll-padding-top:82px}
body{background:var(--bg);color:var(--tx);font-family:'Almoni',system-ui,sans-serif;-webkit-font-smoothing:antialiased}
/* רקע הכוכבים קבוע: נשאר במקום בזמן הגלילה, רק התוכן זז (עובד גם במובייל, בלי background-attachment) */
body::before{content:"";position:fixed;inset:0;z-index:-1;background:var(--bg) var(--stars) repeat;background-size:700px auto;pointer-events:none}
a{color:inherit;text-decoration:none}
img{max-width:100%;display:block}
.wrap{max-width:1140px;margin:0 auto;padding-inline:clamp(16px,4vw,40px)}
.tzar{font-family:'Almoni Tzar','Almoni',sans-serif}
.gtx{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}

/* ── topbar ── */
.topbar{position:sticky;top:0;z-index:50;background:#000208e8;backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.topbar .wrap{display:flex;align-items:center;justify-content:space-between;gap:14px;padding-block:10px}
.brand{display:flex;align-items:center;gap:15px;min-width:0}
.brand .sep{width:1px;height:26px;background:var(--line)}
.brand img.lg-isf,.brand img.lg-min,.brand img.lg-rakia,.brand img.lg-cam{height:36px}
.brand img.lg-min{height:46px}
.foot-partners img[alt="מנהלת החלל"]{height:44px}
.issue-tag{display:flex;align-items:center;gap:10px;font-size:13.5px;color:var(--mut);white-space:nowrap}
.issue-tag b{font-family:'Almoni Tzar';font-weight:700;font-size:15px;letter-spacing:.14em;color:var(--tx)}
.issue-tag a.archive-link{border:1px solid #ffffff42;border-radius:99px;padding:2px 12px;font-size:12.5px;color:var(--tx2);transition:border-color .2s,color .2s}
.issue-tag a.archive-link:hover{border-color:#11b6bc;color:#4fd6c0}
@media(max-width:760px){
  .brand{gap:9px}
  .brand img.lg-isf,.brand img.lg-min,.brand img.lg-rakia,.brand img.lg-cam{height:25px}
  .brand img.lg-min{height:32px}
  .issue-tag{gap:7px;font-size:12px}
  .issue-tag b{font-size:13px;letter-spacing:.08em}
  .issue-tag span.date{display:none}
}
@media(max-width:560px){.issue-tag span{display:none}}

/* ── hero ── */
.hero{position:relative;min-height:clamp(440px,70vh,660px);display:flex;align-items:flex-end;overflow:hidden;background:#000208}
.hero-bg{position:absolute;inset:0;background-size:cover;background-position:center 30%;animation:kb 16s ease-out forwards}
@keyframes kb{from{transform:scale(1.08)}to{transform:scale(1)}}
.hero-shade{position:absolute;inset:0;background:linear-gradient(0deg,#000208 4%,#00060fb0 55%,#00030a55 100%)}
.hero-in{position:relative;width:100%;padding-block:clamp(30px,6vh,58px)}
.kicker{display:flex;align-items:center;gap:12px;font-family:'Almoni Tzar';font-weight:500;font-size:14px;letter-spacing:.24em;color:#4fd6c0}
.kicker::after{content:"";height:1.5px;width:64px;background:var(--grad)}
.hero h1{font-family:'Almoni Tzar';font-weight:700;font-size:clamp(52px,9vw,96px);line-height:.9;color:var(--tx);margin-top:14px;text-wrap:balance}
.hero p{font-size:clamp(16px,2.2vw,20px);font-weight:300;color:var(--tx2);margin-top:14px;max-width:620px;line-height:1.55}
.hero .range{margin-top:16px;font-family:'Almoni Tzar';font-weight:700;font-size:clamp(24px,3.8vw,36px);line-height:1;background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero .date{margin-top:7px;font-size:15px;color:var(--mut);font-weight:300}
.hero-nav{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}
.btn-news{display:inline-flex;align-items:center;gap:10px;background:var(--grad);color:#021018;font-family:'Almoni Tzar';font-weight:700;font-size:18px;border-radius:99px;padding:.55rem 1.5rem;box-shadow:0 10px 34px #11b6bc3d;transition:transform .22s,box-shadow .22s}
.btn-news:hover{transform:translateY(3px);box-shadow:0 6px 22px #11b6bc55}
.btn-news .ar{font-size:20px;line-height:1;transform:translateY(1px)}
.btn-sec{display:inline-flex;align-items:center;border:1.5px solid #ffffff55;border-radius:99px;padding:.5rem 1.25rem;font-family:'Almoni Tzar';font-weight:500;font-size:17px;color:var(--tx);background:#00020866;transition:border-color .2s,color .2s;cursor:pointer}
.btn-sec:hover{border-color:#11b6bc;color:#4fd6c0}

/* ── share + floating buttons ── */
.share-wrap{position:relative;display:inline-flex}
.share-menu{display:none;position:absolute;bottom:calc(100% + 10px);inset-inline-start:0;z-index:40;background:var(--surf2);border:1px solid var(--line);border-radius:14px;padding:8px;min-width:210px;box-shadow:0 18px 44px #000000cc;flex-direction:column}
.fabs{position:fixed;bottom:18px;inset-inline-end:18px;z-index:60;display:flex;flex-direction:column;gap:10px;opacity:0;visibility:hidden;transform:translateY(10px);transition:opacity .3s,transform .3s,visibility .3s}
.fabs.show{opacity:1;visibility:visible;transform:none}
.fab{display:flex;align-items:center;justify-content:center;width:52px;height:52px;border-radius:50%;border:none;cursor:pointer;box-shadow:0 10px 28px #000000aa;transition:transform .2s,box-shadow .2s}
.fab:hover{transform:translateY(-3px);box-shadow:0 14px 34px #11b6bc44}
.fab svg{display:block}
.fab-share{background:var(--grad);color:#021018}
.fab-home{background:#0b1220f2;color:var(--tx);border:1.5px solid #ffffff33;backdrop-filter:blur(8px)}
.fabs .share-menu{inset-inline-start:auto;inset-inline-end:0}
@media(max-width:560px){.fabs{bottom:14px;inset-inline-end:12px}.fab{width:48px;height:48px}}
.share-menu.open{display:flex}
.share-menu a,.share-menu button{display:block;width:100%;text-align:start;font-family:'Almoni',sans-serif;font-size:15px;font-weight:400;color:var(--tx);padding:9px 12px;border-radius:9px;background:transparent;border:none;cursor:pointer;transition:background .15s}
.share-menu a:hover,.share-menu button:hover{background:#ffffff14}
.share-menu .wa{font-weight:700;background:#ffffff0d}
.share-cta{margin-bottom:20px}
.share-cta b{font-family:'Almoni Tzar';font-weight:700;font-size:17px;letter-spacing:.06em;display:block;margin-bottom:10px}
.share-row{display:flex;gap:8px;flex-wrap:wrap}
.sh{display:inline-flex;align-items:center;border:1.5px solid #ffffff42;border-radius:99px;padding:.28rem 1rem;font-family:'Almoni Tzar';font-weight:500;font-size:15.5px;color:var(--tx);background:transparent;cursor:pointer;transition:border-color .2s,color .2s}
.sh:hover{border-color:#11b6bc;color:#4fd6c0}
.sh-wa{background:var(--grad);color:#021018;border-color:transparent;font-weight:700}
.sh-wa:hover{color:#021018;opacity:.92}

/* ── section headers ── */
section{padding-block:clamp(34px,6vw,64px)}
.sec-head{display:flex;align-items:flex-end;gap:16px;margin-bottom:10px}
.sec-head h2{font-family:'Almoni Tzar';font-weight:700;font-size:clamp(30px,4.5vw,42px);line-height:1;color:var(--tx)}
.sec-head .rule{flex:1;height:1.5px;background:var(--grad);opacity:.7;margin-bottom:10px}
.sec-head .dot{width:7px;height:7px;border-radius:50%;background:var(--grad);margin-bottom:7px}
.sec-sub{font-size:16.5px;font-weight:300;color:var(--mut2);max-width:560px;margin-bottom:26px}

/* ── stats ── */
.stats{background:#020a14d9;border-block:1px solid var(--line);padding-block:clamp(26px,4vw,40px)}
.stats .wrap{display:grid;grid-template-columns:repeat(3,1fr);gap:clamp(16px,3vw,40px)}
.stat{border-inline-start:1.5px solid #ffffff1f;padding-inline-start:clamp(14px,2vw,24px)}
.stat:first-child{border:none;padding-inline-start:0}
.stat b{font-family:'Almoni Tzar';font-weight:700;font-size:clamp(34px,5vw,52px);line-height:1;display:block;direction:ltr;text-align:right;background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.stat b small{font-size:.55em}
.stat span{display:block;margin-top:6px;font-size:14px;font-weight:300;color:var(--mut2);line-height:1.4}
@media(max-width:720px){.stats .wrap{grid-template-columns:1fr;gap:18px}.stat{border-inline-start:none;border-top:1px solid #ffffff1f;padding:14px 0 0}.stat:first-child{border:none;padding-top:0}}

/* ── forum events (הבלוק העליון) ── */
.forum{background:transparent}
.forum .fe-brand{display:flex;align-items:center;gap:14px;margin-bottom:8px}
.forum .fe-brand img{height:52px}
.fe-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
@media(max-width:980px){.fe-grid{grid-template-columns:1fr 1fr}}
@media(max-width:640px){.fe-grid{grid-template-columns:1fr}}
.fe{background:var(--surf);border:1px solid var(--line);border-radius:18px;overflow:hidden;display:flex;flex-direction:column;transition:transform .25s,box-shadow .3s,border-color .3s}
.fe:hover{transform:translateY(-4px);box-shadow:0 18px 40px #11b6bc22;border-color:#11b6bc66}
.fe-img{aspect-ratio:16/9;background-size:cover;background-position:center}
.fe-tx{padding:16px 18px 18px;display:flex;flex-direction:column;gap:8px;flex:1}
.fe-date{font-family:'Almoni Tzar';font-weight:700;font-size:14px;letter-spacing:.04em;background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.fe h3{font-family:'Almoni Tzar';font-weight:700;font-size:20.5px;line-height:1.1;color:var(--tx)}
.fe p{font-size:14.5px;font-weight:300;line-height:1.5;color:var(--tx2)}
.fe .place{font-size:13.5px;color:var(--mut)}
.btn-g{display:inline-flex;align-items:center;gap:8px;align-self:flex-start;margin-top:auto;background:var(--grad);color:#021018;font-family:'Almoni Tzar';font-weight:700;font-size:15.5px;border-radius:99px;padding:.32rem 1.1rem;transition:transform .2s,box-shadow .2s}
.btn-g:hover{transform:translateY(-2px);box-shadow:0 8px 24px #11b6bc44}

/* ── opportunities ── */
.opps{background:transparent}
.opps-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:860px){.opps-grid{grid-template-columns:1fr}}
.opp{background:var(--surf);border:1px solid var(--line);border-radius:18px;padding:24px;display:flex;flex-direction:column;gap:10px;transition:transform .25s,box-shadow .25s,border-color .3s}
.opp:hover{transform:translateY(-3px);box-shadow:0 14px 34px #11b6bc1c;border-color:#11b6bc55}
.opp-top{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.chip{font-family:'Almoni Tzar';font-weight:500;font-size:14px;line-height:1.6;background:#ffffff12;color:var(--tx2);border-radius:99px;padding:0 1rem}
.deadline{font-size:13.5px;font-weight:600;color:var(--g1)}
.opp h3{font-family:'Almoni Tzar';font-weight:700;font-size:clamp(21px,2.6vw,25px);line-height:1.12;color:var(--tx)}
.opp p{font-size:15.5px;font-weight:300;line-height:1.55;color:var(--tx2)}
.opp .meta{font-size:14.5px;font-weight:300;color:var(--mut2)}
.cta{display:inline-flex;align-items:center;gap:8px;font-size:14.5px;font-weight:600;margin-top:auto;padding-top:6px;color:var(--tx)}
.cta::after{content:"";width:26px;height:1.5px;background:var(--grad);transition:width .25s}
.opp:hover .cta::after{width:44px}
#opps-extra{display:none;flex-direction:column;gap:10px;margin-top:12px}
#opps-extra.open{display:flex}
.oppx{display:flex;align-items:center;gap:14px;background:var(--surf);border:1px solid var(--line);border-radius:13px;padding:14px 20px;transition:transform .2s,border-color .25s}
.oppx:hover{transform:translateY(-2px);border-color:#11b6bc55}
.oppx .chip{flex:none}
.oppx b{font-family:'Almoni Tzar';font-weight:700;font-size:17.5px;line-height:1.15;color:var(--tx)}
.oppx span{font-size:13.5px;font-weight:300;color:var(--mut)}
.oppx::after{content:"←";margin-inline-start:auto;font-weight:600;color:var(--g2)}
.opps-more{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;border:1.5px solid #ffffff4d;border-radius:99px;padding:.5rem 1.2rem;font-family:'Almoni Tzar';font-weight:500;font-size:17px;color:var(--tx);background:transparent;cursor:pointer;margin-top:14px;transition:.2s}
.opps-more:hover{border-color:#11b6bc;color:#4fd6c0}
@media(max-width:720px){.oppx{flex-wrap:wrap;gap:8px}.oppx::after{display:none}}

/* ── events (לוח בינלאומי) ── */
.events{background:transparent}
.ev-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}
@media(max-width:640px){.ev-grid{grid-template-columns:1fr}}
.ev{background:var(--surf);border:1px solid var(--line);border-radius:16px;padding:20px;display:flex;gap:16px;align-items:center;transition:transform .25s,border-color .3s}
.ev:hover{transform:translateY(-3px);border-color:#11b6bc55}
.ev-date{text-align:center;flex:none;min-width:54px}
.ev-date b{font-family:'Almoni Tzar';font-weight:700;font-size:30px;line-height:.9;display:block;color:var(--tx)}
.ev-date span{font-family:'Almoni Tzar';font-weight:500;font-size:12.5px;letter-spacing:.14em;color:var(--mut)}
.ev-bar{width:2px;height:44px;border-radius:2px;flex:none}
.ev h3{font-family:'Almoni Tzar';font-weight:700;font-size:18.5px;line-height:1.12;color:var(--tx)}
.ev p{font-size:13.5px;font-weight:300;color:var(--mut);margin-top:3px}
.ev-static{cursor:default}
.ev.ev-static:hover,.fe.ev-static:hover{transform:none;border-color:var(--line);box-shadow:none}

/* ── news ── */
.lead-card{display:grid;grid-template-columns:1.15fr 1fr;background:linear-gradient(120deg,#0b3438 0%,#082030 48%,#0b1220 100%);border:1px solid var(--line);border-radius:20px;overflow:hidden;color:var(--tx);margin-bottom:26px;transition:transform .25s,box-shadow .3s}
.lead-card:hover{transform:translateY(-3px);box-shadow:0 18px 44px #11b6bc26}
.lead-img{display:block;min-height:280px;background-size:cover;background-position:center}
.lead-tx{padding:clamp(20px,3vw,34px);display:flex;flex-direction:column;gap:12px}
.lead-tx .row{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.chip-inv{font-family:'Almoni Tzar';font-size:13.5px;line-height:1.6;border-radius:99px;padding:0 .85rem;background:var(--grad);color:#021018;font-weight:700}
.chip-line{font-family:'Almoni Tzar';font-size:13.5px;line-height:1.6;border-radius:99px;padding:0 .85rem;box-shadow:inset 0 0 0 1.5px #ffffff88;color:var(--tx)}
.lead-tx .src{font-size:12.5px;font-weight:300;color:var(--mut)}
.lead-tx h3{font-family:'Almoni Tzar';font-weight:700;font-size:clamp(26px,3.4vw,34px);line-height:1.04}
.lead-tx p{font-size:16px;font-weight:300;line-height:1.55;color:var(--tx2)}
.lead-tx p.more-p{font-size:15px;color:var(--mut2)}
@media(max-width:860px){.lead-card{grid-template-columns:1fr}.lead-img{min-height:220px}}

.filters{display:flex;gap:8px;flex-wrap:nowrap;overflow-x:auto;padding-block:6px 20px;-ms-overflow-style:none;scrollbar-width:none}
.filters::-webkit-scrollbar{display:none}
.fbtn{font-family:'Almoni Tzar';font-weight:500;font-size:16px;border:1.5px solid #ffffff42;border-radius:99px;padding:.3rem 1.1rem;background:transparent;color:var(--tx2);cursor:pointer;white-space:nowrap;transition:.2s}
.fbtn:hover{border-color:#11b6bc;color:#4fd6c0}
.fbtn.on{background:var(--grad);border-color:transparent;color:#021018;font-weight:700}

.news-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:860px){.news-grid{grid-template-columns:1fr}}
.card{background:var(--surf);border:1px solid var(--line);border-radius:18px;overflow:hidden;display:flex;flex-direction:column;transition:transform .25s,box-shadow .3s,border-color .3s}
.card:hover{transform:translateY(-4px);box-shadow:0 16px 38px #11b6bc1f;border-color:#11b6bc55}
.card.hide{display:none}
.card-img{aspect-ratio:16/9;background-size:cover;background-position:center}
.card-tx{padding:18px 20px 20px;display:flex;flex-direction:column;gap:8px;flex:1}
.card .row{display:flex;align-items:center;gap:7px;flex-wrap:wrap}
.tag-il{font-family:'Almoni Tzar';font-size:13px;line-height:1.6;border-radius:99px;padding:0 .8rem;background:var(--grad);color:#021018;font-weight:700}
.tag{font-family:'Almoni Tzar';font-size:13px;line-height:1.6;border-radius:99px;padding:0 .8rem;background:#ffffff12;color:var(--tx2)}
.card .src{font-size:12.5px;font-weight:300;color:var(--mut)}
.card h3{font-family:'Almoni Tzar';font-weight:700;font-size:21px;line-height:1.1;color:var(--tx)}
.card .teaser{font-size:15px;font-weight:400;line-height:1.5;color:var(--tx2)}
.card .more-p{font-size:14.5px;font-weight:300;line-height:1.55;color:var(--mut2)}
.card .goto{display:inline-flex;align-items:center;gap:7px;font-size:14px;font-weight:600;margin-top:auto;padding-top:10px;color:var(--tx)}
.card .goto::after{content:"←";transition:transform .2s;color:var(--g2)}
.card:hover .goto::after{transform:translateX(-4px)}

/* ── upcoming launches countdown ── */
.launches{padding-block:clamp(34px,5vw,56px)}
.ln-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}
@media(max-width:560px){.ln-grid{display:flex;overflow-x:auto;gap:12px;padding-bottom:6px;-ms-overflow-style:none;scrollbar-width:none}.ln-grid::-webkit-scrollbar{display:none}.ln{flex:0 0 80%}}
.ln{display:flex;flex-direction:column;gap:10px;background:var(--surf);border:1px solid var(--line);border-radius:18px;padding:18px 18px 20px;color:var(--tx);transition:transform .25s,box-shadow .3s,border-color .3s}
.ln:hover{transform:translateY(-4px);box-shadow:0 16px 38px #11b6bc1f;border-color:#11b6bc55}
.ln.feat{background:linear-gradient(120deg,#0b3438 0%,#082030 48%,#0b1220 100%)}
.ln-top{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.ln-top .ln-when{margin-inline-start:auto}
.ln-st{font-family:'Almoni Tzar';font-size:13px;line-height:1.6;border-radius:99px;padding:0 .8rem;font-weight:700;white-space:nowrap}
.st-go,.st-success{background:var(--grad);color:#021018}
.st-tbc,.st-in-flight{box-shadow:inset 0 0 0 1.5px #f2c14e;color:#f2c14e}
.st-tbd,.st-hold{box-shadow:inset 0 0 0 1.5px #ffffff66;color:var(--tx2)}
.st-failure,.st-partial{box-shadow:inset 0 0 0 1.5px #ff8a8a;color:#ff8a8a}
.st-auto{box-shadow:inset 0 0 0 1.5px #ffffff33;color:var(--mut)}
.ln-when{font-size:12.5px;font-weight:300;color:var(--mut);white-space:nowrap}
.ln-cd{display:flex;gap:6px;direction:ltr;justify-content:flex-end}
.cd-u{display:flex;flex-direction:column;align-items:center;min-width:54px;background:#ffffff0a;border:1px solid #ffffff14;border-radius:12px;padding:8px 6px 6px}
.cd-u b{font-family:'Almoni Tzar';font-weight:700;font-size:30px;line-height:1;background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent;font-variant-numeric:tabular-nums}
.cd-u i{font-style:normal;font-size:11.5px;color:var(--mut);margin-top:3px}
.ln-past{display:none;font-family:'Almoni Tzar';font-weight:700;font-size:18px;color:#4fd6c0;padding:10px 0}
.ln.past .ln-cd{display:none}.ln.past .ln-past{display:block}
.ln h3{font-family:'Almoni Tzar';font-weight:700;font-size:20px;line-height:1.1}
.ln-pay{font-size:14px;font-weight:300;line-height:1.5;color:var(--tx2)}
.ln-meta{font-size:13px;font-weight:400;color:var(--mut);margin-top:auto;padding-top:4px}
.ln-foot{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-top:14px;font-size:13px;color:var(--mut)}
.ln-foot a{color:#4fd6c0;font-weight:600}

/* ── briefs ── */
.briefs{background:#ffffff08;border:1px solid var(--line);border-radius:18px;padding:22px 26px;margin-top:26px}
.briefs b{font-family:'Almoni Tzar';font-weight:700;font-size:16px;letter-spacing:.14em;display:block;margin-bottom:12px}
.briefs a{display:flex;gap:10px;align-items:baseline;font-size:15.5px;line-height:1.45;padding-block:5px;transition:color .2s}
.briefs a:hover{color:#4fd6c0}
.briefs a::before{content:"";width:6px;height:6px;border-radius:50%;background:var(--grad);flex:none;transform:translateY(-2px)}

/* ── videos ── */
.videos{background:transparent;color:var(--tx)}
.vid-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
@media(max-width:860px){.vid-grid{grid-template-columns:1fr}}
.vid{border-radius:16px;overflow:hidden;background:var(--surf);border:1px solid var(--line);transition:transform .25s,border-color .3s}
.vid:hover{transform:translateY(-4px);border-color:#11b6bc55}
.vid-th{position:relative;aspect-ratio:16/9;background-size:cover;background-position:center}
.vid-th::after{content:"";position:absolute;inset:0;background:#00020844;transition:background .25s}
.vid:hover .vid-th::after{background:#0002081a}
.play{position:absolute;inset:0;margin:auto;width:58px;height:58px;border-radius:50%;background:#f2f6fbe8;z-index:2;display:flex;align-items:center;justify-content:center;transition:transform .25s}
.vid:hover .play{transform:scale(1.12)}
.play::before{content:"";border-style:solid;border-width:10px 0 10px 16px;border-color:transparent transparent transparent #021018;margin-left:-3px}
.vid-tx{padding:16px 18px 18px}
.vid-tx h3{font-family:'Almoni Tzar';font-weight:700;font-size:18px;line-height:1.15;color:var(--tx)}
.vid-tx p{font-size:13px;font-weight:300;color:var(--mut);margin-top:5px}

/* ── footer ── */
footer{background:#00040c;color:var(--tx);position:relative;overflow:hidden;border-top:1px solid var(--line)}
.blob{position:absolute;border-radius:50%;filter:blur(90px)}
.blob.b1{width:16rem;height:16rem;background:#11b6bc44;top:-100px;left:-70px}
.blob.b2{width:14rem;height:14rem;background:#1776b14d;bottom:-120px;right:-50px}
.foot-in{position:relative;padding-block:clamp(30px,5vw,48px)}
.foot-top{display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap}
.foot-top img.f-isf,.foot-top img.f-rakia{height:32px}
.foot-brand{display:flex;align-items:center;gap:16px}
.foot-links{display:flex;gap:18px;font-size:14.5px}
.foot-links a{color:var(--tx2);transition:color .2s}
.foot-links a:hover{color:#4fd6c0}
.socials{display:flex;gap:12px}
.socials img{height:20px;opacity:.85;transition:opacity .2s,transform .2s}
.socials a:hover img{opacity:1;transform:translateY(-2px)}
.foot-line{height:1px;background:var(--line);margin-block:22px}
.foot-partners{display:flex;align-items:center;gap:18px;flex-wrap:wrap;margin-bottom:18px}
.foot-partners span{font-size:12.5px;letter-spacing:.06em;color:var(--mut)}
.foot-partners img{height:28px;opacity:.9}
@media(max-width:720px){.foot-partners{gap:12px}.foot-partners img{height:22px}}
.legal{font-size:12.5px;font-weight:300;line-height:1.7;color:var(--mut)}

/* ── mobile polish ── */
@media(max-width:560px){
  .hero{min-height:clamp(430px,74vh,560px)}
  .hero h1{font-size:44px}
  .hero p{font-size:15.5px;line-height:1.6}
  .hero .range{font-size:23px}
  .hero-nav{gap:8px;margin-top:18px;flex-wrap:nowrap;overflow-x:auto;padding-bottom:6px;-ms-overflow-style:none;scrollbar-width:none}
  .hero-nav::-webkit-scrollbar{display:none}
  .btn-news,.btn-sec{font-size:14.5px;padding:.4rem .95rem;flex:none;white-space:nowrap}
  .sec-head h2{font-size:27px}
  .sec-sub{font-size:15px}
  .lead-tx{padding:18px}
  .lead-tx h3{font-size:24px}
  .card-tx{padding:15px 16px 17px}
  .card h3{font-size:19.5px}
  .fe-tx{padding:14px 15px 16px}
  .opp{padding:19px}
  .ev{padding:16px;gap:12px}
}

/* ── reveal animation ── */
.rv{opacity:0;transform:translateY(26px);transition:opacity .7s ease,transform .7s ease}
.rv.in{opacity:1;transform:none}
@media(prefers-reduced-motion:reduce){
  *{animation:none!important;transition:none!important}
  .rv{opacity:1;transform:none}
}
"""

JS = """
(function(){
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var hasIO = 'IntersectionObserver' in window;
  if(!hasIO){ document.querySelectorAll('.rv').forEach(function(el){ el.classList.add('in'); }); }
  // reveal on scroll
  var io = hasIO && new IntersectionObserver(function(es){
    es.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); } });
  }, {threshold:.12});
  if(io) document.querySelectorAll('.rv').forEach(function(el){ io.observe(el); });
  // stat count-up
  function countUp(el){
    var raw = el.getAttribute('data-n'); var target = parseFloat(raw.replace(/,/g,''));
    if(reduce || isNaN(target)){ return; }
    var t0 = null, dur = 1200;
    function fmt(v){ return raw.indexOf(',')>-1 ? Math.round(v).toLocaleString('en-US') : String(Math.round(v)); }
    function step(ts){ if(!t0) t0=ts; var p=Math.min(1,(ts-t0)/dur); p=1-Math.pow(1-p,3);
      el.firstChild.nodeValue = fmt(target*p); if(p<1) requestAnimationFrame(step); }
    requestAnimationFrame(step);
  }
  var so = hasIO && new IntersectionObserver(function(es){
    es.forEach(function(e){ if(e.isIntersecting){ countUp(e.target); so.unobserve(e.target); } });
  }, {threshold:.5});
  if(so) document.querySelectorAll('.stat b[data-n]').forEach(function(el){ so.observe(el); });
  // launch countdown: ticks locally; on the live site it also refreshes NET/status from /api/launches
  var lnSec = document.getElementById('launches');
  if (lnSec) {
    var fmtIL = new Intl.DateTimeFormat('he-IL', {timeZone:'Asia/Jerusalem', day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit', hour12:false});
    var STH = {Go:'אושר לשיגור', TBC:'ממתין לאישור', TBD:'מועד לא סופי', Hold:'מושהה', Success:'שוגר בהצלחה', Failure:'השיגור נכשל', Partial:'הצלחה חלקית', 'In Flight':'בטיסה', Auto:'עדכון אוטומטי'};
    var HEB = {'Falcon 9 Block 5':'פאלקון 9','Falcon 9':'פאלקון 9','Falcon Heavy':'פאלקון הבי','Starship':'סטארשיפ','Starship V3':'סטארשיפ','Electron':'אלקטרון','Neutron':'ניוטרון','Ariane 64 Block 2':'אריאן 6','Ariane 62 Block 2':'אריאן 6','Vega-C':'וגה-C','Vulcan VC2S':'וולקן','Vulcan VC4S':'וולקן','New Glenn':'ניו גלן','Atlas V 551':'אטלס 5','Soyuz 2.1b':'סויוז 2.1b','Soyuz 2.1a':'סויוז 2.1a','H3-22':'H3','PSLV-XL':'PSLV','GSLV Mk III':'LVM3','KSLV-2 Nuri':'נורי','SpaceX':'SpaceX','Rocket Lab':'רוקט לאב','Arianespace':'אריאנספייס','United Launch Alliance':'ULA','Blue Origin':'בלו אוריג׳ין','Russian Federal Space Agency (ROSCOSMOS)':'רוסקוסמוס','Indian Space Research Organization':'ISRO','Japan Aerospace Exploration Agency':'JAXA','Korea Aerospace Research Institute':'KARI','China Aerospace Science and Technology Corporation':'CASC','Cape Canaveral SFS, FL, USA':'קייפ קנוורל, פלורידה','Kennedy Space Center, FL, USA':'מרכז קנדי, פלורידה','Vandenberg SFB, CA, USA':'ונדנברג, קליפורניה','SpaceX Starbase, TX, USA':'סטארבייס, טקסס','Rocket Lab Launch Complex 1, Mahia Peninsula, New Zealand':'מאהיה, ניו זילנד','Guiana Space Centre, French Guiana':'קורו, גיאנה הצרפתית','Baikonur Cosmodrome, Republic of Kazakhstan':'בייקונור','Plesetsk Cosmodrome, Russian Federation':'פלסצק','Tanegashima Space Center, Japan':'טנגשימה, יפן','Satish Dhawan Space Centre, India':'סריהריקוטה, הודו','Naro Space Center, South Korea':'נארו, דרום קוריאה'};
    var TYPE = {Communications:'לווייני תקשורת','Earth Science':'תצפית על כדור הארץ','Government/Top Secret':'מטען ממשלתי מסווג','Human Exploration':'טיסה מאוישת','Dedicated Rideshare':'שיגור שיתוף','Test Flight':'טיסת ניסוי',Navigation:'ניווט',Resupply:'אספקה לתחנת חלל','Planetary Science':'חקר כוכבי לכת',Astrophysics:'אסטרופיזיקה','Technology':'הדגמת טכנולוגיה'};
    function heb(s){ return HEB[s] || s || ''; }
    function pad2(n){ return (n<10?'0':'')+n; }
    function whenIL(d){ return fmtIL.format(d).replace(',', ' ·') + ' שעון ישראל'; }
    function paint(el){
      var net = new Date(el.getAttribute('data-net')), st = el.getAttribute('data-status') || 'TBD';
      var when = el.querySelector('.ln-when'); if (when) when.textContent = whenIL(net);
      var sb = el.querySelector('.ln-st'); if (sb && st !== 'Auto') { sb.textContent = STH[st] || st; sb.className = 'ln-st st-' + st.toLowerCase().replace(/[^a-z]+/g,'-'); }
      var diff = net - Date.now(), b = el.querySelectorAll('.cd-u b');
      if (diff <= 0 || /Success|Failure|Partial|In Flight/.test(st)) {
        el.classList.add('past');
        var lbl = el.querySelector('.ln-past'); if (lbl) lbl.textContent = /Success|Failure|Partial/.test(st) ? STH[st] : 'המועד עבר, לעדכון החי ←';
        return;
      }
      el.classList.remove('past');
      b[0].textContent = pad2(Math.floor(diff/864e5)); b[1].textContent = pad2(Math.floor(diff%864e5/36e5)); b[2].textContent = pad2(Math.floor(diff%36e5/6e4));
    }
    function paintAll(){ lnSec.querySelectorAll('.ln[data-net]').forEach(paint); }
    paintAll(); setInterval(paintAll, 30000);
    var api = lnSec.getAttribute('data-api');
    if (api && window.fetch && location.protocol.indexOf('http') === 0) {
      fetch(api, {cache:'no-store'}).then(function(r){ return r.ok ? r.json() : null; }).then(function(d){
        if (!d || !d.upcoming) return;
        var byId = {}, curated = {};
        d.upcoming.forEach(function(l){ byId[l.id] = l; });
        lnSec.querySelectorAll('.ln[data-id]').forEach(function(el){
          var id = el.getAttribute('data-id'); curated[id] = 1; var l = byId[id];
          if (l) { el.setAttribute('data-net', l.net); el.setAttribute('data-status', l.status || 'TBD'); }
          else if (new Date(el.getAttribute('data-net')) < Date.now()) { el.setAttribute('data-status', 'Success'); }
        });
        // a card whose launch already happened gets replaced by the next upcoming launch we did not write up
        var grid = document.getElementById('ln-grid'), want = lnSec.querySelectorAll('.ln[data-id]').length;
        var live = lnSec.querySelectorAll('.ln[data-id]').length - lnSec.querySelectorAll('.ln[data-id].past').length;
        paintAll();
        live = 0; lnSec.querySelectorAll('.ln[data-id]').forEach(function(el){ if (!el.classList.contains('past')) live++; });
        d.upcoming.forEach(function(l){
          if (live >= want || curated[l.id] || /Unknown Payload/i.test(l.name) || new Date(l.net) < Date.now()) return;
          var a = document.createElement('a'); a.className = 'ln rv in'; a.href = 'https://www.spacelaunchschedule.com/launch/' + l.slug + '/'; a.target = '_blank'; a.rel = 'noopener';
          a.setAttribute('data-net', l.net); a.setAttribute('data-status', l.status || 'TBD');
          a.innerHTML = '<div class="ln-top"><span class="ln-st"></span><span class="ln-st st-auto">עדכון אוטומטי</span><span class="ln-when"></span></div>'
            + '<div class="ln-cd"><span class="cd-u"><b>--</b><i>ימים</i></span><span class="cd-u"><b>--</b><i>שעות</i></span><span class="cd-u"><b>--</b><i>דקות</i></span></div><div class="ln-past"></div>'
            + '<h3></h3><p class="ln-pay"></p><div class="ln-meta"></div>';
          a.querySelector('h3').textContent = l.mission || l.name;
          a.querySelector('.ln-pay').textContent = (TYPE[l.type] || l.type || '') + (l.provider ? ' · ' + heb(l.provider) : '');
          a.querySelector('.ln-meta').textContent = [heb(l.rocket), heb(l.provider), heb(l.site)].filter(Boolean).join(' · ');
          grid.appendChild(a); paint(a); live++;
        });
        var up = document.getElementById('ln-updated'); if (up) up.textContent = 'המועדים מתעדכנים מלוח השיגורים החי (Launch Library) · עודכן ' + fmtIL.format(new Date(d.updated)).replace(',', ' ·');
      }).catch(function(){});
    }
  }
  // extra opportunities toggle
  var mb = document.getElementById('opps-more-btn'), ox = document.getElementById('opps-extra');
  if (mb && ox) mb.addEventListener('click', function(){
    var open = ox.classList.toggle('open');
    mb.textContent = open ? mb.getAttribute('data-less') : mb.getAttribute('data-more');
  });
  // floating buttons: appear once scrolling starts, stay for the whole page
  var fabs = document.getElementById('fabs'), tt = document.getElementById('to-top');
  if (fabs) {
    var onScroll = function(){ fabs.classList.toggle('show', scrollY > 250); };
    addEventListener('scroll', onScroll, {passive:true});
    onScroll();
  }
  if (tt) tt.addEventListener('click', function(){ scrollTo({top:0, behavior: reduce ? 'auto' : 'smooth'}); });
  // share: menu toggle, copy link, native share
  var sb = document.getElementById('share-btn'), sm = document.getElementById('share-menu');
  if (sb && sm) {
    sb.addEventListener('click', function(){ sm.classList.toggle('open'); });
    document.addEventListener('click', function(e){
      if (!e.target.closest('.share-wrap')) sm.classList.remove('open');
    });
  }
  document.querySelectorAll('.copy-link').forEach(function(el){
    el.addEventListener('click', function(){
      var u = el.getAttribute('data-url');
      function done(){ var t = el.textContent; el.textContent = 'הקישור הועתק'; setTimeout(function(){ el.textContent = t; }, 1800); }
      function fallback(){ var ta = document.createElement('textarea'); ta.value = u; document.body.appendChild(ta); ta.select();
        try { document.execCommand('copy'); done(); } catch(e){} document.body.removeChild(ta); }
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(u).then(done, fallback);
      else fallback();
    });
  });
  document.querySelectorAll('.native-share').forEach(function(el){
    if (!navigator.share) { el.style.display = 'none'; return; }
    el.addEventListener('click', function(){
      navigator.share({ title: 'השבוע בחלל', text: el.getAttribute('data-text'), url: el.getAttribute('data-url') }).catch(function(){});
    });
  });
  // category filter
  var btns = document.querySelectorAll('.fbtn'), cards = document.querySelectorAll('.news-grid .card');
  btns.forEach(function(b){ b.addEventListener('click', function(){
    btns.forEach(function(x){ x.classList.remove('on'); }); b.classList.add('on');
    var f = b.getAttribute('data-f');
    cards.forEach(function(c){
      var show = f==='*' || c.getAttribute('data-cat')===f || (f==='il' && c.getAttribute('data-scope')==='il');
      c.classList.toggle('hide', !show);
    });
  }); });
})();
"""


def site_base():
    """כתובת האתר החי (לקישור הארכיון) — מ-site_config.json, עם ברירת מחדל."""
    try:
        cfg = json.load(open(os.path.join(HERE, "site_config.json"), encoding="utf-8"))
        return cfg["base_url"].rstrip("/")
    except Exception:
        return "https://rakia-weekly.vercel.app"


def build(content):
    iss = content["issue"]
    num = iss["number"]
    art_dir = os.path.join(ASSETS, "articles", f"issue{num}")
    archive_url = site_base() + "/archive/"

    def art_img(name):
        if name.startswith("brand:"):
            return data_uri(os.path.join(ASSETS, name[6:]))
        return data_uri(os.path.join(art_dir, name))

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

    # רקע הכוכבים מוזרק כמשתנה CSS (בקובץ עצמאי אין קבצים חיצוניים)
    stars_css = f":root{{--stars:url('{data_uri(os.path.join(ASSETS, 'bg-stars.jpg'))}')}}"

    # topbar — מימין לשמאל: הפורום › מפא"ת › רקיע › ספייס קמפוס (גרסאות בהירות לרקע כהה)
    topbar = f"""
<div class="topbar"><div class="wrap">
  <div class="brand">
    <img class="lg-isf" src="{data_uri(os.path.join(ASSETS, 'logo-isf-light.png'))}" alt="הפורום הישראלי לחלל">
    <span class="sep"></span>
    <img class="lg-min" src="{data_uri(os.path.join(ASSETS, 'logo-minhelet-dark-bg.png'))}" alt="מנהלת החלל">
    <span class="sep"></span>
    <img class="lg-rakia" src="{data_uri(os.path.join(ASSETS, 'logo-rakia-dark-bg.png'))}" alt="משימת רקיע">
    <span class="sep"></span>
    <img class="lg-cam" src="{data_uri(os.path.join(ASSETS, 'logo-spacecampus-white.png'))}" alt="IL Space Campus">
  </div>
  <div class="issue-tag"><b>ניוזלטר שבועי</b><span class="date">{t(iss['window_he'])}</span><a class="archive-link" href="{esc(archive_url)}" target="_blank" rel="noopener">לארכיון</a></div>
</div></div>"""

    # האם יש בלוק פורום חי ולוח אירועים? (לכפתורי הקיצור בהירו)
    _today = iss.get("date_iso", "")
    _fe = content.get("forum_events")
    has_forum = bool(_fe and [e for e in _fe.get("items") or []
                              if not _today or ((e.get("expires") or "9999") >= _today)])
    has_events = bool(content.get("events"))
    year = (iss.get("date_iso") or "")[:4]
    range_txt = f"{iss['window_he']} {year}".strip()

    # קישורי שיתוף (שיווק אורגני): הקישור המשותף הוא הכתובת הקבועה של הגיליון באתר החי
    share_url = f"{site_base()}/{iss.get('date_iso') or num}/"
    share_text = f"השבוע בחלל · ניוזלטר תעשיית החלל של הפורום הישראלי לחלל · {iss['window_he']}"
    enc_u = urllib.parse.quote(share_url, safe="")
    enc_t = urllib.parse.quote(share_text, safe="")
    sh_wa = f"https://wa.me/?text={enc_t}%0A{enc_u}"
    sh_tg = f"https://t.me/share/url?url={enc_u}&text={enc_t}"
    sh_li = f"https://www.linkedin.com/sharing/share-offsite/?url={enc_u}"
    sh_tw = f"https://twitter.com/intent/tweet?text={enc_t}&url={enc_u}"
    sh_mail = f"mailto:?subject={enc_t}&body={enc_t}%0A{enc_u}"

    share_items = f"""
    <a class="wa" href="{esc(sh_wa)}" target="_blank" rel="noopener">שיתוף בוואטסאפ</a>
    <a href="{esc(sh_tg)}" target="_blank" rel="noopener">טלגרם</a>
    <a href="{esc(sh_li)}" target="_blank" rel="noopener">לינקדאין</a>
    <a href="{esc(sh_tw)}" target="_blank" rel="noopener">X (טוויטר)</a>
    <a href="{esc(sh_mail)}">מייל</a>
    <button type="button" class="copy-link" data-url="{esc(share_url)}">העתקת קישור</button>
    <button type="button" class="native-share" data-url="{esc(share_url)}" data-text="{esc(share_text)}">עוד אפשרויות…</button>"""

    # כפתורים צפים: שיתוף + חזרה למעלה (מופיעים אחרי תחילת גלילה, נשארים לכל אורכה)
    ic_share = ('<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" '
                'stroke-width="2.2" stroke-linecap="round"><circle cx="18" cy="5" r="2.7"/>'
                '<circle cx="6" cy="12" r="2.7"/><circle cx="18" cy="19" r="2.7"/>'
                '<line x1="8.4" y1="10.7" x2="15.6" y2="6.3"/><line x1="8.4" y1="13.3" x2="15.6" y2="17.7"/></svg>')
    ic_home = ('<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" '
               'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
               '<path d="M3 10.5 12 3l9 7.5"/><path d="M5.5 9.5V20a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1V9.5"/>'
               '<path d="M9.5 21v-6h5v6"/></svg>')
    fabs = f"""
<div class="fabs" id="fabs">
  <div class="share-wrap">
    <button class="fab fab-share" id="share-btn" type="button" aria-label="שיתוף הניוזלטר" title="שיתוף">{ic_share}</button>
    <div class="share-menu" id="share-menu">{share_items}
    </div>
  </div>
  <button class="fab fab-home" id="to-top" type="button" aria-label="חזרה לתחילת העמוד" title="לתחילת העמוד">{ic_home}</button>
</div>"""

    nav_btns = ['<a class="btn-news" href="#news">חדשות השבוע <span class="ar">↓</span></a>']
    if has_forum:
        nav_btns.append('<a class="btn-sec" href="#forum">פורום החלל הישראלי</a>')
    nav_btns.append('<a class="btn-sec" href="#opps">הזדמנויות חמות</a>')
    if has_events:
        nav_btns.append('<a class="btn-sec" href="#events">אירועים בעולם</a>')

    hero = f"""
<header class="hero">
  <div class="hero-bg" style="background-image:url('{data_uri(os.path.join(ASSETS, 'img-hero.webp'))}')"></div>
  <div class="hero-shade"></div>
  <div class="hero-in wrap">
    <div class="kicker tzar">{t(iss['hero_kicker'])}</div>
    <h1>{esc(iss['hero_title'])}</h1>
    <p>{t(iss['hero_sub'])}</p>
    <div class="range">{t(range_txt)}</div>
    <nav class="hero-nav">{''.join(nav_btns)}</nav>
  </div>
</header>"""

    # שורת המספרים ("נתוני השבוע") הוסרה לצמיתות לבקשת המשתמש (23.9.2026): המספרים לא
    # אמינים מספיק לפרסום. המפתח "stats" ב-JSON נשמר לתיעוד פנימי בלבד ואינו מרונדר.
    stats = ""

    # ── אירועי הפורום הישראלי לחלל: נשארים עד שתאריכם עובר (expires >= date_iso) ──
    forum = ""
    fe = content.get("forum_events")
    if fe:
        today = iss.get("date_iso", "")
        live = [e for e in fe.get("items") or [] if not today or ((e.get("expires") or "9999") >= today)]

        def fe_card(e):
            url = (e.get("url") or "").strip()
            # mailto נפתח באפליקציית המייל — target=_blank רק ל-http
            tgt = ' target="_blank" rel="noopener"' if url.startswith("http") else ""
            tag, attrs, close = ("a", f' href="{esc(url)}"{tgt}', "a") if url else ("div", "", "div")
            btn = f'<span class="btn-g">{esc(e["cta"])}</span>' if url and e.get("cta") else ""
            return f"""
  <{tag} class="fe rv{'' if url else ' ev-static'}"{attrs}>
    <div class="fe-img" style="background-image:url('{art_img(e['img'])}')"></div>
    <div class="fe-tx">
      <div class="fe-date">{t(e['date_label'])}</div>
      <h3>{t(e['title'])}</h3>
      <div class="place">📍 {t(e['place'])}</div>
      <p>{t(e['desc'])}</p>
      {btn}
    </div>
  </{close}>"""
        fe_cards = "".join(fe_card(e) for e in live)
        if fe_cards:
            forum = f"""
<section class="forum" id="forum"><div class="wrap">
  <div class="fe-brand rv"><img src="{data_uri(os.path.join(ASSETS, 'logo-isf-light.png'))}" alt="הפורום הישראלי לחלל"></div>
  <div class="sec-head rv"><h2>{esc(fe.get('title', 'פורום החלל הישראלי'))}</h2><span class="rule"></span><span class="dot"></span></div>
  <div class="sec-sub rv">{t(fe.get('intro', ''))}</div>
  <div class="fe-grid">{fe_cards}</div>
</div></section>"""

    # opportunities
    opps = content["opportunities"]
    opp_cards = []
    for o in opps.get("large") or []:
        opp_cards.append(f"""
  <a class="opp rv" href="{esc(o['url'])}" target="_blank" rel="noopener">
    <div class="opp-top"><span class="chip tzar">{esc(o['type'])}</span><span class="deadline">{t(o['deadline_label'])}</span></div>
    <h3>{esc(o['title'])}</h3><p>{t(o['desc'])}</p>
    <span class="cta">{esc(o.get('cta', 'לפרטים'))}</span>
  </a>""")
    for o in opps.get("small") or []:
        opp_cards.append(f"""
  <a class="opp rv" href="{esc(o['url'])}" target="_blank" rel="noopener">
    <div class="opp-top"><span class="chip tzar">{esc(o['type'])}</span></div>
    <h3>{esc(o['title'])}</h3><div class="meta">{t(o['meta'])}</div>
    <span class="cta">{esc(o.get('cta', 'לפרטים'))}</span>
  </a>""")
    extra = opps.get("extra") or []
    extra_rows = "".join(
        f"""
    <a class="oppx" href="{esc(o['url'])}" target="_blank" rel="noopener">
      <span class="chip tzar">{esc(o['type'])}</span>
      <div><b>{esc(o['title'])}</b><br><span>{t(o['meta'])}</span></div>
    </a>"""
        for o in extra)
    extra_html = ""
    if extra:
        extra_html = (f'<div id="opps-extra">{extra_rows}</div>'
                      f'<button class="opps-more" id="opps-more-btn" data-more="עוד {len(extra)} הזדמנויות פתוחות +" data-less="להסתיר −">'
                      f'עוד {len(extra)} הזדמנויות פתוחות +</button>')
    opportunities = f"""
<section class="opps" id="opps"><div class="wrap">
  <div class="sec-head rv"><h2>הזדמנויות חמות</h2><span class="rule"></span><span class="dot"></span></div>
  <div class="sec-sub rv">{t(opps.get('intro', ''))}</div>
  <div class="opps-grid">{''.join(opp_cards)}</div>
  {extra_html}
</div></section>"""

    # events — לוח האירועים הבינלאומי
    accents = ["#64e275", "#11b6bc", "#1776b1"]
    def ev_card(i, ev):
        url = (ev.get("url") or "").strip()
        tag, attrs, close = ("a", f' href="{esc(url)}" target="_blank" rel="noopener"', "a") if url else ("div", "", "div")
        return f"""
  <{tag} class="ev rv{'' if url else ' ev-static'}"{attrs}>
    <div class="ev-date"><b>{esc(ev['day'])}</b><span>{esc(ev['month_he'])}</span></div>
    <span class="ev-bar" style="background:{accents[i % 3]}"></span>
    <div><h3>{esc(ev['title'])}</h3><p>{t(ev['meta'])}</p></div>
  </{close}>"""

    ev_cards = "".join(ev_card(i, ev) for i, ev in enumerate(content.get("events") or []))
    events = f"""
<section class="events" id="events"><div class="wrap">
  <div class="sec-head rv"><h2>אירועים קרובים בעולם</h2><span class="rule"></span><span class="dot"></span></div>
  <div class="ev-grid">{ev_cards}</div>
</div></section>""" if ev_cards else ""

    # upcoming launches countdown (מדור קבוע מ-23.9.2026; מועדים מ-Launch Library 2, מתעדכנים חי באתר)
    launches_html = ""
    ln = content.get("launches") or {}
    if ln.get("items"):
        try:
            with open(os.path.join(HERE, "site_config.json"), encoding="utf-8") as f:
                ln_api = json.load(f)["base_url"].rstrip("/") + "/api/launches"
        except Exception:
            ln_api = ""
        st_he = {"Go": "אושר לשיגור", "TBC": "ממתין לאישור", "TBD": "מועד לא סופי", "Hold": "מושהה"}
        ln_cards = []
        for it in ln["items"]:
            st = it.get("status") or "TBD"
            scope = '<span class="tag-il tzar">ישראל</span>' if it.get("scope") == "ישראל" else ""
            ln_cards.append(f"""
  <a class="ln{' feat' if it.get('featured') else ''} rv" href="{esc(it['url'])}" target="_blank" rel="noopener" data-id="{esc(it['id'])}" data-net="{esc(it['net'])}" data-status="{esc(st)}">
    <div class="ln-top"><span class="ln-st st-{esc(st.lower())}">{esc(st_he.get(st, st))}</span>{scope}<span class="ln-when">{il_time(it['net'])} שעון ישראל</span></div>
    <div class="ln-cd"><span class="cd-u"><b>--</b><i>ימים</i></span><span class="cd-u"><b>--</b><i>שעות</i></span><span class="cd-u"><b>--</b><i>דקות</i></span></div>
    <div class="ln-past"></div>
    <h3>{t(it['title'])}</h3>
    <p class="ln-pay">{t(it['payload'])}</p>
    <div class="ln-meta">{t(it['meta'])}</div>
  </a>""")
        launches_html = f"""
<section class="launches" id="launches" data-api="{esc(ln_api)}"><div class="wrap">
  <div class="sec-head rv"><h2>{esc(ln.get('title') or 'השיגורים הבאים')}</h2><span class="rule"></span><span class="dot"></span></div>
  <div class="sec-sub rv">{t(ln.get('intro') or '')}</div>
  <div class="ln-grid" id="ln-grid">{''.join(ln_cards)}</div>
  <div class="ln-foot rv"><span id="ln-updated">המועדים לפי Launch Library של The Space Devs, בשעון ישראל · נכון ל{esc(content['issue'].get('date_he', ''))}</span><a href="https://www.spacelaunchschedule.com/" target="_blank" rel="noopener">ללוח השיגורים המלא ←</a></div>
</div></section>"""

    # news
    news = content["news"]
    lead = news["lead"]
    lead_html = f"""
  <div class="lead-card rv">
    <a class="lead-img" style="background-image:url('{art_img(lead['img'])}')" href="{esc(lead['url'])}" target="_blank" rel="noopener"></a>
    <div class="lead-tx">
      <div class="row"><span class="chip-inv tzar">{esc(lead['scope'])}</span><span class="chip-line tzar">{esc(lead['category'])}</span><span class="src">{t(lead['date_source'])}</span></div>
      <a href="{esc(lead['url'])}" target="_blank" rel="noopener"><h3>{t(lead['title'])}</h3></a>
      <p>{t(lead['teaser'])}</p>
      <p class="more-p">{t(lead['more'])}</p>
      <a class="cta" href="{esc(lead['url'])}" target="_blank" rel="noopener">לכתבה המלאה</a>
    </div>
  </div>"""

    cats = []
    for it in news["items"]:
        if it["category"] not in cats:
            cats.append(it["category"])
    fbtns = '<button class="fbtn on" data-f="*">הכול</button>' + "".join(
        f'<button class="fbtn" data-f="{esc(c)}">{esc(c)}</button>' for c in cats)
    if any("ישראל" in it["scope"] for it in news["items"]):
        fbtns += '<button class="fbtn il" data-f="il">ישראל</button>'

    cards = []
    for it in news["items"]:
        scope_tag = '<span class="tag-il tzar">ישראל</span>' if "ישראל" in it["scope"] else f'<span class="tag tzar">{esc(it["scope"])}</span>'
        cards.append(f"""
  <article class="card rv" data-cat="{esc(it['category'])}" data-scope="{'il' if 'ישראל' in it['scope'] else 'intl'}">
    <a href="{esc(it['url'])}" target="_blank" rel="noopener"><div class="card-img" style="background-image:url('{art_img(it['img'])}')"></div></a>
    <div class="card-tx">
      <div class="row">{scope_tag}<span class="tag tzar">{esc(it['category'])}</span><span class="src">{t(it['date_source'])}</span></div>
      <h3>{t(it['title'])}</h3>
      <p class="teaser">{t(it['teaser'])}</p>
      <p class="more-p">{t(it['more'])}</p>
      <a class="goto" href="{esc(it['url'])}" target="_blank" rel="noopener">לכתבה המלאה</a>
    </div>
  </article>""")

    briefs = "".join(f'<a href="{esc(b["url"])}" target="_blank" rel="noopener">{t(b["text"])}</a>'
                     for b in news.get("briefs") or [])
    briefs_html = f'<div class="briefs rv"><b class="tzar">בקצרה</b>{briefs}</div>' if briefs else ""

    news_html = f"""
<section id="news"><div class="wrap">
  <div class="sec-head rv"><h2>חדשות השבוע</h2><span class="rule"></span><span class="dot"></span></div>
  <div class="sec-sub rv">סננו לפי תחום, או לחצו על "ישראל" כדי לראות רק ידיעות ישראליות.</div>
  {lead_html}
  <div class="filters rv">{fbtns}</div>
  <div class="news-grid">{''.join(cards)}</div>
  {briefs_html}
</div></section>"""

    vids = "".join(
        f"""
  <a class="vid rv" href="{esc(v['url'])}" target="_blank" rel="noopener">
    <div class="vid-th" style="background-image:url('{art_img(v['thumb'])}')"><span class="play"></span></div>
    <div class="vid-tx"><h3>{t(v['title'])}</h3><p>{esc(v['channel'])}</p></div>
  </a>"""
        for v in content.get("videos") or [])
    videos = f"""
<section class="videos"><div class="wrap">
  <div class="sec-head rv"><h2>שווה צפייה</h2><span class="rule"></span><span class="dot"></span></div>
  <div class="vid-grid">{vids}</div>
</div></section>""" if vids else ""

    socials = "".join(
        f'<a href="{url}" target="_blank" rel="noopener"><img src="{data_uri(os.path.join(ASSETS, icon))}" alt="{name}"></a>'
        for name, icon, url in [
            ("LinkedIn", "social-linkedin.png", "https://www.linkedin.com/company/rakia-mission"),
            ("Facebook", "social-facebook.png", "https://www.facebook.com/rakiamission"),
            ("Instagram", "social-instagram.png", "https://www.instagram.com/rakiamission"),
            ("YouTube", "social-youtube.png", "https://www.youtube.com/@rakiamission"),
        ])
    partners = (f'<div class="foot-partners"><span>בשיתוף</span>'
                f'<img src="{data_uri(os.path.join(ASSETS, "logo-minhelet-dark-bg.png"))}" alt="מנהלת החלל">'
                f'<img src="{data_uri(os.path.join(ASSETS, "logo-spacecampus-white.png"))}" alt="IL Space Campus"></div>')

    footer = f"""
<footer><span class="blob b1"></span><span class="blob b2"></span>
  <div class="wrap foot-in">
    <div class="foot-top">
      <div class="foot-brand">
        <img class="f-isf" src="{data_uri(os.path.join(ASSETS, 'logo-isf-light.png'))}" alt="הפורום הישראלי לחלל">
        <img class="f-rakia" src="{data_uri(os.path.join(ASSETS, 'logo-rakia-dark-bg.png'))}" alt="משימת רקיע">
      </div>
      <div class="foot-links">
        <a href="https://israelspaceforum.com/" target="_blank" rel="noopener">הפורום הישראלי לחלל</a>
        <a href="https://www.rakiamission.com/" target="_blank" rel="noopener">אתר משימת רקיע</a>
        <a href="{esc(archive_url)}" target="_blank" rel="noopener">ארכיון הגיליונות</a>
      </div>
      <div class="socials">{socials}</div>
    </div>
    <div class="foot-line"></div>
    <div class="share-cta">
      <b>אהבתם? שתפו את הניוזלטר</b>
      <div class="share-row">
        <a class="sh sh-wa" href="{esc(sh_wa)}" target="_blank" rel="noopener">שיתוף בוואטסאפ</a>
        <a class="sh" href="{esc(sh_tg)}" target="_blank" rel="noopener">טלגרם</a>
        <a class="sh" href="{esc(sh_li)}" target="_blank" rel="noopener">לינקדאין</a>
        <a class="sh" href="{esc(sh_tw)}" target="_blank" rel="noopener">X</a>
        <a class="sh" href="{esc(sh_mail)}">מייל</a>
        <button type="button" class="sh copy-link" data-url="{esc(share_url)}">העתקת קישור</button>
      </div>
    </div>
    {partners}
    <div class="legal">
      קיבלתם את המייל הזה משום שנרשמתם לניוזלטר של הפורום הישראלי לחלל, מיסודה של משימת רקיע. · משימת רקיע (ע״ר), תל אביב<br>
      {esc(content.get('credit_note', ''))}
    </div>
  </div>
</footer>"""

    body = (f'<div dir="rtl" lang="he">{topbar}{hero}{stats}{forum}{opportunities}'
            f'{events}{launches_html}{news_html}{videos}{footer}{fabs}</div>')
    head_css = f"<style>\n{fonts_css}\n{stars_css}\n{CSS}\n</style>"
    script = ("<noscript><style>.rv{opacity:1;transform:none}</style></noscript>"
              f"<script>{JS}</script>")
    title = "השבוע בחלל — ניוזלטר הפורום הישראלי לחלל"

    full = (f'<!DOCTYPE html>\n<html lang="he" dir="rtl">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{title}</title>\n{head_css}\n</head>\n<body>{body}{script}</body>\n</html>')
    artifact = f"<title>ניוזלטר שבועי רקיע</title>\n{head_css}\n{body}\n{script}"
    counts = {"news": 1 + len(news["items"]) + len(news.get("briefs") or []),
              "opps": len(opps.get("large") or []) + len(opps.get("small") or []) + len(extra),
              "forum_events": len(re.findall(r'class="fe rv"', forum)),
              "events": len(content.get("events") or []), "videos": len(content.get("videos") or [])}
    return full, artifact, counts


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "content/issue_001_v2.json"
    with open(src if os.path.isabs(src) else os.path.join(HERE, src), encoding="utf-8") as f:
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
    proj = os.path.abspath(os.path.join(HERE, "..", "..", f"ניוזלטר_שבועי_{num}.html"))
    with open(proj, "w", encoding="utf-8") as f:
        f.write(full)
    print(json.dumps({"full": p_full, "counts": counts, "size_mb": round(len(full) / 1048576, 2)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
