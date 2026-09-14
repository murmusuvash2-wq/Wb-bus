#!/usr/bin/env python3
"""
Apply SEO redesign patch to gen_seo_pages.py (in place).
Replaces 6 template functions with compact "Departure Board" design versions.
Run from repo root: python3 scripts/apply_seo_redesign.py
Then regenerate pages: python3 scripts/gen_seo_pages.py
"""
import re, os, sys

SCRIPT = os.path.join(os.path.dirname(__file__), "gen_seo_pages.py")

src = open(SCRIPT, encoding="utf-8").read()

# ============================================================
# 1. NEW HEADER
# ============================================================
NEW_HEADER = '''def header_html():
    return """<header class="header">
  <div class="container header-inner">
    <a href="../index.html" class="logo" style="text-decoration:none;color:inherit">
      <svg class="icon" viewBox="0 0 24 24" style="width:1.35rem;height:1.35rem;color:var(--amber)" aria-hidden="true">
        <path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"/><path d="M4 16h16"/>
      </svg>
      Bus<span>Jatri</span>
    </a>
    <nav style="display:flex;gap:10px;align-items:center;font-size:13px">
      <a href="../index.html" style="color:var(--ink-dim);text-decoration:none;font-weight:600">Home</a>
      <a href="./" style="color:var(--ink-dim);text-decoration:none;font-weight:600">Routes</a>
    </nav>
  </div>
</header>"""'''

# ============================================================
# 2. NEW FOOTER (all links + email)
# ============================================================
NEW_FOOTER = '''def footer_html():
    return """<footer class="footer">
  <div class="container">
    <div class="footer-links">
      <a href="../about.html">About Us</a>
      <a href="../contact.html">Contact Us</a>
      <a href="../privacy-policy.html">Privacy Policy</a>
      <a href="../about.html#credits">Credits</a>
      <a href="./">All Bus Timetables</a>
    </div>
    <p><strong>BusJatri</strong> — West Bengal Bus Timetable<br>
    Not affiliated with any transport corporation<br>
    Contact: <a href="mailto:busjatri@zohomail.in">busjatri@zohomail.in</a></p>
  </div>
</footer>"""'''

# ============================================================
# 3. NEW SHELL (links seo.css + extras.css, 720px max-width)
# ============================================================
NEW_SHELL = '''def shell(title, description, canonical, body, schema=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(canonical)}">
<meta name="theme-color" content="#b8791f">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b8791f' stroke-width='2'%3E%3Cpath d='M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10'/%3E%3Cpath d='M4 16h16'/%3E%3C/svg%3E">
<link rel="stylesheet" href="../css/seo.css">
<link rel="stylesheet" href="../css/extras.css">
{schema}
</head>
<body>
{header_html()}
<main class="container seo-main" style="padding-top:18px;padding-bottom:48px;max-width:720px">
{body}
</main>
{footer_html()}
</body>
</html>"""'''

# ============================================================
# 4. NEW BUS CARD (compact single-line row with badge)
# ============================================================
NEW_BUS_CARD = '''def bus_card(bus):
    name = clean_text(bus.get("bus_name")) or "Bus service"
    dep = format_time(parse_time(bus.get("departure_time")))
    arr = format_time(parse_time(bus.get("arrival_time")))
    operator = operator_name(bus)
    stops = total_stops(bus)
    duration = calculate_duration(bus)
    dur_text = fmt_duration(duration) if duration else "—"
    fare = clean_text(bus.get("fare")) or "—"
    bt_raw = (bus.get("bus_type") or "").lower()
    if "gov" in bt_raw or "sbstc" in bt_raw or "nbstc" in bt_raw or "wbtc" in bt_raw:
        badge = '<span class="badge badge-govt">Govt</span>'
    elif "ac" in bt_raw and "non" not in bt_raw:
        badge = '<span class="badge badge-ac">AC</span>'
    else:
        badge = '<span class="badge badge-priv">Private</span>'
    op_line = esc(name)
    if operator:
        op_line += f' · {esc(operator)}'
    return f"""<div class="bus-row">
  <div class="dep">{esc(dep)}<small>{esc(arr)} arr</small></div>
  <div class="bmid">
    <div class="op">{op_line}</div>
    <div class="mrow"><span>{esc(fare)}</span><span>~{esc(dur_text)}</span><span>{stops or 0} stops</span></div>
  </div>
  {badge}
</div>"""'''

# ============================================================
# 5. NEW ROUTE STOPS (horizontal map)
# ============================================================
NEW_ROUTE_STOPS = '''def route_stops_html(buses):
    sequences = []
    for bus in buses:
        stops = bus_stops(bus)
        if stops:
            sequences.append(stops)
    if not sequences:
        return ""
    from collections import Counter as _C
    sc = _C(tuple(s) for s in sequences)
    sequence, frequency = sc.most_common(1)[0]
    sequence = list(sequence[:10])
    if len(sequence) < 2:
        return ""
    dots = ""
    for i, stop in enumerate(sequence):
        end_cls = " end" if i in (0, len(sequence)-1) else ""
        dots += f'<div class="rm-stop{end_cls}"><div class="rm-dot"></div><div class="rm-name">{esc(stop)}</div></div>'
    more = '<div class="rm-more">▸ full timetable below</div>' if len(sequence) == 10 else ""
    return f"""<section class="seo-section">
  <h3 class="section-title">Route Map</h3>
  <div class="routemap">
    <div class="rm-track"><div class="rm-line"></div><div class="rm-stops">{dots}</div></div>
    {more}
  </div>
</section>"""'''

# ============================================================
# 6. NEW ROUTE PAGE (compact: hero chips, bus rows, map, FAQ, related)
# ============================================================
NEW_ROUTE_PAGE = r'''def generate_route_page(origin, destination, buses):
    filename = f"{slug(origin)}-to-{slug(destination)}.html"
    route_bn = bn_route(origin, destination)
    stats = route_stats(buses)
    first = format_time(stats["first"])
    last = format_time(stats["last"])
    duration = stats["duration"]
    operators = stats["operators"]
    count = len(buses)
    dur_text = fmt_duration(duration) if duration else "—"

    title = f"{origin} to {destination} Bus Time Table | {SITE_NAME}"
    description = f"{origin} to {destination} bus timings, operators, stoppages. {count} buses listed. First {first}, last {last}."[:300]
    canonical = f"{BASE}/bus-time-table/{filename}"
    major_stops = stoppage_summary(buses)

    faqs = [
        (f"What is the first bus from {origin} to {destination}?",
         f"The first bus departs at {first}." if stats["first"] is not None else "Check the timetable above."),
        (f"What is the last bus from {origin} to {destination}?",
         f"The last bus departs at {last}." if stats["last"] is not None else "Check the timetable above."),
        (f"How many buses run from {origin} to {destination}?",
         f"{count} bus services are listed on this route."),
    ]

    bn_sub = f'<p class="bn-sub">{esc(route_bn)} বাসের সময়সূচী</p>' if route_bn else ""
    hero = f"""<div class="crumbs"><a href="../index.html">Home</a> › <a href="./">Bus Timetable</a> › <span>{esc(origin)} → {esc(destination)}</span></div>
<div class="seo-hero">
  <h1>{esc(origin)} <span class="arr">→</span> {esc(destination)}</h1>
  {bn_sub}
  <div class="stat-chips">
    <span class="schip">🚌 {count} buses</span>
    <span class="schip hot">⏰ First {esc(first)}</span>
    <span class="schip">⏰ Last {esc(last)}</span>
    <span class="schip">⏱ ~{esc(dur_text)}</span>
  </div>
</div>"""

    sorted_buses = sorted(buses, key=lambda b: parse_time(b.get("departure_time")) or 9999)
    timetable = f"""<section class="seo-section">
  <h3 class="section-title">Today's Departures</h3>
  {''.join(bus_card(b) for b in sorted_buses)}
</section>"""

    route_section = route_stops_html(buses)

    major_section = ""
    if major_stops:
        chips = "".join(f'<span class="via-chip">{esc(s)}</span>' for s in major_stops)
        major_section = f"""<section class="seo-section">
  <h3 class="section-title">Via Stoppages</h3>
  <div class="chip-row">{chips}</div>
</section>"""

    faq_html = "".join(
        f'<details{" open" if i==0 else ""}><summary>{esc(q)}</summary><div class="fa-body">{esc(a)}</div></details>'
        for i, (q, a) in enumerate(faqs)
    )
    faq_section = f"""<section class="seo-section">
  <h3 class="section-title">FAQ</h3>
  {faq_html}
</section>"""

    related = [(o, t) for (o, t) in route_meta if o == origin and t != destination]
    related = sorted(related, key=lambda p: -len(route_meta[p]))[:8]
    related_section = ""
    if related:
        links = "".join(
            f'<a class="rel-chip" href="{slug(o)}-to-{slug(t)}.html">{esc(o)} → {esc(t)}</a>'
            for o, t in related
        )
        related_section = f"""<section class="seo-section">
  <h3 class="section-title">More Routes from {esc(origin)}</h3>
  <div class="chip-row">{links}</div>
</section>"""

    reverse_section = ""
    if (destination, origin) in route_meta:
        rev_file = f"{slug(destination)}-to-{slug(origin)}.html"
        reverse_section = f"""<section class="seo-section">
  <a class="rel-chip" href="{rev_file}">↩ {esc(destination)} → {esc(origin)} (return)</a>
</section>"""

    body = hero + timetable + route_section + major_section + faq_section + reverse_section + related_section

    schema = (
        faq_schema(faqs) + "\n" +
        breadcrumb_schema([("Home", "/"), ("Bus Timetable", "/bus-time-table/"), (f"{origin} to {destination}", f"/bus-time-table/{filename}")])
    )
    return filename, shell(title, description, canonical, body, schema)'''


def replace_func(src, func_name, new_def):
    """Replace a top-level function definition with new code."""
    start = src.find(f'def {func_name}(')
    if start == -1:
        print(f"WARNING: {func_name} not found — skipping")
        return src
    remaining = src[start:]
    next_def = remaining.find('\ndef ', 1)
    if next_def == -1:
        next_def = remaining.find('\n# ', 1)
    if next_def == -1:
        next_def = len(remaining)
    old_block = remaining[:next_def]
    return src[:start] + new_def + '\n\n' + src[start + len(old_block):]


print("Patching gen_seo_pages.py with SEO redesign templates...")
before = len(src)
src = replace_func(src, 'header_html', NEW_HEADER)
src = replace_func(src, 'footer_html', NEW_FOOTER)
src = replace_func(src, 'shell', NEW_SHELL)
src = replace_func(src, 'bus_card', NEW_BUS_CARD)
src = replace_func(src, 'route_stops_html', NEW_ROUTE_STOPS)
src = replace_func(src, 'generate_route_page', NEW_ROUTE_PAGE)
# Switch CSS link to seo.css
src = src.replace('CSS = "../css/style.css"', 'CSS = "../css/seo.css"')
after = len(src)

open(SCRIPT, 'w', encoding='utf-8').write(src)
print(f"Done: {before} -> {after} bytes")

# Verify syntax
import py_compile
try:
    py_compile.compile(SCRIPT, doraise=True)
    print("SYNTAX OK")
except py_compile.PyCompileError as e:
    print(f"SYNTAX ERROR: {e}")
    sys.exit(1)
