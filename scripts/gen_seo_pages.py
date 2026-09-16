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
    if len(buses) >= 1
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
</header>"""


def footer_html():
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
</head>
<body>
{header_html()}
<main class="container seo-main" style="padding-top:18px;padding-bottom:48px;max-width:720px">
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


def bus_card(bus):
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
    if dep == "—":
        dep_html = '<span class="no-time">Time N/A</span>'
    else:
        dep_html = f"{esc(dep)}<small>{esc(arr)} arr</small>"
    return f"""<div class="bus-row">
  <div class="dep">{dep_html}</div>
  <div class="bmid">
    <div class="op">{op_line}</div>
    <div class="mrow"><span>{esc(fare)}</span><span>~{esc(dur_text)}</span><span>{stops or 0} stops</span></div>
  </div>
  {badge}
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
    <span class="schip">🚌 {count} bus{'es' if count != 1 else ''}</span>
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
    {number} bus{'es' if number != 1 else ''}
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

# ============================================================
# BUS TIME TABLE INDEX (v6 — animated all-bus-time-table page)
# ============================================================

# ============================================================
# BUS TIME TABLE INDEX (v6 — animated all-bus-time-table page)
# ============================================================

by_origin = defaultdict(list)

for origin, destination in route_meta:
    by_origin[origin].append((origin, destination))


_total_places = len(by_origin)
_total_routes = len(route_meta)
_total_buses = sum(len(v) for v in route_meta.values())


# Popular: top 16 by total buses
_popular = sorted(
    by_origin.items(),
    key=lambda kv: -sum(len(route_meta[(o, t)]) for o, t in kv[1]),
)[:16]

_popular_html = "\n".join(
    f'<a class="place-card" style="--i:{i}" href="buses-from-{slug(p)}.html">'
    f'<div class="pc-top"><span class="pc-count">{len(rs)}</span></div>'
    f'<div class="pc-name">{esc(p)}</div>'
    f'<div class="pc-meta">{sum(len(route_meta[(o, t)]) for o, t in rs)} buses daily '
    f'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
    f'<path d="M5 12h14m-6-6 6 6-6 6"/></svg></div></a>'
    for i, (p, rs) in enumerate(_popular)
)


# A-Z groups (static HTML — crawlable place names)
_az_places = sorted(by_origin.keys())

_az_letters = sorted(set(
    (p[0].upper() if p and p[0].isalpha() else "#")
    for p in _az_places
))

_az_groups_html = []
for letter in _az_letters:
    group_places = [
        p for p in _az_places
        if (p[0].upper() if p and p[0].isalpha() else "#") == letter
    ]
    _az_groups_html.append(f'<div class="letter-group reveal" id="L{letter}">')
    _az_groups_html.append(f'<div class="letter-head">{letter}</div>')
    _az_groups_html.append('<div class="place-list">')
    for p in group_places:
        rs = by_origin[p]
        _az_groups_html.append(
            f'<div class="place-row" data-place="{esc(p)}">'
            f'<div class="pr-head" onclick="togglePlace(this,event)">'
            f'<span class="pr-dots"></span>'
            f'<span class="pr-name">{esc(p)}</span>'
            f'<span class="pr-n">{len(rs)} route{'s' if len(rs) != 1 else ''}</span>'
            f'<svg class="pr-chev" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6"/></svg>'
            f'</div><div class="pr-body"><div class="pr-inner"></div></div></div>'
        )
    _az_groups_html.append('</div></div>')

_az_html = "".join(_az_groups_html)


# Embedded JSON for search: place -> [[to, n], ...]
_btt_json = {}
for p in _az_places:
    _btt_json[p] = [
        [t, len(route_meta[(o, t)])]
        for o, t in sorted(by_origin[p])
    ]

_btt_json_str = json.dumps(_btt_json, ensure_ascii=False, separators=(",", ":"))


# Quick chips
_quick_names = [
    "Esplanade", "Howrah", "Digha", "Kolkata",
    "Bankura", "Siliguri", "Bardhaman", "Durgapur",
]
_quick_html = "".join(
    f'<button class="qchip" onclick="qsearch(\'{esc(n).lower()}\')">{esc(n)}</button>'
    for n in _quick_names
)


# FAQ
_faqs = [
    (
        "How many bus routes are listed on BusJatri?",
        f"The timetable covers {_total_routes:,} bus routes connecting {_total_places} places across West Bengal, with {_total_buses:,} daily bus services listed.",
    ),
    (
        "How do I find a bus time table on this page?",
        "Use the search box to type a place name (e.g. Esplanade, Digha). Matching places and routes appear instantly. You can also browse places alphabetically with the A-Z index.",
    ),
    (
        "Which places have the most bus connections?",
        "Esplanade, Howrah Station, Digha, Kolkata and Karunamoyee are the busiest starting points, with the widest choice of long-distance and local buses.",
    ),
    (
        "Are the bus timings updated?",
        "Timetable data is refreshed regularly from published SBSTC, WBTC, NBSTC and private operator schedules. Always confirm the current departure at the bus stand.",
    ),
]
_faq_html = "\n".join(
    f'<div class="faq-item" style="--i:{i}" onclick="this.classList.toggle(\'open\')">'
    f'<div class="faq-q">{esc(q)}<svg class="chev" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6"/></svg></div>'
    f'<div class="faq-a"><p>{esc(a)}</p></div></div>'
    for i, (q, a) in enumerate(_faqs)
)


# --- CSS (new classes only — base from seo.css) ---
_btt_css = """<style>
.hero h1{font-size:clamp(1.6rem,5vw,2.4rem)}
.stat-chip strong{font-variant-numeric:tabular-nums}
.eyebrow svg{animation:wiggle 2.6s ease-in-out infinite}
@keyframes wiggle{0%,100%{transform:translateX(0)}50%{transform:translateX(4px)}}
.live-dot{width:7px;height:7px;border-radius:50%;background:var(--green);display:inline-block;animation:lvPulse 1.8s infinite;flex-shrink:0}
.result-info{font-family:var(--font-mono);font-size:11px;color:var(--ink-dim);padding:10px 4px 0;display:none}
.clear-btn{background:none;border:none;cursor:pointer;color:var(--ink-dim);padding:6px;display:none}
.qchips{display:flex;gap:6px;flex-wrap:wrap;margin-top:12px}
.qchips-l{font-family:var(--font-mono);font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-dim);align-self:center;font-weight:600}
.qchip{background:var(--surface-2);border:1px solid var(--line);border-radius:999px;padding:6px 13px;font-size:12px;font-weight:600;color:var(--ink-dim);cursor:pointer;font-family:var(--font-body);transition:all .15s;min-height:32px}
.qchip:hover{border-color:var(--amber);color:var(--amber);background:var(--amber-soft)}
.place-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:9px}
.place-card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:13px 14px;cursor:pointer;color:var(--ink);transition:all .15s;animation:fadeUp .4s ease both;animation-delay:calc(var(--i)*35ms);display:flex;flex-direction:column;gap:3px;text-decoration:none}
.place-card:hover{border-color:var(--amber);background:var(--amber-soft);transform:translateY(-2px);box-shadow:var(--shadow-sm)}
.pc-top{display:flex;justify-content:space-between;align-items:center}
.pc-count{font-family:var(--font-mono);font-size:10px;font-weight:700;color:var(--amber-ink);background:var(--amber-soft);border-radius:999px;padding:2px 9px;align-self:flex-start}
.pc-name{font-weight:700;font-size:14.5px;line-height:1.25}
.pc-meta{font-size:11px;color:var(--ink-dim);display:flex;align-items:center;gap:4px}
.pc-meta svg{transition:transform .15s}
.place-card:hover .pc-meta svg{transform:translateX(3px);color:var(--amber)}
.rm-chip{display:inline-flex;align-items:center;gap:8px;background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:8px 15px;font-size:13px;font-weight:600;color:var(--ink);cursor:pointer;transition:all .15s;animation:fadeUp .3s ease both;text-decoration:none}
.rm-chip:hover{border-color:var(--amber);background:var(--amber-soft)}
.rm-chip .arr{color:var(--amber);font-family:var(--font-mono)}
.rm-chip .n{font-family:var(--font-mono);font-size:10px;color:var(--ink-dim);background:var(--surface-2);border-radius:999px;padding:1px 8px}
.az-nav{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:16px;position:sticky;top:60px;background:color-mix(in srgb,var(--bg) 92%,transparent);backdrop-filter:blur(10px);padding:8px 0;z-index:50;border-bottom:1px solid var(--line)}
.az-btn{font-family:var(--font-mono);font-size:12px;font-weight:700;color:var(--ink-dim);background:var(--surface);border:1px solid var(--line);border-radius:7px;width:30px;height:30px;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all .12s}
.az-btn:hover{border-color:var(--amber);color:var(--amber)}
.az-btn.has{color:var(--ink);border-color:var(--line-strong)}
.az-btn.miss{opacity:.35;cursor:default}
.letter-group{margin-bottom:6px}
.letter-head{font-family:var(--font-display);font-size:1.35rem;font-weight:700;color:var(--amber);padding:12px 4px 8px;position:sticky;top:100px;background:color-mix(in srgb,var(--bg) 90%,transparent);backdrop-filter:blur(8px);z-index:40;border-bottom:1px solid var(--line)}
.place-list{display:flex;flex-direction:column;gap:6px;padding-top:8px}
.place-row{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius-sm);overflow:hidden;animation:fadeUp .35s ease both}
.place-row.open{border-color:var(--amber)}
.pr-head{display:flex;align-items:center;gap:10px;padding:11px 14px;cursor:pointer;user-select:none}
.pr-head:hover{background:var(--surface-2)}
.pr-dots{width:9px;height:9px;border-radius:50%;background:var(--amber);flex-shrink:0}
.pr-name{flex:1;font-weight:700;font-size:14px}
.pr-n{font-family:var(--font-mono);font-size:10.5px;color:var(--ink-dim);white-space:nowrap}
.pr-chev{color:var(--ink-dim);transition:transform .25s;flex-shrink:0}
.place-row.open .pr-chev{transform:rotate(180deg)}
.pr-body{max-height:0;overflow:hidden;transition:max-height .3s ease}
.place-row.open .pr-body{max-height:800px}
.pr-inner{padding:4px 14px 12px;border-top:1px dashed var(--line-strong)}
.route-chip{display:inline-flex;align-items:center;gap:6px;background:var(--surface-2);border:1px solid var(--line);border-radius:999px;padding:5px 12px;font-size:12.5px;font-weight:600;color:var(--ink);cursor:pointer;transition:all .13s;margin:3px 4px 3px 0;text-decoration:none;opacity:0}
.route-chip:hover{border-color:var(--amber);background:var(--amber-soft);color:var(--ink)}
.route-chip .arr{color:var(--amber);font-family:var(--font-mono);font-size:11px}
.route-chip .n{font-family:var(--font-mono);font-size:9.5px;color:var(--ink-dim)}
.place-row .route-chip{opacity:0}
.place-row.open .route-chip{animation:popIn .34s cubic-bezier(.22,.61,.36,1) both;animation-delay:calc(min(var(--i),42)*13ms)}
@keyframes popIn{0%{opacity:0;transform:scale(.82) translateY(6px)}100%{opacity:1;transform:none}}
.pr-empty{padding:10px 4px;font-size:12px;color:var(--ink-dim)}
.reveal{opacity:0;transform:translateY(20px);transition:opacity .55s cubic-bezier(.22,.61,.36,1),transform .55s cubic-bezier(.22,.61,.36,1)}
.reveal.in{opacity:1;transform:none}
.empty{padding:34px 16px;text-align:center;color:var(--ink-dim);display:none;animation:fadeUp .3s ease both}
.empty svg{width:34px;height:34px;opacity:.5;margin-bottom:10px}
.empty b{display:block;color:var(--ink);font-size:15px;margin-bottom:3px}
@media(max-width:640px){.place-grid{grid-template-columns:repeat(2,1fr)}.az-nav{top:56px}.letter-head{top:96px;font-size:1.15rem}.search-field input{font-size:16px}}
@media(prefers-reduced-motion:reduce){.reveal,.eyebrow svg,.live-dot,.place-row .route-chip,.place-card,.tagline,.hero h1{animation:none!important;transition:none!important;opacity:1!important;transform:none!important}}
</style>"""


# --- JS (reads data from embedded JSON at runtime) ---
_btt_js = """<script>
var BTT=JSON.parse(document.getElementById('bttData').textContent);
var ROWS=[],LETTERS="";
(function(){
  var ps=Object.keys(BTT);
  ps.sort(function(a,b){return a.localeCompare(b)});
  for(var i=0;i<ps.length;i++){
    var p=ps[i],L=p[0].toUpperCase();
    if(!/[A-Z]/.test(L))L="#";
    ROWS.push([p,L,BTT[p]]);
    if(LETTERS.indexOf(L)<0)LETTERS+=L;
  }
})();
function slug(s){return(s||'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'')}
function renderAZ(){
  var nav=document.getElementById("azNav");nav.innerHTML="";
  LETTERS.split("").sort().forEach(function(L){
    var has=ROWS.some(function(r){return r[1]===L});
    var b=document.createElement("button");
    b.className="az-btn "+(has?"has":"miss");
    b.textContent=L;
    if(has)b.onclick=function(){document.getElementById("L"+L).scrollIntoView({behavior:"smooth",block:"start"})};
    nav.appendChild(b);
  });
}
function togglePlace(head,e){
  if(e&&e.target.closest("a"))return;
  var row=head.parentElement,inner=row.querySelector(".pr-inner");
  var place=row.getAttribute("data-place");
  if(!inner.children.length){
    var routes=BTT[place]||[];
    inner.innerHTML=routes.map(function(r,ci){
      var href=slug(place)+'-to-'+slug(r[0])+'.html';
      return '<a class="route-chip" style="--i:'+ci+'" href="'+href+'"><span class="arr">\\u2192</span><span class="to">'+r[0]+'</span><span class="n">'+r[1]+((r[1]===1)?' bus':' buses')+'</span></a>';
    }).join("")||'<div class="pr-empty">No routes</div>';
  }
  row.classList.toggle("open");
}
function qsearch(q){
  document.getElementById("q").value=q;doSearch();
  var t=document.getElementById("routeMatchesSec");
  if(t&&t.style.display!=="none")t.scrollIntoView({behavior:"smooth",block:"start"});
}
function doSearch(){
  var q=document.getElementById("q").value.trim().toLowerCase();
  var info=document.getElementById("resultInfo"),empty=document.getElementById("emptyState");
  var rm=document.getElementById("routeMatchesSec"),rmc=document.getElementById("rmChips");
  var pop=document.getElementById("popSection");
  document.querySelectorAll(".letter-group").forEach(function(g){g.style.display="";g.classList.add("in")});
  document.querySelectorAll(".place-row").forEach(function(r){r.style.display="";r.classList.remove("open")});
  if(!q){info.style.display="none";empty.style.display="none";rm.style.display="none";pop.style.display="";return}
  pop.style.display="none";
  var shown=0,routeChips=[];
  document.querySelectorAll(".letter-group").forEach(function(g){
    var any=false;
    g.querySelectorAll(".place-row").forEach(function(r){
      var n=r.getAttribute("data-place"),hit=n.toLowerCase().indexOf(q)>=0;
      if(hit){any=true;shown++;r.style.display=""}else r.style.display="none";
      var rs=BTT[n]||[];
      rs.forEach(function(rt){
        if(rt[0].toLowerCase().indexOf(q)>=0&&routeChips.length<24){
          var href=slug(n)+'-to-'+slug(rt[0])+'.html';
          routeChips.push('<a class="rm-chip" href="'+href+'">'+n+' <span class="arr">\\u2192</span> '+rt[0]+' <span class="n">'+rt[1]+((rt[1]===1)?' bus':' buses')+'</span></a>');
        }
      });
    });
    g.style.display=any?"":"none";
    if(any)g.classList.add("in");
  });
  rmc.innerHTML=routeChips.join("");
  rm.style.display=routeChips.length?"":"none";
  info.textContent="Showing "+shown+" places and "+routeChips.length+(routeChips.length>=24?"+":"")+" routes matching \\u201c"+q+"\\u201d";
  info.style.display="block";
  if(!shown&&!routeChips.length)empty.style.display="block";else empty.style.display="none";
}
function countUp(el,target,dur){
  var s=performance.now();
  function tk(now){
    var p=Math.min(1,(now-s)/dur);
    var e=1-Math.pow(1-p,3);
    el.textContent=Math.round(target*e).toLocaleString("en-IN");
    if(p<1)requestAnimationFrame(tk);
  }
  requestAnimationFrame(tk);
}
function initAnim(){
  document.querySelectorAll("[data-count]").forEach(function(el){
    var n=parseInt(el.getAttribute("data-count"),10);
    if(window.matchMedia&&window.matchMedia("(prefers-reduced-motion:reduce)").matches){el.textContent=n.toLocaleString("en-IN");return}
    countUp(el,n,1200);
  });
  var q=document.getElementById("q"),cb=document.getElementById("clearBtn");
  if(q&&cb)q.addEventListener("input",function(){cb.style.display=q.value?"flex":"none"});
  if("IntersectionObserver" in window){
    var io=new IntersectionObserver(function(es){
      es.forEach(function(e){if(e.isIntersecting){e.target.classList.add("in");io.unobserve(e.target)}});
    },{rootMargin:"0px 0px -8% 0px"});
    document.querySelectorAll(".reveal").forEach(function(el){io.observe(el)});
  }else{
    document.querySelectorAll(".reveal").forEach(function(el){el.classList.add("in")});
  }
}
(function(){
  try{
    var t=localStorage.getItem("seo-theme");
    if(t==="dark")document.body.classList.add("dark");
    if(t==="dark"&&document.getElementById("themeBtn"))document.getElementById("themeBtn").textContent="\\u2600\\ufe0f";
    var l=null;
    try{l=localStorage.getItem("bj-lang")||localStorage.getItem("seo-lang")}catch(e){}
    if(!l&&((navigator.language||"").toLowerCase().indexOf("bn")===0))l="bn";
    if(l==="bn"){document.body.classList.add("lang-bn");if(document.getElementById("langBtn"))document.getElementById("langBtn").textContent="English"}
  }catch(e){}
  renderAZ();
  initAnim();
})();
function toggleLang(){
  var bnMode=document.body.classList.toggle("lang-bn");
  try{localStorage.setItem("bj-lang",bnMode?"bn":"en")}catch(e){}
  var b=document.getElementById("langBtn");
  if(b)b.textContent=bnMode?"English":"বাংলা";
  var q=document.getElementById("q");
  if(q)q.placeholder=bnMode?"যেমন: এসপ্লেন্ড, দীঘা, বাঁকুড়া...":"e.g. Esplanade, Digha, Bankura...";
}
(function(){
  var nav=document.querySelector(".header-inner nav");
  if(nav){
    var b=document.createElement("button");
    b.id="langBtn";
    b.type="button";
    b.textContent="বাংলা";
    if(document.body.classList.contains("lang-bn")){
      b.textContent="English";
      var q=document.getElementById("q");
      if(q)q.placeholder="যেমন: এসপ্লেন্ড, দীঘা, বাঁকুড়া...";
    }
    b.style.cssText="font-family:var(--font-body);font-size:13px;font-weight:700;background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:6px 13px;cursor:pointer;color:var(--ink-dim);min-height:34px;line-height:1";
    b.onclick=toggleLang;
    nav.appendChild(b);
  }
})();
</script>"""


_index_body = f"""{_btt_css}

<div class="breadcrumb"><a href="../index.html">Home</a><span class="sep">/</span><span>Bus Time Table</span></div>

<div class="hero">
  <span class="eyebrow"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"/><path d="M4 16h16"/></svg> West Bengal Bus Routes</span>
  <h1><span class="label-en">West Bengal <span class="accent">Bus Time Table</span></span><span class="label-bn">পশ্চিমবঙ্গ <span class="accent">বাস টাইম টেবিল</span></span></h1>
  <p class="tagline"><span class="label-en">Complete bus timings for every route — SBSTC, WBTC, NBSTC and private operators across all districts.</span><span class="label-bn">প্রতিটি রুটের বাসের সম্পূর্ণ সময়সূচী — SBSTC, WBTC, NBSTC ও প্রাইভেট অপারেটর।</span></p>
  <div class="stat-chips">
    <span class="stat-chip"><strong data-count="{_total_places}">0</strong> <span class="label-en">places</span><span class="label-bn">স্থান</span></span>
    <span class="stat-chip"><strong data-count="{_total_routes}">0</strong> <span class="label-en">routes</span><span class="label-bn">রুট</span></span>
    <span class="stat-chip"><strong data-count="{_total_buses}">0</strong> <span class="label-en">bus services</span><span class="label-bn">বাস সার্ভিস</span></span>
  </div>
</div>

<div class="search-box">
  <div class="search-row">
    <div class="search-field">
      <label><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m20 20-4.3-4.3"/></svg> <span class="live-dot"></span> <span class="label-en">Search place or route</span><span class="label-bn">স্থান বা রুট খুঁজুন</span></label>
      <input id="q" type="text" placeholder="e.g. Esplanade, Digha, Bankura..." oninput="doSearch()" autocomplete="off">
    </div>
    <button class="clear-btn" id="clearBtn" onclick="document.getElementById('q').value='';doSearch()" title="Clear"><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg></button>
  </div>
  <div class="qchips">
    <span class="qchips-l"><span class="label-en">Quick:</span><span class="label-bn">দ্রুত:</span></span>
    {_quick_html}
  </div>
</div>
<div class="result-info" id="resultInfo"></div>

<div class="ad-zone" id="ad1"></div>

<section class="section" id="routeMatchesSec" style="display:none">
  <div class="section-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v2a2 2 0 0 0 0 4v2a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-2a2 2 0 0 0 0-4z"/><path d="M10 6v12" stroke-dasharray="2 3"/></svg> <span class="label-en">Matching Routes</span><span class="label-bn">মিলছে এমন রুট</span></div>
  <div class="chip-row" id="rmChips"></div>
</section>

<section class="section" id="popSection">
  <div class="section-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6.1-7-11.3A7 7 0 0 0 5 9.7C5 14.9 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.3"/></svg> <span class="label-en">Popular Starting Places</span><span class="label-bn">জনপ্রিয় ছাড়ার জায়গা</span></div>
  <div class="place-grid">
{_popular_html}
  </div>
</section>

<section class="section">
  <div class="section-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M3 12h18M3 18h12"/></svg> <span class="label-en">All Places &middot; A to Z</span><span class="label-bn">সব জায়গা &middot; A–Z</span></div>
  <div class="az-nav" id="azNav"></div>
  <div id="azGroups">{_az_html}</div>
  <div class="empty" id="emptyState">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
    <b><span class="label-en">No matches found</span><span class="label-bn">কিছু পাওয়া যায়নি</span></b><span class="label-en">Try a different place name</span><span class="label-bn">অন্য নাম লিখে দেখুন</span>
  </div>
</section>

<div class="ad-zone" id="ad2"></div>

<section class="section">
  <div class="section-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.5h.01"/></svg> Frequently Asked Questions</div>
  <div class="faq-list">
{_faq_html}
  </div>
</section>

<script type="application/json" id="bttData">{_btt_json_str}</script>
{_btt_js}"""


_index_schema = (
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
            "West Bengal Bus Time Table \u2013 All Routes | BusJatri",
            (
                "Complete West Bengal bus time table: "
                f"{_total_routes} routes from {_total_places} places. "
                "Find SBSTC, WBTC, NBSTC and private bus timings with departure "
                "times, operators and stoppages."
            ),
            f"{BASE}/bus-time-table/",
            _index_body,
            _index_schema,
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



