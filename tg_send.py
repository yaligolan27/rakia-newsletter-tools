# -*- coding: utf-8 -*-
"""שליחה לבוט הטלגרם של רקיע (למשתמש המורשה בלבד).
שימוש:  python tg_send.py "הודעת טקסט"
        python tg_send.py --file "C:\\path\\to\\file.html" "כיתוב"
"""
import json
import os
import ssl
import sys
import urllib.parse
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, "telegram_config.json"), encoding="utf-8"))
TOK, CHAT = CFG["bot_token"], CFG["allowed_chat_id"]
CTX = ssl.create_default_context()
API = f"https://api.telegram.org/bot{TOK}"


def send_text(text):
    for i in range(0, len(text), 3900):
        data = urllib.parse.urlencode({"chat_id": CHAT, "text": text[i:i + 3900],
                                       "disable_web_page_preview": "false"}).encode()
        urllib.request.urlopen(urllib.request.Request(f"{API}/sendMessage", data=data),
                               timeout=30, context=CTX)


def send_file(path, caption=""):
    boundary = uuid.uuid4().hex
    fname = os.path.basename(path)

    def part(name, val):
        return (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{val}\r\n').encode()

    body = part("chat_id", CHAT) + part("caption", caption[:1000])
    body += (f'--{boundary}\r\nContent-Disposition: form-data; name="document"; filename="{fname}"\r\n'
             f'Content-Type: application/octet-stream\r\n\r\n').encode()
    body += open(path, "rb").read() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(f"{API}/sendDocument", data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    urllib.request.urlopen(req, timeout=180, context=CTX)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--file":
        send_file(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
    elif len(sys.argv) >= 2:
        send_text(sys.argv[1])
    else:
        print("usage: tg_send.py <text> | --file <path> [caption]")
