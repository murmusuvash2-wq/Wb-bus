# BusJatri Work Log

Permanent memory of all work done on the repo. Newest entries first.

### 2026-09-15 — All Bus Time Table Index Page v6 (LIVE)
- What: Replaced the 808KB plain-list index page (bus-time-table/index.html) with a v6 animated design — live search with Matching Routes chips, quick filter chips, 16 Popular Starting Places cards (link to place pages), A–Z alphabet nav with 597 static crawlable place rows, accordion place rows with staggered route chips (1,903 routes from embedded JSON), FAQ accordion, hidden ad zones, WebSite + BreadcrumbList JSON-LD, canonical. Page size 808KB → 319KB (-60%).
- Animations: count-up stat chips (597/1903/3382), IntersectionObserver scroll-reveal for letter groups, popIn staggered route chips on accordion open (capped 42×13ms), wiggle eyebrow bus icon, live-dot pulse on search label, prefers-reduced-motion fallback.
- Why: User approved the demo ("pass animation laga dena bas") — design pass + animations requested.
- Files: scripts/v5/new_index_part1.txt + new_index_part2.txt (source of truth), scripts/patches/apply_index.py (splice script), .github/workflows/apply-index.yml (workflow), scripts/gen_seo_pages.py (spliced, auto-commit), bus-time-table/index.html (generated, auto-commit)
- Commits: 29cdaa5e (apply_index.py), 350a9ded (apply-index.yml), ff282afc (part1), e4970d1c (part2), workflow auto-commit (index pages). Workflow run 34914538432: SUCCESS.
- Status: done — verified 16/16 live checks on raw.githubusercontent.com main. Vercel auto-deploying.
- Notes: apply-index.yml and apply-v5.yml BOTH trigger on scripts/v5/** pushes (they run concurrently; first two index runs failed due to missing part2 + push race, workflow_dispatch run succeeded). If editing scripts/v5/*.txt again, expect apply-v5.yml to also fire (harmless — idempotent splice) but trigger apply-index.yml via dispatch afterwards.

### 2026-09-15 — SEO Route Pages v5 Redesign (LIVE)
- What: Replaced all ~2,015 SEO route pages with v5 design — working search box, live departures board (auto-refreshing, IST clock), accordion bus cards with mini-timelines, route stops timeline, via chips, FAQ accordion, related routes, breadcrumb, hero with route-line animation. Ads stay HIDDEN (display:none by default, only .active shows). Bilingual EN/BN toggle works.
- Why: Approved v5 demo design — user said "phele demo wala implement karo". This is the core Month 1 visual/UX upgrade for SEO pages.
- Files: scripts/gen_seo_pages.py (spliced via scripts/patches/apply_v5.py from scripts/v5/*.txt), css/seo.css (new 17.8KB v5 stylesheet), .github/workflows/apply-v5.yml (one-time regen workflow)
- Commit: df89e187 (workflow auto-commit), af1fac51 (route_bn fix), 5e37cea4 (CSS), eb174951 (route page), a50c3b4a (bus_card), 1c8afe68 (shell), ec130506 (splice+workflow)
- Status: done — pages live on GitHub, Vercel deploying. Workflow ran successfully (run #6, conclusion: success).
- Bug fixed: route_nn → route_bn typo in bn_sub variable caused NameError on first run.

### 2026-09-15 — Home Page Animations (from earlier session)
- What: Added driftBus, fadeUp staggered, eyebrow animations to home page
- Files: index.html, css/extras.css, js/app.js (via scripts/patch_home_page.py)
- Status: done — live on site

## Next steps / backlog
- [ ] Verify v6 index page on live site after Vercel deploy (https://wb-bus.vercel.app/bus-time-table/ — hard refresh)
- [ ] Fix theme/lang persistence bug on ALL SEO pages: shell IIFE runs in <head> before body exists, so localStorage restore fails silently (index page has its own working restore in body script)
- [ ] Clean up: delete .github/workflows/apply-v5.yml + scripts/patches/apply_v5.py (one-time files; apply-v5 still triggers on scripts/v5/** pushes alongside apply-index)
- [ ] Fix sub-12px text on SEO pages (meta-lb is 9px — bump to 11px)
- [ ] Fix tap targets <44px on some buttons
- [ ] Add focus-visible styles for accessibility
- [ ] Add tablet breakpoint (640px-768px)
- [ ] Improve light-mode contrast on ink-dim text
- [ ] Submit sitemap in Google Search Console (needs authorization)
- [ ] Request indexing for key route pages in GSC
- [ ] Apply for AdSense after 20-30 quality sessions/day
- [ ] Expand route coverage: generate pages for searched-but-missing routes
- [ ] Add Bengali meta descriptions to route pages
- [ ] Consider Supabase/Cloudflare migration (deferred)
