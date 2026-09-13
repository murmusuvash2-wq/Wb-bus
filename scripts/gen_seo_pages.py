#!/usr/bin/env python3
"""Generate static bilingual (EN/Bangla) SEO pages for BusJatri.

Pages: bus-time-table/<from>-to-<to>.html (routes >=2 buses), buses-from-<place>.html,
index, sitemap.xml, robots.txt. All paths relative so they work on any host.

Every page carries the full text in both languages via .label-en / .label-bn
spans (same system as the home page SPA) with a header EN/বাংলা toggle.
The choice is remembered in localStorage ('bj-lang') and shared with the SPA.
"""
import json, re, os, html, glob, shutil
from collections import Counter, defaultdict
from datetime import datetime

DATA = 'data/busjatri_data.json'
OUT = 'bus-time-table'
BASE = os.environ.get('SITE_BASE', 'https://wb-bus.vercel.app').rstrip('/')
LASTMOD = datetime.now().strftime('%Y-%m-%d')

d = json.load(open(DATA))
BUSES = d['buses']

# ---------------------------------------------------------------------------
# Bengali place names (confident mappings only; missing places fall back to EN)
# ---------------------------------------------------------------------------
BN = {
 'Bankura':'বাঁকুড়া','Digha':'দীঘা','Kolkata':'কলকাতা','Medinipur':'মেদিনীপুর',
 'Bardhaman':'বর্ধমান','Burdwan':'বর্ধমান','Kharagpur':'খড়্গপুর','Siliguri':'শিলিগুড়ি',
 'Cooch Behar':'কোচবিহার','Asansol':'আসানসোল','Durgapur':'দুর্গাপুর','Purulia':'পুরুলিয়া',
 'Jhargram':'ঝাড়গ্রাম','Contai':'কাঁথি','Tamluk':'তমলুক','Bishnupur':'বিষ্ণুপুর',
 'Khatra':'খাতড়া','Alipurduar':'আলিপুরদুয়ার','Dinhata':'দিনহাটা','Mathabhanga':'মাথাভাঙ্গা',
 'Ghatal':'ঘাটাল','Nabadwip':'নবদ্বীপ','Arambagh':'আরামবাগ','Manbazar':'মানবাজার',
 'Tarkeshwar':'তারকেশ্বর','Mecheda':'মেছেদা','Haldia':'হলদিয়া','Baruipur':'বারুইপুর',
 'Esplanade':'এসপ্ল্যানেড','Howrah':'হাওড়া','Ranaghat':'রানাঘাট','Krishnanagar':'কৃষ্ণনগর',
 'Malda':'মালদা','Raiganj':'রায়গঞ্জ','Balurghat':'বালুরঘাট','Suri':'সিউড়ি',
 'Sainthia':'সাঁইথিয়া','Bolpur':'বোলপুর','Kalna':'কালনা','Guskara':'গুসকরা',
 'Katwa':'কাটোয়া','Bandel':'বান্দেল','Chandannagar':'চন্দননগর','Kalyani':'কল্যাণী',
 'Barasat':'বারাসাত','Barrackpore':'ব্যারাকপুর','Dunlop':'ডানলপ','Garia':'গড়িয়া',
 'Tarakeswar':'তারকেশ্বর','Jangipur':'জঙ্গীপুর','Berhampore':'বহরমপুর',
 'Berhampur':'বহরমপুর','Salar':'সালার','Kirnahar':'কীর্ণাহার','Ilam Bazar':'ইলাম বাজার',
 # extended
 'Baharampur':'বাহরামপুর','Raniganj':'রানিগঞ্জ','Barjora':'বড়জোড়া','Beliatore':'বেলিয়াটোর',
 'Chittaranjan':'চিত্তরঞ্জন','Barakar':'বারাকর','Rampurhat':'রামপুরহাট','Sonamukhi':'সোনামুখী',
 'Egra':'এগরা','Panskura':'পাঁসকুরা','Kolaghat':'কোলাঘাট','Durgachak':'দুর্গাচক',
 'Chandrakona':'চন্দ্রকোণা','Garhbeta':'গড়বেতা','Goaltore':'গোয়ালটোর','Belpahari':'বেলপাহাড়ি',
 'Silda':'শিলদা','Lalgarh':'লালগড়','Gopiballavpur':'গোপীবল্লভপুর','Binpur':'বীণপুর',
 'Simlapal':'সিমলাপাল','Tufanganj':'তুফানগঞ্জ','Falakata':'ফলকাটা','Maynaguri':'ময়নাগুড়ি',
 'Dhupguri':'ধুপগুড়ি','Jalpaiguri':'জলপাইগুড়ি','Mekhliganj':'মেখলিগঞ্জ','Dhubri':'ধুবরি',
 'Ranchi':'রাঁচি','Tatanagar':'টাটানগর','Dhanbad':'ধানবাদ','Bokaro':'বোকারো',
 'Bhubaneswar':'ভুবনেশ্বর','Midnapore':'মেদিনীপুর','Kakdwip':'কাকদ্বীপ','Namkhana':'নামখানা',
 'Diamond Harbour':'ডায়মন্ড হারবার','Karunamoyee':'করুণাময়ী','Nabanna':'নবান্ন',
 'Saltora':'সলতোড়া','Ajodhya Hills':'অযোধ্যা পাহাড়','Mukutmanipur':'মুকুটমণিপুর',
 'Kamarpukur':'কামারপুকুর','Benachity':'বেনাচিটি','Chirkunda':'চিরকুন্ডা',
 'Pandaveswar':'পান্ডবেশ্বর','Dishergarh':'ডিসেরগড়','Patrasayer':'পত্রসায়ের',
 'Shyambazar':'শ্যামবাজার','Amtala':'আমতলা','Bakra':'বাকড়া','Farakka':'ফরাক্কা',
}


# ---------------------------------------------------------------------------
# District grouping for the All Routes page (curated; unmapped -> 'Other')
# ---------------------------------------------------------------------------
DISTRICTS = {
 'Bankura': 'Bankura', 'Bishnupur': 'Bankura', 'Khatra': 'Bankura', 'Ranibandh': 'Bankura',
 'Sonamukhi': 'Bankura', 'Patrasayer': 'Bankura', 'Kotulpur': 'Bankura', 'Simlapal': 'Bankura',
 'Kenjakura': 'Bankura', 'Sarenga': 'Bankura', 'Fulkusma': 'Bankura', 'Raipur': 'Bankura',
 'Ramgarh': 'Bankura', 'Jhantipahari': 'Bankura', 'Lakshmisagar': 'Bankura', 'Guniada': 'Bankura',
 'Baksi': 'Bankura', 'Chendapathar': 'Bankura', 'Kutni': 'Bankura', 'Khetua': 'Bankura',
 'Raskundu': 'Bankura', 'Bhutsahar': 'Bankura', 'Ramsagar': 'Bankura',
 'Purulia': 'Purulia', 'Manbazar': 'Purulia', 'Bandwan': 'Purulia', 'Balarampur': 'Purulia',
 'Barabazar': 'Purulia', 'Ajodhya Hills': 'Purulia', 'Chelyama': 'Purulia',
 'Asansol': 'Paschim Bardhaman', 'Durgapur (Station)': 'Paschim Bardhaman',
 'Durgapur (City Center)': 'Paschim Bardhaman', 'Raniganj': 'Paschim Bardhaman',
 'Barakar': 'Paschim Bardhaman', 'Chittaranjan': 'Paschim Bardhaman', 'Benachity': 'Paschim Bardhaman',
 'Pandaveswar': 'Paschim Bardhaman', 'Jamtoria': 'Paschim Bardhaman', 'Chandankyari': 'Paschim Bardhaman',
 'Bardhaman': 'Purba Bardhaman', 'Kalna': 'Purba Bardhaman', 'Katwa': 'Purba Bardhaman',
 'Madanmohanpur': 'Purba Bardhaman',
 'Medinipur': 'Paschim Medinipur', 'Kharagpur': 'Paschim Medinipur',
 'Chandrakona Road': 'Paschim Medinipur', 'Chandrakona Town': 'Paschim Medinipur',
 'Ghatal': 'Paschim Medinipur', 'Dantan': 'Paschim Medinipur', 'Hijli Sorif': 'Paschim Medinipur',
 'Jhargram': 'Jhargram', 'Silda': 'Jhargram', 'Lalgarh': 'Jhargram', 'Belpahari': 'Jhargram',
 'Binpur': 'Jhargram', 'Amlasuli': 'Jhargram',
 'Digha': 'Purba Medinipur', 'Contai': 'Purba Medinipur', 'Haldia': 'Purba Medinipur',
 'Egra': 'Purba Medinipur', 'Panskura': 'Purba Medinipur', 'Mecheda': 'Purba Medinipur',
 'Moyna': 'Purba Medinipur', 'Gadiara': 'Purba Medinipur', 'Bhagabanpur': 'Purba Medinipur',
 'Chichra': 'Purba Medinipur', 'Itaberia': 'Purba Medinipur', 'Balaipanda': 'Purba Medinipur',
 'Runakuraghat': 'Purba Medinipur', 'Patharmora': 'Purba Medinipur', 'Shikarpur': 'Purba Medinipur',
 'Samaspur': 'Purba Medinipur', 'Solpatta': 'Purba Medinipur',
 'Howrah': 'Howrah', 'Kukrahati': 'Howrah',
 'Kolkata': 'Kolkata', 'Kolkata (Esplanade)': 'Kolkata', 'Garia': 'Kolkata',
 'Shyambazar': 'Kolkata', 'Jadavpore': 'Kolkata', 'Parnasree': 'Kolkata',
 'Tarkeshwar': 'Hooghly', 'Arambagh': 'Hooghly', 'Chuchura': 'Hooghly',
 'Krishnanagar': 'Nadia', 'Nabadwip': 'Nadia', 'Karimpur': 'Nadia',
 'Bolpur': 'Birbhum', 'Patharchapuri': 'Birbhum',
 'Baharampur': 'Murshidabad', 'Domkal': 'Murshidabad', 'Salar': 'Murshidabad', 'Sagarpara': 'Murshidabad',
 'Cooch Behar': 'Cooch Behar', 'Mathabhanga': 'Cooch Behar', 'Dinhata': 'Cooch Behar', 'Tufanganj': 'Cooch Behar',
 'Alipurduar': 'Alipurduar',
 'Tatanagar': 'Jharkhand', 'Ranchi': 'Jharkhand',
 'Bhubaneswar': 'Odisha',
}
DISTRICT_META = {
 'Bankura': ('Bankura District', 'বাঁকুড়া জেলা'),
 'Purulia': ('Purulia District', 'পুরুলিয়া জেলা'),
 'Paschim Bardhaman': ('Paschim Bardhaman District', 'পশ্চিম বর্ধমান জেলা'),
 'Purba Bardhaman': ('Purba Bardhaman District', 'পূর্ব বর্ধমান জেলা'),
 'Paschim Medinipur': ('Paschim Medinipur District', 'পশ্চিম মেদিনীপুর জেলা'),
 'Jhargram': ('Jhargram District', 'ঝাড়গ্রাম জেলা'),
 'Purba Medinipur': ('Purba Medinipur District', 'পূর্ব মেদিনীপুর জেলা'),
 'Howrah': ('Howrah District', 'হাওড়া জেলা'),
 'Kolkata': ('Kolkata', 'কলকাতা'),
 'Hooghly': ('Hooghly District', 'হুগলি জেলা'),
 'Nadia': ('Nadia District', 'নদীয়া জেলা'),
 'Birbhum': ('Birbhum District', 'বীরভূম জেলা'),
 'Murshidabad': ('Murshidabad District', 'মুরশিদাবাদ জেলা'),
 'Cooch Behar': ('Cooch Behar District', 'কোচবিহার জেলা'),
 'Alipurduar': ('Alipurduar District', 'আলিপুরদুয়ার জেলা'),
 'Jharkhand': ('Jharkhand (outside WB)', 'ঝাড়খণ্ড'),
 'Odisha': ('Odisha (outside WB)', 'ওডিশা'),
 'Other': ('More Places', 'আরও জায়গা'),
}

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def slug(s): return re.sub(r'[^a-z0-9]+', '-', str(s).lower()).strip('-')
def esc(s): return html.escape(str(s or ''), quote=True)

def lbl(en, bn_):
    """bilingual label spans"""
    if bn_ and bn_ != en:
        return f'<span class="label-en">{en}</span><span class="label-bn">{esc(bn_)}</span>'
    return str(en)

def place(name):
    """place name, bilingual if we have a Bangla mapping"""
    n = str(name or '').strip()
    if not n or n == '—': return '—'
    b = BN.get(n)
    if b: return f'<span class="label-en">{esc(n)}</span><span class="label-bn">{esc(b)}</span>'
    return esc(n)

def place_plain(name): return esc(str(name or '').strip())

BN_DIG = str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯')
def bnum(x): return str(x).translate(BN_DIG)

def parse_time(t):
    if not t: return None
    m = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)?', str(t).strip(), re.I)
    if not m: return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), (m.group(3) or '').upper()
    if ap == 'PM' and h < 12: h += 12
    if ap == 'AM' and h == 12: h = 0
    return h * 60 + mi

def hhmm(m):
    return f'{(m//60)%12 or 12}:{m%60:02d} {"AM" if (m//60)<12 else "PM"}'

def bn_time(m):
    """minutes -> Bangla time, e.g. সকাল ৫:৪৫"""
    h = m // 60
    if 4 <= h <= 5: part = 'ভোর'
    elif 6 <= h <= 11: part = 'সকাল'
    elif 12 <= h <= 15: part = 'দুপুর'
    elif 16 <= h <= 17: part = 'বিকেল'
    elif 18 <= h <= 19: part = 'সন্ধ্যা'
    else: part = 'রাত'
    return f'{part} {bnum((h%12) or 12)}:{bnum(f"{m%60:02d}")}'

def fmt_dur(mins):
    h, m = divmod(int(mins), 60)
    return f'{h}h {m:02d}m' if h else f'{m}m'

def bn_dur(mins):
    h, m = divmod(int(mins), 60)
    if h and m: return f'{bnum(h)} ঘণ্টা {bnum(m)} মিনিট'
    if h: return f'{bnum(h)} ঘণ্টা'
    return f'{bnum(m)} মিনিট'

# ---- bus name / type cleaning --------------------------------------------
def clean_bus(b):
    """fix garbled names like 'KALOSONA Registration WB29G9687 Type — Op' (truncated in source)"""
    nm = (b.get('bus_name') or '').strip()
    regn = (b.get('reg_no') or '').strip()
    if ' Registration ' in nm:
        head, rest = nm.split(' Registration ', 1)
        if head.strip():
            nm = head.strip()
            if not regn and rest.strip():
                regn = rest.split()[0]
    # 'govtb8'-style codes are internal source IDs, not real registrations
    if regn and re.match(r'^govt?b?[0-9]+$', regn.strip(), re.I):
        regn = ''
    if regn:
        regn = regn.strip().upper()
    # title-case nicer names (keep govt acronyms as-is)
    ACRO = {'SBSTC', 'NBSTC', 'WBTC', 'CSTC'}
    if nm and nm.isupper() and len(nm) > 3:
        if "'" in nm or len(nm.split()) > 1:
            nm = ' '.join(w.capitalize() if not w.isdigit() else w for w in nm.split())
        elif nm not in ACRO:
            nm = nm.capitalize()
    return nm, regn

def type_badges(bt, nm=''):
    g = (bt or '').lower()
    nl = (nm or '').lower()
    out = []
    if 'gov' in g or 'sbstc' in g or 'nbstc' in g or 'wbtc' in g or 'sbstc' in nl or 'nbstc' in nl or 'wbtc' in nl:
        out.append('<span class="badge badge-govt"><span class="label-en">Govt</span><span class="label-bn">সরকারি</span></span>')
    else:
        out.append('<span class="badge badge-private"><span class="label-en">Private</span><span class="label-bn">প্রাইভেট</span></span>')
    if 'ac' in g and 'non' not in g:
        out.append('<span class="badge badge-ac">AC</span>')
    return ' '.join(out)

def route_pairs():
    fwd = defaultdict(list)
    for b in BUSES:
        o, t = b.get('origin'), b.get('destination')
        if o and t and o != '—' and t != '—':
            fwd[(o, t)].append(b)
    return fwd

FWD = route_pairs()
groups = defaultdict(list)
for (o, t), bs in FWD.items():
    groups[tuple(sorted([o, t]))].extend(bs)
groups = {k: v for k, v in groups.items() if len(v) >= 2}

def buses_for(o, t):
    return FWD.get((o, t), [])

def bn(name): return BN.get(str(name).strip())

def merged_rows(bs):
    """clean + merge rows that share (name, regn) — keeps times from one, type from the other"""
    out = []
    for b in bs:
        nm, regn = clean_bus(b)
        key = (nm.lower(), regn)
        row = next((r for r in out if r[0] == key), None)
        cur = {
            'nm': nm, 'regn': regn,
            'dep': parse_time(b.get('departure_time')),
            'arr': parse_time(b.get('arrival_time')),
            'dep_raw': b.get('departure_time') or '',
            'arr_raw': b.get('arrival_time') or '',
            'type': b.get('bus_type') or '',
            'stops': b.get('total_stoppages') or len(b.get('stoppages') or []),
        }
        if row is None:
            out.append((key, cur))
        else:
            r = row[1]
            # same regn = same physical bus duplicated across sources;
            # no regn + one side has no times = incomplete duplicate row.
            # otherwise two same-named buses are different trips - keep both.
            cur_empty = cur['dep'] is None and cur['arr'] is None
            r_empty = r['dep'] is None and r['arr'] is None
            if regn or cur_empty or r_empty:
                if r['dep'] is None: r['dep'], r['dep_raw'] = cur['dep'], cur['dep_raw']
                if r['arr'] is None: r['arr'], r['arr_raw'] = cur['arr'], cur['arr_raw']
                if not r['type']: r['type'] = cur['type']
                if not r['stops']: r['stops'] = cur['stops']
            else:
                out.append((key, cur))
    rows = [r for _, r in out]
    rows.sort(key=lambda r: r['dep'] if r['dep'] is not None else 9999)
    return rows

# ---------------------------------------------------------------------------
# page shell
# ---------------------------------------------------------------------------
CSS = '../css/style.css'
CSS2 = '../css/seo.css'

def shell(title, desc, canonical, body, extra_schema='', og_type='article'):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#b8791f">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="BusJatri">
<meta name="twitter:card" content="summary">
<meta property="og:image" content="{BASE}/og-image.png">
<meta name="twitter:image" content="{BASE}/og-image.png">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b8791f' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10'/%3E%3Cpath d='M4 16h16'/%3E%3Cpath d='M4 16v2a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-2'/%3E%3Cpath d='M17 16v2a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-2'/%3E%3Cpath d='M6 10h12'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,500;0,600;0,700;0,900;1,500&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Sans+Bengali:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{CSS}">
<link rel="stylesheet" href="{CSS2}">
{extra_schema}
</head>
<body>
<header class="header"><div class="container header-inner">
<a class="logo" href="../index.html" aria-label="BusJatri home">
<svg class="icon" viewBox="0 0 24 24" style="width:1.35rem;height:1.35rem"><path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"/><path d="M4 16h16"/><path d="M4 16v2a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-2"/><path d="M17 16v2a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-2"/><path d="M6 10h12"/></svg>Bus<span>Jatri</span></a>
<div class="header-actions">
<div class="lang-group" role="group" aria-label="Language">
<button class="lang-btn active" id="langEN" onclick="setLang('en')">EN</button>
<button class="lang-btn" id="langBN" onclick="setLang('bn')">বাংলা</button>
</div>
<button class="icon-btn" onclick="toggleTheme()" title="Toggle theme" aria-label="Toggle dark mode">◐</button>
</div>
</div></header>
<main class="container" style="padding-top:0;padding-bottom:40px">
{body}
</main>
<footer class="footer"><div class="container">
<p><strong>BusJatri</strong> — {lbl(esc('West Bengal bus timetable. Timings can change; verify with the operator or depot before travelling.'), 'পশ্চিমবঙ্গের বাস টাইম টেবিল। সময় বদলাতে পারে — যাত্রার আগে অপারেটর বা ডিপো থেকে নিশ্চিত করে নিন।')}</p>
<p><a href="../index.html">{lbl('Home', 'হোম')}</a> · <a href="./">{lbl('All Bus Time Tables', 'সব বাস টাইম টেবিল')}</a></p>
</div></footer>
<script>
(function () {{
  var saved = null;
  try {{ saved = localStorage.getItem('bj-lang'); }} catch (e) {{}}
  var lang = saved || ((navigator.language || '').toLowerCase().indexOf('bn') === 0 ? 'bn' : 'en');
  window.setLang = function (l) {{
    document.body.className = l === 'bn' ? 'lang-bn' : '';
    document.getElementById('langEN').classList.toggle('active', l === 'en');
    document.getElementById('langBN').classList.toggle('active', l === 'bn');
    document.documentElement.setAttribute('lang', l === 'bn' ? 'bn' : 'en');
    try {{ localStorage.setItem('bj-lang', l); }} catch (e) {{}}
  }};
  setLang(lang);
  var t = null;
  try {{ t = localStorage.getItem('bj-theme'); }} catch (e) {{}}
  if (t === 'dark' || t === 'light') document.documentElement.setAttribute('data-theme', t);
  window.toggleTheme = function () {{
    var root = document.documentElement;
    var dark = root.getAttribute('data-theme') === 'dark' ||
      (!root.getAttribute('data-theme') && matchMedia('(prefers-color-scheme: dark)').matches);
    root.setAttribute('data-theme', dark ? 'light' : 'dark');
    try {{ localStorage.setItem('bj-theme', dark ? 'light' : 'dark'); }} catch (e) {{}}
  }};
}})();
</script>
</body>
</html>'''

def faq_schema(faqs):
    items = ', '.join(
        json.dumps({'@type': 'Question', 'name': q,
                    'acceptedAnswer': {'@type': 'Answer', 'text': a}}, ensure_ascii=False)
        for q, a in faqs)
    return f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{items}]}}</script>'

def breadcrumb(items):
    lst = ', '.join(json.dumps(
        {'@type': 'ListItem', 'position': i + 1, 'name': n,
         'item': f'{BASE}{u}' if u else n}, ensure_ascii=False)
        for i, (n, u) in enumerate(items))
    return f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{lst}]}}</script>'

CHEV = '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 18l6-6-6-6"/></svg>'

def crumbs(bn_label):
    return (f'<nav class="crumbs" aria-label="Breadcrumb">'
            f'<a href="../index.html">{lbl("Home", "হোম")}</a> {CHEV} '
            f'<a href="./">{lbl("Bus Time Table", "বাস টাইম টেবিল")}</a> {CHEV} '
            f'<span aria-current="page">{bn_label}</span></nav>')

# wipe stale pages from previous runs so the deployed dir always matches the data
os.makedirs(OUT, exist_ok=True)
for f in glob.glob(os.path.join(OUT, '*.html')):
    os.remove(f)
sitemap = []
written = []

# ---------------------------------------------------------------------------
# route pages
# ---------------------------------------------------------------------------
route_meta = {}
for (a, b) in sorted(groups):
    for o, t in [(a, b), (b, a)]:
        if buses_for(o, t):
            route_meta[(o, t)] = buses_for(o, t)

for (o, t), bs in route_meta.items():
    fname = f'{slug(o)}-to-{slug(t)}.html'
    bo, bt_ = bn(o), bn(t)
    bn_r = f'{bo} থেকে {bt_}' if bo and bt_ else None
    title = f'{o} to {t} Bus Time Table' + (f' | {bn_r}' if bn_r else '')
    rows = merged_rows(bs)
    n = len(rows)
    times = sorted(x for x in (r['dep'] for r in rows) if x is not None)
    firstm, lastm = (min(times), max(times)) if times else (None, None)
    ops = sorted({(b.get('operator') or '').strip() for b in bs
                  if (b.get('operator') or '').strip() and b['operator'] != '—'})
    ops = [re.sub(r"'S$|'s$", "'s", x).strip() for x in ops if x != '—']
    med_dur = None
    durs = []
    for r in rows:
        if r['dep'] is not None and r['arr'] is not None:
            dd = r['arr'] - r['dep'] if r['arr'] > r['dep'] else r['arr'] + 1440 - r['dep']
            if 0 < dd < 900: durs.append(dd)
    if durs: med_dur = sorted(durs)[len(durs)//2]

    q_first = hhmm(firstm) if firstm is not None else '—'
    q_last = hhmm(lastm) if lastm is not None else '—'
    has_govt = any('gov' in (r['type'] or '').lower() or 'sbstc' in (r['nm'] or '').lower()
                   or 'nbstc' in (r['nm'] or '').lower() or 'wbtc' in (r['nm'] or '').lower() for r in rows)

    # ---- bilingual FAQs (schema stays English; page shows both) ----
    faqs_en, faqs_bn = [], []
    if firstm is not None:
        faqs_en.append((f'What is the first bus from {o} to {t}?',
                        f'The first bus from {o} to {t} departs at {q_first}. Timings may vary by day — always verify before travelling.'))
        faqs_bn.append((f'{bo} থেকে {bt_} প্রথম বাস কখন ছাড়ে?' if bn_r else f'What is the first bus from {o} to {t}?',
                        f'প্রথম বাস {bn_time(firstm)}-এ ছাড়ে। সময় বদলাতে পারে — যাত্রার আগে নিশ্চিত করে নিন।'))
    if lastm is not None:
        faqs_en.append((f'What is the last bus from {o} to {t}?',
                        f'The last bus from {o} to {t} departs at {q_last}.'))
        faqs_bn.append(('শেষ বাস কখন ছাড়ে?', f'শেষ বাস {bn_time(lastm)}-এ ছাড়ে।'))
    g = len(groups[tuple(sorted([o, t]))])
    n_word = f'{n} bus' if n == 1 else f'{n} buses'
    faqs_en.append((f'How many buses run from {o} to {t}?',
                    f'{n_word.capitalize()} run directly from {o} to {t} each day; counting both directions, '
                    f'{g} bus services connect the two places.'
                    + (f' Major operators: {", ".join(ops[:4])}.' if ops else '')))
    faqs_bn.append(('দিনে কতগুলো বাস চলে?', f'সরাসরি {bnum(n)}টি বাস {bo or o} থেকে {bt_ or t} চলে; দুই দিকে মিলিয়ে মোট {bnum(g)}টি।'
                    + (f' প্রধান অপারেটর: {", ".join(ops[:4])}।' if ops else '')))
    if med_dur:
        faqs_en.append((f'How long does the bus take from {o} to {t}?',
                        f'The journey takes approximately {fmt_dur(med_dur)} by bus, depending on stops, traffic and bus type.'))
        faqs_bn.append(('কত সময় লাগে?', f'প্রায় {bn_dur(med_dur)} — স্টপ, ট্রাফিক ও বাসের ধরনের উপর নির্ভর করে।'))
    faqs_en.append((f'Are there government (SBSTC/WBTC/NBSTC) buses from {o} to {t}?',
                    ('Yes — government SBSTC/WBTC/NBSTC services run on this route; check the Type column in the timetable above.'
                     if has_govt else
                     'This route is mainly served by private operators. Check the Type column in the timetable above.')))
    faqs_bn.append(('সরকারি (SBSTC/WBTC/NBSTC) বাস আছে কি?',
                    ('হ্যাঁ — এই রুটে সরকারি বাস চলে; টাইম টেবিলের "ধরন" কলাম দেখুন।' if has_govt
                     else 'এই রুটে মূলত প্রাইভেট অপারেটর চলে। "ধরন" কলাম দেখুন।')))

    desc = (f'{o} to {t} bus time table: {n} buses with departure & arrival timings, operators, stoppages. '
            f'First bus {q_first}, last bus {q_last}.')[:300]

    # ---- hero ----
    sub_o_en = bo if bo else 'West Bengal'
    sub_o_bn = o
    sub_t_en = bt_ if bt_ else 'West Bengal'
    sub_t_bn = t
    hero = f'''<section class="route-hero" aria-labelledby="route-h1">
<p class="route-eyebrow"><svg class="icon" viewBox="0 0 24 24" style="width:13px;height:13px" aria-hidden="true"><path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"/><path d="M4 16h16"/></svg>{lbl('Route · Bus Time Table', 'রুট · বাস টাইম টেবিল')}</p>
<h1 id="route-h1" class="route-main">
<span class="route-end"><span class="place">{place(o)}</span><span class="sub"><span class="label-en">{esc(sub_o_en)}</span><span class="label-bn">{esc(sub_o_bn)}</span></span></span>
<svg class="icon route-arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14"/><path d="M12 5l7 7-7 7"/></svg>
<span class="route-end dest"><span class="place">{place(t)}</span><span class="sub"><span class="label-en">{esc(sub_t_en)}</span><span class="label-bn">{esc(sub_t_bn)}</span></span></span>
</h1>
<div class="route-dash"><span class="stamp">{lbl(f'Updated {LASTMOD}', f'আপডেট {LASTMOD}')}</span></div>
</section>'''

    stats = f'''<div class="stats" role="list">
<div class="stat" role="listitem"><div class="num">{n}</div><div class="label">{lbl('Direct buses', 'সরাসরি বাস')}</div></div>
<div class="stat" role="listitem"><div class="num">{lbl(q_first, bn_time(firstm) if firstm is not None else '—')}</div><div class="label">{lbl('First bus', 'প্রথম বাস')}</div></div>
<div class="stat" role="listitem"><div class="num">{lbl(q_last, bn_time(lastm) if lastm is not None else '—')}</div><div class="label">{lbl('Last bus', 'শেষ বাস')}</div></div>
{f'<div class="stat" role="listitem"><div class="num">' + lbl(fmt_dur(med_dur), bn_dur(med_dur)) + '</div><div class="label">' + lbl('Duration', 'সময় লাগে') + '</div></div>' if med_dur else ''}
</div>'''

    # ---- timetable ----
    trows = []
    for r in rows:
        dep_en = hhmm(r['dep']) if r['dep'] is not None else '—'
        arr_en = hhmm(r['arr']) if r['arr'] is not None else '—'
        dep = lbl(dep_en, bn_time(r['dep']) if r['dep'] is not None else '—')
        arr = lbl(arr_en, bn_time(r['arr']) if r['arr'] is not None else '—')
        regn = f'<div class="bus-regn">{esc(r["regn"])}</div>' if r['regn'] else ''
        trows.append(
            f'<tr><td><div class="bus-name">{esc(r["nm"] or "—")}</div>{regn}</td>'
            f'<td>{type_badges(r["type"], r["nm"])}</td>'
            f'<td class="time-cell">{dep}</td><td class="time-cell">{arr}</td>'
            f'<td class="stops-cell">{r["stops"] or "—"}</td></tr>')
    timetable = f'''<section class="section">
<h2 class="section-title"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>{esc(o)} {lbl("to", "থেকে")} {esc(t)} — {lbl("All Bus Timings", "সব বাসের সময়")}</h2>
<div class="bus-table-wrap">
<table class="bus-table">
<thead><tr>
<th scope="col">{lbl('Bus', 'বাস')}</th><th scope="col">{lbl('Type', 'ধরন')}</th>
<th scope="col">{lbl('Departure', 'ছাড়ে')}</th><th scope="col">{lbl('Arrival', 'পৌঁছায়')}</th>
<th scope="col">{lbl('Stops', 'স্টপ')}</th>
</tr></thead>
<tbody>{''.join(trows)}</tbody>
</table>
</div>
</section>'''

    # ---- stops timeline (from the bus with most stoppages) ----
    best = max(bs, key=lambda b: len(b.get('stoppages') or []))
    stops = (best.get('stoppages') or [])[:14]
    stop_lines = []
    for i, s in enumerate(stops):
        nm = s.get('name') or ''
        term = ' term' if i == 0 or i == len(stops) - 1 else ''
        fl = ' first-last' if term else ''
        tm = parse_time(s.get('up_time'))
        right = lbl(hhmm(tm), bn_time(tm)) if tm is not None else ''
        if i == 0:
            right = lbl('Origin', 'যাত্রা শুরু')
        elif i == len(stops) - 1:
            right = lbl('Destination', 'গন্তব্য')
        stop_lines.append(
            f'<div class="rstop-row"><span class="rstop-dot{term}"></span>'
            f'<span class="rstop-name{fl}">{place(nm)}</span>'
            f'<span class="rstop-km">{right}</span></div>')
    stops_html = ''
    if len(stop_lines) >= 3:
        stops_html = f'''<section class="section">
<h2 class="section-title"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"/><path d="M4 16h16"/></svg>{lbl('Major Stoppages on this Route', 'এই রুটের প্রধান স্টপেজ')}</h2>
<div class="stops-card">{''.join(stop_lines)}</div>
</section>'''

    # ---- FAQ ----
    faq_html = ''.join(
        f'<details class="faq-item"><summary>{lbl(esc(q_en), esc(q_bn))}</summary>'
        f'<p>{lbl(esc(a_en), esc(a_bn))}</p></details>'
        for (q_en, a_en), (q_bn, a_bn) in zip(faqs_en, faqs_bn))
    faq_section = f'''<section class="section">
<h2 class="section-title"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>{lbl('Frequently Asked Questions', 'সাধারণ জিজ্ঞাসা')}</h2>
{faq_html}
</section>'''

    # ---- related ----
    rel = [(oo, tt) for (oo, tt) in route_meta if oo == o and tt != t][:6]
    rel_html = ''
    if rel:
        chips = ' '.join(
            f'<a class="sugg-chip" href="{slug(oo)}-to-{slug(tt)}.html">{place(oo)} → {place(tt)}</a>'
            for oo, tt in rel)
        rel_html = f'''<section class="section">
<h2 class="section-title"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14"/><path d="M12 5l7 7-7 7"/></svg>{lbl(f'More buses from {esc(o)}', (f'{bo} থেকে আরও বাস' if bo else f'More buses from {esc(o)}'))}</h2>
<div class="chip-row">{chips}</div>
<p class="rev-callout"><svg class="icon" viewBox="0 0 24 24" style="width:16px;height:16px" aria-hidden="true"><path d="M17 1l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="M7 23l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>{lbl(f'Coming back? See the <a href="{slug(t)}-to-{slug(o)}.html"><strong>{esc(t)} to {esc(o)}</strong></a> return time table.', (f'ফিরে আসছেন? <a href="{slug(t)}-to-{slug(o)}.html"><strong>{bt_ or esc(t)} থেকে {bo or esc(o)}</strong></a> রিটার্ন টাইম টেবিল দেখুন।'))}</p>
</section>'''

    body = crumbs(f'{esc(o)} {lbl("to", "থেকে")} {esc(t)}') + hero + stats + timetable + stops_html + faq_section + rel_html
    schema = faq_schema(faqs_en) + '\n' + breadcrumb(
        [('Home', '/'), ('Bus Time Table', '/bus-time-table/'), (f'{o} to {t}', f'/bus-time-table/{fname}')])
    open(f'{OUT}/{fname}', 'w').write(shell(title, desc, f'{BASE}/bus-time-table/{fname}', body, schema))
    sitemap.append(f'{BASE}/bus-time-table/{fname}')
    written.append(fname)

# ---------------------------------------------------------------------------
# place pages (buses from X)
# ---------------------------------------------------------------------------
place_buses = defaultdict(list)
for b in BUSES:
    o = b.get('origin')
    if o and o != '—':
        place_buses[o].append(b)
by_place = defaultdict(list)
for (o, t) in route_meta:
    by_place[o].append((o, t))
hub_places = sorted(by_place, key=lambda p: -len(by_place[p]))
top_places = hub_places[:30]

for p in hub_places:
    bs = place_buses[p]
    n = len(bs)
    bn_p = bn(p)
    dests = Counter(b['destination'] for b in bs if b.get('destination') and b['destination'] != '—')
    top_dests = dests.most_common(12)
    fname = f'buses-from-{slug(p)}.html'
    title = f'Buses from {p}' + (f' | {bn_p} থেকে বাস' if bn_p else '') + ' — BusJatri'
    desc = f'All buses from {p}: {n} bus services with timings and destinations across West Bengal. Popular: ' + ', '.join(x for x, _ in top_dests[:3]) + '.'
    routes_from = [(t, c) for t, c in dests.most_common(24) if (p, t) in route_meta]
    chips = ' '.join(f'<a class="sugg-chip" href="{slug(p)}-to-{slug(t)}.html">{place(p)} → {place(t)}</a>' for t, c in routes_from) or \
        f'<p>{lbl("See the search on the ", "হোম পেজের সার্চ দেখুন — ")}<a href="../index.html">{lbl("home page", "")}</a>.</p>'
    body = f'''{crumbs(lbl(f'Buses from {esc(p)}', (f'{bn_p} থেকে বাস' if bn_p else f'Buses from {esc(p)}')))}
<section class="route-hero">
<h1 class="route-main"><span class="route-end"><span class="place">{place(p)}</span><span class="sub"><span class="label-en">{esc(bn_p) if bn_p else 'West Bengal'}</span><span class="label-bn">{esc(p)}</span></span></span></h1>
<div class="route-dash"><span class="stamp">{lbl(f'Updated {LASTMOD}', f'আপডেট {LASTMOD}')}</span></div>
</section>
<div class="stats" role="list"><div class="stat" role="listitem"><div class="num">{n}</div><div class="label">{lbl('Buses', 'টি বাস')}</div></div><div class="stat" role="listitem"><div class="num">{len(dests)}</div><div class="label">{lbl('Destinations', 'গন্তব্য')}</div></div></div>
<section class="section">
<h2 class="section-title">{lbl(f'Top routes from {esc(p)}', (f'{bn_p} থেকে জনপ্রিয় রুট' if bn_p else f'Top routes from {esc(p)}'))}</h2>
<div class="chip-row">{chips}</div>
</section>
<section class="section">
<h2 class="section-title">{lbl(f'All destinations from {esc(p)} ({len(dests)})', f'{esc(p)} থেকে সব গন্তব্য ({bnum(len(dests))})')}</h2>
<div class="chip-row">{' '.join(f'<a class="sugg-chip" href="{slug(p)}-to-{slug(t)}.html">{place(t)} ({c})</a>' for t, c in dests.most_common())}</div>
</section>'''
    schema = breadcrumb([('Home', '/'), ('Bus Time Table', '/bus-time-table/'), (f'Buses from {p}', f'/bus-time-table/{fname}')])
    open(f'{OUT}/{fname}', 'w').write(shell(title, desc, f'{BASE}/bus-time-table/{fname}', body, schema, og_type='website'))
    sitemap.append(f'{BASE}/bus-time-table/{fname}')
    written.append(fname)

# ---------------------------------------------------------------------------
# index page
# ---------------------------------------------------------------------------
idx_rows = ''.join(
    f'<section class="section" style="padding-top:14px"><h2 class="section-title">{place(p)} <span class="count">({len(routes)})</span></h2><div class="chip-row">'
    + ' '.join(f'<a class="sugg-chip" href="{slug(o)}-to-{slug(t)}.html">{place(o)} → {place(t)}</a>' for o, t in sorted(routes))
    + '</div></section>'
    for p, routes in sorted(by_place.items(), key=lambda kv: -len(kv[1])))
# ---- district sections ----
dist_map = defaultdict(list)
for p, routes_ in by_place.items():
    dist_map[DISTRICTS.get(p, 'Other')].append((p, routes_))
dist_order = sorted(dist_map, key=lambda d: (d == 'Other', -sum(len(r) for _, r in dist_map[d])))

PIN = '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>'

def district_section(d):
    places_ = dist_map[d]
    en_d, bn_d = DISTRICT_META[d]
    nroutes = sum(len(r) for _, r in places_)
    cards = ''.join(
        f'<a class="place-card" href="buses-from-{slug(p)}.html">'
        f'<span class="pc-name">{place(p)}</span>'
        f'<span class="pc-count">{lbl(f"{len(rs)} routes", f"{bnum(len(rs))}টি রুট")}</span></a>'
        for p, rs in sorted(places_, key=lambda kv: -len(kv[1])))
    open_attr = ' open' if d in dist_order[:3] else ''
    return (f'<details class="district-card"{open_attr}>'
            f'<summary>{PIN}{lbl(en_d, bn_d)}'
            f'<span class="dist-count">{lbl(f"{nroutes} routes", f"{bnum(nroutes)}টি রুট")}</span></summary>'
            f'<div class="place-cards">{cards}</div></details>')

districts_html = ''.join(district_section(d) for d in dist_order)

# ---- search card (plain string, JS braces must not hit the f-string) ----
search_js = """
<script>
(function () {
  var IDX = null;
  var input = document.getElementById('routeSearch');
  var list = document.getElementById('srList');
  if (!input || !list) return;
  fetch('search-index.json').then(function (r) { return r.json(); }).then(function (x) { IDX = x; });
  input.addEventListener('input', function () {
    if (!IDX) return;
    var q = input.value.trim().toLowerCase();
    list.innerHTML = '';
    if (!q) return;
    var out = [];
    for (var i = 0; i < IDX.length && out.length < 14; i++) {
      var e = IDX[i];
      if (e.en.toLowerCase().indexOf(q) !== -1 || (e.bn && e.bn.indexOf(q) !== -1)) out.push(e);
    }
    if (!out.length) {
      var d = document.createElement('div');
      d.className = 'sr-empty';
      d.innerHTML = '__EMPTY__';
      list.appendChild(d);
      return;
    }
    var frag = document.createDocumentFragment();
    out.forEach(function (e) {
      var a = document.createElement('a');
      a.className = 'sr-item' + (e.t === 'p' ? ' sr-place' : '');
      a.href = e.u;
      var s1 = document.createElement('span');
      s1.className = 'sr-en'; s1.textContent = e.en;
      a.appendChild(s1);
      if (e.bn) {
        var s2 = document.createElement('span');
        s2.className = 'sr-bn'; s2.textContent = e.bn;
        a.appendChild(s2);
      }
      frag.appendChild(a);
    });
    list.appendChild(frag);
  });
})();
</script>
"""
search_js = search_js.replace('__EMPTY__', lbl('No matching route or place', 'কোনো রুট বা জায়গা পাওয়া যায়নি'))

search_card = f"""
<section class="search-card" id="searchCard" aria-label="{esc('Search routes and places')}">
<div class="sc-row">
<svg class="icon sc-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
<input type="search" id="routeSearch" autocomplete="off"
 placeholder="{esc('Search: Digha / দীঘা / Bankura / বাঁকুড়া ...')}" aria-label="{esc('Search routes and places')}">
</div>
<div class="sc-hint">{lbl(f'{len(route_meta)} routes', f'{bnum(len(route_meta))}টি রুট')} · {lbl('English and বাংলা both work', 'ইংরেজি ও বাংলা দুটোই চলবে')}</div>
<div class="sr-list" id="srList" aria-live="polite"></div>
{search_js}
</section>"""

all_list = (f'<details class="all-list"><summary><svg class="icon" viewBox="0 0 24 24" aria-hidden="true">'
            f'<path d="M4 6h16M4 12h16M4 18h16"/></svg>'
            + lbl('All routes A-Z', 'সব রুট A-Z')
            + f' <span class="dist-count">{lbl(f"{len(route_meta)}", f"{bnum(len(route_meta))}")}</span></summary>{idx_rows}</details>')

body = f"""
<section class="route-hero">
<p class="route-eyebrow">{lbl('All Routes', 'সব রুট')}</p>
<h1 class="route-main"><span class="route-end"><span class="place">{lbl('West Bengal Bus Time Tables', 'পশ্চিমবঙ্গের বাস টাইম টেবিল')}</span></span></h1>
<div class="route-dash"><span class="stamp">{lbl(f'Updated {LASTMOD}', f'আপডেট {LASTMOD}')}</span></div>
</section>
<div class="stats" role="list"><div class="stat" role="listitem"><div class="num">{len(route_meta)}</div><div class="label">{lbl('Routes', 'রুট')}</div></div><div class="stat" role="listitem"><div class="num">{len(BUSES)}</div><div class="label">{lbl('Buses', 'বাস')}</div></div></div>
{search_card}
<section class="section" style="padding-top:0"><h2 class="section-title">{PIN}{lbl('Browse by District', 'জেলা অনুযায়ী দেখুন')}</h2></section>
{districts_html}
{all_list}
"""


schema = f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebSite","name":"BusJatri","url":"{BASE}"}}</script>'
open(f'{OUT}/index.html', 'w').write(shell('West Bengal Bus Time Tables — All Routes | BusJatri',
    f'Complete bus timetables for {len(route_meta)} routes across West Bengal with timings, operators and stoppages.',
    f'{BASE}/bus-time-table/', body, schema, og_type='website'))

# ---------------------------------------------------------------------------
# sitemap & robots
# ---------------------------------------------------------------------------
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
sm += f'<url><loc>{BASE}/</loc><lastmod>{LASTMOD}</lastmod><priority>1.0</priority></url>\n'
for u in [f'{BASE}/bus-time-table/'] + sitemap:
    sm += f'<url><loc>{u}</loc><lastmod>{LASTMOD}</lastmod><priority>0.8</priority></url>\n'
sm += '</urlset>'
# search index (client-side search on the All Routes page)
search = []
for (o, t) in route_meta:
    bo_, bt_2 = bn(o), bn(t)
    search.append({'t': 'r', 'u': f'{slug(o)}-to-{slug(t)}.html',
                   'en': f'{o} to {t}',
                   'bn': f'{bo_} থেকে {bt_2}' if bo_ and bt_2 else ''})
for p_ in hub_places:
    bp_ = bn(p_)
    search.append({'t': 'p', 'u': f'buses-from-{slug(p_)}.html',
                   'en': f'Buses from {p_}',
                   'bn': f'{bp_} থেকে বাস' if bp_ else ''})
json.dump(search, open(f'{OUT}/search-index.json', 'w'), ensure_ascii=False, separators=(',', ':'))

open('sitemap.xml', 'w').write(sm)
open('robots.txt', 'w').write(f'User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n')

print(json.dumps({'route_pages': len(route_meta), 'place_pages': len(hub_places),
                  'total_pages': len(written) + 1, 'sitemap_urls': len(sitemap) + 1}))
