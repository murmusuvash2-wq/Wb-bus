#!/usr/bin/env python3
"""Patch js/app.js: 'via' support in the SPA search.

- Home search box gets a third optional 'Via' field
- doSearch sends via in the URL params
- renderSearch filters buses whose stop order is from -> via -> to
Run from repo root."""

P = 'js/app.js'
src = open(P, encoding='utf-8').read()

def rep(old, new, cnt=1):
    global src
    assert src.count(old) == cnt, f'pattern x{src.count(old)} (expected {cnt}): {old[:80]!r}'
    src = src.replace(old, new)

# ---- 1. via input field on the home search box -----------------------------
rep("""          <div class=\"search-field\">
            <label>${icon('compass')} <span class=\"label-en\">To</span><span class=\"label-bn\">কোথায়</span></label>
            <input id=\"toInput\" list=\"stopList\" placeholder=\"e.g. Digha\" onkeydown=\"if(event.key==='Enter')doSearch()\">
          </div>
        </div>""",
    """          <div class=\"search-field\">
            <label>${icon('compass')} <span class=\"label-en\">To</span><span class=\"label-bn\">কোথায়</span></label>
            <input id=\"toInput\" list=\"stopList\" placeholder=\"e.g. Digha\" onkeydown=\"if(event.key==='Enter')doSearch()\">
          </div>
          <div class=\"search-field\">
            <label>${icon('ticket')} <span class=\"label-en\">Via (optional)</span><span class=\"label-bn\">মার্গে (ঐচ্ছিক)</span></label>
            <input id=\"viaInput\" list=\"stopList\" placeholder=\"e.g. Bishnupur\" onkeydown=\"if(event.key==='Enter')doSearch()\">
          </div>
        </div>""")

# ---- 2. doSearch sends via --------------------------------------------------
rep("""  const from = (document.getElementById('fromInput')?.value || '').trim();
  const to = (document.getElementById('toInput')?.value || '').trim();
  const q = new URLSearchParams();
  if (from) q.set('from', from);
  if (to) q.set('to', to);""",
    """  const from = (document.getElementById('fromInput')?.value || '').trim();
  const to = (document.getElementById('toInput')?.value || '').trim();
  const via = (document.getElementById('viaInput')?.value || '').trim();
  const q = new URLSearchParams();
  if (from) q.set('from', from);
  if (to) q.set('to', to);
  if (via) q.set('via', via);""")

# ---- 3. renderSearch: via filter --------------------------------------------
rep("""  const from = (params.get('from') || '').toLowerCase().trim();
  const to = (params.get('to') || '').toLowerCase().trim();
  let results = Object.values(BUSES);

  if (from && to) {
    const posIn = (b, q) => {
      if ((b.origin || '').toLowerCase().includes(q)) return 0;
      const sts = b.stoppages || [];
      const idx = sts.findIndex(s => (s.name || '').toLowerCase().includes(q));
      if (idx >= 0) return idx + 1;
      if ((b.destination || '').toLowerCase().includes(q)) return sts.length + 2;
      return -1;
    };
    results = results.filter(b => {
      const fi = posIn(b, from), ti = posIn(b, to);
      return fi >= 0 && ti >= 0 && fi < ti;
    });
    if (!results.length) {
      results = Object.values(BUSES).filter(b => {
        const fi = posIn(b, from), ti = posIn(b, to);
        return fi >= 0 && ti >= 0;
      });
    }
  } else if (from || to) {""",
    """  const from = (params.get('from') || '').toLowerCase().trim();
  const to = (params.get('to') || '').toLowerCase().trim();
  const via = (params.get('via') || '').toLowerCase().trim();
  let results = Object.values(BUSES);

  if (from && to) {
    const posIn = (b, q) => {
      if ((b.origin || '').toLowerCase().includes(q)) return 0;
      const sts = b.stoppages || [];
      const idx = sts.findIndex(s => (s.name || '').toLowerCase().includes(q));
      if (idx >= 0) return idx + 1;
      if ((b.destination || '').toLowerCase().includes(q)) return sts.length + 2;
      return -1;
    };
    results = results.filter(b => {
      const fi = posIn(b, from), ti = posIn(b, to);
      if (!(fi >= 0 && ti >= 0 && fi < ti)) return false;
      if (via) {
        const vi = posIn(b, via);
        if (!(vi > fi && vi < ti)) return false;
      }
      return true;
    });
    if (!results.length && !via) {
      results = Object.values(BUSES).filter(b => {
        const fi = posIn(b, from), ti = posIn(b, to);
        return fi >= 0 && ti >= 0;
      });
    }
  } else if (from || to) {""")

# ---- 4. show 'via X' in the results header ----------------------------------
rep("""    ${from || to ? `<p style=\"color:var(--ink-dim);font-size:13.5px;margin-bottom:18px\">${esc(from || '…')} → ${esc(to || '…')}</p>` : ''}""",
    """    ${from || to ? `<p style=\"color:var(--ink-dim);font-size:13.5px;margin-bottom:18px\">${esc(from || '…')} → ${esc(to || '…')}${via ? ` <span class=\"badge badge-ac\">via ${esc(via)}</span>` : ''}</p>` : ''}""")

open(P, 'w', encoding='utf-8').write(src)
print('app.js via patch applied OK')
