#!/usr/bin/env python3
"""Apply via system to gen_seo_pages.py. Reads via_func.py at runtime."""

P = 'scripts/gen_seo_pages.py'
src = open(P, encoding='utf-8').read()

if 'via_stops' in src:
    print('generator already has via system')
    exit(0)

via_func = open('scripts/patches/via_func.py', encoding='utf-8').read()

# 1. Insert via computation after route_meta
idx = src.find('# HTML SHELL')
old1 = src[src.rfind('route_meta[(o, t)] = buses', 0, idx):idx]
compute = '''

# VIA COMBOS (computed from stoppages - fully data-driven)
# ------------------------------------------------------------

def via_stops(o, t, bs, min_buses=3, top=2):
    counts = Counter()
    for b in bs:
        seq = [x for x in [clean_text(b.get("origin"))] + [clean_text(s.get("name")) for s in (b.get("stoppages") or [])] + [clean_text(b.get("destination"))] if x and x != "—"]
        io = next((i for i, x in enumerate(seq) if x == o), None)
        it = next((i for i in range(len(seq) - 1, -1, -1) if seq[i] == t), None)
        if io is None or it is None or io >= it:
            continue
        for k in range(io + 1, it):
            cc = seq[k]
            if cc and cc != o and cc != t:
                counts[cc] += 1
    return [cc for cc, nn in counts.most_common() if nn >= min_buses][:top]


VIA = {}

for (o_, t_), bs_ in route_meta.items():
    vv_ = via_stops(o_, t_, bs_)
    if vv_:
        VIA[(o_, t_)] = vv_

'''
src = src.replace(old1, old1 + compute, 1)

# 2. Insert via page function before os.makedirs
anchor2 = '''os.makedirs(OUT, exist_ok=True)

sitemap_urls = []
written = []'''
src = src.replace(anchor2, via_func + chr(10) + anchor2, 1)

# 3. Insert via loop after place pages
anchor3 = '''    written.append(filename)


# ------------------------------------------------------------
# ROUTE INDEX'''
via_loop = '''    written.append(filename)

# Via pages (fully data-driven - computed from stoppages)
via_count = 0
for (origin, destination), vv_ in sorted(VIA.items(), key=lambda kv: -len(route_meta[kv[0]])):
    for via_stop in vv_:
        via_filename, via_content = generate_via_page(origin, destination, via_stop, route_meta[(origin, destination)])
        if via_filename is None:
            continue
        via_path = os.path.join(OUT, via_filename)
        with open(via_path, "w", encoding="utf-8") as f:
            f.write(via_content)
        sitemap_urls.append(f"{BASE}/bus-time-table/{via_filename}")
        written.append(via_filename)
        via_count += 1


# ------------------------------------------------------------
# ROUTE INDEX'''
src = src.replace(anchor3, via_loop, 1)

# 4. Stats
src = src.replace('"place_pages": len(top_places),',
    '"place_pages": len(top_places),' + chr(10) + '            "via_pages": via_count,', 1)

import ast
ast.parse(src)
open(P, 'w', encoding='utf-8').write(src)
print('via system applied to generator')
