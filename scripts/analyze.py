#!/usr/bin/env python3
"""Parse the crawled pages in pages/ into data/audit.json and print the on-page report.

Usage:
    scripts/probe.sh <url>          # single-URL status + canonical probe
    xargs -a data/urls.txt -P10 -I{} scripts/probe.sh "{}" > data/probe.tsv
    awk -F'\t' '$1==200{print $2}' data/probe.tsv > data/live.txt
    xargs -a data/live.txt -P10 -I{} scripts/grab.sh "{}"
    python3 scripts/analyze.py
"""
import collections
import json
import os
import re

PAGES = "pages"
OUT = "data/audit.json"


def meta(head, name, attr="name"):
    m = re.search(r'<meta[^>]*%s=["\']%s["\'][^>]*>' % (attr, re.escape(name)), head, re.I)
    if not m:
        return ""
    c = re.search(r'content=["\']([^"\']*)', m.group(0), re.I)
    return c.group(1) if c else ""


def parse(path, url):
    h = open(path, encoding="utf-8", errors="replace").read()
    head = h.split("</head>")[0]
    title = re.search(r"<title>(.*?)</title>", head, re.S)
    h1 = [
        re.sub(r"\s+", " ", re.sub("<[^>]+>", "", x)).strip()
        for x in re.findall(r"<h1[^>]*>(.*?)</h1>", h, re.S | re.I)
    ]
    blocks = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', h, re.S
    )
    types, empty = set(), 0
    for b in blocks:
        if not b.strip():
            empty += 1
            continue
        types |= set(re.findall(r'"@type"\s*:\s*"([^"]+)"', b))
    return dict(
        url=url,
        title=title.group(1).strip() if title else "",
        desc=meta(head, "description"),
        og_type=meta(head, "og:type", "property"),
        og_img=meta(head, "og:image", "property"),
        og_url=meta(head, "og:url", "property"),
        tw_title=meta(head, "twitter:title"),
        h1=h1,
        types=sorted(types),
        nld=len(blocks),
        empty=empty,
        imgs=len(re.findall(r"<img", h)),
        noalt=len(re.findall(r"<img(?![^>]*\balt=)[^>]*>", h)),
    )


def main():
    rows = []
    for fn in sorted(os.listdir(PAGES)):
        if not fn.endswith(".html"):
            continue
        url = "https://inbeat.agency/" + fn[:-5].replace("__", "/").replace("HOME", "")
        rows.append(parse(os.path.join(PAGES, fn), url))
    json.dump(rows, open(OUT, "w"), indent=1)

    def sec(t):
        print("\n" + "=" * 66 + "\n" + t + "\n" + "=" * 66)

    sec("TITLES")
    print("over 60 chars:", sum(1 for r in rows if len(r["title"]) > 60), "/", len(rows))
    print("under 30 chars:", sum(1 for r in rows if 0 < len(r["title"]) < 30))
    dup = collections.Counter(r["title"] for r in rows if r["title"])
    for t, c in dup.most_common(5):
        if c > 1:
            print(f"  duplicate x{c}: {t[:70]}")

    sec("META DESCRIPTIONS")
    print("missing:", [r["url"] for r in rows if not r["desc"]])
    print("under 70 chars:", sum(1 for r in rows if 0 < len(r["desc"]) < 70))

    sec("H1")
    for r in rows:
        if len(r["h1"]) != 1:
            print(f"  {len(r['h1'])} H1s: {r['url']}")

    sec("SCHEMA TYPES IN STATIC HTML")
    tc = collections.Counter()
    for r in rows:
        tc.update(r["types"])
    for t, c in tc.most_common():
        print(f"  {c:4}  {t}")
    print("\npages with an empty ld+json tag:", sum(1 for r in rows if r["empty"]))

    sec("OPEN GRAPH")
    for field in ("og_type", "og_img", "og_url", "tw_title"):
        print(f"  missing {field}:", sum(1 for r in rows if not r[field]))
    print("  og:type=website:", sum(1 for r in rows if r["og_type"] == "website"))


if __name__ == "__main__":
    main()
