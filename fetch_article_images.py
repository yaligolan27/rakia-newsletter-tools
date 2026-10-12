# -*- coding: utf-8 -*-
"""מוריד תמונת og:image מכל כתבה, מכווץ (רוחב<=900, JPEG q72) ושומר ל-assets/articles/<issue>/<slug>.jpg"""
import io
import json
import os
import re
import ssl
import sys
import urllib.request

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9,he;q=0.8"}
CTX = ssl.create_default_context()


def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read()


def og_image(page_url):
    html_bytes = get(page_url)
    head = html_bytes[:300000].decode("utf-8", errors="ignore")
    for pat in (r'property=["\']og:image["\'][^>]*content=["\']([^"\']+)',
                r'content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']',
                r'name=["\']twitter:image["\'][^>]*content=["\']([^"\']+)'):
        m = re.search(pat, head)
        if m:
            return m.group(1).replace("&amp;", "&")
    return None


def fetch_one(slug, url, outdir):
    try:
        img_url = url if re.search(r"\.(jpg|jpeg|png|webp)(\?|$)", url, re.I) else og_image(url)
        if not img_url:
            return {"slug": slug, "ok": False, "err": "no og:image"}
        if img_url.startswith("//"):
            img_url = "https:" + img_url
        raw = get(img_url)
        img = Image.open(io.BytesIO(raw))
        img = img.convert("RGB")
        w, h = img.size
        if w < 300 or h < 150:
            return {"slug": slug, "ok": False, "err": f"too small {w}x{h}", "img_url": img_url}
        if w > 900:
            img = img.resize((900, int(h * 900 / w)), Image.LANCZOS)
        out = os.path.join(outdir, f"{slug}.jpg")
        img.save(out, "JPEG", quality=72, optimize=True)
        return {"slug": slug, "ok": True, "size": os.path.getsize(out), "dims": img.size, "img_url": img_url}
    except Exception as e:
        return {"slug": slug, "ok": False, "err": str(e)[:120]}


def main():
    mapping = json.load(open(sys.argv[1], encoding="utf-8"))
    issue = mapping.pop("_issue", "issue")
    outdir = os.path.join(HERE, "assets", "articles", issue)
    os.makedirs(outdir, exist_ok=True)
    report = [fetch_one(slug, url, outdir) for slug, url in mapping.items()]
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
