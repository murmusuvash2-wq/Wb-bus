#!/usr/bin/env python3
"""Redesign bus-time-table/index.html: district-wise grouped, searchable,
compact pill links instead of a flat 800KB link dump. Idempotent.

Runs AFTER gen_seo_pages.py. Reads the generated index, extracts every route
link (href, origin -> destination, bus count), maps the origin hub to a WB
district, and rebuilds the page with:
  - proper H1 + intro (SEO)
  - live search box (client-side filter)
  - district jump chips
  - district sections (H2) with hub groups (H3)
  - compact CSS-class pills (~75% smaller HTML)
All links stay crawlable (in DOM, not JS-rendered).
"""

import re
import html as _html

INDEX_PATH = 'bus-time-table/index.html'
BASE = 'https://wb-bus.vercel.app'

MARKER = '<!-- redesigned-index-v1 -->'

# ---------------- district mapping ----------------
DISTRICTS = {
    # Kolkata (KMC core + city)
    'esplanade': 'Kolkata', 'kolkata': 'Kolkata', 'babughat': 'Kolkata',
    'bbd bag': 'Kolkata', 'rajabazar': 'Kolkata', 'shyambazar': 'Kolkata',
    'ahiritola': 'Kolkata', 'bagbazar': 'Kolkata', 'park circus': 'Kolkata',
    'golf green': 'Kolkata', 'alipore zoo': 'Kolkata', 'sealdah': 'Kolkata',
    'park street': 'Kolkata', 'rashbehari': 'Kolkata', 'golpark': 'Kolkata',
    'high court': 'Kolkata', 'rabindra sadan': 'Kolkata', 'chetla park': 'Kolkata',
    'kankurgachi': 'Kolkata', 'phoolbagan': 'Kolkata', 'belgachia': 'Kolkata',
    'cossipore': 'Kolkata', 'tangra': 'Kolkata', 'topsia': 'Kolkata',
    'picnic garden': 'Kolkata', 'jodhpur park': 'Kolkata', 'ruby': 'Kolkata',
    'mukundapur': 'Kolkata', 'anandapur': 'Kolkata', 'science city': 'Kolkata',
    'garh bhowanipore': 'Kolkata', 'ballygunge station': 'Kolkata',
    'aliah university': 'Kolkata', 'uttar panchannagram': 'Kolkata',
    'new alipore': 'Kolkata', 'kamal talkies': 'Kolkata', 'vip bazar': 'Kolkata',
    'kasba rathtala': 'Kolkata', 'bansdroni': 'Kolkata', 'kudghat': 'Kolkata',
    'tollygunge': 'Kolkata', 'jadavpur 8b': 'Kolkata', 'jadavpore': 'Kolkata',
    'baghajatin': 'Kolkata', 'mahamayatala': 'Kolkata', 'nayabad': 'Kolkata',
    'patuli': 'Kolkata', 'dhakuria': 'Kolkata', 'behala 14 no': 'Kolkata',
    'behala chowrasta': 'Kolkata', 'behala airport': 'Kolkata',
    'thakurpukur': 'Kolkata', 'metiabruz': 'Kolkata', 'sarsuna': 'Kolkata',
    'garia': 'Kolkata', 'camac street': 'Kolkata',
    # North 24 Parganas
    'barasat': 'North 24 Parganas', 'karunamoyee': 'North 24 Parganas',
    'saltlake': 'North 24 Parganas', 'sector v': 'North 24 Parganas',
    'newtown': 'North 24 Parganas', 'dunlop': 'North 24 Parganas',
    'ultadanga': 'North 24 Parganas', 'dumdum': 'North 24 Parganas',
    'birati': 'North 24 Parganas', 'baguiati': 'North 24 Parganas',
    'bangur avenue': 'North 24 Parganas', 'nager bazar': 'North 24 Parganas',
    'madhyamgram': 'North 24 Parganas', 'habra': 'North 24 Parganas',
    'basirhat': 'North 24 Parganas', 'bongaon': 'North 24 Parganas',
    'baduria': 'North 24 Parganas', 'barrackpore': 'North 24 Parganas',
    'kanchrapara': 'North 24 Parganas', 'naihati': 'North 24 Parganas',
    'khardaha': 'North 24 Parganas', 'sodepur': 'North 24 Parganas',
    'belgharia': 'North 24 Parganas', 'belghoria': 'North 24 Parganas',
    'agarpara': 'North 24 Parganas', 'kamarhati': 'North 24 Parganas',
    'laketown': 'North 24 Parganas', 'lake town': 'North 24 Parganas',
    'sinthi': 'North 24 Parganas', 'derozio college': 'North 24 Parganas',
    'ghatakpukur': 'North 24 Parganas', 'rajarhat': 'North 24 Parganas',
    'chingrighata': 'North 24 Parganas', 'ecospace': 'North 24 Parganas',
    'unitech': 'North 24 Parganas', 'technopolis': 'North 24 Parganas',
    'amity university': 'North 24 Parganas', 'aquatica': 'North 24 Parganas',
    'greenfield city': 'North 24 Parganas', 'hasnabad': 'North 24 Parganas',
    'hemnagar': 'North 24 Parganas', 'taki': 'North 24 Parganas',
    'sohai bazar': 'North 24 Parganas', 'nazat': 'North 24 Parganas',
    'haroa': 'North 24 Parganas', 'bibirhat': 'North 24 Parganas',
    'berachampa': 'North 24 Parganas', 'ariadaha': 'North 24 Parganas',
    'hatiara': 'North 24 Parganas', 'sajirhat': 'North 24 Parganas',
    'nimta bazar': 'North 24 Parganas', 'new barrackpore': 'North 24 Parganas',
    'gouripur': 'North 24 Parganas', 'birati tantkal': 'North 24 Parganas',
    # South 24 Parganas
    'baruipur': 'South 24 Parganas', 'sonarpur': 'South 24 Parganas',
    'kamalgazi': 'South 24 Parganas', 'amtala': 'South 24 Parganas',
    'bakkhali': 'South 24 Parganas', 'diamond harbour': 'South 24 Parganas',
    'diamond': 'South 24 Parganas', 'kakdwip': 'South 24 Parganas',
    'gangasagar': 'South 24 Parganas', 'kachuberia': 'South 24 Parganas',
    'namkhana': 'South 24 Parganas', 'canning': 'South 24 Parganas',
    'joynagar': 'South 24 Parganas', 'bhangore': 'South 24 Parganas',
    'basanti': 'South 24 Parganas', 'raidighi': 'South 24 Parganas',
    'patharpratima': 'South 24 Parganas', 'falta': 'South 24 Parganas',
    'raichak': 'South 24 Parganas', 'maheshtala': 'South 24 Parganas',
    'harinavi': 'South 24 Parganas', 'nimpith': 'South 24 Parganas',
    'jibantala': 'South 24 Parganas', 'lakshmikantapur': 'South 24 Parganas',
    'mandirtala': 'South 24 Parganas', 'jharkhali': 'South 24 Parganas',
    'chunakhali': 'South 24 Parganas', 'sonakhali': 'South 24 Parganas',
    'bhebia': 'South 24 Parganas', 'ramganga': 'South 24 Parganas',
    'usthi': 'South 24 Parganas', 'nainan': 'South 24 Parganas',
    'shibrampur': 'South 24 Parganas', 'dostipur': 'South 24 Parganas',
    'balaipanda': 'South 24 Parganas', 'dakghar': 'South 24 Parganas',
    'kanmari bazar': 'South 24 Parganas', 'chaital ghat': 'South 24 Parganas',
    'kushdwip': 'South 24 Parganas', 'aushbali': 'South 24 Parganas',
    'sabaldaha': 'South 24 Parganas', 'kaijuri bazar': 'South 24 Parganas',
    'sahararhat': 'South 24 Parganas', 'kanchkol': 'South 24 Parganas',
    'langolpota': 'South 24 Parganas', 'patharghata': 'South 24 Parganas',
    'maipith': 'South 24 Parganas', 'lebukhali': 'South 24 Parganas',
    'taranipur': 'South 24 Parganas', 'malancha': 'South 24 Parganas',
    'kukrahati': 'Howrah', 'badartala': 'South 24 Parganas',
    'bakultala': 'South 24 Parganas', 'sitalia': 'South 24 Parganas',
    # Howrah
    'howrah': 'Howrah', 'nabanna': 'Howrah', 'santragachi': 'Howrah',
    'bagnan': 'Howrah', 'uluberia': 'Howrah', 'domjur': 'Howrah',
    'sankrail': 'Howrah', 'andul': 'Howrah', 'shalimar': 'Howrah',
    'mourigram': 'Howrah', 'tikiapara': 'Howrah', 'salkia': 'Howrah',
    'ramrajatala': 'Howrah', 'batanagar': 'Howrah', 'bally': 'Howrah',
    'dhulagarh': 'Howrah', 'birshibpur': 'Howrah', 'panchla': 'Howrah',
    'jagatballavpur': 'Howrah', 'jangipara': 'Howrah', 'bhattanagar': 'Howrah',
    'dasnagar': 'Howrah', 'kona': 'Howrah', 'shibpur': 'Howrah',
    'ballyhalt': 'Howrah', 'ballykhal': 'Howrah', 'bargachia': 'Howrah',
    'rajchandrapur': 'Howrah', 'shyampur': 'Howrah', 'ranihati': 'Howrah',
    'jamirgachi': 'Howrah', 'kulgachia': 'Howrah', 'raskundu': 'Howrah',
    'mourigram railway': 'Howrah', 'sankrail railway': 'Howrah',
    # Hooghly
    'serampore': 'Hooghly', 'chinsurah': 'Hooghly', 'chuchura': 'Hooghly',
    'tarakeswar': 'Hooghly', 'tarakeshwar': 'Hooghly', 'arambagh': 'Hooghly',
    'arambag': 'Hooghly', 'haripal': 'Hooghly', 'pandua': 'Hooghly',
    'jirat': 'Hooghly', 'gurap': 'Hooghly', 'muchighata': 'Hooghly',
    'dasghara': 'Hooghly', 'chanditala': 'Hooghly', 'kamarpukur': 'Hooghly',
    'salap': 'Hooghly', 'rajbalhat': 'Hooghly', 'baburhat': 'Hooghly',
    'jagardanga': 'Hooghly', 'bali': 'Hooghly',
    # Purba Bardhaman
    'bardhaman': 'Purba Bardhaman', 'barddhaman': 'Purba Bardhaman',
    'burdwan': 'Purba Bardhaman', 'kalna': 'Purba Bardhaman',
    'katwa': 'Purba Bardhaman', 'ketugram': 'Purba Bardhaman',
    'guskara': 'Purba Bardhaman', 'dainhat': 'Purba Bardhaman',
    'maldanga': 'Purba Bardhaman', 'rasulpur': 'Purba Bardhaman',
    'madanmohanpur': 'Purba Bardhaman', 'barshal': 'Purba Bardhaman',
    'dhaldanga': 'Purba Bardhaman', 'tatarpur': 'Purba Bardhaman',
    # Paschim Bardhaman
    'asansol': 'Paschim Bardhaman', 'durgapur': 'Paschim Bardhaman',
    'raniganj': 'Paschim Bardhaman', 'barakar': 'Paschim Bardhaman',
    'jamuria': 'Paschim Bardhaman', 'chittaranjan': 'Paschim Bardhaman',
    'ukhra': 'Paschim Bardhaman', 'pandaveswar': 'Paschim Bardhaman',
    'rupnarayanpur': 'Paschim Bardhaman', 'harishpur': 'Paschim Bardhaman',
    'jamtoria': 'Paschim Bardhaman', 'chandankyari': 'Paschim Bardhaman',
    'beri gopalpur': 'Paschim Bardhaman', 'chunavati': 'Paschim Bardhaman',
    # Bankura
    'bankura': 'Bankura', 'bishnupur': 'Bankura', 'bisunupur': 'Bankura',
    'sonamukhi': 'Bankura', 'khatra': 'Bankura', 'patrasayer': 'Bankura',
    'joypur': 'Bankura', 'simlapal': 'Bankura', 'ranibandh': 'Bankura',
    'kenjakura': 'Bankura', 'fulkusma': 'Bankura', 'sarenga': 'Bankura',
    'chendapathar': 'Bankura', 'bhutsahar': 'Bankura', 'guniada': 'Bankura',
    'lakshmisagar': 'Bankura', 'daroka': 'Bankura', 'balgona': 'Bankura',
    'kuli': 'Bankura', 'shyamsundar': 'Bankura', 'indus': 'Bankura',
    # Purulia
    'purulia': 'Purulia', 'manbazar': 'Purulia', 'bandwan': 'Purulia',
    'bandowan': 'Purulia', 'baghmundi': 'Purulia', 'ajodhya': 'Purulia',
    'jhalda': 'Purulia', 'balarampur': 'Purulia', 'barabazar': 'Purulia',
    'raipur': 'Purulia', 'chelyama': 'Purulia', 'molian': 'Purulia',
    # Jhargram
    'jhargram': 'Jhargram', 'belpahari': 'Jhargram', 'lalgarh': 'Jhargram',
    'silda': 'Jhargram', 'binpur': 'Jhargram', 'shikarpur': 'Jhargram',
    'shikharpur': 'Jhargram', 'chakta': 'Jhargram',
    # Paschim Medinipur
    'kharagpur': 'Paschim Medinipur', 'medinipur': 'Paschim Medinipur',
    'midnapore': 'Paschim Medinipur', 'midnapur': 'Paschim Medinipur',
    'garhbeta': 'Paschim Medinipur', 'chandrakona': 'Paschim Medinipur',
    'ghatal': 'Paschim Medinipur', 'goaltore': 'Paschim Medinipur',
    'khirpai': 'Paschim Medinipur', 'keshargarh': 'Paschim Medinipur',
    'godapiasal': 'Paschim Medinipur', 'dantan': 'Paschim Medinipur',
    'gangadharpur': 'Paschim Medinipur', 'hoomgarh': 'Paschim Medinipur',
    # Purba Medinipur
    'tamluk': 'Purba Medinipur', 'haldia': 'Purba Medinipur',
    'contai': 'Purba Medinipur', 'digha': 'Purba Medinipur',
    'mecheda': 'Purba Medinipur', 'panskura': 'Purba Medinipur',
    'panshkura': 'Purba Medinipur', 'egra': 'Purba Medinipur',
    'ramnagar': 'Purba Medinipur', 'nandigram': 'Purba Medinipur',
    'moyna': 'Purba Medinipur', 'bhagabanpur': 'Purba Medinipur',
    'sonachura': 'Purba Medinipur', 'boga': 'Purba Medinipur',
    # Nadia
    'krishnanagar': 'Nadia', 'ranaghat': 'Nadia', 'kalyani': 'Nadia',
    'nabadwip': 'Nadia', 'karimpur': 'Nadia', 'gayeshpur': 'Nadia',
    'palashipara': 'Nadia', 'duttaphulia': 'Nadia', 'krishnabati': 'Nadia',
    # Murshidabad
    'berhampore': 'Murshidabad', 'baharampur': 'Murshidabad',
    'kandi': 'Murshidabad', 'jangipur': 'Murshidabad', 'dhulian': 'Murshidabad',
    'dhuliyan': 'Murshidabad', 'lalgola': 'Murshidabad', 'domkal': 'Murshidabad',
    'khagraghat': 'Murshidabad', 'sagarpara': 'Murshidabad',
    'panchthupi': 'Murshidabad',
    # Malda
    'malda': 'Malda', 'gazole': 'Malda', 'chanchal': 'Malda',
    # Uttar Dinajpur
    'raiganj': 'Uttar Dinajpur', 'islampur': 'Uttar Dinajpur',
    'dalkhola': 'Uttar Dinajpur',
    # Dakshin Dinajpur
    'balurghat': 'Dakshin Dinajpur', 'gangarampur': 'Dakshin Dinajpur',
    'tapan': 'Dakshin Dinajpur',
    # Darjeeling
    'siliguri': 'Darjeeling', 'darjeeling': 'Darjeeling',
    'kurseong': 'Darjeeling', 'kharibari': 'Darjeeling',
    # Jalpaiguri
    'jalpaiguri': 'Jalpaiguri', 'moynaguri': 'Jalpaiguri',
    'dhupguri': 'Jalpaiguri', 'malbazar': 'Jalpaiguri',
    'mainaguri': 'Jalpaiguri',
    # Alipurduar
    'alipurduar': 'Alipurduar',
    # Cooch Behar
    'cooch behar': 'Cooch Behar', 'mathabhanga': 'Cooch Behar',
    'dinhata': 'Cooch Behar', 'tufanganj': 'Cooch Behar',
    # Outside West Bengal
    'dhanbad': 'Outside West Bengal', 'ranchi': 'Outside West Bengal',
    'tatanagar': 'Outside West Bengal', 'delhi': 'Outside West Bengal',
    'bangalore': 'Outside West Bengal', 'bhubaneswar': 'Outside West Bengal',
    'sasaram': 'Outside West Bengal', 'gorakhpur': 'Outside West Bengal',
    'lucknow': 'Outside West Bengal', 'aurangabad bihar': 'Outside West Bengal',
    'gopalganj bihar': 'Outside West Bengal', 'puri': 'Outside West Bengal',
    # Birbhum (was missing entirely!)
    'bolpur': 'Birbhum', 'suri': 'Birbhum', 'santiniketan': 'Birbhum',
    'rampurhat': 'Birbhum', 'tarapith': 'Birbhum', 'sainthia': 'Birbhum',
    'labhpur': 'Birbhum', 'kirnahar': 'Birbhum', 'nanur': 'Birbhum',
    'illambazar': 'Birbhum', 'patharchapuri': 'Birbhum', 'moham': 'Birbhum',
    # extra Howrah
    'amta': 'Howrah', 'udaynarayanpur': 'Howrah', 'gadiara': 'Howrah',
    'belurmath': 'Howrah', 'dumurjola': 'Howrah', 'bankra bazar': 'Howrah',
    'kadamtala': 'Howrah',
    # extra North 24 Parganas
    'dakshineswar': 'North 24 Parganas', 'airport': 'North 24 Parganas',
    'bonhooghly': 'North 24 Parganas', 'nahata': 'North 24 Parganas',
    'rahara': 'North 24 Parganas', 'noapara': 'North 24 Parganas',
    'fatikgachi': 'North 24 Parganas', 'mohishpota': 'North 24 Parganas',
    'chakla': 'North 24 Parganas', 'bichali ghat': 'North 24 Parganas',
    'samshernagar': 'North 24 Parganas', 'mahishbathan': 'North 24 Parganas',
    'shapoorji': 'North 24 Parganas', 'dumdum cantonment': 'North 24 Parganas',
    'dumdum canton': 'North 24 Parganas',
    # extra South 24 Parganas
    'burul': 'South 24 Parganas', 'noorpur': 'South 24 Parganas',
    'dhamakhali': 'South 24 Parganas', 'julpia': 'South 24 Parganas',
    'baisnabghata': 'South 24 Parganas', 'akra': 'South 24 Parganas',
    'itaberia': 'South 24 Parganas', 'gadkhali': 'South 24 Parganas',
    'kantakhali': 'South 24 Parganas', 'pailan': 'South 24 Parganas',
    'sapuipara': 'South 24 Parganas', 'shirakole': 'South 24 Parganas',
    'polerhat': 'South 24 Parganas', 'dihibhursut': 'South 24 Parganas',
    'choto finga': 'South 24 Parganas', 'solpatta': 'South 24 Parganas',
    'garchakraberia': 'South 24 Parganas', 'old dakghar': 'South 24 Parganas',
    'nabatkati': 'South 24 Parganas', 'birlapur': 'South 24 Parganas',
    # extra Kolkata
    'parnasree': 'Kolkata', 'sakher bazar': 'Kolkata', 'taratala': 'Kolkata',
    'kidderpore': 'Kolkata', 'barisha': 'Kolkata', 'haridevpur': 'Kolkata',
    'teghoria': 'Kolkata', 'beleghata': 'Kolkata', 'leather complex': 'Kolkata',
    'boyra': 'Kolkata', 'garhbhowanipur': 'Kolkata', 'danesh shaikh lane': 'Kolkata',
    'joka': 'Kolkata', 'metiabruz ssp': 'Kolkata', 'behala': 'Kolkata',
    # extra Hooghly
    'tarkeshwar': 'Hooghly', 'dankuni': 'Hooghly', 'furfura sharif': 'Hooghly',
    'malipanchghara': 'Hooghly',
    # extra Paschim Bardhaman
    'benachity': 'Paschim Bardhaman',
    # extra Paschim Medinipur
    'hijli': 'Paschim Medinipur', 'kandra': 'Purba Medinipur',
    'pancharul': 'Purba Medinipur', 'uttar ramnagar': 'Purba Medinipur',
    # extra Bankura
    'jayrambati': 'Bankura', 'kotulpur': 'Bankura', 'ramsagar': 'Bankura',
    'sehara bazar': 'Bankura', 'jhantipahari': 'Bankura',
    # extra Murshidabad
    'alampur': 'Murshidabad', 'salar': 'Murshidabad', 'shibgunge': 'Murshidabad',
    # extra Nadia
    'mayapur': 'Nadia', 'chapadanga': 'Nadia', 'jaguli': 'Nadia',
    'goyespur': 'Nadia', 'shimuliyahat': 'Nadia',
    # extra Purulia
    'kashipur': 'Purulia', 'nagar': 'Purulia',
    # extra Jhargram
    'baharagora': 'Jhargram',
}


DISTRICT_ORDER = [
    'Kolkata', 'North 24 Parganas', 'South 24 Parganas', 'Howrah', 'Hooghly',
    'Purba Bardhaman', 'Paschim Bardhaman', 'Birbhum', 'Bankura', 'Purulia',
    'Jhargram', 'Paschim Medinipur', 'Purba Medinipur', 'Nadia', 'Murshidabad',
    'Malda', 'Uttar Dinajpur', 'Dakshin Dinajpur', 'Darjeeling', 'Jalpaiguri',
    'Alipurduar', 'Cooch Behar', 'Other Places', 'Outside West Bengal',
]

def find_district(hub_name):
    """Map a hub name to its district. Exact prefix match, then exact dict hit."""
    h = hub_name.strip().lower()
    if not h:
        return 'Other Places'
    # exact hit
    if h in DISTRICTS:
        return DISTRICTS[h]
    # prefix match — longest town name that the hub starts with
    best = None
    for town, dist in DISTRICTS.items():
        if h.startswith(town) and (best is None or len(town) > len(best[0])):
            best = (town, dist)
    if best:
        return best[1]
    return 'Other Places'


def slugify(s):
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s or 'x'


def main():
    src = open(INDEX_PATH, encoding='utf-8').read()
    if MARKER in src:
        print('redesign_seo_index: already applied')
        return

    # ---- extract all route links from the generated page ----
    route_re = re.compile(
        r'<a href="([a-z0-9\-]+-to-[a-z0-9\-]+\.html)"[^>]*>\s*<span>\s*(.+?)\s*</span>\s*'
        r'<span[^>]*>\s*(\d+)\s*buses\s*</span>', re.DOTALL)
    routes = []  # (href, label, count)
    for href, label, cnt in route_re.findall(src):
        label = re.sub(r'<[^>]+>', '', label).strip()
        cnt = int(cnt)
        origin = label.split('\u2192')[0].strip()  # before arrow
        routes.append((href, label, cnt, origin))

    if len(routes) < 100:
        raise SystemExit(f'ERROR: only {len(routes)} routes parsed - aborting')

    # total buses for stats
    total_buses = sum(r[2] for r in routes)

    # ---- group: district -> hub -> [(href, label, cnt)] ----
    by_district = {}
    for href, label, cnt, origin in routes:
        d = find_district(origin)
        by_district.setdefault(d, {}).setdefault(origin, []).append((href, label, cnt))

    # ---- build sections ----
    sections = []
    chips = []
    for d in DISTRICT_ORDER:
        if d not in by_district:
            continue
        hubs = by_district[d]
        n_routes = sum(len(v) for v in hubs.values())
        did = 'd-' + slugify(d)
        chips.append(
            '<a class="chip" href="#' + did + '">' + _html.escape(d)
            + '<b>' + str(n_routes) + '</b></a>')
        # hubs sorted by route count desc, then name
        hub_items = sorted(hubs.items(), key=lambda kv: (-sum(x[2] for x in kv[1]), kv[0]))
        hub_html = []
        for hub, rl in hub_items:
            rl_sorted = sorted(rl, key=lambda x: x[1].lower())
            n_buses = sum(x[2] for x in rl)
            pills = ''.join(
                '<a class="rt" href="' + h + '">' + _html.escape(lab)
                + '<span>' + str(c) + '</span></a>'
                for h, lab, c in rl_sorted)
            hub_html.append(
                '<div class="hub"><h3>' + _html.escape(hub)
                + '<span>' + str(len(rl)) + ' route' + ('s' if len(rl) > 1 else '')
                + ' \u00b7 ' + str(n_buses) + ' buses</span></h3>'
                '<div class="rg">' + pills + '</div></div>')
        sections.append(
            '<section class="dist" id="' + did + '"><h2>' + _html.escape(d)
            + '<span>' + str(n_routes) + ' routes</span></h2>'
            + ''.join(hub_html) + '</section>')

    n_districts = len([d for d in DISTRICT_ORDER if d in by_district])

    # ---- page ----
    page = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>West Bengal Bus Time Table — All Routes by District | BusJatri</title>
<meta name="description" content="Browse __NR__ bus routes across West Bengal by district — Kolkata, Howrah, Bardhaman, Medinipur and more. Timings, operators and stoppages on BusJatri.">
<link rel="canonical" href="__BASE__/bus-time-table/">
<meta property="og:title" content="West Bengal Bus Time Table — All Routes | BusJatri">
<meta property="og:description" content="__NR__ bus routes across West Bengal, grouped by district. Search timings, operators and stoppages.">
<meta property="og:type" content="website">
<meta property="og:url" content="__BASE__/bus-time-table/">
<meta property="og:image" content="__BASE__/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#b8791f">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b8791f' stroke-width='2'%3E%3Cpath d='M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10'/%3E%3Cpath d='M4 16h16'/%3E%3C/svg%3E">
<link rel="stylesheet" href="../css/style.css">
<style>
.wrap{max-width:1080px;margin:0 auto;padding:22px 16px 48px}
.crumb{font-size:13px;color:var(--ink-dim);margin-bottom:14px}
.crumb a{color:var(--amber);text-decoration:none}
h1{font-family:var(--font-display,Georgia,serif);font-size:clamp(1.7rem,4.5vw,2.4rem);margin:0 0 6px;letter-spacing:-.5px}
.intro{color:var(--ink-dim);font-size:14.5px;margin:0 0 18px;max-width:640px}
.statrow{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px}
.stat{background:var(--panel,var(--surface-2));border:1px solid var(--border,var(--line));border-radius:10px;padding:8px 14px;font-family:var(--font-mono,monospace);font-size:13px}
.stat b{color:var(--amber);font-size:1.05rem}
.qwrap{position:sticky;top:8px;z-index:5;margin-bottom:16px}
#q{width:100%;box-sizing:border-box;padding:13px 16px;font-size:15px;border-radius:12px;border:1.5px solid var(--line-strong,var(--border));background:var(--surface,var(--panel));color:var(--ink,#211c16);outline:none}
#q:focus{border-color:var(--amber)}
.qmeta{font-size:12px;color:var(--ink-dim,#6f6653);font-family:var(--font-mono,monospace);margin:6px 2px 0}
.dnav{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 6px}
.chip{font-size:12.5px;color:var(--ink,#211c16);text-decoration:none;background:var(--panel,var(--surface-2));border:1px solid var(--border,var(--line));padding:5px 11px;border-radius:999px;transition:border-color .15s}
.chip:hover{border-color:var(--amber)}
.chip b{color:var(--amber);font-weight:600;margin-left:4px;font-size:11px}
.dist{margin-top:26px}
.dist h2{font-size:1.25rem;border-bottom:2px solid var(--border,var(--line));padding-bottom:8px;margin:0 0 4px;display:flex;justify-content:space-between;align-items:baseline}
.dist h2 span{font-size:12px;color:var(--ink-dim,#6f6653);font-family:var(--font-mono,monospace);font-weight:400}
.hub{margin-top:16px}
.hub h3{font-size:.95rem;margin:0 0 8px;color:var(--ink,#211c16)}
.hub h3 span{font-size:11px;color:var(--ink-dim,#6f6653);font-family:var(--font-mono,monospace);font-weight:400;margin-left:8px}
.rg{display:grid;grid-template-columns:repeat(auto-fill,minmax(215px,1fr));gap:6px}
.rt{display:flex;justify-content:space-between;align-items:baseline;gap:6px;font-size:13px;padding:7px 10px;border-radius:8px;background:var(--surface,var(--panel));border:1px solid var(--border,var(--line));text-decoration:none;color:var(--ink,#211c16);transition:border-color .15s}
.rt:hover{border-color:var(--amber)}
.rt span{color:var(--ink-dim,#6f6653);font-size:11px;font-family:var(--font-mono,monospace);flex:none}
#nores{display:none;text-align:center;color:var(--ink-dim,#6f6653);padding:40px 0}
footer{border-top:1px solid var(--border,var(--line));margin-top:40px;padding:18px 0 6px;font-size:13px;color:var(--ink-dim,#6f6653)}
footer a{color:var(--amber);text-decoration:none}
</style>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebSite","name":"BusJatri","url":"__BASE__"}</script>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":"__BASE__/"},{"@type":"ListItem","position":2,"name":"Bus Timetable","item":"__BASE__/bus-time-table/"}]}</script>
</head>
<body>
<header class="header"><div class="container header-inner">
<a href="../index.html" class="logo" style="text-decoration:none;color:inherit;font-family:var(--font-display,Georgia,serif);font-weight:700;font-size:1.2rem">
<svg class="icon" viewBox="0 0 24 24" style="width:1.3rem;height:1.3rem;color:var(--amber);vertical-align:-3px" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"/><path d="M4 16h16"/><path d="M6 10h12"/></svg>
Bus<span style="color:var(--amber);font-style:italic">Jatri</span></a>
</div></header>
<main class="wrap" __MARKER__>
<div class="crumb"><a href="../index.html">Home</a> / Bus Timetable</div>
<h1>West Bengal Bus Time Table</h1>
<p class="intro">Complete bus timetable for West Bengal — SBSTC, WBTC, NBSTC and private operators. __NB__ buses on __NR__ routes, grouped by district. Search any route below or open a route for full timings, stoppages and operators.</p>
<div class="statrow">
<div class="stat"><b>__NR__</b> routes</div>
<div class="stat"><b>__NB__</b> buses</div>
<div class="stat"><b>__ND__</b> districts</div>
</div>
<div class="qwrap"><input id="q" type="search" placeholder='Search route — try "kolkata to digha" or "asansol"' autocomplete="off" aria-label="Search routes">
<div class="qmeta" id="qmeta"></div></div>
<nav class="dnav" aria-label="Districts">
__CHIPS__
</nav>
<div id="nores">No routes match — try a place name like "Digha" or "Esplanade".</div>
__SECTIONS__
<footer>BusJatri — West Bengal bus timetable &middot; <a href="../index.html">Search buses</a> &middot; Not affiliated with any transport corporation</footer>
</main>
<script>
(function(){
var q=document.getElementById('q'),total=__NR__,meta=document.getElementById('qmeta');
var rts=[].slice.call(document.querySelectorAll('.rt'));
function filter(){
var t=q.value.trim().toLowerCase(),vis=0;
for(var i=0;i<rts.length;i++){var m=!t||rts[i].getAttribute('data-s').indexOf(t)>-1;
rts[i].style.display=m?'':'none';if(m)vis++;}
var hubs=[].slice.call(document.querySelectorAll('.hub'));
for(var j=0;j<hubs.length;j++){var any=false,as=hubs[j].querySelectorAll('.rt');
for(var k=0;k<as.length;k++){if(as[k].style.display!=='none'){any=true;break}}
hubs[j].style.display=any?'':'none';}
var ds=[].slice.call(document.querySelectorAll('.dist'));
for(var x=0;x<ds.length;x++){var a2=false,rs=ds[x].querySelectorAll('.rt');
for(var y=0;y<rs.length;y++){if(rs[y].style.display!=='none'){a2=true;break}}
ds[x].style.display=a2?'':'none';}
document.getElementById('nores').style.display=vis?'none':'';
meta.textContent=t?('Showing '+vis+' of '+total+' routes'):'';
}
q.addEventListener('input',filter);
})();
</script>
</body>
</html>'''

    # attach data-s attributes: rebuild sections with data-s on pills
    # (we re-generate pills here with data-s to keep filter fast)
    sections2 = []
    chips2 = []
    for d in DISTRICT_ORDER:
        if d not in by_district:
            continue
        hubs = by_district[d]
        n_routes = sum(len(v) for v in hubs.values())
        did = 'd-' + slugify(d)
        chips2.append('<a class="chip" href="#' + did + '">' + _html.escape(d) + '<b>' + str(n_routes) + '</b></a>')
        hub_items = sorted(hubs.items(), key=lambda kv: (-sum(x[2] for x in kv[1]), kv[0]))
        hub_html = []
        for hub, rl in hub_items:
            rl_sorted = sorted(rl, key=lambda x: x[1].lower())
            n_buses = sum(x[2] for x in rl)
            pills = ''.join(
                '<a class="rt" data-s="' + _html.escape(lab.lower().replace('\u2192', ' to ')) + '" href="' + h + '">'
                + _html.escape(lab) + '<span>' + str(c) + '</span></a>'
                for h, lab, c in rl_sorted)
            hub_html.append(
                '<div class="hub"><h3>' + _html.escape(hub)
                + '<span>' + str(len(rl)) + ' route' + ('s' if len(rl) > 1 else '')
                + ' \u00b7 ' + str(n_buses) + ' buses</span></h3>'
                '<div class="rg">' + pills + '</div></div>')
        sections2.append(
            '<section class="dist" id="' + did + '"><h2>' + _html.escape(d)
            + '<span>' + str(n_routes) + ' routes</span></h2>'
            + ''.join(hub_html) + '</section>')

    page = (page
            .replace('__MARKER__', MARKER)
            .replace('__BASE__', BASE)
            .replace('__NR__', str(len(routes)))
            .replace('__NB__', str(total_buses))
            .replace('__ND__', str(n_districts))
            .replace('__CHIPS__', ''.join(chips2))
            .replace('__SECTIONS__', ''.join(sections2)))

    open(INDEX_PATH, 'w', encoding='utf-8').write(page)
    print(f'redesign_seo_index: rebuilt — {len(routes)} routes, {n_districts} districts, '
          f'{len(page)//1024}KB (was {len(src)//1024}KB)')

if __name__ == '__main__':
    main()
