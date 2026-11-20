"""Build ldrservice.com as a static multi-page site.

    python3 _src/build.py

Writes real HTML files to the repo root (served by GitHub Pages).
Edit page copy in _src/content.py, layout here, styles in _src/site.css.
"""
import html, json, pathlib, re, shutil, datetime
from content import BIZ, SERVICES, SERVICE_BY_SLUG, AREAS, AREAS_SHORT, GUIDES, GENERAL_FAQS

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "_src"
LEG = SRC / "legacy" / "pages"
SITE = BIZ["url"]
TODAY = datetime.date.today().isoformat()

# ---- integration settings (edit here, then rebuild) -----------------------
CONFIG = {
    # Lead destination (Leaders Hub URL, key, email backup) is NOT set here.
    # It lives in /lead-config.js at the repo root, read by the browser at runtime,
    # so switching Dev -> Live is a one-word edit with no rebuild.
    # Google Analytics 4 measurement id, e.g. "G-XXXXXXX". Empty = no analytics.
    "ga4": "",
    "phone": BIZ["phone"], "email": BIZ["email"],
}

LEGACY_ROUTES = {  # old #/hash routes -> new paths
    "": "/", "home": "/", "divisions": "/about/", "home-services": "/residential/",
    "mechanical-services": "/commercial/", "services": "/services/", "care": "/maintenance-program/",
    "technology": "/technology/", "contact": "/contact/", "privacy-policy": "/privacy-policy/",
    "sms-terms": "/sms-terms/", "terms": "/terms/",
}
CONFIG["legacyRoutes"] = LEGACY_ROUTES

e = html.escape
SITEMAP = []
BUSINESS_ID = SITE + "/#business"

def svc_url(s): return f"/{s['book']}/{s['slug']}/"
def area_url(a): return f"/service-areas/{a['slug']}/"
def guide_url(g): return f"/guides/{g['slug']}/"

# ---------------------------------------------------------------------------
# schema
# ---------------------------------------------------------------------------
def business_schema():
    return {
        "@type": ["HVACBusiness", "Plumber"], "@id": BUSINESS_ID,
        "name": BIZ["name"], "legalName": BIZ["legal"], "url": SITE + "/",
        "telephone": BIZ["tel"], "email": BIZ["email"],
        "logo": SITE + "/assets/img/logo.png", "image": SITE + "/assets/img/og.jpg",
        "slogan": "Leading you in the right direction",
        "description": "Residential and commercial mechanical services in Vaughan and the Greater Toronto Area: plumbing, heating, boilers, air conditioning, hydronics, drains, water filtration, backflow testing, flood response and preventative maintenance programs.",
        "address": {"@type": "PostalAddress", "streetAddress": BIZ["street"], "addressLocality": BIZ["city"],
                    "addressRegion": BIZ["region"], "postalCode": BIZ["postal"], "addressCountry": "CA"},
        "geo": {"@type": "GeoCoordinates", "latitude": BIZ["lat"], "longitude": BIZ["lng"]},
        "areaServed": [{"@type": "City", "name": n} for n in AREAS_SHORT] + [{"@type": "AdministrativeArea", "name": "Greater Toronto Area"}],
        "openingHoursSpecification": [{"@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"], "opens": "00:00", "closes": "23:59"}],
        "priceRange": "$$",
        "parentOrganization": {"@type": "Organization", "name": "Leader Mechanical"},
        "knowsAbout": ["Boiler service", "Furnace repair", "Air conditioning", "Plumbing", "Hydronic radiant heating",
                       "Snowmelt systems", "Tankless water heaters", "Drain cleaning", "Backflow testing",
                       "Sump pumps", "Backwater valves", "Water softeners", "Commercial HVAC", "Preventative maintenance"],
        "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Mechanical services", "itemListElement": [
            {"@type": "Offer", "itemOffered": {"@type": "Service", "name": s["short"], "url": SITE + svc_url(s)}} for s in SERVICES]},
    }

def crumbs_schema(trail):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(trail)]}

def faq_schema(faqs):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}

def ld(*objs):
    graph = {"@context": "https://schema.org", "@graph": [o for o in objs if o]}
    return '<script type="application/ld+json">' + json.dumps(graph, ensure_ascii=False).replace("</", "<\\/") + "</script>"

# ---------------------------------------------------------------------------
# chrome
# ---------------------------------------------------------------------------
ICON_PHONE = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M4 4h4l2 5-3 2c1 3 3 5 6 6l2-3 5 2v4c0 1-1 2-2 2A16 16 0 013 6c0-1 1-2 2-2z"></path></svg>'
ICON_MAIL = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="1.5"></rect><path d="M4 6l8 6 8-6"></path></svg>'
SPRITE = '''<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
  <linearGradient id="lgmark" x1="0" y1="18" x2="0" y2="211" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#3E86DE"></stop><stop offset="1" stop-color="#123C86"></stop></linearGradient>
  <symbol id="mark" viewBox="8 10 190 208">
    <polygon points="159,18 185,18 44,210 16,210" fill="url(#lgmark)"></polygon>
    <polygon points="108,18 134,18 47,140 19,141" fill="url(#lgmark)"></polygon>
    <polygon points="151,94 176,93 95,208 66,211" fill="url(#lgmark)"></polygon>
  </symbol></defs></svg>'''

NAV = [("Residential", "/residential/"), ("Commercial", "/commercial/"), ("Maintenance Program", "/maintenance-program/"),
       ("Service Areas", "/service-areas/"), ("About", "/about/")]

def header(path):
    def cur(u): return " current" if u != "/" and path.startswith(u) else ""
    links = "".join(f'<a class="nlink{cur(u)}" href="{u}">{n}</a>' for n, u in NAV)
    mlinks = '<a href="/">Home</a>' + "".join(f'<a href="{u}">{n}</a>' for n, u in NAV) + \
             '<a href="/services/">All Services</a><a href="/faq/">FAQ</a><a href="/contact/">Book Service</a>'
    return f'''<a href="#main" class="skip-link">Skip to content</a>
{SPRITE}
<header class="nav" id="nav">
  <div class="bar">
    <a class="brand" href="/" aria-label="Leader Service home">
      <svg class="mark" aria-hidden="true"><use href="#mark"></use></svg>
      <span><span class="logo-word">LEADER</span><span class="logo-sub"><i></i>SERVICE<i></i></span></span>
    </a>
    <nav class="links" aria-label="Main">{links}</nav>
    <div class="nav-right">
      <a href="tel:{BIZ['tel']}" class="navphone" data-loc="header">{BIZ['phone']}</a>
      <a class="btn btn-line" href="/contact/">Book Service</a>
      <button class="burger" id="burger" aria-label="Menu"><span></span><span></span><span></span></button>
    </div>
  </div>
</header>
<div class="mobile-menu" id="mobileMenu">{mlinks}<a href="tel:{BIZ['tel']}" class="mphone">{BIZ['phone']}</a></div>'''

def footer():
    res = "".join(f'<a href="{svc_url(s)}">{e(s["short"])}</a>' for s in SERVICES if s["book"] == "residential")
    com = "".join(f'<a href="{svc_url(s)}">{e(s["short"])}</a>' for s in SERVICES if s["book"] == "commercial")
    areas = "".join(f'<a href="{area_url(a)}">{e(a["name"])}</a>' for a in AREAS)
    return f'''<footer>
  <div class="wrap">
    <div class="foot-grid wide">
      <div class="foot-brand">
        <a class="brand" href="/">
          <svg class="mark" aria-hidden="true"><use href="#mark"></use></svg>
          <span><span class="logo-word" style="color:#fff">LEADER</span><span class="logo-sub" style="color:#8fa9c9"><i></i>SERVICE<i></i></span></span>
        </a>
        <p>Residential and commercial mechanical service for homes and buildings across Vaughan and the Greater Toronto Area. Backed by three generations of Leader Mechanical.</p>
        <address class="foot-addr">{e(BIZ['legal'])}<br>{e(BIZ['street'])}<br>{BIZ['city']}, {BIZ['region']} {BIZ['postal']}<br><a href="tel:{BIZ['tel']}">{BIZ['phone']}</a> · <a href="mailto:{BIZ['email']}">{BIZ['email']}</a><br>Open 24/7 for emergencies</address>
      </div>
      <div><h4>Residential</h4>{res}</div>
      <div><h4>Commercial</h4>{com}<h4 style="margin-top:22px">Company</h4><a href="/about/">About</a><a href="/maintenance-program/">Maintenance Program</a><a href="/technology/">Technology</a><a href="/guides/">Guides</a><a href="/faq/">FAQ</a><a href="/contact/">Book a Service Call</a></div>
      <div><h4>Service Areas</h4>{areas}<a href="/service-areas/">All service areas</a></div>
    </div>
    <div class="foot-bottom">
      <span class="line">BUILT ON TRUST · POWERED BY TECHNOLOGY · DRIVEN BY PURPOSE</span>
      <small>© {datetime.date.today().year} {e(BIZ['legal'])}. All rights reserved.</small><div class="foot-legal" style="margin-top:10px;display:flex;gap:18px;flex-wrap:wrap"><a href="/privacy-policy/" style="color:inherit;opacity:.82;text-decoration:underline">Privacy Policy</a><a href="/sms-terms/" style="color:inherit;opacity:.82;text-decoration:underline">SMS Terms &amp; Conditions</a><a href="/terms/" style="color:inherit;opacity:.82;text-decoration:underline">Terms of Use</a></div>
    </div>
  </div>
</footer>
<div class="mbar" role="navigation" aria-label="Quick actions"><a class="call" href="tel:{BIZ['tel']}" data-loc="mobile-bar">{ICON_PHONE} Call now</a><a class="bk" href="#book">Book online</a></div>'''

CONSENT = (SRC / "consent.html").read_text(encoding="utf-8")
CONSENT = (CONSENT.replace('href="#/privacy-policy" data-nav="privacy-policy"', 'href="/privacy-policy/"')
                  .replace('href="#/sms-terms" data-nav="sms-terms"', 'href="/sms-terms/"'))
assert 'href="/privacy-policy/"' in CONSENT and 'href="/sms-terms/"' in CONSENT

SERVICE_OPTIONS = ["Heating — furnace or boiler", "Air conditioning or heat pump", "Plumbing", "Water heater / tankless",
    "Drain cleaning or backup", "Sump pump / backwater valve", "Water filtration / softener", "Radiant heat / snowmelt",
    "Emergency flood response", "Maintenance program walkthrough", "Commercial HVAC", "Commercial backflow testing",
    "Commercial boilers", "Commercial plumbing", "Commercial maintenance program", "Not sure — help me"]

def lead_form(preselect=None):
    opts = "".join(f'<option{" selected" if o == preselect else ""}>{e(o)}</option>' for o in SERVICE_OPTIONS)
    return f'''<form class="book lead-form" id="bookForm" novalidate>
          <div class="book-steps"><span class="steplab">Booking · Step <span class="stepNum">1</span> of 3</span><span class="track"><svg class="progmark" viewBox="8 10 190 208" aria-hidden="true"><polygon class="ps" points="108,18 134,18 47,140 19,141"></polygon><polygon class="ps" points="159,18 185,18 44,210 16,210"></polygon><polygon class="ps" points="151,94 176,93 95,208 66,211"></polygon></svg></span></div>
          <div class="frow">
            <div class="field"><label for="fn">Full Name</label><input id="fn" name="name" autocomplete="name" placeholder="Jane Smith" required></div>
            <div class="field"><label for="ph">Phone</label><input id="ph" name="phone" type="tel" autocomplete="tel" placeholder="(905) 555-0123" required></div>
          </div>
          <div class="field"><label for="em">Email <span style="opacity:.6">(optional)</span></label><input id="em" name="email" type="email" autocomplete="email" placeholder="jane@email.com"></div>
          <div class="field"><label for="addr">Street Address</label><input id="addr" name="address" autocomplete="address-line1" placeholder="123 Main St"></div>
          <div class="frow">
            <div class="field"><label for="city">City</label><input id="city" name="city" autocomplete="address-level2" placeholder="Vaughan"></div>
            <div class="field"><label for="pc">Postal Code</label><input id="pc" name="postal_code" autocomplete="postal-code" placeholder="L4K 4X2" maxlength="7"></div>
          </div>
          <div class="frow">
            <div class="field"><label for="svc">Service Needed</label><select id="svc" name="service">{opts}</select></div>
            <div class="field"><label for="urg">Urgency</label><select id="urg" name="urgency"><option>Standard</option><option>Same-day</option><option>Emergency (24/7)</option></select></div>
          </div>
          <div class="emerg-note" hidden><b>Emergency?</b> Call <a href="tel:{BIZ['tel']}" data-loc="emergency-note">{BIZ['phone']}</a> now for the fastest response. You can still send this request too.</div>
          <div class="field"><label for="msg">What's happening? <span style="opacity:.6">(optional)</span></label><input id="msg" name="message" placeholder="e.g. no heat upstairs, boiler showing an error"></div>
          <div class="hp" aria-hidden="true"><label>Leave blank<input name="website" tabindex="-1" autocomplete="off"></label></div>
          {CONSENT}<button type="submit" class="btn btn-solid">Request my service call</button>
          <div class="formmsg" role="status" aria-live="polite"></div>
          <div class="book-note">By submitting you agree to be contacted about your request. We never share your information. See our <a href="/privacy-policy/">Privacy Policy</a>.</div>
        </form>'''

def book_band(heading="Book a service call", sub="Same-day and 24/7 emergency service across Vaughan and the Greater Toronto Area. Tell us what's happening — a coordinator calls you back to confirm.", preselect=None):
    return f'''<section class="book-band" id="book">
      <div class="wrap contact-grid">
        <div class="contact-copy">
          <span class="kicker light">Book A Service Call</span>
          <h2>{e(heading)}</h2>
          <p class="lead">{e(sub)}</p>
          <a href="tel:{BIZ['tel']}" class="bookphone" data-loc="book-band"><span class="pi">{ICON_PHONE}</span>{BIZ['phone']}</a>
          <a href="mailto:{BIZ['email']}" class="bookmail"><span class="pi">{ICON_MAIL}</span>{BIZ['email']}</a>
          <div class="contact-meta">Based at 132 Corstate Ave, Concord · Serving Vaughan &amp; the GTA · 24/7 emergency</div>
        </div>
        {lead_form(preselect)}
      </div>
    </section>'''

TRUST = '''<div class="trust">
  <div><b>3 generations</b><span>Backed by Leader Mechanical</span></div>
  <div><b>24/7</b><span>Emergency response</span></div>
  <div><b>Price first</b><span>Approved before work begins</span></div>
  <div><b>Every visit documented</b><span>Digital service record</span></div>
</div>'''

def _trim(d):
    if len(d) <= 158: return d
    cut = d[:156]
    for sep in [". ", ", "]:
        i = cut.rfind(sep)
        if i > 100: return cut[:i + 1].rstrip(",") if sep == ". " else cut[:i] + "."
    return cut.rsplit(" ", 1)[0] + "…"

def page(path, title, desc, body, schema="", is_home=False, og_type="website", extra_head="", priority="0.7"):
    canon = SITE + path
    desc = _trim(desc)
    cfg = json.dumps(CONFIG)
    ga = ""
    if CONFIG["ga4"]:
        ga = f'<script async src="https://www.googletagmanager.com/gtag/js?id={CONFIG["ga4"]}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","{CONFIG["ga4"]}");</script>'
    doc = f'''<!doctype html>
<html lang="en-CA"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canon}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="Leader Service"><meta property="og:locale" content="en_CA">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canon}">
<meta property="og:image" content="{SITE}/assets/img/og.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(desc)}"><meta name="twitter:image" content="{SITE}/assets/img/og.jpg">
<meta name="geo.region" content="CA-ON"><meta name="geo.placename" content="Vaughan">
<meta name="theme-color" content="#0A1C33">
<link rel="icon" type="image/svg+xml" href="/favicon.svg"><link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png"><link rel="apple-touch-icon" sizes="180x180" href="/favicon-180.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800&family=Inter:wght@400;500;600&family=Fraunces:opsz,wght@9..144,400;9..144,600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/site.css?v={VER}">
{extra_head}{ga}<script>window.LS_CONFIG={cfg};</script>
{ld(business_schema() if is_home else {"@type": ["HVACBusiness","Plumber"], "@id": BUSINESS_ID, "name": BIZ["name"], "url": SITE + "/", "telephone": BIZ["tel"]}, *(schema if isinstance(schema, (list, tuple)) else [schema]))}
</head>
<body class="{'is-home' if is_home else 'inner'}">
{header(path)}
<main id="main"><div class="page active" data-page="{'home' if is_home else 'inner'}">
{body}
</div></main>
{footer()}
<script src="/assets/js/site.js?v={VER}" defer></script>
{'<script src="/assets/js/cine.js?v=' + VER + '" defer></script>' if is_home else ''}
</body></html>
'''
    out = ROOT / path.strip("/") / "index.html" if path != "/" else ROOT / "index.html"
    if path.endswith(".html"): out = ROOT / path.strip("/")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    if not path.endswith("404.html"):
        SITEMAP.append((canon, priority))

# ---------------------------------------------------------------------------
# helpers for legacy fragments
# ---------------------------------------------------------------------------
def legacy(name):
    s = (LEG / f"{name}.html").read_text(encoding="utf-8")
    def fix(m):
        attrs, target = m.group(1) + m.group(3), m.group(2)
        scroll = re.search(r'\sdata-scroll="([^"]+)"', attrs)
        attrs = re.sub(r'\sdata-scroll="[^"]+"', "", attrs)
        url = LEGACY_ROUTES.get(target, "/")
        if scroll: url = url.rstrip("/") + "/" + scroll.group(1) if url != "/" else "/" + scroll.group(1)
        return f'<a{attrs} href="{url}"'
    s = re.sub(r'<a([^>]*?)\sdata-nav="([^"]+)"([^>]*?)(?=>)', lambda m: fix(m) , s)
    s = s.replace('href="#/privacy-policy"', 'href="/privacy-policy/"').replace('href="#/sms-terms"', 'href="/sms-terms/"')
    s = re.sub(r'(<a[^>]*?) href="[^"]*"([^>]*? href=)', r"\1\2", s)  # drop duplicate href if one existed
    return s

def crumb_html(trail):
    parts = []
    for i, (n, u) in enumerate(trail):
        if i: parts.append('<span aria-hidden="true">/</span>')
        parts.append(f'<a href="{u}">{e(n)}</a>' if i < len(trail) - 1 else f'<span>{e(n)}</span>')
    return '<nav class="crumbs" aria-label="Breadcrumb">' + "".join(parts) + "</nav>"

def hero(trail, label, h1, lead, answer=None, cta=True):
    ans = f'<div class="answer"><span class="alabel">The short answer</span><p>{e(answer)}</p></div>' if answer else ""
    acts = f'<div class="hero-actions"><a class="btn btn-solid" href="#book">Book a service call</a><a class="btn btn-line" href="tel:{BIZ["tel"]}" data-loc="hero">Call {BIZ["phone"]}</a></div>' if cta else ""
    return f'''<section class="dhero"><div class="wrap">{crumb_html(trail)}<div class="dlabel">{e(label)}</div><h1>{e(h1)}</h1><p>{e(lead)}</p>{ans}{acts}</div></section>'''

def faq_html(faqs, heading="Frequently asked questions"):
    items = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in faqs)
    return f'<section class="block"><div class="wrap"><div class="head"><span class="kicker">FAQ</span><h2>{e(heading)}</h2></div><div class="faq">{items}</div></div></section>'

def link_grid(items):
    return '<div class="link-grid">' + "".join(f'<a href="{u}"><b>{e(t)}</b><span>{e(d)}</span></a>' for t, u, d in items) + "</div>"

def svc_card(s): return (s["short"], svc_url(s), s["tag"])

# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------
def build_home():
    frag = legacy("home")
    intro = f'''<section class="home-intro"><div class="wrap">
      <span class="kicker">Vaughan · Kleinburg · Woodbridge · King · Richmond Hill · Toronto</span>
      <h1>Plumbing, heating &amp; mechanical service for homes and buildings across Vaughan and the GTA</h1>
      <p class="lead">Leader Service maintains and repairs the systems that keep a property running: boilers and furnaces, air conditioning, radiant heat and snowmelt, plumbing, water heaters, drains, water treatment and backflow compliance. Residential and commercial, from our base in Concord, with 24/7 emergency response.</p>
      <div class="chips">{"".join(f'<a href="{svc_url(s)}">{e(s["short"])}</a>' for s in SERVICES)}</div>
      <div style="margin-top:44px">{TRUST}</div>
    </div></section>'''
    # place the intro right after the hero stat strip / before approach
    marker = '<section id="approachSec"'
    i = frag.find(marker)
    if i < 0:
        i = frag.find("approachSec"); i = frag.rfind("<section", 0, i)
    frag = frag[:i] + intro + frag[i:]
    areas = link_grid([(a["name"], area_url(a), a["intro"][:110].rsplit(" ", 1)[0] + "…") for a in AREAS[:6]])
    frag += f'''<section class="block mist"><div class="wrap"><div class="head"><span class="kicker">Service Areas</span><h2>Local to Vaughan. Working across the GTA.</h2><p class="lead">Our trucks leave 132 Corstate Avenue in Concord every morning.</p></div>{areas}<p style="margin-top:22px"><a class="arrow-link" href="/service-areas/">See every area we serve →</a></p></div></section>'''
    frag += faq_html(GENERAL_FAQS[:6], "Questions homeowners and property managers ask")
    frag += book_band()
    page("/", "Leader Service | Plumbing, Heating & HVAC in Vaughan",
         "Residential and commercial plumbing, heating, boilers, air conditioning, radiant heat, drains, water treatment and backflow testing in Vaughan, Kleinburg, Woodbridge, King and the GTA. 24/7 emergency service.",
         frag, [faq_schema(GENERAL_FAQS[:6]), {"@type": "WebSite", "@id": SITE + "/#website", "url": SITE + "/", "name": "Leader Service", "publisher": {"@id": BUSINESS_ID}}],
         is_home=True, priority="1.0",
         extra_head='<link rel="preload" as="image" href="/poster.jpg">')

def book_section_replace(frag):
    """swap a legacy booking form for the shared lead form"""
    i = frag.find('<form class="book'); j = frag.find("</form>", i) + 7
    return frag[:i] + lead_form() + frag[j:] if i >= 0 else frag

def build_legacy_pages():
    # About (former Divisions) with heritage lead-in
    heritage = '''<section class="block"><div class="wrap"><div class="prose">
      <span class="kicker">About Leader Service</span>
      <h2>Three generations installing it. Now a company dedicated to keeping it running.</h2>
      <p>For three generations, Leader Mechanical has installed the heating, plumbing and mechanical systems inside custom homes and commercial buildings across the Greater Toronto Area. Leader Service is the part of the Leader family built for what comes after installation: maintaining, repairing and documenting those systems for the life of the property.</p>
      <p>We work from 132 Corstate Avenue in Concord, Vaughan, with two divisions: <a href="/residential/">Leader Home Services</a> for houses and estates, and <a href="/commercial/">Leader Mechanical Services</a> for commercial, industrial and multi-residential buildings.</p>
    </div></div></section>'''
    frag = legacy("divisions").replace("<h2", "<h1", 1).replace("</h2>", "</h1>", 1)
    page("/about/", "About Leader Service | Vaughan Mechanical Service",
         "Leader Service is the residential and commercial service company of the Leader family, backed by three generations of Leader Mechanical. Based in Concord, Vaughan.",
         frag + heritage + book_band(), crumbs_schema([("Home", "/"), ("About", "/about/")]))

    for name, path, title, desc, book in [
        ("home-services", "/residential/", "Home Plumbing, Heating & AC Vaughan | Leader Service",
         "Leader Home Services: plumbing, heating, boilers, air conditioning, hydronics and maintenance for homes, custom homes and estates across Vaughan and the GTA.", "residential"),
        ("mechanical-services", "/commercial/", "Commercial Mechanical Service GTA | Leader Service",
         "Leader Mechanical Services: commercial HVAC, plumbing, boilers, backflow testing and preventative maintenance for buildings across Vaughan, Concord and the GTA.", "commercial"),
    ]:
        frag = legacy(name)
        cards = link_grid([svc_card(s) for s in SERVICES if s["book"] == book])
        frag = re.sub(r'<section class="dcta"[\s\S]*?</section>', "", frag)
        frag += f'<section class="block mist"><div class="wrap"><div class="head"><span class="kicker">Services</span><h2>Explore {"home" if book=="residential" else "commercial"} services</h2></div>{cards}</div></section>'
        label = "Residential" if book == "residential" else "Commercial"
        page(path, title, desc, frag + book_band(), crumbs_schema([("Home", "/"), (label, path)]), priority="0.9")

    frag = legacy("services")
    frag = frag.replace("<h2", "<h1", 1).replace("</h2>", "</h1>", 1)
    allcards = (f'<section class="block mist"><div class="wrap"><div class="head"><span class="kicker">Residential</span><h2>Home services</h2></div>{link_grid([svc_card(s) for s in SERVICES if s["book"]=="residential"])}'
                f'<div class="head" style="margin-top:64px"><span class="kicker">Commercial</span><h2>Commercial services</h2></div>{link_grid([svc_card(s) for s in SERVICES if s["book"]=="commercial"])}</div></section>')
    page("/services/", "All Mechanical Services | Leader Service",
         "Every residential and commercial mechanical service Leader Service provides across Vaughan and the GTA: heating, cooling, plumbing, drains, water filtration, flood response, backflow and maintenance.",
         frag + allcards + book_band(), crumbs_schema([("Home", "/"), ("Services", "/services/")]), priority="0.8")

    frag = legacy("care").replace("<h2", "<h1", 1).replace("</h2>", "</h1>", 1)
    mfaqs = GENERAL_FAQS[4:9]
    page("/maintenance-program/", "Home & Building Maintenance Program | Leader Service",
         "One maintenance program for every mechanical system in your home or building: scoped from a walkthrough, priced on your actual systems, 10% repair discount, no truck charges. Vaughan and the GTA.",
         frag + faq_html(mfaqs, "Maintenance program questions") + book_band("Book a property walkthrough", "We walk the property, inventory every system, and send you a program priced on exactly what you have.", "Maintenance program walkthrough"),
         [crumbs_schema([("Home", "/"), ("Maintenance Program", "/maintenance-program/")]), faq_schema(mfaqs),
          {"@type": "Service", "name": "Leader Service Maintenance Program", "serviceType": "Preventative mechanical maintenance", "provider": {"@id": BUSINESS_ID},
           "areaServed": [{"@type": "City", "name": n} for n in AREAS_SHORT]}], priority="0.9")

    frag = legacy("technology").replace("<h2", "<h1", 1).replace("</h2>", "</h1>", 1)
    page("/technology/", "Technology | How Leader Service Works | Vaughan & GTA",
         "How Leader Service uses technology to get the right technician to your door faster, with your property's history in hand, prices approved up front and every visit documented.",
         frag + book_band(), crumbs_schema([("Home", "/"), ("Technology", "/technology/")]), priority="0.5")

    frag = book_section_replace(legacy("contact")).replace("<h2", "<h1", 1).replace("</h2>", "</h1>", 1)
    frag = frag.replace('<div class="contact-meta r d3">Serving Vaughan &amp; the GTA, Ontario</div>',
        f'<div class="contact-meta r d3">{e(BIZ["street"])}, {BIZ["city"]}, {BIZ["region"]} {BIZ["postal"]}<br>Serving Vaughan &amp; the GTA · Open 24/7 for emergencies</div>')
    frag = frag.replace("<section>", '<section id="book">', 1)
    page("/contact/", "Book a Service Call | Leader Service | 647.848.7526",
         "Book plumbing, heating, HVAC, drain or emergency service in Vaughan and the GTA. Call 647.848.7526 or book online; a coordinator calls back to confirm.",
         frag, [crumbs_schema([("Home", "/"), ("Contact", "/contact/")]), {"@type": "ContactPage", "url": SITE + "/contact/", "about": {"@id": BUSINESS_ID}}], priority="0.8")

    for name, path, title in [("privacy-policy", "/privacy-policy/", "Privacy Policy | Leader Service"),
                              ("sms-terms", "/sms-terms/", "SMS Terms & Conditions | Leader Service"),
                              ("terms", "/terms/", "Terms of Use | Leader Service")]:
        page(path, title, f"{title.split(' |')[0]} for ldrservice.com, operated by Leader Service Group Canada Inc.",
             legacy(name), crumbs_schema([("Home", "/"), (title.split(" |")[0], path)]), priority="0.2")

def build_services():
    for s in SERVICES:
        url = svc_url(s)
        label = "Residential" if s["book"] == "residential" else "Commercial"
        trail = [("Home", "/"), (label, f"/{s['book']}/"), (s["short"], url)]
        secs = "".join(f"<h2>{e(h)}</h2><p>{e(p)}</p>" for h, p in s["sections"])
        incl = "".join(f"<span>{e(x)}</span>" for x in s["includes"])
        areas = "".join(f'<a href="{area_url(a)}">{e(s["short"])} in {e(a["name"])}</a>' for a in AREAS if s["slug"] in a["featured"]) or \
                "".join(f'<a href="{area_url(a)}">{e(a["name"])}</a>' for a in AREAS)
        rel = link_grid([svc_card(SERVICE_BY_SLUG[r]) for r in s["related"]])
        body = hero(trail, label, s["h1"], s["tag"], s["answer"]) + f'''
<section class="block"><div class="wrap split">
  <div class="prose">{secs}
    <h2>Where we provide {e(s["short"].lower())}</h2><p>From our base in Concord we serve Vaughan, Woodbridge, Maple, Kleinburg, King City, Richmond Hill, Toronto and the surrounding GTA.</p><div class="chips">{areas}</div>
  </div>
  <aside class="aside-card"><h3>What's included</h3><div class="sd-includes">{incl}</div>
    <small>Call or text</small><a class="tel" href="tel:{BIZ['tel']}" data-loc="aside">{BIZ['phone']}</a><small>24/7 for emergencies</small>
    <a class="btn btn-solid" href="#book">Book online</a><a class="btn btn-line" href="/maintenance-program/">Add it to a maintenance program</a></aside>
</div></section>
<section class="block mist tight"><div class="wrap">{TRUST}</div></section>
{faq_html(s["faqs"])}
<section class="block mist"><div class="wrap"><div class="head"><span class="kicker">Related</span><h2>Related services</h2></div>{rel}</div></section>
{book_band("Book " + s["short"].lower(), preselect=None)}'''
        schema = [crumbs_schema(trail), faq_schema(s["faqs"]),
                  {"@type": "Service", "@id": SITE + url + "#service", "name": s["h1"], "serviceType": s["stype"], "description": s["answer"],
                   "url": SITE + url, "provider": {"@id": BUSINESS_ID},
                   "areaServed": [{"@type": "City", "name": n} for n in AREAS_SHORT],
                   "audience": {"@type": "Audience", "audienceType": "Homeowners" if s["book"] == "residential" else "Property managers and building owners"}}]
        page(url, s["title"], s["desc"], body, schema, priority="0.8")

def build_areas():
    for a in AREAS:
        url = area_url(a)
        trail = [("Home", "/"), ("Service Areas", "/service-areas/"), (a["name"], url)]
        secs = "".join(f"<h2>{e(h)}</h2><p>{e(p)}</p>" for h, p in a["local"])
        hoods = "".join(f"<span>{e(n)}</span>" for n in a["neighbourhoods"])
        feat = link_grid([(f'{SERVICE_BY_SLUG[k]["short"]} in {a["name"]}', svc_url(SERVICE_BY_SLUG[k]), SERVICE_BY_SLUG[k]["tag"]) for k in a["featured"]])
        others = "".join(f'<a href="{area_url(o)}">{e(o["name"])}</a>' for o in AREAS if o is not a)
        faqs = a["faqs"] + [(f"What services does Leader Service offer in {a['name']}?",
                 "Plumbing, furnace and boiler service, air conditioning and heat pumps, radiant heating and snowmelt, water heaters and tankless, drain cleaning, sump pumps and backwater valves, water filtration, flood response, commercial HVAC, backflow testing and preventative maintenance programs.")]
        body = hero(trail, "Service Area", f"Plumbing, heating & HVAC service in {a['name']}", a["intro"], a["answer"]) + f'''
<section class="block"><div class="wrap split">
  <div class="prose">{secs}<h2>Neighbourhoods we serve</h2><div class="chips">{hoods}</div></div>
  <aside class="aside-card"><h3>Service in {e(a["name"])}</h3><small>Call or text</small><a class="tel" href="tel:{BIZ['tel']}" data-loc="aside">{BIZ['phone']}</a><small>24/7 for emergencies</small><a class="btn btn-solid" href="#book">Book online</a></aside>
</div></section>
<section class="block mist"><div class="wrap"><div class="head"><span class="kicker">{e(a["name"])}</span><h2>Most-requested services in {e(a["name"])}</h2></div>{feat}<div class="chips" style="margin-top:30px"><b style="font-family:Montserrat;font-size:.84rem;padding:7px 4px">Also serving:</b>{others}</div></div></section>
{faq_html(faqs, f"{a['name']} service questions")}
{book_band(f"Book service in {a['name']}")}'''
        schema = [crumbs_schema(trail), faq_schema(faqs),
                  {"@type": "Service", "name": f"Mechanical services in {a['name']}", "serviceType": "Plumbing, heating, HVAC and mechanical service",
                   "provider": {"@id": BUSINESS_ID}, "areaServed": {"@type": "City", "name": a["name"], "containedInPlace": {"@type": "AdministrativeArea", "name": "Ontario"}}, "url": SITE + url}]
        page(url, a["title"], a["desc"], body, schema, priority="0.8")
    grid = link_grid([(a["name"], area_url(a), a["intro"][:120].rsplit(" ", 1)[0] + "…") for a in AREAS])
    page("/service-areas/", "Service Areas: Vaughan & the GTA | Leader Service",
         "Leader Service provides residential and commercial mechanical service across Vaughan, Woodbridge, Maple, Kleinburg, Concord, King City, Richmond Hill and Toronto.",
         hero([("Home", "/"), ("Service Areas", "/service-areas/")], "Service Areas", "Where we work",
              "From our base at 132 Corstate Avenue in Concord, we serve homes and buildings across Vaughan and the Greater Toronto Area.",
              "Leader Service serves Vaughan (Woodbridge, Maple, Kleinburg, Concord, Thornhill and Vellore), King City and King Township, Richmond Hill, Toronto and the surrounding Greater Toronto Area, for residential and commercial properties, with 24/7 emergency response.")
         + f'<section class="block"><div class="wrap">{grid}</div></section>' + book_band(),
         crumbs_schema([("Home", "/"), ("Service Areas", "/service-areas/")]), priority="0.8")

def build_guides():
    for g in GUIDES:
        url = guide_url(g)
        trail = [("Home", "/"), ("Guides", "/guides/"), (g["h1"], url)]
        secs = "".join(f"<h2>{e(h)}</h2>" + (p if p.lstrip().startswith("<") else f"<p>{e(p)}</p>") for h, p in g["sections"])
        src = ""
        if g.get("sources"):
            src = "<h2>Sources</h2><ul>" + "".join(f'<li><a href="{u}" rel="noopener" target="_blank">{e(t)}</a></li>' for t, u in g["sources"]) + "</ul>"
        rel = link_grid([svc_card(SERVICE_BY_SLUG[r]) for r in g["related"]])
        body = hero(trail, "Guide", g["h1"], "From the technicians at Leader Service.", g["answer"], cta=False) + f'''
<section class="block"><div class="wrap split"><article class="prose">{secs}{src}<p style="margin-top:36px;color:var(--gray);font-size:.9rem">Written by the Leader Service team · Updated {TODAY}</p></article>
<aside class="aside-card"><h3>Need it done?</h3><small>Call or text</small><a class="tel" href="tel:{BIZ['tel']}" data-loc="aside">{BIZ['phone']}</a><a class="btn btn-solid" href="#book">Book online</a></aside></div></section>
{faq_html(g["faqs"])}
<section class="block mist"><div class="wrap"><div class="head"><span class="kicker">Related</span><h2>Related services</h2></div>{rel}</div></section>
{book_band()}'''
        schema = [crumbs_schema(trail), faq_schema(g["faqs"]),
                  {"@type": "Article", "headline": g["h1"], "description": g["desc"], "datePublished": TODAY, "dateModified": TODAY,
                   "author": {"@id": BUSINESS_ID}, "publisher": {"@id": BUSINESS_ID}, "mainEntityOfPage": SITE + url,
                   "image": SITE + "/assets/img/og.jpg"}]
        page(url, g["title"], g["desc"], body, schema, og_type="article", priority="0.6")
    grid = link_grid([(g["h1"], guide_url(g), g["desc"][:120].rsplit(" ", 1)[0] + "…") for g in GUIDES])
    page("/guides/", "Homeowner & Property Manager Guides | Leader Service",
         "Plain-language guides to maintaining boilers, furnaces, plumbing and building systems in Ontario, from the technicians at Leader Service.",
         hero([("Home", "/"), ("Guides", "/guides/")], "Guides", "Guides", "Straight answers about the systems in your home or building.", cta=False)
         + f'<section class="block"><div class="wrap">{grid}</div></section>' + book_band(),
         crumbs_schema([("Home", "/"), ("Guides", "/guides/")]), priority="0.5")

def build_faq():
    page("/faq/", "Frequently Asked Questions | Leader Service, Vaughan & GTA",
         "Answers about Leader Service: areas served, 24/7 emergency service, the maintenance program, pricing, contract terms and booking.",
         hero([("Home", "/"), ("FAQ", "/faq/")], "FAQ", "Frequently asked questions", "Everything people ask us before they book.", cta=False)
         + faq_html(GENERAL_FAQS, "About Leader Service") + book_band(),
         [crumbs_schema([("Home", "/"), ("FAQ", "/faq/")]), faq_schema(GENERAL_FAQS)], priority="0.6")

def build_404():
    page("/404.html", "Page not found | Leader Service", "This page could not be found.",
         hero([("Home", "/"), ("Not found", "/404.html")], "404", "This page has moved", "The site has a new structure. Try one of these:", cta=False)
         + f'<section class="block"><div class="wrap">{link_grid([("Home", "/", "Start here"), ("Residential", "/residential/", "Home services"), ("Commercial", "/commercial/", "Building services"), ("Book service", "/contact/", "Call or book online"), ("Service areas", "/service-areas/", "Where we work"), ("FAQ", "/faq/", "Common questions")])}</div></section>')
    # 404 must not claim a canonical
    p = ROOT / "404.html"; p.write_text(p.read_text().replace('<link rel="canonical" href="https://ldrservice.com/404.html">', '').replace('content="index,follow,max-image-preview:large"', 'content="noindex"'))

# ---------------------------------------------------------------------------
def build_static():
    (ROOT / "assets/css").mkdir(parents=True, exist_ok=True)
    (ROOT / "assets/js").mkdir(parents=True, exist_ok=True)
    legacy_css = (ROOT / "assets/css/legacy.css").read_text(encoding="utf-8")
    legacy_css = re.sub(r"@import url\([^)]*\);", "", legacy_css)
    (ROOT / "assets/css/site.css").write_text(legacy_css + "\n" + (SRC / "site.css").read_text(), encoding="utf-8")
    shutil.copy(SRC / "site.js", ROOT / "assets/js/site.js")
    shutil.copy(SRC / "cine.js", ROOT / "assets/js/cine.js")

    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod><priority>{p}</priority></url>" for u, p in SITEMAP]
    sm.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(sm) + "\n")

    (ROOT / "robots.txt").write_text(f"""# ldrservice.com
User-agent: *
Allow: /
Disallow: /_src/

# AI search and assistant crawlers are welcome: we want to be cited.
User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: Applebot-Extended
Allow: /
User-agent: Bingbot
Allow: /

Sitemap: {SITE}/sitemap.xml
""")

    svc_lines = "\n".join(f"- [{s['short']}]({SITE}{svc_url(s)}): {s['answer']}" for s in SERVICES)
    area_lines = "\n".join(f"- [{a['name']}]({SITE}{area_url(a)})" for a in AREAS)
    guide_lines = "\n".join(f"- [{g['h1']}]({SITE}{guide_url(g)})" for g in GUIDES)
    faq_lines = "\n".join(f"- **{q}** {a}" for q, a in GENERAL_FAQS)
    (ROOT / "llms.txt").write_text(f"""# Leader Service

> Leader Service ({BIZ['legal']}) is a residential and commercial mechanical service company based at {BIZ['street']}, {BIZ['city']} (Vaughan), Ontario {BIZ['postal']}, Canada. It provides plumbing, heating, boiler, furnace, air conditioning, hydronic radiant and snowmelt, water heater, drain, sump pump and backwater valve, water filtration, flood response, commercial HVAC, backflow testing and preventative maintenance services across Vaughan and the Greater Toronto Area, with 24/7 emergency response. Phone {BIZ['phone']}, email {BIZ['email']}.

Key facts:
- Service area: {", ".join(AREAS_SHORT)} and the surrounding Greater Toronto Area, Ontario, Canada.
- Two divisions: Leader Home Services (residential, including custom and estate homes) and Leader Mechanical Services (commercial, industrial, institutional and multi-residential).
- Part of the Leader family of companies; Leader Mechanical has installed mechanical systems in the GTA for three generations.
- Maintenance program: one binary membership (no tiers), priced from a property walkthrough on the systems actually covered; 10% repair discount; no truck, call-out or fuel charges on program work; transfers on sale. Residential 12-month auto-renewing; commercial 12 or 36 months.
- Open 24/7 for emergencies.

## Services
{svc_lines}

## Service areas
{area_lines}

## Guides
{guide_lines}

## FAQ
{faq_lines}

## Contact
- [Book a service call]({SITE}/contact/)
""")

VER = datetime.datetime.now().strftime("%Y%m%d%H%M")

if __name__ == "__main__":
    build_home(); build_legacy_pages(); build_services(); build_areas(); build_guides(); build_faq(); build_404()
    build_static()
    print(f"built {len(SITEMAP)} pages")
