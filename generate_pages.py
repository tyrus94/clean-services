#!/usr/bin/env python3
"""Generate SEO landing pages for the towns listed in towns.csv.

Run from the project folder:
    python generate_pages.py

Canonical host defaults to https://www.cleaningserviceskenya.co.ke.
Override it with SITE_URL if you need another host:
    SITE_URL=https://www.example.co.ke python generate_pages.py

Inputs:
    towns.csv            town, county, region, slug
    town_profiles.json   optional per-town details (type, areas, note) that make pages genuinely different
    testimonials.csv     REAL client testimonials only (name, town, service, rating, date, text)
    town-template.html   shared page layout

Output:
    cleaning-services/<town-slug>/index.html
    cleaning-services/index.html
    Hand-written Nairobi neighbourhood pages (see NAIROBI_AREA_PAGES in page_chrome.py)
    are not generated here. Their URLs are appended to sitemap.xml, and matching
    neighbourhood names in town_profiles.json are linked. Do not add those slugs
    to towns.csv.
    testimonials/index.html   (only when testimonials.csv has rows)
    index.html                (Locations + Testimonials blocks between the markers are refreshed,
                               plus the homepage LocalBusiness JSON-LD between SCHEMA markers)
    sitemap.xml
    robots.txt
    fumigation/, carpet-cleaning/, sofa-cleaning/, parapet-cleaning/,
    house-cleaning/, office-cleaning/
"""
from pathlib import Path
from urllib.parse import quote
import csv, hashlib, html, json, os, random, re

from page_chrome import (
    HOME_DESCRIPTION,
    KIAMBU_AREA_PAGES,
    NAIROBI_AREA_PAGES,
    OG_IMAGE,
    PHONE_DISPLAY,
    PHONE_TEL,
    SITE_URL,
    WHATSAPP_NUMBER,
    breadcrumb_ld,
    breadcrumb_nav,
    json_ld_script,
    nairobi_area_links_html,
    organization_ref,
    render_page,
    seo_tags,
)
from service_pages import service_paths, write_service_pages

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "towns.csv"
TEMPLATE_FILE = BASE_DIR / "town-template.html"
PROFILES_FILE = BASE_DIR / "town_profiles.json"
TESTIMONIALS_FILE = BASE_DIR / "testimonials.csv"
URL_PREFIX = "cleaning-services"          # town pages live at /cleaning-services/<town>/
NAIROBI_AREA_SLUGS = {name: slug for slug, name in NAIROBI_AREA_PAGES}
KIAMBU_AREA_ROWS = [
    {"town": name, "county": "Kiambu", "region": "Central", "slug": slug}
    for slug, name in KIAMBU_AREA_PAGES
]
OUTPUT_DIR = BASE_DIR / URL_PREFIX
TESTIMONIALS_DIR = BASE_DIR / "testimonials"
HOME_FILE = BASE_DIR / "index.html"
SCHEMA_START, SCHEMA_END = "<!-- SCHEMA:START -->", "<!-- SCHEMA:END -->"
LOC_START, LOC_END = "<!-- LOCATIONS:START -->", "<!-- LOCATIONS:END -->"
NAIROBI_AREAS_START, NAIROBI_AREAS_END = "<!-- NAIROBI-AREAS:START -->", "<!-- NAIROBI-AREAS:END -->"
TST_START, TST_END = "<!-- TESTIMONIALS:START -->", "<!-- TESTIMONIALS:END -->"
BOOKING_ANCHOR = '<section class="section booking-section" id="contact">'
PER_PAGE_TESTIMONIALS = 6


# ---------------------------------------------------------------- helpers
def slugify(value: str) -> str:
    value = value.lower().replace("’", "").replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def replace_tokens(template: str, values: dict) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", str(value))
    return template


def seed(slug: str, salt: str) -> int:
    return int(hashlib.md5(f"{slug}:{salt}".encode()).hexdigest(), 16)


def pick(slug, salt, options):
    return options[seed(slug, salt) % len(options)]


def sample(slug, salt, pool, k):
    return random.Random(seed(slug, salt)).sample(pool, min(k, len(pool)))


def fmt(text, ctx):
    """Fill {town}/{county}/... then HTML-escape the result."""
    return html.escape(text.format(**ctx))


def join_names(names):
    names = list(names)
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


# ---------------------------------------------------------------- content pools
# {town} {county} {region} {nearby} are filled in per page. Variants are chosen per town
# (deterministically), so every page reads differently but rebuilds stay stable.
INTROS = {
    "city": [
        "{town} keeps moving: offices, apartment blocks, restaurants and busy family homes all need cleaning that fits around a full schedule. Tell us about your space and we'll confirm what we can do in {town}.",
        "In a busy centre like {town}, a clean workplace or home takes more than a quick tidy. Send us an enquiry for residential or commercial cleaning and we'll confirm availability for your exact location.",
        "From apartment blocks to shopfronts, {town} has a mix of properties with very different cleaning needs. Share yours with us and we'll talk through a sensible plan.",
    ],
    "commuter": [
        "Many people in {town} leave early and get home late, which is exactly when a clean home is hardest to keep up. Send us an enquiry and we'll confirm what's possible in {town}.",
        "New apartments, rentals and family homes keep going up around {town}, and every handover or move-in is a good moment for a proper deep clean. Ask us about availability in {town}.",
        "Living in {town} often means long days on the road. Talk to us about regular or one-off cleaning that gives you your weekends back.",
    ],
    "coastal": [
        "Sea air, humidity and sand find their way into every room on the coast. For homes, rentals and guesthouses in {town}, talk to us about regular upkeep or a thorough reset.",
        "Between guests, seasons and salty air, properties in {town} need cleaning that keeps up. Send us your details and we'll confirm availability in {town}, {county} County.",
        "Holiday homes and rentals in {town} often need a fast, reliable turnaround. Tell us what you need and we'll let you know what we can arrange.",
    ],
    "tourism": [
        "Guesthouses, lodges, holiday homes and family houses in {town} all see steady comings and goings. Tell us about your property and we'll confirm what we can arrange in {town}.",
        "Visitors notice a clean room straight away. If you run or own a property in {town}, tell us what it needs and we'll discuss a suitable cleaning routine.",
        "Whether it's a weekend rental or a family home in {town}, a proper clean makes the difference. Send us an enquiry and we'll confirm availability.",
    ],
    "border": [
        "{town} is a busy trading and transit town, with shops, guesthouses and homes that see constant foot traffic. Enquire about cleaning in {town} and we'll confirm availability.",
        "Constant comings and goings mean shops, lodgings and homes in {town} get dirty fast. Tell us what you need and our team will confirm what we can arrange.",
        "For businesses and households in {town}, regular cleaning keeps a busy place running smoothly. Send your details and we'll discuss options.",
    ],
    "market": [
        "{town} is a growing town in {county} County, with homes, shops, schools and small businesses that all benefit from a reliable clean. Send us an enquiry and we'll confirm whether we can serve your location.",
        "Whether it's a family home, a rental or a small business in {town}, a clean space makes the day easier. Tell us what you need and we'll be honest about availability in {town}.",
        "Looking for cleaning help in {town}? Share your property type and needs, and our team will confirm what we can arrange in {county} County.",
    ],
}

NEEDS = {
    "city": [
        ("Offices and workplaces", "Regular cleaning for offices, studios and shared workspaces in {town}, planned around your working hours."),
        ("Apartments and serviced units", "Between-tenant and between-guest cleans for apartments in {town}, so every handover looks fresh."),
        ("Shops and restaurants", "Commercial premises in {town} that need floors, counters and washrooms kept customer-ready."),
        ("Landlord move-out cleans", "A thorough clean after a tenant leaves, so a {town} property is ready for the next viewing."),
        ("Festive-season deep cleans", "A top-to-bottom reset for family homes in {town} before visitors or events."),
        ("Regular home upkeep", "Weekly or fortnightly cleaning for busy households in {town}."),
    ],
    "commuter": [
        ("Move-in and move-out cleans", "Rentals around {town} change hands often. A proper clean helps deposits and first impressions."),
        ("New-home freshening", "Settling into a new place in {town}? Start with a deep clean of kitchens, bathrooms and floors."),
        ("Weekly home cleaning", "Regular visits for households in {town} that would rather spend weekends elsewhere."),
        ("Landlord handovers", "Get a {town} rental ready for its next tenant with a full, room-by-room clean."),
        ("Small offices and shops", "Compact commercial spaces around {town} that need a dependable, scheduled clean."),
        ("Festive-season deep cleans", "A thorough reset for family homes in {town} before guests arrive."),
    ],
    "coastal": [
        ("Holiday-rental turnarounds", "Quick, careful cleans between guests for rentals in {town}."),
        ("Humidity-prone rooms", "Warm, damp conditions can leave bathrooms and kitchens in {town} needing extra attention."),
        ("Guesthouse and lodging rooms", "Regular cleaning for rooms and shared areas at guesthouses around {town}."),
        ("Move-out cleans", "A full clean when a tenant leaves a {town} property."),
        ("Seasonal deep cleans", "A thorough reset before or after the busy season for homes in {town}."),
        ("Regular home upkeep", "Ongoing cleaning for residents of {town} who want less dust and sand indoors."),
    ],
    "tourism": [
        ("Guesthouse and lodge rooms", "Room-by-room cleaning for guest accommodation in and around {town}."),
        ("Holiday-home turnarounds", "Cleans between stays for second homes and rentals near {town}."),
        ("Regular home cleaning", "Dependable upkeep for family homes in {town}."),
        ("Move-in and move-out cleans", "A fresh start for tenants and landlords in {town}."),
        ("Event and festive deep cleans", "A thorough clean before hosting guests or events in {town}."),
        ("Small commercial spaces", "Cafes, shops and offices in {town} that need regular attention."),
    ],
    "border": [
        ("Shops and trading premises", "High-traffic floors, counters and washrooms for businesses in {town}."),
        ("Lodgings and guesthouses", "Room turnarounds and shared-area cleaning for accommodation in {town}."),
        ("Family homes", "Regular or one-off cleaning for households in {town}."),
        ("Move-in and move-out cleans", "A proper clean when a property in {town} changes hands."),
        ("Small offices", "Scheduled cleaning for compact offices and service businesses in {town}."),
        ("Deep cleans", "Kitchens, bathrooms and floors that need more than a surface wipe."),
    ],
    "market": [
        ("Family homes", "Regular upkeep or a one-off deep clean for houses in {town}."),
        ("Shops and small businesses", "Tidy, customer-ready premises for businesses in {town}."),
        ("Rental handovers", "Landlords and tenants in {town} can ask about a full clean at move-in or move-out."),
        ("Schools and institutions", "Ask about cleaning for small schools, clinics and community spaces around {town}."),
        ("Festive-season deep cleans", "A thorough reset for homes in {town} before guests and celebrations."),
        ("Regular maintenance", "Scheduled visits to keep a {town} home or workplace consistently clean."),
    ],
}

FAQS = [
    ("Do you offer cleaning services in {town}?", "Send us an enquiry with your location in {town} and a few property details. Our team will confirm whether we can serve your area before anything is booked."),
    ("How do I request a cleaning quote in {town}?", "Use the form on this page or message us on WhatsApp. Tell us the property type, rough size and the service you want, and we'll discuss a quote."),
    ("Can you clean both homes and businesses in {town}?", "We take enquiries for residential and commercial cleaning. Mention which one applies when you get in touch."),
    ("Do you do move-in and move-out cleaning in {town}?", "Yes, it's one of the services you can enquire about. Tell us the property size and the date you need it done."),
    ("Can I book regular cleaning instead of a one-off?", "You can ask for a regular schedule (for example weekly or fortnightly) and we'll confirm what works for your location."),
    ("What should I tell you when I enquire?", "Your neighbourhood in {town}, the type and size of the property, the service you want and your preferred date. Any special requests help too."),
    ("Is a WhatsApp enquiry a confirmed booking?", "No. It's an enquiry. Our team replies to confirm availability, price and next steps before a booking is made."),
    ("Do you serve areas around {town}?", "Enquiries from {county} County and nearby towns such as {nearby} are welcome. We'll confirm whether your exact location is covered."),
    ("Can I choose the day and time?", "Share your preferred date in the form. We'll confirm what's possible for {town} when we reply."),
]

# Titles stay accurate for a general town page (house and office cleaning),
# and they differ by more than the town name. Nairobi keeps the exact
# high-volume phrasing "Cleaning services in Nairobi".
TITLE_VARIANTS = [
    "Cleaning Services in {town} | {county} County",
    "Cleaning Services in {town}, Kenya",
    "{town} Cleaning Services | House & Office",
    "House & Office Cleaning in {town}",
    "Professional Cleaning Services in {town}",
    "Home & Business Cleaning in {town}",
    "{town} Cleaners | {county} County, Kenya",
    "Cleaning Services in {town} | Homes & Workplaces",
]
META_ANGLES = [
    "house cleaning, office cleaning and deep cleans",
    "residential and commercial cleaning",
    "home, workplace and move-out cleaning",
    "regular home cleaning and one-off deep cleans",
    "office cleaning, house cleaning and fumigation enquiries",
    "carpet, sofa and everyday home cleaning",
]
SERVICES_INTRO = [
    "From homes and apartments to offices and commercial premises, tell us what needs cleaning in {town} and we’ll help you discuss the right service.",
    "Residential or commercial, one-off or regular: explain what your {town} property needs and we’ll suggest a sensible starting point.",
    "Not sure which service fits? Describe your space in {town} and we’ll help you choose between a deep clean, regular upkeep or a move-out clean.",
    "Cleaning needs in {town} range from a single apartment to a full workplace. Tell us about yours and we’ll talk it through.",
]
HOME_CARD = [
    "Regular home cleaning, deep cleaning and move-in or move-out cleaning enquiries for properties in {town}.",
    "Family homes, apartments and rentals in {town}: ask about regular upkeep, a one-off deep clean or a move-out clean.",
    "Whether it’s a flat or a family house in {town}, tell us the size and what needs attention.",
]
BUSINESS_CARD = [
    "Discuss office, workplace and commercial cleaning requirements in {town} with our team.",
    "Shops, offices and other commercial premises in {town}: tell us the size, when the workplace can be cleaned, and the routine you need.",
    "Looking after a workplace in {town}? Share what you need and we’ll discuss a suitable schedule.",
]
ABOUT_TEXT = [
    "For cleaning enquiries in {town} and the wider {county} County area, contact our team to discuss your property, requirements and whether we can accommodate your location.",
    "Tell us about your property in {town} and what you’d like done. We’ll be upfront about availability in {county} County before you commit to anything.",
    "Every property in {town} is different. A short conversation about your space, timing and priorities lets us confirm what we can offer.",
    "Whether your property is in the centre of {town} or on its edge, send us the details and we’ll confirm whether we can take it on.",
]
COVERAGE_TEXT = [
    "We welcome enquiries from residents, landlords and businesses in {town}. Share your exact neighbourhood, property type and cleaning needs so our team can confirm service availability before you make plans.",
    "Our team reviews each enquiry from {town} individually, so you only hear a firm yes once we’ve checked we can reach your location in {county} County.",
    "Landlords, tenants, homeowners and business owners around {town} are all welcome to enquire. The more you tell us about your property, the quicker we can confirm availability.",
    "Cleaning availability can differ between neighbourhoods. Tell us where in {town} you are and we’ll let you know honestly what we can arrange.",
]
LOCAL_HEADINGS = [
    "Cleaning that suits <em>{town}.</em>",
    "What {town} properties <em>often ask for.</em>",
    "Made for the way <em>{town} lives.</em>",
    "Where we can help <em>in {town}.</em>",
]
LOCAL_INTROS = [
    "Here are some of the cleaning requests we expect from properties in {town}. Tell us which ones apply to yours.",
    "Every town has its own rhythm. These are common reasons people in {town} get in touch.",
    "A few of the jobs property owners and tenants in {town} typically enquire about.",
]


# ---------------------------------------------------------------- loading
def load_towns():
    with CSV_FILE.open(newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))
    valid = []
    for row in rows:
        t = (row.get("town") or "").strip()
        c = (row.get("county") or "").strip()
        r = (row.get("region") or "").strip()
        s = (row.get("slug") or "").strip() or slugify(t)
        if not t or not c or not s:
            print(f"Skipping incomplete row: {row}")
            continue
        valid.append({"town": t, "county": c, "region": r, "slug": s})
    return valid


def load_profiles():
    if not PROFILES_FILE.exists():
        return {}
    data = json.loads(PROFILES_FILE.read_text(encoding="utf-8"))
    return data.get("towns", {})


def load_testimonials():
    """Reads testimonials.csv (comma- or tab-separated; a leading A,B,C... spreadsheet row is skipped)."""
    if not TESTIMONIALS_FILE.exists():
        return []
    raw = TESTIMONIALS_FILE.read_text(encoding="utf-8-sig")
    first = raw.splitlines()[0] if raw.strip() else ""
    delim = "\t" if first.count("\t") > first.count(",") else ","
    rows = list(csv.reader(raw.splitlines(), delimiter=delim))
    hdr_i = next((i for i, r in enumerate(rows) if "name" in [c.strip().lower() for c in r] and "text" in [c.strip().lower() for c in r]), None)
    if hdr_i is None:
        return []
    hdr = [c.strip().lower() for c in rows[hdr_i]]
    out = []
    for r in rows[hdr_i + 1:]:
        row = dict(zip(hdr, r))
        text, name = (row.get("text") or "").strip(), (row.get("name") or "").strip()
        if not text or not name:
            continue
        try:
            rating = max(1, min(5, int(float(row.get("rating") or 5))))
        except ValueError:
            rating = 5
        out.append({"name": name, "town": (row.get("town") or "").strip(),
                    "service": (row.get("service") or "").strip(), "rating": rating,
                    "date": (row.get("date") or "").strip(), "text": text})
    return out


# ---------------------------------------------------------------- town helpers
def nearby_towns(row, rows, limit=4):
    same_county = [r for r in rows if r["county"] == row["county"] and r["slug"] != row["slug"]]
    chosen = sample(row["slug"], "nearby-county", same_county, limit)
    if len(chosen) < limit:
        same_region = [r for r in rows if r["region"] == row["region"] and r["slug"] != row["slug"] and r not in chosen]
        chosen += sample(row["slug"], "nearby-region", same_region, limit - len(chosen))
    return chosen


def build_town_options(town_rows, current_town=""):
    seen = set()
    options = ['<option value="">Select another town / location</option>']
    curr = current_town.strip().lower()
    for item in town_rows:
        name, county = item["town"].strip(), item["county"].strip()
        if curr and name.lower() == curr:
            continue
        label = f"{name}, {county} County" if county else name
        if label in seen:
            continue
        seen.add(label)
        options.append(f'<option value="{html.escape(label, quote=True)}">{html.escape(label)}</option>')
    options.append('<option value="Other / Not listed">Other / Not listed</option>')
    return "\n            ".join(options)


def stars(n):
    return "★" * n + "☆" * (5 - n)


def testimonial_card(t, hidden=False):
    meta = t["town"]  # date intentionally not shown
    return (
        f'<article class="testimonial-card"{" hidden" if hidden else ""}>'
        f'<div class="t-top"><span class="t-stars" role="img" aria-label="{t["rating"]} out of 5 stars">{"★" * t["rating"]}</span>'
        f'<span class="t-service">{html.escape(t["service"])}</span></div>'
        f'<p class="t-text">“{html.escape(t["text"])}”</p>'
        f'<div class="t-meta"><strong>{html.escape(t["name"])}</strong><span>{html.escape(meta)}</span></div></article>'
    )


def build_testimonials_section(testimonials, row=None, rows=None, slug="home"):
    """Every page gets testimonials: the town's own first, then nearby towns, then others."""
    if not testimonials:
        return ""
    if row:
        town = row["town"]
        local = [t for t in testimonials if t["town"].lower() == town.lower()]
        near_c = [t for t in testimonials if t not in local and any(
            r["town"].lower() == t["town"].lower() and r["county"] == row["county"] for r in rows)]
        near_r = [t for t in testimonials if t not in local and t not in near_c and any(
            r["town"].lower() == t["town"].lower() and r["region"] == row["region"] for r in rows)]
        rest = [t for t in testimonials if t not in local and t not in near_c and t not in near_r]
        chosen = sample(slug, "t-local", local, PER_PAGE_TESTIMONIALS)
        for pool, salt in ((near_c, "t-county"), (near_r, "t-region"), (rest, "t-rest")):
            if len(chosen) < PER_PAGE_TESTIMONIALS:
                chosen += sample(slug, salt, pool, PER_PAGE_TESTIMONIALS - len(chosen))
        eyebrow = f"CLIENT FEEDBACK IN {html.escape(town.upper())}"
        heading = f"Trusted by homes &amp;<br><em>businesses in {html.escape(town)}.</em>"
        summary = (f"Feedback from {len(local)} client{'s' if len(local) != 1 else ''} in {html.escape(town)}, "
                   f"plus others across Kenya." if local else "Feedback from clients across Kenya.")
    else:
        chosen = sample(slug, "t-home", testimonials, PER_PAGE_TESTIMONIALS)
        eyebrow, heading = "CLIENT FEEDBACK ACROSS KENYA", "Trusted by homes &amp;<br><em>businesses nationwide.</em>"
        summary = f"Feedback from {len(testimonials)} clients across Kenya."
    cards = "\n".join("        " + testimonial_card(t) for t in chosen)
    return (
        '<section class="section testimonials-section" id="reviews">\n'
        f'      <div class="center-heading">\n        <p class="eyebrow"><span class="eyebrow-line"></span> {eyebrow}</p>\n'
        f'        <h2>{heading}</h2>\n        <p class="reviews-summary">{summary}</p>\n      </div>\n'
        f'      <div class="testimonials-grid">\n{cards}\n      </div>\n'
        f'      <p class="testimonial-more"><a class="text-link" href="/testimonials/">Read all {len(testimonials)} testimonials <span>↗</span></a></p>\n'
        '    </section>'
    )


# ---------------------------------------------------------------- page building
def build_title(slug, ctx):
    if slug == "nairobi":
        return "Cleaning Services in Nairobi | House & Office"
    return pick(slug, "title-v2", TITLE_VARIANTS).format(**ctx)


def build_description(slug, ctx, profile):
    angle = pick(slug, "meta-angle", META_ANGLES)
    areas = [area for area in (profile.get("areas") or []) if area]
    if areas:
        place = "Areas include " + join_names(areas[:3]) + "."
    else:
        place = "Nearby towns include " + ctx["nearby"] + "."
    description = (
        f"Cleaning services in {ctx['town']}, {ctx['county']} County: {angle}. "
        f"{place} WhatsApp +254 706 855633."
    )
    if len(description) > 170:
        if areas:
            place = "Areas include " + areas[0] + "."
        else:
            place = "Nearby: " + ctx["nearby"].split(" and ")[0] + "."
        description = (
            f"Cleaning services in {ctx['town']}, {ctx['county']} County: {angle}. "
            f"{place} WhatsApp +254 706 855633."
        )
    return description


def build_content(row, rows, profiles):
    slug, town, county, region = row["slug"], row["town"], row["county"], row["region"]
    profile = profiles.get(slug, {})
    ttype = profile.get("type", "market")
    if ttype not in INTROS:
        ttype = "market"
    near = nearby_towns(row, rows)
    ctx = {"town": town, "county": county, "region": region,
           "nearby": join_names(n["town"] for n in near[:3]) or county}

    # needs: 4 of 6, chosen per town
    needs = sample(slug, "needs", NEEDS[ttype], 4)
    need_cards = "".join(
        f'<article class="need-card"><h3>{fmt(title, ctx)}</h3><p>{fmt(text, ctx)}</p></article>'
        for title, text in needs
    )

    blocks = [f'<div class="need-grid">{need_cards}</div>']
    areas = profile.get("areas") or []
    note = (profile.get("note") or "").strip()
    if note:
        blocks.append(f'<p class="local-note">{html.escape(note)}</p>')
    if areas:
        def area_chip(area: str) -> str:
            label = html.escape(area)
            slug = NAIROBI_AREA_SLUGS.get(area)
            if slug:
                return f'<li><a href="/{URL_PREFIX}/{slug}/">{label}</a></li>'
            return f"<li>{label}</li>"

        chips = "".join(area_chip(a) for a in areas)
        link_class = " area-links" if any(a in NAIROBI_AREA_SLUGS for a in areas) else ""
        blocks.append(
            f'<div class="areas-block"><h3>Neighbourhoods in and around {html.escape(town)}</h3>'
            f'<ul class="area-chips{link_class}">{chips}</ul>'
            f'<p class="areas-note">Not listed? Ask us. We’ll confirm whether we can reach you.</p></div>'
        )
    if near:
        near_links = list(near)
        if slug == "karuri":
            near_links = KIAMBU_AREA_ROWS + near_links
        links = "".join(
            f'<li><a href="/{URL_PREFIX}/{html.escape(n["slug"])}/">Cleaning in {html.escape(n["town"])}</a></li>'
            for n in near_links
        )
        blocks.append(
            f'<div class="areas-block"><h3>Nearby towns</h3><ul class="area-chips area-links">{links}</ul></div>'
        )

    local_section = (
        '<section class="section local-section" id="local"><div class="section-heading"><div>'
        '<p class="eyebrow"><span class="eyebrow-line"></span> LOCAL CLEANING NEEDS</p>'
        f'<h2>{pick(slug, "lh", LOCAL_HEADINGS).format(town=html.escape(town))}</h2></div>'
        f'<p class="section-intro">{fmt(pick(slug, "li", LOCAL_INTROS), ctx)}</p></div>'
        + "".join(blocks) + "</section>"
    )

    # FAQ: availability question is always first, then 4 more chosen per town
    first, others = FAQS[0], FAQS[1:]
    faq_items = [first] + sample(slug, "faq", others, 4)
    faq_html = "".join(
        f'<details><summary>{fmt(q, ctx)}</summary><p>{fmt(a, ctx)}</p></details>' for q, a in faq_items
    )
    faq_section = (
        '<section class="section faq-section" id="faq"><div class="center-heading">'
        '<p class="eyebrow"><span class="eyebrow-line"></span> GOOD TO KNOW</p>'
        f'<h2>Cleaning in <em>{html.escape(town)}:</em><br>common questions</h2></div>'
        f'<div class="faq-list">{faq_html}</div></section>'
    )
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q.format(**ctx),
             "acceptedAnswer": {"@type": "Answer", "text": a.format(**ctx)}}
            for q, a in faq_items
        ],
    }
    faq_schema_tag = '<script type="application/ld+json">' + json.dumps(faq_schema, ensure_ascii=False).replace("</", "<\\/") + "</script>"

    title = build_title(slug, ctx)
    description = build_description(slug, ctx, profile)

    return {
        "ctx": ctx, "title": title, "description": description,
        "h1_html": f"Cleaning services<br><em>in {html.escape(town)}.</em>",
        "hero_description": fmt(pick(slug, "intro", INTROS[ttype]), ctx),
        "services_intro": fmt(pick(slug, "si", SERVICES_INTRO), ctx),
        "home_card_text": fmt(pick(slug, "hc", HOME_CARD), ctx),
        "business_card_text": fmt(pick(slug, "bc", BUSINESS_CARD), ctx),
        "about_text": fmt(pick(slug, "about", ABOUT_TEXT), ctx),
        "coverage_text": fmt(pick(slug, "cov", COVERAGE_TEXT), ctx),
        "local_section": local_section, "faq_section": faq_section, "faq_schema_tag": faq_schema_tag,
    }


def simple_page(title, description, path, body, extra="", crumbs=None):
    crumb_html = breadcrumb_nav(crumbs) if crumbs else ""
    main = f'<main class="section">{crumb_html}{body}</main>'
    blocks = [breadcrumb_ld(crumbs)] if crumbs else []
    return render_page(title, description, path, main, extra_ld=blocks, extra_body=extra)


def with_kiambu_area_rows(town_rows):
    out = []
    inserted = False
    for row in town_rows:
        out.append(row)
        if row["slug"] == "karuri":
            out.extend(KIAMBU_AREA_ROWS)
            inserted = True
    if not inserted:
        out.extend(KIAMBU_AREA_ROWS)
    return out


def build_locations_html(town_rows):
    groups = {}
    for item in with_kiambu_area_rows(town_rows):
        groups.setdefault(item["region"] or "Other", []).append(item)
    blocks = []
    for region, items in groups.items():
        links = "\n".join(
            f'            <li><a href="/{URL_PREFIX}/{html.escape(i["slug"])}/" '
            f'title="Cleaning services in {html.escape(i["town"], quote=True)}, {html.escape(i["county"], quote=True)} County">'
            f'{html.escape(i["town"])}</a></li>'
            for i in items
        )
        blocks.append(
            f'        <div class="location-group">\n'
            f'          <h3>{html.escape(region)} <small>{len(items)} TOWNS</small></h3>\n'
            f'          <ul class="location-links">\n{links}\n          </ul>\n'
            f'        </div>'
        )
    return '      <div class="location-groups">\n' + "\n".join(blocks) + "\n      </div>"


LOC_SECTION = (
    '    <section class="section locations-section" id="locations">\n'
    '      <div class="section-heading"><div><p class="eyebrow"><span class="eyebrow-line"></span> OUR LOCATIONS</p>'
    '<h2>Find cleaning in<br><em>your town.</em></h2></div>'
    '<p class="section-intro">Choose your town to enquire about residential or commercial cleaning. Availability is confirmed individually.</p></div>\n'
    f'      {LOC_START}\n      {LOC_END}\n    </section>\n\n'
)


def update_homepage(town_rows, testimonials):
    if not HOME_FILE.exists():
        return False, False
    page = HOME_FILE.read_text(encoding="utf-8")
    page = page.replace('href="/towns/"', f'href="/{URL_PREFIX}/"')
    if LOC_START not in page and BOOKING_ANCHOR in page:
        page = page.replace(BOOKING_ANCHOR, LOC_SECTION + "    " + BOOKING_ANCHOR, 1)
    if 'href="#locations"' not in page and 'href="/#locations"' not in page:
        page = page.replace('<a href="#contact">Contact</a>', '<a href="#locations">Locations</a>\n      <a href="#contact">Contact</a>', 1)
    block = build_locations_html(town_rows)
    pat = re.compile(re.escape(LOC_START) + r".*?" + re.escape(LOC_END), re.S)
    page = pat.sub(lambda m: f"{LOC_START}\n{block}\n      {LOC_END}", page, count=1)
    if TST_START not in page:
        old = re.search(r'    <section class="section testimonials-section" id="reviews">.*?</section>', page, re.S)
        if old:
            page = page[:old.start()] + f"    {TST_START}\n    {TST_END}" + page[old.end():]
        elif BOOKING_ANCHOR in page:
            page = page.replace(BOOKING_ANCHOR, f"{TST_START}\n{TST_END}\n    {BOOKING_ANCHOR}", 1)
    pat = re.compile(re.escape(TST_START) + r".*?" + re.escape(TST_END), re.S)
    page = pat.sub(lambda m: f"{TST_START}\n{build_testimonials_section(testimonials)}\n    {TST_END}", page, count=1)
    if NAIROBI_AREAS_START in page and NAIROBI_AREAS_END in page:
        area_chips = "".join(
            f'<li><a href="/{URL_PREFIX}/{html.escape(slug)}/">{html.escape(name)}</a></li>'
            for slug, name in NAIROBI_AREA_PAGES
        )
        areas_block = (
            '    <section class="section" id="nairobi-areas">\n'
            '      <div class="section-heading">\n'
            '        <div><p class="eyebrow"><span class="eyebrow-line"></span> NAIROBI NEIGHBOURHOODS</p><h2>Areas we serve<br><em>in Nairobi.</em></h2></div>\n'
            '        <p class="section-intro">These neighbourhoods have their own pages. The Nairobi city page still covers the city as a whole. If your estate is not listed, name it when you enquire and we will confirm we can reach it.</p>\n'
            '      </div>\n'
            f'      <ul class="area-chips area-links">{area_chips}</ul>\n'
            '    </section>\n'
        )
        pat = re.compile(re.escape(NAIROBI_AREAS_START) + r".*?" + re.escape(NAIROBI_AREAS_END), re.S)
        page = pat.sub(lambda m: f"{NAIROBI_AREAS_START}\n{areas_block}\n{NAIROBI_AREAS_END}", page, count=1)
    footer_areas_pat = re.compile(r'<nav class="footer-links footer-areas"[^>]*>.*?</nav>')
    page = footer_areas_pat.sub(
        lambda m: f'<nav class="footer-links footer-areas" aria-label="Areas we serve in Nairobi"><span>Nairobi areas</span>{nairobi_area_links_html()}</nav>',
        page,
        count=1,
    )
    if "<html lang=\"en\">" in page:
        page = page.replace("<html lang=\"en\">", "<html lang=\"en-KE\">", 1)
    page = upsert_home_schema(page, town_rows)
    HOME_FILE.write_text(page, encoding="utf-8")
    return True, True


def home_schema(town_rows):
    node = {"@context": "https://schema.org", **organization_ref()}
    node.update({
        "image": OG_IMAGE,
        "description": HOME_DESCRIPTION,
        "areaServed": [
            {
                "@type": "City",
                "name": row["town"],
                "containedInPlace": {
                    "@type": "AdministrativeArea",
                    "name": f"{row['county']} County, Kenya",
                },
            }
            for row in with_kiambu_area_rows(town_rows)
        ],
    })
    return node


def upsert_home_schema(page, town_rows):
    block = (
        "<!-- Service-area business. Cleaning is at the customer's property. "
        "Contact is phone and WhatsApp only. Do not add address, geo, or openingHours. -->\n  "
        "<!-- TODO(owner): priceRange, a logo file, and sameAs profiles stay out until confirmed. "
        "Do not add aggregateRating or review markup. -->\n  "
        + json_ld_script(home_schema(town_rows))
    )
    wrapped = f"{SCHEMA_START}\n  {block}\n  {SCHEMA_END}"
    pattern = re.compile(re.escape(SCHEMA_START) + r".*?" + re.escape(SCHEMA_END), re.S)
    if pattern.search(page):
        return pattern.sub(lambda _match: wrapped, page, count=1)
    return page.replace("</head>", f"  {wrapped}\n</head>", 1)


def write_testimonials_page(testimonials):
    if not testimonials:
        if TESTIMONIALS_DIR.exists():
            (TESTIMONIALS_DIR / "index.html").unlink(missing_ok=True)
        return False
    cards = "\n".join(testimonial_card(t, hidden=i >= 24) for i, t in enumerate(testimonials))
    contact_buttons = (
        '<div class="hero-actions" style="margin:28px 0;justify-content:center">'
        f'<a class="button" href="tel:{PHONE_TEL}">Call us <span>↗</span></a>'
        f'<a class="button" href="https://wa.me/{WHATSAPP_NUMBER}" target="_blank" rel="noopener">Chat with us <span>↗</span></a>'
        '</div>'
    )
    body = (
        '<p class="eyebrow">CLIENT TESTIMONIALS</p><h1>What our clients say</h1>'
        f'<p>{len(testimonials)} testimonials from clients across Kenya.</p>'
        f'{contact_buttons}'
        f'<div class="testimonials-grid" id="all-testimonials">{cards}</div>'
        '<p class="testimonial-more"><button class="button" id="show-more" type="button">Show more</button></p>'
        f'{contact_buttons}'
    )
    script = """<script>
(function(){var b=document.getElementById('show-more');if(!b)return;
function more(){var h=document.querySelectorAll('#all-testimonials [hidden]');
for(var i=0;i<24&&i<h.length;i++)h[i].hidden=false;
if(document.querySelectorAll('#all-testimonials [hidden]').length===0)b.style.display='none';}
b.addEventListener('click',more);more();})();
</script>"""
    TESTIMONIALS_DIR.mkdir(exist_ok=True)
    page = simple_page(
        "Client Testimonials | Cleaning Services Kenya",
        "Testimonials from Cleaning Services Kenya clients across Kenya. Read the feedback, then call or WhatsApp +254 706 855633.",
        "/testimonials/",
        body,
        script,
        [("Home", "/"), ("Testimonials", "/testimonials/")],
    )
    (TESTIMONIALS_DIR / "index.html").write_text(page, encoding="utf-8")
    return True


def write_privacy_page():
    body = """<div class="legal"><p class="eyebrow">LEGAL</p><h1>Privacy Policy</h1>
<p><em>Last updated: November 2026</em></p>
<p>This policy explains how Cleaning Services Kenya (“we”, “us”) collects and uses personal information when you visit this website or contact us about residential or commercial cleaning services in Kenya.</p>
<h2>Who we are and how to contact us</h2>
<p>Cleaning Services Kenya provides home and business cleaning. You can reach us by phone on <a href="tel:+254706855633">+254 706 855633</a> or on <a href="https://wa.me/254706855633" target="_blank" rel="noopener">WhatsApp</a>. Use either to ask about your information or to make a privacy request.</p>
<h2>Information we collect</h2>
<p><strong>Information you give us.</strong> When you use our enquiry form, call us or message us, you may give us your name, phone number, the service you want, your property location, a preferred date and any details you add.</p>
<p><strong>Technical information.</strong> Like most websites, standard technical data (such as IP address, browser and device type, and the pages visited) may be processed by our hosting provider and the third-party services the site uses. If we use analytics or advertising tools, they may also use cookies or similar technologies.</p>
<h2>How the enquiry form works</h2>
<p>The form on this site does not send your details to our web server. It opens WhatsApp with your enquiry pre-filled, and nothing is sent until you press Send in WhatsApp. Once sent, your message is handled by WhatsApp (Meta) under its own terms and privacy policy, and we receive it on our WhatsApp account.</p>
<h2>How we use your information</h2>
<ul><li>to reply to your enquiry, give a quote and confirm availability;</li><li>to arrange and carry out cleaning services;</li><li>to keep basic records and meet legal obligations;</li><li>to understand how the website is used and to measure and improve our advertising.</li></ul>
<p>We do not sell your personal information.</p>
<h2>Third parties</h2>
<p>We rely on service providers to run this website, including website hosting (Vercel), image hosting (GitHub), web fonts (Google Fonts) and WhatsApp (Meta). If we advertise online, advertising platforms such as Google or Meta may collect information through cookies or pixels to measure and show ads. These providers have their own privacy policies.</p>
<h2>Cookies and advertising</h2>
<p>Where cookies or similar tools are used for analytics or advertising, they help us measure visits and show relevant ads. You can control cookies in your browser settings, and manage ad personalisation through your Google Ad Settings and Meta ad preferences.</p>
<h2>How long we keep information</h2>
<p>We keep enquiry and service information only as long as needed to respond to you, provide the service, keep reasonable business records and meet legal requirements.</p>
<h2>Security</h2>
<p>We take reasonable steps to protect the information we hold. No method of transmission or storage is completely secure, so we cannot guarantee absolute security.</p>
<h2>Your rights</h2>
<p>Under Kenya’s Data Protection Act, 2019, you may ask to access, correct or delete your personal information, object to certain uses, or withdraw consent you have given. Contact us using the details above. You may also complain to the Office of the Data Protection Commissioner.</p>
<h2>Children</h2>
<p>Our services and website are not directed at children under 18, and we do not knowingly collect their personal information.</p>
<h2>Changes to this policy</h2>
<p>We may update this policy from time to time. The latest version will always be on this page, with the date above.</p></div>"""
    page = simple_page(
        "Privacy Policy | Cleaning Services Kenya",
        "How Cleaning Services Kenya collects, uses and protects your personal information.",
        "/privacy-policy/",
        body,
        crumbs=[("Home", "/"), ("Privacy Policy", "/privacy-policy/")],
    )
    (BASE_DIR / "privacy-policy").mkdir(exist_ok=True)
    (BASE_DIR / "privacy-policy" / "index.html").write_text(page, encoding="utf-8")


def main():
    if not CSV_FILE.exists() or not TEMPLATE_FILE.exists():
        raise SystemExit("Missing towns.csv or town-template.html. Keep them in the same folder as this script.")
    template = TEMPLATE_FILE.read_text(encoding="utf-8")
    valid_towns = load_towns()
    if not valid_towns:
        raise SystemExit("No valid towns found in towns.csv.")
    reserved = set(NAIROBI_AREA_SLUGS.values()) | {slug for slug, _name in KIAMBU_AREA_PAGES}
    clashes = [row["slug"] for row in valid_towns if row["slug"] in reserved]
    if clashes:
        raise SystemExit(
            "These slugs are hand-written area pages and must not be "
            "regenerated from towns.csv: " + ", ".join(clashes)
        )
    profiles = load_profiles()
    testimonials = load_testimonials()

    OUTPUT_DIR.mkdir(exist_ok=True)
    index_cards = []

    for row in valid_towns:
        town, county, region, slug = row["town"], row["county"], row["region"], row["slug"]
        c = build_content(row, valid_towns, profiles)
        whatsapp_text = quote(f"Hello Cleaning Services Kenya, I would like to enquire about cleaning services in {town}, {county} County.")
        path = f"/{URL_PREFIX}/{slug}/"
        crumbs = [("Home", "/"), ("Locations", f"/{URL_PREFIX}/"), (town, path)]
        schema = {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": f"Cleaning services in {town}",
            "serviceType": ["Residential cleaning", "Commercial cleaning", "Deep cleaning", "House cleaning", "Office cleaning"],
            "url": f"{SITE_URL}{path}",
            "areaServed": {"@type": "City", "name": town,
                           "containedInPlace": {"@type": "AdministrativeArea", "name": f"{county} County, Kenya"}},
            "provider": organization_ref(),
            "description": c["description"],
        }
        options = build_town_options(valid_towns, current_town=town)
        values = {
            "town": html.escape(town), "town_upper": html.escape(town.upper()),
            "county": html.escape(county), "county_upper": html.escape(county.upper()),
            "region": html.escape(region),
            "page_title": html.escape(c["title"]),
            "meta_description": html.escape(c["description"], quote=True),
            "seo_tags": seo_tags(path, c["title"], c["description"]),
            "breadcrumb_nav": breadcrumb_nav(crumbs),
            "breadcrumb_json": json.dumps(breadcrumb_ld(crumbs), ensure_ascii=False).replace("</", "<\\/"),
            "schema_json": json.dumps(schema, ensure_ascii=False).replace("</", "<\\/"),
            "whatsapp_text": whatsapp_text,
            "phone_display": html.escape(PHONE_DISPLAY), "phone_tel": PHONE_TEL,
            "whatsapp_number": WHATSAPP_NUMBER,
            "nairobi_area_links": nairobi_area_links_html(),
            "town_options": options, "other_town_options": options,
            "h1_html": c["h1_html"], "hero_description": c["hero_description"],
            "services_intro": c["services_intro"], "home_card_text": c["home_card_text"],
            "business_card_text": c["business_card_text"], "about_text": c["about_text"],
            "coverage_text": c["coverage_text"], "local_section": c["local_section"],
            "faq_section": c["faq_section"], "faq_schema_tag": c["faq_schema_tag"],
            "testimonials_section": build_testimonials_section(testimonials, row, valid_towns, slug),
        }
        # content tokens first, then the plain tokens they may contain
        page = replace_tokens(template, {k: values[k] for k in (
            "h1_html", "hero_description", "services_intro", "home_card_text", "business_card_text",
            "about_text", "coverage_text", "local_section", "faq_section", "faq_schema_tag",
            "testimonials_section")})
        page = replace_tokens(page, values)
        dest = OUTPUT_DIR / slug / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page, encoding="utf-8")
        index_cards.append((town, county, slug))

    directory_entries = []
    for town, county, slug in index_cards:
        directory_entries.append((town, county, slug))
        if slug == "karuri":
            for k_slug, k_name in KIAMBU_AREA_PAGES:
                directory_entries.append((k_name, "Kiambu", k_slug))
    links = "\n".join(
        f'<li><a href="/{URL_PREFIX}/{html.escape(slug)}/">Cleaning services in {html.escape(town)}</a> <span>— {html.escape(county)} County</span></li>'
        for town, county, slug in directory_entries
    )
    service_chips = "".join(
        f'<li><a href="/{slug}/">{html.escape(label)}</a></li>'
        for slug, label in __import__("page_chrome").SERVICE_LINKS
    )
    body = (
        '<p class="eyebrow">OUR LOCATIONS</p><h1>Cleaning service locations across Kenya</h1>'
        '<p>Choose a town to enquire about residential or commercial cleaning. Service availability is confirmed individually.</p>'
        '<div class="areas-block"><h2>Services</h2>'
        f'<ul class="area-chips area-links">{service_chips}</ul></div>'
        '<div class="areas-block"><h2>Areas we serve in Nairobi</h2>'
        f'<ul class="area-chips area-links">{"".join(f"<li><a href=\"/{URL_PREFIX}/{html.escape(slug)}/\">{html.escape(name)}</a></li>" for slug, name in NAIROBI_AREA_PAGES)}</ul></div>'
        f'<ul class="town-directory">{links}</ul>'
    )
    (OUTPUT_DIR / "index.html").write_text(
        simple_page(
            "Cleaning Service Locations in Kenya | Cleaning Services Kenya",
            "Cleaning service locations across Kenya. Choose a town to enquire about house cleaning, office cleaning, fumigation and more.",
            f"/{URL_PREFIX}/",
            body,
            crumbs=[("Home", "/"), ("Locations", f"/{URL_PREFIX}/")],
        ),
        encoding="utf-8",
    )

    seen_titles, seen_meta = {}, {}
    for town, county, slug in index_cards:
        page_html = (OUTPUT_DIR / slug / "index.html").read_text(encoding="utf-8")
        title = re.search(r"<title>(.*?)</title>", page_html).group(1)
        meta = re.search(r'<meta name="description" content="(.*?)">', page_html).group(1)
        if title in seen_titles:
            raise SystemExit(f"Duplicate title for {slug} and {seen_titles[title]}: {title}")
        if meta in seen_meta:
            raise SystemExit(f"Duplicate meta description for {slug} and {seen_meta[meta]}")
        seen_titles[title] = slug
        seen_meta[meta] = slug

    loc_ok, tst_ok = update_homepage(valid_towns, testimonials)
    has_tst_page = write_testimonials_page(testimonials)
    write_privacy_page()
    service_count = write_service_pages(BASE_DIR)

    urls = [f"{SITE_URL}/"]
    urls.extend(f"{SITE_URL}{path}" for path in service_paths())
    urls.append(f"{SITE_URL}/{URL_PREFIX}/")
    for _, _, slug in index_cards:
        urls.append(f"{SITE_URL}/{URL_PREFIX}/{slug}/")
        if slug == "nairobi":
            urls.extend(f"{SITE_URL}/{URL_PREFIX}/{area_slug}/" for area_slug, _name in NAIROBI_AREA_PAGES)
        elif slug == "karuri":
            urls.extend(f"{SITE_URL}/{URL_PREFIX}/{area_slug}/" for area_slug, _name in KIAMBU_AREA_PAGES)
    if has_tst_page:
        urls.append(f"{SITE_URL}/testimonials/")
    urls.append(f"{SITE_URL}/privacy-policy/")
    body = "\n".join(f"  <url><loc>{html.escape(url)}</loc></url>" for url in urls)
    (BASE_DIR / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n</urlset>\n",
        encoding="utf-8",
    )
    (BASE_DIR / "robots.txt").write_text(
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {SITE_URL}/sitemap.xml\n",
        encoding="utf-8",
    )

    print(f"Generated {len(index_cards)} town pages in: {OUTPUT_DIR}")
    print(f"Generated {service_count} service pages.")
    detailed = sum(1 for r in valid_towns if profiles.get(r["slug"], {}).get("areas"))
    print(f"Towns with neighbourhood details: {detailed}/{len(valid_towns)} (fill in town_profiles.json for the rest)")
    print(f"Testimonials loaded: {len(testimonials)}" + ("" if testimonials else " (section hidden until testimonials.csv has real rows)"))
    print("Homepage locations and testimonials updated." if loc_ok else "Note: homepage not updated.")
    if (BASE_DIR / "towns").exists():
        print("Note: an old 'towns' folder still exists. Delete it; vercel.json redirects /towns/* to /cleaning-services/*.")
    print(f"Canonical host: {SITE_URL}")


if __name__ == "__main__":
    main()
