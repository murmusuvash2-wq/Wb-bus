# BusJatri — Design Changes (2026-09-14)

## Overview
Redesigned SEO route pages and bus detail pages with compact "Departure Board" aesthetic (amber/maroon, ticket-stub style). Home page layout fixes (centered title, animation at top, prominent search) were also applied.

---

## Files Pushed to GitHub

### 1. `css/seo.css` (NEW — 6492 bytes)
Complete CSS for SEO route pages. Replaces inline styles with a clean class-based system.
- Amber/maroon palette matching main site
- Dark mode support (`[data-theme="dark"]`)
- Compact bus rows (`.bus-row`)
- Horizontal route map (`.routemap`, `.rm-track`, `.rm-dot`)
- Stat chips (`.schip`)
- FAQ accordion (`details`/`summary`)
- Footer links (About, Contact, Privacy, Credits, All Bus Timetables)

### 2. `js/bus-page.js` (NEW — 5809 bytes)
Overrides `app.js`'s `renderBus()` function with redesigned bus detail page:
- **Ticket-stub header**: bus name + type badge + route line, with amber/maroon striped top border
- **Info grid**: 6 compact info cards (Departure, Arrival, Stops, Fare, Operator, Depot, Contact)
- **WhatsApp share button**: green button with bus name + route + site link
- **Google Maps button**: opens route directions with all stoppages as waypoints
- **Weather card**: shows destination weather (lazy-loaded)
- **Compact stop timeline**: vertical dotted rail with stop names, railway info, up/down times
- **Show all/less stops**: initially shows 8 stops, button expands to full list
- Loaded AFTER `app.js` so function redefinition takes effect at call time

### 3. `css/bus-page.css` (NEW — 3763 bytes)
Styles for the bus detail page (`.bus-head`, `.info-grid`, `.stop-list`, `.wa-btn`, `.map-btn`, `.weather-card`, `.show-all`)

### 4. `js/extras.js` (RESTORED — 5929 bytes)
Restored to original pre-corruption state. Contains: theme toggle, WhatsApp share, geolocation, contact form, report time, admin dashboard, AdSense activation.

### 5. `css/extras.css` (RESTORED — 10431 bytes)
Restored to original state with: bus animation, bigger search, WhatsApp button, AdSense zones, footer links, compact home layout, centered title/taglines.

### 6. `index.html` (PATCHED — 4035 bytes)
Added two lines:
- `<link rel="stylesheet" href="css/bus-page.css" />` in `<head>`
- `<script src="js/bus-page.js"></script>` after `extras.js` script tag

---

## Design: SEO Route Page (Kolkata → Digha example)

```
┌─────────────────────────────────────┐
│ [BusJatri logo]    Home  Routes     │  ← sticky header
├─────────────────────────────────────┤
│ HOME › BUS TIMETABLE › KOLKATA → DIGHA │  ← breadcrumb
│                                     │
│  Kolkata → Digha                   │  ← H1 (centered, large)
│  কলকাতা থেকে দীঘা বাসের সময়সূচী  │  ← Bengali subtitle
│                                     │
│  [8 buses] [First 6:00] [Last 5:30] │  ← stat chips
│                                     │
│  Today's Departures                 │
│  ┌───────────────────────────────┐  │
│  │ 6:00  SBSTC Express  [Govt]  │  │  ← compact bus row
│  │ AM    ₹160 ~4h 30m 14 stops  │  │
│  ├───────────────────────────────┤  │
│  │ 7:30  WBTC Volvo AC  [AC]    │  │
│  ├───────────────────────────────┤  │
│  │ 8:45  Digha Super  [Private] │  │
│  └───────────────────────────────┘  │
│                                     │
│  Route Map                          │
│  ●──────●──────●──────●──────●     │  ← horizontal dots
│  KOL    KOL    MEC   CON    DIG    │
│  6:00   7:40   8:15  9:50   10:30  │
│                                     │
│  Via Stoppages                      │
│  [Kolaghat] [Mecheda] [Contai]      │  ← tappable chips
│                                     │
│  FAQ                                │
│  ▸ First bus?  ─ 6:00 AM           │  ← accordion
│  ▸ Last bus?   ─ 5:30 PM           │
│  ▸ How many?  ─ 8 services         │
│                                     │
│  More Routes from Kolkata           │
│  [→ Shankarpur] [→ Mandarmani]     │
│                                     │
│  About | Contact | Privacy | Credits│  ← footer links
│  BusJatri — busjatri@zohomail.in    │
└─────────────────────────────────────┘
```

**Key changes from old design:**
- Removed: long paragraph text, "Journey Information" section, "Bus Operators" list, "Search another route" button
- Added: horizontal route map, stat chips, via stoppage chips, compact bus rows with badges
- FAQ limited to 3 questions (was 5)
- Max width reduced to 720px (was 980px) — more mobile-friendly

---

## Design: Bus Detail Page

```
┌─────────────────────────────────────┐
│ ← Back                              │
│ ┌─────────────────────────────────┐ │
│ │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │ │  ← amber/maroon stripe
│ │ SBSTC Kolkata-Digha [Govt]     │ │  ← bus name + badge
│ │ 🚌 Kolkata ⇄ Digha             │ │  ← route line
│ │                                 │ │
│ │ [Dep 6:00] [Arr 10:30] [14 stops]│ │  ← info grid (6 cards)
│ │ [₹160] [SBSTC] [Karunamoyee]    │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [🗺 Route on Maps] [💬 Share WhatsApp]│  ← action buttons
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ WEATHER IN DIGHA (NOW)         │ │  ← weather card
│ │ 28°C                            │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Route Timetable                     │
│ ┌─────────────────────────────────┐ │
│ │ ● Kolkata (Esplanade)  6:00 dep │ │  ← stop timeline
│ │ │                               │ │
│ │ ● Kolaghat            7:40 7:50 │ │
│ │ │   Railway: Kolaghat ~1 km     │ │  ← railway info
│ │ ● Mecheda              8:15 8:25 │ │
│ │ │                               │ │
│ │ ● Contai               9:50 10:00│ │
│ │ │                               │ │
│ │ ● Digha Bus Stand     arr 10:30 │ │
│ │                                 │ │
│ │ [Show all 14 stops ⇓]          │ │  ← expand button
│ └─────────────────────────────────┘ │
│                                     │
│ About | Contact | Privacy | Credits │  ← footer
└─────────────────────────────────────┘
```

**Key changes from old design:**
- Removed: long paragraph descriptions, inline styles, large spacing
- Added: ticket-stub header with striped border, info grid (6 cards), WhatsApp share with site link, Google Maps with waypoints, weather card, railway station info per stop, show all/less stops button
- Stop timeline: compact vertical rail with up/down times (was wide table)

---

## SEO Page Regeneration — COMPLETE ✅ (2026-09-15)

The compact route-page templates were pushed to `scripts/gen_seo_pages.py` and all 2,015 pages were regenerated via the `Regenerate SEO Pages` GitHub workflow. Route pages now use the new design with `css/seo.css`.

---

# UX Fixes (2026-09-16)

## Overview
Four data-accuracy and language fixes applied via `scripts/apply_ux_fixes.py` (idempotent patch script, runs in CI before generation) and `scripts/finalize_pages.py` updates. All pages regenerated through the workflow: **2,639 pages total, sitemap 2,640 URLs.**

## Changes

### 1. Single-bus routes now get pages (+543 new route pages)
Removed the `len(buses) >= 2` filter in `gen_seo_pages.py` route grouping. Routes like Kharagpur → Baharampur now have their own page. Route pages: 1,984 → 2,527. Index search data now covers 775 places / 2,527 route pairs.

### 2. "Time N/A" pill for missing departure times
Buses without a departure time (2,346 of 4,018 entries) previously showed a bare "—" in the time column. Now render `<span class="no-time">Time N/A</span>` (styled small uppercase pill, existing CSS).

### 3. Bengali toggle on the timetable index (`/bus-time-table/`)
- `বাংলা` button injected into the header nav (JS, index only)
- Key texts switch EN ↔ বাংলা via `label-en`/`label-bn` spans: H1, tagline, stat chips, search label, section titles, empty state, search placeholder
- Language preference saved in localStorage key `bj-lang` (shared with the site-wide `js/lang-persist.js` key), with `navigator.language` bn auto-detect

### 4. Grammar + scroll fixes
- "1 routes" → "1 route", "1 buses" → "1 bus" (index A–Z rows, chips, route hero chips, place pages, JS-rendered chips)
- Quick search chips now scroll to the Matching Routes section instead of a hidden section

## Files
- `scripts/apply_ux_fixes.py` (NEW) — 21 exact-match patches, idempotent (skips if already applied)
- `scripts/finalize_pages.py` — stat-chip rewrites updated for the bilingual markup; numbers still sourced from dataset meta (2,740 stops / 2,526 routes / 4,018 bus services)
- `.github/workflows/regenerate-seo-pages.yml` — runs `apply_ux_fixes.py` (replaces the old one-shot `apply_seo_redesign.py` step); trigger paths extended to the generator and finalize scripts
