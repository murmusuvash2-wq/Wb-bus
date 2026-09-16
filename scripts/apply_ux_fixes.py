#!/usr/bin/env python3
"""Apply UX fixes to gen_seo_pages.py (v2 — fragment patterns, no backslash issues).
1. Time N/A pill for buses with missing departure time
2. Include single-bus routes (route pages + index)
3. Bengali toggle on bus-time-table index (bj-lang key, syncs with home)
4. Grammar: "1 route"/"1 bus" instead of "1 routes"/"1 buses"
5. Quick-chip scroll fix
Each replacement must match exactly once — abort otherwise (writes only if ALL ok).
"""
import sys

PATH = "scripts/gen_seo_pages.py"
src = open(PATH, encoding="utf-8").read()

# Idempotency: already-applied check (safe to re-run in CI)
if 'no-time">Time N/A' in src and 'if len(buses) >= 1' in src:
    print("UX fixes already applied — skipping")
    sys.exit(0)

P = []

# ---- P1: include single-bus routes ----
P.append((
'''groups = {
    key: buses
    for key, buses in groups.items()
    if len(buses) >= 2
}''',
'''groups = {
    key: buses
    for key, buses in groups.items()
    if len(buses) >= 1
}''',
"include single-bus routes"))

# ---- P2: bus_card Time N/A ----
P.append((
'''    return f"""<div class="bus-row">
  <div class="dep">{esc(dep)}<small>{esc(arr)} arr</small></div>''',
'''    if dep == "—":
        dep_html = '<span class="no-time">Time N/A</span>'
    else:
        dep_html = f"{esc(dep)}<small>{esc(arr)} arr</small>"
    return f"""<div class="bus-row">
  <div class="dep">{dep_html}</div>''',
"bus_card Time N/A"))

# ---- P3: route hero grammar ----
P.append((
'''<span class="schip">🚌 {count} buses</span>''',
'''<span class="schip">🚌 {count} bus{'es' if count != 1 else ''}</span>''',
"route hero 1 bus grammar"))

# ---- P4: index pr-n grammar (fragment) ----
P.append((
"{len(rs)} routes</span>",
"{len(rs)} route{'s' if len(rs) != 1 else ''}</span>",
"index pr-n grammar"))

# ---- P5: place page route-links grammar ----
P.append((
'''    {number} buses
  </span>''',
'''    {number} bus{'es' if number != 1 else ''}
  </span>''',
"place page buses grammar"))

# ---- P6: index h1 bilingual ----
P.append((
'''  <h1>West Bengal <span class="accent">Bus Time Table</span></h1>''',
'''  <h1><span class="label-en">West Bengal <span class="accent">Bus Time Table</span></span><span class="label-bn">পশ্চিমবঙ্গ <span class="accent">বাস টাইম টেবিল</span></span></h1>''',
"index h1 bilingual"))

# ---- P7: tagline bilingual ----
P.append((
'''  <p class="tagline">Complete bus timings for every route — SBSTC, WBTC, NBSTC and private operators across all districts.</p>''',
'''  <p class="tagline"><span class="label-en">Complete bus timings for every route — SBSTC, WBTC, NBSTC and private operators across all districts.</span><span class="label-bn">প্রতিটি রুটের বাসের সম্পূর্ণ সময়সূচী — SBSTC, WBTC, NBSTC ও প্রাইভেট অপারেটর।</span></p>''',
"tagline bilingual"))

# ---- P8: stat chips bilingual ----
P.append((
'''<strong data-count="{_total_places}">0</strong> places</span>''',
'''<strong data-count="{_total_places}">0</strong> <span class="label-en">places</span><span class="label-bn">স্থান</span></span>''',
"stat chip places"))
P.append((
'''<strong data-count="{_total_routes}">0</strong> routes</span>''',
'''<strong data-count="{_total_routes}">0</strong> <span class="label-en">routes</span><span class="label-bn">রুট</span></span>''',
"stat chip routes"))
P.append((
'''<strong data-count="{_total_buses}">0</strong> bus services</span>''',
'''<strong data-count="{_total_buses}">0</strong> <span class="label-en">bus services</span><span class="label-bn">বাস সার্ভিস</span></span>''',
"stat chip buses"))

# ---- P9: search label bilingual ----
P.append((
'''<span class="live-dot"></span> Search place or route</label>''',
'''<span class="live-dot"></span> <span class="label-en">Search place or route</span><span class="label-bn">স্থান বা রুট খুঁজুন</span></label>''',
"search label bilingual"))

# ---- P10: Quick label bilingual ----
P.append((
'''  <span class="qchips-l">Quick:</span>''',
'''  <span class="qchips-l"><span class="label-en">Quick:</span><span class="label-bn">দ্রুত:</span></span>''',
"quick label bilingual"))

# ---- P11: section titles bilingual ----
P.append((
'''</svg> Matching Routes</div>''',
'''</svg> <span class="label-en">Matching Routes</span><span class="label-bn">মিলছে এমন রুট</span></div>''',
"matching routes title"))
P.append((
'''</svg> Popular Starting Places</div>''',
'''</svg> <span class="label-en">Popular Starting Places</span><span class="label-bn">জনপ্রিয় ছাড়ার জায়গা</span></div>''',
"popular title"))
P.append((
'''</svg> All Places &middot; A to Z</div>''',
'''</svg> <span class="label-en">All Places &middot; A to Z</span><span class="label-bn">সব জায়গা &middot; A–Z</span></div>''',
"az title"))

# ---- P12: empty state bilingual ----
P.append((
'''    <b>No matches found</b>Try a different place name''',
'''    <b><span class="label-en">No matches found</span><span class="label-bn">কিছু পাওয়া যায়নি</span></b><span class="label-en">Try a different place name</span><span class="label-bn">অন্য নাম লিখে দেখুন</span>''',
"empty state bilingual"))

# ---- P13: qsearch scroll fix ----
P.append((
'''function qsearch(q){
  document.getElementById("q").value=q;doSearch();
  document.getElementById("popSection").scrollIntoView({behavior:"smooth",block:"start"});
}''',
'''function qsearch(q){
  document.getElementById("q").value=q;doSearch();
  var t=document.getElementById("routeMatchesSec");
  if(t&&t.style.display!=="none")t.scrollIntoView({behavior:"smooth",block:"start"});
}''',
"qsearch scroll fix"))

# ---- P14: lang init — site key + auto-detect ----
P.append((
'''    var l=localStorage.getItem("seo-lang");
    if(l==="bn"){document.body.classList.add("lang-bn");if(document.getElementById("langBtn"))document.getElementById("langBtn").textContent="English"}''',
'''    var l=null;
    try{l=localStorage.getItem("bj-lang")||localStorage.getItem("seo-lang")}catch(e){}
    if(!l&&((navigator.language||"").toLowerCase().indexOf("bn")===0))l="bn";
    if(l==="bn"){document.body.classList.add("lang-bn");if(document.getElementById("langBtn"))document.getElementById("langBtn").textContent="English"}''',
"lang init bj-lang + auto-detect"))

# ---- P15/P16: JS chips grammar (fragments) ----
P.append((
"+r[1]+' buses",
"+r[1]+((r[1]===1)?' bus':' buses')+'",
"place chips 1 bus grammar"))
P.append((
"+rt[1]+' buses",
"+rt[1]+((rt[1]===1)?' bus':' buses')+'",
"search chips 1 bus grammar"))

# ---- P17: toggleLang + lang button injection ----
P.append((
'''  renderAZ();
  initAnim();
})();
</script>"""''',
'''  renderAZ();
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
</script>"""''',
"toggleLang + lang button"))

# ---- apply: ALL must match exactly once, else abort without writing ----
ok = True
for i, (old, new, desc) in enumerate(P, 1):
    n = src.count(old)
    if n != 1:
        print(f"FAIL P{i} ({desc}): found {n} occurrences (need exactly 1)")
        ok = False
    else:
        src = src.replace(old, new)
        print(f"OK   P{i}: {desc}")

if not ok:
    print("ABORTED — file NOT written")
    sys.exit(1)

open(PATH, "w", encoding="utf-8").write(src)
print("")
print(f"All {len(P)} patches applied → {PATH} ({len(src)} bytes)")
