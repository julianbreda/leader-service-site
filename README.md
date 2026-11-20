# ldrservice.com

Static multi-page site for Leader Service, served by GitHub Pages from the `main` branch root.

## Edit and publish

1. Copy lives in `_src/content.py` (services, service areas, guides, FAQ). Layout is in `_src/build.py`, styles in `_src/site.css`, behaviour in `_src/site.js`.
2. Build: `python3 _src/build.py` (Python 3, no packages needed). It writes the HTML pages, `sitemap.xml`, `robots.txt` and `llms.txt` to the repo root.
3. Commit and push to `main`. GitHub Pages redeploys automatically.

Never hand-edit the generated `index.html` files; they are overwritten on every build.

## Integrations (in `CONFIG` at the top of `_src/build.py`)

- `leadEndpoint` / `leadKey`: Leaders Hub lead webhook. See `_src/LEADS-HUB-SPEC.md`.
- `web3formsKey`: optional email copy of every lead.
- `ga4`: Google Analytics 4 measurement ID. Lead submissions fire `generate_lead`; phone taps fire `click_to_call`.

## Other notes

- `_src/legacy/index.html` is the original single-file site, kept for reference. The hero video (`cine.mp4`) and the legal pages come from it.
- Old `ldrservice.com/#/page` links redirect to the new URLs.
- The SMS consent wording on the forms is the TCR-approved text. Don't change it without re-checking the 10DLC registration.
