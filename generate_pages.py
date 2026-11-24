!/usr/bin/env python3
"""Generate SEO landing pages for the towns listed in towns.csv and testimonials.csv.

Run from the project folder:
    python generate_pages.py

Optional canonical domain:
    SITE_URL=https://www.example.co.ke python generate_pages.py

Output:
    towns/<town-slug>/index.html
    towns/index.html
"""
from pathlib import Path
from urllib.parse import quote
import csv, html, json, os, re

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "towns.csv"
TESTIMONIALS_FILE = BASE_DIR / "testimonials.csv"
TEMPLATE_FILE = BASE_DIR / "town-template.html"
OUTPUT_DIR = BASE_DIR / "towns"
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")
PHONE_DISPLAY = "+254 706 855633"
PHONE_TEL = "+254706855633"
WHATSAPP_NUMBER = "254706855633"


def slugify(value: str) -> str:
    value = value.lower().replace("’", "").replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def replace_tokens(template: str, values: dict) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", str(value))
    return template


def build_town_options(town_rows: list, current_town: str = "") -> str:
    seen = set()
    options = ['<option value="">Select another town / location</option>']
    curr_norm = current_town.strip().lower()
    for item in town_rows:
        t_name = item["town"].strip()
        t_county = item["county"].strip()
        if not t_name:
            continue
        if curr_norm and t_name.lower() == curr_norm:
            continue
        label = f"{t_name}, {t_county} County" if t_county else t_name
        if label in seen:
            continue
        seen.add(label)
        options.append(f'<option value="{html.escape(label, quote=True)}">{html.escape(label)}</option>')
    options.append('<option value="Other / Not listed">Other / Not listed</option>')
    return "\n            ".join(options)


def build_testimonials_html(reviews: list, limit: int = 6) -> tuple[str, str, int]:
    if not reviews:
        return "", "5.0", 0
    total = len(reviews)
    avg = sum(int(r.get("rating", 5)) for r in reviews) / total
    cards = []
    for r in reviews[:limit]:
        stars = "★" * int(r.get("rating", 5))
        cards.append(
            f'        <article class="testimonial-card">'
            f'<div class="t-top"><span class="t-stars" aria-label="{r["rating"]} out of 5 stars">{stars}</span>'
            f'<span class="t-service">{html.escape(r["service"])}</span></div>'
            f'<p class="t-text">“{html.escape(r["text"])}”</p>'
            f'<div class="t-meta"><strong>{html.escape(r["name"])}</strong>'
            f'<span>{html.escape(r["town"])} • {html.escape(r["date"])}</span></div>'
            f'</article>'
        )
    return "\n".join(cards), f"{avg:.1f}", total


def main() -> None:
    if not CSV_FILE.exists() or not TEMPLATE_FILE.exists():
        raise SystemExit("Missing towns.csv or town-template.html. Keep all files in the same folder.")

    template = TEMPLATE_FILE.read_text(encoding="utf-8")
    with CSV_FILE.open(newline="", encoding="utf-8-sig") as file:
        towns = list(csv.DictReader(file))

    if not towns:
        raise SystemExit("No towns found in towns.csv.")

    testimonials_by_town = {}
    if TESTIMONIALS_FILE.exists():
        with TESTIMONIALS_FILE.open(newline="", encoding="utf-8-sig") as f:
            for item in csv.DictReader(f):
                t_key = (item.get("town") or "").strip().lower()
                if t_key:
                    testimonials_by_town.setdefault(t_key, []).append(item)

    valid_towns = []
    for row in towns:
        t = (row.get("town") or "").strip()
        c = (row.get("county") or "").strip()
        r = (row.get("region") or "").strip()
        s = (row.get("slug") or "").strip() or slugify(t)
        if not t or not c or not s:
            print(f"Skipping incomplete row: {row}")
            continue
        valid_towns.append({"town": t, "county": c, "region": r, "slug": s})

    if not valid_towns:
        raise SystemExit("No valid towns found in towns.csv.")

    OUTPUT_DIR.mkdir(exist_ok=True)
    index_cards = []
    generated = 0

    for row in valid_towns:
        town = row["town"]
        county = row["county"]
        region = row["region"]
        slug = row["slug"]

        town_reviews = testimonials_by_town.get(town.lower(), [])
        testimonials_html, avg_rating, review_count = build_testimonials_html(town_reviews, limit=6)

        title = f"Cleaning Services in {town} | Cleaning Services Kenya"
        description = f"Looking for home or commercial cleaning in {town}, {county} County? Contact Cleaning Services Kenya to request a quote and confirm service availability."
        whatsapp_text = quote(f"Hello Cleaning Services Kenya, I would like to enquire about cleaning services in {town}, {county} County.")
        canonical_tag = f'<link rel="canonical" href="{SITE_URL}/towns/{slug}/">' if SITE_URL else ""
        schema = {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": f"Cleaning services in {town}",
            "serviceType": ["Residential cleaning", "Commercial cleaning", "Deep cleaning"],
            "areaServed": {
                "@type": "City",
                "name": town,
                "containedInPlace": {"@type": "AdministrativeArea", "name": f"{county} County, Kenya"}
            },
            "provider": {"@type": "Organization", "name": "Cleaning Services Kenya"},
            "description": description
        }
        if SITE_URL:
            schema["provider"]["url"] = SITE_URL
        if review_count > 0:
            schema["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": avg_rating,
                "reviewCount": str(review_count)
            }

        other_town_options_html = build_town_options(valid_towns, current_town=town)

        values = {
            "town": html.escape(town),
            "town_upper": html.escape(town.upper()),
            "county": html.escape(county),
            "county_upper": html.escape(county.upper()),
            "region": html.escape(region),
            "page_title": html.escape(title),
            "meta_description": html.escape(description, quote=True),
            "canonical_tag": canonical_tag,
            "schema_json": json.dumps(schema, ensure_ascii=False).replace("</", "<\/"),
            "whatsapp_text": whatsapp_text,
            "phone_display": html.escape(PHONE_DISPLAY),
            "phone_tel": PHONE_TEL,
            "whatsapp_number": WHATSAPP_NUMBER,
            "town_options": other_town_options_html,
            "other_town_options": other_town_options_html,
            "testimonials_html": testimonials_html,
            "avg_rating": avg_rating,
            "review_count": review_count,
        }
        page = replace_tokens(template, values)
        destination = OUTPUT_DIR / slug / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(page, encoding="utf-8")
        generated += 1
        index_cards.append((town, county, slug))

    links = "\n".join(
        f'<li><a href="/towns/{html.escape(slug)}/">Cleaning services in {html.escape(town)}</a> <span>— {html.escape(county)} County</span></li>'
        for town, county, slug in index_cards
    )
    directory_page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Cleaning Service Locations in Kenya | Cleaning Services Kenya</title><meta name="description" content="Browse our cleaning service enquiry pages for towns across Kenya."><link rel="stylesheet" href="/styles.css"></head><body><header class="site-header"><a class="brand" href="/"><span class="brand-name">CLEANING SERVICES <b>KENYA</b></span></a><nav class="main-nav"><a href="/">Home</a><a href="/#services">Services</a><a href="/#contact">Contact</a></nav></header><main class="section"><p class="eyebrow">OUR LOCATIONS</p><h1>Cleaning service locations across Kenya</h1><p>Choose a town to enquire about residential or commercial cleaning. Service availability is confirmed individually.</p><ul class="town-directory">{links}</ul></main><footer class="site-footer"><a href="/">Cleaning Services Kenya</a><small>Made by Lumen Labs</small></footer></body></html>"""
    (OUTPUT_DIR / "index.html").write_text(directory_page, encoding="utf-8")

    if SITE_URL:
        sitemap_urls = [f"{SITE_URL}/"] + [f"{SITE_URL}/towns/{slug}/" for _, _, slug in index_cards]
        sitemap_body = "\n".join(f"  <url><loc>{html.escape(url)}</loc></url>" for url in sitemap_urls)
        sitemap = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sitemap_body}\n</urlset>\n'
        (BASE_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    print(f"Generated {generated} town pages in: {OUTPUT_DIR}")
    print(f"Town directory: {OUTPUT_DIR / 'index.html'}")


if __name__ == "__main__":
    main()
