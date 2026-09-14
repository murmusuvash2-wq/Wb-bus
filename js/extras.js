/* BusJatri Extras — WhatsApp share, geolocation, report time, admin, static-page helpers */

/* ---------- Theme (static pages) ---------- */
function toggleThemeStatic() {
  var cur = document.documentElement.getAttribute('data-theme') ||
    (window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  var next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  try { localStorage.setItem('bj-theme', next); } catch (e) {}
  updateThemeIconStatic(next);
}
function updateThemeIconStatic(theme) {
  var btn = document.getElementById('themeBtn');
  if (!btn) return;
  btn.innerHTML = theme === 'dark'
    ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 13h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>'
    : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
}
(function () {
  var saved = null;
  try { saved = localStorage.getItem('bj-theme'); } catch (e) {}
  if (saved) document.documentElement.setAttribute('data-theme', saved);
  var eff = saved || (window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  updateThemeIconStatic(eff);
})();

/* ---------- WhatsApp Share — bus time + site link ---------- */
function shareWhatsApp(busName, origin, destination, departure, stops) {
  var msg = "BusJatri — West Bengal Bus Timetable\n\n";
  msg += "Bus: " + (busName || "—") + "\n";
  msg += "Route: " + (origin || "—") + " → " + (destination || "—") + "\n";
  if (departure) msg += "Departure: " + departure + "\n";
  if (stops) msg += "Stops: " + stops + "\n";
  msg += "\nView full timetable:\nhttps://wb-bus.vercel.app";
  msg += "\n\nMore buses on BusJatri (বাস যাত্রী)";
  window.open("https://wa.me/?text=" + encodeURIComponent(msg), "_blank");
}

/* ---------- Geolocation Auto-Detect — prefill "From" field ---------- */
function detectLocation() {
  if (!navigator.geolocation) return;
  navigator.geolocation.getCurrentPosition(function (pos) {
    fetch("https://nominatim.openstreetmap.org/reverse?lat=" + pos.coords.latitude + "&lon=" + pos.coords.longitude + "&format=json&accept-language=en")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var a = data.address || {};
        var city = a.city || a.town || a.village || a.county || a.state_district;
        if (city) {
          var inputs = document.querySelectorAll(".search-field input");
          if (inputs[0] && !inputs[0].value) {
            inputs[0].value = city;
            var hint = document.querySelector(".geo-hint");
            if (hint) {
              var c = hint.querySelector(".geo-city");
              if (c) c.textContent = city;
              hint.classList.add("show");
            }
          }
        }
      })
      .catch(function () { /* silent — detection is best-effort only */ });
  }, function () { /* denied or failed — ignore */ }, { timeout: 8000 });
}

/* ---------- Contact Form — opens user's email client ---------- */
function sendContact() {
  var name = (document.getElementById("cName") || {}).value || "";
  var email = (document.getElementById("cEmail") || {}).value || "";
  var subject = (document.getElementById("cSubject") || {}).value || "Feedback";
  var message = (document.getElementById("cMessage") || {}).value || "";
  var body = "Name: " + name + "\nEmail: " + email + "\n\n" + message;
  var url = "mailto:busjatri@zohomail.in?subject=" + encodeURIComponent("[BusJatri] " + subject) + "&body=" + encodeURIComponent(body);
  var ok = document.getElementById("contactSuccess");
  if (ok) ok.style.display = "flex";
  window.location.href = url;
}

/* ---------- Report Time — on bus detail pages ---------- */
function toggleReport(btn) {
  var form = document.getElementById("reportForm");
  if (!form) return;
  var showing = form.classList.toggle("show");
  if (btn) btn.style.display = showing ? "none" : "inline-flex";
}
function submitReport() {
  var form = document.getElementById("reportForm");
  var done = document.getElementById("reportDone");
  var t = (document.getElementById("reportTime") || {}).value || "";
  if (!t) { alert("Please enter the correct time."); return; }
  if (form) form.classList.remove("show");
  if (done) done.classList.add("show");
  /* Time corrections go to the team via email */
  var msg = "BusJatri time correction:\n" + document.title + "\nCorrect time: " + t;
  window.open("https://wa.me/?text=" + encodeURIComponent(msg), "_blank");
}

/* ---------- Admin Dashboard (demo actions) ---------- */
function adminUpdate(btn, msg) {
  if (!btn) return;
  var old = btn.textContent;
  btn.textContent = "✓ Saved";
  btn.disabled = true;
  setTimeout(function () { btn.textContent = old; btn.disabled = false; }, 1600);
  if (msg) {
    var bar = document.getElementById("adminMsg");
    if (bar) { bar.textContent = msg; bar.style.display = "block"; setTimeout(function () { bar.style.display = "none"; }, 2600); }
  }
}
function approveReport(btn) {
  if (!btn) return;
  var row = btn.closest(".admin-report-row");
  btn.textContent = "Approved ✓";
  btn.disabled = true;
  if (row) { row.style.opacity = ".55"; }
}

/* ---------- AdSense zone activation (when ads script present) ---------- */
(function () {
  if (window.adsbygoogle) {
    document.querySelectorAll(".ad-zone").forEach(function (z) { z.classList.add("active"); });
  }
})();

/* ---------- Auto-detect location on home page ---------- */
document.addEventListener("DOMContentLoaded", function () {
  if (document.querySelector(".search-field")) detectLocation();
});

/* ==== Bus Detail Page Redesign (overrides app.js renderBus) ==== */
function renderBus(el, id) {
  id = id.split('?')[0];
  const b = BUSES[id];
  if (!b) {
    el.innerHTML = '<div class="container" style="padding:40px"><div class="empty-state">' + icon('alert') + '<p>Bus not found.</p></div><div class="back-btn" onclick="location.hash=\'#/\'">' + icon('chevronLeft') + ' Back</div></div>';
    return;
  }
  const stops = b.stoppage_pages || b.stoppages || [];
  const INITIAL = 8;
  const showAll = location.hash.includes('full=1');
  const visible = showAll ? stops : stops.slice(0, INITIAL);

  const stopNames = stops.map(s => s.name).filter(Boolean);
  let mapUrl = '';
  if (stopNames.length >= 2) {
    const o = encodeURIComponent(stopNames[0] + ', West Bengal');
    const d2 = encodeURIComponent(stopNames[stopNames.length - 1] + ', West Bengal');
    const wp = stopNames.slice(1, -1).slice(0, 8).map(n => encodeURIComponent(n + ', West Bengal')).join('|');
    mapUrl = 'https://www.google.com/maps/dir/?api=1&origin=' + o + '&destination=' + d2 + (wp ? '&waypoints=' + wp : '') + '&travelmode=driving';
  } else if (b.origin && b.destination) {
    mapUrl = 'https://www.google.com/maps/dir/?api=1&origin=' + encodeURIComponent(b.origin + ', West Bengal') + '&destination=' + encodeURIComponent(b.destination + ', West Bengal') + '&travelmode=driving';
  }

  const stopHTML = visible.map(function(s, i) {
    var isEnd = i === 0 || i === visible.length - 1;
    var stn = (STOPS[s.name] || {}).nearest_station;
    var stnBadge = stn ? '<span class="rail">Railway: ' + esc(stn.name) + (stn.code ? ' (' + esc(stn.code) + ')' : '') + ' · ~' + stn.km + ' km</span>' : '';
    var upT = s.up_time ? '<span>' + esc(s.up_time) + '</span>' : '<span class="no-t">—</span>';
    var dnT = s.down_time ? '<span>' + esc(s.down_time) + '</span>' : '<span class="no-t">—</span>';
    return '<div class="stop-row ' + (isEnd ? 'end' : '') + '"><span class="stop-dot"></span><span class="stop-name">' + esc(pn(s.name)) + stnBadge + '</span><span class="stop-times">' + upT + dnT + '</span></div>';
  }).join('');

  var showMoreBtn = '';
  if (!showAll && stops.length > INITIAL) {
    showMoreBtn = '<button class="show-all" onclick="location.hash=\'#/bus/' + encodeURIComponent(id) + '?full=1\'">Show all ' + stops.length + ' stops ⇓</button>';
  } else if (showAll && stops.length > INITIAL) {
    showMoreBtn = '<button class="show-all" onclick="location.hash=\'#/bus/' + encodeURIComponent(id) + '\'">Show less ⇑</button>';
  }

  el.innerHTML =
    '<div class="container" style="padding-top:22px;padding-bottom:40px">' +
      '<div class="back-btn" onclick="history.length>1?history.back():location.hash=\'#/\'">' + icon('chevronLeft') + ' <span class="label-en">Back</span></div>' +
      '<div class="bus-head">' +
        '<h2>' + esc(b.bus_name) + (b.reg_no ? ' <span class="reg">' + esc(b.reg_no) + '</span>' : '') + ' ' + busTypeBadge(b.bus_type) + '</h2>' +
        '<div class="route-line">' + icon('bus') + ' ' + esc(pn(b.origin)) + ' ⇄ ' + esc(pn(b.destination)) + '</div>' +
        '<div class="info-grid">' +
          (b.departure_time ? '<div class="info-item"><div class="lbl">Departure</div><div class="val">' + esc(b.departure_time) + '</div></div>' : '') +
          (b.arrival_time ? '<div class="info-item"><div class="lbl">Arrival</div><div class="val">' + esc(b.arrival_time) + '</div></div>' : '') +
          '<div class="info-item"><div class="lbl">Stops</div><div class="val">' + (stops.length || b.total_stoppage_pages || 0) + '</div></div>' +
          (b.fare ? '<div class="info-item"><div class="lbl">Fare</div><div class="val">' + esc(b.fare) + '</div></div>' : '') +
          (b.operator ? '<div class="info-item"><div class="lbl">Operator</div><div class="val">' + esc(b.operator) + '</div></div>' : '') +
          (b.depot_name ? '<div class="info-item"><div class="lbl">Depot</div><div class="val">' + esc(b.depot_name) + '</div></div>' : '') +
          (b.contact_number && b.contact_number !== 'Not Available !' ? '<div class="info-item"><div class="lbl">Contact</div><div class="val"><a href="tel:' + esc(b.contact_number) + '">' + esc(b.contact_number) + '</a></div></div>' : '') +
        '</div>' +
      '</div>' +
      '<div class="wa-row">' +
        (mapUrl ? '<a class="map-btn" href="' + mapUrl + '" target="_blank" rel="noopener">' + icon('map') + ' <span class="label-en">Route on Google Maps</span></a>' : '') +
        '<a class="wa-btn" href="javascript:void(0)" onclick="shareWhatsApp(this.dataset)" data-bus="' + esc(b.bus_name) + '" data-org="' + esc(pn(b.origin)) + '" data-dest="' + esc(pn(b.destination)) + '" data-dep="' + esc(b.departure_time||'') + '" data-stops="' + (stops.length||0) + '">' + icon('waves') + ' <span class="label-en">Share on WhatsApp</span></a>' +
      '</div>' +
      (b.destination && b.destination !== '—' ? '<div class="weather-card" id="weatherCard" data-dest="' + esc(b.destination) + '"><div class="lbl">Weather in ' + esc(b.destination) + ' (now)</div><div class="val" id="weatherVal">Loading…</div></div>' : '') +
      (stops.length ? '<h3 class="section-title" style="margin-top:22px">' + icon('ticket') + ' <span class="label-en">Route Timetable</span></h3><div class="stop-list">' + stopHTML + showMoreBtn + '</div>' : '<p style="color:var(--ink-dim);margin-top:12px">Stoppage details not available.</p>') +
      '<p style="font-size:12px;color:var(--ink-dim);margin:10px 0 0">Data updated: ' + esc(DATA.meta?.last_updated || '') + '</p>' +
    '</div>';
  loadWeather();
}
