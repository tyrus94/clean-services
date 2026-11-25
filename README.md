# Cleaning Services Kenya website

A responsive static website built with HTML, CSS and JavaScript.

## Run locally
Open `index.html` in your browser.

## Deploy to Netlify
1. Extract this ZIP.
2. Open Netlify and choose **Add new site** > **Deploy manually**.
3. Drag the extracted `cleaning-services-kenya` folder (or its contents) into the deploy area.
4. Your site will be published.

No build command is required. Publish directory: `.`

## Contact integration
The website uses:
- Phone: `tel:+254706855633`
- WhatsApp: `https://wa.me/254706855633`

The booking form opens WhatsApp with the visitor's enquiry pre-filled. The visitor still needs to press Send in WhatsApp.

## Before going live
- Confirm that +254 706 855633 is the correct business number and that its WhatsApp account is active.
- Replace stock photography if you have your own team and cleaning photos.
- Add verified testimonials, exact service areas, business hours and any pricing details.
- Test phone and WhatsApp links on a mobile device.

## Website image assets

The four main image areas now use images from the repository Assets folder:

- Hero image: https://raw.githubusercontent.com/zoneislaced/Cleaning-Services-Kenya/refs/heads/main/Assets/portrait-of-happy-female-janitor-cleaning-floor.webp
- Residential service card: https://raw.githubusercontent.com/zoneislaced/Cleaning-Services-Kenya/refs/heads/main/Assets/stock-photo-professional-cleaning-service-team-cleans-living-room-in-modern-apartment.webp
- Commercial service card: https://raw.githubusercontent.com/zoneislaced/Cleaning-Services-Kenya/refs/heads/main/Assets/african-commercial-janitor-cleaning-staff.webp
- About section: https://raw.githubusercontent.com/zoneislaced/Cleaning-Services-Kenya/refs/heads/main/Assets/depositphotos_390354242-stock-photo-positive-multiethnic-cleaners-holding-mop.webp


## Managing the website images

The four main website images are now regular HTML `<img>` elements in `index.html` (hero, residential service, commercial service, and about section). To replace one, update the image URL in that element’s `src` attribute. The image sizing and cropping remain controlled in `styles.css`. The images are not inserted by JavaScript.


## Programmatic SEO town pages

Files: `towns.csv` (towns), `town_profiles.json` (real local details per town), `testimonials.csv` (real client testimonials), `town-template.html`, `generate_pages.py`, `vercel.json`.

Pages are generated at `/cleaning-services/<town>/` (directory at `/cleaning-services/`). `vercel.json` 301-redirects the old `/towns/...` URLs. Delete any old `towns` folder from the project.

### Generate pages
```bash
python generate_pages.py
```

Canonical URLs, Open Graph tags, `sitemap.xml` and `robots.txt` use `https://www.cleaningserviceskenya.co.ke` unless you override `SITE_URL`. The script also writes the service pages at `/fumigation/`, `/carpet-cleaning/`, `/sofa-cleaning/`, `/parapet-cleaning/`, `/house-cleaning/` and `/office-cleaning/`.

`vercel.json` sets `trailingSlash: true`, so `/fumigation` redirects to `/fumigation/`. Paths with a file extension, including `/sitemap.xml` and `/robots.txt`, are left as they are.

This is a service-area business: cleaning happens at the customer's property, and the only contact details are the phone number and WhatsApp. Do not add a street address, geo coordinates, or opening hours. Do not invent prices or review stars. HTML comments marked `TODO(owner)` are the remaining facts (prices, a logo, and social profiles).

### Making each page different
Each page picks its own intro, headings, meta text, FAQs and "local needs" cards from pools of variants (stable between runs). That reduces duplication, but the real fix is real local detail: fill in `town_profiles.json` per town (`type`: city, commuter, coastal, tourism, border or market; `areas`: neighbourhoods you genuinely serve; `note`: one true sentence about the town). Only fill what your team can verify.

### Testimonials
`testimonials.csv` (columns: name, town, service, rating, date, text; comma- or tab-separated) feeds every page. A town page shows that town's testimonials first, then ones from nearby towns, so all 84 pages have a testimonials section. The homepage shows a selection and `/testimonials/` lists all of them with a "Show more" button. Only publish testimonials from real customers, and do not add star-rating schema markup for your own business reviews.

**SEO quality note:** confirm operational coverage before indexing each page and avoid implying an office or presence that does not exist.
