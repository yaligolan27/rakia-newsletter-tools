# -*- coding: utf-8 -*-
"""Issue 009 base: carries over opportunities/events/forum from 008 with this week's verification changes."""
import json, copy, os
ROOT = r"C:\Users\yalig\Downloads\מנהלת החלל\מלודי -רקיע\tools\newsletter"
prev = json.load(open(os.path.join(ROOT, "content", "issue_008_v2.json"), encoding="utf-8"))
d = {"issue": {"number": "009", "date_he": "חמישי, 15 באוקטובר 2026", "window_he": "4 עד 10 באוקטובר",
               "hero_kicker": "סיכום השבוע", "hero_title": "השבוע בחלל", "hero_sub": "", "date_iso": "2026-10-15"}}
o = copy.deepcopy(prev["opportunities"])
ex = {x["url"]: x for x in o["extra"]}
fast = ex["https://innovationisrael.org.il/kol_kore/eic-accelerator-2026/"]
bird = ex["https://www.birdf.com/bird_programs/bird-general-program/"]
o["small"] = [
    {"type": "מסלול מהיר", "title": "חברות שעברו את Round A יכולות לדלג על שלב ב-EIC", "meta": fast["meta"], "url": fast["url"], "cta": "לפרטים"},
    {"type": "מענק", "title": bird["title"], "meta": bird["meta"], "url": bird["url"], "cta": "לפרטים"},
]
edu = {"type": "קול קורא", "title": "הציעו שיתוף פעולה ותוכן לכנס החינוך לחלל 2027",
       "meta": "הגשה בטופס מקוון עד 18.10 בשעה 12:00 · סוכנות החלל הישראלית · לגופים, ארגונים ומוסדות · הכנס ייערך במסגרת שבוע החלל הישראלי",
       "url": "https://www.space.gov.il/kolkore/135046"}
keep = ["https://starburst.aero/astra/apply-now/", "https://www.creation-space.com/expand/",
        "https://hello-tomorrow.org/global-challenge/", "https://www.space.gov.il/kolkore/134977"]
o["extra"] = [edu] + [ex[u] for u in keep]
d["opportunities"] = o

ev = copy.deepcopy(prev["events"])
for e in ev:
    if "commercialspaceweek" in e["url"]:
        e["day"] = "12"; e["meta"] = "12–14.1.2027 · אורלנדו, פלורידה · כנס החלל המסחרי שנערך בשיתוף נאס״א"
new = [
    {"day": "20", "month_he": "אוק׳", "title": "NeoSpace Europe 2026",
     "meta": "20.10 · לוקסמבורג · כנס החלל המסחרי של סוכנות החלל של לוקסמבורג, עם הצגות סטארט-אפים ומפגשי משקיעים",
     "url": "https://space-agency.public.lu/en/news-events/events/2026/neospace-europe.html"},
    {"day": "27", "month_he": "אוק׳", "title": "Defence in Space Conference 2026",
     "meta": "27–28.10 · לונדון · כנס חינמי על חלל וביטחון: תקשורת לוויינית צבאית, מודיעין מהחלל ומודעות למצב במסלול",
     "url": "https://defenceinspace.com/"},
]
d["events"] = new + ev  # new ones are earliest; SV Space Week (27.10) follows DISC
d["forum_events"] = copy.deepcopy(prev["forum_events"])
d["forum_events"]["items"] = [x for x in d["forum_events"]["items"] if x["expires"] >= "2026-10-15"]
d["credit_note"] = prev["credit_note"]
json.dump(d, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "base009.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(o["extra"]), len(d["events"]), len(d["forum_events"]["items"]))
