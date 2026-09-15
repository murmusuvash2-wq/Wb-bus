#!/usr/bin/env python3
"""
Generate static SEO pages for BusJatri.

Generates:
- bus-time-table/<from>-to-<to>.html
- bus-time-table/buses-from-<place>.html
- bus-time-table/index.html
- sitemap.xml
- robots.txt

Data source:
- data/busjatri_data.json
"""

import json
import re
import os
import html
from collections import Counter, defaultdict
from datetime import datetime


DATA = "data/busjatri_data.json"
OUT = "bus-time-table"

BASE = os.environ.get(
    "SITE_BASE",
    "https://wb-bus.vercel.app"
).rstrip("/")

SITE_NAME = "BusJatri"
LASTMOD = datetime.now().strftime("%Y-%m-%d")
CSS = "../css/seo.css"


# ------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------

with open(DATA, "r", encoding="utf-8") as f:
    data = json.load(f)

BUSES = data.get("buses", [])


# ------------------------------------------------------------
# BENGALI PLACE NAMES
# ------------------------------------------------------------

BN = {
    "Bankura": "বাঁকুড়া",
    "Digha": "দীঘা",
    "Kolkata": "কলকাতা",
    "Medinipur": "মেদিনীপুর",
    "Bardhaman": "বর্ধমান",
    "Burdwan": "বর্ধমান",
    "Kharagpur": "খড়্গপুর",
    "Siliguri": "শিলিগুড়ি",
    "Cooch Behar": "কোচবিহার",
    "Asansol": "আসানসোল",
    "Durgapur": "দুর্গাপুর",
    "Purulia": "পুরুলিয়া",
    "Jhargram": "ঝাড়গ্রাম",
    "Contai": "কাঁথি",
    "Tamluk": "তমলুক",
    "Bishnupur": "বিষ্ণুপুর",
    "Khatra": "খাতড়া",
    "Alipurduar": "আলিপুরদুয়ার",
    "Dinhata": "দিনহাটা",
    "Mathabhanga": "মাথাভাঙ্গা",
    "Ghatal": "ঘাটাল",
    "Nabadwip": "নবদ্বীপ",
    "Arambagh": "আরামবাগ",
    "Manbazar": "মানবাজার",
    "Tarkeshwar": "তারকেশ্বর",
    "Tarakeswar": "তারকেশ্বর",
    "Mecheda": "মেছেদা",
    "Haldia": "হলদিয়া",
    "Baruipur": "বারুইপুর",
    "Esplanade": "এসপ্ল্যানেড",
    "Howrah": "হাওড়া",
    "Ranaghat": "রানাঘাট",
    "Krishnanagar": "কৃষ্ণনগর",
    "Malda": "মালদা",
    "Raiganj": "রায়গঞ্জ",
    "Balurghat": "বালুরঘাট",
    "Suri": "সিউড়ি",
    "Sainthia": "সাঁইথিয়া",
    "Bolpur": "বোলপুর",
    "Kalna": "কালনা",
    "Guskara": "গুসকরা",
    "Katwa": "কাটোয়া",
    "Bandel": "বান্দেল",
    "Chandannagar": "চন্দননগর",
    "Kalyani": "কল্যাণী",
    "Barasat": "বারাসাত",
    "Barrackpore": "ব্যারাকপুর",
    "Dunlop": "ডানলপ",
    "Garia": "গড়িয়া",
    "Jangipur": "জঙ্গীপুর",
    "Berhampore": "বহরমপুর",
    "Berhampur": "বহরমপুর",
    "Salar": "সালার",
    "Kirnahar": "কীর্ণাহার",
    "Ilam Bazar": "ইলাম বাজার",
}


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")


def esc(value):
    return html.escape(str(value or ""), quote=True)


def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def bn(name):
    return BN.get(clean_text(name))


def bn_route(origin, destination):
    bo = bn(origin)
    bt = bn(destination)
    return f"{bo} থেকে {bt}" if bo and bt else None


def parse_time(value):
    if not value:
        return None

    text = clean_text(value)

    match = re.match(
        r"^(\d{1,2}):(\d{2})\s*(AM|PM)?",
        text,
        re.I,
    )

    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2))
    suffix = (match.group(3) or "").upper()

    if minute > 59:
        return None

    if suffix == "PM" and hour < 12:
        hour += 12

    if suffix == "AM" and hour == 12:
        hour = 0

    if hour > 23:
        return None

    return hour * 60 + minute


def format_time(minutes):
    if minutes is None:
        return "—"

    hour = (minutes // 60) % 24
    minute = minutes % 60
    suffix = "AM" if hour < 12 else "PM"
    hour12 = hour % 12 or 12

    return f"{hour12}:{minute:02d} {suffix}"


def fmt_duration(minutes):
    if minutes is None:
        return "—"

    hours, mins = divmod(int(minutes), 60)

    if hours:
        return f"{hours}h {mins:02d}m"

    return f"{mins}m"


def calculate_duration(bus):
    dep = parse_time(bus.get("departure_time"))
    arr = parse_time(bus.get("arrival_time"))

    if dep is None or arr is None:
        return None

    duration = arr - dep

    if duration < 0:
        duration += 1440

    if duration <= 0 or duration >= 900:
        return None

    return duration


def bus_stops(bus):
    stops = bus.get("stoppages") or []
    result = []

    for stop in stops:
        if isinstance(stop, dict):
            name = clean_text(stop.get("name"))
        else:
            name = clean_text(stop)

        if name and name not in result:
            result.append(name)

    return result


def total_stops(bus):
    explicit = bus.get("total_stoppages")

    if explicit:
        try:
            return int(explicit)
        except (TypeError, ValueError):
            pass

    return len(bus_stops(bus))


def bus_type_label(value):
    text = clean_text(value).lower()

    if any(
        key in text
        for key in ("gov", "sbstc", "nbstc", "wbtc")
    ):
        return "Government"

    if "ac" in text and "non" not in text:
        return "AC"

    if text:
        return clean_text(value)

    return "Bus"


def operator_name(bus):
    value = clean_text(bus.get("operator"))

    if value in ("", "—", "Operator not listed") or not value:
        return ""

    return value


# ------------------------------------------------------------
# ROUTE INDEX
# ------------------------------------------------------------

def route_pairs():
    routes = defaultdict(list)

    for bus in BUSES:
        origin = clean_text(bus.get("origin"))
        destination = clean_text(bus.get("destination"))

        if not origin or not destination:
            continue

        if origin == "—" or destination == "—":
            continue

        if origin == destination:
            continue

        routes[(origin, destination)].append(bus)

    return routes


FWD = route_pairs()

groups = defaultdict(list)

for (origin, destination), buses in FWD.items():
    groups[tuple(sorted([origin, destination]))].extend(buses)

groups = {
    key: buses
    for key, buses in groups.items()
    if len(buses) >= 2
}


def buses_for(origin, destination):
    return FWD.get((origin, destination), [])


route_meta = {}

for origin, destination in sorted(groups):
    for o, t in (
        (origin, destination),
        (destination, origin),
    ):
        buses = buses_for(o, t)

        if buses:
            route_meta[(o, t)] = buses


# ------------------------------------------------------------


# VIA COMBOS (computed from stoppages - fully data-driven)
# ------------------------------------------------------------

def via_stops(o, t, bs, min_buses=3, top=2):
    counts = Counter()
    for b in bs:
        seq = [x for x in [clean_text(b.get("origin"))] + [clean_text(s.get("name")) for s in (b.get("stoppages") or [])] + [clean_text(b.get("destination"))] if x and x != "—"]
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

for (o_, t_), bs_ in route_meta.items():
    vv_ = via_stops(o_, t_, bs_)
    if vv_:
        VIA[(o_, t_)] = vv_

# HTML SHELL
# ------------------------------------------------------------



def header_html():
    return """<header class="top-bar">
  <div class="top-inner">
    <a href="../index.html" class="brand">Bus<span class="accent">Jatri</span></a>
    <div class="top-actions">
      <button class="top-btn" onclick="seoLang()" id="langBtn">বাংলা</button>
      <button class="top-btn" onclick="seoTheme()" id="themeBtn">🌙</button>
    </div>
  </div>
</header>"""


def footer_html():
    return """<footer class="seo-footer">
  <div class="container">
    <div class="footer-links">
      <a href="../index.html">Home</a>
      <a href="../about.html">About</a>
      <a href="../contact.html">Contact</a>
      <a href="../privacy-policy.html">Privacy Policy</a>
      <a href="./">All Routes</a>
    </div>
    <p>© 2026 BusJatri — West Bengal Bus Timetable<br>
    Not affiliated with any transport corporation</p>
  </div>
</footer>"""


def shell(title, description, canonical, body, schema=""):
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
<script>
function seoTheme(){{var d=document.body;d.classList.toggle('dark');document.getElementById('themeBtn').textContent=d.classList.contains('dark')?'☀️':'🌙';try{{localStorage.setItem('seo-theme',d.classList.contains('dark')?'dark':'light')}}catch(e){{}}}}
function seoLang(){{var b=document.body;b.classList.toggle('lang-bn');document.getElementById('langBtn').textContent=b.classList.contains('lang-bn')?'English':'বাংলা';try{{localStorage.setItem('seo-lang',b.classList.contains('lang-bn')?'bn':'en')}}catch(e){{}}}}
function toggleBus(card,e){{if(e&&e.target&&e.target.closest('a'))return;card.classList.toggle('open')}}
function toggleAllBuses(btn){{var h=document.querySelectorAll('.bus-card.hidden-bus');var s=h.length>0&&h[0].classList.contains('show');h.forEach(function(c){{c.classList.toggle('show',!s)}});btn.innerHTML=s?'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6"/></svg> Show all buses':'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m18 15-6-6-6 6"/></svg> Show fewer'}}
function swapFromTo(){{var f=document.getElementById('fromInput'),t=document.getElementById('toInput');if(!f||!t)return;var x=f.value;f.value=t.value;t.value=x}}
function seoSearch(){{var f=document.getElementById('fromInput'),t=document.getElementById('toInput'),s=document.getElementById('stopInput');if(!f)return;var from=f.value.trim(),to=t?t.value.trim():'',stop=s?s.value.trim():'';if(from&&to){{window.location.href='../index.html#/search?from='+encodeURIComponent(from)+'&to='+encodeURIComponent(to)}}else if(stop){{window.location.href='../index.html#/search?stop='+encodeURIComponent(stop)}}else if(from){{window.location.href='../index.html#/search?from='+encodeURIComponent(from)}}}}
(function(){{try{{var th=localStorage.getItem('seo-theme');if(th==='dark')document.body.classList.add('dark');var ln=localStorage.getItem('seo-lang');if(ln==='bn')document.body.classList.add('lang-bn')}}catch(e){{}}}})();
</script>
</head>
<body>
{header_html()}
<main class="container" style="padding-top:14px;padding-bottom:48px">
{body}
</main>
{footer_html()}
</body>
</html>"""


def jsonld(payload):
    return (
        '<script type="application/ld+json">'
        + json.dumps(payload, ensure_ascii=False)
        + "</script>"
    )


def faq_schema(faqs):
    return jsonld({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": answer,
                },
            }
            for question, answer in faqs
        ],
    })


def breadcrumb_schema(items):
    return jsonld({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index,
                "name": name,
                "item": (
                    path
                    if path.startswith("http")
                    else f"{BASE}{path}"
                ),
            }
            for index, (name, path) in enumerate(items, 1)
        ],
    })


def website_schema():
    return jsonld({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME,
        "url": BASE,
    })


# ------------------------------------------------------------
# ROUTE DATA
# ------------------------------------------------------------

def route_stats(buses):
    times = [
        parse_time(bus.get("departure_time"))
        for bus in buses
    ]
    times = [time for time in times if time is not None]

    first = min(times) if times else None
    last = max(times) if times else None

    durations = [
        calculate_duration(bus)
        for bus in buses
    ]
    durations = [
        value for value in durations
        if value is not None
    ]

    median_duration = None

    if durations:
        durations.sort()
        median_duration = durations[len(durations) // 2]

    operators = sorted({
        operator_name(bus)
        for bus in buses
        if operator_name(bus)
    })

    return {
        "first": first,
        "last": last,
        "duration": median_duration,
        "operators": operators,
    }


def stoppage_summary(buses):
    counter = Counter()

    for bus in buses:
        seen = set()

        for stop in bus_stops(bus):
            if stop in seen:
                continue

            seen.add(stop)
            counter[stop] += 1

    if not counter:
        return []

    threshold = max(2, len(buses) // 3)

    return [
        name
        for name, count in counter.most_common(12)
        if count >= threshold
    ][:8]


# ------------------------------------------------------------
# ROUTE VISUAL
# ------------------------------------------------------------

def route_stops_html(buses):
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
</section>"""




def bus_card(bus, idx=0):
    name = clean_text(bus.get("bus_name")) or "Bus service"
    dep = format_time(parse_time(bus.get("departure_time")))
    arr = format_time(parse_time(bus.get("arrival_time")))
    operator = operator_name(bus)
    stops_list = bus_stops(bus)
    n_stops = len(stops_list)
    duration = calculate_duration(bus)
    dur_text = fmt_duration(duration) if duration else "—"
    fare = clean_text(bus.get("fare")) or "—"
    bt_raw = (bus.get("bus_type") or "").lower()
    badge = ""
    if "gov" in bt_raw or "sbstc" in bt_raw or "nbstc" in bt_raw or "wbtc" in bt_raw:
        badge = '<span class="badge badge-govt">Govt</span>'
    elif "private" in bt_raw:
        badge = '<span class="badge badge-private">Private</span>'
    if " ac" in bt_raw and "non" not in bt_raw:
        badge += '<span class="badge badge-ac">AC</span>'
    elif "non ac" in bt_raw:
        badge += '<span class="badge badge-nonac">Non-AC</span>'

    origin = clean_text(bus.get("origin")) or ""
    destination = clean_text(bus.get("destination")) or ""
    dep_html = f'<span class="dep.time">{esc(dep)}</span>' if dep != "—" else '<span class="no-time">—:—</span>'

    meta = '<div class="bus-meta-grid">'
    if operator:
        meta += f'<div class="meta-item"><div class="lb">Operator</div><div class="vl">{esc(operator)}</div></div>'
    meta += f'<div class="meta-item"><div class="lb">Stops</div><div class="vl">{n_stops}</div></div>'
    if duration:
        meta += f'<div class="meta-item"><div class="lb">Duration</div><div class="vl">{esc(dur_text)}</div></div>'
    if fare != "—":
        meta += f'<div class="meta-item"><div class="lb">Fare</div><div class="vl">{esc(fare)}</div></div>'
    meta += '</div>'

    tl = '<div class="mini-timeline">'
    for st in stops_list:
        tl += f'<div class="mini-stop"><span class="dot"></span><span class="st-name">{esc(st)}</span></div>'
    tl += '</div>'

    return f"""<div class="bus-card" style="--i:{idx}" onclick="toggleBus(this,event)">
  <div class="bus-head">
    <div class="bus-info">
      <div class="name">{esc(name)} {badge}</div>
      <div class="route">{esc(origin)} \u2192 {esc(destination)}</div>
    </div>
    {dep_html}
    <svg class="chev" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6"/></svg>
  </div>
  <div class="bus-body"><div class="bus-body-inner">
    {meta}
    {tl}
  </div></div>
</div>"""


def _board_data(origin, destination):
    """Collect timed departures for board tabs: origin + destination."""
    import json as _j
    tabs = {}
    for place in [origin, destination]:
        key = place.lower()
        if key in tabs:
            continue
        deps = []
        for bus in BUSES:
            bt = clean_text(bus.get("origin", ""))
            if key in bt.lower():
                t = parse_time(bus.get("departure_time"))
                if t is not None:
                    deps.append({
                        "t": t,
                        "n": clean_text(bus.get("bus_name")) or "Bus",
                        "d": clean_text(bus.get("destination")) or "",
                    })
        deps.sort(key=lambda x: x["t"])
        tabs[place] = deps[:12]
    return _j.dumps(tabs, ensure_ascii=False)


def generate_route_page(origin, destination, buses):
    filename = f"{slug(origin)}-to-{slug(destination)}.html"
    route_bn = bn_route(origin, destination)
    stats = route_stats(buses)
    first = format_time(stats["first"])
    last = format_time(stats["last"])
    duration = stats["duration"]
    operators = stats["operators"]
    count = len(buses)
    dur_text = fmt_duration(duration) if duration else "\u2014"

    title = f"{origin} to {destination} Bus Time Table | {SITE_NAME}"
    description = f"{origin} to {destination} bus timings, operators, stoppages. {count} buses listed. First {first}, last {last}."[:300]
    canonical = f"{BASE}/bus-time-table/{filename}"
    major_stops = stoppage_summary(buses)

    faqs = [
        (f"What is the first bus from {origin} to {destination}?",
         f"The first bus departs at {first}." if stats["first"] is not None else "Check the timetable above for departure times."),
        (f"What is the last bus from {origin} to {destination}?",
         f"The last bus departs at {last}." if stats["last"] is not None else "Check the timetable above for departure times."),
        (f"How many buses run from {origin} to {destination}?",
         f"{count} bus services are listed on this route."),
        (f"How long is the journey from {origin} to {destination}?",
         f"The journey takes approximately {dur_text}." if duration else "Journey time varies by bus and traffic."),
    ]

    bn_sub = f'<span class="label-bn" style="display:none">{esc(route_bn)} \u09ac\u09be\u09b8\u09c7\u09b0 \u09b8\u09ae\u09af\u09bc\u09b8\u09c2\u099a\u09c0</span>' if route_bn else ""
    operators_str = ", ".join(operators[:3]) if operators else "Multiple operators"
    arrow = "\u2192"

    hero = f"""<div class="breadcrumb"><a href="../index.html">Home</a><span class="sep">/</span><a href="./">Bus Time Table</a><span class="sep">/</span><span>{esc(origin)} {arrow} {esc(destination)}</span></div>
<div class="hero">
  <div class="hero-route-line"><svg class="icon" viewBox="0 0 24 24"><path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"/><path d="M4 16h16"/><path d="M4 16v2a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-2"/><path d="M17 16v2a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-2"/><path d="M6 10h12"/></svg></div>
  <span class="eyebrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v2a2 2 0 0 0 0 4v2a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-2a2 2 0 0 0 0-4Z"/><path d="M10 6v12" stroke-dasharray="2 3"/></svg> {esc(origin)} {arrow} {esc(destination)} \u00b7 West Bengal</span>
  <h1>{esc(origin)} <span class="arrow">{arrow}</span> <span class="accent">{esc(destination)}</span> Bus Time Table</h1>
  {bn_sub}
  <p class="tagline">Complete bus timings, operators and stoppages. {count} buses on this route.</p>
  <div class="stat-chips">
    <span class="stat-chip"><strong>{count}</strong> buses</span>
    <span class="stat-chip">First <strong>{esc(first)}</strong></span>
    <span class="stat-chip">Last <strong>{esc(last)}</strong></span>
    <span class="stat-chip">~<strong>{esc(dur_text)}</strong> journey</span>
    <span class="stat-chip">{esc(operators_str)}</span>
  </div>
</div>"""

    search_html = f"""<div class="search-box">
  <div class="search-row">
    <div class="search-field">
      <label><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s7-6.1 7-11.3A7 7 0 0 0 5 9.7C5 14.9 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.3"/></svg> From</label>
      <input id="fromInput" placeholder="e.g. {esc(origin)}" value="{esc(origin)}">
    </div>
    <button class="swap-btn" onclick="swapFromTo()" title="Swap"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 3h5v5"/><path d="M8 3H3v5"/><path d="M21 3 12 12"/><path d="M3 3l9 9"/></svg></button>
    <div class="search-field">
      <label><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 3v2.2M12 18.8V21M21 12h-2.2M5.2 12H3"/></svg> To</label>
      <input id="toInput" placeholder="e.g. {esc(destination)}" value="{esc(destination)}">
    </div>
    <div class="search-field">
      <label><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="6" cy="6" r="2"/><circle cx="6" cy="18" r="2"/><path d="M6 8v8"/><path d="M6 12h9a3 3 0 0 0 3-3V7"/></svg> Stoppage <span class="via-hint">(optional)</span></label>
      <input id="stopInput" placeholder="e.g. Kolaghat">
    </div>
  </div>
  <div class="search-actions">
    <button class="search-btn" onclick="seoSearch()">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m20 20-4.3-4.3"/></svg>
      Search buses
    </button>
  </div>
</div>"""

    board_json = _board_data(origin, destination)
    tabs_keys = list(json.loads(board_json).keys())
    first_tab = esc(tabs_keys[0]) if tabs_keys else ""

    board_html = f"""<div class="lv-wrap">
  <div class="lv-clock-wrap">
    <div>
      <div class="lv-clock-label"><span class="ldot"></span> Live Departures</div>
      <div class="lv-clock-big" id="lvClock">--:--:--<small>IST</small></div>
    </div>
    <div class="lv-geo" id="lvGeo">West Bengal</div>
  </div>
  <div class="lv-board">
    <div class="lv-tabs" id="lvTabs"></div>
    <div id="lvRows"></div>
  </div>
</div>
<script>
var SEO_TABS={board_json};
var boardTab="{first_tab}";
function t2m(t){{var m=String(t).match(/^(\\d+):#+)\s*(AM|PM)?/i);if(!m)return null;var h=+m[1],mm=+m[2],ap=(m[3]|"").toUpperCase();if(mm>59)return null;if(ap){{if(h<1||h>12)return null}}else{{if(h>23)return null}}if(ap==="PM"&&h<12)h+=12;if(ap==="AM"&&h===12)h=0;return h*60+mm}}
function minutesNow(){{var d=new Date();return d.getHours()*60+d.getMinutes()}}
function cd(m){{if(m<60)return m+"m";var h=Math.floor(m/60),r=m%60;return h+"h "+r?r+"m":"")}}
function fmtT(m){{var h=Math.floor(m/60),mm=m%60;var ap=h>=12?"PM":"AM";if(h>12)h-=12;if(h===0)h=12;return h+":"+String(mm).padStart(2,"0")+" "+ap}}
function renderBoard(anim){{var el=document.getElementById("lvRows");if(el)el.classList.toggle("still",anim===false);var tabs=Object.keys(SEO_TABS);document.getElementById("lvTabs").innerHTML=tabs.map(function(t){{return '<button class="lv-tab'+(t===boardTab?" on":"")+'" onclick="boardTab=\\''+t+'\\';renderBoard(true)">'+t+'</button>'}}).join("");var deps=SEO_TABS[boardTab]||[],now=minutesNow();var nextIdx=-1;for(var i=0;i<deps.length;i++){{if(deps[i].t>now){{nextIdx=i;break}}}}if(nextIdx<0&&deps.length)nextIdx=0;var rows=deps.map(function(n,i){{var cls="",right="";if(i===nextIdx){{cls="next";right='<span class="ltag">'+(n.t<=now?"tmrw +":"in ")+cd(Math.abs(n.t-now))+'</span>'}}else if(i>nextIdx){{right='<span class="lgone">+'+cd(n.t-now)+'</span>'}}else{{cls="past";right='<span class="lgone">departed</span>'}}return '<div class="lv-row '+cls+'" style="animation-delay:'+(i*0.07)+'s">'+'<span class="lt">'+fmtT(n.t).replace(" ","")+'</span>'+'<span class="lnm">'+n.n+'</span>'+'<span class="ldst">'+arrow+' '+n.d+'</span>'+right+'</div>'}}).join("");el.innerHTML=rows||'<div class="lv-row"><span class="lnm">No timed departures</span></div>'}}
function tickClock(){{var t=new Date().toLocaleTimeString("en-IN",{{hour12:false,timeZone:"Asia/Kolkata"}});document.getElementById("lvClock").innerHTML=t+"<small>IST</small>"}}
tickClock();setInterval(tickClock,1000);renderBoard(true);setInterval(function(){{renderBoard(false)}},30000);
</script>"""

    sorted_buses = sorted(buses, key=lambda b: parse_time(b.get("departure_time")) or 9999)
    visible = 4
    cards = "".join(bus_card(b, i) for i, b in enumerate(sorted_buses[:visible]))
    hidden_cards = ""
    for i, b in enumerate(sorted_buses[visible:]):
        bc = bus_card(b, i + visible)
        bc = bc.replace('<div class="bus-card"', '<div class="bus-card hidden-bus"', 1)
        hidden_cards += bc
    show_all = ""
    if len(sorted_buses) > visible:
        show_all = f'<button class="show-all-btn" id="showAllBtn" onclick="toggleAllBuses(this)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6"/></svg> Show all {len(sorted_buses)} buses</button>'

    bus_list = f"""<section class="section">
  <div class="section-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v2a2 2 0 0 0 0 4v2a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-2a2 2 0 0 0 0-4z"/><path d="M10 6v12" stroke-dasharray="2 3"/></svg> All Buses on This Route</div>
  <div class="bus-list">{cards}{hidden_cards}</div>
  {show_all}
</section>"""

    route_section = route_stops_html(buses)

    major_section = ""
    if major_stops:
        chips = "".join(f'<a class="via-chip" style="--i:{i}" href="{slug(origin)}-to-{slug(destination)}-via-{slug(s)}.html">{esc(s)}</a>' for i, s in enumerate(major_stops))
        major_section = f"""<section class="section">
  <div class="section-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="6" cy="6" r="2"/><circle cx="6" cy="18" r="2"/><path d="M6 8v8"/><path d="M6 12h9a3 3 0 0 0 3-3V7"/></svg> Popular Stops on This Route</div>
  <div class="via-chips">{chips}</div>
</section>"""

    faq_html = "".join(
        f'<div class="faq-item" style="--i:{i}" onclick="this.classList.toggle(\'open\')"><div class="faq-q">{esc(q)}<svg class="chev" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6"/></svg></div><div class="faq-a"><p>{esc(a)}</p></div></div>'
        for i, (q, a) in enumerate(faqs)
    )
    faq_section = f"""<section class="section">
  <div class="section-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.5h.01"/></svg> Frequently Asked Questions</div>
  <div class="faq-list">{faq_html}</div>
</section>"""

    related = [(o, t) for (o, t) in route_meta if o == origin and t != destination]
    related = sorted(related, key=lambda p: -len(route_meta[p]))[:8]
    related_section = ""
    if related:
        links = "".join(f'<a class="rel-chip" style="--i:{i}" href="{slug(o)}-to-{slug(t)}.html">{esc(o)} {arrow} {esc(t)}</a>' for i, (o, t) in enumerate(related))
        related_section = f"""<section class="section">
  <div class="section-title">More Routes from {esc(origin)}</div>
  <div class="chip-row">{links}</div>
</section>"""

    reverse_section = ""
    if (destination, origin) in route_meta:
        rev_file = f"{slug(destination)}-to-{slug(origin)}.html"
        reverse_section = f'<section class="section"><a class="rel-chip" href="{rev_file}">\u21a9 {esc(destination)} {arrow} {esc(origin)} (return)</a></section>'

    ad1 = '<div class="ad-zone" id="ad1"></div>'
    ad2 = '<div class="ad-zone" id="ad2"></div>'
    ad3 = '<div class="ad-zone" id="ad3"></div>'

    body = hero + search_html + board_html + ad1 + bus_list + route_section + major_section + ad2 + faq_section + reverse_section + related_section + ad3

    schema = (
        faq_schema(faqs) + "\n" +
        breadcrumb_schema([("Home", "/"), ("Bus Timetable", "/bus-time-table/"), (f"{origin} to {destination}", f"/bus-time-table/{filename}")])
    )
    return filename, shell(title, description, canonical, body, schema)


def generate_place_page(place, buses):
    count = len(buses)
    bengali = bn(place)

    destinations = Counter(
        clean_text(bus.get("destination"))
        for bus in buses
        if clean_text(bus.get("destination"))
        and clean_text(bus.get("destination")) != "—"
    )

    top_destinations = destinations.most_common(15)

    filename = f"buses-from-{slug(place)}.html"

    title = (
        f"Buses from {place} – Time Table & Routes | বাস সময়সূচী | {SITE_NAME}"
    )

    description = (
        f"Find bus services from {place}, including "
        f"departure times, destinations, operators and "
        f"route information on {SITE_NAME}."
    )

    canonical = (
        f"{BASE}/bus-time-table/{filename}"
    )

    bengali_line = ""

    if bengali:
        bengali_line = f"""
<div style="color:var(--ink-dim);margin-top:6px">
  {esc(bengali)} থেকে বাস
</div>
"""

    route_links = []

    for destination, number in top_destinations:
        route = (place, destination)

        if route not in route_meta:
            continue

        href = (
            f"{slug(place)}-to-{slug(destination)}.html"
        )

        route_links.append(
            f"""
<a href="{href}"
   style="
     display:flex;
     justify-content:space-between;
     gap:12px;
     padding:13px 14px;
     border-bottom:1px solid var(--border);
     text-decoration:none;
   ">

  <span>
    {esc(place)} → {esc(destination)}
  </span>

  <span style="
    color:var(--ink-dim);
    font-size:13px;
    white-space:nowrap;
  ">
    {number} buses
  </span>

</a>
"""
        )

    if not route_links:
        route_links = [
            """
<p style="padding:14px;color:var(--ink-dim)">
  Route pages are not currently available for the
  destinations listed in this dataset.
</p>
"""
        ]

    body = f"""
<section style="
  background:var(--panel);
  border:1px solid var(--border);
  border-radius:20px;
  padding:24px;
  margin-bottom:24px;
">

  <div style="
    font-size:13px;
    color:var(--ink-dim);
    margin-bottom:14px;
  ">
    <a href="../index.html">Home</a>
    <span style="margin:0 5px">›</span>
    <a href="./">Bus Timetable</a>
    <span style="margin:0 5px">›</span>
    Buses from {esc(place)}
  </div>

  <h1 style="
    font-size:clamp(1.8rem,5vw,2.5rem);
    line-height:1.2;
    margin:0;
  ">
    Buses from {esc(place)}
  </h1>

  {bengali_line}

  <p style="
    color:var(--ink-dim);
    line-height:1.7;
    max-width:700px;
    margin-bottom:0;
  ">
    Explore listed bus services departing from
    {esc(place)}, including destinations, operators
    and available timetable information.
  </p>

</section>

<section style="
  display:flex;
  gap:10px;
  flex-wrap:wrap;
  margin-bottom:32px;
">

  <div style="
    flex:1 1 170px;
    background:var(--panel);
    border:1px solid var(--border);
    border-radius:14px;
    padding:15px;
  ">

    <div style="font-size:12px;color:var(--ink-dim)">
      Listed services
    </div>

    <strong style="font-size:1.25rem">
      {count}
    </strong>

  </div>

  <div style="
    flex:1 1 170px;
    background:var(--panel);
    border:1px solid var(--border);
    border-radius:14px;
    padding:15px;
  ">

    <div style="font-size:12px;color:var(--ink-dim)">
      Destinations
    </div>

    <strong style="font-size:1.25rem">
      {len(destinations)}
    </strong>

  </div>

</section>

<section>

  <h2 style="font-size:1.35rem">
    Popular Bus Routes from {esc(place)}
  </h2>

  <div style="
    background:var(--panel);
    border:1px solid var(--border);
    border-radius:16px;
    overflow:hidden;
  ">
    {''.join(route_links)}
  </div>

</section>

<section style="margin-top:34px">

  <h2 style="font-size:1.35rem">
    All Destinations from {esc(place)}
  </h2>

  <p style="
    line-height:1.9;
    color:var(--ink-dim);
  ">
    {" · ".join(
        f"{esc(destination)} ({number})"
        for destination, number in destinations.most_common()
    )}
  </p>

</section>
"""

    schema = breadcrumb_schema([
        ("Home", "/"),
        ("Bus Timetable", "/bus-time-table/"),
        (
            f"Buses from {place}",
            f"/bus-time-table/{filename}",
        ),
    ])

    return filename, shell(
        title,
        description,
        canonical,
        body,
        schema,
    )


# ------------------------------------------------------------
# OUTPUT
# ------------------------------------------------------------

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

os.makedirs(OUT, exist_ok=True)

sitemap_urls = []
written = []


# Route pages
for (origin, destination), buses in sorted(route_meta.items()):

    filename, content = generate_route_page(
        origin,
        destination,
        buses,
    )

    path = os.path.join(
        OUT,
        filename,
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    sitemap_urls.append(
        f"{BASE}/bus-time-table/{filename}"
    )

    written.append(filename)


# Place pages
place_buses = defaultdict(list)

for bus in BUSES:
    origin = clean_text(bus.get("origin"))

    if origin and origin != "—":
        place_buses[origin].append(bus)


top_places = sorted(
    place_buses,
    key=lambda place: -len(place_buses[place]),
)[:30]


for place in top_places:

    filename, content = generate_place_page(
        place,
        place_buses[place],
    )

    path = os.path.join(
        OUT,
        filename,
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    sitemap_urls.append(
        f"{BASE}/bus-time-table/{filename}"
    )

    written.append(filename)

# Via pages (fully data-driven - computed from stoppages)
via_count = 0
for (origin, destination), vv_ in sorted(VIA.items(), key=lambda kv: -len(route_meta[kv[0]])):
    for via_stop in vv_:
        via_filename, via_content = generate_via_page(origin, destination, via_stop, route_meta[(origin, destination)])
        if via_filename is None:
            continue
        via_path = os.path.join(OUT, via_filename)
        with open(via_path, "w", encoding="utf-8") as f:
            f.write(via_content)
        sitemap_urls.append(f"{BASE}/bus-time-table/{via_filename}")
        written.append(via_filename)
        via_count += 1


# ------------------------------------------------------------
# ROUTE INDEX
# ------------------------------------------------------------

by_origin = defaultdict(list)

for origin, destination in route_meta:
    by_origin[origin].append(
        (origin, destination)
    )


origin_sections = []

for origin, routes in sorted(
    by_origin.items(),
    key=lambda item: -len(item[1]),
):

    links = []

    for o, t in sorted(routes):
        filename = (
            f"{slug(o)}-to-{slug(t)}.html"
        )

        links.append(
            f"""
<a href="{filename}"
   style="
     display:block;
     padding:11px 13px;
     border-bottom:1px solid var(--border);
     text-decoration:none;
   ">

  <span>
    {esc(o)} → {esc(t)}
  </span>

  <span style="
    float:right;
    color:var(--ink-dim);
    font-size:13px;
  ">
    {len(route_meta[(o, t)])} buses
  </span>

</a>
"""
        )

    origin_sections.append(
        f"""
<section style="margin-top:28px">

  <h2 style="
    font-size:1.2rem;
    margin-bottom:10px;
  ">
    {esc(origin)}
  </h2>

  <div style="
    background:var(--panel);
    border:1px solid var(--border);
    border-radius:15px;
    overflow:hidden;
  ">
    {''.join(links)}
  </div>

</section>
"""
    )


place_links = " · ".join(
    f'<a href="buses-from-{slug(place)}.html">'
    f'Buses from {esc(place)}</a>'
    for place in top_places[:20]
)


index_body = f"""
<section style="
  background:var(--panel);
  border:1px solid var(--border);
  border-radius:20px;
  padding:24px;
">

  <div style="
    font-size:13px;
    color:var(--ink-dim);
    margin-bottom:14px;
  ">
    <a href="../index.html">Home</a>
    <span style="margin:0 5px">›</span>
    Bus Timetable
  </div>

  <h1 style="
    font-size:clamp(1.8rem,5vw,2.5rem);
    line-height:1.2;
    margin:0;
  ">
    West Bengal Bus Time Table · সব বাস সময়সূচী
  </h1>

  <p style="
    max-width:720px;
    color:var(--ink-dim);
    line-height:1.7;
    margin-bottom:0;
  ">
    Browse BusJatri route timetables for bus services
    across West Bengal. Find departures, operators,
    destinations and commonly listed stoppages.
  </p>

</section>

<section style="margin-top:28px">

  <h2 style="font-size:1.3rem">
    Popular Starting Places
  </h2>

  <p style="
    line-height:1.9;
    color:var(--ink-dim);
  ">
    {place_links}
  </p>

</section>

{''.join(origin_sections)}
"""


index_schema = (
    website_schema()
    + "\n"
    + breadcrumb_schema([
        ("Home", "/"),
        ("Bus Timetable", "/bus-time-table/"),
    ])
)


with open(
    os.path.join(OUT, "index.html"),
    "w",
    encoding="utf-8",
) as f:
    f.write(
        shell(
            "West Bengal Bus Time Table – All Routes | সব বাস সময়সূচী | BusJatri",
            (
                "Browse West Bengal bus timetables with "
                "route information, operators, departures "
                "and stoppages on BusJatri."
            ),
            f"{BASE}/bus-time-table/",
            index_body,
            index_schema,
        )
    )


# ------------------------------------------------------------
# SITEMAP
# ------------------------------------------------------------

sitemap = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    (
        "<url>"
        f"<loc>{BASE}/</loc>"
        f"<lastmod>{LASTMOD}</lastmod>"
        "<priority>1.0</priority>"
        "</url>"
    ),
    (
        "<url>"
        f"<loc>{BASE}/bus-time-table/</loc>"
        f"<lastmod>{LASTMOD}</lastmod>"
        "<priority>0.9</priority>"
        "</url>"
    ),
]


for url in sitemap_urls:
    sitemap.append(
        "<url>"
        f"<loc>{url}</loc>"
        f"<lastmod>{LASTMOD}</lastmod>"
        "<priority>0.7</priority>"
        "</url>"
    )


sitemap.append("</urlset>")


with open(
    "sitemap.xml",
    "w",
    encoding="utf-8",
) as f:
    f.write("\n".join(sitemap))


# ------------------------------------------------------------
# ROBOTS
# ------------------------------------------------------------

with open(
    "robots.txt",
    "w",
    encoding="utf-8",
) as f:
    f.write(
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {BASE}/sitemap.xml\n"
    )


# ------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------

print(
    json.dumps(
        {
            "route_pages": len(route_meta),
            "place_pages": len(top_places),
            "via_pages": via_count,
            "total_generated_pages": len(written) + 1,
            "sitemap_urls": len(sitemap_urls) + 2,
            "site_base": BASE,
        },
        ensure_ascii=False,
        indent=2,
    )
)


