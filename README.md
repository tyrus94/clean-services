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
SITE_URL=https://www.yourdomain.co.ke python generate_pages.py   # adds canonical tags + sitemap.xml
```

### Making each page different
Each page picks its own intro, headings, meta text, FAQs and "local needs" cards from pools of variants (stable between runs). That reduces duplication, but the real fix is real local detail: fill in `town_profiles.json` per town (`type`: city, commuter, coastal, tourism, border or market; `areas`: neighbourhoods you genuinely serve; `note`: one true sentence about the town). Only fill what your team can verify.

### Testimonials
Add real testimonials to `testimonials.csv` (columns: name, town, service, rating, date, text). Town pages show that town's testimonials first. The homepage shows a selection and `/testimonials/` lists all with a "Show more" button. With no rows the section is hidden. Only use testimonials from real customers with their permission; do not add review/rating schema markup for your own business reviews.

**SEO quality note:** confirm operational coverage before indexing each page and avoid implying an office or presence that does not exist.
