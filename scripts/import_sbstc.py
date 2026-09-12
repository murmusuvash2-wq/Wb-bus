#!/usr/bin/env python3
"""Import SBSTC routes from the official transport.wb.gov.in PDF into
data/busjatri_data.json. Creates one bus entry per departure time, with fares.
Run from repo root (needs: pip install pdfplumber)."""
import json, re, sys
from collections import defaultdict
from datetime import date

PDF_URL = 'https://transport.wb.gov.in/wp-content/uploads/2016/09/RouteTimeTableFareSBSTC.pdf'
PDF_FILE = sys.argv[1] if len(sys.argv) > 1 else 'sbstc.pdf'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'sbstc_buses.json'

def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', str(s or '').lower()).strip('-')

def to_12h(t):
    """'13.05' -> '1:05 PM'"""
    h, m = t.split('.')
    h, m = int(h), int(m)
    ap = 'PM' if h >= 12 else 'AM'
    h12 = h % 12 or 12
    return f'{h12}:{m:02d} {ap}'

def parse_times(cell):
    """Extract all dotted times from a cell like '4.50/5.45/6.15'."""
    if not cell:
        return []
    return re.findall(r'\d{1,2}\.\d{2}', str(cell))

def parse_fare(cell):
    if not cell:
        return ''
    m = re.search(r'R[sS]\.?\s*([\d]+(?:\.\d+)?)', str(cell))
    return f'Rs. {m.group(1)}' if m else ''

def split_name(name):
    """'PURULIA TO KOLKATA VIA BANKURA' -> (origin, dest, [via...])"""
    via = []
    m = re.match(r'^(.*?)\s+VIA\s+(.*)$', name, re.I)
    if m:
        name, via_part = m.group(1), m.group(2)
        via = [v.strip(' .,') for v in re.split(r',|AND', via_part) if v.strip(' .,')]
    parts = re.split(r'\s+TO\s+', name, maxsplit=1)
    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
        return None
    return parts[0].strip(), parts[1].strip(), via

def make_buses(routes):
    """routes: list of dicts {name, length, up[], down[], fare}"""
    buses = []
    used_ids = set()
    def make_id(base):
        n = 0
        while f'{base}-{n}' in used_ids:
            n += 1
        bid = f'{base}-{n}'
        used_ids.add(bid)
        return bid

    for r in routes:
        sp = split_name(r['name'])
        if not sp:
            continue
        o, t, via = sp
        o, t = o.title(), t.title()
        via = [v.title() for v in via]
        ac = bool(re.search(r'\bA\.?\s?C\b', r['name'], re.I))
        btype = 'Government - SBSTC AC' if ac else 'Government - SBSTC'
        stops_up = [{'no': 1, 'name': o, 'up_time': '', 'down_time': ''}] + \
                   [{'no': i + 2, 'name': v, 'up_time': '', 'down_time': ''} for i, v in enumerate(via)] + \
                   [{'no': len(via) + 2, 'name': t, 'up_time': '', 'down_time': ''}]
        stops_dn = list(reversed([dict(s) for s in stops_up]))
        for i, s in enumerate(stops_dn):
            s['no'] = i + 1
        for dep in r['up']:
            buses.append({
                'id': make_id(f'sbstc-{slug(o)}-{slug(t)}'),
                'bus_name': f'SBSTC {o}-{t}' + (' (AC)' if ac else ''),
                'reg_no': '', 'operator': 'SBSTC',
                'bus_type': btype, 'origin': o.title(), 'destination': t.title(),
                'departure_time': to_12h(dep), 'arrival_time': '',
                'contact_number': 'Not Available !', 'depot_name': o.title(),
                'route': f"{o.title()} - {t.title()}",
                'stoppages': [dict(s) for s in stops_up],
                'source': 'SBSTC (govt)', 'total_stoppages': len(stops_up),
                'fare': r['fare'], 'detail_url': PDF_URL,
            })
        for dep in r['down']:
            buses.append({
                'id': make_id(f'sbstc-{slug(t)}-{slug(o)}'),
                'bus_name': f'SBSTC {t}-{o}' + (' (AC)' if ac else ''),
                'reg_no': '', 'operator': 'SBSTC',
                'bus_type': btype, 'origin': t.title(), 'destination': o.title(),
                'departure_time': to_12h(dep), 'arrival_time': '',
                'contact_number': 'Not Available !', 'depot_name': t.title(),
                'route': f"{t.title()} - {o.title()}",
                'stoppages': [dict(s) for s in stops_dn],
                'source': 'SBSTC (govt)', 'total_stoppages': len(stops_dn),
                'fare': r['fare'], 'detail_url': PDF_URL,
            })
    return buses

def parse_pdf(path):
    import pdfplumber
    routes = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in (page.extract_tables() or []):
                for row in table:
                    cells = [(c or '').replace('\n', ' ').strip() for c in row]
                    if len(cells) < 5:
                        continue
                    # find sl.no (int) and route name (CAPS)
                    joined = ' | '.join(cells)
                    m = re.match(r'^(\d{1,3})$', cells[0])
                    if not m:
                        continue
                    name = cells[1]
                    if not name or not re.match(r'^[A-Z][A-Z0-9 .,\'&()\-]*$', name):
                        continue
                    up = parse_times(cells[3] if len(cells) > 3 else '')
                    down = parse_times(cells[4] if len(cells) > 4 else '')
                    fare = parse_fare(cells[5] if len(cells) > 5 else '')
                    if not up and not down:
                        continue
                    routes.append({'name': name, 'up': up, 'down': down, 'fare': fare})
    return routes

def merge_into_data(buses):
    data = json.load(open('data/busjatri_data.json'))
    data['buses'] = [b for b in data['buses'] if b.get('source') != 'SBSTC (govt)']
    data['buses'].extend(buses)
    # rebuild indexes
    routes_map, stops_map = defaultdict(list), defaultdict(list)
    for b in data['buses']:
        if b.get('origin') and b.get('destination') and b['origin'] != '—' and b['destination'] != '—':
            routes_map[f"{slug(b['origin'])}-{slug(b['destination'])}"].append(b['id'])
        seen = set()
        for s in b.get('stoppages') or []:
            n = s.get('name')
            if n and n not in seen:
                seen.add(n)
                stops_map[n].append(b['id'])
    routes_out = {}
    for b in data['buses']:
        k = f"{slug(b.get('origin'))}-{slug(b.get('destination'))}"
        if k in routes_map and k not in routes_out:
            routes_out[k] = {'from': b['origin'], 'to': b['destination'],
                            'bus_ids': list(dict.fromkeys(routes_map[k]))}
    stops_out = {n: {'name': n, 'bus_ids': list(dict.fromkeys(ids))}
                 for n, ids in stops_map.items()}
    # preserve nearest_station from old stops
    for n, s in stops_out.items():
        old = (data.get('stops') or {}).get(n, {})
        if old.get('nearest_station'):
            s['nearest_station'] = old['nearest_station']
    data['routes'] = routes_out
    data['stops'] = stops_out
    data['meta'].update({'total_buses': len(data['buses']),
                         'total_routes': len(routes_out),
                         'total_stops': len(stops_out),
                         'last_updated': str(date.today())})
    json.dump(data, open('data/busjatri_data.json', 'w'),
              ensure_ascii=False, separators=(',', ':'))
    print(f"merged: {len(data['buses'])} buses, {len(routes_out)} routes, {len(stops_out)} stops")

if __name__ == '__main__':
    routes = parse_pdf(PDF_FILE)
    print(f'parsed routes: {len(routes)}')
    assert len(routes) >= 50, f'only {len(routes)} routes parsed - aborting'
    buses = make_buses(routes)
    assert len(buses) >= 100, f'only {len(buses)} buses generated - aborting'
    json.dump(buses, open(OUT, 'w'), ensure_ascii=False)
    print(f'generated {len(buses)} SBSTC buses -> {OUT}')
    for b in buses[:2]:
        print('SAMPLE', json.dumps(b, ensure_ascii=False)[:300])
    if '--merge' in sys.argv:
        merge_into_data(buses)
