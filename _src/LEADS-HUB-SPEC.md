# ldrservice.com → Leaders Hub: website lead intake

Every booking form on ldrservice.com (one on every page) sends the inquiry to the Leaders Hub as a new **lead**. This is the contract the Hub needs to accept.

## What the Hub needs to expose

`POST https://<public hub domain>/api/leads` (any path works; tell Julian the final URL)

- Must be **public HTTPS**. A `localhost` dev server cannot receive website leads. Use the deployed Hub domain, or a stable tunnel (Cloudflare Tunnel / ngrok reserved domain) while in dev.
- **CORS** (the browser calls it directly from ldrservice.com):
  - Answer `OPTIONS` preflight with `204`
  - `Access-Control-Allow-Origin: https://ldrservice.com` (also `https://www.ldrservice.com`)
  - `Access-Control-Allow-Methods: POST, OPTIONS`
  - `Access-Control-Allow-Headers: Content-Type, X-Lead-Key`
- Return any **2xx** on success. Anything else makes the site show "please call us" and, if configured, fall back to an email copy.

## Request

Headers: `Content-Type: application/json`, `X-Lead-Key: <shared value>`

The key is visible in the site's JavaScript, so it is a **spam filter, not a secret**. Also rate-limit by IP (e.g. 10/hour) and reject payloads where `website` honeypot logic or phone validation fails.

```json
{
  "source": "website",
  "site": "ldrservice.com",
  "submitted_at": "2026-11-20T17:26:48.071Z",
  "name": "Jane Smith",
  "phone": "905 555 0123",
  "email": "",
  "address": "12 Example Ct",
  "city": "Kleinburg",
  "postal_code": "L0J 1C0",
  "service": "Radiant heat / snowmelt",
  "urgency": "Standard | Same-day | Emergency (24/7)",
  "message": "free text, optional",
  "property_type": "residential | commercial",
  "page_url": "https://ldrservice.com/service-areas/kleinburg/",
  "page_title": "Kleinburg Boilers, Radiant & Snowmelt | Leader Service",
  "landing_page": "/residential/boiler-service/",
  "referrer": "https://www.google.com/",
  "attribution": {"utm_source": "google", "utm_medium": "cpc", "utm_campaign": "...", "gclid": "..."},
  "sms_consent": true,
  "sms_consent_text": "By checking this box, you agree to receive recurring text messages ...",
  "consent_disclosure_version": "2026-09-08-v2",
  "consent_timestamp": "2026-11-20T17:26:48.071Z"
}
```

`service` is one of: Heating — furnace or boiler · Air conditioning or heat pump · Plumbing · Water heater / tankless · Drain cleaning or backup · Sump pump / backwater valve · Water filtration / softener · Radiant heat / snowmelt · Emergency flood response · Maintenance program walkthrough · Commercial HVAC · Commercial backflow testing · Commercial boilers · Commercial plumbing · Commercial maintenance program · Not sure — help me

## What the Hub should do with it

1. Create a **Lead** (status New) with name, phone (normalize to E.164 `+1XXXXXXXXXX`), email, address, service, urgency, message, property type.
2. **Match or create the customer** by normalized phone, then email.
3. **Store consent as its own record** (CASL / 10DLC): `sms_consent`, the exact `sms_consent_text`, `consent_disclosure_version`, `consent_timestamp`, `page_url`. Marketing texts only go to leads with `sms_consent: true`; keep transactional and marketing consent as separate flags.
4. **Store attribution** (`landing_page`, `referrer`, `attribution.*`) so marketing ROI by channel and by page can be reported.
5. If `urgency` = `Emergency (24/7)`, alert the on-call person immediately (push/SMS).
6. Respond `201 {"ok": true, "lead_id": "..."}`.

## Hooking it up on the website

Edit `/lead-config.js` at the repo root: fill in `endpoints.dev` / `endpoints.live` and `key` (the same key is used for both Hub projects), and set `use` to `"dev"` or `"live"`. Commit. No rebuild is needed. Optional: `emailBackupKey` (web3forms.com) also emails each lead to info@ldrservice.com.

## Changes after the Hub findings (20 Nov)
- `address` is now the street line only; `city` and `postal_code` are sent as separate fields (map to `address_line1`, `city`, `postal_code`; postal code is uppercased).
- "Commercial boiler / plumbing" is now two options: "Commercial boilers" → `hvac`, "Commercial plumbing" → `plumbing`.
- Choosing "Emergency (24/7)" now also shows a "call now" prompt on the form, so an emergency never relies on the form alone.
