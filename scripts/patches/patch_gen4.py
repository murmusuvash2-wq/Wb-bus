#!/usr/bin/env python3
"""Patch gen_seo_pages.py part 4: via system (X to Y via Z).

- VIA combos are computed from bus stoppages on every run - when new buses
  are added to the data, new via pages/chips appear automatically and stale
  ones disappear (generator wipes output dir). Nothing to maintain by hand.
- Adds: via computation, via chips on route pages, via pages, search-index
  entries, sitemap entries."""

P = 'scripts/gen_seo_pages.py'
src = open(P, encoding='utf-8').read()
def rep(old, new, cnt=1):
    global src
    assert src.count(old) == cnt, f'pattern x{src.count(old)} (expected {cnt}): {old[:80]!r}'
    src = src.replace(old, new)

# ---------------- L. via computation (before route pages loop) --------------
rep("""for (o, t), bs in route_meta.items():
    fname = f'{slug(o)}-to-{slug(t)}.html'""",
    """# ---------------------------------------------------------------------------
# via combos: derived from stoppages at every run - new data => new combos
# ---------------------------------------------------------------------------
def via_stops(o, t, bs, min_buses=3, top=2):
    counts = Counter()
    for b in bs:
        seq = [x for x in [b.get('origin')] + [s.get('name') for s in (b.get('stoppages') or [])] + [b.get('destination')] if x and x != '—']
        io = next((i for i, x in enumerate(seq) if x == o), None)
        it = next((i for i in range(len(seq) - 1, -1, -1) if seq[i] == t), None)
        if io is None or it is None or io >= it:
            continue
        for k in range(io + 1, it):
            cc = seq[k]
            if cc and cc != o and cc != t:
                counts[cc] += 1
    return [cc for cc, nn in counts.most_common() if nn >= min_buses][:top]

VIA = {}
for (o, t), bs_ in route_meta.items():
    vv_ = via_stops(o, t, bs_)
    if vv_:
        VIA[(o, t)] = vv_

for (o, t), bs in route_meta.items():
    fname = f'{slug(o)}-to-{slug(t)}.html'""")

# ---------------- M. via chips on route pages -------------------------------
rep("""    body = crumbs(f'{esc(o)} {lbl("to", "থেকে")} {esc(t)}') + hero + stats + timetable + stops_html + faq_section + rel_html""",
    """    via_html = ''
    vv_ = VIA.get((o, t)) or []
    if vv_:
        vc = ' '.join(f'<a class="sugg-chip" href="{slug(o)}-to-{slug(t)}-via-{slug(c)}.html">{lbl("via", "হয়ে")} {place(c)}</a>' for c in vv_)
        via_html = f'''<section class="section">
<h2 class="section-title"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"/><path d="M4 16h16"/></svg>{lbl(f'All {esc(o)} buses via intermediate stops', f'{bo} থেকে বাস - মধ্যবর্তী স্টপ হয়ে' if bo else f'All {esc(o)} buses via intermediate stops')}</h2>
<div class="chip-row">{vc}</div>
</section>'''
    body = crumbs(f'{esc(o)} {lbl("to", "থেকে")} {esc(t)}') + hero + stats + timetable + stops_html + faq_section + rel_html + via_html""")

# ---------------- N. via pages (before index section) -----------------------
rep("""# ---------------------------------------------------------------------------
# index page
# ---------------------------------------------------------------------------""",
    """# ---------------------------------------------------------------------------
# via pages (X to Y via Z) - auto-computed from stoppages, data-driven
# ---------------------------------------------------------------------------
for (o, t), vv_ in sorted(VIA.items(), key=lambda kv: -len(route_meta[kv[0]])):
    for c in vv_:
        rows = []
        seen = set()
        for b in route_meta[(o, t)]:
            seq = [x for x in [b.get('origin')] + [s.get('name') for s in (b.get('stoppages') or [])] + [b.get('destination')] if x and x != '—']
            try:
                io = seq.index(o)
                ic = seq.index(c, io + 1)
                it = seq.index(t, ic + 1)
            except ValueError:
                continue
            nm, regn = clean_bus(b)
            key_ = (nm.lower(), regn)
            if key_ in seen:
                continue
            seen.add(key_)
            st = next((s for s in (b.get('stoppages') or []) if s.get('name') == c), {})
            rows.append({'nm': nm, 'regn': regn, 'type': b.get('bus_type') or '',
                         'dep': parse_time(b.get('departure_time')),
                         'via': parse_time(st.get('up_time')),
                         'arr': parse_time(b.get('arrival_time')),
                         'stops': b.get('total_stoppages') or len(b.get('stoppages') or [])})
        rows.sort(key=lambda r: r['dep'] if r['dep'] is not None else 9999)
        n = len(rows)
        if n < 2:
            continue
        fname = f'{slug(o)}-to-{slug(t)}-via-{slug(c)}.html'
        bo, bt_, bc = bn(o), bn(t), bn(c)
        times = sorted(r['dep'] for r in rows if r['dep'] is not None)
        vtimes = sorted(r['via'] for r in rows if r['via'] is not None)
        firstm, lastm = (times[0], times[-1]) if times else (None, None)
        q_first = hhmm(firstm) if firstm is not None else '—'
        q_last = hhmm(lastm) if lastm is not None else '—'
        ntot = len(route_meta[(o, t)])
        title = f'{o} to {t} via {c} Bus Time Table'
        if bo and bt_ and bc:
            title += f' | {bo} থেকে {bt_} ({bc} হয়ে)'
        desc = (f'{o} to {t} buses via {c}: {n} of {ntot} buses pass through {c}. '
                f'First bus {q_first}, last bus {q_last}.')[:300]

        hero = f'''<section class="route-hero" aria-labelledby="route-h1">
<p class="route-eyebrow"><svg class="icon" viewBox="0 0 24 24" style="width:13px;height:13px" aria-hidden="true"><path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"/><path d="M4 16h16"/></svg>{lbl('Route · Bus Time Table', 'রুট · বাস টাইম টেবিল')}</p>
<h1 id="route-h1" class="route-main">
<span class="route-end"><span class="place">{place(o)}</span></span>
<svg class="icon route-arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14"/><path d="M12 5l7 7-7 7"/></svg>
<span class="route-end dest"><span class="place">{place(t)}</span></span>
</h1>
<p style="margin-top:12px"><span class="badge badge-ac">{lbl(f'via {esc(c)}', f'{bc or esc(c)} হয়ে')}</span></p>
<div class="route-dash"><span class="stamp">{lbl(f'Updated {LASTMOD}', f'আপডেট {LASTMOD}')}</span></div>
</section>'''

        via_stat_lbl = lbl(f'Buses via {esc(c)}', f'{bc} হয়ে' if bc else None)
        stats = f'''<div class="stats" role="list">
<div class="stat" role="listitem"><div class="num">{n}</div><div class="label">{via_stat_lbl}</div></div>
<div class="stat" role="listitem"><div class="num">{lbl(q_first, bn_time(firstm) if firstm is not None else '—')}</div><div class="label">{lbl('First bus', 'প্রথম বাস')}</div></div>
<div class="stat" role="listitem"><div class="num">{lbl(q_last, bn_time(lastm) if lastm is not None else '—')}</div><div class="label">{lbl('Last bus', 'শেষ বাস')}</div></div>
</div>'''

        trows = []
        for r in rows:
            regn_ = f'<div class="bus-regn">{esc(r["regn"])}</div>' if r['regn'] else ''
            dep = lbl(hhmm(r['dep']) if r['dep'] is not None else '—', bn_time(r['dep']) if r['dep'] is not None else '—')
            via_ = lbl(hhmm(r['via']) if r['via'] is not None else '—', bn_time(r['via']) if r['via'] is not None else '—')
            arr = lbl(hhmm(r['arr']) if r['arr'] is not None else '—', bn_time(r['arr']) if r['arr'] is not None else '—')
            trows.append(
                f'<tr><td><div class="bus-name">{esc(r["nm"] or "—")}</div>{regn_}</td>'
                f'<td>{type_badges(r["type"], r["nm"])}</td>'
                f'<td class="time-cell">{dep}</td><td class="time-cell">{via_}</td><td class="time-cell">{arr}</td>'
                f'<td class="stops-cell">{r["stops"] or "—"}</td></tr>')
        timetable = f'''<section class="section">
<h2 class="section-title"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>{esc(o)} {lbl("to", "থেকে")} {esc(t)} — {lbl(f"via {esc(c)}", f"{bc or esc(c)} হয়ে" if bc else f"via {esc(c)}")}</h2>
<div class="bus-table-wrap">
<table class="bus-table">
<thead><tr>
<th scope="col">{lbl('Bus', 'বাস')}</th><th scope="col">{lbl('Type', 'ধরন')}</th>
<th scope="col">{lbl('Departure', 'ছাড়ে')}</th><th scope="col">{lbl(f'At {esc(c)}', f'{bc or esc(c)} পৌঁছায়' if bc else f'At {esc(c)}')}</th>
<th scope="col">{lbl('Arrival', 'পৌঁছায়')}</th><th scope="col">{lbl('Stops', 'স্টপ')}</th>
</tr></thead>
<tbody>{''.join(trows)}</tbody>
</table>
</div>
</section>'''

        faqs_en, faqs_bn = [], []
        faqs_en.append((f'How many buses run from {o} to {t} via {c}?',
                        f'{n} of the {ntot} buses on the {o} to {t} route pass through {c}. '
                        f'Check the "At {c}" column for the exact time each bus reaches {c}.'))
        faqs_bn.append((f'{bo or o} থেকে {bt_ or t} কতগুলো বাস {bc or c} হয়ে চলে?' if (bo and bt_ and bc) else f'How many buses run from {o} to {t} via {c}?',
                        f'{bo or o} থেকে {bt_ or t} রুটের {bnum(ntot)}টি বাসের মধ্যে {bnum(n)}টি {bc or c} হয়ে যায়। '
                        f'"পৌঁছায়" কলামে প্রতিটি বাস {bc or c} পৌঁছানোর সময় দেখুন।'))
        if firstm is not None:
            faqs_en.append((f'What is the first bus from {o} to {t} via {c}?',
                            f'The first bus that passes through {c} on this route departs {o} at {q_first}.'))
            faqs_bn.append(('ভিয়া রুটে প্রথম বাস কখন?', f'প্রথম বাস {bn_time(firstm)}-এ ছাড়ে।'))
        if lastm is not None:
            faqs_en.append((f'What is the last bus from {o} to {t} via {c}?',
                            f'The last bus that passes through {c} on this route departs {o} at {q_last}.'))
            faqs_bn.append(('ভিয়া রুটে শেষ বাস কখন?', f'শেষ বাস {bn_time(lastm)}-এ ছাড়ে।'))
        if vtimes:
            vf, vl = vtimes[0], vtimes[-1]
            faqs_en.append((f'When do buses reach {c} from {o}?',
                            f'The first bus reaches {c} at about {hhmm(vf)}; the last one at about {hhmm(vl)}. '
                            f'Times depend on traffic and boarding stops.'))
            faqs_bn.append((f'{bc or c} কখন পৌঁছায়?' if bc else f'When do buses reach {c}?',
                            f'প্রথম বাস প্রায় {bn_time(vf)}-এ এবং শেষ বাস প্রায় {bn_time(vl)}-এ {bc or c} পৌঁছায়।'))
        faqs_en.append((f'Do I have to change buses at {c}?',
                        f'No — these are through-buses: they pass through {c} on the way from {o} to {t}, so you can stay seated.'))
        faqs_bn.append((f'{bc or c}-এ বাস বদলাতে হবে?' if bc else f'Do I have to change buses at {c}?',
                        f'না — এগুলো সরাসরি বাস, {bc or c} হয়ে যায়, বসে থাকলেই হবে।'))
        faq_html = ''.join(
            f'<details class="faq-item"><summary>{lbl(esc(q_en), esc(q_bn))}</summary>'
            f'<p>{lbl(esc(a_en), esc(a_bn))}</p></details>'
            for (q_en, a_en), (q_bn, a_bn) in zip(faqs_en, faqs_bn))
        faq_section = f'''<section class="section">
<h2 class="section-title"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>{lbl('Frequently Asked Questions', 'সাধারণ জিজ্ঞাসা')}</h2>
{faq_html}
</section>'''

        rel_chips = [f'<a class="sugg-chip" href="{slug(o)}-to-{slug(t)}.html">{lbl(f"Direct {o} to {t} route", f"সরাসরি {bo or o} থেকে {bt_ or t}" if bo and bt_ else f"Direct {o} to {t} route")}</a>']
        if (o, c) in route_meta:
            rel_chips.append(f'<a class="sugg-chip" href="{slug(o)}-to-{slug(c)}.html">{place(o)} → {place(c)}</a>')
        if (c, t) in route_meta:
            rel_chips.append(f'<a class="sugg-chip" href="{slug(c)}-to-{slug(t)}.html">{place(c)} → {place(t)}</a>')
        for c2 in vv_:
            if c2 != c:
                rel_chips.append(f'<a class="sugg-chip" href="{slug(o)}-to-{slug(t)}-via-{slug(c2)}.html">{lbl("via", "হয়ে")} {place(c2)}</a>')
        rel_html = f'''<section class="section">
<h2 class="section-title"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14"/><path d="M12 5l7 7-7 7"/></svg>{lbl(f'Related routes', f'সম্পর্কিত রুট')}</h2>
<div class="chip-row">{' '.join(rel_chips)}</div>
</section>'''

        body = crumbs(f'{esc(o)} {lbl("to", "থেকে")} {esc(t)} {lbl("via", "হয়ে")} {esc(c)}') + hero + stats + timetable + faq_section + rel_html
        schema = faq_schema(faqs_en) + '\n' + breadcrumb(
            [('Home', '/'), ('Bus Time Table', '/bus-time-table/'), (f'{o} to {t} via {c}', f'/bus-time-table/{fname}')])
        open(f'{OUT}/{fname}', 'w').write(shell(title, desc, f'{BASE}/bus-time-table/{fname}', body, schema))
        sitemap.append(f'{BASE}/bus-time-table/{fname}')
        written.append(fname)

# ---------------------------------------------------------------------------
# index page
# ---------------------------------------------------------------------------""")

# ---------------- O. search-index via entries --------------------------------
rep("""for p_ in hub_places:
    bp_ = bn(p_)
    search.append({'t': 'p', 'u': f'buses-from-{slug(p_)}.html',
                   'en': f'Buses from {p_}',
                   'bn': f'{bp_} থেকে বাস' if bp_ else ''})""",
    """for p_ in hub_places:
    bp_ = bn(p_)
    search.append({'t': 'p', 'u': f'buses-from-{slug(p_)}.html',
                   'en': f'Buses from {p_}',
                   'bn': f'{bp_} থেকে বাস' if bp_ else ''})
for (o, t), vv_ in VIA.items():
    for c in vv_:
        bo_, bt_2, bc_ = bn(o), bn(t), bn(c)
        search.append({'t': 'v', 'u': f'{slug(o)}-to-{slug(t)}-via-{slug(c)}.html',
                       'en': f'{o} to {t} via {c}',
                       'bn': f'{bo_} থেকে {bt_2} ({bc_} হয়ে)' if bo_ and bt_2 and bc_ else ''})""")

open(P, 'w', encoding='utf-8').write(src)
print('patch 4 (via system) applied OK')
