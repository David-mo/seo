#!/usr/bin/env python3
"""Build the shareable SEO fix tracker workbook from the audit findings."""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

OUT = "report/inbeat-seo-fix-tracker.xlsx"

FONT = "Arial"
INK = "1A1420"
ACCENT = "8C1D3F"
HDR_FILL = PatternFill("solid", fgColor="1A1420")
EDIT_FILL = PatternFill("solid", fgColor="FFF9DB")
BAND = PatternFill("solid", fgColor="F5F3F7")
OWNER_FILL = {
    "MCP": PatternFill("solid", fgColor="E3F1EB"),
    "Designer": PatternFill("solid", fgColor="FBEEDD"),
    "Settings": PatternFill("solid", fgColor="E7EDF7"),
    "inBeat": PatternFill("solid", fgColor="F5E6EC"),
}
PRIO_FONT = {
    "Critical": Font(name=FONT, size=10, bold=True, color="A3201B"),
    "High": Font(name=FONT, size=10, bold=True, color="8A4B00"),
    "Medium": Font(name=FONT, size=10, color="3F5A8A"),
    "Low": Font(name=FONT, size=10, color="736C80"),
}
THIN = Side(style="thin", color="D8D4E0")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

# id, phase, priority, area, change, why, scale, owner, tool/location, blocked by
FIXES = [
    # ---- MCP: structured data & custom code
    (1, "1", "Critical", "Schema", "Point the date selector at #updatedOn",
     "Template renders id=updatedOn but the script reads #dateUpdated, so it throws on null and aborts before injecting anything",
     "264 posts", "MCP", "set_page_freeform_code · detail_blog", "Publishing window (36)"),
    (2, "1", "Critical", "Schema", "Convert both dates to ISO 8601",
     "The DOM holds 'March 19, 2026', which is not a valid datePublished value even once the selector is fixed",
     "264 posts", "MCP", "set_page_freeform_code · detail_blog", "Publishing window (36)"),
    (3, "1", "Critical", "Schema", "Emit author as Person with @id on a normalised /author/ URL",
     "Live schema credits the Organization; bylines otherwise pass 301 URLs straight into the markup",
     "264 posts", "MCP", "set_page_freeform_code · detail_blog", "Publishing window (36)"),
    (4, "1", "High", "Schema", "Add @id and mainEntityOfPage; reference Organization by @id",
     "Removes the stale uploads-ssl.webflow.com logo URL and ties the post to the existing Organization node",
     "264 posts", "MCP", "set_page_freeform_code · detail_blog", "Publishing window (36)"),
    (5, "1", "Critical", "Schema", "Remove the site-wide fallback node before appending",
     "Fallback ships BlogPosting with author: Organization and no dates on every post",
     "264 posts", "MCP", "set_page_freeform_code · detail_blog", "Publishing window (36)"),
    (6, "4", "High", "Author", "ProfilePage + Person schema bound to the new author fields",
     "No Person or ProfilePage schema exists anywhere on the site today",
     "16 pages", "MCP", "set_page_freeform_code · detail_author", "Fields (11), content (39)"),
    (7, "6", "Medium", "Category", "CollectionPage + ItemList on category pages",
     "Category pages carry no page-level schema at all",
     "10 pages", "MCP", "set_page_freeform_code · detail_categories", "Fields (12)"),
    (8, "7", "Medium", "Schema", "FAQPage schema for the five homepage Q&As",
     "Homepage FAQ renders as plain H3s; only 12 service pages carry FAQPage",
     "1 page", "MCP", "set_page_freeform_code · home", ""),
    (9, "7", "Medium", "Schema", "Rewrite breadcrumbs: three tiers, live title, real /blog level",
     "Position 1 is hardcoded to a stale title and posts get Home > Post with no /blog tier",
     "All pages", "MCP", "set_site_freeform_code", ""),
    (10, "7", "Low", "Schema", "Remove the empty ld+json script tag",
     "Ships on 264 pages and trips structured-data validators",
     "264 pages", "MCP", "set_site_freeform_code", ""),
    # ---- MCP: CMS
    (11, "3", "High", "CMS", "Add 6 Authors fields: Job Title, Headshot, LinkedIn, X, Credentials, Meta Description",
     "Collection has only Bio/Name/Slug, so there is nothing to build Person schema from",
     "1 collection", "MCP", "create_collection_static_field", "Designer layout (29)"),
    (12, "6", "Medium", "CMS", "Add Categories fields: Description, Meta Description",
     "Meta description is bound to the slug field, so pages ship descriptions reading 'ugc'",
     "1 collection", "MCP", "create_collection_static_field", ""),
    (13, "5", "Medium", "CMS", "Add a Blogs 'Last Updated' date field",
     "No updated-date field exists; the modified date is typed by hand into a DOM element",
     "1 collection", "MCP", "create_collection_static_field", "Decision (41)"),
    (14, "3", "High", "CMS", "Populate all 16 author records",
     "9 of 16 authors have empty bios, which is why 6 author pages ship with no meta description",
     "16 items", "MCP", "update_collection_items", "Content (39)"),
    (15, "3", "High", "Assets", "Upload headshot assets",
     "No author images exist anywhere in the project",
     "~11 files", "MCP", "data_assets_tool", "Content (39)"),
    (16, "6", "Medium", "Category", "Write descriptions for all 10 categories",
     "Current descriptions are raw slugs: 'ugc', 'advertising', 'ppc-and-google-ads'",
     "10 items", "MCP", "update_collection_items", "Fields (12)"),
    (17, "5", "High", "CMS", "Backfill article-author from the obsolete fields",
     "54 of 100 sampled blog items have no author reference set",
     "~402 items", "MCP", "update_collection_items", ""),
    (18, "5", "Medium", "CMS", "Clear obsolete author-name and author-page fields",
     "59 and 23 of 100 sampled items still carry the deprecated fields",
     "~402 items", "MCP", "update_collection_items", "Backfill (17)"),
    (19, "5", "High", "Meta", "Draft and write title-tag for over-length pages",
     "257 of 421 titles exceed 60 characters; 129 exceed 80; the longest is 118",
     "257 pages", "MCP", "update_collection_items", "Review (42)"),
    # ---- MCP: page settings & sitemap
    (20, "7", "Medium", "Sitemap", "Exclude the 24 redirecting URLs from the sitemap",
     "Sitemap currently submits URLs that return 301",
     "24 URLs", "MCP", "bulk_update_items_sitemap_status", ""),
    (21, "7", "Medium", "Meta", "Set a default og:image on pages without one",
     "155 pages have no og:image, including all 46 locations and 16 case studies",
     "155 pages", "MCP", "bulk_update_pages", ""),
    (22, "7", "Low", "Meta", "Replace the 404 and 401 Webflow template boilerplate",
     "The 401 title still reads 'Lemon - Webflow HTML website template'",
     "2 pages", "MCP", "update_page_settings", ""),
    (23, "7", "Medium", "Meta", "Set og:type to article on blog posts — METHOD TO VERIFY",
     "Webflow emits its own og:type, so a custom-code override risks a duplicate tag; confirm the clean route first",
     "264 posts", "MCP", "TBC — needs verification", ""),
    (24, "all", "Critical", "Publish", "Publish the site",
     "No change reaches inbeat.agency until the site is published",
     "Whole site", "MCP", "publish_site", "Publishing window (36)"),
    # ---- Designer
    (25, "2", "Critical", "Author", "Rebind the byline link to the article-author reference",
     "181 of 264 bylines point at a 301 or at href='#'; this is the root fix",
     "264 posts", "Designer", "detail_blog", "Canonical sign-off (38)"),
    (26, "5", "High", "Meta", "Rebind SEO title to title-tag with name as fallback; delete the double space",
     "Template binds the full article name, producing titles up to 118 characters",
     "264 posts", "Designer", "detail_blog", "Title drafts (19)"),
    (27, "6", "Medium", "Category", "Rebind meta description off slug onto the new Meta Description field",
     "Category descriptions currently render as raw URL slugs",
     "10 pages", "Designer", "detail_categories", "Fields (12)"),
    (28, "4", "High", "Author", "Demote post-card headings from H1 to H2",
     "Author pages carry 2 to 101 H1 tags; one page has 101",
     "16 pages", "Designer", "detail_author", ""),
    (29, "4", "High", "Author", "Add visible bio, headshot and role blocks to the author layout",
     "Person schema describing content the page never renders is a markup/content mismatch",
     "16 pages", "Designer", "detail_author", "Fields (11)"),
    (30, "2", "High", "Author", "Delete or unpublish the 8 static /blog-author/author-blog/ pages",
     "Duplicate author pages that the sitemap submits and nothing links to",
     "8 pages", "Designer", "Pages panel", "Redirects (32)"),
    (31, "6", "Low", "Category", "Optional: move categories to /blog/category/",
     "Categories currently sit nested under the author folder, which is structurally wrong",
     "10 pages", "Designer", "Collection settings", "Decision (43)"),
    # ---- Settings
    (32, "2", "Critical", "Redirects", "301 the 8 /blog-author/author-blog/* URLs onto their CMS equivalents",
     "Consolidates two competing author page systems onto one",
     "8 URLs", "Settings", "Publishing > Redirects", "Canonical sign-off (38)"),
    (33, "2", "High", "Redirects", "Collapse /blog/author/* onto /author/*, including two-hop chains",
     "147 byline links currently pass through at least one redirect",
     "~10 rules", "Settings", "Publishing > Redirects", "Canonical sign-off (38)"),
    (34, "7", "Low", "Sitemap", "Remove the duplicate Sitemap: line from robots.txt",
     "robots.txt declares the same sitemap twice",
     "1 file", "Settings", "SEO > robots.txt", ""),
    (35, "6", "Low", "Redirects", "Redirects for the category URL move",
     "Only needed if the optional category move goes ahead",
     "10 rules", "Settings", "Publishing > Redirects", "Decision (43)"),
    # ---- inBeat
    (36, "all", "Critical", "Decision", "Publishing window, or a branch-and-merge decision",
     "Publishing pushes the whole site; unpublished non-draft changes were staged during the audit",
     "Blocks all", "inBeat", "David", ""),
    (37, "2", "Critical", "Decision", "Designer access, or a named person for changes 25-31",
     "Seven changes are Designer-only and cannot be done through MCP",
     "Blocks 4,5,6", "inBeat", "David", ""),
    (38, "2", "Critical", "Decision", "Sign-off that /author/{slug} is the canonical pattern",
     "Changes 181 internal links and needs a redirect set; not free to reverse",
     "Blocks phase 2", "inBeat", "David", ""),
    (39, "3", "High", "Content", "Role, bio, LinkedIn and headshot for each real author",
     "Person schema with no supporting content is a claim of expertise with no evidence",
     "~11 authors", "inBeat", "Content team", ""),
    (40, "3", "High", "Decision", "Ruling on jhon, sarah, luz, precious, peter",
     "Placeholder author records with no bios, 4 posts between them; 'jhon' looks like a typo",
     "5 records", "inBeat", "David", ""),
    (41, "5", "Medium", "Decision", "Whether dateModified comes from system Last Updated or a new field",
     "Automatic timestamps change on every trivial edit, which dilutes the freshness signal",
     "Blocks 13", "inBeat", "David", ""),
    (42, "5", "Medium", "Review", "Review of the 257 drafted title tags",
     "Titles will be drafted for approval rather than pushed blind",
     "257 pages", "inBeat", "SEO team", "Drafts (19)"),
    (43, "6", "Low", "Decision", "Whether category URLs move now or later",
     "Cleaner structure, but costs another redirect set",
     "Blocks 31,35", "inBeat", "David", ""),
]

FINDINGS = [
    ("F1", "Critical", "Article schema throws on every blog post",
     "detail_blog reads #dateUpdated; the template renders id=updatedOn. querySelector returns null, .innerHTML throws, the script aborts.",
     "id=\"dateUpdated\" in 0 of 264 crawled posts; headless render throws \"Cannot read properties of null\"",
     "264 posts", "1"),
    ("F2", "Critical", "Fallback credits the Organization and drops both dates",
     "A site-wide script injects BlogPosting only when no Article exists, which is always. It sets author to Organization and omits datePublished and dateModified.",
     "Fallback source read directly from site custom code; type guard confirmed",
     "264 posts", "1"),
    ("F3", "Critical", "Author bylines point at three different URL patterns",
     "83 posts use /author/{slug}; 147 use /blog/author/{slug} which 301s, some over two hops; 34 link to href='#'.",
     "Counted across 264 crawled post pages; redirect chains followed with curl",
     "264 posts", "2"),
    ("F4", "Critical", "Two competing author page systems",
     "/author/{slug} (CMS, 16 authors) and /blog-author/author-blog/{slug} (8 static pages) both return 200 and self-canonicalise. The sitemap lists only the static set, which nothing links to.",
     "Both sets crawled; sitemap parsed; internal links counted",
     "24 pages", "2"),
    ("F5", "High", "No Person or ProfilePage schema anywhere",
     "Author pages carry only the site-wide Organization graph. No sameAs, no photo, no job title on any URL.",
     "JSON-LD parsed on all 421 live pages",
     "Whole site", "4"),
    ("F6", "High", "Nine of sixteen authors have no bio; five look like placeholders",
     "The author template binds meta description to the bio field, so an empty bio means no meta description. jhon, sarah, luz, precious and peter have no bios.",
     "Authors collection read in full (16 of 16 items)",
     "16 authors", "3"),
    ("F7", "High", "All structured data is JavaScript-injected",
     "Static HTML contains only the Organization graph. Google renders JS; GPTBot, ClaudeBot, PerplexityBot and CCBot largely do not, and robots.txt invites all of them.",
     "Static HTML parsed on 421 pages; confirmed against headless render",
     "Whole site", "7"),
    ("F8", "High", "The title-tag CMS field is ignored by the template",
     "The template binds the full article name plus a stray double space. Only 2 of 100 sampled items have title-tag filled.",
     "Template SEO binding read via get_page_metadata; 421 titles measured",
     "257 pages", "5"),
    ("F9", "Medium", "Category pages use the URL slug as their meta description",
     "detail_categories binds description to the slug field, producing descriptions reading 'ugc' and 'advertising'. Titles carry no brand suffix.",
     "Template binding read via list_pages; 10 category pages crawled",
     "10 pages", "6"),
    ("F10", "Medium", "24 sitemap URLs return 301",
     "Includes /blog/ab-testing-ugc-ads to /ugc-agency and /blog/top-digital-marketing-agencies-las-vegas to the homepage.",
     "All 445 sitemap URLs probed for status and redirect target",
     "24 URLs", "7"),
    ("F11", "Medium", "og:type is website sitewide and 155 pages lack og:image",
     "All 405 pages that set og:type use 'website', blog posts included. Missing og:image covers all 46 locations, 15 territories, 16 case studies, 18 author pages.",
     "Open Graph tags parsed on all 421 live pages",
     "421 pages", "7"),
    ("F12", "Medium", "Breadcrumbs are two levels and stale",
     "Position 1 is hardcoded to 'inBeat - #1 Micro Influencer Agency in North America', which no longer matches the homepage title. Posts get Home > Post with no /blog tier.",
     "Breadcrumb script read from site custom code",
     "All pages", "7"),
    ("OK1", "Clean", "Canonicals, H1s and alt text are correct",
     "All 421 live pages self-canonicalise with zero missing or mismatched canonicals. Every page has a title. Zero images missing alt. The robots.txt AI-crawler policy is well built.",
     "Full crawl of 421 pages",
     "421 pages", "-"),
]


def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
        cell.fill = HDR_FILL
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        cell.border = BORDER
    ws.row_dimensions[row].height = 30
    # Use a string ref: ws.cell() would instantiate the cell and create an empty
    # row, pushing every appended data row down by one.
    ws.freeze_panes = f"A{row + 1}"


def build():
    wb = Workbook()

    # ---------------------------------------------------------------- Summary
    s = wb.active
    s.title = "Summary"
    s["A1"] = "inBeat on-page SEO — fix tracker"
    s["A1"].font = Font(name=FONT, size=16, bold=True, color=INK)
    s["A2"] = "Audit of inbeat.agency, 13 August 2026. 445 sitemap URLs crawled, 421 live pages parsed."
    s["A2"].font = Font(name=FONT, size=10, color="736C80")
    s["A3"] = "Counts below are live formulas — they update as the team fills in the Status column on 'Fix Tracker'."
    s["A3"].font = Font(name=FONT, size=10, italic=True, color="736C80")

    def block(title, row, pairs, formula):
        s.cell(row=row, column=1, value=title).font = Font(
            name=FONT, size=11, bold=True, color=ACCENT)
        for i, label in enumerate(pairs, start=1):
            s.cell(row=row + i, column=1, value=label).font = Font(name=FONT, size=10)
            c = s.cell(row=row + i, column=2, value=formula(label))
            c.font = Font(name=FONT, size=10)
            c.alignment = Alignment(horizontal="right")
            c.border = BORDER
        return row + len(pairs) + 2

    r = 5
    r = block("By owner", r, ["MCP", "Designer", "Settings", "inBeat"],
              lambda v: f"=COUNTIF('Fix Tracker'!$H$2:$H$200,\"{v}\")")
    r = block("By priority", r, ["Critical", "High", "Medium", "Low"],
              lambda v: f"=COUNTIF('Fix Tracker'!$C$2:$C$200,\"{v}\")")
    r = block("By status", r, ["Not started", "In progress", "Blocked", "Done", "Won't do"],
              lambda v: f"=COUNTIF('Fix Tracker'!$K$2:$K$200,\"{v}\")")

    s.cell(row=r, column=1, value="Total changes").font = Font(name=FONT, size=11, bold=True, color=ACCENT)
    tot = s.cell(row=r, column=2, value="=COUNTA('Fix Tracker'!$A$2:$A$200)")
    tot.font = Font(name=FONT, size=11, bold=True)
    tot.alignment = Alignment(horizontal="right")
    tot.border = BORDER

    r += 2
    s.cell(row=r, column=1, value="% complete").font = Font(name=FONT, size=11, bold=True, color=ACCENT)
    pc = s.cell(row=r, column=2,
                value="=IFERROR(COUNTIF('Fix Tracker'!$K$2:$K$200,\"Done\")/COUNTA('Fix Tracker'!$A$2:$A$200),0)")
    pc.font = Font(name=FONT, size=11, bold=True)
    pc.number_format = "0.0%"
    pc.alignment = Alignment(horizontal="right")
    pc.border = BORDER

    r += 3
    s.cell(row=r, column=1, value="How to use this workbook").font = Font(
        name=FONT, size=11, bold=True, color=ACCENT)
    for i, line in enumerate([
        "Fix Tracker — every change, one per row. Edit only the shaded columns: Status, Assignee, Target date, Notes.",
        "Owner column: MCP = automated via the Webflow API. Designer = Webflow canvas. Settings = Webflow site settings. inBeat = your decision or content.",
        "Findings — the underlying audit evidence, so anyone can verify a fix is warranted before doing it.",
        "Decisions — the eight items blocking work, each with what it unblocks.",
        "Start with phase 1 (rows 1-5). It is one API call and repairs structured data on all 264 posts.",
    ], start=1):
        c = s.cell(row=r + i, column=1, value=line)
        c.font = Font(name=FONT, size=10)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        s.merge_cells(start_row=r + i, start_column=1, end_row=r + i, end_column=6)
        s.row_dimensions[r + i].height = 26

    s.column_dimensions["A"].width = 62
    s.column_dimensions["B"].width = 12
    for col in "CDEF":
        s.column_dimensions[col].width = 14

    # ------------------------------------------------------------ Fix Tracker
    t = wb.create_sheet("Fix Tracker")
    headers = ["ID", "Phase", "Priority", "Area", "Change", "Why it matters", "Scale",
               "Owner", "Tool / location", "Blocked by",
               "Status", "Assignee", "Target date", "Notes"]
    t.append(headers)
    style_header(t, 1, len(headers))

    for row in FIXES:
        t.append(list(row) + ["Not started", "", "", ""])

    widths = [5, 6, 9, 11, 46, 58, 11, 10, 34, 22, 13, 14, 12, 30]
    for i, w in enumerate(widths, start=1):
        t.column_dimensions[get_column_letter(i)].width = w

    for r_ in range(2, t.max_row + 1):
        for c_ in range(1, len(headers) + 1):
            cell = t.cell(row=r_, column=c_)
            cell.font = Font(name=FONT, size=10)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = BORDER
            if c_ in (5, 6, 9):
                cell.alignment = Alignment(wrap_text=True, vertical="top")
            if c_ in (1, 2, 3, 7, 8):
                cell.alignment = Alignment(horizontal="center", vertical="top", wrap_text=True)
        t.cell(row=r_, column=3).font = PRIO_FONT[t.cell(row=r_, column=3).value]
        owner = t.cell(row=r_, column=8).value
        t.cell(row=r_, column=8).fill = OWNER_FILL[owner]
        t.cell(row=r_, column=8).font = Font(name=FONT, size=10, bold=True)
        for c_ in (11, 12, 13, 14):
            t.cell(row=r_, column=c_).fill = EDIT_FILL
        t.row_dimensions[r_].height = 42

    dv = DataValidation(
        type="list",
        formula1='"Not started,In progress,Blocked,Done,Won\'t do"',
        allow_blank=True, showDropDown=False)
    dv.error = "Pick a value from the list."
    dv.errorTitle = "Invalid status"
    t.add_data_validation(dv)
    dv.add(f"K2:K{t.max_row}")

    t.auto_filter.ref = f"A1:N{t.max_row}"

    note = t.cell(row=t.max_row + 2, column=1,
                  value="Shaded columns (Status, Assignee, Target date, Notes) are the only ones to edit. "
                        "Everything to their left is audit output. Row 1 above shows the expected format: "
                        "Status from the dropdown, Assignee as a name, Target date as YYYY-MM-DD.")
    note.font = Font(name=FONT, size=9, italic=True, color="736C80")
    note.alignment = Alignment(wrap_text=True, vertical="top")
    t.merge_cells(start_row=t.max_row, start_column=1, end_row=t.max_row, end_column=10)
    t.row_dimensions[t.max_row].height = 30

    # Example values on the first row so the format is unambiguous.
    t["L2"] = "Claude (MCP)"
    t["M2"] = "2026-08-14"
    t["N2"] = "Code written and tested; awaiting publishing window"

    # -------------------------------------------------------------- Findings
    f = wb.create_sheet("Findings")
    fh = ["Ref", "Severity", "Finding", "Detail", "How it was verified", "Scale", "Phase"]
    f.append(fh)
    style_header(f, 1, len(fh))
    for row in FINDINGS:
        f.append(list(row))
    for i, w in enumerate([7, 10, 44, 68, 52, 12, 7], start=1):
        f.column_dimensions[get_column_letter(i)].width = w
    for r_ in range(2, f.max_row + 1):
        for c_ in range(1, len(fh) + 1):
            cell = f.cell(row=r_, column=c_)
            cell.font = Font(name=FONT, size=10)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = BORDER
        sev = f.cell(row=r_, column=2).value
        f.cell(row=r_, column=2).font = PRIO_FONT.get(
            sev, Font(name=FONT, size=10, bold=True, color="1D6249"))
        f.cell(row=r_, column=3).font = Font(name=FONT, size=10, bold=True)
        if r_ % 2 == 0:
            for c_ in range(1, len(fh) + 1):
                f.cell(row=r_, column=c_).fill = BAND
        f.row_dimensions[r_].height = 56
    f.auto_filter.ref = f"A1:G{f.max_row}"

    # ------------------------------------------------------------- Decisions
    d = wb.create_sheet("Decisions")
    dh = ["Ref", "Decision needed", "Why it matters", "What it unblocks", "Owner", "Answer", "Decided on"]
    d.append(dh)
    style_header(d, 1, len(dh))
    decisions = [(r[0], r[4], r[5], r[9] or "Phase " + r[1], r[8])
                 for r in FIXES if r[7] == "inBeat"]
    for ref, dec, why, _unb, owner in decisions:
        match = next(x for x in FIXES if x[0] == ref)
        d.append([ref, dec, why, match[6], owner, "", ""])
    for i, w in enumerate([7, 52, 62, 18, 16, 34, 13], start=1):
        d.column_dimensions[get_column_letter(i)].width = w
    for r_ in range(2, d.max_row + 1):
        for c_ in range(1, len(dh) + 1):
            cell = d.cell(row=r_, column=c_)
            cell.font = Font(name=FONT, size=10)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = BORDER
        d.cell(row=r_, column=2).font = Font(name=FONT, size=10, bold=True)
        for c_ in (6, 7):
            d.cell(row=r_, column=c_).fill = EDIT_FILL
        d.row_dimensions[r_].height = 48
    d["F2"] = "e.g. Thursday 21 Aug, after the team stands down"
    d["G2"] = "2026-08-14"

    wb.save(OUT)
    print("wrote", OUT)
    print("fix rows:", len(FIXES), "| findings:", len(FINDINGS), "| decisions:", len(decisions))


if __name__ == "__main__":
    build()
