# BusJatri Work Log

Permanent memory of all work done on this site. Read this before starting any new task.

---

## 2026-09-14 — Home page: Live Departures board + Stoppage search + Popular Routes

- What: Three user-approved changes to the home page:
  1. **Live Departures board** — big amber IST clock (32px) + geo-aware tabs showing 3-4 nearest origin cities (Kolkata/Digha/Burdwan/Siliguri/Bankura). Uses navigator.geolocation + haversine to pick nearest 3; falls back to Kolkata/Digha/Burdwan when denied. Departure rows with live countdown ("in 25m" / "tmrw +13h"), departed buses dimmed. Reuses existing stopDepartures() so rows show real buses; clicking a row opens the bus detail page.
  2. **Stoppage search** — replaced the "Via (optional)" field with "Stoppage" field. Searching with only a stoppage shows all buses halting there; From+To+Stoppage filters routes that pass through the stop.
  3. **Popular Routes section** — top 10 route pairs by bus count (computed from live data), rendered as clickable chips that trigger route search.
- Why: User approved demo home-current-demo-v2.html. Ads stay hidden (ad-zone display:none by default) until AdSense approval.
- Files: `js/app.js` (doSearch, renderHome, renderSearch + new renderBoard/detectLocation/computePopularRoutes), `css/extras.css` (lv-* board styles + route-chip styles), `scripts/patch_home_page.py` (patch script)
- Commit: 4abb1548 (patch via workflow), 5bed6005 (cleanup)
- Status: done — Vercel auto-deploys; verify on wb-bus.vercel.app

## 2026-09-14 — Fix GitHub workflow indentation error
- What: `fix-garhbeta-railway.yml` had Python heredoc indentation errors (lines at 11-15 spaces instead of 10) causing IndentationError on every run; second step's `run:` key was misaligned at 9 spaces
- Why: 20+ failed workflow runs; the Garhbeta railway fix never got applied
- Files: `.github/workflows/fix-garhbeta-railway.yml`
- Commit: 1be91d9c56b2794403a8ee5c29cba13932854646
- Status: superseded — indentation fix was correct but NOT the root cause; the workflow still failed after it (runs #34+). Real root cause found and fixed in the entry below.

## 2026-09-14 — Fix Garhbeta workflow (real root cause) + restore geocode cache
- What: `fix-garhbeta-railway.yml` Step 1 did `json.loads(data/stop_coords.json)` but that file contained the literal text `PLACEHOLDER_COORDS` (not JSON) — committed by mistake in 7f42033 ("free geocode pass"). This raised JSONDecodeError on every run, so the Garhbeta railway fix never got applied (live data still had Garhbeta ↔ SALBONNI 17.3km). Fixed by (a) restoring the real 677-entry geocode cache (269 non-null coords) from commit 54e9f96 as pure-ASCII JSON, and (b) wrapping the workflow's `json.loads` in try/except so it falls back to `{}` instead of hard-failing on a bad/placeholder cache.
- Why: 33+ failed workflow runs; Garhbeta showed the wrong railway station on the live site. The cache file is build-time only (frontend `js/app.js` does NOT load `stop_coords.json`), so the placeholder didn't break the live site directly but blocked all railway re-attachment.
- Files: `data/stop_coords.json` (restored, ASCII), `.github/workflows/fix-garhbeta-railway.yml` (defensive json.loads)
- Commits: eab3acf (cache restore — got UTF-8 corrupted via base64 tool path), 39de048 (workflow fix — also base64-corrupted), 128cbc4 (workflow fix corrected as plain text), a070671 (cache restored clean as ASCII JSON)
- Status: done — workflow runs #36 and #37 both SUCCESS. Live `busjatri_data.json` now has Garhbeta ↔ GARHBETA (GBA) 0.0km, and 251 stops retain a `nearest_station` (key routes verified: Kharagpur↔KGP, Digha↔DGHA, Bankura↔BQA, Siliguri↔NHU, Asansol↔ASNE).
- Lesson: the GitHub file-commit tool can corrupt UTF-8 bytes when given base64 input — commit non-ASCII data as plain text, or pre-flatten to ASCII (`json.dumps(ensure_ascii=True)`).

## 2026-09-14 — UI/UX + SEO audit of live site
- What: Full audit of colour contrast, text sizes, responsiveness, tap targets, focus states, and SEO tags on index.html and route pages
- Why: Preparing for Google ranking push and AdSense application
- Files: (audit only, no changes)
- Status: done — findings recorded below in backlog

### Audit findings

**Colour contrast — PASS:** light theme ink 16.5:1, dim text 5.5:1; dark theme 13.9:1 / 6.1:1. Only light-mode search button text on amber is borderline (3.46:1).

**Text sizes — FAIL:** 24 instances of sub-12px text (9px admin labels, 10px/10.5px/11px labels & meta). report-form input 13px triggers iOS zoom.

**Responsiveness — GAPS:** only 480/560/640px breakpoints; nothing between 640-980px (tablet landscape); result-item and place-card have no mobile adjustments.

**Tap targets — FAIL:** sugg-chip ~31px, lang-btn ~25px, report-btn ~21px height (Apple HIG minimum 44px).

**Focus states — FAIL:** 4x `outline: none` without replacement `:focus-visible` styles.

**SEO index.html — FAIL:** no visible H1 (JS-rendered), no canonical, no JSON-LD schema, description 178 chars (too long, Google truncates ~155).

**SEO route pages — FAIL:** 2,000 pages missing meta descriptions, og:image, twitter:card. (canonical OK, H1 OK, JSON-LD OK on route pages.)

**robots.txt — PASS:** sitemap referenced.

---

## Next steps / backlog

### Month 1 — Technical SEO (priority order)
- [x] Verify fix-garhbeta-railway.yml passes when triggered — DONE 2026-09-14 (runs #36, #37 success)
- [ ] Add meta descriptions to route pages via `scripts/gen_seo_pages.py` (fixes 2,000 pages in one change)
- [ ] index.html: add visible H1, canonical link, JSON-LD WebSite schema
- [ ] Shorten index.html meta description to ≤155 chars
- [ ] Add og:image + twitter:card to route pages (generator change)
- [ ] Add noindex to admin.html
- [ ] Submit sitemap.xml in Google Search Console; request indexing for top routes
- [x] Home page: Live Departures board + Stoppage search + Popular Routes — DONE 2026-09-14

### Month 2 — Content & UX
- [ ] Fix sub-12px text sizes (raise to 12px floor, especially Bengali text)
- [ ] Enlarge tap targets to 44px+ (sugg-chip, lang-btn, report-btn)
- [ ] Add :focus-visible styles, remove bare outline:none
- [ ] Add 768px tablet breakpoint
- [ ] Improve light-mode button contrast (3.46:1 -> 4.5:1)
- [ ] Generate pages for searched-but-missing routes
- [ ] Add fare/first bus/last bus/journey time blocks to route pages
- [ ] Interlink route pages (related routes)
- [ ] Add FAQ schema to route pages

### Month 3 — Authority & monitoring
- [ ] Monitor Search Console queries/CTR; rewrite titles of high-impression low-CTR pages
- [ ] District hub pages, "how to reach X" pages
- [ ] Keep data fresh weekly (auto-update workflows)
- [ ] Apply for AdSense after Month 1+2 fixes deployed

### Data sources
- [ ] Identify new official sources (WBTC/SBSTC/NBSTC route data) and wire scrapers into scheduled workflows
- [ ] Monitor `Auto-update from bussathi.in` — run #4 was cancelled (not failed); check the next scheduled run completes, debug if it repeats
- [ ] Optional: full geocode run (without SKIP_GEOCODE) to give the remaining ~2,470 uncached stops coords + railway stations
