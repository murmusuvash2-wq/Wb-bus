#!/usr/bin/env python3
"""Patch app.js: add Live Departures board, Stoppage search, Popular Routes.
Run from repo root: python3 scripts/patch_home_page.py"""

import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

with open('js/app.js', 'r') as f:
    c = f.read()

original = c

# 1. doSearch: via -> stop
c = c.replace(
    "const via = (document.getElementById('viaInput')?.value || '').trim();\n  if (!from && !to) {",
    "const stop = (document.getElementById('stopInput')?.value || '').trim();\n  if (!from && !to && !stop) {"
)
c = c.replace("if (via) q.set('via', via);", "if (stop) q.set('stop', stop);")

# 2. renderSearch: via -> stop
c = c.replace(
    "const via = (params.get('via') || '').toLowerCase().trim();",
    "const stop = (params.get('stop') || '').toLowerCase().trim();"
)
c = c.replace(
    """      if (via) {
        const vi = posIn(b, via);
        if (!(vi > fi && vi < ti)) return false;
      }""",
    """      if (stop) {
        const si = posIn(b, stop);
        if (si < 0) return false;
      }"""
)
c = c.replace("if (!results.length && !via) {", "if (!results.length && !stop) {")

# 3. Add stoppage-only search mode
c = c.replace(
    "  } else if (from || to) {",
    """  } else if (stop) {
    results = results.filter(b =>
      (b.stoppages || []).some(s => (s.name || '').toLowerCase().includes(stop)) ||
      (b.origin || '').toLowerCase().includes(stop) ||
      (b.destination || '').toLowerCase().includes(stop)
    );
  } else if (from || to) {"""
)

# 4. Search results header
c = c.replace(
    """${via ? ` <span class="badge badge-ac">via ${esc(via)}</span>` : ''}</p>` : ''}""",
    """${stop ? ` <span class="badge badge-ac">stop ${esc(stop)}</span>` : ''}</p>` : ''}
    ${stop && !from && !to ? `<p style="color:var(--ink-dim);font-size:13.5px;margin-bottom:18px">${LANG==='bn'?'এই স্টপেজে থামে: ':'Buses halting at '}${esc(stop)}</p>` : ''}"""
)

# 5. Replace Via field with Stoppage field
c = c.replace(
    """          <div class="search-field">
            <label>${icon('ticket')} Via <span class="via-hint">(optional)</span></label>
            <input id="viaInput" list="stopList" placeholder="e.g. Bishnupur" onkeydown="if(event.key==='Enter')doSearch()">
          </div>""",
    """          <div class="search-field">
            <label>${icon('stops')} <span class="label-en">Stoppage</span><span class="label-bn">স্টপেজ</span> <span class="via-hint">(optional)</span></label>
            <input id="stopInput" list="stopList" placeholder="e.g. Kolaghat" onkeydown="if(event.key==='Enter')doSearch()">
          </div>"""
)

# 6. Update empty-search message
c = c.replace(
    "Please fill <strong>From</strong> and <strong>To</strong> to search buses.",
    "Fill <strong>From</strong> + <strong>To</strong> for routes, or just a <strong>Stoppage</strong> to see every bus that halts there."
)
c = c.replace(
    "বাস খুঁজতে <strong>কোথা থেকে</strong> ও <strong>কোথায়</strong> লিখুন।",
    "<strong>কোথা থেকে</strong> ও <strong>কোথায়</strong> লিখুন, অথবা শুধু একটি <strong>স্টপেজ</strong> লিখলে সেখানে থামা সব বাস দেখা যাবে।"
)

# 7. Replace Next Buses with Live Departures + Popular Routes
c = c.replace(
    """  const nextDeps = stopDepartures(slug('Kolkata'), Object.keys(BUSES), 6).map(n => n.b).filter(Boolean);
  const nextCards = nextDeps.map((b, i) => `
      <div class="result-item" style="--i:${i}" onclick="location.hash='#/bus/${encodeURIComponent(b.id)}'">
        <div class="ri-main">
          <div class="name">${esc(b.bus_name)} ${busTypeBadge(b.bus_type)}</div>
          <div class="route">${esc(pn(b.origin))} ⇥ ${esc(pn(b.destination))}</div>
          <div class="meta"><span>${icon('stops')} ${b.total_stoppages || (b.stoppages || []).length || 0} stops</span></div>
        </div>
        ${b.departure_time ? `<span class="time-pill">${icon('clock')} ${esc(b.departure_time)}</span>` : ''}
      </div>`).join('');""",
    """  const routeChips = computePopularRoutes().map(p =>
    `<span class="route-chip" onclick="location.hash='#/search?from=${encodeURIComponent(p.from)}&to=${encodeURIComponent(p.to)}'">${esc(pn(p.from))} <span class="rarr">→</span> ${esc(pn(p.to))}<span class="rcnt">${p.n}</span></span>`).join('');"""
)
c = c.replace(
    """  ${nextCards ? `
  <div class="section">
    <div class="container">
      <div class="section-title">${icon('clock')} <span class="label-en">Next Buses from Kolkata</span><span class="label-bn">কলকাতা থেকে পরের বাস</span></div>
      ${nextCards}
    </div>
  </div>` : ''}`;""",
    """  <div class="section">
    <div class="container">
      <div class="section-title">${icon('clock')} <span class="label-en">Live Departures</span><span class="label-bn">লাইভ ছাড়ার তালিকা</span></div>
      <div id="lvBoard"></div>
    </div>
  </div>
  <div class="section">
    <div class="container">
      <div class="section-title">${icon('map')} <span class="label-en">Popular Routes</span><span class="label-bn">জনপ্রিয় রুট</span></div>
      <div class="route-chips">${routeChips}</div>
    </div>
  </div>`;
  renderBoard();
  detectLocation();"""
)

# 8. Add board/geolocation/popular-routes functions after animateStats
new_fns = """

/* ===================== Live Departures Board (geo-aware) ===================== */
const LV_ORIGINS = [
  { name: 'Kolkata', lat: 22.56263, lon: 88.36304 },
  { name: 'Digha', lat: 21.62776, lon: 87.51965 },
  { name: 'Burdwan', lat: 23.2324, lon: 87.8678 },
  { name: 'Siliguri', lat: 26.71004, lon: 88.42851 },
  { name: 'Bankura', lat: 23.23241, lon: 87.0716 },
];
const LV_FALLBACK = ['Kolkata', 'Digha', 'Burdwan'];
let lvOrigin = null;
let lvNear = [];

function lvHaversine(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}

function detectLocation() {
  if (!navigator.geolocation) { renderBoard(); return; }
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const { latitude: lat, longitude: lon } = pos.coords;
      lvNear = LV_ORIGINS.map(o => ({ ...o, dist: lvHaversine(lat, lon, o.lat, o.lon) }))
        .sort((a, b) => a.dist - b.dist).slice(0, 4);
      if (lvNear.length && !lvOrigin) lvOrigin = lvNear[0].name;
      renderBoard();
    },
    () => { lvNear = []; renderBoard(); },
    { timeout: 5000, maximumAge: 300000 }
  );
}

function lvGetOrigins() {
  if (lvNear.length) return lvNear;
  return LV_FALLBACK.map(n => ({ name: n, dist: null }));
}

function renderBoard() {
  const wrap = document.getElementById('lvBoard');
  if (!wrap) return;
  if (!lvOrigin) lvOrigin = lvGetOrigins()[0].name;
  const origins = lvGetOrigins();
  const now = minutesNow();
  const clockT = new Date().toLocaleTimeString('en-IN', { hour12: false, timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', second: '2-digit' });

  const originStop = STOPS[lvOrigin];
  const deps = originStop
    ? stopDepartures(slug(lvOrigin), originStop.bus_ids || Object.keys(BUSES), 10)
    : [];

  let rows = '';
  if (deps.length) {
    const nextIdx = deps.findIndex(d => d.diff > 0);
    const allPast = nextIdx < 0;
    const idx = allPast ? 0 : nextIdx;
    rows = deps.map((n, i) => {
      let cls = '', right = '';
      if (i === idx) {
        cls = 'next';
        right = `<span class="ltag">${allPast ? (LANG==='bn'?'কাল +':'tmrw +') : (LANG==='bn'?'এখন +':'in ')}${countdownText(n.diff)}</span>`;
      } else if (i > idx && !allPast) {
        right = `<span class="lgone">+${countdownText(n.diff)}</span>`;
      } else {
        cls = 'past';
        right = `<span class="lgone">✓ ${LANG==='bn'?'চলে গেছে':'departed'}</span>`;
      }
      return `<div class="lv-row ${cls}" style="animation-delay:${i*0.07}s" onclick="location.hash='#/bus/${encodeURIComponent(n.b.id)}'">` +
        `<span class="lt">${fmtTime(n.t).replace(' ','')}</span>` +
        `<span class="lnm">${esc(n.b.bus_name)}</span>` +
        `<span class="ldst">→ ${esc(pn(n.b.destination))}</span>` +
        `${right}</div>`;
    }).join('');
  } else {
    rows = `<div class="lv-row"><span class="lnm">${LANG==='bn'?'সময়ের তথ্য নেই':'No timed departures listed'}</span></div>`;
  }

  const geoHtml = lvNear.length
    ? `<div class="lv-geo"><span class="label-en">Detected near</span><span class="label-bn">কাছাকাছি শনাক্ত</span><b>${esc(lvNear[0].name)}</b>${lvNear[0].dist != null ? `<span>${Math.round(lvNear[0].dist)} km</span>` : ''}</div>`
    : `<div class="lv-geo"><span class="label-en">Popular stops</span><span class="label-bn">জনপ্রিয় স্টপ</span></div>`;

  wrap.innerHTML = `
    <div class="lv-clock-wrap">
      <div>
        <div class="lv-clock-label"><span class="ldot"></span> <span class="label-en">Live Departures</span><span class="label-bn">লাইভ ছাড়ার তালিকা</span></div>
        <div class="lv-clock-big">${clockT}<small>IST</small></div>
      </div>
      ${geoHtml}
    </div>
    <div class="lv-board">
      <div class="lv-tabs">${origins.map(o => `<button class="lv-tab${o.name === lvOrigin ? ' on' : ''}" onclick="lvOrigin='${o.name}';renderBoard()">${esc(o.name)}${o.dist != null ? `<span class="dist">${Math.round(o.dist)}km</span>` : ''}</button>`).join('')}</div>
      <div id="lvRows">${rows}</div>
    </div>`;
}

/* ===================== Popular Routes ===================== */
function computePopularRoutes() {
  const pair = {};
  for (const id in BUSES) {
    const b = BUSES[id];
    const o = (b.origin || '').trim(), d = (b.destination || '').trim();
    if (o && d && o !== d) {
      const key = o + '||' + d;
      pair[key] = (pair[key] || 0) + 1;
    }
  }
  return Object.entries(pair).sort((a, b) => b[1] - a[1]).slice(0, 10)
    .map(([k, n]) => { const [o, d] = k.split('||'); return { from: o, to: d, n }; });
}
"""

c = c.replace(
    """    requestAnimationFrame(step);
  });
}

function renderHome(el) {""",
    """    requestAnimationFrame(step);
  });
}""" + new_fns + """

function renderHome(el) {"""
)

with open('js/app.js', 'w') as f:
    f.write(c)

# Verify
changes = [
    ('via removed', 'viaInput' not in c),
    ('stop added', 'stopInput' in c),
    ('board fn', 'function renderBoard()' in c),
    ('geo fn', 'function detectLocation()' in c),
    ('popular routes fn', 'function computePopularRoutes()' in c),
    ('Live Departures', 'Live Departures' in c),
    ('Popular Routes', 'Popular Routes' in c),
]
all_ok = all(ok for _, ok in changes)
for name, ok in changes:
    print(f"  {'OK' if ok else 'FAIL'}: {name}")

if not all_ok:
    raise SystemExit(1)

print(f"Patched app.js: {len(original)} -> {len(c)} chars")
