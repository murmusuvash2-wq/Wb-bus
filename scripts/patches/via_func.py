def generate_via_page(origin, destination, via_stop, buses):
    filename = f'{slug(origin)}-to-{slug(destination)}-via-{slug(via_stop)}.html'
    via_bn = bn(via_stop)
    route_bn = bn_route(origin, destination)
    rows = []
    seen = set()
    for b in buses:
        seq = [x for x in [clean_text(b.get('origin'))] + [clean_text(s.get('name')) for s in (b.get('stoppages') or [])] + [clean_text(b.get('destination'))] if x and x != '—']
        try:
            io = seq.index(origin)
            ic = seq.index(via_stop, io + 1)
            it = seq.index(destination, ic + 1)
        except ValueError:
            continue
        # --- FIX: filter garbage buses (no dep/arr) ---
        dep_raw = b.get('departure_time', '')
        arr_raw = b.get('arrival_time', '')
        dep_min = _t2m(dep_raw)
        arr_min = _t2m(arr_raw)
        if dep_min is None or arr_min is None:
            continue
        op = operator_name(b)
        key = (op or '').lower()
        if key in seen:
            continue
        seen.add(key)
        st = next((s for s in (b.get('stoppages') or []) if clean_text(s.get('name')) == via_stop), {})
        # --- FIX: pick correct via time (not always up_time) ---
        up_min = _t2m(st.get('up_time', ''))
        down_min = _t2m(st.get('down_time', ''))
        via_min = _pick_via_time(dep_min, arr_min, up_min, down_min)
        via_str = _m2t(via_min) if via_min is not None else '—'
        rows.append({'operator': op or '—', 'dep': parse_time(dep_raw), 'via': via_str, 'arr': parse_time(arr_raw), 'stops': total_stops(b), 'bus_type': bus_type_label(b.get('bus_type') or '')})
    rows.sort(key=lambda r: r['dep'] if r['dep'] is not None else 9999)
    n = len(rows)
    if n < 2:
        return None, None
    dep_times = [r['dep'] for r in rows if r['dep'] is not None]
    via_times_raw = [r['via'] for r in rows if r['via'] != '—']
    first = format_time(min(dep_times)) if dep_times else '—'
    last = format_time(max(dep_times)) if dep_times else '—'
    ntot = len(buses)
    title = f'{origin} to {destination} via {via_stop} Bus Time Table'
    if route_bn:
        title += f' | {route_bn}'
    if via_bn:
        title += f' ({via_bn} হযে)'
    description = f'{origin} to {destination} buses via {via_stop}: {n} of {ntot} buses pass through {via_stop}. First bus {first}, last bus {last}.'
    canonical = f'{BASE}/bus-time-table/{filename}'
    trows = ''
    for r in rows:
        dep_f = format_time(r['dep'])
        via_f = r['via']
        arr_f = format_time(r['arr'])
        type_html = ''
        if r['bus_type']:
            type_html = '<span style="font-size:12px;color:var(--ink-dim)">' + esc(r['bus_type']) + '</span>'
        trows += '<tr><td style="padding:10px 12px;border-bottom:1px solid var(--border)">' + esc(r['operator']) + '<br>' + type_html + '</td>'
        trows += '<td style="padding:10px 12px;border-bottom:1px solid var(--border);white-space:nowrap">' + dep_f + '</td>'
        trows += '<td style="padding:10px 12px;border-bottom:1px solid var(--border);white-space:nowrap;color:var(--amber)">' + via_f + '</td>'
        trows += '<td style="padding:10px 12px;border-bottom:1px solid var(--border);white-space:nowrap">' + arr_f + '</td>'
        trows += '<td style="padding:10px 12px;border-bottom:1px solid var(--border);text-align:center">' + str(r['stops']) + '</td></tr>'
    faqs = [
        ('How many buses run from ' + origin + ' to ' + destination + ' via ' + via_stop + '?', str(n) + ' of the ' + str(ntot) + ' buses on the ' + origin + ' to ' + destination + ' route pass through ' + via_stop + '.'),
        ('What is the first bus from ' + origin + ' to ' + destination + ' via ' + via_stop + '?', 'The first bus passing through ' + via_stop + ' departs ' + origin + ' at ' + first + '.' if dep_times else 'No reliable departure time available.'),
        ('What is the last bus from ' + origin + ' to ' + destination + ' via ' + via_stop + '?', 'The last bus passing through ' + via_stop + ' departs ' + origin + ' at ' + last + '.' if dep_times else 'No reliable departure time available.'),
        ('Do I have to change buses at ' + via_stop + '?', 'No, these are through-buses. They pass through ' + via_stop + ' on the way from ' + origin + ' to ' + destination + '.'),
    ]
    if via_times_raw:
        faq_html_inner = '<details style="border:1px solid var(--border);border-radius:10px;padding:12px 16px;margin-bottom:10px"><summary style="cursor:pointer;font-weight:600">' + esc('When do buses reach ' + via_stop + ' from ' + origin + '?') + '</summary><p style="margin:8px 0 0;color:var(--ink-dim);font-size:14px">' + esc('Buses reach ' + via_stop + ' between ' + via_times_raw[0] + ' and ' + via_times_raw[-1] + ' depending on departure time.') + '</p></details>'
    else:
        faq_html_inner = ''
    faq_html = ''
    for q, a in faqs:
        faq_html += '<details style="border:1px solid var(--border);border-radius:10px;padding:12px 16px;margin-bottom:10px"><summary style="cursor:pointer;font-weight:600">' + esc(q) + '</summary><p style="margin:8px 0 0;color:var(--ink-dim);font-size:14px">' + esc(a) + '</p></details>'
    faq_html += faq_html_inner
    related_links = '<a href="' + slug(origin) + '-to-' + slug(destination) + '.html" style="display:block;padding:12px 14px;border-bottom:1px solid var(--border);text-decoration:none">Direct ' + esc(origin) + ' to ' + esc(destination) + ' route <span style="float:right;color:var(--ink-dim);font-size:13px">' + str(ntot) + ' buses</span></a>'
    if (origin, via_stop) in route_meta:
        related_links += '<a href="' + slug(origin) + '-to-' + slug(via_stop) + '.html" style="display:block;padding:12px 14px;border-bottom:1px solid var(--border);text-decoration:none">' + esc(origin) + ' to ' + esc(via_stop) + ' <span style="float:right;color:var(--ink-dim);font-size:13px">' + str(len(route_meta[(origin, via_stop)])) + ' buses</span></a>'
    if (via_stop, destination) in route_meta:
        related_links += '<a href="' + slug(via_stop) + '-to-' + slug(destination) + '.html" style="display:block;padding:12px 14px;border-bottom:1px solid var(--border);text-decoration:none">' + esc(via_stop) + ' to ' + esc(destination) + ' <span style="float:right;color:var(--ink-dim);font-size:13px">' + str(len(route_meta[(via_stop, destination)])) + ' buses</span></a>'
    for c2 in VIA.get((origin, destination), []):
        if c2 != via_stop:
            related_links += '<a href="' + slug(origin) + '-to-' + slug(destination) + '-via-' + slug(c2) + '.html" style="display:block;padding:12px 14px;border-bottom:1px solid var(--border);text-decoration:none">via ' + esc(c2) + '</a>'
    via_label = ''
    if via_bn:
        via_label = ' | ' + via_bn + ' হযে'
    body = '<section style="max-width:760px;margin:0 auto;padding:28px 16px 40px">'
    body += '<div style="font-size:13px;color:var(--ink-dim);margin-bottom:8px"><a href="../index.html" style="color:var(--amber);text-decoration:none">Home</a> / <a href="index.html" style="color:var(--amber);text-decoration:none">Bus Timetable</a> / ' + esc(origin) + ' to ' + esc(destination) + ' via ' + esc(via_stop) + '</div>'
    body += '<h1 style="font-size:1.8rem;margin:0 0 6px">' + esc(origin) + ' to ' + esc(destination) + ' Bus Time Table</h1>'
    body += '<p style="color:var(--amber);font-weight:600;margin:0 0 4px">via ' + esc(via_stop) + via_label + '</p>'
    body += '<p style="color:var(--ink-dim);font-size:13px;margin:0 0 20px">Updated ' + LASTMOD + ' - ' + str(n) + ' of ' + str(ntot) + ' buses pass through ' + esc(via_stop) + '</p>'
    body += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:28px;font-size:13px">'
    body += '<div style="background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:12px;text-align:center"><div style="font-size:1.4rem;font-weight:700">' + str(n) + '</div><div style="color:var(--ink-dim)">Buses via ' + esc(via_stop) + '</div></div>'
    body += '<div style="background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:12px;text-align:center"><div style="font-size:1.4rem;font-weight:700">' + first + '</div><div style="color:var(--ink-dim)">First bus</div></div>'
    body += '<div style="background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:12px;text-align:center"><div style="font-size:1.4rem;font-weight:700">' + last + '</div><div style="color:var(--ink-dim)">Last bus</div></div>'
    body += '</div>'
    body += '<h2 style="font-size:1.35rem;margin:28px 0 12px">' + esc(origin) + ' to ' + esc(destination) + ' - via ' + esc(via_stop) + ' Timings</h2>'
    body += '<div style="overflow-x:auto;border:1px solid var(--border);border-radius:12px"><table style="width:100%;border-collapse:collapse;font-size:14px"><thead><tr style="background:var(--panel);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.5px"><th style="padding:10px 12px;text-align:left">Bus</th><th style="padding:10px 12px;text-align:left">Departure</th><th style="padding:10px 12px;text-align:left">At ' + esc(via_stop) + '</th><th style="padding:10px 12px;text-align:left">Arrival</th><th style="padding:10px 12px;text-align:center">Stops</th></tr></thead><tbody>' + trows + '</tbody></table></div>'
    body += '<h2 style="font-size:1.35rem;margin:36px 0 12px">FAQ</h2>' + faq_html
    body += '<h2 style="font-size:1.35rem;margin:36px 0 12px">Related Routes</h2><div style="background:var(--panel);border:1px solid var(--border);border-radius:16px;overflow:hidden">' + related_links + '</div>'
    body += '</section>'
    schema = faq_schema(faqs) + chr(10) + breadcrumb_schema([('Home', '/'), ('Bus Timetable', '/bus-time-table/'), (origin + ' to ' + destination + ' via ' + via_stop, '/bus-time-table/' + filename)])
    return filename, shell(title, description, canonical, body, schema)


# --- time helpers ---
import re as _re

def _t2m(t):
    """Convert '6:15 AM' to minutes since midnight (375). None if invalid."""
    if not t or not isinstance(t, str):
        return None
    m = _re.match(r'(\d+):(\d+)\s*(AM|PM)', t.strip())
    if not m:
        return None
    h, mn, ap = int(m.group(1)), int(m.group(2)), m.group(3)
    if ap == 'PM' and h != 12:
        h += 12
    if ap == 'AM' and h == 12:
        h = 0
    return h * 60 + mn

def _m2t(m):
    """Convert minutes since midnight to '6:15 AM' format."""
    if m is None:
        return None
    h = m // 60 % 24
    mn = m % 60
    if h == 0:
        h12, ap = 12, 'AM'
    elif h < 12:
        h12, ap = h, 'AM'
    elif h == 12:
        h12, ap = 12, 'PM'
    else:
        h12, ap = h - 12, 'PM'
    return f'{h12}:{mn:02d} {ap}'

def _pick_via_time(dep_min, arr_min, up_min, down_min):
    """Pick the via-stop time that falls between dep and arr. Handle overnight."""
    if dep_min is None or arr_min is None:
        return None
    end = arr_min + 24 * 60 if arr_min < dep_min else arr_min
    for t in [down_min, up_min]:
        if t is None:
            continue
        t_adj = t + 24 * 60 if t < dep_min else t
        if dep_min <= t_adj <= end:
            return t
    return None
