#!/usr/bin/env python3
"""Attach nearest railway station to every bus stop in data/busjatri_data.json.

- Downloads the CC0 datameet/railways station list (regional states only)
- Geocodes stops via Open-Meteo (free, no key), cached in data/stop_coords.json
- Writes stops[name].nearest_station = {name, code, km} (straight-line km)
Run from repo root."""
import json, math, os, time
import urllib.request, urllib.parse

STATIONS_URL = 'https://raw.githubusercontent.com/datameet/railways/master/stations.json'
STATES = {'West Bengal', 'Jharkhand', 'Bihar', 'Odisha', 'Assam', 'Sikkim'}
UA = {'User-Agent': 'Mozilla/5.0 (compatible; BusJatriUpdater/1.0; +https://github.com/murmusuvash2-wq/Wb-bus)'}

def haversine(a, b):
    R = 6371.0
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode('utf-8', 'replace')

def geocode(name):
    q = urllib.parse.quote(f'{name}, West Bengal, India')
    try:
        d = json.loads(get('https://geocoding-api.open-meteo.com/v1/search?count=1&language=en&format=json&name=' + q))
        res = d.get('results') or []
        if res:
            return [res[0]['latitude'], res[0]['longitude']]
    except Exception:
        pass
    return None

def load_stations():
    raw = json.loads(get(STATIONS_URL))
    out = []
    for f in (raw.get('features') or []):
        p, g = f.get('properties') or {}, f.get('geometry') or {}
        c = g.get('coordinates') if g else None
        if p.get('state') in STATES and c and len(c) >= 2:
            out.append({'name': p.get('name'), 'code': p.get('code'), 'lat': c[1], 'lon': c[0]})
    return out

def main():
    data = json.load(open('data/busjatri_data.json'))
    stations = load_stations()
    print(f'stations loaded: {len(stations)}', flush=True)

    cache = {}
    if os.path.exists('data/stop_coords.json'):
        cache = json.load(open('data/stop_coords.json'))
    stops = data.get('stops') or {}

    geocoded = failed = 0
    for i, name in enumerate(stops):
        if name in cache:
            continue
        c = geocode(name)
        cache[name] = c
        if c:
            geocoded += 1
        else:
            failed += 1
        if (i + 1) % 50 == 0:
            print(f'geocoding {i + 1}/{len(stops)} (new={geocoded} failed={failed})', flush=True)
        time.sleep(0.35)
    json.dump(cache, open('data/stop_coords.json', 'w'), ensure_ascii=False)

    have = 0
    for name, s in stops.items():
        s.pop('nearest_station', None)
        c = cache.get(name)
        if not c:
            continue
        best, bd = None, 1e9
        for st in stations:
            d = haversine(c, (st['lat'], st['lon']))
            if d < bd:
                bd, best = d, st
        if best:
            s['nearest_station'] = {'name': best['name'], 'code': best['code'] or '', 'km': round(bd, 1)}
            have += 1
    data['stops'] = stops
    json.dump(data, open('data/busjatri_data.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print(f'stops={len(stops)} newly_geocoded={geocoded} failed={failed} with_station={have}')

if __name__ == '__main__':
    main()
