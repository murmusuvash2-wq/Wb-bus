#!/usr/bin/env python3
"""Apply shared stats, trust copy, and accessibility/UX polish after page generation."""
from pathlib import Path
import json, re

ROOT = Path(__file__).resolve().parents[1]
meta = json.loads((ROOT / 'data' / 'busjatri_data.json').read_text(encoding='utf-8')).get('meta', {})
stops = int(meta.get('total_stops', 0))
routes = int(meta.get('total_routes', 0))
buses = int(meta.get('total_buses', 0))
updated = str(meta.get('last_updated', ''))
source_text = ' · '.join(meta.get('sources', [])[:4])
trust = (f'<div class="trust-note" role="note"><strong>Schedule data refreshed {updated}</strong> · '
        'Listed schedules can change; confirm with the operator before travel.</div>')
seo_css = '''<style id="busjatri-ux-polish">
.trust-note{margin:12px 0;padding:10px 14px;border:1px solid color-mix(in srgb,var(--accent,#b8791f) 35%,transparent);border-radius:12px;background:color-mix(in srgb,var(--accent,#b8791f) 8%,transparent);color:var(--ink-dim,#665);font-size:.82rem;line-height:1.5}.trust-note strong{color:var(--ink,#222)}
.no-results,.empty-state{display:none}.bus-card{transition:transform .18s ease,box-shadow .18s ease}.bus-card:hover{transform:translateY(-2px);box-shadow:0 8px 22px rgba(50,35,10,.10)}.bus-card .dep{font-variant-numeric:tabular-nums;white-space:nowrap}.missing-data{color:var(--ink-dim,#777);font-style:italic}
@media(min-width:760px){.bus-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr)));gap:12px}.bus-card{height:fit-content}.search-panel,.search-box{position:sticky;top:10px;z-index:4}.letter-nav{position:sticky;top:0;z-index:3;background:var(--paper,#fbf7ee);padding:8px 0}}
@media(max-width:759px){.bus-card{border-radius:14px}.trust-note{font-size:.76rem}.letter-nav{overflow-x:auto;white-space:nowrap}}
</style>'''

def inject_once(s, marker, value):
    return s if value in s else s.replace(marker, value + marker, 1)

# Homepage labels are dynamic, but this also updates static copy if present.
p = ROOT / 'index.html'
s = p.read_text(encoding='utf-8')
s = s.replace('Live Departures', 'Next Scheduled Departures')
s = inject_once(s, '</main>', trust)
s = inject_once(s, '</head>', seo_css)
p.write_text(s, encoding='utf-8')

# Generated timetable index: use the same dataset truth everywhere.
p = ROOT / 'bus-time-table' / 'index.html'
s = p.read_text(encoding='utf-8')
old_desc = re.compile(r'Complete West Bengal bus time table: [^\"]+')
new_desc = f'Complete West Bengal bus time table: {routes:,} routes from {stops:,} stops. Find SBSTC, WBTC, NBSTC and private bus timings with departure times, operators and stoppages.'
s = old_desc.sub(new_desc, s)
s = re.sub(r'<strong data-count="\d+">\d+</strong> <span class="label-en">places</span>', f'<strong data-count="{stops}">{stops:,}</strong> <span class="label-en">stops</span>', s)
s = re.sub(r'<strong data-count="\d+">\d+</strong> <span class="label-en">routes</span>', f'<strong data-count="{routes}">{routes:,}</strong> <span class="label-en">routes</span>', s)
s = re.sub(r'<strong data-count="\d+">\d+</strong> <span class="label-en">bus services</span>', f'<strong data-count="{buses}">{buses:,}</strong> <span class="label-en">bus services</span>', s)
s = s.replace('<span class="label-bn">\u09b8\u09cd\u09a5\u09be\u09a8</span>', '<span class="label-bn">\u09b8\u09cd\u099f\u09aa</span>')
s = re.sub(r'The timetable covers [^<]+daily bus services listed\.', f'The timetable covers {routes:,} bus routes connecting {stops:,} stops across West Bengal, with {buses:,} listed bus services.', s)
s = s.replace('<b>No matches found</b>', '<b class="no-results">No matches found</b>')
s = s.replace('buses daily', 'listed buses')
s = inject_once(s, '<div class="stat-chips">', trust)
s = inject_once(s, '</head>', seo_css)
p.write_text(s, encoding='utf-8')

# Route pages: honest scheduled-data language, missing-value clarity, trust notice, and card polish.
for p in (ROOT / 'bus-time-table').glob('*.html'):
    if p.name == 'index.html':
        continue
    s = p.read_text(encoding='utf-8')
    s = s.replace("Today's Departures", 'Scheduled Departures')
    s = s.replace('Live Departures', 'Scheduled Departures')
    s = re.sub(r'>0 stops<', '><span class="missing-data">Stops not available</span><', s)
    s = inject_once(s, '<div class="stat-chips">', trust)
    s = inject_once(s, '</head>', seo_css)
    p.write_text(s, encoding='utf-8')

print(f'finalized pages with stats: {stops:,} stops, {routes:,} routes, {buses:,} buses; refreshed {updated}')
