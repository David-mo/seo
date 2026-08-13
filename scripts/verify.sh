#!/bin/bash
# Check the live site's structured data against what the audit found.
#
#   scripts/verify.sh                 # default sample post
#   scripts/verify.sh <blog-url>      # any post
#
# Before phase 1 is applied every BROKEN line below should report 1 and every
# FIXED line 0. After it is applied and published, that inverts.

set -uo pipefail
URL="${1:-https://inbeat.agency/blog/top-digital-marketing-agencies-in-the-us}"
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT

CODE=$(curl -sS -A "Mozilla/5.0" "$URL" -o "$TMP" -w "%{http_code}")
echo "URL    $URL"
echo "HTTP   $CODE   $(wc -c < "$TMP" | tr -d ' ') bytes"
echo

# grep -c prints 0 and exits 1 on no match, so swallow the status, not the output.
count() { grep -c "$1" "$TMP" 2>/dev/null || true; }

echo "BROKEN — expect 1 before phase 1, 0 after"
printf '  %-46s %s\n' "template queries #dateUpdated"        "$(count "querySelector('#dateUpdated')")"
printf '  %-46s %s\n' "fallback node global-blogposting"     "$(count 'global-blogposting-schema')"
echo
echo "FIXED — expect 0 before phase 1, 1 after"
printf '  %-46s %s\n' "new node inbeat-blogposting-schema"   "$(count 'inbeat-blogposting-schema')"
echo
echo "UNCHANGED by phase 1 — these are template facts"
printf '  %-46s %s\n' "renders id=updatedOn"                 "$(count 'id="updatedOn"')"
printf '  %-46s %s\n' "byline element present"               "$(count 'id="authorName"')"
printf '  %-46s %s\n' "byline href"                          "$(grep -o '<a id="authorName" href="[^"]*"' "$TMP" | sed 's/.*href="//;s/"//' || echo none)"
echo
# Parse real <script type="application/ld+json"> blocks only. A plain grep for
# "@type" also matches the JavaScript that *builds* the schema, which makes the
# page look like it already ships Article and Person markup when it does not.
echo "@type values in genuine JSON-LD blocks (JS-injected schema will NOT appear):"
python3 - "$TMP" <<'PY'
import json, re, sys, collections
html = open(sys.argv[1], encoding='utf-8', errors='replace').read()
blocks = re.findall(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.S)
counts, empty = collections.Counter(), 0
for b in blocks:
    if not b.strip():
        empty += 1
        continue
    try:
        counts.update(re.findall(r'"@type"\s*:\s*"([^"]+)"', json.dumps(json.loads(b))))
    except ValueError:
        counts['<unparseable block>'] += 1
print(f"  {len(blocks)} block(s), {empty} empty")
for t, c in counts.most_common():
    print(f"  {c:4}  {t}")
PY
echo
echo "Note: the Article/BlogPosting node is injected by JavaScript, so curl"
echo "cannot see it. Confirm the rendered result in Google's Rich Results Test:"
echo "  https://search.google.com/test/rich-results?url=$(printf '%s' "$URL" | sed 's|:|%3A|g; s|/|%2F|g')"
