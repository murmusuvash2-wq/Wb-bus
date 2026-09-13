#!/usr/bin/env python3
"""Apply UI polish to style.css and app.js. Idempotent."""

# ---- 1. style.css ----
css_path = 'css/style.css'
css = open(css_path, encoding='utf-8').read()

if '--panel:' not in css:
    # Insert aliases in :root
    css = css.replace(
        '  --line-strong: rgba(33, 28, 22, .24);\n\n  --amber:',
        '  --line-strong: rgba(33, 28, 22, .24);\n  --border: rgba(33, 28, 22, .13);\n  --panel: #efe6d3;\n\n  --amber:', 1)
    # Dark mode aliases
    css = css.replace(
        '  --line: rgba(241, 234, 216, .1);\n  --line-strong: rgba(241, 234, 216, .2);\n\n  --amber:',
        '  --line: rgba(241, 234, 216, .1);\n  --line-strong: rgba(241, 234, 216, .2);\n  --border: rgba(241, 234, 216, .12);\n  --panel: #29243570;\n\n  --amber:', 1)
    css = css.replace(
        '    --line: rgba(241, 234, 216, .1); --line-strong: rgba(241, 234, 216, .2);\n    --amber:',
        '    --line: rgba(241, 234, 216, .1); --line-strong: rgba(241, 234, 216, .2);\n    --border: rgba(241, 234, 216, .12); --panel: #29243570;\n    --amber:', 1)
    # Compact hero
    css = css.replace('padding: 46px 0 26px;', 'padding: 30px 0 18px;', 1)
    css = css.replace('font-size: 16px; margin-bottom: 26px;', 'font-size: 15px; margin-bottom: 18px;', 1)
    css = css.replace('padding: 22px 22px 20px;', 'padding: 16px 18px 14px;', 1)
    # Append new CSS
    css += '''
/* ---------- UI polish round ---------- */
.swap-btn {
  align-self: center; flex: none; width: 32px; height: 32px; border-radius: 50%;
  border: 1px solid var(--line-strong); background: var(--surface-2); color: var(--ink-dim);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: transform .2s, border-color .2s, color .2s;
}
.swap-btn:hover { border-color: var(--amber); color: var(--amber); transform: rotate(180deg); }
.swap-btn:active { transform: rotate(180deg) scale(.94); }
.swap-btn .icon { width: 15px; height: 15px; }
@media (max-width: 639px) { .swap-btn { display: none; } }

.via-hint { font-weight: 400; color: var(--ink-dim); text-transform: none; letter-spacing: 0; font-family: var(--font-body); }

.stats-inline {
  color: var(--ink-dim); font-size: 13.5px; font-family: var(--font-mono);
  padding: 14px 0 0; margin: 0;
}
.stats-inline .icon { width: 14px; height: 14px; color: var(--amber); vertical-align: -2px; margin-right: 4px; }

.place-card .place-bn { display: block; font-size: 12px; color: var(--ink-dim); margin-top: 1px; }
body:not(.lang-bn) .place-card .place-bn { display: none; }
.place-card .place-tag {
  font-size: 10.5px; color: var(--amber-ink); background: var(--amber-soft);
  display: inline-block; padding: 2px 8px; border-radius: 999px; margin-top: 8px;
  font-family: var(--font-mono); letter-spacing: .05em; text-transform: uppercase; font-weight: 600;
}
.place-card .count { display: none; }
'''
    open(css_path, 'w', encoding='utf-8').write(css)
    print('style.css polished')
else:
    print('style.css already polished')

# ---- 2. app.js ----
app_path = 'js/app.js'
src = open(app_path, encoding='utf-8').read()

if 'swapFromTo' not in src:
    # Via label: English only
    src = src.replace(
        "<label>${icon('ticket')} <span class=\"label-en\">Via (optional)</span><span class=\"label-bn\">\u09ae\u09be\u09b0\u09cd\u0997\u09c7 (\u0990\u099a\u09cd\u099b\u09bf\u0995)</span></label>",
        "<label>${icon('ticket')} Via <span class=\"via-hint\">(optional)</span></label>", 1)

    # Place cards: remove bus count, add tourist tag
    old_cards_head = "    const count = stop ? stop.bus_ids.length : 0;\n    const iconName = PLACE_ICONS[p.name] || 'pin';"
    new_cards_head = "    const iconName = PLACE_ICONS[p.name] || 'pin';"
    src = src.replace(old_cards_head, new_cards_head, 1)
    src = src.replace(
        "      <div class=\"count\">${count ? count + ' buses' : 'Explore'}</div>",
        "      <div class=\"place-tag\">${esc(p.tag || 'Explore')}</div>", 1)

    # Popular places -> tourist spots
    import re
    src = re.sub(
        r"const POPULAR_PLACES = \[.*?\];",
        "const POPULAR_PLACES = [\n"
        "  { name: 'Digha', tag: 'Sea Beach' },\n"
        "  { name: 'Mukutmanipur', tag: 'Lake & Dam' },\n"
        "  { name: 'Bishnupur', tag: 'Terracotta Temples' },\n"
        "  { name: 'Jhargram', tag: 'Forest & Palaces' },\n"
        "  { name: 'Purulia', tag: 'Hills & Falls' },\n"
        "  { name: 'Sundarban', tag: 'Mangrove Forest' },\n"
        "  { name: 'Shantiniketan', tag: 'Tagore Home' },\n"
        "  { name: 'Kolkata', tag: 'City of Joy' },\n"
        "  { name: 'Mandarmani', tag: 'Beach Resort' },\n"
        "  { name: 'Bankura', tag: 'Heritage Trails' },\n"
        "  { name: 'Kurseong', tag: 'Tea Gardens' },\n"
        "  { name: 'Bakreshwar', tag: 'Hot Springs' },\n"
        "];", src, count=1, flags=re.DOTALL)

    # Swap button between From and To
    src = src.replace(
        '          </div>\n          <div class="search-field">\n            <label>${icon(\'compass\')}',
        '          </div>\n          <button class="swap-btn" onclick="swapFromTo()" title="Swap From & To" aria-label="Swap origin and destination">${icon(\'compass\')}</button>\n          <div class="search-field">\n            <label>${icon(\'compass\')}', 1)

    # swapFromTo function
    src = src.replace(
        'function quickSearch(name) {',
        'function swapFromTo() {\n  const f = document.getElementById(\'fromInput\');\n  const t = document.getElementById(\'toInput\');\n  const tmp = f.value; f.value = t.value; t.value = tmp;\n}\n\nfunction quickSearch(name) {', 1)

    # Stats: inline text
    src = re.sub(
        r'<div class="stats">.*?</div>\s*</div>\s*</div>\s*</div>',
        '<p class="stats-inline">${icon(\'bus\')} ${(DATA.meta.total_buses || 0).toLocaleString(\'en-IN\')}+ <span class="label-en">buses</span><span class="label-bn">\u099f\u09bf \u09ac\u09be\u09b8</span> &middot; ${(DATA.meta.total_routes || 0).toLocaleString(\'en-IN\')}+ <span class="label-en">routes</span><span class="label-bn">\u099f\u09bf \u09b0\u09c1\u099f</span> &middot; ${(DATA.meta.total_stops || 0).toLocaleString(\'en-IN\')}+ <span class="label-en">stops</span><span class="label-bn">\u099f\u09bf \u09b8\u09cd\u099f\u09aa</span></p>',
        src, count=1, flags=re.DOTALL)

    # Section title
    src = src.replace('Popular Places</span><span class="label-bn">', 'Popular Destinations</span><span class="label-bn">', 1)
    src = src.replace('\u099c\u09a8\u09aa\u09cd\u09b0\u09bf\u09af\u09bc \u09b8\u09cd\u09a5\u09be\u09a8\u09ac\u09cd\u09af</span>', '\u099c\u09a8\u09aa\u09cd\u09b0\u09bf\u09af\u09bc \u0997\u09a8\u09cd\u09a4\u09ac\u09cd\u09af</span>', 1)

    # PLACE_ICONS additions
    src = src.replace(
        "  Durgapur: 'cog', Khatra: 'bus', Bishnupur: 'dome', Medinipur: 'pin',\n};",
        "  Durgapur: 'cog', Khatra: 'bus', Bishnupur: 'dome', Medinipur: 'pin',\n"
        "  Sundarban: 'trees', Shantiniketan: 'landmark', Mandarmani: 'waves',\n"
        "  Kurseong: 'mountain', Bakreshwar: 'sun',\n};", 1)

    open(app_path, 'w', encoding='utf-8').write(src)
    print('app.js polished')
else:
    print('app.js already polished')

