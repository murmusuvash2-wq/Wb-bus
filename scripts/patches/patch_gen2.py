#!/usr/bin/env python3
"""Patch gen_seo_pages.py part 2: hub pages for all origins, district-wise
index page with search box, search-index.json."""

P = 'scripts/gen_seo_pages.py'
src = open(P, encoding='utf-8').read()
def rep(old, new, cnt=1):
    global src
    assert src.count(old) == cnt, f'pattern x{src.count(old)} (expected {cnt}): {old[:80]!r}'
    src = src.replace(old, new)

# ---------------- G. hub pages for every origin that has route pages --------
rep("""top_places = sorted(place_buses, key=lambda p: -len(place_buses[p]))[:30]

for p in top_places:""",
    """by_place = defaultdict(list)
for (o, t) in route_meta:
    by_place[o].append((o, t))
hub_places = sorted(by_place, key=lambda p: -len(by_place[p]))
top_places = hub_places[:30]

for p in hub_places:""")

# ---------------- H. index section: remove duplicate by_place --------------
rep("""by_place = defaultdict(list)
for (o, t) in route_meta:
    by_place[o].append((o, t))
idx_rows = ''.join(""",
    """idx_rows = ''.join(""")

# ---------------- J. search-index.json --------------------------------------
rep("""open('sitemap.xml', 'w').write(sm)""",
    """# search index (client-side search on the All Routes page)
search = []
for (o, t) in route_meta:
    bo_, bt_2 = bn(o), bn(t)
    search.append({'t': 'r', 'u': f'{slug(o)}-to-{slug(t)}.html',
                   'en': f'{o} to {t}',
                   'bn': f'{bo_} থেকে {bt_2}' if bo_ and bt_2 else ''})
for p_ in hub_places:
    bp_ = bn(p_)
    search.append({'t': 'p', 'u': f'buses-from-{slug(p_)}.html',
                   'en': f'Buses from {p_}',
                   'bn': f'{bp_} থেকে বাস' if bp_ else ''})
json.dump(search, open(f'{OUT}/search-index.json', 'w'), ensure_ascii=False, separators=(',', ':'))

open('sitemap.xml', 'w').write(sm)""")

# ---------------- K. stale print fix ----------------------------------------
rep("""print(json.dumps({'route_pages': len(route_meta), 'place_pages': len(top_places),""",
    """print(json.dumps({'route_pages': len(route_meta), 'place_pages': len(hub_places),""")

open(P, 'w', encoding='utf-8').write(src)
print('patch 2 applied OK')
