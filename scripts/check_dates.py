#!/usr/bin/env python3
"""Pre-flight for phase 1: prove the ISO date conversion handles every live post.

Extracts the #datePublished and #updatedOn strings from every crawled post in
pages/, then runs the *actual* toISODate function from the proposed template
script against them in Chromium — not a Python approximation, since the
conversion depends on JavaScript's Date parsing.

    python3 scripts/check_dates.py

Exits non-zero if any date string fails to convert, which would mean phase 1
would ship a post with a missing or malformed date.
"""

import json
import os
import re
import sys
from collections import Counter

from playwright.sync_api import sync_playwright

PAGES = "pages"
SCRIPT = "webflow/proposed/detail_blog.footer.schema.js"


def extract():
    rows = []
    for fn in sorted(os.listdir(PAGES)):
        if not fn.startswith("blog__"):
            continue
        html = open(os.path.join(PAGES, fn), encoding="utf-8", errors="replace").read()

        def grab(element_id):
            m = re.search(r'id="%s"[^>]*>(.*?)</div>' % element_id, html, re.S)
            return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else None

        rows.append({"page": fn, "pub": grab("datePublished"), "upd": grab("updatedOn")})
    return rows


def to_iso_impl():
    """Slice the real toISODate out of the proposed script so the two cannot drift."""
    src = open(SCRIPT, encoding="utf-8").read()
    start = src.index("function toISODate")
    end = src.index("// Collapse the real byline")
    return src[start:end]


def main():
    rows = extract()
    if not rows:
        sys.exit("no crawled posts in pages/ — run the crawl first, see README")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/opt/pw-browsers/chromium", args=["--no-sandbox"])
        page = browser.new_page()
        page.goto("about:blank")
        results = page.evaluate(
            """([impl, rows]) => {
                const toISODate = new Function(impl + '; return toISODate;')();
                return rows.map(r => ({
                    page: r.page,
                    pub: r.pub, pubISO: toISODate(r.pub),
                    upd: r.upd, updISO: toISODate(r.upd)
                }));
            }""",
            [to_iso_impl(), rows],
        )
        browser.close()

    bad = [r for r in results if (r["pub"] and not r["pubISO"]) or (r["upd"] and not r["updISO"])]
    missing = [r for r in results if not r["pub"]]

    print(f"posts tested            : {len(results)}")
    print(f"publish dates parsed OK : {sum(1 for r in results if r['pubISO'])}")
    print(f"updated dates parsed OK : {sum(1 for r in results if r['updISO'])}")
    print(f"UNPARSEABLE             : {len(bad)}")
    print(f"no publish date in DOM  : {len(missing)}")
    for r in missing:
        print("   ", r["page"])

    years = Counter(r["pubISO"][:4] for r in results if r["pubISO"])
    print("\npublish year spread:", dict(sorted(years.items())))
    odd = [r for r in results if r["pubISO"] and not ("2023" <= r["pubISO"][:4] <= "2026")]
    if odd:
        print("\nimplausible publish dates — likely typos, worth a content check:")
        for r in odd:
            print(f"   {r['pubISO']}  {r['page']}")

    if bad:
        print("\nFAILED — these would ship with a missing or malformed date:")
        for r in bad:
            print(f"   {r['page']}  pub={r['pub']!r}  upd={r['upd']!r}")
        sys.exit(1)
    print("\nOK — every date string converts cleanly.")


if __name__ == "__main__":
    main()
