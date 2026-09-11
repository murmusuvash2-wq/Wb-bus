/* BusJatri — app logic. Hash-based router over a single local JSON dataset. */

let DATA = null, BUSES = {}, ROUTES = {}, STOPS = {}, LANG = 'en';

const ICONS = {
  bus: '<svg class="icon" viewBox="0 0 24 24"><path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"/><path d="M4 16h16"/><path d="M4 16v2a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-2"/><path d="M17 16v2a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-2"/><path d="M6 10h12"/><circle cx="7.5" cy="16" r="0"/></svg>',
  sun: '<svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2.5M12 19.5V22M4.2 4.2l1.8 1.8M18 18l1.8 1.8M2 12h2.5M19.5 12H22M4.2 19.8 6 18M18 6l1.8-1.8"/></svg>',
  moon: '<svg class="icon" viewBox="0 0 24 24"><path d="M20.5 14.5a8.5 8.5 0 1 1-9-11 7 7 0 0 0 9 11Z"/></svg>',
  chevronLeft: '<svg class="icon" viewBox="0 0 24 24"><path d="M14.5 5 8 12l6.5 7"/></svg>',
  clock: '<svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/></svg>',
  map: '<svg class="icon" viewBox="0 0 24 24"><path d="M9 4 3 6.5v13L9 17l6 3 6-2.5v-13L15 7 9 4Z"/><path d="M9 4v13M15 7v13"/></svg>',
  pin: '<svg class="icon" viewBox="0 0 24 24"><path d="M12 21s7-6.1 7-11.3A7 7 0 0 0 5 9.7C5 14.9 12 21 12 21Z"/><circle cx="12" cy="9.5" r="2.3"/></svg>',
  stops: '<svg class="icon" viewBox="0 0 24 24"><circle cx="6" cy="6" r="2"/><circle cx="6" cy="18" r="2"/><path d="M6 8v8"/><path d="M6 12h9a3 3 0 0 0 3-3V7"/></svg>',
  search: '<svg class="icon" viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m20 20-4.3-4.3"/></svg>',
  mountain: '<svg class="icon" viewBox="0 0 24 24"><path d="m3 19 6.5-11L14 15l2.5-4L21 19Z"/></svg>',
  waves: '<svg class="icon" viewBox="0 0 24 24"><path d="M2 8c2 2 4 2 6 0s4-2 6 0 4 2 6 0"/><path d="M2 14c2 2 4 2 6 0s4-2 6 0 4 2 6 0"/><path d="M2 20c2 2 4 2 6 0s4-2 6 0 4 2 6 0"/></svg>',
  landmark: '<svg class="icon" viewBox="0 0 24 24"><path d="M4 10h16L12 4z"/><path d="M5 10v9M9 10v9M15 10v9M19 10v9"/><path d="M3 21h18"/></svg>',
  building: '<svg class="icon" viewBox="0 0 24 24"><rect x="5" y="3" width="14" height="18" rx="1"/><path d="M9 7h.01M9 11h.01M9 15h.01M15 7h.01M15 11h.01M15 15h.01"/></svg>',
  factory: '<svg class="icon" viewBox="0 0 24 24"><path d="M3 21V11l5 3v-3l5 3V9l5 3v9Z"/><path d="M3 21h18"/><path d="M8 5.5c0-1 1-1 1-2s-1-1-1-2"/></svg>',
  train: '<svg class="icon" viewBox="0 0 24 24"><rect x="5" y="4" width="14" height="13" rx="3"/><path d="M5 11h14"/><circle cx="9" cy="17.5" r="1.4"/><circle cx="15" cy="17.5" r="1.4"/><path d="m8 21-2 2M16 21l2 2"/></svg>',
  trees: '<svg class="icon" viewBox="0 0 24 24"><path d="M8 3 4 9h2l-3 5h4v6M8 3l4 6h-2l3 5h-4"/><path d="M17 7l-3.5 6H15l-2.5 4.5H18v5.5"/></svg>',
  cog: '<svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 3v2.2M12 18.8V21M21 12h-2.2M5.2 12H3M18.4 5.6l-1.5 1.5M7.1 16.9l-1.5 1.5M18.4 18.4l-1.5-1.5M7.1 7.1 5.6 5.6"/></svg>',
  dome: '<svg class="icon" viewBox="0 0 24 24"><path d="M5 15a7 7 0 0 1 14 0"/><path d="M3 19h18M12 8V4M10 4h4"/><path d="M6 15v4M18 15v4"/></svg>',
  compass: '<svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="m14.5 9.5-1.8 5.2-5.2 1.8 1.8-5.2z"/></svg>',
  ticket: '<svg class="icon" viewBox="0 0 24 24"><path d="M3 8a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v2a2 2 0 0 0 0 4v2a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-2a2 2 0 0 0 0-4Z"/><path d="M10 6v12" stroke-dasharray="2 3"/></svg>',
  alert: '<svg class="icon" viewBox="0 0 24 24"><path d="M12 3 2 20h20L12 3Z"/><path d="M12 10v4M12 17h.01"/></svg>',
  info: '<svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.5h.01"/></svg>',
  data: '<svg class="icon" viewBox="0 0 24 24"><path d="M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3Z"/><path d="M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/></svg>',
};

const PLACE_ICONS = {
  Mukutmanipur: 'waves', Digha: 'waves', Bankura: 'landmark', Kolkata: 'building',
  Asansol: 'factory', Burdwan: 'train', Jhargram: 'trees', Purulia: 'mountain',
  Durgapur: 'cog', Khatra: 'bus', Bishnupur: 'dome', Medinipur: 'pin',
};
const FEATURED_PLACES = ['Kolkata', 'Digha'];

const POPULAR_PLACES = [
  { name: 'Mukutmanipur' }, { name: 'Digha' }, { name: 'Bankura' }, { name: 'Kolkata' },
  { name: 'Asansol' }, { name: 'Burdwan' }, { name: 'Jhargram' }, { name: 'Purulia' },
  { name: 'Durgapur' }, { name: 'Khatra' }, { name: 'Bishnupur' }, { name: 'Medinipur' },
];

function icon(name) { return ICONS[name] || ''; }

function renderInitialSkeleton() {
  document.getElementById('app').innerHTML = `
  <div class="hero">
    <div class="hero-inner skel-hero">
      <div class="skel skel-line" style="width:40%;height:26px"></div>
      <div class="skel skel-line" style="width:60%"></div>
      <div class="skel" style="height:150px;border-radius:20px;margin-top:20px"></div>
    </div>
  </div>
  <div class="section"><div class="container">
    <div class="skel skel-line" style="width:160px;height:20px;margin:0 0 16px"></div>
    <div class="skel-grid">${Array(8).fill('<div class="skel skel-card"></div>').join('')}</div>
  </div></div>`;
}

async function loadData() {
  renderInitialSkeleton();
  try {
    const res = await fetch('data/busjatri_data.json');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    DATA = await res.json();
    BUSES = {};
    DATA.buses.forEach(b => BUSES[b.id] = b);
    ROUTES = DATA.routes || {};
    STOPS = DATA.stops || {};
    window.addEventListener('hashchange', render);
    render();
  } catch (e) {
    document.getElementById('app').innerHTML = `
    <div class="container"><div class="error-panel">
      ${icon('alert')}
      <p><strong>Could not load the timetable.</strong><br>${esc(e.message)}</p>
      <button class="retry-btn" onclick="loadData()">Try again</button>
    </div></div>`;
  }
}

function setLang(l) {
  LANG = l;
  document.body.className = l === 'bn' ? 'lang-bn' : '';
  document.getElementById('langEN').classList.toggle('active', l === 'en');
  document.getElementById('langBN').classList.toggle('active', l === 'bn');
  render();
}

function toggleTheme() {
  const cur = document.documentElement.getAttribute('data-theme') ||
    (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  const next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('bj-theme', next);
  updateThemeIcon(next);
}

function updateThemeIcon(theme) {
  const btn = document.getElementById('themeBtn');
  if (btn) btn.innerHTML = theme === 'dark' ? icon('sun') : icon('moon');
}

(function () {
  const saved = localStorage.getItem('bj-theme');
  if (saved) document.documentElement.setAttribute('data-theme', saved);
  const effective = saved || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  updateThemeIcon(effective);
})();

function esc(s) {
  return String(s || '').replace(/[<>&"]/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;' }[c]));
}
function slug(s) {
  return String(s || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

function parseTime(t) {
  if (!t) return null;
  const m = t.match(/(\d{1,2}):(\d{2})\s*(AM|PM)?/i);
  if (!m) return null;
  let h = parseInt(m[1], 10), min = parseInt(m[2], 10);
  const ap = (m[3] || '').toUpperCase();
  if (ap === 'PM' && h < 12) h += 12;
  if (ap === 'AM' && h === 12) h = 0;
  return h * 60 + min;
}

function minutesNow() {
  const d = new Date();
  return d.getHours() * 60 + d.getMinutes();
}

function busTypeBadge(t) {
  if (!t) return '';
  const g = t.toLowerCase();
  if (g.includes('gov') || g.includes('sbstc') || g.includes('nbstc') || g.includes('wbtc'))
    return '<span class="badge badge-govt">Govt</span>';
  if (g.includes('ac') && !g.includes('non'))
    return '<span class="badge badge-ac">AC</span>';
  return '<span class="badge badge-private">Private</span>';
}

function timeOrDash(t) {
  return t ? `<span class="stop-time">${esc(t)}</span>` : `<span class="no-time">—</span>`;
}

function doSearch() {
  const from = (document.getElementById('fromInput')?.value || '').trim();
  const to = (document.getElementById('toInput')?.value || '').trim();
  const q = new URLSearchParams();
  if (from) q.set('from', from);
  if (to) q.set('to', to);
  location.hash = '#/search?' + q.toString();
}

function quickSearch(name) {
  const q = new URLSearchParams();
  q.set('from', name);
  location.hash = '#/search?' + q.toString();
}

function render() {
  const hash = location.hash.slice(1) || '/';
  const app = document.getElementById('app');
  if (hash === '/' || hash === '') renderHome(app);
  else if (hash.startsWith('/search')) renderSearch(app);
  else if (hash.startsWith('/route/')) renderRoute(app, decodeURIComponent(hash.slice(7)));
  else if (hash.startsWith('/bus/')) renderBus(app, decodeURIComponent(hash.slice(5)));
  else if (hash.startsWith('/stop/')) renderStop(app, decodeURIComponent(hash.slice(6)));
  else if (hash.startsWith('/place/')) renderPlace(app, decodeURIComponent(hash.slice(7)));
  else if (hash.startsWith('/about')) renderAbout(app);
  else renderHome(app);
  window.scrollTo(0, 0);
  animateStats();
}

function animateStats() {
  document.querySelectorAll('.stat .num[data-target]').forEach(el => {
    const target = parseInt(el.dataset.target, 10) || 0;
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) { el.textContent = target.toLocaleString(); return; }
    const start = performance.now();
    const dur = 700;
    function step(now) {
      const p = Math.min(1, (now - start) / dur);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * eased).toLocaleString();
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  });
}

function renderHome(el) {
  const placeCards = POPULAR_PLACES.map((p, i) => {
    const stop = Object.values(STOPS).find(s => s.name.toLowerCase() === p.name.toLowerCase())
      || Object.values(STOPS).find(s => s.name.toLowerCase().includes(p.name.toLowerCase()));
    const count = stop ? stop.bus_ids.length : 0;
    const iconName = PLACE_ICONS[p.name] || 'pin';
    const featured = FEATURED_PLACES.includes(p.name) ? ' featured' : '';
    return `<div class="place-card${featured}" style="--i:${i}" onclick="location.hash='#/place/${encodeURIComponent(p.name)}'">
      <div class="icon-badge">${icon(iconName)}</div>
      <div class="name">${esc(p.name)}</div>
      <div class="count">${count ? count + ' buses' : 'Explore'}</div>
    </div>`;
  }).join('');

  el.innerHTML = `
  <div class="hero">
    <div class="hero-route-line">${icon('bus')}</div>
    <div class="container hero-inner">
      <span class="eyebrow">${icon('ticket')} West Bengal · Route Data</span>
      <h1>Bus<span class="accent">Jatri</span></h1>
      <p class="tagline en">West Bengal's largest bus timetable</p>
      <p class="tagline bn">পশ্চিমবঙ্গের সবচেয়ে বড় বাস টাইম টেবিল</p>
      <div class="search-box">
        <div class="search-row">
          <div class="search-field">
            <label>${icon('pin')} <span class="label-en">From</span><span class="label-bn">কোথা থেকে</span></label>
            <input id="fromInput" list="stopList" placeholder="e.g. Bankura" onkeydown="if(event.key==='Enter')doSearch()">
          </div>
          <div class="search-field">
            <label>${icon('compass')} <span class="label-en">To</span><span class="label-bn">কোথায়</span></label>
            <input id="toInput" list="stopList" placeholder="e.g. Digha" onkeydown="if(event.key==='Enter')doSearch()">
          </div>
        </div>
        <div class="search-actions">
          <button class="search-btn" onclick="doSearch()">${icon('search')} <span class="label-en">Search buses</span><span class="label-bn">খুঁজুন</span></button>
        </div>
        <datalist id="stopList">${Object.values(STOPS).slice(0, 800).map(s => `<option value="${esc(s.name)}">`).join('')}</datalist>
      </div>
      <div class="stats">
        <div class="stat"><div class="num" data-target="${DATA.meta.total_buses || 0}">0</div><div class="label"><span class="label-en">Buses</span><span class="label-bn">বাস</span></div></div>
        <div class="stat"><div class="num" data-target="${DATA.meta.total_routes || 0}">0</div><div class="label"><span class="label-en">Routes</span><span class="label-bn">রুট</span></div></div>
        <div class="stat"><div class="num" data-target="${DATA.meta.total_stops || 0}">0</div><div class="label"><span class="label-en">Stops</span><span class="label-bn">স্টপ</span></div></div>
      </div>
    </div>
  </div>
  <div class="section">
    <div class="container">
      <div class="section-title">${icon('pin')} <span class="label-en">Popular Places</span><span class="label-bn">জনপ্রিয় স্থান</span></div>
      <div class="place-cards">${placeCards}</div>
    </div>
  </div>`;
}

function renderSearch(el) {
  const params = new URLSearchParams(location.hash.split('?')[1] || '');
  const from = (params.get('from') || '').toLowerCase().trim();
  const to = (params.get('to') || '').toLowerCase().trim();
  let results = Object.values(BUSES);

  if (from && to) {
    results = results.filter(b =>
      (b.origin || '').toLowerCase().includes(from) && (b.destination || '').toLowerCase().includes(to)
      || (b.origin || '').toLowerCase().includes(to) && (b.destination || '').toLowerCase().includes(from)
    );
  } else if (from || to) {
    const q = from || to;
    results = results.filter(b =>
      (b.origin || '').toLowerCase().includes(q) ||
      (b.destination || '').toLowerCase().includes(q) ||
      (b.bus_name || '').toLowerCase().includes(q) ||
      (b.route || '').toLowerCase().includes(q)
    );
  }

  const now = minutesNow();
  results.sort((a, b) => {
    const ta = parseTime(a.departure_time);
    const tb = parseTime(b.departure_time);
    if (ta == null && tb == null) return 0;
    if (ta == null) return 1;
    if (tb == null) return -1;
    const da = Math.min(Math.abs(ta - now), Math.abs(ta + 1440 - now));
    const db = Math.min(Math.abs(tb - now), Math.abs(tb + 1440 - now));
    if (da <= 180 && db > 180) return -1;
    if (db <= 180 && da > 180) return 1;
    return ta - tb;
  });

  const near = results.filter(b => {
    const t = parseTime(b.departure_time);
    if (t == null) return false;
    const d = Math.min(Math.abs(t - now), Math.abs(t + 1440 - now));
    return d <= 180;
  });

  const emptyState = `
    <div class="empty-state">
      ${icon('bus')}
      <p><span class="label-en">No buses found for that route. Try a nearby town instead.</span><span class="label-bn">কোনো বাস পাওয়া যায়নি। কাছাকাছি কোনো শহর চেষ্টা করুন।</span></p>
      <div class="chip-row">
        ${['Bankura', 'Digha', 'Kolkata', 'Durgapur'].map(n => `<span class="sugg-chip" onclick="quickSearch('${n}')">${esc(n)}</span>`).join('')}
      </div>
    </div>`;

  el.innerHTML = `
  <div class="container" style="padding-top:22px;padding-bottom:40px">
    <div class="back-btn" onclick="location.hash='#/'">${icon('chevronLeft')} <span class="label-en">Back</span><span class="label-bn">পিছনে</span></div>
    <h2 class="page-title"><span class="label-en">Search Results</span><span class="label-bn">সার্চ ফলাফল</span> <span style="color:var(--ink-dim);font-family:var(--font-mono);font-size:1rem">(${results.length})</span></h2>
    ${from || to ? `<p style="color:var(--ink-dim);font-size:13.5px;margin-bottom:18px">${esc(from || '…')} → ${esc(to || '…')}</p>` : ''}
    ${near.length ? `<p class="near-label">${icon('clock')} <span class="label-en">${near.length} buses around current time</span><span class="label-bn">${near.length} বাস বর্তমান সময়ের কাছাকাছি</span></p>` : ''}
    ${results.length ? results.map((b, i) => {
      const t = parseTime(b.departure_time);
      const isNear = t != null && Math.min(Math.abs(t - now), Math.abs(t + 1440 - now)) <= 180;
      return `<div class="result-item ${isNear ? 'near' : ''}" style="--i:${i}" onclick="location.hash='#/bus/${encodeURIComponent(b.id)}'">
        <div class="ri-main">
          ${isNear ? `<div class="near-label">${icon('clock')} Near now</div>` : ''}
          <div class="name">${esc(b.bus_name)} ${b.reg_no ? `<span class="reg">${esc(b.reg_no)}</span>` : ''} ${busTypeBadge(b.bus_type)}</div>
          <div class="route">${esc(b.origin)} → ${esc(b.destination)}</div>
          <div class="meta">
            <span>${icon('stops')} ${b.total_stoppages || (b.stoppages || []).length} stops</span>
            ${b.operator ? `<span>${esc(b.operator)}</span>` : ''}
          </div>
        </div>
        ${b.departure_time ? `<span class="time-pill">${icon('clock')} ${esc(b.departure_time)}</span>` : ''}
      </div>`;
    }).join('') : emptyState}
  </div>`;
}

function renderPlace(el, placeName) {
  const q = placeName.toLowerCase();
  const related = Object.values(BUSES).filter(b =>
    (b.origin || '').toLowerCase().includes(q) ||
    (b.destination || '').toLowerCase().includes(q) ||
    (b.stoppages || []).some(s => (s.name || '').toLowerCase().includes(q))
  );
  related.sort((a, b) => {
    const ta = parseTime(a.departure_time), tb = parseTime(b.departure_time);
    if (ta == null && tb == null) return 0;
    if (ta == null) return 1;
    if (tb == null) return -1;
    return ta - tb;
  });

  el.innerHTML = `
  <div class="container" style="padding-top:22px;padding-bottom:40px">
    <div class="back-btn" onclick="location.hash='#/'">${icon('chevronLeft')} <span class="label-en">Back</span><span class="label-bn">পিছনে</span></div>
    <h2 class="page-title">${esc(placeName)}</h2>
    <p style="color:var(--ink-dim);font-size:14px;margin-bottom:18px">${related.length} <span class="label-en">buses related to this place</span><span class="label-bn">বাস এই স্থানের সাথে যুক্ত</span></p>
    ${related.map((b, i) => `
      <div class="result-item" style="--i:${i}" onclick="location.hash='#/bus/${encodeURIComponent(b.id)}'">
        <div class="ri-main">
          <div class="name">${esc(b.bus_name)} ${busTypeBadge(b.bus_type)}</div>
          <div class="route">${esc(b.origin)} → ${esc(b.destination)}</div>
          <div class="meta"><span>${icon('stops')} ${b.total_stoppages || 0} stops</span></div>
        </div>
        ${b.departure_time ? `<span class="time-pill">${icon('clock')} ${esc(b.departure_time)}</span>` : ''}
      </div>`).join('') || `<div class="empty-state">${icon('bus')}<p>No buses found for this place.</p></div>`}
  </div>`;
}

function renderBus(el, id) {
  const b = BUSES[id];
  if (!b) {
    el.innerHTML = `<div class="container" style="padding:40px"><div class="empty-state">${icon('alert')}<p>Bus not found.</p></div><div class="back-btn" onclick="location.hash='#/'">${icon('chevronLeft')} Back</div></div>`;
    return;
  }
  const stops = b.stoppages || [];
  const INITIAL = 8;
  const showAll = location.hash.includes('full=1');
  const visible = showAll ? stops : stops.slice(0, INITIAL);

  const stopNames = stops.map(s => s.name).filter(Boolean);
  let mapUrl = '';
  if (stopNames.length >= 2) {
    const origin = encodeURIComponent(stopNames[0] + ', West Bengal');
    const dest = encodeURIComponent(stopNames[stopNames.length - 1] + ', West Bengal');
    const waypoints = stopNames.slice(1, -1).slice(0, 8).map(n => encodeURIComponent(n + ', West Bengal')).join('|');
    mapUrl = `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${dest}` + (waypoints ? `&waypoints=${waypoints}` : '') + '&travelmode=driving';
  } else if (b.origin && b.destination) {
    mapUrl = `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(b.origin + ', West Bengal')}&destination=${encodeURIComponent(b.destination + ', West Bengal')}&travelmode=driving`;
  }

  el.innerHTML = `
  <div class="container" style="padding-top:22px;padding-bottom:40px">
    <div class="back-btn" onclick="history.length>1?history.back():location.hash='#/'">${icon('chevronLeft')} <span class="label-en">Back</span><span class="label-bn">পিছনে</span></div>
    <div class="bus-detail">
      <h2>${esc(b.bus_name)} ${b.reg_no ? `<span style="font-size:14px;color:var(--ink-dim);font-weight:500;font-family:var(--font-mono)">${esc(b.reg_no)}</span>` : ''}</h2>
      <div class="route-line">${esc(b.origin)} → ${esc(b.destination)} ${busTypeBadge(b.bus_type)}</div>
      <div class="info-grid">
        ${b.departure_time ? `<div class="info-item"><div class="lbl">Departure</div><div class="val">${esc(b.departure_time)}</div></div>` : ''}
        ${b.arrival_time ? `<div class="info-item"><div class="lbl">Arrival</div><div class="val">${esc(b.arrival_time)}</div></div>` : ''}
        ${b.operator ? `<div class="info-item"><div class="lbl">Operator</div><div class="val">${esc(b.operator)}</div></div>` : ''}
        ${b.depot_name ? `<div class="info-item"><div class="lbl">Depot</div><div class="val">${esc(b.depot_name)}</div></div>` : ''}
        ${b.contact_number && b.contact_number !== 'Not Available !' ? `<div class="info-item"><div class="lbl">Contact</div><div class="val"><a href="tel:${esc(b.contact_number)}">${esc(b.contact_number)}</a></div></div>` : ''}
        <div class="info-item"><div class="lbl">Stops</div><div class="val">${stops.length || b.total_stoppages || 0}</div></div>
        <div class="info-item"><div class="lbl">Source</div><div class="val" style="font-size:12px">${esc(b.source)}</div></div>
      </div>
      ${mapUrl ? `<a class="map-btn" href="${mapUrl}" target="_blank" rel="noopener">${icon('map')} <span class="label-en">View route on Google Maps</span><span class="label-bn">গুগল ম্যাপে রুট দেখুন</span></a>` : ''}
      ${stops.length ? `
        <h3 class="timetable-title">${icon('ticket')} <span class="label-en">Route Timetable</span><span class="label-bn">রুট টাইমটেবিল</span></h3>
        <div class="timetable-head"><span>#</span><span><span class="label-en">Stoppage</span><span class="label-bn">স্টপ</span></span><span style="text-align:right">Up</span><span style="text-align:right">Down</span></div>
        <div class="stops-list">
          ${visible.map(s => `<div class="stop-row">
            <span class="stop-dot"></span>
            <span class="stop-name"><a href="#/stop/${slug(s.name)}">${esc(s.name)}</a></span>
            ${timeOrDash(s.up_time)}
            ${timeOrDash(s.down_time)}
          </div>`).join('')}
        </div>
        ${!showAll && stops.length > INITIAL ? `<button class="show-more-btn" onclick="location.hash='#/bus/${encodeURIComponent(id)}?full=1'">Show all ${stops.length} stops ↓</button>` : ''}
        ${showAll && stops.length > INITIAL ? `<button class="show-more-btn" onclick="location.hash='#/bus/${encodeURIComponent(id)}'">Show less ↑</button>` : ''}
      ` : '<p style="color:var(--ink-dim);margin-top:12px">Stoppage details not available for this bus.</p>'}
    </div>
  </div>`;
}

function renderRoute(el, key) {
  const r = ROUTES[key];
  if (!r) {
    el.innerHTML = `<div class="container" style="padding:40px"><div class="empty-state">${icon('alert')}<p>Route not found.</p></div></div>`;
    return;
  }
  const buses = (r.bus_ids || []).map(id => BUSES[id]).filter(Boolean);
  el.innerHTML = `
  <div class="container" style="padding-top:22px;padding-bottom:40px">
    <div class="back-btn" onclick="location.hash='#/'">${icon('chevronLeft')} Back</div>
    <h2 class="page-title">${esc(r.from)} → ${esc(r.to)}</h2>
    <p style="color:var(--ink-dim);margin-bottom:18px">${buses.length} buses</p>
    ${buses.map((b, i) => `
      <div class="result-item" style="--i:${i}" onclick="location.hash='#/bus/${encodeURIComponent(b.id)}'">
        <div class="ri-main">
          <div class="name">${esc(b.bus_name)} ${busTypeBadge(b.bus_type)}</div>
          <div class="meta"><span>${icon('stops')} ${b.total_stoppages || 0} stops</span></div>
        </div>
        ${b.departure_time ? `<span class="time-pill">${icon('clock')} ${esc(b.departure_time)}</span>` : ''}
      </div>`).join('')}
  </div>`;
}

function renderStop(el, slugKey) {
  const stop = Object.values(STOPS).find(s => slug(s.name) === slugKey);
  if (!stop) {
    el.innerHTML = `<div class="container" style="padding:40px"><div class="empty-state">${icon('alert')}<p>Stop not found.</p></div></div>`;
    return;
  }
  const buses = (stop.bus_ids || []).map(id => BUSES[id]).filter(Boolean);
  el.innerHTML = `
  <div class="container" style="padding-top:22px;padding-bottom:40px">
    <div class="back-btn" onclick="location.hash='#/'">${icon('chevronLeft')} Back</div>
    <h2 class="page-title">${esc(stop.name)}</h2>
    <p style="color:var(--ink-dim);margin-bottom:14px">${buses.length} buses pass through</p>
    <a class="map-btn" href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(stop.name + ', West Bengal, India')}" target="_blank" rel="noopener">${icon('map')} View on Google Maps</a>
    ${buses.map((b, i) => `
      <div class="result-item" style="--i:${i}" onclick="location.hash='#/bus/${encodeURIComponent(b.id)}'">
        <div class="ri-main">
          <div class="name">${esc(b.bus_name)}</div>
          <div class="route">${esc(b.origin)} → ${esc(b.destination)}</div>
        </div>
        ${b.departure_time ? `<span class="time-pill">${icon('clock')} ${esc(b.departure_time)}</span>` : ''}
      </div>`).join('')}
  </div>`;
}

function renderAbout(el) {
  const sources = (DATA.meta && DATA.meta.sources) || ['bussathi.in', 'wbbus.in', 'wbbustime.in', 'WBTC', 'NBSTC'];
  el.innerHTML = `
  <div class="container" style="padding-top:26px;padding-bottom:40px">
    <div class="back-btn" onclick="location.hash='#/'">${icon('chevronLeft')} Back</div>
    <div class="about-card">
      <h3>${icon('bus')} About BusJatri</h3>
      <p>
        BusJatri is an independent, community-oriented bus timetable for West Bengal.
        We aggregate publicly available route and timing data so travellers can find buses faster.
        This is <strong>not</strong> an official government or corporation site.
      </p>
    </div>
    <div class="about-card">
      <h3>${icon('data')} Data Sources &amp; Credits</h3>
      <p>
        Timetable data is compiled from public sources. All credit belongs to the original platforms and transport corporations:
      </p>
      <div class="source-list">
        ${sources.map(s => `<span class="source-chip">${esc(s)}</span>`).join('')}
        <span class="source-chip">SBSTC</span>
        <span class="source-chip">Public sources</span>
      </div>
      <p style="margin-top:14px;font-size:13px">
        Last updated: ${esc(DATA.meta?.last_updated || '—')} · Version ${esc(DATA.meta?.version || '2.0')}
      </p>
    </div>
    <div class="about-card">
      <h3>${icon('info')} Disclaimer</h3>
      <p>
        Timings can change. Always verify with the operator or depot before travelling.
        BusJatri does not guarantee accuracy of schedules.
      </p>
    </div>
  </div>`;
}

loadData();
