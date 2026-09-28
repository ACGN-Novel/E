# -*- coding: utf-8 -*-
import os, re, json, collections, urllib.request, urllib.parse
from pypinyin import lazy_pinyin, Style

SITES = os.environ["SITES"].split(",")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}


def get(url, timeout=120):
    r = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "ignore")


def unquote_segs(path):
    return [urllib.parse.unquote(s, encoding="utf-8", errors="replace") for s in path.strip("/").split("/")]


def initial_of(title):
    s = title.strip()
    s = re.sub(r"^[^0-9A-Za-z\u4e00-\u9fff]+", "", s)      # 去掉开头符号（《【[(等
    s = re.sub(r"^[0-9\s._\-]+", "", s)                    # 去掉开头的编号 "013." "100012970"
    if not s:
        return "#"
    ch = s[0]
    if "\u4e00" <= ch <= "\u9fff":
        py = lazy_pinyin(ch, style=Style.FIRST_LETTER)
        return (py[0].upper() if py and py[0] else "#")
    if ch.isalpha():
        return ch.upper()
    if ch.isdigit():
        return "0"
    return "#"


books = []
site_ok = {}
for base in SITES:
    try:
        xml = get(base + "/sitemap.xml", timeout=180)
        locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)
        pages = [l for l in locs if l.endswith("_page/")]
        site_ok[base] = f"ok:{len(pages)}"
        for l in pages:
            txt = l[:-6] + ".txt"
            path = urllib.parse.urlparse(txt).path
            segs = unquote_segs(path)
            if len(segs) < 2:
                continue
            cat, name = segs[0], segs[-1]
            if not name.lower().endswith(".txt"):
                continue
            books.append({"site": base, "cat": cat, "title": name[:-4], "url": txt})
    except Exception as e:
        site_ok[base] = f"ERR:{type(e).__name__}:{str(e)[:100]}"

hist = collections.Counter(initial_of(b["title"]) for b in books)
out = {
    "total": len(books),
    "site_status": site_ok,
    "hist": dict(sorted(hist.items())),
    "samples": {k: [b["title"] for b in books if initial_of(b["title"]) == k][:3] for k in sorted(hist)},
}
with open("_survey.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print("站点状态:", json.dumps(site_ok, ensure_ascii=False))
print("书目总数:", len(books))
print("首拼分布:")
for k, v in sorted(hist.items()):
    print(f"  {k}: {v}")
