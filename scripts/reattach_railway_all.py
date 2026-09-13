#!/usr/bin/env python3
"""Re-attach nearest railway to every stop that has coords.
Always attach — even if station is far. No confidence skip. No km hide.
"""
from __future__ import annotations
import json, math, os, re, urllib.request

STATIONS_URL = "https://raw.githubusercontent.com/datameet/railways/master/stations.json"
WB_LAT, WB_LON = (21.0, 27.5), (85.2, 90.2)
STATES = {"West Bengal", "Jharkhand", "Bihar", "Odisha", "Assam", "Sikkim"}
UA = {"User-Agent": "BusJatriRailway/1.0 (+https://github.com/murmusuvash2-wq/busjatri)"}

def haversine(a, b):
    R = 6371.0
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 2 * R * math.asin(math.sqrt(h))

def norm(s):
    s = re.sub(r"[^a-z]", "", (s or "").lower())
    aliases = {"garbeta": "garhbeta", "midnapore": "medinipur", "midnapur": "medinipur",
               "burdwan": "bardhaman", "barddhaman": "bardhaman", "tarakeswar": "tarkeshwar"}
    return aliases.get(s, s)

def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode())

def load_stations():
    raw = get_json(STATIONS_URL)
    out = []
    for f in raw.get("features") or []:
        p, g = f.get("properties") or {}, f.get("geometry") or {}
        c = g.get("coordinates") if g else None
        if not c or len(c) < 2: continue
        lat, lon = c[1], c[0]
        if p.get("state") in STATES or (WB_LAT[0] <= lat <= WB_LAT[1] and WB_LON[0] <= lon <= WB_LON[1]):
            out.append({"name": p.get("name") or "", "code": p.get("code") or "", "lat": lat, "lon": lon})
    return out

def load_coords(path):
    if not os.path.isfile(path): return {}
    raw = json.load(open(path, encoding="utf-8"))
    out = {}
    for name, val in raw.items():
        if val is None: continue
        if isinstance(val, (list, tuple)) and len(val) >= 2:
            out[name] = (float(val[0]), float(val[1]))
        elif isinstance(val, dict) and "lat" in val:
            out[name] = (float(val["lat"]), float(val["lon"]))
    return out

def pick_railway(coord, stations, stop_name):
    best, bd = None, 1e9
    exact, ed = None, 1e9
    nstop = norm(stop_name)
    for st in stations:
        d = haversine(coord, (st["lat"], st["lon"]))
        if d < bd:
            bd, best = d, st
        nst = norm(st["name"])
        if nst == nstop and d < ed:
            ed, exact = d, st
        elif exact is None and len(nstop) >= 5 and (nstop in nst or nst in nstop) and d < 50 and d < ed:
            ed, exact = d, st
    if exact is not None and ed <= 50:
        return exact, ed
    return best, bd

def main():
    data = json.load(open("data/busjatri_data.json", encoding="utf-8"))
    stations = load_stations()
    coords = load_coords("data/stop_coords.json")
    for st in stations:
        if (st.get("code") or "").upper() == "GBA":
            coords["Garhbeta"] = (st["lat"], st["lon"])
            print("Forced Garhbeta -> GBA", st["lat"], st["lon"])
            break

    stops = data.get("stops") or {}
    have = exact = no_coord = 0
    for name, s in stops.items():
        s.pop("nearest_station", None)
        coord = coords.get(name)
        if not coord:
            no_coord += 1
            continue
        pick, km = pick_railway(coord, stations, name)
        if pick:
            s["nearest_station"] = {
                "name": pick["name"],
                "code": pick["code"] or "",
                "km": round(km, 1),
            }
            have += 1
            if norm(name) == norm(pick["name"]):
                exact += 1

    old = {}
    if os.path.isfile("data/stop_coords.json"):
        try:
            old = json.load(open("data/stop_coords.json", encoding="utf-8"))
        except Exception:
            pass
    out = {}
    for n, (lat, lon) in coords.items():
        prev = old.get(n) if isinstance(old.get(n), dict) else {}
        out[n] = {
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "confidence": prev.get("confidence", "medium"),
            "score": prev.get("score", 50),
            "source": prev.get("source", "reattach"),
        }
    if "Garhbeta" in out:
        out["Garhbeta"]["source"] = "rail-snap:GBA"
        out["Garhbeta"]["confidence"] = "high"
        out["Garhbeta"]["score"] = 145

    os.makedirs("data", exist_ok=True)
    with open("data/stop_coords.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    data["stops"] = stops
    with open("data/busjatri_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    print(f"DONE railway={have} exact_name={exact} no_coord={no_coord}")
    print("Garhbeta =>", stops.get("Garhbeta", {}).get("nearest_station"))
    for n in ["Khatra", "Ranibandh", "Karimpur", "Jalangi"]:
        print(n, "=>", (stops.get(n) or {}).get("nearest_station"))

if __name__ == "__main__":
    main()
