# Webflow changes

Proposed replacements for Webflow custom code, kept under version control so
every production change is reviewable and revertible.

## `proposed/detail_blog.footer.schema.js` — phase 1

Replaces the broken `Article` builder in the **Blogs Template** (`detail_blog`,
page `65f9d9d22fb2f3b3f17c0a39`) footer custom code.

The current script reads the modified date from `#dateUpdated`. The template
renders that element as `id="updatedOn"`, so `querySelector` returns `null`,
`.innerHTML` throws, and the script aborts before injecting anything. A
site-wide fallback then ships `BlogPosting` with `author: Organization` and no
dates. This affects all 264 published posts.

### Verified in a headless render

Against three real saved pages, one per byline shape:

| Byline in DOM | Posts | `author.url` emitted |
|---|---:|---|
| `/author/tereza-spaseska` | 83 | `/author/tereza-spaseska` |
| `/blog/author/sehar-fatima` | 147 | `/author/sehar-fatima` — 301 hop removed |
| `href="#"` | 34 | omitted, `name` only |

Dates convert correctly (`March 19, 2026` → `2026-03-19`), and the fallback's
`#global-blogposting-schema` node is removed before ours is appended.

The `href="#"` case deliberately omits `url`. Slugifying the display name there
invents URLs that 404 — "Luz Marina Dugarte Pulpeiro" yields
`/author/luz-marina-dugarte-pulpeiro` when the CMS slug is `luz`. Those posts
get a `Person` with a name only until the phase 2 Designer rebind supplies a
real `href`.

### Applying

1. Fetch and save the current footer code as the rollback copy:
   `data_scripts_tool > get_page_freeform_code` on `65f9d9d22fb2f3b3f17c0a39`,
   written to `backup/detail_blog.footer.<timestamp>.html`.
2. Swap only the `<script type="text/javascript">` block containing
   `querySelector('#dateUpdated')` for the contents of the proposed file. Leave
   the `<style>` block, the TOC builder, the progress bar, the slide-in CTA and
   the `rich-text-performance.js` tag untouched.
3. `data_scripts_tool > set_page_freeform_code`.
4. Publish — see the caveat below.
5. Re-run the headless check against a live post and validate in Google's Rich
   Results Test.

### Rollback

Restore the saved `backup/` copy through `set_page_freeform_code` and republish.
The change is confined to one page's custom code and touches no CMS data.

## Publishing caveat

Publishing pushes the whole site. Draft pages and draft CMS items are excluded
by Webflow, so those are not a risk — but any **non-draft** staged change is.

At the time of the audit the site had unpublished changes:

```
lastPublished  2026-08-13 15:57:09
lastUpdated    2026-08-13 17:24:51
```

Check `data_sites_tool > get_site` and compare the two before publishing. If
`lastUpdated` is newer, someone has staged work that will go live alongside this
change.
