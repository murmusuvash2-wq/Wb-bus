#!/usr/bin/env python3
"""Patch gen_seo_pages.py part 3: splice the new index-body block
(districts + search card + collapsed A-Z) into the index section."""

P = 'scripts/gen_seo_pages.py'
src = open(P, encoding='utf-8').read()

OLD_IDX = """places_links = ' '.join(f'<a class="sugg-chip" href="buses-from-{slug(p)}.html">{place(p)}</a>' for p in top_places[:20])
body = f'''"""
tail_old = "{idx_rows}'''"
assert src.count(OLD_IDX) == 1, f'OLD_IDX x{src.count(OLD_IDX)}'
assert src.count(tail_old) == 1, f'tail x{src.count(tail_old)}'

NEW_BLOCK = r'''# ---- district sections ----
dist_map = defaultdict(list)
for p, routes_ in by_place.items():
    dist_map[DISTRICTS.get(p, 'Other')].append((p, routes_))
dist_order = sorted(dist_map, key=lambda d: (d == 'Other', -sum(len(r) for _, r in dist_map[d])))

PIN = '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>'

def district_section(d):
    places_ = dist_map[d]
    en_d, bn_d = DISTRICT_META[d]
    nroutes = sum(len(r) for _, r in places_)
    cards = ''.join(
        f'<a class="place-card" href="buses-from-{slug(p)}.html">'
        f'<span class="pc-name">{place(p)}</span>'
        f'<span class="pc-count">{lbl(f"{len(rs)} routes", f"{bnum(len(rs))}টি রুট")}</span></a>'
        for p, rs in sorted(places_, key=lambda kv: -len(kv[1])))
    open_attr = ' open' if d in dist_order[:3] else ''
    return (f'<details class="district-card"{open_attr}>'
            f'<summary>{PIN}{lbl(en_d, bn_d)}'
            f'<span class="dist-count">{lbl(f"{nroutes} routes", f"{bnum(nroutes)}টি রুট")}</span></summary>'
            f'<div class="place-cards">{cards}</div></details>')

districts_html = ''.join(district_section(d) for d in dist_order)

# ---- search card (plain string, JS braces must not hit the f-string) ----
search_js = """
<script>
(function () {
  var IDX = null;
  var input = document.getElementById('routeSearch');
  var list = document.getElementById('srList');
  if (!input || !list) return;
  fetch('search-index.json').then(function (r) { return r.json(); }).then(function (x) { IDX = x; });
  input.addEventListener('input', function () {
    if (!IDX) return;
    var q = input.value.trim().toLowerCase();
    list.innerHTML = '';
    if (!q) return;
    var out = [];
    for (var i = 0; i < IDX.length && out.length < 14; i++) {
      var e = IDX[i];
      if (e.en.toLowerCase().indexOf(q) !== -1 || (e.bn && e.bn.indexOf(q) !== -1)) out.push(e);
    }
    if (!out.length) {
      var d = document.createElement('div');
      d.className = 'sr-empty';
      d.innerHTML = '__EMPTY__';
      list.appendChild(d);
      return;
    }
    var frag = document.createDocumentFragment();
    out.forEach(function (e) {
      var a = document.createElement('a');
      a.className = 'sr-item' + (e.t === 'p' ? ' sr-place' : '');
      a.href = e.u;
      var s1 = document.createElement('span');
      s1.className = 'sr-en'; s1.textContent = e.en;
      a.appendChild(s1);
      if (e.bn) {
        var s2 = document.createElement('span');
        s2.className = 'sr-bn'; s2.textContent = e.bn;
        a.appendChild(s2);
      }
      frag.appendChild(a);
    });
    list.appendChild(frag);
  });
})();
</script>
"""
search_js = search_js.replace('__EMPTY__', lbl('No matching route or place', 'কোনো রুট বা জায়গা পাওয়া যায়নি'))

search_card = f"""
<section class="search-card" id="searchCard" aria-label="{esc('Search routes and places')}">
<div class="sc-row">
<svg class="icon sc-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
<input type="search" id="routeSearch" autocomplete="off"
 placeholder="{esc('Search: Digha / দীঘা / Bankura / বাঁকুড়া ...')}" aria-label="{esc('Search routes and places')}">
</div>
<div class="sc-hint">{lbl(f'{len(route_meta)} routes', f'{bnum(len(route_meta))}টি রুট')} · {lbl('English and বাংলা both work', 'ইংরেজি ও বাংলা দুটোই চলবে')}</div>
<div class="sr-list" id="srList" aria-live="polite"></div>
{search_js}
</section>"""

all_list = (f'<details class="all-list"><summary><svg class="icon" viewBox="0 0 24 24" aria-hidden="true">'
            f'<path d="M4 6h16M4 12h16M4 18h16"/></svg>'
            + lbl('All routes A-Z', 'সব রুট A-Z')
            + f' <span class="dist-count">{lbl(f"{len(route_meta)}", f"{bnum(len(route_meta))}")}</span></summary>{idx_rows}</details>')

body = f"""
<section class="route-hero">
<p class="route-eyebrow">{lbl('All Routes', 'সব রুট')}</p>
<h1 class="route-main"><span class="route-end"><span class="place">{lbl('West Bengal Bus Time Tables', 'পশ্চিমবঙ্গের বাস টাইম টেবিল')}</span></span></h1>
<div class="route-dash"><span class="stamp">{lbl(f'Updated {LASTMOD}', f'আপডেট {LASTMOD}')}</span></div>
</section>
<div class="stats" role="list"><div class="stat" role="listitem"><div class="num">{len(route_meta)}</div><div class="label">{lbl('Routes', 'রুট')}</div></div><div class="stat" role="listitem"><div class="num">{len(BUSES)}</div><div class="label">{lbl('Buses', 'বাস')}</div></div></div>
{search_card}
<section class="section" style="padding-top:0"><h2 class="section-title">{PIN}{lbl('Browse by District', 'জেলা অনুযায়ী দেখুন')}</h2></section>
{districts_html}
{all_list}
"""

'''

i = src.find(OLD_IDX)
j = src.find(tail_old, i) + len(tail_old)
src = src[:i] + NEW_BLOCK + src[j:]

open(P, 'w', encoding='utf-8').write(src)
print('patch 3 (index splice) applied OK')
