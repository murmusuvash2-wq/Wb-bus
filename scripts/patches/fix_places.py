#!/usr/bin/env python3
"""Fix POPULAR_PLACES: only keep tourist spots with actual bus data."""

P = 'js/app.js'
src = open(P, encoding='utf-8').read()

if 'Sundarban' in src:
    import re
    new_list = """const POPULAR_PLACES = [
  { name: 'Digha', tag: 'Sea Beach' },
  { name: 'Mukutmanipur', tag: 'Lake & Dam' },
  { name: 'Bishnupur', tag: 'Terracotta Temples' },
  { name: 'Jhargram', tag: 'Forest & Palaces' },
  { name: 'Purulia', tag: 'Hills & Falls' },
  { name: 'Tarapith', tag: 'Temple Town' },
  { name: 'Mayapur', tag: 'Pilgrimage' },
  { name: 'Bolpur', tag: 'Shantiniketan' },
  { name: 'Kolkata', tag: 'City of Joy' },
  { name: 'Mandarmani', tag: 'Beach Resort' },
  { name: 'Bankura', tag: 'Heritage Trails' },
  { name: 'Darjeeling', tag: 'Hill Station' },
];"""
    src = re.sub(r"const POPULAR_PLACES = \[.*?\];", new_list, src, count=1, flags=re.DOTALL)
    # remove dead icons
    src = src.replace("  Sundarban: 'trees', Shantiniketan: 'landmark', Mandarmani: 'waves',\n  Kurseong: 'mountain', Bakreshwar: 'sun',\n", "  Tarapith: 'dome', Mayapur: 'dome', Darjeeling: 'mountain',\n", 1)
    open(P, 'w', encoding='utf-8').write(src)
    print('popular places fixed - all have bus data')
else:
    print('already fixed')

