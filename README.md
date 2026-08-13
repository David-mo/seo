# inbeat.agency — on-page SEO audit

Crawl, analysis scripts and findings for the August 2026 on-page audit of
[inbeat.agency](https://inbeat.agency), plus the remediation plan to be executed
through the Webflow MCP server.

**Report:** `report/inbeat-onpage-audit.html`

Scope: 445 sitemap URLs probed, 421 live pages fetched and parsed, structured data
verified against a headless-Chromium render, and the Webflow project read directly
(6 CMS collections, 173 pages, template custom code).

## Headline findings

| # | Severity | Finding |
|---|----------|---------|
| 1 | Critical | Article schema throws on all 264 blog posts — the template reads `#dateUpdated`, the DOM renders `id="updatedOn"` |
| 2 | Critical | The fallback ships `author: Organization` with no `datePublished` or `dateModified` |
| 3 | Critical | Author bylines split across three URL patterns — 147 through a 301, 34 to `href="#"` |
| 4 | Critical | Two competing author page systems; the sitemap submits the weaker set, which nothing links to |
| 5 | High | No `Person` or `ProfilePage` schema anywhere; Authors collection has only Bio/Name/Slug |
| 6 | High | 9 of 16 authors have empty bios; 5 records look like placeholders |
| 7 | High | All structured data is JavaScript-injected — invisible to non-rendering AI crawlers |
| 8 | High | The `title-tag` CMS field is ignored by the template; 257 of 421 titles exceed 60 chars |
| 9 | Medium | Category pages use the URL slug as their meta description |
| 10 | Medium | 24 sitemap URLs return 301; `og:type` is `website` sitewide; 155 pages lack `og:image` |

### Verifying finding 1

```
$ grep -l 'id="dateUpdated"' pages/blog__*.html | wc -l     # 0
$ grep -l 'id="updatedOn"'   pages/blog__*.html | wc -l     # 264
```

A headless render of a live post throws `Cannot read properties of null (reading
'innerHTML')` and produces no Article node.

## Reproducing the crawl

`pages/` (62MB of fetched HTML) is gitignored. To rebuild it:

```bash
curl -sS https://inbeat.agency/sitemap.xml \
  | grep -o '<loc>[^<]*</loc>' | sed 's/<[^>]*>//g' > data/urls.txt

xargs -a data/urls.txt -P10 -I{} scripts/probe.sh "{}" > data/probe.tsv
awk -F'\t' '$1==200{print $2}' data/probe.tsv > data/live.txt

mkdir -p pages
xargs -a data/live.txt -P10 -I{} scripts/grab.sh "{}"
python3 scripts/analyze.py
```

## Layout

```
scripts/probe.sh    status code, redirect target, canonical and title per URL
scripts/grab.sh     fetch one page into pages/
scripts/analyze.py  parse pages/ into data/audit.json and print the report
data/               derived crawl data (committed — small)
report/             the audit deliverable
```

## Webflow reference

Site `65f9d9d22fb2f3b3f17c09ed`. IDs referenced by the remediation plan:

| Resource | ID |
|----------|-----|
| Blogs collection | `65f9d9d22fb2f3b3f17c0a73` |
| Authors collection | `6984ac7958fada1768844771` |
| Categories collection | `67339307763062df26089ef5` |
| Blog template (`detail_blog`) | `65f9d9d22fb2f3b3f17c0a39` |
| Author template (`detail_author`) | `6984ac7958fada1768844779` |
| Category template (`detail_categories`) | `67339307763062df26089fd5` |

Three fixes are not reachable through MCP and need the Webflow Designer or Site
Settings: the byline link binding, the template title-tag binding, and all 301
redirects.

## Known limitation

The Webflow CMS list endpoint ignored the `offset` parameter, so blog-item field
statistics come from the first 100 of 402 items. The Authors collection (16 items)
and all page-level findings are complete.
