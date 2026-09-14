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
- [ ] Verify v5 pages on live site after Vercel deploy (check https://wb-bus.vercel.app/bus-time-table/esplanade-to-digha.html)
- [ ] Clean up: delete .github/workflows/apply-v5.yml + scripts/v5/ + scripts/patches/apply_v5.py (one-time files)
- [ ] Fix sub-12px text on SEO pages (meta-lb is 9px — bump to 11px)
- [ ] Fix tap targets <44px on some buttons
- [ ] Add focus-visible styles for accessibility
- [ ] Add tablet breakpoint (640px-768px)
- [ ] Improve light-mode contrast on ink-dim text
- [ ] Submit sitemap in Google Search Console (needs authorization)
- [ ] Request indexing for key route pages in GSC
- [ ] Design "all bus times" page (user mentioned: "uske baad all bus time wala bhi design karenge")
- [ ] Apply for AdSense after 20-30 quality sessions/day
- [ ] Expand route coverage: generate pages for searched-but-missing routes
- [ ] Add Bengali meta descriptions to route pages
- [ ] Consider Supabase/Cloudflare migration (deferred)
