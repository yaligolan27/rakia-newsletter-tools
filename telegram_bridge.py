# -*- coding: utf-8 -*-
"""
גשר טלגרם ↔ Claude Code: מאזין לבוט, ומריץ כל הודעה מהמשתמש המורשה דרך claude CLI
בתיקיית הפרויקט (עם המשכיות שיחה), ומחזיר את התשובה לטלגרם.
- מגיב אך ורק ל-allowed_user_id מ-telegram_config.json; כל השאר נרשמים ללוג ונזרקים.
- מצב הרשאות: acceptEdits + allowlist הפקודות שב-.claude/settings.json של הפרויקט.
- ריצה: pythonw telegram_bridge.py  (מותקן גם ב-Startup — עולה עם המחשב)
"""
import json
import os
import ssl
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.abspath(os.path.join(HERE, "..", ".."))
CFG_PATH = os.path.join(HERE, "telegram_config.json")
STATE_PATH = os.path.join(HERE, "telegram_state.json")
LOCK_PATH = os.path.join(HERE, "telegram_bridge.lock")
LOG_PATH = os.path.join(HERE, "telegram_bridge.log")
CTX = ssl.create_default_context()

CFG = json.load(open(CFG_PATH, encoding="utf-8"))
TOK = CFG["bot_token"]
ALLOWED_USER = CFG["allowed_user_id"]
API = f"https://api.telegram.org/bot{TOK}"

CLAUDE = None
for cand in ("claude.cmd", "claude.exe", "claude"):
    import shutil
    p = shutil.which(cand)
    if p:
        CLAUDE = p
        break


def log(msg):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")


def api(method, data=None, timeout=70):
    url = f"{API}/{method}"
    body = urllib.parse.urlencode(data).encode() if data else None
    with urllib.request.urlopen(urllib.request.Request(url, data=body), timeout=timeout, context=CTX) as r:
        return json.load(r)


def send(chat_id, text):
    text = text.strip() or "(תשובה ריקה)"
    for i in range(0, len(text), 3900):
        try:
            api("sendMessage", {"chat_id": chat_id, "text": text[i:i + 3900]}, timeout=30)
        except Exception as e:
            log(f"send failed: {e}")


def typing_loop(chat_id, stop_event):
    while not stop_event.is_set():
        try:
            api("sendChatAction", {"chat_id": chat_id, "action": "typing"}, timeout=15)
        except Exception:
            pass
        stop_event.wait(7)


PROMPT_WRAP = """[הודעה מהמשתמש המורשה דרך גשר הטלגרם של ניוזלטר רקיע]
אתה רץ ללא ממשק (headless) בתיקיית הפרויקט. עריכות קבצים מאושרות אוטומטית; פקודות shell לרוב ייחסמו — אל תנסה להריץ אותן.
אם אחרי העריכות צריך לבנות מחדש את הגיליון ולשלוח את הקובץ המעודכן למשתמש — סיים את תשובתך בשורה נפרדת עם המרקר [[REBUILD]] והגשר יעשה זאת (build_newsletter.py על הגיליון העדכני + שליחת הקובץ לטלגרם).
ענה בעברית, קצר ותכליתי (התשובה נשלחת כהודעת טלגרם).

ההודעה: """


def newest_issue_json():
    import glob
    files = sorted(glob.glob(os.path.join(HERE, "content", "issue_*_v2.json")))
    return files[-1] if files else None


def do_rebuild_and_send(chat_id):
    cj = newest_issue_json()
    if not cj:
        send(chat_id, "לא מצאתי קובץ גיליון לבנייה.")
        return
    num = json.load(open(cj, encoding="utf-8"))["issue"]["number"]
    r = subprocess.run([sys.executable, os.path.join(HERE, "build_newsletter.py"), cj],
                       cwd=HERE, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        send(chat_id, f"הבנייה נכשלה: {(r.stderr or r.stdout)[:600]}")
        return
    out = os.path.join(HERE, "output", f"newsletter_{num}_full.html")
    sys.path.insert(0, HERE)
    import tg_send
    tg_send.send_file(out, f"גיליון {num} — גרסה מעודכנת")
    log(f"rebuilt and sent issue {num}")


def run_claude(text):
    base = [CLAUDE, "-p", PROMPT_WRAP + text, "--output-format", "text", "--permission-mode", "acceptEdits"]
    env = dict(os.environ)
    for args in ([CLAUDE, "--continue"] + base[1:], base):
        try:
            r = subprocess.run(args, cwd=PROJECT, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=1500, env=env)
            out = (r.stdout or "").strip()
            if r.returncode == 0 and out:
                return out
            err = (r.stderr or "").strip()
            log(f"claude rc={r.returncode} err={err[:300]}")
            if "No conversation" in err or "no conversation" in err:
                continue
            if out or err:
                return out or f"שגיאה מהסוכן: {err[:500]}"
        except subprocess.TimeoutExpired:
            return "⏱️ המשימה לקחה יותר מ-25 דקות ונעצרה. נסו לפצל לבקשות קטנות יותר."
        except Exception as e:
            log(f"claude spawn error: {e}")
            return f"שגיאה בהרצת קלוד: {e}"
    return "לא הצלחתי להריץ את קלוד. בדקו את telegram_bridge.log"


def main():
    if not ALLOWED_USER:
        log("no allowed_user_id configured; exiting")
        return
    # single instance
    if os.path.exists(LOCK_PATH):
        try:
            pid = int(open(LOCK_PATH).read().strip())
            if pid and subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True,
                                      text=True).stdout.find(str(pid)) != -1:
                log(f"already running (pid {pid}); exiting")
                return
        except Exception:
            pass
    open(LOCK_PATH, "w").write(str(os.getpid()))
    log(f"bridge started (pid {os.getpid()}, claude={CLAUDE})")

    state = {"offset": 0}
    if os.path.exists(STATE_PATH):
        try:
            state = json.load(open(STATE_PATH))
        except Exception:
            pass

    while True:
        try:
            upd = api("getUpdates", {"offset": state["offset"] + 1, "timeout": 50})
        except Exception as e:
            log(f"getUpdates error: {e}")
            time.sleep(10)
            continue
        for u in upd.get("result", []):
            state["offset"] = u["update_id"]
            json.dump(state, open(STATE_PATH, "w"))
            msg = u.get("message") or {}
            frm = msg.get("from", {})
            chat_id = msg.get("chat", {}).get("id")
            text = (msg.get("text") or "").strip()
            if frm.get("id") != ALLOWED_USER:
                log(f"ignored message from stranger id={frm.get('id')} user={frm.get('username')}")
                continue
            if not text:
                send(chat_id, "קיבלתי קובץ/מדיה — כרגע אני עובד עם טקסט בלבד 🙏")
                continue
            if text == "/start":
                send(chat_id, "מחובר! ✅ כתבו לי כל דבר — בקשת עריכה לניוזלטר, שאלה, או משימה — ואני מריץ את קלוד על הפרויקט ועונה כאן.")
                continue
            log(f"processing: {text[:120]}")
            stop = threading.Event()
            t = threading.Thread(target=typing_loop, args=(chat_id, stop), daemon=True)
            t.start()
            try:
                answer = run_claude(text)
            finally:
                stop.set()
            rebuild = "[[REBUILD]]" in answer
            answer = answer.replace("[[REBUILD]]", "").strip()
            send(chat_id, answer)
            if rebuild:
                try:
                    do_rebuild_and_send(chat_id)
                except Exception as e:
                    log(f"rebuild error: {e}")
                    send(chat_id, f"שגיאה בבנייה: {e}")
            log(f"answered ({len(answer)} chars, rebuild={rebuild})")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            os.remove(LOCK_PATH)
        except OSError:
            pass
