"""Service landing pages for the high-volume topics in the keyword research.

Copy stays inside what the site already supports: enquiries by phone or
WhatsApp, availability confirmed per address, and no published prices.
"""
import html
from pathlib import Path
from urllib.parse import quote

from page_chrome import (
    FEATURED_TOWNS,
    IMG_FLOOR,
    IMG_HOME,
    IMG_TEAM,
    IMG_WORK,
    PHONE_DISPLAY,
    PHONE_TEL,
    SERVICE_LINKS,
    SITE_URL,
    WHATSAPP_NUMBER,
    breadcrumb_ld,
    breadcrumb_nav,
    render_page,
    service_options,
)

# TODO(owner): add Offer.price or priceRange on each Service node only after real prices are confirmed.
SCHEMA_TODO = (
    "<!-- TODO(owner): Service schema has no Offer, price or priceRange. "
    "Add them only when the owner confirms real figures. "
    "A pest-control licence number is also omitted because it is not published on the site. -->"
)

TOWN_LINKS = FEATURED_TOWNS


def _p(parts):
    return "".join(f"<p>{part}</p>" for part in parts)


def _cards(cards):
    body = "".join(
        f'<article class="need-card"><h3>{html.escape(title)}</h3><p>{html.escape(text)}</p></article>'
        for title, text in cards
    )
    return f'<div class="need-grid">{body}</div>'


def _steps(steps):
    articles = []
    for index, (title, text) in enumerate(steps, start=1):
        articles.append(
            "<article>"
            f'<span class="process-no">{index:02d}</span>'
            '<div class="process-icon">✳</div>'
            f"<h3>{html.escape(title)}</h3>"
            f"<p>{html.escape(text)}</p>"
            "</article>"
        )
    return (
        '<section class="section process-section" id="process">'
        '<div class="center-heading"><p class="eyebrow"><span class="eyebrow-line"></span> HOW A VISIT IS ARRANGED</p>'
        "<h2>Tell us, confirm,<br><em>then we come.</em></h2></div>"
        f'<div class="process-grid">{"".join(articles)}</div></section>'
    )


def _faq(faqs):
    blocks = "".join(
        f"<details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>"
        for q, a in faqs
    )
    return (
        '<section class="section faq-section" id="faq">'
        '<div class="center-heading"><p class="eyebrow"><span class="eyebrow-line"></span> GOOD TO KNOW</p>'
        "<h2>Questions we hear<br><em>before a quote.</em></h2></div>"
        f'<div class="faq-list">{blocks}</div></section>'
    )


def _faq_ld(faqs):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {"@type": "Answer", "text": answer},
            }
            for question, answer in faqs
        ],
    }


def _town_chips():
    items = "".join(
        f'<li><a href="/cleaning-services/{slug}/">Cleaning services in {html.escape(name)}</a></li>'
        for slug, name in TOWN_LINKS
    )
    return (
        '<div class="areas-block"><h3>Town pages</h3>'
        f'<ul class="area-chips area-links">{items}</ul>'
        '<p class="areas-note">Choose a town to enquire locally. Availability is confirmed for your address.</p></div>'
    )


def _related(current_slug):
    items = "".join(
        f'<li><a href="/{slug}/">{html.escape(label)}</a></li>'
        for slug, label in SERVICE_LINKS
        if slug != current_slug
    )
    return (
        '<div class="areas-block"><h3>Related services</h3>'
        f'<ul class="area-chips area-links">{items}</ul></div>'
    )


def _booking(selected, intro):
    wa = f"https://wa.me/{WHATSAPP_NUMBER}"
    return f"""<section class="section booking-section" id="contact">
      <div class="booking-intro">
        <p class="eyebrow"><span class="eyebrow-line"></span> LET'S GET STARTED</p>
        <h2>Request a quote<br><em>on WhatsApp.</em></h2>
        <p>{intro}</p>
        <div class="contact-details">
          <div><span class="contact-symbol">☎</span><p><small>GIVE US A CALL</small><a href="tel:{PHONE_TEL}">{PHONE_DISPLAY}</a></p></div>
          <div><span class="contact-symbol">◉</span><p><small>CHAT WITH OUR TEAM</small><a href="{wa}" target="_blank" rel="noopener">WhatsApp us</a></p></div>
        </div>
      </div>
      <form class="booking-form" id="booking">
        <div class="form-top"><span>YOUR CLEANING ENQUIRY</span><span>KENYA</span></div>
        <div class="form-row">
          <label>Your name<input name="name" type="text" placeholder="How should we address you?" required></label>
          <label>Phone number<input name="phone" type="tel" placeholder="Your contact number" required></label>
        </div>
        <label>What service are you looking for?<select name="service" required>{service_options(selected)}</select></label>
        <div class="form-row">
          <label>Where is the property?<input name="location" type="text" placeholder="Town / neighbourhood" required></label>
          <label>Preferred date<input name="date" type="date"></label>
        </div>
        <label>Tell us a little more <span class="optional">(optional)</span><textarea name="details" rows="3" placeholder="Property size, rooms, special requests..."></textarea></label>
        <button class="button form-submit" type="submit">Continue to WhatsApp <span>↗</span></button>
        <p class="form-note">Nothing is booked until our team confirms availability and next steps on WhatsApp.</p>
        <p class="form-error" role="alert" aria-live="polite"></p>
      </form>
    </section>"""


def _hero(page, wa_url):
    crumbs = breadcrumb_nav([("Home", "/"), (page["crumb"], page["path"])])
    return f"""<section class="hero">
      <div class="hero-copy">
        {crumbs}
        <p class="eyebrow"><span class="eyebrow-line"></span> {html.escape(page["eyebrow"])}</p>
        <h1>{page["h1_html"]}</h1>
        <p class="hero-slogan">{page["slogan_html"]}</p>
        <p class="hero-description">{page["lead"]}</p>
        <div class="hero-actions">
          <a class="button" href="#booking">Request a quote <span>↗</span></a>
          <a class="text-link" href="tel:{PHONE_TEL}"><span class="phone-icon">↗</span> Call {PHONE_DISPLAY}</a>
        </div>
      </div>
      <div class="hero-visual">
        <img class="hero-image" src="{page["image"]}" alt="{html.escape(page["image_alt"], quote=True)}" fetchpriority="high">
        <div class="image-note"><span class="note-spark">✳</span><span>Make room for<br><strong>feeling good.</strong></span></div>
        <div class="vertical-label">CLEAN SPACES, CALMER DAYS</div>
      </div>
    </section>
    <section class="trust-strip" aria-label="How enquiries work">
      <div><span>01</span><strong>Phone or WhatsApp</strong></div>
      <div><span>02</span><strong>Quote for your space</strong></div>
      <div><span>03</span><strong>Address confirmed</strong></div>
      <div><span>04</span><strong>Nairobi and beyond</strong></div>
    </section>"""


def _section(sec):
    sid = f' id="{html.escape(sec["id"], quote=True)}"' if sec.get("id") else ""
    cards = _cards(sec["cards"]) if sec.get("cards") else ""
    paragraphs = sec.get("paragraphs") or []
    bullets = ""
    if sec.get("bullets"):
        bullets = "<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in sec["bullets"]) + "</ul>"
    if bullets and paragraphs:
        copy = f"<p>{paragraphs[0]}</p>{bullets}" + "".join(f"<p>{part}</p>" for part in paragraphs[1:])
    else:
        copy = _p(paragraphs) + bullets
    return f"""<section class="section"{sid}>
      <div class="section-heading"><div><p class="eyebrow"><span class="eyebrow-line"></span> {html.escape(sec["eyebrow"])}</p><h2>{sec["h2_html"]}</h2></div></div>
      <div class="copy">{copy}</div>
      {cards}
    </section>"""


def _service_ld(page):
    return {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": page["schema_name"],
        "serviceType": page["service_type"],
        "url": SITE_URL + page["path"],
        "description": page["description"],
        "areaServed": [{"@type": "Country", "name": "Kenya"}]
        + [{"@type": "City", "name": name} for _, name in TOWN_LINKS],
        "provider": {
            "@type": "LocalBusiness",
            "@id": f"{SITE_URL}/#organization",
            "name": "Cleaning Services Kenya",
            "url": f"{SITE_URL}/",
            "telephone": PHONE_TEL,
        },
    }


def render_service(page) -> str:
    wa_text = page["whatsapp_text"]
    wa_url = f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(wa_text)}"
    sections = "".join(_section(sec) for sec in page["sections"])
    places = f"""<section class="section" id="locations">
      <div class="section-heading"><div><p class="eyebrow"><span class="eyebrow-line"></span> WHERE WE TAKE ENQUIRIES</p><h2>Nairobi, and towns<br><em>across Kenya.</em></h2></div></div>
      <div class="copy">{_p(page["place_paragraphs"])}</div>
      {_town_chips()}
      {_related(page["slug"])}
    </section>"""
    main = (
        "<main>\n"
        + _hero(page, wa_url)
        + sections
        + places
        + _steps(page["steps"])
        + _faq(page["faqs"])
        + _booking(page["form_service"], page["booking_intro"])
        + f"""<section class="final-cta"><div><p class="eyebrow eyebrow-light"><span class="eyebrow-line"></span> A FRESH START IS ONE MESSAGE AWAY</p><h2>Ready to talk about<br><em>{html.escape(page["cta_em"])}?</em></h2></div><div class="final-actions"><a class="button button-light" href="{html.escape(wa_url, quote=True)}" target="_blank" rel="noopener">Book on WhatsApp <span>↗</span></a><a href="tel:{PHONE_TEL}" class="final-call">Or call {PHONE_DISPLAY}</a></div></section>
  </main>"""
    )
    extra_ld = [
        SCHEMA_TODO,
        _service_ld(page),
        breadcrumb_ld([("Home", "/"), (page["crumb"], page["path"])]),
        _faq_ld(page["faqs"]),
    ]
    return render_page(
        page["title"],
        page["description"],
        page["path"],
        main,
        extra_ld=extra_ld,
        whatsapp_text=wa_text,
    )


def _page(**kwargs):
    kwargs["path"] = f"/{kwargs['slug']}/"
    return kwargs


PAGES = [
    _page(
        slug="fumigation",
        crumb="Fumigation",
        title="Fumigation Services in Nairobi & Kenya | Cleaning Services Kenya",
        description="Fumigation and pest control for homes and businesses in Nairobi and across Kenya. Cockroaches, bed bugs and other pests. Call or WhatsApp +254 706 855633.",
        eyebrow="FUMIGATION & PEST CONTROL",
        h1_html="Fumigation services<br><em>in Nairobi &amp; Kenya.</em>",
        slogan_html="Pest control for homes and workplaces.",
        lead="Tell us the pest, the town and the type of property. Cleaning Services Kenya replies with whether we can visit and what the fumigation quote covers.",
        image=IMG_TEAM,
        image_alt="A team of professional cleaners ready to work",
        schema_name="Fumigation and pest control",
        service_type="Fumigation",
        form_service="Fumigation & pest control",
        whatsapp_text="Hello Cleaning Services Kenya, I would like a fumigation and pest control quote.",
        booking_intro="Send the town, the pest and a rough size. Your enquiry opens in WhatsApp for you to review before it is sent. You can also call +254 706 855633.",
        cta_em="a fumigation visit",
        sections=[
            {
                "eyebrow": "WHAT FUMIGATION MEANS",
                "h2_html": "A pest treatment,<br><em>arranged for your building.</em>",
                "paragraphs": [
                    "In Kenya, people usually say fumigation when they want a property treated for insects. The visit may use a spray, a mist or a fog. The method depends on the pest and on where it is living, which is why we ask before we quote.",
                    "A fumigation visit is a different booking from a <a href=\"/house-cleaning/\">house clean</a> or an <a href=\"/office-cleaning/\">office clean</a>. Pair them when you want both, and we will say which part of the quote covers which job.",
                    "One visit is a treatment, not a lifetime guarantee. If food is left open, drains stay wet or gaps let insects back in, they can return. We will say that plainly when it applies to your place.",
                ],
            },
            {
                "eyebrow": "PESTS PEOPLE ASK ABOUT",
                "h2_html": "Cockroaches, bed bugs<br><em>and the rest.</em>",
                "paragraphs": [
                    "Name what you are seeing. A kitchen full of cockroaches, bed bugs in a bedroom, ants along a skirting board, fleas after pets, or mosquitoes in a room that will not settle: each one changes how we plan the visit.",
                    "Bed bugs often involve the mattress and the sofa as well as the room. If you want those cleaned rather than treated, see <a href=\"/sofa-cleaning/\">sofa and upholstery cleaning</a> and tell us in the same message.",
                    "We carry out the treatment and bring the equipment for that visit. This page does not sell fumigation machines or list machine prices. If you were comparing equipment to buy, the service we offer is the visit itself.",
                ],
                "cards": [
                    ("Cockroach fumigation", "Kitchens, drains and shop stores. Tell us how widespread it is and whether the space is a home or a food business."),
                    ("Bed bug fumigation", "Bedrooms, guest rooms and lodgings. Say how many rooms are affected and whether furniture can be moved."),
                    ("Before a move-in", "A treatment ahead of unpacking, often alongside a move-in clean. Share the key date."),
                    ("Workplaces", "Offices, shops and restaurants. Share opening hours so the visit can sit around customers and staff."),
                ],
            },
            {
                "eyebrow": "FUMIGATION PRICES IN KENYA",
                "h2_html": "The quote follows<br><em>the property.</em>",
                "paragraphs": [
                    "Fumigation prices in Kenya vary with the number of rooms, the pest, how heavy the problem is and whether you want a follow-up. Cleaning Services Kenya does not print a flat rate on this page.",
                    "Message the neighbourhood, the pest and the bedroom or floor count. We reply with a figure for that property, or we tell you if we cannot take the address.",
                ],
            },
        ],
        place_paragraphs=[
            "Fumigation services in Nairobi are the enquiries we plan around most often. Neighbourhoods already listed for our Nairobi cleaning page include Westlands, Kilimani, Lavington, Karen, South B, Kileleshwa, Parklands and Embakasi. Start from the <a href=\"/cleaning-services/nairobi/\">Nairobi page</a> if that is your city.",
            "Fumigation services in Mombasa, Kisumu and other towns are welcome too. Use the town page so the message lands with the right place name, and say that you want fumigation rather than a general clean.",
        ],
        steps=[
            ("Describe the pest", "Tell us what you have seen, which rooms, and whether anyone sleeps or cooks there."),
            ("We confirm a quote", "We check the town and reply with the price and a time that can work."),
            ("The visit goes ahead", "Once you accept, the team comes with the equipment for that treatment."),
        ],
        faqs=[
            ("What is fumigation?", "It is a pest-control treatment for a room or a whole property, using a spray, mist or fog chosen for the insect and the building. It is booked separately from an ordinary house clean."),
            ("Do you offer fumigation services in Nairobi?", "Yes. Send the neighbourhood, the pest and the type of property. We confirm that we can reach the address before anything is booked."),
            ("Do you treat cockroaches and bed bugs?", "Those are two of the most common reasons people enquire. Name the pest in your message so the quote matches the job."),
            ("How much do fumigation services cost in Kenya?", "We quote after we know the rooms, the pest and whether a follow-up is needed. There is no single price on this page."),
            ("Do you sell fumigation machines?", "No. We provide the fumigation visit. We do not sell machines or publish machine prices."),
            ("Can you fumigate an office or a shop?", "Send the workplace details and the hours you can give us access. We will say whether that timing works."),
        ],
    ),
    _page(
        slug="carpet-cleaning",
        crumb="Carpet cleaning",
        title="Carpet Cleaning Services in Nairobi & Kenya | Cleaning Services Kenya",
        description="Carpet cleaning for homes and offices in Nairobi and across Kenya. Rugs, fitted carpets and stains. Call or WhatsApp +254 706 855633 for a quote.",
        eyebrow="CARPET CLEANING",
        h1_html="Carpet cleaning services<br><em>in Nairobi &amp; Kenya.</em>",
        slogan_html="Rugs and fitted carpets, cleaned where they lie.",
        lead="Send the rooms, a rough size and what has been spilled. We confirm carpet cleaning availability for your address and quote before any visit is booked.",
        image=IMG_FLOOR,
        image_alt="Professional cleaner carefully cleaning a floor",
        schema_name="Carpet cleaning",
        service_type="Carpet cleaning",
        form_service="Carpet cleaning",
        whatsapp_text="Hello Cleaning Services Kenya, I would like a carpet cleaning quote.",
        booking_intro="Tell us the town, how many carpets or rooms, and whether the pile is wool, synthetic or unknown. Call +254 706 855633 or continue on WhatsApp.",
        cta_em="your carpets",
        sections=[
            {
                "eyebrow": "WHAT WE CLEAN",
                "h2_html": "From a single rug<br><em>to an office floor.</em>",
                "paragraphs": [
                    "Nairobi dust, rainy-season mud and everyday foot traffic settle into carpet pile. Vacuuming lifts the surface. Tea, soda, mud from the gate and the grey film in a hallway often need a proper carpet clean.",
                    "If the floors are tile, terrazzo or wood, ask for <a href=\"/house-cleaning/\">house cleaning</a> instead. This page is for rugs and fitted carpet. Fabric sofas in the same room can be quoted with <a href=\"/sofa-cleaning/\">sofa cleaning</a>.",
                ],
                "cards": [
                    ("Home carpets", "Living rooms, bedrooms and hallways in houses and apartments. Tell us which rooms and whether anyone will be home."),
                    ("Rugs", "Loose rugs that can be cleaned in place. Mention the size and if the fringe or the backing is delicate."),
                    ("Office carpet", "Reception and workstation carpet in workplaces. Share the floor area and the best time to be on site."),
                    ("Move-in carpets", "A carpet clean before a new tenant arrives. Pair it with a move-in house clean if the rest of the rooms need it too."),
                ],
            },
            {
                "eyebrow": "STAINS AND FIBRES",
                "h2_html": "Tell us the carpet<br><em>and the mark.</em>",
                "paragraphs": [
                    "Wool, polypropylene and blended carpets take water differently. If you know the fibre, say so. If you do not, say that too. We would rather see a photo than guess from a one-word description.",
                    "Point out stains when you enquire: tea, juice, ink, mud or something you cannot name. Some marks lift. Some have sat too long. We will tell you when a stain looks unlikely to come out fully.",
                    "Carpet cleaning prices depend on the area, how soiled the carpet is and whether you want extra time on stains. We quote the job in front of us. There is no rate card on this page.",
                ],
            },
        ],
        place_paragraphs=[
            "Carpet cleaning in Nairobi covers the neighbourhoods on our <a href=\"/cleaning-services/nairobi/\">Nairobi cleaning page</a>: Westlands, Kilimani, Lavington, Karen, South B, Kileleshwa, Parklands and Embakasi. If you searched for carpet cleaning near you, the neighbourhood is the detail that lets us confirm the visit.",
            "The same enquiry works for Mombasa, Kisumu, Nakuru, Eldoret, Thika and the other towns linked below. Salt air on the coast and red soil upcountry mark carpets in different ways, so the town belongs in the message.",
        ],
        steps=[
            ("Send the details", "Rooms, approximate size, fibre if you know it, and the stains you care about."),
            ("We quote the clean", "The price follows the area and the condition. We also confirm we can reach you."),
            ("We clean on site", "The carpets stay in your home or office. You do not deliver them to a shop."),
        ],
        faqs=[
            ("Do you offer carpet cleaning in Nairobi?", "Yes. Send the neighbourhood and what needs cleaning. We confirm the address before a visit is agreed."),
            ("Can you clean office carpets?", "Share the floor area and a time when we can work around staff. Office carpet is a normal enquiry."),
            ("Do you clean loose rugs as well as fitted carpet?", "Yes. Tell us the size and whether the rug can be cleaned where it lies."),
            ("How much do carpet cleaning services cost?", "The quote depends on the area, the soil and any stain work. Send those details and we will price that carpet."),
            ("Can you also clean the sofa?", "Ask for both. Sofa and upholstery cleaning is quoted on its own page and can be booked for the same day when the schedule allows."),
        ],
    ),
    _page(
        slug="sofa-cleaning",
        crumb="Sofa cleaning",
        title="Sofa & Upholstery Cleaning in Nairobi | Cleaning Services Kenya",
        description="Sofa cleaning, couch cleaning and upholstery cleaning in Nairobi and across Kenya, including sofa sets and mattresses. WhatsApp or call +254 706 855633.",
        eyebrow="SOFA & UPHOLSTERY",
        h1_html="Sofa cleaning services<br><em>in Nairobi &amp; Kenya.</em>",
        slogan_html="Couches, sofa sets and other upholstery, cleaned at home.",
        lead="Fabric and leather need different care. Tell us what the suite is made of, how many seats it has and which town it is in. We quote sofa cleaning before we book the visit.",
        image=IMG_HOME,
        image_alt="Cleaning team refreshing a modern apartment living room",
        schema_name="Sofa and upholstery cleaning",
        service_type="Upholstery cleaning",
        form_service="Sofa & upholstery cleaning",
        whatsapp_text="Hello Cleaning Services Kenya, I would like a sofa and upholstery cleaning quote.",
        booking_intro="Include the number of seats, fabric or leather, and the town. A mattress or carpet in the same room can go in the same message. Call +254 706 855633 if you prefer.",
        cta_em="the sofa",
        sections=[
            {
                "eyebrow": "SOFAS, COUCHES AND SETS",
                "h2_html": "Seat by seat,<br><em>in your living room.</em>",
                "paragraphs": [
                    "A sofa set in a Kenyan living room collects tea, juice, dust and the traffic of a household. We clean it in your home. There is no need to send the furniture anywhere.",
                    "Say whether you have a two-seater, a corner suite or a 7-seater. The seat count changes the time and the quote. Fabric, leather and mixed suites are priced from what you describe, and photos help.",
                    "Upholstery cleaning on this page also covers fabric dining chairs and loose cushions when they are part of the same visit. Tell us the count.",
                ],
                "cards": [
                    ("Fabric sofas", "The usual request: a fabric couch or a full sofa set with cushions. Mention stains you want treated."),
                    ("Leather", "Leather is a different process from cloth. Say so in the first message so the quote is for the right job."),
                    ("Sofa sets", "L-shaped suites and 7-seaters. Count the seats, including the ones that do not look dirty."),
                    ("Chairs and cushions", "Dining chairs and spare cushions cleaned with the sofa when you want the room handled together."),
                ],
            },
            {
                "id": "mattress-cleaning",
                "eyebrow": "MATTRESSES",
                "h2_html": "Mattress cleaning<br><em>with the same visit.</em>",
                "paragraphs": [
                    "Mattress cleaning is a common add-on when the sofa is already being done, or on its own when a bed needs attention. Clients have asked us to refresh mattresses along with carpets. Tell us the bed size and how many mattresses.",
                    "If the reason is bed bugs rather than stains or dust, start with <a href=\"/fumigation/\">fumigation</a> and mention the mattress. A clean and a pest treatment solve different problems, and we will quote the one you actually need.",
                    "Sofa cleaning prices in Kenya follow the seats, the material and the staining. A mattress adds its own line. We send the figure after we have those details. Nothing on this page is a fixed tariff.",
                ],
            },
        ],
        place_paragraphs=[
            "Sofa cleaning in Nairobi is booked through the <a href=\"/cleaning-services/nairobi/\">Nairobi page</a> or the form on this page. Neighbourhoods we already name for Nairobi include Westlands, Kilimani, Lavington, Karen, Kileleshwa, Parklands, South B and Embakasi.",
            "People also ask about sofa cleaning in Thika, Mombasa, Kisumu, Nakuru and Eldoret. Open that town's page, or write the town in the form. We confirm the address either way. The living-room carpet can be added from the <a href=\"/carpet-cleaning/\">carpet cleaning</a> page.",
        ],
        steps=[
            ("Describe the suite", "Seats, fabric or leather, stains, and whether a mattress is included."),
            ("We price the visit", "You get a quote for that furniture and a yes or no on the location."),
            ("We work in the room", "Protective coverings go down where the floor needs them, then we clean the upholstery."),
        ],
        faqs=[
            ("Do you offer sofa cleaning in Nairobi?", "Yes. Send the neighbourhood, the material and the number of seats. We confirm the visit before it is booked."),
            ("Can you clean a whole sofa set?", "Yes. A sofa set, including larger 7-seaters, is a normal request. The seat count belongs in the enquiry."),
            ("Do you clean leather couches?", "Leather can be booked. It is quoted separately from fabric because the work is different."),
            ("Do you offer mattress cleaning?", "Yes, on its own or with the sofa. Tell us how many mattresses and the sizes."),
            ("How much does sofa cleaning cost in Kenya?", "The price depends on seats, material and staining. Send those details for a quote. We do not list a single sofa price here."),
            ("Which towns can request sofa cleaning?", "Nairobi, Thika, Mombasa, Kisumu, Nakuru, Eldoret and the other towns on our location list. Your exact address is confirmed in the reply."),
        ],
    ),
    _page(
        slug="parapet-cleaning",
        crumb="Parapet cleaning",
        title="Parapet Cleaning Services in Nairobi & Kenya | Cleaning Services Kenya",
        description="Parapet cleaning for apartments and offices in Nairobi and across Kenya. Exterior parapet walls, quoted once access is confirmed. Call +254 706 855633.",
        eyebrow="PARAPET CLEANING",
        h1_html="Parapet cleaning services<br><em>in Nairobi &amp; Kenya.</em>",
        slogan_html="Exterior parapet walls, cleaned with the building's access in mind.",
        lead="A parapet is the low wall at the edge of a roof, balcony or terrace. On many blocks it is also the band of exterior wall that collects dust, algae and rain streaks. Tell us the building and how it can be reached.",
        image=IMG_WORK,
        image_alt="Commercial cleaning staff at work",
        schema_name="Parapet cleaning",
        service_type="Parapet cleaning",
        form_service="Parapet cleaning",
        whatsapp_text="Hello Cleaning Services Kenya, I would like a parapet cleaning quote.",
        booking_intro="Send the town, the number of floors or balconies, and who can approve access. Photos help. Call +254 706 855633 or use WhatsApp.",
        cta_em="the parapet",
        sections=[
            {
                "eyebrow": "WHAT THE JOB IS",
                "h2_html": "The outside wall,<br><em>not the corridor mop.</em>",
                "paragraphs": [
                    "Parapet cleaning services in Nairobi are usually for mid-rise and high-rise buildings: balcony fronts, rooftop parapets and the exterior walls around them. It is outdoor work. Interior <a href=\"/office-cleaning/\">office cleaning</a> and <a href=\"/house-cleaning/\">house cleaning</a> are separate bookings.",
                    "Access has to be safe for that building. The visit might be from a balcony, from the roof, or by another route the caretaker or property manager allows. We agree the route before we set a date. We do not arrive and invent a way onto a facade.",
                    "This page is for booking the clean. Staff vacancies are not advertised here.",
                ],
                "cards": [
                    ("Apartment blocks", "Balcony parapets and shared exterior walls. A manager may need to approve access even when a resident makes the enquiry."),
                    ("Office buildings", "Street-facing parapets ahead of a tenant moving in, a sale, or a scheduled wash."),
                    ("Rooftop edges", "The low wall around a roof terrace. Tell us about water supply and who holds the roof key."),
                    ("Single homes", "A house balcony that has gone dark in the rain. Say how many sides and whether a ladder is already on site."),
                ],
            },
            {
                "eyebrow": "WHAT TO SEND",
                "h2_html": "Height, access<br><em>and a photo.</em>",
                "bullets": [
                    "The town and the estate or road",
                    "Floors, or the number of balconies to be washed",
                    "Who can grant roof or balcony access",
                    "Whether water is available on that level",
                    "Photos of the parapet from the ground and, if you have them, from the balcony",
                ],
                "paragraphs": [
                    "Include these details so the quote is for the right building.",
                    "Parapet cleaning prices depend on the area, the height and the access. We quote after those facts are clear. There is no flat national rate on this page.",
                    "If the building also needs an indoor office clean or a pest treatment, mention <a href=\"/office-cleaning/\">office cleaning</a> or <a href=\"/fumigation/\">fumigation</a> in the same message and we will separate the quotes.",
                ],
            },
        ],
        place_paragraphs=[
            "Parapet cleaning in Nairobi can be requested for the neighbourhoods on our <a href=\"/cleaning-services/nairobi/\">Nairobi page</a>, including Westlands, Kilimani, Lavington, Parklands, Kileleshwa, Karen, South B and Embakasi. The building address still has to be confirmed.",
            "Parapet cleaning services in Kenya outside Nairobi follow the same rule. Mombasa, Kisumu, Nakuru, Eldoret, Thika and the other town pages are the right place to name the town. Coastal salt and upcountry dust leave different marks, so the location matters to the quote.",
        ],
        steps=[
            ("Show us the building", "Photos, floors and the town are enough to start."),
            ("Agree access", "We confirm who lets us onto the balcony or roof, and whether we can take the job."),
            ("Wash the parapet", "The visit happens only after the quote and the access are both accepted."),
        ],
        faqs=[
            ("What is parapet cleaning?", "It is the cleaning of parapet walls: the low walls at roof edges and balcony fronts, and often the exterior band around them. It is outside work, planned around safe access."),
            ("Do you offer parapet cleaning in Nairobi?", "Yes. Send the neighbourhood, the height and how the wall can be reached. We confirm the building before we book."),
            ("Do you work outside Nairobi?", "Enquiries from other Kenyan towns are welcome. Use the town pages below and write parapet cleaning as the service."),
            ("How much do parapet cleaning services cost?", "Height, area and access set the price. We quote the building you describe. This page has no fixed fee."),
            ("Can a resident book, or only a manager?", "Either person can enquire. Shared exterior walls often need the building's permission, and we will ask for that before the visit."),
            ("Is this a vacancy listing?", "No. This page is for requesting parapet cleaning. It does not advertise jobs."),
        ],
    ),
    _page(
        slug="house-cleaning",
        crumb="House cleaning",
        title="House Cleaning Services in Nairobi & Kenya | Cleaning Services Kenya",
        description="House cleaning services in Nairobi and across Kenya. Regular upkeep, deep cleaning and move-in or move-out cleans. Call or WhatsApp +254 706 855633.",
        eyebrow="HOUSE CLEANING",
        h1_html="House cleaning services<br><em>in Nairobi &amp; Kenya.</em>",
        slogan_html="Homes, apartments and rentals, cleaned to the brief you send.",
        lead="House cleaning, home cleaning and household cleaning all land here. Tell us the town, the number of bedrooms and whether you want a regular visit, a deep clean or a move-out.",
        image=IMG_HOME,
        image_alt="Cleaning team refreshing a modern apartment living room",
        schema_name="House cleaning",
        service_type="House cleaning",
        form_service="House cleaning",
        whatsapp_text="Hello Cleaning Services Kenya, I would like a house cleaning quote.",
        booking_intro="Bedrooms, bathrooms, town and the kind of clean are enough to start. Your message opens in WhatsApp. You can also call +254 706 855633.",
        cta_em="the house",
        sections=[
            {
                "id": "regular-cleaning",
                "eyebrow": "REGULAR HOUSE CLEANING",
                "h2_html": "A rhythm that<br><em>fits the household.</em>",
                "paragraphs": [
                    "Regular house cleaning is the weekly or fortnightly visit: kitchens, bathrooms, floors and the dusting you want kept up. You choose the rooms. A family home and a small apartment are quoted differently because the time is different.",
                    "Say whether anyone is usually home, and whether we should expect pets or a house help's routine we need to work around. Those details make the schedule honest.",
                ],
            },
            {
                "id": "deep-cleaning",
                "eyebrow": "DEEP CLEANING",
                "h2_html": "When the house needs<br><em>more than upkeep.</em>",
                "paragraphs": [
                    "A deep clean is a heavier reset. Bathrooms, kitchen grease, skirtings, fans and the corners a quick tidy misses. Ask us to include inside cupboards if that is what you want. We will only open storage you have asked us to open.",
                    "It suits a home before visitors, a place that has gone a long time between cleans, or a handover that needs more than a surface wipe. Deep cleaning is still a house-cleaning enquiry. Name it in the form so the quote matches.",
                    "If painters or builders have just left, say so. A post-construction clean, with dust, paint flecks and residue, is heavier than a lived-in deep clean and is quoted as its own job.",
                ],
            },
            {
                "id": "move-in-out",
                "eyebrow": "MOVE-IN AND MOVE-OUT",
                "h2_html": "A clear house<br><em>when the keys change.</em>",
                "paragraphs": [
                    "Landlords and tenants use move-in and move-out cleaning so an empty or nearly empty home is ready for the next person. Tell us the bedroom count, whether it is furnished, and the date the keys change.",
                    "Tile, terrazzo and wood floors are part of a house clean. Fitted carpets are better booked with <a href=\"/carpet-cleaning/\">carpet cleaning</a>, and fabric sofas with <a href=\"/sofa-cleaning/\">sofa cleaning</a>. Pests are a <a href=\"/fumigation/\">fumigation</a> enquiry. Mention them together if you want one conversation and separate lines on the quote.",
                    "How much house cleaning costs in Nairobi, or anywhere else we visit, depends on rooms, condition and the type of clean. Send those three and we reply with a figure. This page does not publish a price list.",
                ],
                "cards": [
                    ("Apartments", "Flats and maisonettes. The floor and the bedroom count are the details that matter."),
                    ("Family houses", "More rooms and outdoor shoes. Say if the compound or balcony is in scope."),
                    ("Rentals", "End-of-tenancy and start-of-tenancy cleans. Share the inspection date if you have one."),
                    ("After a renovation", "Dust and residue from building work, quoted separately from a standard deep clean."),
                ],
            },
        ],
        place_paragraphs=[
            "House cleaning services in Nairobi cover the neighbourhoods named on the <a href=\"/cleaning-services/nairobi/\">Nairobi page</a>: Westlands, Kilimani, Lavington, Karen, South B, Kileleshwa, Parklands and Embakasi. If you searched for house cleaning near you, write the estate as well as the city.",
            "The same house-cleaning enquiry is open for Mombasa, Kisumu, Nakuru, Eldoret, Thika, Ruiru and every other town linked below. <a href=\"/office-cleaning/\">Office cleaning</a> is the page to use when the property is a workplace rather than a home.",
        ],
        steps=[
            ("Tell us the house", "Town, bedrooms, bathrooms, and regular, deep or move-out."),
            ("We confirm and quote", "You hear whether that address can be served and what the clean will cost."),
            ("The team comes", "The visit follows the brief you agreed. Extra rooms are a new conversation, not a surprise add-on."),
        ],
        faqs=[
            ("Do you offer house cleaning services in Nairobi?", "Yes. Send the neighbourhood and the size of the home. We confirm the address before booking."),
            ("What is included in a regular clean?", "The rooms you name: typically kitchen, bathrooms, floors and dusting. Cupboards and inside the oven are included when you ask for them."),
            ("What is a deep clean?", "A heavier, one-off clean of the same home: grease, bathrooms, skirtings and the details a weekly visit does not always reach."),
            ("Do you do move-out cleaning?", "Yes. Tell us the key date, the bedroom count and whether the house is empty."),
            ("How much is house cleaning in Nairobi?", "The quote follows the number of rooms, the condition and the type of clean. Send those details. We do not list a flat house-cleaning price."),
            ("Can you clean tiles?", "Hard floors, including tile, are part of house cleaning. Fitted carpet is booked as carpet cleaning."),
        ],
    ),
    _page(
        slug="office-cleaning",
        crumb="Office cleaning",
        title="Office Cleaning Services in Nairobi & Kenya | Cleaning Services Kenya",
        description="Office cleaning services in Nairobi and across Kenya for offices, studios and shops. Regular or one-off. Call or WhatsApp +254 706 855633.",
        eyebrow="OFFICE CLEANING",
        h1_html="Office cleaning services<br><em>in Nairobi &amp; Kenya.</em>",
        slogan_html="Workplaces kept tidy around the hours you actually use them.",
        lead="Tell us the floor area, how many washrooms, and whether you want a daily clean, a few days a week, or a single visit. We confirm office cleaning around your working hours before anything is booked.",
        image=IMG_WORK,
        image_alt="Commercial cleaning staff at work",
        schema_name="Office cleaning",
        service_type="Office cleaning",
        form_service="Office cleaning",
        whatsapp_text="Hello Cleaning Services Kenya, I would like an office cleaning quote.",
        booking_intro="Share the town, the rough size and the days you want. The form opens WhatsApp with your enquiry ready to send. The phone line is +254 706 855633.",
        cta_em="the office",
        sections=[
            {
                "eyebrow": "WHAT AN OFFICE CLEAN COVERS",
                "h2_html": "Desks, washrooms<br><em>and the kitchenette.</em>",
                "paragraphs": [
                    "Office cleaning services in Nairobi are planned around the people in the building. A reception, workstations, meeting rooms, a kitchenette, washrooms and bins are the usual brief. Add or remove rooms when you write.",
                    "Carpeted floors can be part of the regular clean or a separate <a href=\"/carpet-cleaning/\">carpet cleaning</a> visit when the pile needs more than a vacuum. The exterior parapet of an office block is <a href=\"/parapet-cleaning/\">parapet cleaning</a>. A pest problem in a kitchen or store is <a href=\"/fumigation/\">fumigation</a>. Name them if you want those quotes too.",
                    "Tell us if we should use products already kept on site or bring cleaning products. We confirm that when we quote, so the first visit is not a guess.",
                ],
                "cards": [
                    ("Daily or weekly", "A standing visit on the days you choose. Say the start time you prefer."),
                    ("One-off cleans", "Before a new tenant, after a stocktake, or when the office has fallen behind."),
                    ("Shops and studios", "Smaller commercial rooms, counters and washrooms. The same enquiry form covers them."),
                    ("After hours", "Share the evening or early morning window. We confirm whether that slot can be staffed."),
                ],
            },
            {
                "eyebrow": "A SCHEDULE THAT FITS",
                "h2_html": "Your hours,<br><em>then our reply.</em>",
                "paragraphs": [
                    "Some offices want the clean finished before staff arrive. Others want it after closing. Write the window you have in mind. We only agree a time we can actually keep.",
                    "Office cleaning prices follow the floor area, the number of washrooms and how many visits you want each week. A shop with one room is a different quote from a full floor. Send the size and the frequency. There is no printed tariff here.",
                    "A home office inside a house is usually <a href=\"/house-cleaning/\">house cleaning</a>. Use this page when the space is a workplace with its own entrance, staff or customers.",
                ],
            },
        ],
        place_paragraphs=[
            "For office cleaning in Nairobi, name the neighbourhood. Our <a href=\"/cleaning-services/nairobi/\">Nairobi page</a> already lists Westlands, Kilimani, Lavington, Parklands, Kileleshwa, Karen, South B and Embakasi. Other estates are fine to ask about.",
            "Office cleaning in Mombasa, Kisumu, Nakuru, Eldoret, Thika and the rest of the town list works the same way. Open the town page or write the town in the form so the reply is about the right place.",
        ],
        steps=[
            ("Describe the workplace", "Area, washrooms, town and how often you want the clean."),
            ("We confirm the slot", "You get a quote and a yes or no on the hours you asked for."),
            ("The clean starts", "The first visit follows that brief. A change of days is agreed, not assumed."),
        ],
        faqs=[
            ("Do you offer office cleaning services in Nairobi?", "Yes. Send the neighbourhood, the size and how often you want a visit. We confirm the address and the timing."),
            ("Can you clean before we open or after we close?", "Share the hours you want. We accept the slot only when we can staff it."),
            ("Do you clean shops and small offices?", "Yes. Counters, floors and washrooms in a small commercial space are a normal brief."),
            ("Do you bring cleaning products?", "Tell us your preference. We confirm in the quote whether products come with us or are already on site."),
            ("How much do office cleaning services cost?", "Floor area, washrooms and visits per week set the price. Send those details for a quote."),
            ("Can the same team clean the parapet outside?", "Exterior parapet cleaning is quoted separately. Mention it if the building needs both."),
        ],
    ),
]


def service_paths():
    return [page["path"] for page in PAGES]


def write_service_pages(base_dir: Path) -> int:
    for page in PAGES:
        dest = base_dir / page["slug"] / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render_service(page), encoding="utf-8")
    return len(PAGES)
