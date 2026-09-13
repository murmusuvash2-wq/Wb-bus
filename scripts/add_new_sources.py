#!/usr/bin/env python3
"""add_new_sources.py — Phase 2: add KTR + kolbusopedia + NBSTC + Shyamoli buses
to data/busjatri_data.json AFTER import_sbstc.py has run. Rebuilds routes/stops
in the repo's dict format, preserving nearest_station. Run from repo root."""
import json, re, csv, os
from collections import defaultdict
from datetime import date

SRC = "/scratch/work/scrape_all"
DATA = "data/busjatri_data.json"

def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', str(s or '').lower()).strip('-')

def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower().strip())

data = json.load(open(DATA))
buses = data['buses']
print(f"Phase 2 start: {len(buses)} buses (post-SBSTC import)")

existing_ids = set(b['id'] for b in buses)

# ---- existing dedup keys ----
def ex_key(b):
    o, d = norm(b.get('origin','')), norm(b.get('destination',''))
    m = re.search(r'\b([A-Z]{1,4}[-/]?\d{0,4}[A-Z]?)\b', b.get('bus_name','') or '')
    code = norm(m.group(1)) if m else ''
    return (o, d, code, norm(b.get('departure_time','')))

ex_keys = set(ex_key(b) for b in buses)
ex_od_nocode = set((norm(b.get('origin','')), norm(b.get('destination','')))
                   for b in buses if not re.search(r'\b([A-Z]{1,4}[-/]?\d{0,4}[A-Z]?)\b', b.get('bus_name','') or ''))

new_buses = []

# ---------- 1. KTR ----------
ktr = json.load(open(f"{SRC}/github_data/ktr_busdata.json"))
KIND_MAP = {'government':'WBTC','private':'Private','mini':'Mini Bus','metro':'Metro'}
def code_to_type(code, kind):
    c = code.upper()
    is_ac = c.startswith('AC') or c.startswith('VS') or 'AC' in c.split('-')[0]
    if kind == 'government':
        return 'Government - AC' if is_ac else 'Government - NON AC'
    if kind == 'mini':
        return 'Private - Mini Bus'
    return 'Private - NON AC'

seen_ktr = set()
n_ktr = 0
for r in ktr['routes']:
    if r.get('kind') == 'metro':
        continue
    stops = r.get('stops', [])
    if len(stops) < 2:
        continue
    code, kind = r['code'], r.get('kind','private')
    origin, dest = stops[0], stops[-1]
    dk = (norm(code), '|'.join(norm(s) for s in stops))
    if dk in seen_ktr:
        continue
    seen_ktr.add(dk)
    # dedup vs existing: same code + same OD
    if (norm(origin), norm(dest), norm(code), '') in ex_keys:
        continue
    bid = f"ktr-{slug(kind)}-{slug(code)}"
    n = 0
    while bid in existing_ids:
        n += 1
        bid = f"ktr-{slug(kind)}-{slug(code)}-{n}"
    existing_ids.add(bid)
    new_buses.append({
        'id': bid, 'bus_name': code, 'reg_no': '',
        'operator': KIND_MAP.get(kind, 'Private'),
        'bus_type': code_to_type(code, kind),
        'origin': origin, 'destination': dest,
        'departure_time': '', 'arrival_time': '',
        'contact_number': 'Not Available !', 'depot_name': '',
        'route': f"{origin} - {dest}",
        'stoppages': [{'no': i+1, 'name': s, 'up_time': '', 'down_time': ''} for i, s in enumerate(stops)],
        'source': 'kolkata-travel-router (GitHub)',
        'total_stoppages': len(stops),
        'detail_url': 'https://kolkata-bus.vercel.app/',
    })
    n_ktr += 1
print(f"KTR added: {n_ktr}")

# ---------- 2. kolbusopedia ----------
kb = json.load(open(f"{SRC}/kolbusopedia_missing.json"))
n_kb = 0
for r in kb:
    if len(r['stops']) < 2:
        continue
    o, d = r['from'], r['to']
    if (norm(o), norm(d), norm(r['code']), '') in ex_keys:
        continue
    bid = f"kbop-{slug(r['code'])}"
    n = 0
    while bid in existing_ids:
        n += 1
        bid = f"kbop-{slug(r['code'])}-{n}"
    existing_ids.add(bid)
    new_buses.append({
        'id': bid, 'bus_name': r['code'], 'reg_no': '',
        'operator': r.get('operator','WBTC'),
        'bus_type': 'Government - AC' if r.get('ac') else 'Government - NON AC',
        'origin': o, 'destination': d,
        'departure_time': '', 'arrival_time': '',
        'contact_number': 'Not Available !', 'depot_name': '',
        'route': f"{o} - {d}",
        'stoppages': [{'no': i+1, 'name': s, 'up_time': '', 'down_time': ''} for i, s in enumerate(r['stops'])],
        'source': 'kolbusopedia.com',
        'total_stoppages': len(r['stops']),
        'detail_url': 'https://www.kolbusopedia.com/bus-routes-government',
    })
    n_kb += 1
print(f"kolbusopedia added: {n_kb}")

# ---------- 3. NBSTC ----------
n_nb = 0
nb_seen = set()
for csvf in ['nbstc_page1.csv', 'nbstc_extra.csv']:
    path = f"{SRC}/{csvf}"
    if not os.path.exists(path):
        continue
    for line in open(path):
        line = line.strip()
        if '|' not in line:
            continue
        parts = line.split('|')
        if len(parts) < 3:
            continue
        origin, dest, time = parts[0], parts[1], parts[2]
        via = parts[3] if len(parts) > 3 else ''
        k = (norm(origin), norm(dest), norm(time))
        if k in nb_seen:
            continue
        # dedup vs existing buses: try code variants 'nbstc' and ''
        if ((norm(origin), norm(dest), 'nbstc', norm(time)) in ex_keys
                or (norm(origin), norm(dest), '', norm(time)) in ex_keys):
            continue
        nb_seen.add(k)
        stops = [origin] + ([via] if via else []) + [dest]
        bid = f"nbstc-in-{slug(origin)}-{slug(dest)}-{n_nb}"
        while bid in existing_ids:
            n_nb += 1
            bid = f"nbstc-in-{slug(origin)}-{slug(dest)}-{n_nb}"
        existing_ids.add(bid)
        new_buses.append({
            'id': bid, 'bus_name': f"NBSTC {origin}-{dest}", 'reg_no': '',
            'operator': 'NBSTC', 'bus_type': 'Government',
            'origin': origin, 'destination': dest,
            'departure_time': time, 'arrival_time': '',
            'contact_number': '03582-222576', 'depot_name': origin,
            'route': f"{origin} - {dest}",
            'stoppages': [{'no': i+1, 'name': s, 'up_time': time if i==0 else '', 'down_time': ''} for i, s in enumerate(stops)],
            'source': 'nbstc.in',
            'total_stoppages': len(stops),
            'detail_url': 'https://nbstc.in/bus-routes.php',
        })
        n_nb += 1
print(f"NBSTC added: {n_nb}")

# ---------- 4. Shyamoli ----------
n_sh = 0
for line in open(f"{SRC}/shyamoli_wb.csv"):
    line = line.strip()
    if '|' not in line:
        continue
    parts = line.split('|')
    if len(parts) < 4:
        continue
    origin, dest, time, desc = parts[0], parts[1], parts[2], parts[3]
    is_ac = 'AC' in desc or 'Volvo' in desc
    bid = f"shyamoli-{slug(origin)}-{slug(dest)}-{n_sh}"
    while bid in existing_ids:
        n_sh += 1
        bid = f"shyamoli-{slug(origin)}-{slug(dest)}-{n_sh}"
    existing_ids.add(bid)
    new_buses.append({
        'id': bid, 'bus_name': 'Shyamoli Paribahan', 'reg_no': '',
        'operator': 'Shyamoli Paribahan',
        'bus_type': 'Private - AC Volvo' if is_ac else 'Private - NON AC',
        'origin': origin, 'destination': dest,
        'departure_time': time, 'arrival_time': '',
        'contact_number': '8336003361', 'depot_name': origin,
        'route': f"{origin} - {dest}",
        'stoppages': [{'no': 1, 'name': origin, 'up_time': time, 'down_time': ''},
                      {'no': 2, 'name': dest, 'up_time': '', 'down_time': ''}],
        'source': 'shyamolibus.com',
        'total_stoppages': 2,
        'detail_url': 'https://www.shyamolibus.com/',
    })
    n_sh += 1
print(f"Shyamoli added: {n_sh}")

buses.extend(new_buses)
print(f"Total after adds: {len(buses)}")

# ---------- Rebuild routes/stops in repo dict format, preserve nearest_station ----------
old_stops = data.get('stops') or {}
routes_map, stops_map = defaultdict(list), defaultdict(list)
for b in buses:
    if b.get('origin') and b.get('destination') and b['origin'] != '—' and b['destination'] != '—':
        routes_map[f"{slug(b['origin'])}-{slug(b['destination'])}"].append(b['id'])
    seen = set()
    for s in b.get('stoppages') or []:
        n = s.get('name')
        if n and n not in seen:
            seen.add(n)
            stops_map[n].append(b['id'])

routes_out = {}
for b in buses:
    k = f"{slug(b.get('origin'))}-{slug(b.get('destination'))}"
    if k in routes_map and k not in routes_out:
        routes_out[k] = {'from': b['origin'], 'to': b['destination'],
                         'bus_ids': list(dict.fromkeys(routes_map[k]))}
stops_out = {n: {'name': n, 'bus_ids': list(dict.fromkeys(ids))}
             for n, ids in stops_map.items()}
preserved = 0
for n, s in stops_out.items():
    old = old_stops.get(n, {})
    if old.get('nearest_station'):
        s['nearest_station'] = old['nearest_station']
        preserved += 1

data['routes'] = routes_out
data['stops'] = stops_out
data['meta'].update({
    'total_buses': len(buses),
    'total_routes': len(routes_out),
    'total_stops': len(stops_out),
    'version': '3.0.0',
    'last_updated': str(date.today()),
    'sources': ['bussathi.in','wbbus.in','wbbustime.com','whereismybus.in',
                'kolkata-travel-router (GitHub)','kolbusopedia.com','nbstc.in',
                'shyamolibus.com','SBSTC (govt)','WBTC (govt)'],
})
json.dump(data, open(DATA, 'w'), ensure_ascii=False, separators=(',', ':'))
print(f"FINAL: {len(buses)} buses, {len(routes_out)} routes, {len(stops_out)} stops")
print(f"nearest_station preserved: {preserved}")
