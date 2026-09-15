/* BusJatri — Bus Detail Page redesign (overrides app.js renderBus)
   Loaded AFTER app.js so function redefinition takes effect at call time.
   Depends on globals from app.js: BUSES, STOPS, DATA, esc, pn, busTypeBadge, icon, loadWeather */
var COMMUNITY_TIME_KEY = 'busjatri-community-times-v1';
function communityTimes() {
  try { return JSON.parse(localStorage.getItem(COMMUNITY_TIME_KEY) || '{}'); } catch (e) { return {}; }
}
function communityTimeKey(busId, stopIndex, direction) { return busId + '|' + stopIndex + '|' + direction; }
function normalizeCommunityTime(value) {
  var v = String(value || '').trim().replace('.', ':').toUpperCase();
  var m = v.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/);
  if (!m || Number(m[1]) < 1 || Number(m[1]) > 12 || Number(m[2]) > 59) return '';
  return Number(m[1]) + ':' + m[2] + ' ' + m[3];
}
function addCommunityTime(busId, stopIndex, direction) {
  var value = normalizeCommunityTime(window.prompt('Enter time, for example 11:30 AM'));
  if (!value) { window.alert('Please enter time like 11:30 AM.'); return; }
  var times = communityTimes();
  times[communityTimeKey(busId, stopIndex, direction)] = value;
  try { localStorage.setItem(COMMUNITY_TIME_KEY, JSON.stringify(times)); } catch (e) {}
  render();
}
function timeCell(stop, stopIndex, direction, busId) {
  var official = stop[direction + '_time'] || '';
  if (official) return '<span>' + esc(official) + '</span>';
  var userTime = communityTimes()[communityTimeKey(busId, stopIndex, direction)];
  if (userTime) return '<span class="community-time">' + esc(userTime) + '<small>User updated</small></span>';
  return '<button class="add-time-btn" onclick="addCommunityTime(\'' + esc(busId) + '\',' + stopIndex + ',\'' + direction + '\')">+ Add time</button>';
}
async function renderBus(el, id) {
  id = id.split('?')[0];
  const b = typeof loadFullBus === 'function' ? await loadFullBus(id) : BUSES[id];
  if (!b) {
    el.innerHTML = '<div class="container" style="padding:40px"><div class="empty-state">' + icon('alert') + '<p>Bus not found.</p></div><div class="back-btn" onclick="location.hash=\'#/\'">' + icon('chevronLeft') + ' Back</div></div>';
    return;
  }
  const stops = b.stoppage_pages || b.stoppages || [];
  const INITIAL = 8;
  const showAll = location.hash.includes('full=1');
  const visible = showAll ? stops : stops.slice(0, INITIAL);
  const returnDeparture = stops.slice().reverse().find(s => s.down_time)?.down_time || '';
  const returnArrival = stops.find(s => s.down_time)?.down_time || '';

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
    var stnBadge = stn ? '<span class="rail">Railway: ' + esc(stn.name) + (stn.code ? ' (' + esc(stn.code) + ')' : '') + ' \u00b7 ~' + stn.km + ' km</span>' : '';
    var upT = timeCell(s, i, 'up', id);
    var dnT = timeCell(s, i, 'down', id);
    return '<div class="stop-row ' + (isEnd ? 'end' : '') + '"><span class="stop-dot"></span><span class="stop-name">' + esc(pn(s.name)) + stnBadge + '</span><span class="stop-times"><span class="time-out">' + upT + '</span><span class="time-in">' + dnT + '</span></span></div>';
  }).join('');

  var showMoreBtn = '';
  if (!showAll && stops.length > INITIAL) {
    showMoreBtn = '<button class="show-all" onclick="location.hash=\'#/bus/' + encodeURIComponent(id) + '?full=1\'">Show all ' + stops.length + ' stops \u21d3</button>';
  } else if (showAll && stops.length > INITIAL) {
    showMoreBtn = '<button class="show-all" onclick="location.hash=\'#/bus/' + encodeURIComponent(id) + '\'">Show less \u21d1</button>';
  }

  el.innerHTML =
    '<div class="container" style="padding-top:22px;padding-bottom:40px">' +
      '<div class="back-btn" onclick="history.length>1?history.back():location.hash=\'#/\'">' + icon('chevronLeft') + ' <span class="label-en">Back</span></div>' +
      '<div class="bus-head">' +
        '<h2>' + esc(b.bus_name) + (b.reg_no ? ' <span class="reg">' + esc(b.reg_no) + '</span>' : '') + ' ' + busTypeBadge(b.bus_type) + '</h2>' +
        '<div class="route-line">' + icon('bus') + ' ' + esc(pn(b.origin)) + ' \u21c4 ' + esc(pn(b.destination)) + '</div>' +
        '<div class="info-grid">' +
          (b.departure_time ? '<div class="info-item"><div class="lbl">Departure</div><div class="val">' + esc(b.departure_time) + '</div></div>' : '') +
          (b.arrival_time ? '<div class="info-item"><div class="lbl">Arrival</div><div class="val">' + esc(b.arrival_time) + '</div></div>' : '') +
          '<div class="info-item"><div class="lbl">Stops</div><div class="val">' + (stops.length || b.total_stoppage_pages || 0) + '</div></div>' +
          (b.fare ? '<div class="info-item"><div class="lbl">Fare</div><div class="val">' + esc(b.fare) + '</div></div>' : '') +
          (b.operator ? '<div class="info-item"><div class="lbl">Operator</div><div class="val">' + esc(b.operator) + '</div></div>' : '') +
          (b.depot_name ? '<div class="info-item"><div class="lbl">Depot</div><div class="val">' + esc(b.depot_name) + '</div></div>' : '') +
          (b.contact_number && b.contact_number !== 'Not Available !' ? '<div class="info-item"><div class="lbl">Contact</div><div class="val"><a href="tel:' + esc(b.contact_number) + '">' + esc(b.contact_number) + '</a></div></div>' : '') +
        '</div>' +
        (returnDeparture ? '<div class="return-journey"><strong>Return journey</strong><span>' + esc(pn(b.destination)) + ' → ' + esc(pn(b.origin)) + '</span><span>Departs ' + esc(returnDeparture) + (returnArrival ? ' · arrives around ' + esc(returnArrival) : '') + '</span></div>' : '') +
      '</div>' +
      '<div class="wa-row">' +
        (mapUrl ? '<a class="map-btn" href="' + mapUrl + '" target="_blank" rel="noopener">' + icon('map') + ' <span class="label-en">Route on Google Maps</span></a>' : '') +
        '<a class="wa-btn" href="javascript:void(0)" onclick="shareWhatsApp(this.dataset.bus,this.dataset.org,this.dataset.dest,this.dataset.dep,this.dataset.stops)" data-bus="' + esc(b.bus_name) + '" data-org="' + esc(pn(b.origin)) + '" data-dest="' + esc(pn(b.destination)) + '" data-dep="' + esc(b.departure_time||'') + '" data-stops="' + (stops.length||0) + '">' + icon('waves') + ' <span class="label-en">Share on WhatsApp</span></a>' +
        '<a class="share-x-btn" href="javascript:void(0)" onclick="shareTwitter(this.dataset)" data-bus="' + esc(b.bus_name) + '" data-org="' + esc(pn(b.origin)) + '" data-dest="' + esc(pn(b.destination)) + '" data-dep="' + esc(b.departure_time||'') + '">' + icon('info') + ' <span class="label-en">Share on X</span></a>' +
      '</div>' +
      (b.destination && b.destination !== '\u2014' ? '<div class="weather-card" id="weatherCard" data-dest="' + esc(b.destination) + '"><div class="lbl">Weather in ' + esc(b.destination) + ' (now)</div><div class="val" id="weatherVal">Loading\u2026</div></div>' : '') +
      (stops.length ? '<h3 class="section-title" style="margin-top:22px">' + icon('ticket') + ' <span class="label-en">Route Timetable</span></h3><div class="schedule-legend"><span><i class="legend-dot outbound"></i> From ' + esc(pn(b.origin)) + '</span><span><i class="legend-dot inbound"></i> Return to ' + esc(pn(b.origin)) + '</span><span class="community-note">Times marked “User updated” are community-submitted.</span></div><div class="schedule-table"><div class="schedule-head"><span>Stop</span><span>Outbound</span><span>Return</span></div><div class="stop-list">' + stopHTML + showMoreBtn + '</div></div>' : '<p style="color:var(--ink-dim);margin-top:12px">Stoppage details not available.</p>') +
      '<p style="font-size:12px;color:var(--ink-dim);margin:10px 0 0">Data updated: ' + esc((DATA.meta||{}).last_updated || '') + '</p>' +
    '</div>';
  loadWeather();
}
