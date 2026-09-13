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
CSS = "../css/style.css"


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
    return """
<header class="header">
  <div class="container header-inner">

    <a href="../index.html"
       class="logo"
       style="text-decoration:none;color:inherit">

      <svg class="icon"
           viewBox="0 0 24 24"
           style="width:1.35rem;height:1.35rem;color:var(--amber)"
           aria-hidden="true">

        <path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"/>
        <path d="M4 16h16"/>
      </svg>

      Bus<span>Jatri</span>
    </a>

    <nav style="
      display:flex;
      gap:14px;
      align-items:center;
      font-size:14px;
    ">
      <a href="../index.html">Home</a>
      <a href="./">Routes</a>
    </nav>

  </div>
</header>
"""


def footer_html():
    return """
<footer class="footer">
  <div class="container">

    <p>
      <strong>BusJatri</strong> — West Bengal bus timetable
      and route information.
    </p>

    <p style="font-size:13px;color:var(--ink-dim)">
      Timings and routes can change. Please verify with the
      operator or depot before travelling.
      BusJatri is not affiliated with any transport corporation.
    </p>

  </div>
</footer>
"""


def shell(title, description, canonical, body, schema=""):
    return f"""<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>{esc(title)}</title>

<meta name="description"
      content="{esc(description)}">

<link rel="canonical"
      href="{esc(canonical)}">

<meta property="og:title"
      content="{esc(title)}">

<meta property="og:description"
      content="{esc(description)}">

<meta property="og:type"
      content="website">

<meta property="og:url"
      content="{esc(canonical)}">

<meta name="theme-color"
      content="#b8791f">

<link rel="icon"
      href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b8791f' stroke-width='2'%3E%3Cpath d='M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10'/%3E%3Cpath d='M4 16h16'/%3E%3C/svg%3E">

<link rel="stylesheet"
      href="{CSS}">

{schema}

</head>

<body>

{header_html()}

<main class="container"
      style="
        padding-top:24px;
        padding-bottom:56px;
        max-width:980px;
      ">

{body}

</main>

{footer_html()}

</body>
</html>
"""


# ------------------------------------------------------------
# SCHEMA
# ------------------------------------------------------------

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

    sequence_counter = Counter(
        tuple(sequence)
        for sequence in sequences
    )

    sequence, frequency = sequence_counter.most_common(1)[0]
    sequence = list(sequence[:18])

    items = []

    for index, stop in enumerate(sequence):
        last = index == len(sequence) - 1

        connector = ""

        if not last:
            connector = """
<span style="
  width:2px;
  height:32px;
  background:var(--border);
  display:block;
"></span>
"""

        items.append(f"""
<div style="
  display:flex;
  gap:14px;
  align-items:flex-start;
">

  <div style="
    display:flex;
    flex-direction:column;
    align-items:center;
    min-width:18px;
  ">

    <span style="
      width:12px;
      height:12px;
      border-radius:50%;
      background:var(--amber);
      border:3px solid var(--panel);
      box-shadow:0 0 0 1px var(--border);
      display:block;
    "></span>

    {connector}

  </div>

  <div style="
    font-weight:600;
    padding-bottom:8px;
  ">
    {esc(stop)}
  </div>

</div>
""")

    note = ""

    if frequency < len(buses):
        note = """
<p style="
  margin-top:10px;
  color:var(--ink-dim);
  font-size:13px;
">
  The stop sequence shown represents the most commonly
  listed sequence in the available timetable data.
</p>
"""

    return f"""
<section style="margin-top:34px">

  <h2 style="font-size:1.35rem;margin-bottom:8px">
    Route &amp; Stoppages
  </h2>

  <p style="
    color:var(--ink-dim);
    margin-top:0;
    margin-bottom:18px;
  ">
    Commonly listed stops between the two locations.
  </p>

  <div style="
    background:var(--panel);
    border:1px solid var(--border);
    border-radius:16px;
    padding:20px;
  ">
    {''.join(items)}
    {note}
  </div>

</section>
"""


# ------------------------------------------------------------
# BUS CARD
# ------------------------------------------------------------

def bus_card(bus):
    name = clean_text(
        bus.get("bus_name")
    ) or "Bus service"

    departure = format_time(
        parse_time(bus.get("departure_time"))
    )

    arrival = format_time(
        parse_time(bus.get("arrival_time"))
    )

    bus_type = bus_type_label(
        bus.get("bus_type")
    )

    operator = operator_name(bus)
    stops = total_stops(bus)
    duration = calculate_duration(bus)

    duration_text = (
        fmt_duration(duration)
        if duration
        else "Unavailable"
    )

    source_html = ""

    detail_url = clean_text(
        bus.get("detail_url")
    )

    if detail_url.startswith(("http://", "https://")):
        pass  # source links hidden on site per project decision

    return f"""
<article style="
  background:var(--panel);
  border:1px solid var(--border);
  border-radius:16px;
  padding:18px;
  margin-bottom:12px;
">

  <div style="
    display:flex;
    justify-content:space-between;
    gap:14px;
    flex-wrap:wrap;
    align-items:flex-start;
  ">

    <div>

      <div style="
        font-weight:750;
        font-size:1.05rem;
        margin-bottom:6px;
      ">
        {esc(name)}
      </div>

      <div style="
        display:flex;
        gap:8px;
        flex-wrap:wrap;
        align-items:center;
        font-size:13px;
        color:var(--ink-dim);
      ">

        <span>{esc(bus_type)}</span>
        {f'<span>•</span><span>{esc(operator)}</span>' if operator else ''}

      </div>

    </div>

  </div>

  <div style="
    display:grid;
    grid-template-columns:
      repeat(auto-fit,minmax(110px,1fr));
    gap:10px;
    margin-top:16px;
  ">

    <div>
      <div style="
        font-size:11px;
        color:var(--ink-dim);
        text-transform:uppercase;
      ">
        Departure
      </div>

      <strong style="font-size:1.05rem">
        {esc(departure)}
      </strong>
    </div>

    <div>
      <div style="
        font-size:11px;
        color:var(--ink-dim);
        text-transform:uppercase;
      ">
        Arrival
      </div>

      <strong style="font-size:1.05rem">
        {esc(arrival)}
      </strong>
    </div>

    <div>
      <div style="
        font-size:11px;
        color:var(--ink-dim);
        text-transform:uppercase;
      ">
        Duration
      </div>

      <strong style="font-size:1.05rem">
        {esc(duration_text)}
      </strong>
    </div>

    <div>
      <div style="
        font-size:11px;
        color:var(--ink-dim);
        text-transform:uppercase;
      ">
        Stops
      </div>

      <strong style="font-size:1.05rem">
        {stops or "—"}
      </strong>
    </div>

  </div>

</article>
"""


# ------------------------------------------------------------
# ROUTE PAGE
# ------------------------------------------------------------

def generate_route_page(origin, destination, buses):
    filename = (
        f"{slug(origin)}-to-{slug(destination)}.html"
    )

    route_bn = bn_route(
        origin,
        destination,
    )

    stats = route_stats(buses)

    first = format_time(stats["first"])
    last = format_time(stats["last"])
    duration = stats["duration"]
    operators = stats["operators"]

    count = len(buses)

    title = (
        f"{origin} to {destination} Bus Time Table | বাসের সময়সূচী – {SITE_NAME}"
    )

    description = (
        f"Find {origin} to {destination} bus timings, "
        f"operators, stoppages and route information on "
        f"{SITE_NAME}. See available departures and return "
        f"route options."
    )[:300]
    if route_bn:
        description = (
            f"{description} {route_bn} বাসের সময়সূচী ও রুট তথ্য।"
        )[:300]

    canonical = (
        f"{BASE}/bus-time-table/{filename}"
    )

    major_stops = stoppage_summary(buses)

    operator_text = (
        ", ".join(operators[:5])
        if operators
        else "multiple operators"
    )

    faqs = [
        (
            f"What is the first bus from {origin} to {destination}?",
            (
                f"The earliest listed departure from {origin} "
                f"to {destination} is {first}. Timings can "
                f"change, so verify before travelling."
                if stats["first"] is not None
                else
                "The available timetable does not provide a "
                "reliable first departure time for this route."
            ),
        ),
        (
            f"What is the last bus from {origin} to {destination}?",
            (
                f"The latest listed departure from {origin} "
                f"to {destination} is {last}. Please verify "
                f"the current schedule before travelling."
                if stats["last"] is not None
                else
                "See the timetable above for available departures."
            ),
        ),
        (
            f"How many buses are listed from {origin} to {destination}?",
            (
                f"BusJatri currently lists {count} bus services "
                f"from {origin} to {destination}. Listed "
                f"operators include {operator_text}."
            ),
        ),
    ]

    if duration:
        faqs.append(
            (
                f"How long does the bus take from "
                f"{origin} to {destination}?",
                (
                    f"The typical listed journey duration is "
                    f"approximately {fmt_duration(duration)}. "
                    f"Actual travel time can vary because of "
                    f"traffic, stops and operating conditions."
                ),
            )
        )

    if major_stops:
        faqs.append(
            (
                f"Which major stops are on the {origin} to "
                f"{destination} route?",
                (
                    "Commonly listed stops include "
                    + ", ".join(major_stops[:6])
                    + ". Stop sequences can differ between "
                      "individual services."
                ),
            )
        )

    bengali_line = ""

    if route_bn:
        bengali_line = f"""
<div style="
  margin-top:8px;
  color:var(--ink-dim);
  font-size:15px;
">
  {esc(route_bn)} বাসের সময়সূচী ও রুট তথ্য
</div>
"""

    duration_stat = ""

    if duration:
        duration_stat = f"""
<div style="
  flex:1 1 150px;
  background:var(--panel);
  border:1px solid var(--border);
  border-radius:14px;
  padding:14px 16px;
">

  <div style="
    font-size:12px;
    color:var(--ink-dim);
  ">
    Approx. duration
  </div>

  <strong style="font-size:1.15rem">
    {esc(fmt_duration(duration))}
  </strong>

</div>
"""

    hero = f"""
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
    {esc(origin)} → {esc(destination)}
  </div>

  <div style="
    display:inline-flex;
    align-items:center;
    gap:7px;
    padding:6px 10px;
    border-radius:999px;
    background:var(--bg);
    border:1px solid var(--border);
    color:var(--ink-dim);
    font-size:12px;
    margin-bottom:12px;
  ">
    {count} listed bus services
  </div>

  <h1 style="
    font-size:clamp(1.8rem,5vw,2.7rem);
    line-height:1.15;
    margin:0;
  ">
    {esc(origin)} → {esc(destination)}
    <br>
    <span style="
      font-size:.72em;
      color:var(--ink-dim);
    ">
      Bus Time Table · বাসের সময়সূচী
    </span>
  </h1>

  {bengali_line}

  <p style="
    max-width:700px;
    margin:16px 0 20px;
    color:var(--ink-dim);
    line-height:1.7;
  ">
    Check available bus departures, arrival times,
    operators and commonly listed stoppages for travel
    from {esc(origin)} to {esc(destination)}.
  </p>

  <a href="../index.html"
     style="
       display:inline-block;
       padding:10px 15px;
       border:1px solid var(--border);
       border-radius:10px;
       text-decoration:none;
       font-weight:600;
     ">
    Search another route
  </a>

</section>
"""

    stats_html = f"""
<section style="
  display:flex;
  gap:10px;
  flex-wrap:wrap;
  margin-bottom:32px;
">

  <div style="
    flex:1 1 150px;
    background:var(--panel);
    border:1px solid var(--border);
    border-radius:14px;
    padding:14px 16px;
  ">
    <div style="font-size:12px;color:var(--ink-dim)">
      Services
    </div>
    <strong style="font-size:1.15rem">{count}</strong>
  </div>

  <div style="
    flex:1 1 150px;
    background:var(--panel);
    border:1px solid var(--border);
    border-radius:14px;
    padding:14px 16px;
  ">
    <div style="font-size:12px;color:var(--ink-dim)">
      First listed
    </div>
    <strong style="font-size:1.15rem">
      {esc(first)}
    </strong>
  </div>

  <div style="
    flex:1 1 150px;
    background:var(--panel);
    border:1px solid var(--border);
    border-radius:14px;
    padding:14px 16px;
  ">
    <div style="font-size:12px;color:var(--ink-dim)">
      Last listed
    </div>
    <strong style="font-size:1.15rem">
      {esc(last)}
    </strong>
  </div>

  {duration_stat}

</section>
"""

    sorted_buses = sorted(
        buses,
        key=lambda bus: (
            parse_time(bus.get("departure_time"))
            if parse_time(bus.get("departure_time")) is not None
            else 9999
        ),
    )

    timetable = f"""
<section>

  <h2 style="font-size:1.4rem;margin-bottom:6px">
    {esc(origin)} to {esc(destination)} Bus Timings
  </h2>

  <p style="
    margin:5px 0 14px;
    color:var(--ink-dim);
    font-size:14px;
  ">
    Available departures sorted by departure time.
  </p>

  {''.join(bus_card(bus) for bus in sorted_buses)}

  <p style="
    color:var(--ink-dim);
    font-size:12.5px;
    margin-top:10px;
  ">
    Timetable information is based on the available
    BusJatri dataset. Schedules may change.
  </p>

</section>
"""

    major_section = ""

    if major_stops:
        chips = "".join(
            f"""
<span style="
  display:inline-block;
  padding:7px 10px;
  margin:4px 4px 4px 0;
  border:1px solid var(--border);
  border-radius:999px;
  font-size:13px;
">
  {esc(stop)}
</span>
"""
            for stop in major_stops
        )

        major_section = f"""
<section style="margin-top:34px">

  <h2 style="font-size:1.35rem">
    Major Stoppages
  </h2>

  <p style="color:var(--ink-dim);margin-top:0">
    Frequently listed stops across the services on
    this route.
  </p>

  <div>{chips}</div>

</section>
"""

    operators_section = ""

    if operators:
        operators_section = f"""
<section style="margin-top:34px">

  <h2 style="font-size:1.35rem">
    Bus Operators
  </h2>

  <p style="color:var(--ink-dim);margin-top:0">
    Operators appearing in the available timetable data.
  </p>

  <ul>
    {''.join(
        f'<li style="margin-bottom:6px">{esc(operator)}</li>'
        for operator in operators[:10]
    )}
  </ul>

</section>
"""

    route_section = route_stops_html(buses)

    journey_section = f"""
<section style="margin-top:34px">

  <h2 style="font-size:1.35rem">
    Journey Information
  </h2>

  <div style="
    background:var(--panel);
    border:1px solid var(--border);
    border-radius:16px;
    padding:18px;
    line-height:1.75;
  ">

    <p style="margin-top:0">
      <strong>Route:</strong>
      {esc(origin)} → {esc(destination)}
    </p>

    <p>
      <strong>Listed services:</strong>
      {count}
    </p>

    <p>
      <strong>First listed departure:</strong>
      {esc(first)}
    </p>

    <p>
      <strong>Last listed departure:</strong>
      {esc(last)}
    </p>

    <p style="
      margin-bottom:0;
      color:var(--ink-dim);
    ">
      Actual journey time and service availability can
      vary because of traffic, route changes, holidays
      and operator schedules.
    </p>

  </div>

</section>
"""

    faq_html = "".join(
        f"""
<details style="
  border-bottom:1px solid var(--border);
  padding:14px 0;
">

  <summary style="
    cursor:pointer;
    font-weight:650;
  ">
    {esc(question)}
  </summary>

  <p style="
    margin:9px 0 0;
    color:var(--ink-dim);
    line-height:1.65;
  ">
    {esc(answer)}
  </p>

</details>
"""
        for question, answer in faqs
    )

    faq_section = f"""
<section style="margin-top:36px">

  <h2 style="font-size:1.35rem">
    Frequently Asked Questions
  </h2>

  {faq_html}

</section>
"""

    reverse_filename = (
        f"{slug(destination)}-to-{slug(origin)}.html"
    )

    reverse_section = ""

    if (destination, origin) in route_meta:
        reverse_section = f"""
<section style="margin-top:36px">

  <h2 style="font-size:1.35rem">
    Return Route
  </h2>

  <a href="{esc(reverse_filename)}"
     style="
       display:block;
       background:var(--panel);
       border:1px solid var(--border);
       border-radius:14px;
       padding:16px;
       text-decoration:none;
     ">

    <strong>
      {esc(destination)} → {esc(origin)}
    </strong>

    <div style="
      color:var(--ink-dim);
      font-size:13px;
      margin-top:4px;
    ">
      View return-direction bus timetable →
    </div>

  </a>

</section>
"""

    related = [
        (o, t)
        for (o, t) in route_meta
        if o == origin and t != destination
    ]

    related = sorted(
        related,
        key=lambda pair: -len(route_meta[pair]),
    )[:8]

    related_section = ""

    if related:
        links = "".join(
            f"""
<a href="{slug(o)}-to-{slug(t)}.html"
   style="
     display:block;
     padding:12px 14px;
     border-bottom:1px solid var(--border);
     text-decoration:none;
   ">

  {esc(o)} → {esc(t)}

  <span style="
    float:right;
    color:var(--ink-dim);
    font-size:13px;
  ">
    {len(route_meta[(o, t)])} buses
  </span>

</a>
"""
            for o, t in related
        )

        related_section = f"""
<section style="margin-top:36px">

  <h2 style="font-size:1.35rem">
    More Bus Routes from {esc(origin)}
  </h2>

  <div style="
    background:var(--panel);
    border:1px solid var(--border);
    border-radius:16px;
    overflow:hidden;
  ">
    {links}
  </div>

</section>
"""

    body = (
        hero
        + stats_html
        + timetable
        + route_section
        + major_section
        + operators_section
        + journey_section
        + faq_section
        + reverse_section
        + related_section
    )

    schema = (
        faq_schema(faqs)
        + "\n"
        + breadcrumb_schema([
            ("Home", "/"),
            ("Bus Timetable", "/bus-time-table/"),
            (
                f"{origin} to {destination}",
                f"/bus-time-table/{filename}",
            ),
        ])
    )

    return filename, shell(
        title,
        description,
        canonical,
        body,
        schema,
    )


# ------------------------------------------------------------
# PLACE PAGE
# ------------------------------------------------------------

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
        op = operator_name(b)
        key = (op or '').lower()
        if key in seen:
            continue
        seen.add(key)
        st = next((s for s in (b.get('stoppages') or []) if clean_text(s.get('name')) == via_stop), {})
        rows.append({'operator': op or '—', 'dep': parse_time(b.get('departure_time')), 'via': parse_time(st.get('up_time')), 'arr': parse_time(b.get('arrival_time')), 'stops': total_stops(b), 'bus_type': bus_type_label(b.get('bus_type') or '')})
    rows.sort(key=lambda r: r['dep'] if r['dep'] is not None else 9999)
    n = len(rows)
    if n < 2:
        return None, None
    dep_times = [r['dep'] for r in rows if r['dep'] is not None]
    via_times = [r['via'] for r in rows if r['via'] is not None]
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
        via_f = format_time(r['via'])
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
    if via_times:
        vf = format_time(min(via_times))
        vl = format_time(max(via_times))
        faqs.append(('When do buses reach ' + via_stop + ' from ' + origin + '?', 'The first bus reaches ' + via_stop + ' at about ' + vf + '; the last at about ' + vl + '.'))
    faq_html = ''
    for q, a in faqs:
        faq_html += '<details style="border:1px solid var(--border);border-radius:10px;padding:12px 16px;margin-bottom:10px"><summary style="cursor:pointer;font-weight:600">' + esc(q) + '</summary><p style="margin:8px 0 0;color:var(--ink-dim);font-size:14px">' + esc(a) + '</p></details>'
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
