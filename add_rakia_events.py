# -*- coding: utf-8 -*-
"""מוסיף לגיליון 002 את אירועי רקיע/הפורום שמאיה העבירה (מהגרפיקות הרשמיות),
ואת משלחת החלל לאיחוד האמירויות גם כהזדמנות. הפרטים מהחומרים הרשמיים של המארגנים."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "content", "issue_002_v2.json")
d = json.load(open(SRC, encoding="utf-8"))

ISF = "https://israelspaceforum.com/"

# ── אירועים חדשים (מקור: הגרפיקות הרשמיות שהעבירה מאיה) ────────────────────
new_events = [
    {"day": "08", "month_he": "ספט׳",
     "title": "Space Executive Forum — בניית ההון האנושי",
     "meta": "8.9 · 09:30–13:00 · ארדינסט, בן נתן, טולדנו — ברקוביץ׳ 4, קומה 17, תל אביב · הפורום הישראלי לחלל",
     "url": ISF},
    {"day": "15", "month_he": "ספט׳",
     "title": "חשיפת טיוטת חוק החלל לתעשייה",
     "meta": "15.9 · 09:30–12:00 · Startup Nation Central, לילינבלום 28, תל אביב · בהזמנה בלבד · סוכנות החלל והפורום הישראלי לחלל",
     "url": ""},
    {"day": "13", "month_he": "אוק׳",
     "title": "Czech-Israeli Space Business Forum 2026",
     "meta": "13.10 · Startup Nation Central, לילינבלום 28, תל אביב · CzechTrade, שגרירות צ׳כיה, סוכנות החלל והפורום",
     "url": ISF},
    {"day": "21", "month_he": "אוק׳",
     "title": "משלחת עסקית לאיחוד האמירויות — Israeli Space Roadshow",
     "meta": "21–22.10 · אמירויות · מכון היצוא, הפורום הישראלי לחלל וסוכנות החלל",
     "url": "https://exportgov.tfaforms.net/1835?CID=701Wn000009DzV8"},
]

events = list(d["events"]) + new_events


def sort_key(e):
    months = {"ספט׳": 9, "אוק׳": 10, "נוב׳": 11, "דצמ׳": 12, "ינו׳": 13}
    return (months.get(e["month_he"], 99), int(e["day"]))


d["events"] = sorted(events, key=sort_key)

# ── משלחת האמירויות גם כהזדמנות (הרשמה בתשלום, דורשת פעולה) ────────────────
d["opportunities"]["small"].insert(0, {
    "type": "משלחת",
    "title": "משלחת חלל ישראלית לאיחוד האמירויות",
    "meta": "21–22.10 · פגישות עם Space42, מרכז החלל מוחמד בן ראשד ו-EDGE · חברי מכון היצוא 2,950 ₪ / אחרים 4,300 ₪",
    "url": "https://exportgov.tfaforms.net/1835?CID=701Wn000009DzV8",
    "cta": "לפרטים והרשמה",
})
# שמירה על 4 בולטות: הביתן בברמן יורד ל-extra (התערוכה רק בנובמבר, פחות דחוף)
moved = d["opportunities"]["small"].pop()
d["opportunities"]["extra"].insert(0, {
    "type": moved["type"], "title": moved["title"], "meta": moved["meta"], "url": moved["url"],
})

n_opps = len(d["opportunities"]["large"]) + len(d["opportunities"]["small"]) + len(d["opportunities"]["extra"])
d["opportunities"]["intro"] = (
    "קולות קוראים, מענקים, מכרזים, משלחות וכנסים — נשארים כאן כל עוד הם פתוחים, כדי שתספיקו לנצל אותם. "
    f"כל {n_opps} ההזדמנויות נבדקו ואומתו כפתוחות."
)
for s in d["stats"]:
    if "הזדמנויות" in s["label"]:
        s["value"] = str(n_opps)

json.dump(d, open(SRC, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("events:", len(d["events"]), "| opps:", n_opps)
for e in d["events"]:
    print("  ", e["day"], e["month_he"], "|", e["title"], "|", "LINK" if e["url"] else "no-link")
