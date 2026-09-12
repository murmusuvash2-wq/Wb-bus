🚌 BusJatri — West Bengal Bus Timetable

বাংলা · English · Simple · Fast · Open Data

BusJatri is a free, lightweight bus timetable and route-discovery platform focused on West Bengal, India.

Find buses, timings, routes, stoppages and nearby railway stations — all from one simple interface.

«বাস খুঁজুন। রুট জানুন। সময় মিলিয়ে নিন।»

---

✨ What is BusJatri?

Travelling by bus in West Bengal can be surprisingly difficult when route information is scattered across different sources.

BusJatri brings that information together into a searchable, mobile-friendly interface.

You can:

- 🚌 Search for buses
- 🕐 Check departure timings
- 📍 Explore complete stoppage lists
- 🔎 Search routes and destinations
- 🚉 See the nearest railway station for a bus stop
- 📏 See the approximate distance to that railway station
- 🗺️ Explore routes through generated route pages
- 🌐 Use Bengali and English place names
- 📱 Use the site comfortably on mobile devices

---

🚉 Railway Station Proximity

One of BusJatri's useful features is connecting bus stoppages with nearby railway stations.

For a bus stop, BusJatri attempts to determine:

Bus Stop
   ↓
Geographic location
   ↓
Nearest Railway Station
   ↓
Approximate distance

For example:

📍 Bus Stop
      ↓
🚉 Nearest Railway Station
      ↓
📏 ~2.4 km

The distance is calculated using geographic coordinates and represents approximate straight-line distance, not road or walking distance.

Accuracy philosophy

The goal is not to pretend that automatically geocoded data is perfect.

BusJatri prioritizes:

- multiple candidate locations
- route context
- neighbouring stoppages
- origin/destination context
- geographic consistency
- sensible West Bengal geographic boundaries
- deterministic validation

The system is designed to reject suspicious matches rather than confidently display a wrong location.

---

🧭 Route-Aware Data

A major part of BusJatri is not simply storing bus names and times.

The project treats a bus route as a sequence:

Origin
  ↓
Stop 1
  ↓
Stop 2
  ↓
Stop 3
  ↓
...
  ↓
Destination

This route structure can be used to validate geographic information.

For example, if a stop appears between two known locations, its automatically selected coordinates should make geographic sense relative to the rest of the route.

This is especially important because many places in West Bengal have:

- similar names
- spelling variations
- Bengali/English transliteration differences
- multiple localities with the same name
- bus-stop names that are not official geographic names

---

🔍 Search

BusJatri is designed around quick route discovery.

You can search using place names such as:

Durgapur
Asansol
Kolkata
Bardhaman
Siliguri
Malda
Bankura
Purulia

and Bengali place names where supported.

The application maintains searchable indexes for:

- buses
- routes
- stops

so that users can discover relevant services without navigating complicated menus.

---

🏗️ How It Works

BusJatri is intentionally built as a lightweight static web application.

There is no requirement for a large backend just to display timetable data.

High-level architecture

             DATA SOURCES
                  │
                  ▼
        ┌───────────────────┐
        │ Data Collection   │
        │ & Import Scripts  │
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────┐
        │ Validation &      │
        │ Data Processing   │
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────┐
        │ busjatri_data.json│
        └─────────┬─────────┘
                  │
          ┌───────┴────────┐
          ▼                ▼
     Web Application    SEO Pages
          │                │
          └───────┬────────┘
                  ▼
              BusJatri

---

📦 Data Pipeline

The repository contains scripts for collecting, rebuilding and enriching the timetable dataset.

Main components

data/
├── busjatri_data.json
├── sbstc_routes.json
└── stop_coords.json

scripts/
├── scrape_bussathi.py
├── rebuild_data.py
├── import_sbstc.py
├── enrich_wbtc.py
├── add_railway_stations.py
└── gen_seo_pages.py

Data flow

Bussathi data
     │
     ▼
Scraper
     │
     ▼
Data rebuild
     │
     ├──── SBSTC import
     │
     ├──── WBTC enrichment
     │
     └──── Railway station enrichment
     │
     ▼
busjatri_data.json
     │
     ▼
Web App + SEO route pages

---

🏛️ Government Transport Data

BusJatri also has dedicated processing for government transport information.

The pipeline supports:

SBSTC

South Bengal State Transport Corporation

Data is imported and converted into the common BusJatri data structure.

WBTC

West Bengal Transport Corporation

Route information is processed and used to enrich the unified dataset.

This allows different transport data sources to be presented through a common interface.

---

🤖 Automatic Updates

BusJatri uses GitHub Actions for automated data processing.

The update pipeline can:

1. collect fresh bus information
2. validate the collected data
3. rebuild the unified dataset
4. import government transport data
5. enrich routes
6. attach railway-station information
7. regenerate SEO pages
8. update the sitemap
9. commit the resulting data

The intention is to reduce manual maintenance and keep the public dataset refreshed.

---

🗺️ SEO Route Pages

BusJatri generates dedicated pages for route combinations.

Conceptually:

Origin → Destination

becomes a searchable page containing:

- bus services
- timings
- operators
- stoppages
- route information
- structured metadata

This helps users who search Google for a very specific journey such as:

Durgapur to Kolkata bus
Asansol to Durgapur bus
Bardhaman to Kolkata bus

instead of requiring every visitor to start from the homepage.

---

📱 Design Philosophy

BusJatri follows a simple principle:

«The user should find the bus before they have time to get confused.»

The interface therefore focuses on:

⚡ Speed

Static files and client-side rendering keep the application lightweight.

📱 Mobile-first usability

Most bus searches happen while travelling, so the interface should work well on phones.

🧹 Low visual noise

Timetable information is more important than decorative UI.

🌐 Bengali + English

West Bengal transport information should be accessible to people searching in either language.

---

🛠️ Technology

BusJatri intentionally avoids unnecessary framework complexity.

Frontend

- HTML
- CSS
- JavaScript
- Local JSON data

Data processing

- Python
- JSON
- GitHub Actions

External data / processing

- Public transport data sources
- Railway station geographic data
- Geocoding services

Deployment

The application is designed to work as a static website and can be deployed through modern static hosting platforms.

---

📁 Repository Structure

Wb-bus/
│
├── index.html
│
├── css/
│   └── style.css
│
├── js/
│   └── app.js
│
├── data/
│   ├── busjatri_data.json
│   ├── sbstc_routes.json
│   └── stop_coords.json
│
├── bus-time-table/
│   └── generated route pages
│
├── scripts/
│   ├── scrape_bussathi.py
│   ├── rebuild_data.py
│   ├── import_sbstc.py
│   ├── enrich_wbtc.py
│   ├── add_railway_stations.py
│   └── gen_seo_pages.py
│
├── .github/
│   └── workflows/
│
├── robots.txt
├── sitemap.xml
└── README.md

---

🔄 Data Reliability

Transport information changes.

Bus routes can change.

Timings can change.

Stop names can have spelling differences.

Because of this, BusJatri treats automated data collection as a data-quality problem, not simply a scraping problem.

The project aims to progressively improve:

- duplicate detection
- timetable validation
- route consistency
- stoppage validation
- geographic validation
- suspicious-data detection
- stale-data detection

Important

BusJatri should be treated as an information and discovery tool, not as an official guarantee of current bus operation.

Always confirm important travel information when necessary.

---

🚧 Current Limitations

BusJatri is an evolving project.

Some limitations include:

- automatically geocoded bus stops may not always be perfect
- bus timings can change without notice
- different sources may contain conflicting information
- some bus stops have ambiguous names
- railway-station distance is geographic distance, not actual travel distance
- public transport datasets may contain incomplete information

The project is designed to improve these issues through better validation and automated processing.

---

🎯 Roadmap

Phase 1 — Data Trust

- [x] Unified bus dataset
- [x] Route/stoppage indexing
- [x] Railway station proximity
- [x] Automated data processing
- [x] SEO route generation

Phase 2 — Better Accuracy

- [ ] Route-aware geocoding
- [ ] Multi-candidate location scoring
- [ ] Geographic consistency checks
- [ ] Duplicate stop detection
- [ ] Timetable anomaly detection
- [ ] Stronger automated validation
- [ ] Better stale-data detection

Phase 3 — Better Journey Planning

- [ ] From → To journey planner
- [ ] Next-bus discovery
- [ ] Via-stop search
- [ ] Alternative routes
- [ ] Better transfer suggestions
- [ ] Nearby bus stops

Phase 4 — Maps & Mobility

- [ ] Interactive route maps
- [ ] Bus-stop map
- [ ] Railway ↔ bus connectivity
- [ ] Better location-based discovery
- [ ] Potential real-time integrations where reliable public data becomes available

---

🤝 Contributing

Contributions are welcome.

Useful contributions include:

- fixing incorrect route information
- improving data validation
- improving geocoding logic
- improving Bengali/English search
- improving accessibility
- improving mobile UX
- adding reliable transport data sources
- improving documentation

Please avoid introducing unverified transport information.

Data quality is more important than data quantity.

---

📜 Data & Attribution

BusJatri combines information from public and third-party sources.

Individual datasets may have their own terms, licenses and attribution requirements.

Before redistributing or republishing a particular source, check that source's applicable terms.

BusJatri is not affiliated with any government transport corporation unless explicitly stated otherwise.

---

❤️ Why BusJatri?

West Bengal has a huge bus network.

But having information somewhere is not the same as making that information useful.

BusJatri's goal is simple:

«Make West Bengal bus information easier to find, understand and use.»

From a small bus stop to a major city.

From bus timing to railway connectivity.

From Bengali place names to searchable route pages.

One simple place to start your journey.

---

🚌 BusJatri

বাস যাত্রী — আপনার বাস, আপনার রুট, আপনার যাত্রা।

Made for travellers across West Bengal, India.
