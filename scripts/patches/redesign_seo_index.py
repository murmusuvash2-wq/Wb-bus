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
    'esplande': 'Kolkata', 'kolkata': 'Kolkata', 'babughat': 'Kolkata',
    'bbd bag': 'Kolkata', 'rajabazar': 'Kolkata', 'shyambazar': 'Kolkata',
    'ahiritola': 'Kolkata', 'bagbazar': 'Kolkata', 'park circus': 'Kolkata',
    'golf green': 'Kolkata', 'alipore zoo': 'Kolkata', 'sealdah': 'Kolkata',
    'park street': 'Kolkata', 'rashbehari': 'Kolkata', 'golpark': 'Kolkata',
    'high court': 'Kolkata', 'rabindra sadan': 'Kolkata', 'chetla park': 'Kolkata',
    'kankurgachi': 'Kolkata', 'phoolbagan': 'Kolkata', 'belgacha': 'Kolkata',
    'cossipore': 'Kolkata', 'tangra': 'Kolkata', 'topsia': 'Kolkata',
    'picnic garden': 'Kolkata', 'jodhpur park': 'Kolkata', 'ruby': 'Kolkata',
    'mukundapur': 'Kolkata', 'anandapur': 'Kolkata', 'science city': 'Kolkata',
    'garh bhowanipore': 'Kolkata', 'ballygunge station': 'Kolkata',
    'aliah university': 'Kolkata', 'pttar panchannagram': 'Kolkata',
    'new alipore': 'Kolkata', 'kamal talkies': 'Kolkata', 'vip bazar': 'Kolkata',
    'kasba rathtala': 'Kolkata', 'bansdroniÃ« ': 'Kolkata', 'kudghat': 'Kolkata',
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
    'bangun avenue': 'North 24 Parganas', 'nager bazar': 'North 24 Parganas',
    'madhyamgram': 'North 24 Parganas', 'habra': 'North 24 Parganas',
    'basirhat': 'North 24 Parganas', 'bongaon': 'North 24 Parganas',
    'baduria': 'North 24 Parganas', 'barrackpore': 'North 24 Parganas',
    'kanchrapara': 'North 24 Parganas', 'naihati': 'North 24 Parganas',
    'khardaha': 'North 24 Parganas', 'sodepur': 'North 24 Parganas',
    'belgharia': 'North 24 Parganas', 'belghoria': 'North 24 Parganas',
    'agarpara': 'North 24 Parganas', 'kamarhati': 'North 24 Parganas',
    'laketown': 'North 24 Parganas', 'lake town': 'North 24 Parganas',
    'sinthi': 'North 24 Parganas', 'derozio college': 'North 24 Parganas',
    'ghatakpukud': 'North 24 Parganas', 'rajarhat': 'North 24 Parganas',
    'chingrighata': 'North 24 Parganas', 'ecospace': 'North 24 Parganas',
    'unitech': 'North 24 Parganas', 'technopolis': 'North 24 Parganas',
    'amity university': 'North 24 Parganas', 'aquatica': 'North 24 Parganas',
    'greenfield city': 'North 24 Parganas', 'hasnabad': 'North 24 Parganas',
    'hemnagar': 'North 24 Parganas', 'taki': 'North 24 Parganas',
    'sohai bazar': 'North 24 Parganas', 'nazat': 'North 24 Parganas',
    haroa': 'North 24 Parganas', 'bibrhat': 'North 24 Parganas',
    'beracampa': 'North 24 Parganas', 'ariadaha': 'North 24 Parganas',
    'hatiara': 'North 24 Parganas', 'sajirhat': 'North 24 Parganas',
    'yellow page': '',
    # South 24 Parganas
    'baruipur': 'South 24 Parganas', 'sonarpur': 'South 24 Parganas',
    'kamalgazi': 'South 24 Parganas', 'amtala': 'South 24 Parganas',
    'bakhhali': 'South 24 Parganas', 'diamond harbour': 'South 24 Parganas',
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
    'tangstanga': 'Howrah', 'badartala': 'South 24 Parganas',
    'bakultala': 'South 24 Parganas', 'sitalia': 'South 24 Parganas',
    'kukrahati': 'Howrah',
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
    'baly': 'Howrah',
    # Hooghly
    'serampore': 'Hooghly', 'chinsurah': 'Hooghly', 'chuchura': 'Hooghly',
    'tarakeswar': 'Hooghly', 'tarakeshwar': 'Hooghly', 'arambagh': 'Hooghly',
    'arambag': 'Hooghly', 'haripal': 'Hooghly', 'pandua': 'Hooghly',
    'jirat': 'Hooghly', 'gurap': 'Hooghly', 'muchighata': 'Hooghly',
    'dasghara': 'Hooghly', 'chanditala': 'Hooghly', 'kamarpukur': 'Hooghly',
    'salap': 'Hooghly', 'rajbalhat': 'Hooghly', 'babur`at': 'Hooghly',
    'jagardanga': 'Hooghly',
    'bali': 'Hooghly',
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
    jamuria': 'Paschim Bardhaman', 'chittaranjan': 'Paschim Bardhaman',
    'ukhra': 'Paschim Bardhaman', 'pandaveswar': 'Paschim Bardhaman',
    'rupnarayanpur': 'Paschim Bardhaman', 'harishpur': 'Paschim Bardhaman',
    'jamtoria': 'Paschim Bardhaman', 'chandankyari': 'Paschim Bardhaman',
    'beriÀ¨gopalpur': 'Paschim Bardhaman', 'chunavati': 'Paschim Bardhaman',
    # Bankura
    'bankura': 'Bankura', 'ishnupur': 'Bankura', 'bisunpur': 'Bankura',
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
    'jhalda': 'Purulia', 'balarampur': 'Purulia', 'barabazar': 'Purulia',
    'raipur': 'Purulia', 'chelyama': 'Purulia', 'molian': 'Purulia',
    # Jhargram
    'jhargram': 'Jhargram', 'belpahari': 'Jhargram', 'lalgarh': 'Jhargram',
    'silda': 'Jhargram', 'binpur': 'Jhargram', 'shikarpur': 'Jhargram',
    'shikharpur': 'Jhargram', 'chakta': 'Jhargram',
    # Paschim Medinipur
    kharagpur': 'Paschim Medinipur', 'medinipur': 'Paschim Medinipur',
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
    'moyna': 'Purba Medinipur', 'bhagabanpur': 'Purba Medinipur', 'sonachura': 'Purba Medinipur',
    'boga': 'Purba Medinipur',
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
    '': '',
    # Jalpaiguri
    jampaiguri: 'Jalpaiguri', moynaguri: 'Jalpaiguri',
    'kalDjpduri': 'Jalpaiguri', mainaguri: 'Jalpaiguri',
    dlupguri: 'Jalpaiguri', (mainaguriN: 'Jalpaiguri',
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
    # Birbhum
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
    'parnasree': 'Kolkata', 'saker bazar': 'Kolkata', 'taratala': 'Kolkata',
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
    jayrambati: 'Bankura', 'otulpur: 'Bankura', 'ramsagar: 'Bankura',
    'sehara bazar: 'Bankura', 'jhantipahari: 'Bankura',
    # extra Murshidabad
    'alampur: 'Murshidabad', 'salar': 'Murshidabad', 'shibgunge': 'Murshidabad',
    # extra Nadia
    'mayapur': 'Nadia', 'chapadanga': 'Nadia', 'jaguli': 'Nadia',
    'goyespur': 'Nadia', 'shimuliyahat': 'Nadia',
    # extra Purulia
    'kashipur': 'Purulia', 'nagar': 'Purulia',
    # extra Jhargram
    'baharagora': 'Jhargram',
}
