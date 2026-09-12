#!/usr/bin/env python3
"""Enrich WBTC (Kolkata) buses with stoppages from wbtconline.in route table.
Run from repo root (stdlib only)."""
import json, re, sys, urllib.request
from collections import defaultdict
from datetime import date

URL = 'https://wbtconline.in/wbtc-city-bus-routes'
UA = {'User-Agent': 'Mozilla/5.0 (compatible; BusJatriUpdater/1.0; +https://github.com/murmusuvash2-wq/Wb-bus)'}

def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', str(s or '').lower()).strip('-')

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode('utf-8', 'replace')

def parse_table(html):
    rows = []
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.S | re.I):
        cells = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', c)).strip()
                 for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S | re.I)]
        if len(cells) >= 4 and cells[1] and cells[2] and \
           re.match(r'^[A-Za-z0-9][A-Za-z0-9 \-./()]*$', cells[1]) and \
           not cells[1].lower().startswith('route'):
            rows.append({'no': cells[1], 'origin': cells[2],
                         'dest': cells[3], 'stops_raw': cells[4] if len(cells) > 4 else ''})
    return rows

def main():
    html = get(URL)
    rows = parse_table(html)
    print(f'WBTC routes fetched: {len(rows)}', flush=True)
    assert len(rows) >= 50, f'only {len(rows)} routes - aborting'

    table = {}
    for r in rows:
        table[re.sub(r'[^A-Z0-9]', '', r['no'].upper())] = r

    data = json.load(open('data/busjatri_data.json'))
    matched = 0
    for b in data['buses']:
        if b.get('source') != 'WBTC (govt)':
            continue
        nm = re.sub(r'\s+', ' ', b.get('bus_name') or '').strip()
        m = re.match(r'^WBTC\s+(.+)$', nm, re.I)
        if not m:
            continue
        rn = re.sub(r'[^A-Z0-9]', '', m.group(1).upper())
        row = table.get(rn)
        if not row:
            cands = sorted([k for k in table if k.startswith(rn) or rn.startswith(k)], key=len)
            row = table[cands[0]] if cands else None
        if not row:
            continue
        stops = [s.strip(' .') for s in re.split(r'-|,', row['stops_raw']) if s.strip(' .')]
        seen, seq = set(), []
        for s in [row['origin']] + stops + [row['dest']]:
            k = s.lower()
            if k not in seen:
                seen.add(k)
                seq.append(s)
        b['stoppages'] = [{'no': i + 1, 'name': n, 'up_time': '', 'down_time': ''}
                          for i, n in enumerate(seq)]
        b['total_stoppages'] = len(seq)
        b['origin'], b['destination'] = row['origin'], row['dest']
        matched += 1
    print(f'enriched {matched} WBTC buses', flush=True)

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
    print(f"done: {len(data['buses'])} buses, {len(routes_out)} routes, {len(stops_out)} stops")

if __name__ == '__main__':
    main()
