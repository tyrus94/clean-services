"""Shared head, header and footer for generated pages.

Cleaning Services Kenya is a service-area business. Work is done at the
customer's property. The only contact details on the site are the phone
number and its WhatsApp link. Do not add a street address, geo
coordinates, or opening hours.
"""
import html
import json
import os

SITE_URL = (os.environ.get("SITE_URL") or "https://www.cleaningserviceskenya.co.ke").rstrip("/")
PHONE_DISPLAY = "+254 706 855633"
PHONE_TEL = "+254706855633"
WHATSAPP_NUMBER = "254706855633"
HOME_TITLE = "Cleaning Services in Nairobi & Across Kenya | Cleaning Services Kenya"
HOME_DESCRIPTION = (
    "Cleaning services in Nairobi and across Kenya. House, office, fumigation, "
    "carpet, sofa and parapet cleaning. Call or WhatsApp +254 706 855633."
)
IMG_FLOOR = "https://raw.githubusercontent.com/zoneislaced/clean-services-kenya/refs/heads/main/Assets/pexels-ron-lach-10568269.jpg"
IMG_HOME = "https://raw.githubusercontent.com/zoneislaced/clean-services-kenya/refs/heads/main/Assets/pexels-tima-miroshnichenko-6195106.jpg"
IMG_WORK = "https://raw.githubusercontent.com/zoneislaced/clean-services-kenya/refs/heads/main/Assets/pexels-tima-miroshnichenko-6195125.jpg"
IMG_TEAM = "https://raw.githubusercontent.com/zoneislaced/clean-services-kenya/refs/heads/main/Assets/pexels-tima-miroshnichenko-6197124.jpg"
OG_IMAGE = IMG_FLOOR

# slug, navigation label
SERVICE_LINKS = [
    ("house-cleaning", "House cleaning"),
    ("office-cleaning", "Office cleaning"),
    ("fumigation", "Fumigation & pest control"),
    ("carpet-cleaning", "Carpet cleaning"),
    ("sofa-cleaning", "Sofa & upholstery"),
    ("parapet-cleaning", "Parapet cleaning"),
]

# Hand-written pages at /cleaning-services/<slug>/. Not rows in towns.csv.
# generate_pages.py refuses these slugs so a town regen cannot replace them.
NAIROBI_AREA_PAGES = [
    ("westlands", "Westlands"),
    ("kilimani", "Kilimani"),
    ("kileleshwa", "Kileleshwa"),
    ("lavington", "Lavington"),
    ("karen", "Karen"),
    ("runda", "Runda"),
    ("kiambu-road", "Kiambu Road"),
    ("nairobi-cbd", "Nairobi CBD"),
    ("south-b", "South B"),
    ("south-c", "South C"),
    ("embakasi", "Embakasi"),
    ("parklands", "Parklands"),
    ("kasarani", "Kasarani"),
    ("ruaka", "Ruaka"),
    ("nairobi-west", "Nairobi West"),
]


def nairobi_area_links_html() -> str:
    return "".join(
        f'<a href="/cleaning-services/{slug}/">{html.escape(label)}</a>'
        for slug, label in NAIROBI_AREA_PAGES
    )

def organization_ref():
    """Stable identity for the service-area business.

    Schema.org has no ServiceAreaBusiness type. ProfessionalService is the
    LocalBusiness subtype, published with areaServed and without address,
    geo, or openingHours.
    """
    return {
        "@type": "ProfessionalService",
        "@id": f"{SITE_URL}/#organization",
        "name": "Cleaning Services Kenya",
        "url": f"{SITE_URL}/",
        "telephone": PHONE_TEL,
        "contactPoint": {
            "@type": "ContactPoint",
            "telephone": PHONE_TEL,
            "contactType": "customer service",
            "url": f"https://wa.me/{WHATSAPP_NUMBER}",
        },
    }


FORM_SERVICES = [
    "Residential cleaning",
    "House cleaning",
    "Commercial cleaning",
    "Office cleaning",
    "Deep cleaning",
    "Move-in / move-out cleaning",
    "Regular maintenance cleaning",
    "Fumigation & pest control",
    "Carpet cleaning",
    "Sofa & upholstery cleaning",
    "Parapet cleaning",
    "Other / not sure yet",
]

# Towns used as internal links from service pages. All of these exist as town pages.
FEATURED_TOWNS = [
    ("nairobi", "Nairobi"),
    ("mombasa", "Mombasa"),
    ("kisumu", "Kisumu"),
    ("nakuru", "Nakuru"),
    ("eldoret", "Eldoret"),
    ("thika", "Thika"),
    ("ruiru", "Ruiru"),
    ("nyeri", "Nyeri"),
    ("meru", "Meru"),
    ("kakamega", "Kakamega"),
]


def json_ld_script(data) -> str:
    raw = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return f'<script type="application/ld+json">{raw}</script>'


def seo_tags(path: str, title: str, description: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    if path != "/" and not path.endswith("/"):
        path += "/"
    url = SITE_URL + path
    t = html.escape(title, quote=True)
    d = html.escape(description, quote=True)
    u = html.escape(url, quote=True)
    img = html.escape(OG_IMAGE, quote=True)
    return (
        f'<link rel="canonical" href="{u}">\n'
        f'  <link rel="icon" href="/favicon.ico" sizes="any">\n'
        f'  <link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
        f'  <meta property="og:type" content="website">\n'
        f'  <meta property="og:site_name" content="Cleaning Services Kenya">\n'
        f'  <meta property="og:locale" content="en_KE">\n'
        f'  <meta property="og:title" content="{t}">\n'
        f'  <meta property="og:description" content="{d}">\n'
        f'  <meta property="og:url" content="{u}">\n'
        f'  <meta property="og:image" content="{img}">\n'
        f'  <meta property="og:image:alt" content="Professional cleaner carefully cleaning a floor">\n'
        f'  <meta name="twitter:card" content="summary_large_image">\n'
        f'  <meta name="twitter:title" content="{t}">\n'
        f'  <meta name="twitter:description" content="{d}">\n'
        f'  <meta name="twitter:image" content="{img}">'
    )


def breadcrumb_ld(items):
    """items: list of (name, path)."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index + 1,
                "name": name,
                "item": SITE_URL + path,
            }
            for index, (name, path) in enumerate(items)
        ],
    }


def breadcrumb_nav(items) -> str:
    parts = []
    for index, (name, path) in enumerate(items):
        if index:
            parts.append('<span aria-hidden="true">/</span>')
        if index == len(items) - 1:
            parts.append(f'<span aria-current="page">{html.escape(name)}</span>')
        else:
            parts.append(f'<a href="{html.escape(path, quote=True)}">{html.escape(name)}</a>')
    return '<nav class="breadcrumb" aria-label="Breadcrumb">' + "".join(parts) + "</nav>"


def service_menu() -> str:
    links = "\n".join(
        f'        <a href="/{slug}/">{html.escape(label)}</a>'
        for slug, label in SERVICE_LINKS
    )
    return (
        '<details class="nav-services">\n'
        '        <summary>Services</summary>\n'
        '        <div class="nav-services-menu">\n'
        f'{links}\n'
        '          <a href="/#services">All services</a>\n'
        '        </div>\n'
        '      </details>'
    )


def service_options(selected: str = "") -> str:
    parts = ['<option value="">Select a service</option>']
    for name in FORM_SERVICES:
        sel = " selected" if name == selected else ""
        parts.append(f"<option{sel}>{html.escape(name)}</option>")
    return "".join(parts)


def header_html(whatsapp_url: str) -> str:
    return f"""<div class="announcement"><span>Professional cleaning, with a personal touch</span><a href="tel:{PHONE_TEL}">Call our team: {PHONE_DISPLAY}</a></div>
  <header class="site-header" id="top">
    <a class="brand" href="/" aria-label="Cleaning Services Kenya home"><span class="brand-mark" aria-hidden="true"><span></span><span></span><span></span></span><span class="brand-name">CLEANING SERVICES <b>KENYA</b></span></a>
    <button class="menu-toggle" aria-label="Open navigation" aria-expanded="false"><span></span><span></span></button>
    <nav class="main-nav" aria-label="Main navigation">
      <a href="/">Home</a>
      {service_menu()}
      <a href="/#about">Why choose us</a>
      <a href="/#process">Our process</a>
      <a href="/cleaning-services/">Locations</a>
      <a href="#contact">Contact</a>
      <a class="nav-call" href="tel:{PHONE_TEL}">Call us</a>
      <a class="button button-small" href="{html.escape(whatsapp_url, quote=True)}" target="_blank" rel="noopener">Book on WhatsApp <span>↗</span></a>
    </nav>
  </header>"""


def footer_html(whatsapp_url: str) -> str:
    service_links = "".join(
        f'<a href="/{slug}/">{html.escape(label)}</a>' for slug, label in SERVICE_LINKS
    )
    return f"""<footer class="site-footer">
    <a class="brand brand-footer" href="/"><span class="brand-mark"><span></span><span></span><span></span></span><span class="brand-name">CLEANING SERVICES <b>KENYA</b></span></a>
    <p>Professional care. Beautifully clean spaces.</p>
    <div class="footer-links">{service_links}<a href="/cleaning-services/">Locations</a><a href="/testimonials/">Testimonials</a><a href="/privacy-policy/">Privacy Policy</a></div>
    <small>© <span id="year"></span> Cleaning Services Kenya. All rights reserved. <span class="footer-credit">Made by <a href="/">Lumen Labs</a></span></small>
    <nav class="footer-links footer-areas" aria-label="Areas we serve in Nairobi"><span>Nairobi areas</span>{nairobi_area_links_html()}</nav>
  </footer>
  <a class="floating-whatsapp" href="{html.escape(whatsapp_url, quote=True)}" target="_blank" rel="noopener" aria-label="Chat with us on WhatsApp"><span>◉</span><b>Chat with us</b></a>
  <a class="floating-call" href="tel:{PHONE_TEL}" aria-label="Call us"><span>☎</span><b>Call us</b></a>
  <script src="/script.js"></script>"""


def render_page(title, description, path, main_html, extra_ld=None, extra_body="", whatsapp_text="Hello Cleaning Services Kenya, I would like to request a cleaning quote."):
    from urllib.parse import quote
    wa = f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(whatsapp_text)}"
    ld_html = "\n  ".join(
        block if isinstance(block, str) else json_ld_script(block)
        for block in (extra_ld or [])
    )
    return f"""<!doctype html>
<html lang="en-KE">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#373b32">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description, quote=True)}">
  {seo_tags(path, title, description)}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/styles.css">
  {ld_html}
</head>
<body>
  {header_html(wa)}
  {main_html}
  {footer_html(wa)}
  {extra_body}
</body>
</html>
"""
