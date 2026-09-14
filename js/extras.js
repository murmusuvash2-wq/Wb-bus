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
    ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>'
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
