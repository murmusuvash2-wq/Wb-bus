#!/usr/bin/env python3
"""Merge freshly scraped bussathi.in buses (scraped_bussathi.json) into
data/busjatri_data.json: keeps other sources untouched, preserves existing
bus IDs via detail_url, keeps old stoppages when a scrape row has none,
then rebuilds route/stop indexes. Run from repo root."""
import json, re
from collections import defaultdict
from datetime import date

def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', str(s or '').lower()).strip('-')

data = json.load(open('data/busjatri_data.json'))
scraped = json.load(open('scraped_bussathi.json'))

existing = [b for b in data['buses'] if b.get('source') != 'bussathi.in']
by_url = {b['detail_url']: b for b in data['buses']
          if b.get('source') == 'bussathi.in' and b.get('detail_url')}
used_ids = set(b['id'] for b in data['buses'])
counters = defaultdict(int)

def make_id(name):
    base = f'bussathi-{slug(name)}'
    n = counters[base]
    while f'{base}-{n}' in used_ids:
        n += 1
    counters[base] = n + 1
    return f'{base}-{n}'

kept = added = no_stops_kept = 0
for s in scraped:
    old = by_url.get(s.get('detail_url'))
    bid = old['id'] if old else make_id(s.get('bus_name') or 'bus')
    used_ids.add(bid)
    if old:
        kept += 1
    else:
        added += 1
    stops = s.get('stoppages')
    if not stops and old:
        stops = old.get('stoppages') or []
        no_stops_kept += bool(stops)
    existing.append({
        'id': bid,
        'bus_name': s.get('bus_name') or '—',
        'reg_no': s.get('reg_no') or '',
        'operator': s.get('operator') or '—',
        'bus_type': s.get('bus_type') or '',
        'origin': s.get('origin') or '—',
        'destination': s.get('destination') or '—',
        'departure_time': s.get('departure_time') or '',
        'arrival_time': s.get('arrival_time') or '',
        'contact_number': s.get('contact_number') or 'Not Available !',
        'depot_name': s.get('depot_name') or '',
        'route': f"{s.get('origin')} - {s.get('destination')}",
        'stoppages': stops or [],
        'source': 'bussathi.in',
        'total_stoppages': s.get('total_stoppages') or len(stops or []),
        'detail_url': s.get('detail_url') or '',
    })

routes_map, stops_map = defaultdict(list), defaultdict(list)
for b in existing:
    if b.get('origin') and b.get('destination') and b['origin'] != '—' and b['destination'] != '—':
        routes_map[f"{slug(b['origin'])}-{slug(b['destination'])}"].append(b['id'])
    seen = set()
    for s in b.get('stoppages') or []:
        n = s.get('name')
        if n and n not in seen:
            seen.add(n)
            stops_map[n].append(b['id'])

routes_out = {}
for b in existing:
    k = f"{slug(b.get('origin'))}-{slug(b.get('destination'))}"
    if k in routes_map and k not in routes_out:
        routes_out[k] = {'from': b['origin'], 'to': b['destination'],
                         'bus_ids': list(dict.fromkeys(routes_map[k]))}
stops_out = {n: {'name': n, 'bus_ids': list(dict.fromkeys(ids))}
             for n, ids in stops_map.items()}

data['buses'] = existing
data['routes'] = routes_out
data['stops'] = stops_out
data['meta'].update({
    'total_buses': len(existing),
    'total_routes': len(routes_out),
    'total_stops': len(stops_out),
    'last_updated': str(date.today()),
})
json.dump(data, open('data/busjatri_data.json', 'w'),
          ensure_ascii=False, separators=(',', ':'))
print(f'buses={len(existing)} kept_ids={kept} new={added} '
      f'old_stoppages_reused={no_stops_kept} routes={len(routes_out)} stops={len(stops_out)}')
