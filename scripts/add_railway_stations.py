#!/usr/bin/env python3
"""Attach nearest railway station to every bus stop in data/busjatri_data.json.

- Downloads the CC0 datameet/railways station list. Stations are kept if
  their state field is in STATES **or** they fall inside the West Bengal +
  border bounding box - many WB stations (Jhargram Jn, Purulia Jn, Asansol
  Jn, Kharagpur Jn ...) have a null state field in the source data and were
  wrongly dropped by the old state-only filter, so stops were being matched
  to far-away stations in other states.
- Geocodes stops via Open-Meteo (free, no key) with West Bengal bounds
  filter and depot/district hints; cached in data/stop_coords.json. Only
  stops not already in the cache are geocoded (null results are retried).
  Set SKIP_GEOCODE=1 to reuse the cache as-is without network calls.
- Prefers a station whose name matches the stop name (within 15 km) over a
  slightly closer differently-named halt (e.g. Kharagpur Jn vs Giri Maidan).
- Writes stops[name].nearest_station = {name, code, km} (straight-line km).
Run from repo root.
"""
import json, math, os, re
import urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

STATIONS_URL = 'https://raw.githubusercontent.com/datameet/railways/master/stations.json'
STATES = {'West Bengal', 'Jharkhand', 'Bihar', 'Odisha', 'Assam', 'Sikkim'}
# generous West Bengal + border buffer bounding box (rescues state=None stations)
WB_LAT = (21.0, 27.5)
WB_LON = (85.2, 90.2)
UA = {'User-Agent': 'Mozilla/5.0 (compatible; BusJatriUpdater/1.0; +https://github.com/murmusuvash2-wq/busjatri)'}

def haversine(a, b):
    R = 6371.0
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode('utf-8', 'replace')

def in_wb(lat, lon):
    return WB_LAT[0] <= lat <= WB_LAT[1] and WB_LON[0] <= lon <= WB_LON[1]

def norm(s):
    return re.sub(r'[^a-z]', '', (s or '').lower())

def geocode(task):
    """task = (name, district). Returns (name, [lat, lon] or None)."""
    name, district = task
    queries = []
    if district:
        queries.append(f'{name}, {district}, West Bengal, India')
        queries.append(f'{name}, {district} district, India')
    queries.append(f'{name}, West Bengal, India')
    queries.append(f'{name} railway station, West Bengal, India')
    for q in queries:
        try:
            d = json.loads(get('https://geocoding-api.open-meteo.com/v1/search?count=10&language=en&format=json&name='
                               + urllib.parse.quote(q)))
            for r in d.get('results') or []:
                if in_wb(r['latitude'], r['longitude']):
                    return name, [r['latitude'], r['longitude']]
        except Exception:
            pass
    return name, None

def load_stations():
    raw = json.loads(get(STATIONS_URL))
    out, rescued = [], 0
    for f in (raw.get('features') or []):
        p, g = f.get('properties') or {}, f.get('geometry') or {}
        c = g.get('coordinates') if g else None
        if not c or len(c) < 2:
            continue
        lat, lon = c[1], c[0]
        if p.get('state') in STATES or in_wb(lat, lon):
            out.append({'name': p.get('name'), 'code': p.get('code'), 'lat': lat, 'lon': lon})
            if p.get('state') is None:
                rescued += 1
    print(f'stations rescued by bbox despite null state: {rescued}', flush=True)
    return out

def main():
    data = json.load(open('data/busjatri_data.json'))
    stations = load_stations()
    print(f'stations loaded: {len(stations)}', flush=True)

    stops = data.get('stops') or {}

    # stop -> district hint from bus depot names
    depot_votes = {}
    for b in data.get('buses') or []:
        dep = (b.get('depot_name') or '').strip()
        if dep and dep != '—':
            for s in (b.get('stoppages') or []):
                n = s.get('name')
                if n:
                    depot_votes.setdefault(n, {})
                    depot_votes[n][dep] = depot_votes[n].get(dep, 0) + 1
    districts = {}
    for n, votes in depot_votes.items():
        districts[n] = max(votes, key=votes.get)

    # coordinate cache: reuse whatever we already have, geocode only the rest
    cache = {}
    if os.path.exists('data/stop_coords.json'):
        cache = json.load(open('data/stop_coords.json'))
    todo = [(n, districts.get(n)) for n in stops if not cache.get(n)]
    print(f'stops={len(stops)} cached={sum(1 for v in cache.values() if v)} to_geocode={len(todo)}', flush=True)
    if todo and not os.environ.get('SKIP_GEOCODE'):
        with ThreadPoolExecutor(max_workers=8) as ex:
            for i, (name, c) in enumerate(ex.map(geocode, todo)):
                cache[name] = c
                if (i + 1) % 100 == 0:
                    print(f'geocoded {i + 1}/{len(todo)}', flush=True)
    json.dump(cache, open('data/stop_coords.json', 'w'), ensure_ascii=False)

    have = ok = 0
    exact_matches = 0
    for name, s in stops.items():
        s.pop('nearest_station', None)
        c = cache.get(name)
        if not c:
            continue
        ok += 1
        best, bd = None, 1e9
        exact, ed = None, 1e9
        for st in stations:
            d = haversine(c, (st['lat'], st['lon']))
            if d < bd:
                bd, best = d, st
            if d < 15 and norm(st['name']) == norm(name) and d < ed:
                ed, exact = d, st
        pick = exact or best
        if pick:
            if exact:
                exact_matches += 1
            s['nearest_station'] = {'name': pick['name'], 'code': pick['code'] or '',
                                    'km': round((ed if exact else bd), 1)}
            have += 1
    data['stops'] = stops
    json.dump(data, open('data/busjatri_data.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print(f'coords ok={ok} stops_with_station={have} exact_name_matches={exact_matches}')

if __name__ == '__main__':
    main()
