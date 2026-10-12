# -*- coding: utf-8 -*-
"""
פרסום האתר לאוויר (מ-4.10.2026 רץ אוטומטית מהרוטינה השבועית).
מריץ: build_site.py → git add/commit/push בתיקיית site/ → Vercel מפרסם אוטומטית.
שימוש:  python publish_site.py "issue 002"
"""
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")


def run(cmd, cwd=None):
    print("$", " ".join(cmd))
    r = subprocess.run(cmd, cwd=cwd or SITE)
    if r.returncode != 0:
        raise SystemExit(f"נכשל: {' '.join(cmd)}")


def main():
    msg = sys.argv[1] if len(sys.argv) > 1 else "update newsletter"
    run([sys.executable, os.path.join(HERE, "build_site.py")], cwd=HERE)
    run(["git", "add", "-A"])
    status = subprocess.run(["git", "status", "--porcelain"], cwd=SITE, capture_output=True, text=True)
    if not status.stdout.strip():
        print("אין שינויים לפרסום.")
        return
    run(["git", "commit", "-m", msg])
    run(["git", "push"])
    print("פורסם! Vercel יעדכן את האתר תוך כדקה.")


if __name__ == "__main__":
    main()
