#!/usr/bin/env python3
"""Generate static SEO pages for BusJatri from busjatri_data.json.
Pages: bus-time-table/<from>-to-<to>.html (routes >=2 buses), buses-from-<place>.html,
index, sitemap.xml, robots.txt. All paths relative so they work on any host."""
import json, re, os, html
from collections import Counter, defaultdict
from datetime import datetime

import os
DATA = 'data/busjatri_data.json'
OUT = 'bus-time-table'
BASE = os.environ.get('SITE_BASE', 'https://murmusuvash2-wq.github.io/Wb-bus').rstrip('/')
SITE_NAME = 'BusJatri'
LASTMOD = datetime.now().strftime('%Y-%m-%d')

d = json.load(open(DATA))
BUSES = d['buses']

# Bengali names for major places (confident mappings only)
BN = {
 'Bankura':'বাঁকুড়া','Digha':'দীঘা','Kolkata':'কলকাতা','Medinipur':'মেদিনীপুর',
 'Bardhaman':'বর্ধমান','Burdwan':'বর্ধমান','Kharagpur':'খড়্গপুর','Siliguri':'শিলিগুড়ি',
 'Cooch Behar':'কোচবিহার','Asansol':'আসানসোল','Durgapur':'দুর্গাপুর','Purulia':'পুরুলিয়া',
 'Jhargram':'ঝাড়গ্রাম','Contai':'কাঁথি','Tamluk':'তমলুক','Bishnupur':'বিষ্ণুপুর',
 'Khatra':'খাতড়া','Alipurduar':'আলিপুরদুয়ার','Dinhata':'দিনহাটা','Mathabhanga':'মাথাভাঙ্গা',
 'Ghatal':'ঘাটাল','Nabadwip':'নবদ্বীপ','Arambagh':'আরামবাগ','Manbazar':'মানবাজার',
 'Tarkeshwar':'তারকেশ্বর','Mecheda':'মেছেদা','Haldia':'হলদিয়া','Baruipur':'বারুইপুর',
 'Esplanade':'এসপ্ল্যানেড','Howrah':'হাওড়া','Ranaghat':'রানাঘাট','Krishnanagar':'কৃষ্ণনগর',
 'Malda':'মালদা','Raiganj':'রায়গঞ্জ','Balurghat':'বালুরঘাট','Suri':'সিউড়ি',
 'Sainthia':'সাঁইথিয়া','Bolpur':'বোলপুর','Kalna':'কালনা','Guskara':'গুসকরা',
 'Katwa':'কাটোয়া','Bandel':'বান্দেল','Chandannagar':'চন্দননগর','Kalyani':'কল্যাণী',
 'Barasat':'বারাসাত','Barrackpore':'ব্যারাকপুর','Dunlop':'ডানলপ','Garia':'গড়িয়া',
 'Tarakeswar':'তারকেশ্বর','Jangipur':'জঙ্গীপুর','Berhampore':'বহরমপুর',
 'Berhampur':'বহরমপুর','Salar':'সালার','Kirnahar':'কীর্ণাহার','Ilam Bazar':'ইলাম বাজার',
}

def slug(s): return re.sub(r'[^a-z0-9]+', '-', str(s).lower()).strip('-')
def esc(s): return html.escape(str(s or ''), quote=True)

def parse_time(t):
    if not t: return None
    m = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)?', str(t).strip(), re.I)
    if not m: return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), (m.group(3) or '').upper()
    if ap == 'PM' and h < 12: h += 12
    if ap == 'AM' and h == 12: h = 0
    return h * 60 + mi

def fmt_dur(mins):
    h, m = divmod(int(mins), 60)
    return f'{h}h {m:02d}m' if h else f'{m}m'

def route_pairs():
    fwd = defaultdict(list)
    for b in BUSES:
        o, t = b.get('origin'), b.get('destination')
        if o and t and o != '—' and t != '—':
            fwd[(o, t)].append(b)
    return fwd

FWD = route_pairs()
# bidirectional groups with >= 2 buses
groups = defaultdict(list)
for (o, t), bs in FWD.items():
    groups[tuple(sorted([o, t]))].extend(bs)
groups = {k: v for k, v in groups.items() if len(v) >= 2}

# buses for a directed pair (exact direction)
def buses_for(o, t):
    return FWD.get((o, t), [])

def bn(name):
    return BN.get(str(name).strip())

def bn_route(o, t):
    bo, bt = bn(o), bn(t)
    return f'{bo} থেকে {bt}' if bo and bt else None

def bus_row(b):
    nm = esc(b.get('bus_name') or '—')
    bt = esc(b.get('bus_type') or '')
    dep = esc(b.get('departure_time') or '—')
    arr = esc(b.get('arrival_time') or '—')
    op = esc((b.get('operator') or '').replace('—', '')) or '—'
    stops = b.get('total_stoppages') or len(b.get('stoppages') or [])
    return f'<tr><td><strong>{nm}</strong></td><td>{bt}</td><td>{dep}</td><td>{arr}</td><td>{op}</td><td>{stops}</td></tr>'

def bus_type_label(bt):
    g = (bt or '').lower()
    if 'gov' in g or 'sbstc' in g or 'nbstc' in g or 'wbtc' in g: return 'Government (SBSTC/WBTC/NBSTC)'
    if 'ac' in g and 'non' not in g: return 'AC bus'
    if g: return 'Private non-AC bus'
    return 'Bus'

CSS = '../css/style.css'
def shell(title, desc, canonical, body, extra_schema=''):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#b8791f">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b8791f' stroke-width='2'%3E%3Cpath d='M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10'/%3E%3Cpath d='M4 16h16'/%3E%3C/svg%3E">
<link rel="stylesheet" href="{CSS}">
{extra_schema}
</head>
<body>
<header class="header"><div class="container header-inner">
<div class="logo"><svg class="icon" viewBox="0 0 24 24" style="width:1.35rem;height:1.35rem;color:var(--amber)"><path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"/><path d="M4 16h16"/></svg>Bus<span>Jatri</span></div>
<nav style="display:flex;gap:14px;font-size:14px"><a href="../index.html">Home</a> <a href="./">All Routes</a></nav>
</div></header>
<main class="container" style="padding-top:24px;padding-bottom:48px;max-width:860px">
{body}
</main>
<footer class="footer"><div class="container">
<p><strong>BusJatri</strong> — West Bengal bus timetable. Timings can change; verify with the operator or depot before travelling. Not affiliated with any transport corporation.</p>
</div></footer>
</body>
</html>'''

def faq_schema(faqs):
    items = ', '.join(
        json.dumps({'@type': 'Question', 'name': q,
                    'acceptedAnswer': {'@type': 'Answer', 'text': a}}, ensure_ascii=False)
        for q, a in faqs)
    return f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{items}]}}</script>'

def breadcrumb(items):
    lst = ', '.join(json.dumps(
        {'@type': 'ListItem', 'position': i + 1, 'name': n,
         'item': f'{BASE}{u}' if u else n}, ensure_ascii=False)
        for i, (n, u) in enumerate(items))
    return f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{lst}]}}</script>'

os.makedirs(OUT, exist_ok=True)
sitemap = []
written = []

# ---------- route pages ----------
route_meta = {}
for (a, b) in sorted(groups):
    # canonical direction: the one with more buses; reverse page too
    for o, t in [(a, b), (b, a)]:
        bs = buses_for(o, t)
        if not bs:
            continue
        route_meta[(o, t)] = bs

for (o, t), bs in route_meta.items():
    fname = f'{slug(o)}-to-{slug(t)}.html'
    bn_r = bn_route(o, t)
    title = f'{o} to {t} Bus Time Table' + (f' | {bn_r}' if bn_r else '')
    times = sorted(x for x in (parse_time(b.get('departure_time')) for b in bs) if x is not None)
    first = fmt_time = None
    firstm, lastm = (min(times), max(times)) if times else (None, None)
    def hhmm(m): return f'{((m//60)%12 or 12)}:{m%60:02d} {"AM" if (m//60)<12 else "PM"}'
    n = len(bs)
    ops = sorted({(b.get('operator') or '').strip() for b in bs if (b.get('operator') or '').strip() and b['operator'] != '—'})
    # stoppages aggregation
    stp = Counter()
    for b in bs:
        seen = set()
        for s in (b.get('stoppages') or []):
            nm = s.get('name')
            if nm and nm not in seen:
                seen.add(nm); stp[nm] += 1
    major = [s for s, c in stp.most_common(8) if c >= max(2, len(bs)//3)]
    # durations
    durs = []
    for b in bs:
        dep, arr = parse_time(b.get('departure_time')), parse_time(b.get('arrival_time'))
        if dep is not None and arr is not None:
            dd = arr - dep if arr > dep else arr + 1440 - dep
            if 0 < dd < 900: durs.append(dd)
    med_dur = sorted(durs)[len(durs)//2] if durs else None

    q_first = hhmm(firstm) if firstm is not None else '—'
    q_last = hhmm(lastm) if lastm is not None else '—'
    faqs = [
      (f'What is the first bus from {o} to {t}?',
       f'The first bus from {o} to {t} departs at {q_first}. Timings may vary by day — always verify before travelling.' if firstm is not None
       else f'Departure times for this route vary. See the full timetable above for all {n} buses from {o} to {t}.'),
      (f'What is the last bus from {o} to {t}?',
       f'The last bus from {o} to {t} departs at {q_last}.' if lastm is not None else 'See the timetable above for the latest departures.'),
      (f'How many buses run from {o} to {t}?',
       f'Around {n} bus services operate between {o} and {t} daily, including both directions. '
       + (f'Major operators: {", ".join(ops[:4])}.' if ops else '')),
    ]
    if med_dur:
        faqs.append((f'How long does the bus take from {o} to {t}?',
                     f'The journey takes approximately {fmt_dur(med_dur)} by bus, depending on stops, traffic and bus type.'))
    faqs.append((f'Are there government (SBSTC/WBTC/NBSTC) buses from {o} to {t}?',
                 'This route is served by both government and private operators where available. Check the Operator column in the timetable above.'))

    intro_bn = f'{bn_r} — সম্পূর্ণ আপডেটেড বাসের সময়সূচী।' if bn_r else ''
    desc = (f'{o} to {t} bus time table: {n} buses with departure & arrival timings, operators, stoppages. '
            f'First bus {q_first}, last bus {q_last}.')[:300]

    body = f'''
<nav style="font-size:13px;color:var(--ink-dim);margin-bottom:14px"><a href="../index.html">Home</a> › <a href="./">Bus Time Table</a> › {esc(o)} to {esc(t)}</nav>
<h1 style="font-size:1.8rem;line-height:1.25">{esc(o)} to {esc(t)} Bus Time Table{f' ({esc(bn_r)})' if bn_r else ''}</h1>
<p style="margin:12px 0 20px">Complete {esc(o)} to {esc(t)} bus timetable — all {n} bus services with timings, operators and stoppages, updated from public sources. {esc(intro_bn)}</p>
<div class="stats" style="display:flex;gap:14px;flex-wrap:wrap;margin-bottom:26px">
  <div class="stat" style="background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:12px 18px"><div style="font-size:1.4rem;font-weight:700">{n}</div><div>{esc(o)}–{esc(t)} buses</div></div>
  <div class="stat" style="background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:12px 18px"><div style="font-size:1.4rem;font-weight:700">{q_first}</div><div>First bus</div></div>
  <div class="stat" style="background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:12px 18px"><div style="font-size:1.4rem;font-weight:700">{q_last}</div><div>Last bus</div></div>
  {'<div class="stat" style="background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:12px 18px"><div style="font-size:1.4rem;font-weight:700">'+fmt_dur(med_dur)+'</div><div>Approx. duration</div></div>' if med_dur else ''}
</div>
<h2 style="font-size:1.25rem;margin:24px 0 12px">{esc(o)} to {esc(t)} — All Bus Timings</h2>
<div style="overflow-x:auto">
<table style="width:100%;border-collapse:collapse;font-size:14px">
<thead><tr style="text-align:left;border-bottom:2px solid var(--border)">
<th style="padding:8px">Bus</th><th style="padding:8px">Type</th><th style="padding:8px">Departure</th><th style="padding:8px">Arrival</th><th style="padding:8px">Operator</th><th style="padding:8px">Stops</th>
</tr></thead>
<tbody>
{''.join(bus_row(b) for b in sorted(bs, key=lambda x: parse_time(x.get('departure_time')) if parse_time(x.get('departure_time')) is not None else 9999))}
</tbody></table></div>
<p style="font-size:12.5px;color:var(--ink-dim);margin-top:8px">Also see: <a href="{slug(t)}-to-{slug(o)}.html">{esc(t)} to {esc(o)} bus time table</a> (return direction).</p>
{'<h2 style="font-size:1.25rem;margin:28px 0 12px">Major Stoppages on this Route</h2><p>' + ' · '.join(esc(s) for s in major) + '</p>' if major else ''}
<h2 style="font-size:1.25rem;margin:28px 0 12px">FAQ — {esc(o)} to {esc(t)} Bus</h2>
''' + ''.join(f'<details style="margin-bottom:10px"><summary style="cursor:pointer;font-weight:600">{esc(q)}</summary><p style="margin:8px 0 4px">{esc(a)}</p></details>' for q, a in faqs)

    # related routes
    rel = [(oo, tt) for (oo, tt) in route_meta if oo == o and tt != t][:6]
    if rel:
        body += '<h2 style="font-size:1.25rem;margin:28px 0 12px">More buses from ' + esc(o) + '</h2><p>' + \
            ' · '.join(f'<a href="{slug(oo)}-to-{slug(tt)}.html">{esc(oo)} to {esc(tt)}</a>' for oo, tt in rel) + '</p>'

    schema = faq_schema(faqs) + '\n' + breadcrumb([('Home', '/'), ('Bus Time Table', '/bus-time-table/'),
                                                   (f'{o} to {t}', f'/bus-time-table/{fname}')])
    open(f'{OUT}/{fname}', 'w').write(shell(title, desc, f'{BASE}/bus-time-table/{fname}', body, schema))
    sitemap.append(f'{BASE}/bus-time-table/{fname}')
    written.append(fname)

# ---------- place pages (buses from X) ----------
place_buses = defaultdict(list)
for b in BUSES:
    o = b.get('origin')
    if o and o != '—':
        place_buses[o].append(b)
top_places = sorted(place_buses, key=lambda p: -len(place_buses[p]))[:30]

for p in top_places:
    bs = place_buses[p]
    n = len(bs)
    bn_p = bn(p)
    dests = Counter(b['destination'] for b in bs if b.get('destination') and b['destination'] != '—')
    top_dests = dests.most_common(12)
    fname = f'buses-from-{slug(p)}.html'
    title = f'Buses from {p}' + (f' | {bn_p} থেকে বাস' if bn_p else '') + ' — Timetable & Routes'
    desc = f'All buses from {p}: {n} bus services with timings and destinations across West Bengal. Popular: ' + ', '.join(x for x, _ in top_dests[:3]) + '.'
    links = ' · '.join(f'<a href="{slug(p)}-to-{slug(t)}.html">{esc(p)} to {esc(t)} bus</a>' for t, c in top_dests if (p, t) in route_meta)
    body = f'''
<nav style="font-size:13px;color:var(--ink-dim);margin-bottom:14px"><a href="../index.html">Home</a> › <a href="./">Bus Time Table</a> › Buses from {esc(p)}</nav>
<h1 style="font-size:1.8rem">Buses from {p}{f' ({esc(bn_p)} থেকে বাস)' if bn_p else ''}</h1>
<p style="margin:12px 0 18px">{n} bus services originate from {esc(p)}. Popular destinations: {', '.join(esc(t) for t, _ in top_dests[:8])}.</p>
<h2 style="font-size:1.25rem;margin:22px 0 12px">Top routes from {esc(p)}</h2>
<p>{links or 'See the search on the ' + '<a href="../index.html">home page</a>.'}</p>
<h2 style="font-size:1.25rem;margin:22px 0 12px">All destinations from {esc(p)} ({len(dests)})</h2>
<p style="line-height:1.9">{' · '.join(f'{esc(t)} ({c})' for t, c in dests.most_common())}</p>'''
    schema = breadcrumb([('Home', '/'), ('Bus Time Table', '/bus-time-table/'), (f'Buses from {p}', f'/bus-time-table/{fname}')])
    open(f'{OUT}/{fname}', 'w').write(shell(title, desc, f'{BASE}/bus-time-table/{fname}', body, schema))
    sitemap.append(f'{BASE}/bus-time-table/{fname}')
    written.append(fname)

# ---------- index page ----------
by_place = defaultdict(list)
for (o, t) in route_meta:
    by_place[o].append((o, t))
idx_rows = ''.join(
    f'<h2 style="margin:22px 0 10px;font-size:1.15rem">{esc(p)} ({len(routes)})</h2><p style="line-height:1.9">'
    + ' · '.join(f'<a href="{slug(o)}-to-{slug(t)}.html">{esc(o)} to {esc(t)}</a>' for o, t in sorted(routes))
    + '</p>'
    for p, routes in sorted(by_place.items(), key=lambda kv: -len(kv[1])))
places_links = ' · '.join(f'<a href="buses-from-{slug(p)}.html">Buses from {esc(p)}</a>' for p in top_places[:20])
body = f'''
<h1 style="font-size:1.8rem">West Bengal Bus Time Tables — All Routes</h1>
<p style="margin:12px 0 20px">{len(route_meta)} route timetables with {len(BUSES)} buses across West Bengal — SBSTC, WBTC, NBSTC and private operators. পশ্চিমবঙ্গের সবচেয়ে বড় বাস টাইম টেবিল।</p>
<p style="margin-bottom:8px"><strong>Popular:</strong> {places_links}</p>
{idx_rows}'''
schema = f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebSite","name":"BusJatri","url":"{BASE}"}}</script>'
open(f'{OUT}/index.html', 'w').write(shell('West Bengal Bus Time Tables — All Routes | BusJatri',
    f'Complete bus timetables for {len(route_meta)} routes across West Bengal with timings, operators and stoppages.',
    f'{BASE}/bus-time-table/', body, schema))

# ---------- sitemap & robots ----------
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
sm += f'<url><loc>{BASE}/</loc><lastmod>{LASTMOD}</lastmod><priority>1.0</priority></url>\n'
for u in [f'{BASE}/bus-time-table/'] + sitemap:
    sm += f'<url><loc>{u}</loc><lastmod>{LASTMOD}</lastmod><priority>0.8</priority></url>\n'
sm += '</urlset>'
open('sitemap.xml', 'w').write(sm)
open('robots.txt', 'w').write(f'User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n')

print(json.dumps({'route_pages': len(route_meta), 'place_pages': len(top_places),
                  'total_pages': len(written) + 1, 'sitemap_urls': len(sitemap) + 1}))
