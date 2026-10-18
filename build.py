#!/usr/bin/env python3
"""Build agreatsign.si.

src/<slug>.html holds each page's <main> content, preceded by a JSON front-matter
line: <!--{"title":..., "description":..., "nav":..., "crumbs":[...]}-->
Output:
  dist/     production files, clean URLs (/revelation-12), served by .htaccess
  preview/  same pages with .html links, for the artifact preview
"""
import json, re, shutil, datetime, pathlib

ROOT = pathlib.Path(__file__).parent
SRC, DIST, PREV = ROOT / "src", ROOT / "dist", ROOT / "preview"
SITE = "https://agreatsign.si"
TODAY = datetime.date.today().isoformat()
# Changes whenever style.css changes, so browsers holding a week-old copy fetch the new one.
import hashlib
CSS_VERSION = hashlib.md5((ROOT / "assets" / "style.css").read_bytes()).hexdigest()[:8]

# Charter rule 7 (truthful about who did what). Pages are researched and written with
# Claude and directed by Fr. John; a page he wrote himself sets "credit": "fr-john" in
# its front matter. Fr. John is named as founder, never as author of pages he did not write.
CREDIT_CLAUDE = "Researched and written with Claude, an AI model made by Anthropic. Directed by Fr. John."
CREDIT_FR_JOHN = "Written by Fr. John."
INDEPENDENCE = ("An independent project. Fr. John is a Catholic diocesan priest, but this project is his own "
                "and is not affiliated with or endorsed by his diocese, the USCCB, Anthropic, or any other organization.")
FOUNDER = {"@type": "Person", "name": "Fr. John", "url": SITE + "/about", "jobTitle": "Catholic diocesan priest",
           "description": "Founder and director of A Great Sign"}
SITE_ORG = {"@type": "Organization", "name": "A Great Sign", "url": SITE + "/", "founder": FOUNDER}

def credit_of(meta):
    return CREDIT_FR_JOHN if meta.get("credit") == "fr-john" else CREDIT_CLAUDE

# The mark "✓ Reviewed by Fr. John" appears only on pages he has read and approved.
# Such a page sets "reviewed": "YYYY-MM-DD" (the date he approved it) in its front matter.
REVIEWED = "✓ Reviewed by Fr. John"

def reviewed_mark(meta, cls="reviewed"):
    d = meta.get("reviewed")
    if not d:
        return ""
    nice = datetime.date.fromisoformat(d).strftime("%B %-d, %Y")
    return f'<span class="{cls}" title="Read and approved by Fr. John on {nice}">{REVIEWED}</span>'

def add_review(body, meta):
    """Show the review mark under the breadcrumb line."""
    mark = reviewed_mark(meta)
    if not mark:
        return body
    link = "" if meta.get("crumbs", [[None, None]])[-1][1] == "/how-this-site-is-made" else ' <a class="review-how" href="/how-this-site-is-made" target="_blank" rel="noopener">How this site is made</a>'
    line = f'<p class="review-line">{mark}{link}</p>'
    if '<p class="crumbs">' in body:
        return re.sub(r'(<p class="crumbs">.*?</p>)', lambda m: m.group(1) + "\n" + line, body, count=1, flags=re.S)
    # pages without a breadcrumb (the home page): put the mark at the top of the first content block
    return re.sub(r'(</section>\s*<div class="wrap[^"]*">)', lambda m: m.group(1) + "\n" + line, body, count=1)

def fix_ld(ld, meta):
    """Name the true author in structured data and repeat the page's credit line."""
    if not isinstance(ld, dict):
        return ld
    ld = dict(ld)
    if "author" in ld:
        ld["author"] = FOUNDER if meta.get("credit") == "fr-john" else SITE_ORG
        ld["creditText"] = credit_of(meta)
    if meta.get("reviewed"):
        ld["reviewedBy"] = FOUNDER
        ld["lastReviewed"] = meta["reviewed"]
    return ld

NAV = [
    ("/", "Home"),
    ("/the-bible", "The Bible"),
    ("/apparitions", "Apparitions"),
    ("/fathers-saints-teachers", "Fathers, Saints & Teachers"),
    ("/revelation-12", "Revelation 12"),
    ("/about", "About"),
]

LOGO = ('<svg viewBox="0 0 64 64" aria-hidden="true">'
        + '<g transform="translate(32.00 21.95) scale(0.739) translate(-32.00 -21.95)"><g fill="#1f3f73" color="#1f3f73"><path d="M26.09 31.90 C23.81 35.20 22.89 37.90 24.00 39.93 C26.31 39.88 28.19 37.73 29.91 34.10 Z"/><path d="M22.94 28.11 C19.04 31.55 16.86 34.51 17.16 37.01 C19.66 37.31 22.62 35.13 26.06 31.22 Z"/><path d="M19.90 24.43 C14.47 27.18 11.06 29.78 10.48 32.41 C13.04 33.21 17.00 31.56 22.10 28.24 Z"/><path d="M16.93 20.87 C10.21 22.33 5.70 24.11 4.22 26.56 C6.73 27.94 11.52 27.22 18.07 25.13 Z"/><path d="M14.00 17.47 C6.39 17.14 1.05 17.69 -1.23 19.67 C1.05 21.65 6.39 22.20 14.00 21.87 Z"/><path d="M11.07 14.21 C3.12 11.74 -2.65 10.76 -5.58 12.03 C-3.68 14.58 1.81 16.62 9.93 18.46 Z"/><path d="M8.10 11.09 C0.47 6.31 -5.26 3.64 -8.59 4.00 C-7.24 7.06 -2.06 10.69 5.90 14.91 Z"/><path d="M28.00 33.00 Q17.50 10.00 7.00 13.00" fill="none" stroke="currentColor" stroke-width="4.2" stroke-linecap="round"/><path d="M34.09 34.10 C35.81 37.73 37.69 39.88 40.00 39.93 C41.11 37.90 40.19 35.20 37.91 31.90 Z"/><path d="M37.94 31.22 C41.38 35.13 44.34 37.31 46.84 37.01 C47.14 34.51 44.96 31.55 41.06 28.11 Z"/><path d="M41.90 28.24 C47.00 31.56 50.96 33.21 53.52 32.41 C52.94 29.78 49.53 27.18 44.10 24.43 Z"/><path d="M45.93 25.13 C52.48 27.22 57.27 27.94 59.78 26.56 C58.30 24.11 53.79 22.33 47.07 20.87 Z"/><path d="M50.00 21.87 C57.61 22.20 62.95 21.65 65.23 19.67 C62.95 17.69 57.61 17.14 50.00 17.47 Z"/><path d="M54.07 18.46 C62.19 16.62 67.68 14.58 69.58 12.03 C66.65 10.76 60.88 11.74 52.93 14.21 Z"/><path d="M58.10 14.91 C66.06 10.69 71.24 7.06 72.59 4.00 C69.26 3.64 63.53 6.31 55.90 11.09 Z"/><path d="M36.00 33.00 Q46.50 10.00 57.00 13.00" fill="none" stroke="currentColor" stroke-width="4.2" stroke-linecap="round"/></g><circle cx="32" cy="15" r="13.4" fill="#ffffff"/><polygon points="32.00,2.50 32.66,4.09 34.38,4.23 33.07,5.35 33.47,7.02 32.00,6.12 30.53,7.02 30.93,5.35 29.62,4.23 31.34,4.09" fill="#c9a243"/><polygon points="38.25,4.17 38.03,5.88 39.45,6.86 37.75,7.18 37.26,8.83 36.44,7.31 34.72,7.36 35.90,6.11 35.33,4.48 36.88,5.22" fill="#c9a243"/><polygon points="42.83,8.75 41.78,10.12 42.52,11.67 40.89,11.10 39.64,12.28 39.69,10.56 38.17,9.74 39.82,9.25 40.14,7.55 41.12,8.97" fill="#c9a243"/><polygon points="44.50,15.00 42.91,15.66 42.77,17.38 41.65,16.07 39.98,16.47 40.88,15.00 39.98,13.53 41.65,13.93 42.77,12.62 42.91,14.34" fill="#c9a243"/><polygon points="42.83,21.25 41.12,21.03 40.14,22.45 39.82,20.75 38.17,20.26 39.69,19.44 39.64,17.72 40.89,18.90 42.52,18.33 41.78,19.88" fill="#c9a243"/><polygon points="38.25,25.83 36.88,24.78 35.33,25.52 35.90,23.89 34.72,22.64 36.44,22.69 37.26,21.17 37.75,22.82 39.45,23.14 38.03,24.12" fill="#c9a243"/><polygon points="32.00,27.50 31.34,25.91 29.62,25.77 30.93,24.65 30.53,22.98 32.00,23.88 33.47,22.98 33.07,24.65 34.38,25.77 32.66,25.91" fill="#c9a243"/><polygon points="25.75,25.83 25.97,24.12 24.55,23.14 26.25,22.82 26.74,21.17 27.56,22.69 29.28,22.64 28.10,23.89 28.67,25.52 27.12,24.78" fill="#c9a243"/><polygon points="21.17,21.25 22.22,19.88 21.48,18.33 23.11,18.90 24.36,17.72 24.31,19.44 25.83,20.26 24.18,20.75 23.86,22.45 22.88,21.03" fill="#c9a243"/><polygon points="19.50,15.00 21.09,14.34 21.23,12.62 22.35,13.93 24.02,13.53 23.12,15.00 24.02,16.47 22.35,16.07 21.23,17.38 21.09,15.66" fill="#c9a243"/><polygon points="21.17,8.75 22.88,8.97 23.86,7.55 24.18,9.25 25.83,9.74 24.31,10.56 24.36,12.28 23.11,11.10 21.48,11.67 22.22,10.12" fill="#c9a243"/><polygon points="25.75,4.17 27.12,5.22 28.67,4.48 28.10,6.11 29.28,7.36 27.56,7.31 26.74,8.83 26.25,7.18 24.55,6.86 25.97,5.88" fill="#c9a243"/><circle cx="32" cy="15" r="5.8" fill="#c9a243"/><path d="M5 54 Q18 48 32 52.5 T59 51" fill="none" stroke="#d9c08a" stroke-width="2.6" stroke-linecap="round"/><path d="M14 59.5 Q28 56 44 58.5" fill="none" stroke="#d9c08a" stroke-width="2" stroke-linecap="round"/>'
        + '</svg>')


BOOKS = {"Genesis":"genesis","Exodus":"exodus","Leviticus":"leviticus","Numbers":"numbers","Deuteronomy":"deuteronomy",
"Joshua":"joshua","Judges":"judges","Ruth":"ruth","1 Samuel":"1samuel","2 Samuel":"2samuel","1 Kings":"1kings","2 Kings":"2kings",
"1 Chronicles":"1chronicles","2 Chronicles":"2chronicles","Ezra":"ezra","Nehemiah":"nehemiah","Tobit":"tobit","Judith":"judith",
"Esther":"esther","1 Maccabees":"1maccabees","2 Maccabees":"2maccabees","Job":"job","Psalms":"psalms","Psalm":"psalms",
"Proverbs":"proverbs","Ecclesiastes":"ecclesiastes","Song of Songs":"songofsongs","Wisdom":"wisdom","Sirach":"sirach",
"Isaiah":"isaiah","Jeremiah":"jeremiah","Lamentations":"lamentations","Baruch":"baruch","Ezekiel":"ezekiel","Daniel":"daniel",
"Hosea":"hosea","Joel":"joel","Amos":"amos","Obadiah":"obadiah","Jonah":"jonah","Micah":"micah","Nahum":"nahum",
"Habakkuk":"habakkuk","Zephaniah":"zephaniah","Haggai":"haggai","Zechariah":"zechariah","Malachi":"malachi",
"Matthew":"matthew","Mark":"mark","Luke":"luke","John":"john","Acts":"acts","Romans":"romans","1 Corinthians":"1corinthians",
"2 Corinthians":"2corinthians","Galatians":"galatians","Ephesians":"ephesians","Philippians":"philippians","Colossians":"colossians",
"1 Thessalonians":"1thessalonians","2 Thessalonians":"2thessalonians","1 Timothy":"1timothy","2 Timothy":"2timothy","Titus":"titus",
"Philemon":"philemon","Hebrews":"hebrews","James":"james","1 Peter":"1peter","2 Peter":"2peter","1 John":"1john","2 John":"2john",
"3 John":"3john","Jude":"jude","Revelation":"revelation"}
_names = sorted(BOOKS, key=len, reverse=True)
REF = re.compile(r"(?<![\w])(" + "|".join(re.escape(n) for n in _names) + r")\s(\d{1,3})(?:[:.](\d{1,3}[a-z]{0,2}(?:[–-]\d{1,3}[a-z]{0,2})?))?(?:[–-]\d{1,3}(?::\d{1,3})?)?(?!\w|:\d)")
SKIP = {"a", "h1", "h2", "h3", "title", "script", "style", "head", "button"}

def link_scripture(html):
    out, depth = [], 0
    for part in re.split(r"(<[^>]+>)", html):
        if part.startswith("<"):
            m = re.match(r"<(/?)([a-zA-Z0-9]+)", part)
            if m and m.group(2).lower() in SKIP and not part.endswith("/>"):
                depth += -1 if m.group(1) else 1
            out.append(part)
        elif depth > 0 or not part.strip():
            out.append(part)
        else:
            def rep(m):
                ch = m.group(2)
                return (f'<a class="sref" href="https://bible.usccb.org/bible/{BOOKS[m.group(1)]}/{ch}" '
                        f'target="_blank" rel="noopener">{m.group(0)}</a>')
            out.append(REF.sub(rep, part))
    return "".join(out)

KEY = """<details class="key"><summary>Key to the labels</summary>
<div class="key-grid">
<div><p class="label">How a passage stands</p>
<p><span class="badge b-fulfilled">Fulfilled</span> Accomplished in history, above all in Christ.</p>
<p><span class="badge b-unfolding">Unfolding</span> Being worked out now in the life of the Church.</p>
<p><span class="badge b-future">Future</span> Clearly still to come at Christ's return.</p>
<p><span class="badge b-mystery">Mystery</span> Its meaning or moment is not yet settled.</p></div>
<div><p class="label">What kind of passage it is</p>
<p><span class="badge b-form">Prophecy</span> God's word through a prophet, or Christ, about what will come.</p>
<p><span class="badge b-form">Promise</span> A pledge God makes, kept over generations.</p>
<p><span class="badge b-form">Type</span> A person or event that foreshadows Christ or the Church.</p>
<p><span class="badge b-form">Image</span> A picture Scripture returns to and completes at the end.</p>
<p><span class="badge b-form">Apocalypse</span> A vision unveiling history from heaven's side, in symbols.</p></div>
</div>
<p class="key-more"><a href="/the-bible#how-passages-are-labeled">More on the labels</a></p>
</details>"""

def page(slug, meta, body):
    path = "/" if slug == "index" else f"/{slug}"
    nav = "".join(
        f'<li><a href="{h}"{" aria-current=page" if h == path else ""}>{t}</a></li>' for h, t in NAV)
    crumbs = ""
    if meta.get("crumbs"):
        items = [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + (u if u != "/" else "/")}
                 for i, (n, u) in enumerate(meta["crumbs"])]
        crumbs = ('<script type="application/ld+json">' +
                  json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}) +
                  "</script>")
    ld = fix_ld(meta.get("ld", ""), meta)
    if ld:
        ld = '<script type="application/ld+json">' + json.dumps(ld) + "</script>"
    title = meta["title"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{meta['description']}">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:type" content="{'website' if slug=='index' else 'article'}">
<meta property="og:site_name" content="A Great Sign">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta['description']}">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/assets/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Inter:wght@400;600;700&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/style.css?v={CSS_VERSION}">
{crumbs}{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-head"><div class="wrap">
<a class="brand" href="/">{LOGO}A Great Sign</a>
<button class="nav-toggle" aria-expanded="false" aria-controls="nav">Menu</button>
<nav class="nav" id="nav" aria-label="Main"><ul>{nav}</ul></nav>
</div></header>
<main id="main">
{body}
</main>
<footer class="site-foot"><div class="wrap">
<div class="cols">
<div><h4>A Great Sign</h4><p>Biblical prophecy, approved Marian apparitions and the witness of the Fathers and saints, read with the Catholic Church.</p></div>
<div><h4>Explore</h4><ul>{''.join(f'<li><a href="{h}">{t}</a></li>' for h, t in NAV[1:])}<li><a href="/contact">Contact</a></li><li><a href="/how-this-site-is-made">How This Site Is Made</a></li></ul></div>
<div><h4>Related study</h4><ul><li><a href="https://thelambsvictory.org/" target="_blank" rel="noopener">The Lamb's Victory</a>: Revelation chapter by chapter</li></ul></div>
</div>
<p class="credit">{credit_of(meta)}{(" " + reviewed_mark(meta)) if meta.get("reviewed") else ""} <a href="/how-this-site-is-made">How this site is made</a></p>
<p class="fine">{INDEPENDENCE}</p>
<p class="fine">© {datetime.date.today().year} Fr. John · Scripture quotations are from the New American Bible, Revised Edition © 2010, 1991, 1986, 1970 Confraternity of Christian Doctrine, Washington, D.C., used by permission. All rights reserved.</p>
</div></footer>
<script>
document.querySelector('.nav-toggle').addEventListener('click',function(){{var n=document.getElementById('nav');var o=n.classList.toggle('open');this.setAttribute('aria-expanded',o)}});
</script>
</body>
</html>
"""

def to_preview(html):
    # turn absolute site links into relative .html links for the preview
    def fix(m):
        attr, url = m.group(1), m.group(2)
        if url == "/":
            return f'{attr}="index.html"'
        if url.startswith("/assets/"):
            return f'{attr}="{url[1:]}"'
        frag = ""
        if "#" in url:
            url, frag = url.split("#", 1); frag = "#" + frag
        return f'{attr}="{url[1:]}.html{frag}"'
    return re.sub(r'(href|src)="(/[^"/][^"]*|/)"', fix, html)

def main():
    for d in (DIST, PREV):
        if d.exists(): shutil.rmtree(d)
        (d / "assets").mkdir(parents=True)
        for f in (ROOT / "assets").iterdir(): shutil.copy(f, d / "assets" / f.name)
    urls = []
    for f in sorted(SRC.glob("*.html")):
        text = f.read_text()
        m = re.match(r"<!--(\{.*?\})-->\n", text, re.S)
        meta, body = json.loads(m.group(1)), text[m.end():]
        body = add_review(link_scripture(body.replace('<!--KEY-->', KEY)), meta)
        html = page(f.stem, meta, body)
        (DIST / f"{f.stem}.html").write_text(html)
        (PREV / f"{f.stem}.html").write_text(to_preview(html))
        if f.stem != "404": urls.append("/" if f.stem == "index" else f"/{f.stem}")
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"  <url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    (DIST / ".htaccess").write_text("""Options -Indexes
DirectoryIndex index.html
ErrorDocument 404 /404.html
RewriteEngine On
# https and no www
RewriteCond %{HTTPS} off [OR]
RewriteCond %{HTTP_HOST} ^www\\. [NC]
RewriteRule ^ https://agreatsign.si%{REQUEST_URI} [L,R=301]
# /page.html -> /page
RewriteCond %{THE_REQUEST} \\s/+(.+?)\\.html[\\s?] [NC]
RewriteRule ^ /%1 [L,R=301]
# old builder addresses
RewriteRule ^about-biblical-prophecy/?$ /about [L,R=301]
# /page -> page.html
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME}.html -f
RewriteRule ^(.+?)/?$ $1.html [L]
<IfModule mod_expires.c>
ExpiresActive On
ExpiresByType text/css "access plus 1 week"
ExpiresByType image/svg+xml "access plus 1 month"
</IfModule>
""")
    print("built", len(urls), "pages:", ", ".join(urls))

if __name__ == "__main__":
    main()
