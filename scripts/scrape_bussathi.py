#!/usr/bin/env python3
"""Scrape bussathi.in bus pages into scraped_bussathi.json (stdlib only).

Usage: python3 scrape_bussathi.py [max_bus_id] [output.json]
Iterates /bus/<id> pages politely (0.7s delay), parses each into the BusJatri
bus schema. Pages that 404 or fail to parse are skipped.
"""
import re, json, sys, time, html as H
import urllib.request, urllib.error

MAX = int(sys.argv[1]) if len(sys.argv) > 1 else 1300
OUT = sys.argv[2] if len(sys.argv) > 2 else 'scraped_bussathi.json'
DELAY = 0.7
UA = {'User-Agent': 'Mozilla/5.0 (compatible; BusJatriUpdater/1.0; +https://github.com/murmusuvash2-wq/Wb-bus)'}

T = r'(\d{1,2}:\d{2}\s*(?:AM|PM|Noon))'

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode('utf-8', 'replace')

def text_of(h):
    h = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', h, flags=re.S | re.I)
    h = re.sub(r'<[^>]+>', ' ', h)
    h = h.replace('|', ' ')
    return re.sub(r'\s+', ' ', H.unescape(h))

def clean(s):
    return (s or '').strip()

def parse(txt, url):
    b = {}
    m = re.search(r'From\s+([A-Za-z][^0-9]{1,45}?)\s+' + T + r'\s+To\s+([A-Za-z][^0-9]{1,45}?)\s+' + T, txt)
    if not m:
        return None
    b['origin'], b['departure_time'] = clean(m.group(1)), clean(m.group(2))
    b['destination'], b['arrival_time'] = clean(m.group(3)), clean(m.group(4))

    m = re.search(r'Bus Name\s+(.+?)\s+Registration\s+([A-Za-z0-9]+)\s+Type\s+(.+?)\s+Operator\s+(.+?)\s+Depot\s+([A-Za-z][^0-9]{1,40}?)\s+(?:Total Stops|Contact|Bus Information)', txt)
    if m:
        b['bus_name'], b['reg_no'] = clean(m.group(1)), clean(m.group(2))
        b['bus_type'], b['operator'] = clean(m.group(3)), clean(m.group(4))
        b['depot_name'] = clean(m.group(5))
    else:
        m2 = re.search(r'Bus Name\s+([A-Za-z0-9][^.]{0,40})', txt)
        if not m2:
            return None
        b['bus_name'], b['reg_no'] = clean(m2.group(1)), ''
        b['bus_type'] = b['operator'] = b['depot_name'] = ''
    b['bus_name'] = re.sub(r'\s*\(([^)]*)\)\s*$', '', b['bus_name']) or b['bus_name']

    m = re.search(r'Primary\s+(Not Available !|[0-9 +()-]{6,20})\s+Alternate\s*(Not Available !|[0-9 +()-]{6,20})?', txt)
    if m:
        p, a = clean(m.group(1)), clean(m.group(2) or '')
        b['contact_number'] = p if p != 'Not Available !' else (a if a and a != 'Not Available !' else 'Not Available !')
    else:
        b['contact_number'] = 'Not Available !'

    m = re.search(r'Total Stops\s+(\d+)', txt)
    total = int(m.group(1)) if m else 0

    seg = txt
    i = txt.find('Route Timetable')
    if i >= 0:
        seg = txt[i: i + 4000]
    stops = []
    for sm in re.finditer(r'(\d{1,2})\s+([A-Za-z][A-Za-z0-9 ()/.&\']{1,45}?)\s+' + T + r'(?:\s+' + T + r')?', seg):
        n, name, up, down = int(sm.group(1)), clean(sm.group(2)), clean(sm.group(3)), clean(sm.group(4) or '')
        if 1 <= n <= 40 and len(name) > 1:
            stops.append({'no': n, 'name': name, 'up_time': up, 'down_time': down})
    # dedupe by stop number, keep order
    seen, uniq = set(), []
    for s in stops:
        if s['no'] not in seen:
            seen.add(s['no']); uniq.append(s)
    b['stoppages'] = uniq
    b['total_stoppages'] = total or len(uniq)
    b['detail_url'] = url
    b['source'] = 'bussathi.in'
    return b

def main():
    buses, ok, miss = [], 0, 0
    for i in range(1, MAX + 1):
        url = f'https://bussathi.in/bus/{i}'
        try:
            b = parse(text_of(fetch(url)), url)
        except Exception:
            b = None
        if b:
            buses.append(b); ok += 1
        else:
            miss += 1
        if i % 100 == 0:
            print(f'[{i}/{MAX}] parsed={ok} skipped={miss}', flush=True)
        time.sleep(DELAY)
    json.dump(buses, open(OUT, 'w'), ensure_ascii=False)
    print(f'DONE parsed={ok} skipped={miss} -> {OUT}')
    # print first 2 samples for log inspection
    for b in buses[:2]:
        print('SAMPLE', json.dumps(b, ensure_ascii=False)[:400])

if __name__ == '__main__':
    main()
