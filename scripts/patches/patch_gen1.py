#!/usr/bin/env python3
"""Patch gen_seo_pages.py part 1: districts, regn, merge, FAQ, og:image, stat label."""

P = 'scripts/gen_seo_pages.py'
src = open(P, encoding='utf-8').read()
def rep(old, new, cnt=1):
    global src
    assert src.count(old) == cnt, f'pattern x{src.count(old)} (expected {cnt}): {old[:80]!r}'
    src = src.replace(old, new)

# ---------------------------------------------------------------- A. districts
DISTRICTS = '''
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
 'Bankura': ('Bankura District', '\u09ac\u09be\u0981\u0995\u09c1\u09dc\u09be \u099c\u09c7\u09b2\u09be'),
 'Purulia': ('Purulia District', '\u09aa\u09c1\u09b0\u09c1\u09b2\u09bf\u09af\u09bc\u09be \u099c\u09c7\u09b2\u09be'),
 'Paschim Bardhaman': ('Paschim Bardhaman District', '\u09aa\u09b6\u09cd\u099a\u09bf\u09ae \u09ac\u09b0\u09cd\u09a7\u09ae\u09be\u09a8 \u099c\u09c7\u09b2\u09be'),
 'Purba Bardhaman': ('Purba Bardhaman District', '\u09aa\u09c2\u09b0\u09cd\u09ac \u09ac\u09b0\u09cd\u09a7\u09ae\u09be\u09a8 \u099c\u09c7\u09b2\u09be'),
 'Paschim Medinipur': ('Paschim Medinipur District', '\u09aa\u09b6\u09cd\u099a\u09bf\u09ae \u09ae\u09c7\u09a6\u09bf\u09a8\u09c0\u09aa\u09c1\u09b0 \u099c\u09c7\u09b2\u09be'),
 'Jhargram': ('Jhargram District', '\u099d\u09be\u09dc\u0997\u09cd\u09b0\u09be\u09ae \u099c\u09c7\u09b2\u09be'),
 'Purba Medinipur': ('Purba Medinipur District', '\u09aa\u09c2\u09b0\u09cd\u09ac \u09ae\u09c7\u09a6\u09bf\u09a8\u09c0\u09aa\u09c1\u09b0 \u099c\u09c7\u09b2\u09be'),
 'Howrah': ('Howrah District', '\u09b9\u09be\u0993\u09dc\u09be \u099c\u09c7\u09b2\u09be'),
 'Kolkata': ('Kolkata', '\u0995\u09b2\u0995\u09be\u09a4\u09be'),
 'Hooghly': ('Hooghly District', '\u09b9\u09c1\u0997\u09b2\u09bf \u099c\u09c7\u09b2\u09be'),
 'Nadia': ('Nadia District', '\u09a8\u09a6\u09c0\u09af\u09bc\u09be \u099c\u09c7\u09b2\u09be'),
 'Birbhum': ('Birbhum District', '\u09ac\u09c0\u09b0\u09ad\u09c2\u09ae \u099c\u09c7\u09b2\u09be'),
 'Murshidabad': ('Murshidabad District', '\u09ae\u09c1\u09b0\u09b6\u09bf\u09a6\u09be\u09ac\u09be\u09a6 \u099c\u09c7\u09b2\u09be'),
 'Cooch Behar': ('Cooch Behar District', '\u0995\u09cb\u099a\u09ac\u09bf\u09b9\u09be\u09b0 \u099c\u09c7\u09b2\u09be'),
 'Alipurduar': ('Alipurduar District', '\u0986\u09b2\u09bf\u09aa\u09c1\u09b0\u09a6\u09c1\u09af\u09bc\u09be\u09b0 \u099c\u09c7\u09b2\u09be'),
 'Jharkhand': ('Jharkhand (outside WB)', '\u099d\u09be\u09dc\u0996\u09a3\u09cd\u09a1'),
 'Odisha': ('Odisha (outside WB)', '\u0993\u09a1\u09bf\u09b6\u09be'),
 'Other': ('More Places', '\u0986\u09b0\u0993 \u099c\u09be\u09af\u09bc\u0997\u09be'),
}
'''
rep("# ---------------------------------------------------------------------------\n# helpers",
    DISTRICTS + "\n# ---------------------------------------------------------------------------\n# helpers")

# ------------------------------------------------------- B. fake regn hide
rep("""            if not regn and rest.strip():
                regn = rest.split()[0]""",
    """            if not regn and rest.strip():
                regn = rest.split()[0]
    # 'govtb8'-style codes are internal source IDs, not real registrations
    if regn and re.match(r'^govt?b?[0-9]+$', regn.strip(), re.I):
        regn = ''
    if regn:
        regn = regn.strip().upper()""")

# ------------------------------------------------- C. merge only safe dupes
rep("""        if row is None:
            out.append((key, cur))
        else:
            r = row[1]
            if r['dep'] is None: r['dep'], r['dep_raw'] = cur['dep'], cur['dep_raw']
            if r['arr'] is None: r['arr'], r['arr_raw'] = cur['arr'], cur['arr_raw']
            if not r['type']: r['type'] = cur['type']
            if not r['stops']: r['stops'] = cur['stops']""",
    """        if row is None:
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
                out.append((key, cur))""")

# ------------------------------------------------------------- D. FAQ counts
rep("""    faqs_en.append((f'How many buses run from {o} to {t}?',
                    f'Around {n} bus services operate between {o} and {t} daily, including both directions.'
                    + (f' Major operators: {", ".join(ops[:4])}.' if ops else '')))""",
    """    g = len(groups[tuple(sorted([o, t]))])
    n_word = f'{n} bus' if n == 1 else f'{n} buses'
    faqs_en.append((f'How many buses run from {o} to {t}?',
                    f'{n_word.capitalize()} run directly from {o} to {t} each day; counting both directions, '
                    f'{g} bus services connect the two places.'
                    + (f' Major operators: {", ".join(ops[:4])}.' if ops else '')))""")

rep("দিনে প্রায় {bnum(n)}টি বাস {bo or o}–{bt_ or t} রুটে চলে।",
    "সরাসরি {bnum(n)}টি বাস {bo or o} থেকে {bt_ or t} চলে; দুই দিকে মিলিয়ে মোট {bnum(g)}টি।")

# ------------------------------------------------------------- E. og:image
rep('''<meta name="twitter:card" content="summary">''',
    '''<meta name="twitter:card" content="summary">
<meta property="og:image" content="{BASE}/og-image.png">
<meta name="twitter:image" content="{BASE}/og-image.png">''')

# --------------------------------------------- F. stat label (direct buses)
stats_old = """<div class="num">{n}</div><div class="label">{lbl('Buses', 'টি বাস')}</div></div>
<div class="stat" role="listitem"><div class="num">{lbl(q_first"""
stats_new = """<div class="num">{n}</div><div class="label">{lbl('Direct buses', 'সরাসরি বাস')}</div></div>
<div class="stat" role="listitem"><div class="num">{lbl(q_first"""
rep(stats_old, stats_new)

open(P, 'w', encoding='utf-8').write(src)
print('patch 1 applied OK')
