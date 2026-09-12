#!/usr/bin/env python3
"""Build data/sbstc_routes.json snapshot from the extracted text of the
official SBSTC route PDF (transport.wb.gov.in). One-time manual refresh:
paste the PDF text into scripts/sbstc_text.txt and run this."""
import re, json, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else 'scripts/sbstc_text.txt'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'data/sbstc_routes.json'

TIMEGRP = re.compile(r'\d{1,2}\.\d{2}(?:/\d{1,2}\.\d{2})*')
ROUTE = re.compile(r'(\d{1,3})\s+([A-Z][A-Z0-9 .,\'&()\-]*?(?:\s+VIA\s+[A-Z .,\'\-]+?)?)\s+(\d{2,3})\s+')

text = re.sub(r'\s+', ' ', open(SRC, encoding='utf-8').read())

routes = []
matches = list(ROUTE.finditer(text))
for i, m in enumerate(matches):
    end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
    chunk = text[m.end():end]
    # fare from original text BEFORE currency stripping
    fare_m = re.search(r'R[sS][eE]?\.?\s*(\d+(?:\.\d+)?)', chunk)
    fare = f'Rs. {int(float(fare_m.group(1)))}' if fare_m else ''
    # strip currency text so Rs.7.50 etc. don't look like times
    chunk = re.sub(r'R[sS][eE]?\.?\s*\d+(?:\.\d+)?', ' CUR ', chunk)
    groups = [g.split('/') for g in TIMEGRP.findall(chunk)]
    lon = re.search(r'\s(\d{1,2})\s+CUR', chunk)
    up, down = [], []
    for j, g in enumerate(groups):
        (up if j % 2 == 0 else down).extend(g)
    if not down and lon:
        down.append(f'{lon.group(1)}.00')
    routes.append({'name': m.group(2).strip(), 'up': up, 'down': down,
                   'fare': fare})

bad = [r['name'] for r in routes if not r['up'] and not r['down']]
print(f'routes parsed: {len(routes)} (without times: {len(bad)})')
for r in routes:
    print(f"  {r['name']}: up={len(r['up'])} down={len(r['down'])} fare={r['fare']}")
assert len(routes) >= 50, 'too few routes parsed'
json.dump(routes, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'))
print(f'-> {OUT}')
