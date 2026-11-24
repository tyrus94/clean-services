#!/usr/bin/env python3
"""Generate SEO landing pages for the towns listed in towns.csv.

Run from the project folder:
    python generate_pages.py

Optional canonical domain:
    SITE_URL=https://www.example.co.ke python generate_pages.py

Inputs:
    towns.csv            town, county, region, slug
    town_profiles.json   optional per-town details (type, areas, note) that make pages genuinely different
    testimonials.csv     REAL client testimonials only (name, town, service, rating, date, text)
    town-template.html   shared page layout

Output:
    cleaning-services/<town-slug>/index.html
    cleaning-services/index.html
    testimonials/index.html   (only when testimonials.csv has rows)
    index.html                (Locations + Testimonials blocks between the markers are refreshed)
    sitemap.xml               (when SITE_URL is set)
"""
from pathlib import Path
from urllib.parse import quote
import csv, hashlib, html, json, os, random, re

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "towns.csv"
TEMPLATE_FILE = BASE_DIR / "town-template.html"
PROFILES_FILE = BASE_DIR / "town_profiles.json"
TESTIMONIALS_FILE = BASE_DIR / "testimonials.csv"
URL_PREFIX = "cleaning-services"          # town pages live at /cleaning-services/<town>/
OUTPUT_DIR = BASE_DIR / URL_PREFIX
TESTIMONIALS_DIR = BASE_DIR / "testimonials"
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")
PHONE_DISPLAY = "+254 706 855633"
PHONE_TEL = "+254706855633"
WHATSAPP_NUMBER = "254706855633"
HOME_FILE = BASE_DIR / "index.html"
LOC_START, LOC_END = "<!-- LOCATIONS:START -->", "<!-- LOCATIONS:END -->"
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

H1_VARIANTS = [
    "Professional cleaning in <em>{town}</em>.",
    "Cleaning services in <em>{town}</em>, {county} County.",
    "A cleaner space in <em>{town}</em>.",
    "Home and business cleaning in <em>{town}</em>.",
]
TITLE_VARIANTS = [
    "Cleaning Services in {town}, {county} County | Cleaning Services Kenya",
    "{town} Home & Office Cleaning | Cleaning Services Kenya",
    "Cleaners in {town}: Request a Quote | Cleaning Services Kenya",
    "House & Commercial Cleaning in {town} | Cleaning Services Kenya",
]
META_VARIANTS = [
    "Need cleaning in {town}, {county} County? Request a quote from Cleaning Services Kenya for home or office cleaning and confirm availability.",
    "Home and business cleaning enquiries for {town}. Tell Cleaning Services Kenya what you need and we'll confirm availability in {county} County.",
    "Cleaning Services Kenya takes enquiries for residential, commercial and deep cleaning in {town}. Request a quote by WhatsApp or phone.",
    "Looking for a cleaner in {town}? Send your details to Cleaning Services Kenya for a quote on home, office or move-out cleaning.",
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
    "Shops, offices and other commercial premises in {town}: tell us the size, opening hours and the routine you need.",
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
    meta = " • ".join(x for x in [t["town"], t["date"]] if x)
    return (
        f'<article class="testimonial-card"{" hidden" if hidden else ""}>'
        f'<div class="t-top"><span class="t-stars" aria-label="{t["rating"]} out of 5 stars">{"★" * t["rating"]}</span>'
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
        chips = "".join(f"<li>{html.escape(a)}</li>" for a in areas)
        blocks.append(
            f'<div class="areas-block"><h3>Neighbourhoods in and around {html.escape(town)}</h3>'
            f'<ul class="area-chips">{chips}</ul>'
            f'<p class="areas-note">Not listed? Ask us. We’ll confirm whether we can reach you.</p></div>'
        )
    if near:
        links = "".join(
            f'<li><a href="/{URL_PREFIX}/{html.escape(n["slug"])}/">Cleaning in {html.escape(n["town"])}</a></li>'
            for n in near
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

    title = pick(slug, "title", TITLE_VARIANTS).format(**ctx)
    description = pick(slug, "meta", META_VARIANTS).format(**ctx)

    return {
        "ctx": ctx, "title": title, "description": description,
        "h1_html": pick(slug, "h1", H1_VARIANTS).format(town=html.escape(town), county=html.escape(county)),
        "hero_description": fmt(pick(slug, "intro", INTROS[ttype]), ctx),
        "services_intro": fmt(pick(slug, "si", SERVICES_INTRO), ctx),
        "home_card_text": fmt(pick(slug, "hc", HOME_CARD), ctx),
        "business_card_text": fmt(pick(slug, "bc", BUSINESS_CARD), ctx),
        "about_text": fmt(pick(slug, "about", ABOUT_TEXT), ctx),
        "coverage_text": fmt(pick(slug, "cov", COVERAGE_TEXT), ctx),
        "local_section": local_section, "faq_section": faq_section, "faq_schema_tag": faq_schema_tag,
    }


def simple_page(title, description, body, extra=""):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)}</title><meta name="description" content="{html.escape(description, quote=True)}"><link rel="stylesheet" href="/styles.css"></head><body><header class="site-header"><a class="brand" href="/"><span class="brand-name">CLEANING SERVICES <b>KENYA</b></span></a><nav class="main-nav"><a href="/">Home</a><a href="/#services">Services</a><a href="/#contact">Contact</a></nav></header><main class="section">{body}</main><footer class="site-footer"><a href="/">Cleaning Services Kenya</a><small>Made by Lumen Labs</small></footer>{extra}</body></html>"""


def build_locations_html(town_rows):
    groups = {}
    for item in town_rows:
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
    HOME_FILE.write_text(page, encoding="utf-8")
    return True, True


def write_testimonials_page(testimonials):
    if not testimonials:
        if TESTIMONIALS_DIR.exists():
            (TESTIMONIALS_DIR / "index.html").unlink(missing_ok=True)
        return False
    cards = "\n".join(testimonial_card(t, hidden=i >= 24) for i, t in enumerate(testimonials))
    body = (
        '<p class="eyebrow">CLIENT TESTIMONIALS</p><h1>What our clients say</h1>'
        f'<p>{len(testimonials)} testimonials from clients across Kenya.</p>'
        f'<div class="testimonials-grid" id="all-testimonials">{cards}</div>'
        '<p class="testimonial-more"><button class="button" id="show-more" type="button">Show more</button></p>'
    )
    script = """<script>
(function(){var b=document.getElementById('show-more');if(!b)return;
function more(){var h=document.querySelectorAll('#all-testimonials [hidden]');
for(var i=0;i<24&&i<h.length;i++)h[i].hidden=false;
if(document.querySelectorAll('#all-testimonials [hidden]').length===0)b.style.display='none';}
b.addEventListener('click',more);more();})();
</script>"""
    TESTIMONIALS_DIR.mkdir(exist_ok=True)
    page = simple_page("Client Testimonials | Cleaning Services Kenya",
                       "Read what clients say about Cleaning Services Kenya.", body, script)
    (TESTIMONIALS_DIR / "index.html").write_text(page, encoding="utf-8")
    return True


def main():
    if not CSV_FILE.exists() or not TEMPLATE_FILE.exists():
        raise SystemExit("Missing towns.csv or town-template.html. Keep them in the same folder as this script.")
    template = TEMPLATE_FILE.read_text(encoding="utf-8")
    valid_towns = load_towns()
    if not valid_towns:
        raise SystemExit("No valid towns found in towns.csv.")
    profiles = load_profiles()
    testimonials = load_testimonials()

    OUTPUT_DIR.mkdir(exist_ok=True)
    index_cards = []

    for row in valid_towns:
        town, county, region, slug = row["town"], row["county"], row["region"], row["slug"]
        c = build_content(row, valid_towns, profiles)
        whatsapp_text = quote(f"Hello Cleaning Services Kenya, I would like to enquire about cleaning services in {town}, {county} County.")
        canonical_tag = f'<link rel="canonical" href="{SITE_URL}/{URL_PREFIX}/{slug}/">' if SITE_URL else ""
        schema = {
            "@context": "https://schema.org", "@type": "Service",
            "name": f"Cleaning services in {town}",
            "serviceType": ["Residential cleaning", "Commercial cleaning", "Deep cleaning"],
            "areaServed": {"@type": "City", "name": town,
                           "containedInPlace": {"@type": "AdministrativeArea", "name": f"{county} County, Kenya"}},
            "provider": {"@type": "Organization", "name": "Cleaning Services Kenya"},
            "description": c["description"],
        }
        if SITE_URL:
            schema["provider"]["url"] = SITE_URL
        options = build_town_options(valid_towns, current_town=town)
        values = {
            "town": html.escape(town), "town_upper": html.escape(town.upper()),
            "county": html.escape(county), "county_upper": html.escape(county.upper()),
            "region": html.escape(region),
            "page_title": html.escape(c["title"]),
            "meta_description": html.escape(c["description"], quote=True),
            "canonical_tag": canonical_tag,
            "schema_json": json.dumps(schema, ensure_ascii=False).replace("</", "<\\/"),
            "whatsapp_text": whatsapp_text,
            "phone_display": html.escape(PHONE_DISPLAY), "phone_tel": PHONE_TEL,
            "whatsapp_number": WHATSAPP_NUMBER,
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

    links = "\n".join(
        f'<li><a href="/{URL_PREFIX}/{html.escape(slug)}/">Cleaning services in {html.escape(town)}</a> <span>— {html.escape(county)} County</span></li>'
        for town, county, slug in index_cards
    )
    body = (f'<p class="eyebrow">OUR LOCATIONS</p><h1>Cleaning service locations across Kenya</h1>'
            f'<p>Choose a town to enquire about residential or commercial cleaning. Service availability is confirmed individually.</p>'
            f'<ul class="town-directory">{links}</ul>')
    (OUTPUT_DIR / "index.html").write_text(
        simple_page("Cleaning Service Locations in Kenya | Cleaning Services Kenya",
                    "Browse our cleaning service enquiry pages for towns across Kenya.", body),
        encoding="utf-8")

    loc_ok, tst_ok = update_homepage(valid_towns, testimonials)
    has_tst_page = write_testimonials_page(testimonials)

    if SITE_URL:
        urls = [f"{SITE_URL}/", f"{SITE_URL}/{URL_PREFIX}/"] + [f"{SITE_URL}/{URL_PREFIX}/{s}/" for _, _, s in index_cards]
        if has_tst_page:
            urls.append(f"{SITE_URL}/testimonials/")
        body = "\n".join(f"  <url><loc>{html.escape(u)}</loc></url>" for u in urls)
        (BASE_DIR / "sitemap.xml").write_text(
            f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n',
            encoding="utf-8")

    print(f"Generated {len(index_cards)} town pages in: {OUTPUT_DIR}")
    detailed = sum(1 for r in valid_towns if profiles.get(r["slug"], {}).get("areas"))
    print(f"Towns with neighbourhood details: {detailed}/{len(valid_towns)} (fill in town_profiles.json for the rest)")
    print(f"Testimonials loaded: {len(testimonials)}" + ("" if testimonials else " (section hidden until testimonials.csv has real rows)"))
    print("Homepage locations and testimonials updated." if loc_ok else "Note: homepage not updated.")
    if (BASE_DIR / "towns").exists():
        print("Note: an old 'towns' folder still exists. Delete it; vercel.json redirects /towns/* to /cleaning-services/*.")
    if not SITE_URL:
        print("Note: SITE_URL is not set, so canonical tags and sitemap.xml were omitted.")


if __name__ == "__main__":
    main()
