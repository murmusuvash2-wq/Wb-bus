#!/usr/bin/env python3
"""
Patch gen_seo_pages.py and css/seo.css:

1. Fix "First —, last —" meta description — show proper description when no times.
2. Stat chips: skip First/Last chips, show "Departure times not listed" when None.
3. Bus cards: "Not Available" + "Add Time" button instead of "—:—".
4. User time update: inline <input type="time"> form, localStorage + WhatsApp.
5. CSS additions for new elements.
"""

import py_compile, os

GEN = "scripts/gen_seo_pages.py"
CSS = "css/seo.css"

def patch(filepath, old, new, name):
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    if old not in content:
        print(f"  SKIP: {name} — pattern not found")
        return False
    content = content.replace(old, new, 1)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  OK: {name}")
    return True


def main():
    os.chdir("/repo" if os.path.isdir("/repo") else ".")

    # 1. Meta description
    patch(GEN,
        'description = f"{origin} to {destination} bus timings, operators, stoppages. {count} buses listed. First {first}, last {last}."[:300]',
        'if stats["first"] is not None:\n        description = f"{origin} to {destination} bus timings. {count} buses listed. First {first}, last {last}. Check stoppages & operators."[:300]\n    else:\n        description = f"{origin} to {destination} bus timings and stoppages. {count} buses listed. Departure times vary \\u2014 check the timetable below or help by adding times."[:300]',
        "meta description fix")

    # 2. Stat chips: compute first_last_chips before hero
    patch(GEN,
        'hero = f"""<div class="breadcrumb">',
        'if stats["first"] is not None:\n        first_last_chips = f\'<span class="stat-chip">First <strong>{esc(first)}</strong></span>\\n    <span class="stat-chip">Last <strong>{esc(last)}</strong></span>\'\n    else:\n        first_last_chips = \'<span class="stat-chip">Departure times not listed \\u2014 help by adding times</span>\'\n    hero = f"""<div class="breadcrumb">',
        "stat chips conditional")

    # Replace the two chip lines with {first_last_chips}
    patch(GEN,
        '<span class="stat-chip">First <strong>{esc(first)}</strong></span>\n    <span class="stat-chip">Last <strong>{esc(last)}</strong></span>',
        '{first_last_chips}',
        "chip lines → variable")

    # 3. Bus card: dep_html + bus_id
    patch(GDN,
        "dep_html = f'<span class=\"dep.time\">{esc(dep)}</span>' if dep != \"\u2014\" else '<span class=\"no-time\">\u2014:\u2014</span>'",
        'bus_id = clean_text(bus.get("id")) or f"{slug(origin)}-{slug(destination)}-{idx}"\n'
        "    if dep != \"\u2014\":\n"
        '        dep_html = f\'<span class="dep.time" data-bus-id="{esc(bus_id)}">{esc(dep)}</span>\'\n'
        "    else:\n"
        "        dep_html = (\n"
        '            f\'<span class="no-time" data-bus-id="{esc(bus_id)}">Not Available</span>\'\n'
        '            f\'<button class="update-time-btn" onclick="openTimeUpdate(\\\'{esc(bus_id)}\\\',this)">\'\n'
        "            '<svg width=\"12\" height=\"12\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\">'\n"
        "            '<circle cx=\"12\" cy=\"12\" r=\"9\"/><path d=\"M12 7v5l3 2\"/></svg> Add Time</button>'\n"
        "        )",
        "bus_card dep_html + bus_id")

    # 4. data-bus-id on bus-card div
    patch(GEN,
        '<div class="bus-card" style="--i:{idx}" onclick="toggleBus(this,event)">',
        '<div class="bus-card" style="--i:{idx}" data-bus-id="{esc(bus_id)}" onclick="toggleBus(this,event)">',
        "bus-card data-bus-id")

    # 5. Add JS to shell
    OLD_JS = "(function(){{try{{var th=localStorage.getItem('seo-theme');if(th==='dark')document.body.classList.add('dark');var ln=localStorage.getItem('seo-lang');if(ln==='bn')document.body.classList.add('lang-bn')}}catch(e){{}}}})();"
    NEW_JS = OLD_JS + """
function openTimeUpdate(busId,btn){{
  var card=btn.closest('.bus-card');
  var existing=card.querySelector('.time-update-form');
  if(existing){{existing.remove();return}}
  var f=document.createElement('div');
  f.className='time-update-form';
  f.innerHTML='<input type="time" id="tu_'+busId+'" step="600"><button onclick="saveBusTime(\\''+busId+'\\')" class="tu-save">Save</button><button onclick="this.parentElement.remove()" class="tu-cancel">Cancel</button>';
  btn.parentElement.appendChild(f);
  var inp=f.querySelector('input');
  if(inp)inp.focus();
}}
function saveBusTime(busId){{
  var inp=document.getElementById('tu_'+busId);
  if(!inp||!inp.value){{alert('Please enter a valid time');return}}
  var parts=inp.value.split(':');
  var h=parseInt(parts[0]),m=parts[1];
  var ap=h>=12?'PM':'AM';
  var h12=h%12||12;
  var timeStr=h12+':'+m+' '+ap;
  try{{
    var updates=JSON.parse(localStorage.getItem('bj-user-times')||'{{}}');
    updates[busId]={{time:timeStr,ts:Date.now()}};
    localStorage.setItem('bj-user-times',JSON.stringify(updates));
  }}catch(e){{}}
  var span=document.querySelector('[data-bus-id="'+busId+'"]');
  if(span){{
    span.textContent=timeStr;
    span.className='dep.time user-updated';
    if(!span.parentElement.querySelector('.user-badge')){{
      var badge=document.createElement('span');
      badge.className='user-badge';
      badge.innerHTML='<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M20 6 9 17l-5-5"/></svg> User updated';
      span.parentElement.appendChild(badge);
    }}
  }}
  var form=document.querySelector('.time-update-form');
  if(form)form.remove();
  var page=document.title.split('|')[0].trim();
  var msg='BusJatri time update:\\n'+page+'\\nBus: '+busId+'\\nNew departure: '+timeStr+'\\n(Please verify & update master data)';
  window.open('https://wa.me/?text='+encodeURIComponent(msg),'_blank');
}}
function restoreUserTimes(){{
  try{{
    var updates=JSON.parse(localStorage.getItem('bj=user-times')||'{{}}');
    for(var busId in updates){{
      var span=document.querySelector('[data-bus-id="'+busId+'"]');
      if(span&&span.className.indexOf('no-time')>=0){{
        span.textContent=updates[busId].time;
        span.className='dep.time user-updated';
        if(!span.parentElement.querySelector('.user-badge')){{
          var badge=document.createElement('span');
          badge.className='user-badge';
          badge.innerHTML='<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M20 6 9 17l-5-5"/></svg> User updated';
          span.parentElement.appendChild(badge);
        }}
      }}
    }}
  }}catch(e){{}}
}}
document.addEventListener('DOMContentLoaded',restoreUserTimes);"""
    patch(GEN, OLD_JS, NEW_JS, "shell JS — update time functions")

    # 6. CSS additions
    CSS_ADD = """
/* ===== User time update ===== */
.no-time{font-size:11px;color:var(--ink-dim);font-weight:700;text-transform:uppercase;letter-spacing:.03em}
.update-time-btn{background:var(--amber-soft);border:1px solid color-mix(in srgb,var(--amber) 50%,transparent);border-radius:999px;padding:5px 11px;font-size:11px;font-weight:700;color:var(--amber-ink);cursor:pointer;font-family:var(--font-mono);min-height:32px;display:inline-flex;align-items:center;gap:3px;transition:all .15s;white-space:nowrap}
.update-time-btn:hover{background:var(--amber);color:#fff;border-color:var(--amber)}
.user-updated{color:var(--green)!important}
.user-badge{font-size:10px;color:var(--green);font-weight:700;background:var(--green-soft);padding:2px 8px;border-radius:999px;margin-left:4px;display:inline-flex;align-items:center;gap:3px;font-family:var(--font-mono);white-space:nowrap}
.user-badge svg{flex-shrink:0}
.time-update-form{display:flex;gap:6px;align-items:center;margin-top:6px;padding:8px 10px;background:var(--surface-2);border-radius:9px;border:1px solid var(--line)}
.time-update-form input[type="time"]{padding:8px 10px;border:1px solid var(--line-strong);border-radius:6px;background:var(--surface);color:var(--ink);font-family:var(--font-mono);font-size:14px;font-weight:700;min-height:44px;flex:1;max-width:140px}
.tu-save{background:var(--green);color:#fff;border:none;border-radius:6px;padding:8px 16px;font-size:13px;font-weight:700;cursor:pointer;min-height:44px;font-family:var(--font-body)}
.tu-save:hover{opacity:.85}
.tu-cancel{background:none;border:none;color:var(--ink-dim);font-size:13px;cursor:pointer;min-height:44px;padding:8px}
@media(prefers-reduced-motion:reduce){.update-time-btn,.user-badge{transition:none}}
/* ===== End user time update ===== */"""
    with open(CSS, encoding="utf-8") as f:
        css_content = f.read()
    if ".update-time-btn" not in css_content:
        css_content = css_content.rstrip() + "\n" + CSS_ADD.strip() + "\n"
        with open(CSS, "w", encoding="utf-8") as f:
            f.write(css_content)
        print("  OK: CSS additions")
    else:
        print("  SKIP: CSS already has additions")

    py_compile.compile(GEN, doraise=True)
    print("\nSyntax OK — ready to generate pages.")


if __name__ == "__main__":
    main()
