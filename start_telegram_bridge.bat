@echo off
rem ── מפעיל את גשר הטלגרם של ניוזלטר רקיע ──
rem להפעלה אוטומטית עם המחשב: העתיקו קובץ זה לתיקיית ההפעלה —
rem   לחצו Win+R, כתבו shell:startup, אנטר — וגררו את הקובץ לשם.
start "" /min pythonw "%~dp0telegram_bridge.py"
