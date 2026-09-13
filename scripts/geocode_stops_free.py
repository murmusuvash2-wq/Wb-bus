#!/usr/bin/env python3
"""Free-only stop geocoding + quality pass for BusJatri.

No Google / paid APIs. Sources:
  1. Open-Meteo geocoding API (free)
  2. Nominatim / OpenStreetMap (free, rate-limited)
  3. Indian railway stations (datameet) — name snap when stop ≈ station
  4. Route-neighbour corridor validation

Goals:
  • Fill missing stop coords
  • Re-check stops whose nearest railway is >15 km (likely bad pin)
  • Prefer multi-source agreement within ~3 km
  • Name-match station (Garhbeta → GBA) even when old pin was wrong
  • Low confidence → no railway chip

Writes:
  data/stop_coords.json
  data/busjatri_data.json  (nearest_station on stops)
  data/geocode_report.json (audit)

Usage (repo root):
  python3 scripts/geocode_stops_free.py
  python3 scripts/geocode_stops_free.py --only-suspects
  python3 scripts/geocode_stops_free.py --limit 50
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import time
import urllib.parse
import urllib.request
from collections import defaultdict

STATIONS_URL = "https://raw.githubusercontent.com/datameet/railways/master/stations.json"
WB_LAT = (21.0, 27.5)
WB_LON = (85.2, 90.2)
STATES = {"West Bengal", "Jharkhand", "Bihar", "Odisha", "Assam", "Sikkim"}
UA = {
    "User-Agent": (
        "BusJatriFreeGeocoder/1.0 (+https://github.com/murmusuvash2-wq/busjatri; "
        "contact: bus timetable open data)"
    )
}

HIGH_MIN = 70
MEDIUM_MIN = 40
AGREE_KM = 3.5
SUSPECT_RAIL_KM = 15.0
NAME_SNAP_KM = 50.0
CORRIDOR_KM = 40.0
NEIGHBOUR_WINDOW = 2
NOMINATIM_SLEEP = 1.05


def haversine(a, b):
    R = 6371.0
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (
        math.sin((la2 - la1) / 2) ** 2
        + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(h))


def get_json(url, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def in_wb(lat, lon):
    return WB_LAT[0] <= lat <= WB_LAT[1] and WB_LON[0] <= lon <= WB_LON[1]


def norm(s):
    s = re.sub(r"[^a-z]", "", (s or "").lower())
    aliases = {
        "garbeta": "garhbeta",
        "garhbeta": "garhbeta",
        "midnapore": "medinipur",
        "midnapur": "medinipur",
        "medinipur": "medinipur",
        "burdwan": "bardhaman",
        "barddhaman": "bardhaman",
        "tarakeswar": "tarkeshwar",
        "tarkeswar": "tarkeshwar",
        "coochbehar": "coochbehar",
        "kochbihar": "coochbehar",
    }
    return aliases.get(s, s)


def norm_tokens(s):
    s = re.sub(r"[^a-z0-9\s]", " ", (s or "").lower())
    return re.sub(r"\s+", " ", s).strip()


def name_similarity(stop, candidate_name):
    a, b = norm_tokens(stop), norm_tokens(candidate_name)
    if not a or not b:
        return 0
    if a == b or norm(a) == norm(b):
        return 40
    if a in b or b in a:
        return 28
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0
    inter = len(ta & tb)
    return int(18 * inter / max(len(ta), len(tb)))


def confidence_label(score):
    if score >= HIGH_MIN:
        return "high"
    if score >= MEDIUM_MIN:
        return "medium"
    return "low"


def open_meteo_candidates(name, district=None):
    queries = []
    if district:
        queries.append(f"{name}, {district}, West Bengal, India")
    queries.append(f"{name}, West Bengal, India")
    queries.append(f"{name} bus stand, West Bengal, India")
    queries.append(f"{name}, India")

    seen, out = set(), []
    for q in queries:
        try:
            url = (
                "https://geocoding-api.open-meteo.com/v1/search?"
                + urllib.parse.urlencode(
                    {"name": q, "count": 8, "language": "en", "format": "json"}
                )
            )
            d = get_json(url)
            for r in d.get("results") or []:
                lat, lon = r["latitude"], r["longitude"]
                if not in_wb(lat, lon):
                    continue
                key = (round(lat, 4), round(lon, 4))
                if key in seen:
                    continue
                seen.add(key)
                admin = " ".join(
                    filter(
                        None,
                        [
                            r.get("admin1"),
                            r.get("admin2"),
                            r.get("admin3"),
                            r.get("admin4"),
                        ],
                    )
                ).lower()
                sc = name_similarity(name, r.get("name") or "")
                if "west bengal" in admin:
                    sc += 15
                if district and district.lower() in admin:
                    sc += 12
                ft = (r.get("feature_code") or "").upper()
                if ft.startswith("PPL"):
                    sc += 10
                elif ft.startswith("P"):
                    sc += 6
                pop = r.get("population") or 0
                if pop >= 20000:
                    sc += 6
                elif pop >= 5000:
                    sc += 3
                out.append(
                    {
                        "lat": lat,
                        "lon": lon,
                        "score": sc,
                        "name": r.get("name"),
                        "source": "open-meteo",
                        "population": pop,
                    }
                )
            if len(out) >= 4:
                break
        except Exception:
            continue
        time.sleep(0.05)
    out.sort(key=lambda x: -x["score"])
    return out[:8]


_nominatim_last = 0.0


def nominatim_candidates(name, district=None):
    global _nominatim_last
    queries = []
    if district:
        queries.append(f"{name}, {district}, West Bengal, India")
    queries.append(f"{name}, West Bengal, India")

    seen, out = set(), []
    for q in queries:
        wait = NOMINATIM_SLEEP - (time.time() - _nominatim_last)
        if wait > 0:
            time.sleep(wait)
        try:
            url = (
                "https://nominatim.openstreetmap.org/search?"
                + urllib.parse.urlencode(
                    {
                        "q": q,
                        "format": "json",
                        "limit": 5,
                        "countrycodes": "in",
                        "addressdetails": 1,
                    }
                )
            )
            _nominatim_last = time.time()
            rows = get_json(url)
            if not isinstance(rows, list):
                continue
            for r in rows:
                lat, lon = float(r["lat"]), float(r["lon"])
                if not in_wb(lat, lon):
                    continue
                key = (round(lat, 4), round(lon, 4))
                if key in seen:
                    continue
                seen.add(key)
                disp = r.get("display_name") or ""
                sc = name_similarity(name, (r.get("name") or disp.split(",")[0]))
                addr = r.get("address") or {}
                state = (addr.get("state") or "").lower()
                if "west bengal" in state or "bengal" in state:
                    sc += 15
                if district and district.lower() in disp.lower():
                    sc += 10
                cls = (r.get("class") or "") + ":" + (r.get("type") or "")
                if "bus" in cls or "station" in cls:
                    sc += 12
                elif r.get("type") in ("town", "city", "village", "suburb", "hamlet"):
                    sc += 8
                out.append(
                    {
                        "lat": lat,
                        "lon": lon,
                        "score": sc,
                        "name": r.get("name") or disp.split(",")[0],
                        "source": "nominatim",
                        "population": 0,
                    }
                )
        except Exception:
            continue
        if len(out) >= 3:
            break
    out.sort(key=lambda x: -x["score"])
    return out[:5]


def load_stations():
    raw = get_json(STATIONS_URL)
    out = []
    for f in raw.get("features") or []:
        p, g = f.get("properties") or {}, f.get("geometry") or {}
        c = g.get("coordinates") if g else None
        if not c or len(c) < 2:
            continue
        lat, lon = c[1], c[0]
        if p.get("state") in STATES or in_wb(lat, lon):
            out.append(
                {
                    "name": p.get("name") or "",
                    "code": p.get("code") or "",
                    "lat": lat,
                    "lon": lon,
                }
            )
    return out


def station_name_snap(stop_name, stations):
    nstop = norm(stop_name)
    if len(nstop) < 4:
        return None
    best, best_sc = None, 0
    for st in stations:
        nst = norm(st["name"])
        if nst == nstop:
            return {
                "lat": st["lat"],
                "lon": st["lon"],
                "score": 95,
                "name": st["name"],
                "source": f"rail-snap:{st['code']}",
                "population": 0,
                "station": st,
            }
        if len(nstop) >= 5 and (nstop in nst or nst in nstop):
            sc = 80
            if sc > best_sc:
                best_sc = sc
                best = {
                    "lat": st["lat"],
                    "lon": st["lon"],
                    "score": sc,
                    "name": st["name"],
                    "source": f"rail-soft:{st['code']}",
                    "population": 0,
                    "station": st,
                }
    return best


def merge_candidates(groups):
    flat = []
    for g in groups:
        flat.extend(g or [])
    if not flat:
        return []

    clusters = []
    for c in sorted(flat, key=lambda x: -x["score"]):
        placed = False
        for cl in clusters:
            if haversine((c["lat"], c["lon"]), (cl["lat"], cl["lon"])) <= AGREE_KM:
                cl["members"].append(c)
                cl["sources"].add(c["source"].split(":")[0])
                cl["score"] = max(cl["score"], c["score"])
                placed = True
                break
        if not placed:
            clusters.append(
                {
                    "lat": c["lat"],
                    "lon": c["lon"],
                    "score": c["score"],
                    "name": c.get("name"),
                    "source": c["source"],
                    "members": [c],
                    "sources": {c["source"].split(":")[0]},
                    "station": c.get("station"),
                }
            )

    for cl in clusters:
        nsrc = len(cl["sources"])
        if nsrc >= 2:
            cl["score"] += 20
        if any(m["source"].startswith("rail-snap") for m in cl["members"]):
            cl["score"] += 25
        elif any(m["source"].startswith("rail-") for m in cl["members"]):
            cl["score"] += 10
    clusters.sort(key=lambda x: -x["score"])
    return clusters


def route_boost(candidate, neighbour_coords):
    if not neighbour_coords:
        return 0
    distances = [
        haversine((candidate["lat"], candidate["lon"]), nc)
        for nc in neighbour_coords
        if nc
    ]
    if not distances:
        return 0
    nearest = min(distances)
    if nearest <= 8:
        return 25
    if nearest <= 15:
        return 18
    if nearest <= CORRIDOR_KM:
        return 10
    if nearest <= 80:
        return 0
    return -25


def build_route_neighbours(buses):
    neighbours = defaultdict(set)
    for b in buses or []:
        stops = [s.get("name") for s in (b.get("stoppages") or []) if s.get("name")]
        if not stops:
            stops = [x for x in (b.get("origin"), b.get("destination")) if x]
        for i, name in enumerate(stops):
            for j in range(
                max(0, i - NEIGHBOUR_WINDOW), min(len(stops), i + NEIGHBOUR_WINDOW + 1)
            ):
                if j != i:
                    neighbours[name].add(stops[j])
            if b.get("origin"):
                neighbours[name].add(b["origin"])
            if b.get("destination"):
                neighbours[name].add(b["destination"])
    return {k: list(v) for k, v in neighbours.items()}


def load_coords(path):
    if not os.path.isfile(path):
        return {}
    try:
        raw = json.load(open(path, encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    for name, val in raw.items():
        if val is None:
            continue
        if isinstance(val, (list, tuple)) and len(val) >= 2:
            out[name] = {
                "lat": float(val[0]),
                "lon": float(val[1]),
                "confidence": "medium",
                "score": 50,
                "source": "legacy",
            }
        elif isinstance(val, dict) and "lat" in val and "lon" in val:
            out[name] = val
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
        elif (
            exact is None
            and len(nstop) >= 5
            and (nstop in nst or nst in nstop)
            and d < 25
            and d < ed
        ):
            ed, exact = d, st
    if exact is not None and ed <= NAME_SNAP_KM:
        return exact, ed, True
    return best, bd, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-suspects", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--skip-nominatim", action="store_true")
    args = ap.parse_args()

    data = json.load(open("data/busjatri_data.json", encoding="utf-8"))
    stations = load_stations()
    print(f"stations={len(stations)}", flush=True)

    stops = data.get("stops") or {}
    buses = data.get("buses") or []
    existing = load_coords("data/stop_coords.json")
    neighbours = build_route_neighbours(buses)

    depot_votes = defaultdict(lambda: defaultdict(int))
    for b in buses:
        dep = (b.get("depot_name") or "").strip()
        if not dep or dep in ("—", "-", "Not Available !"):
            continue
        for s in b.get("stoppages") or []:
            n = s.get("name")
            if n:
                depot_votes[n][dep] += 1
    districts = {
        n: max(votes, key=votes.get) for n, votes in depot_votes.items() if votes
    }

    missing = [n for n in stops if n not in existing]
    suspects = []
    for n, s in stops.items():
        if n not in existing:
            continue
        ns = s.get("nearest_station") or {}
        km = ns.get("km")
        if km is not None and km >= SUSPECT_RAIL_KM:
            suspects.append(n)
        elif existing[n].get("confidence") == "low":
            suspects.append(n)

    if args.only_suspects:
        todo = list(dict.fromkeys(suspects))
    else:
        todo = list(dict.fromkeys(missing + suspects))

    if args.limit and args.limit > 0:
        todo = todo[: args.limit]

    print(
        f"stops={len(stops)} coords={len(existing)} missing={len(missing)} "
        f"suspects={len(suspects)} todo={len(todo)}",
        flush=True,
    )

    assigned = dict(existing)
    report = {"fixed": [], "filled": [], "failed": [], "kept": []}

    def neighbour_coords(name):
        coords = []
        for nb in neighbours.get(name) or []:
            if nb in assigned and assigned[nb].get("confidence") != "low":
                coords.append((assigned[nb]["lat"], assigned[nb]["lon"]))
        return coords

    for i, name in enumerate(todo):
        district = districts.get(name)
        snap = station_name_snap(name, stations)
        om = open_meteo_candidates(name, district)
        nom = [] if args.skip_nominatim else nominatim_candidates(name, district)
        groups = [[snap] if snap else [], om, nom]
        clusters = merge_candidates(groups)

        nb = neighbour_coords(name)
        best, best_total = None, -1e9
        for cl in clusters:
            total = cl["score"] + route_boost(cl, nb)
            if total > best_total:
                best_total, best = total, cl

        if best is None:
            report["failed"].append(name)
            print(f"  [{i+1}/{len(todo)}] FAIL {name}", flush=True)
            continue

        conf = confidence_label(best_total)
        prev = existing.get(name)
        if prev and prev.get("confidence") == "high" and conf != "high":
            if best_total < (prev.get("score") or 70) + 15:
                report["kept"].append(name)
                continue

        assigned[name] = {
            "lat": round(best["lat"], 6),
            "lon": round(best["lon"], 6),
            "confidence": conf,
            "score": round(best_total, 1),
            "source": "+".join(sorted(best["sources"]))
            if best.get("sources")
            else best.get("source", ""),
        }
        kind = "filled" if name not in existing else "fixed"
        report[kind].append(
            {
                "name": name,
                "lat": assigned[name]["lat"],
                "lon": assigned[name]["lon"],
                "score": assigned[name]["score"],
                "confidence": conf,
                "source": assigned[name]["source"],
                "prev": prev,
            }
        )
        print(
            f"  [{i+1}/{len(todo)}] {kind.upper()} {name} "
            f"→ {assigned[name]['lat']},{assigned[name]['lon']} "
            f"conf={conf} score={assigned[name]['score']} src={assigned[name]['source']}",
            flush=True,
        )

    cache_out = {}
    for n in sorted(assigned):
        info = assigned[n]
        cache_out[n] = {
            "lat": info["lat"],
            "lon": info["lon"],
            "confidence": info.get("confidence", "medium"),
            "score": info.get("score", 50),
            "source": info.get("source", ""),
        }
    os.makedirs("data", exist_ok=True)
    with open("data/stop_coords.json", "w", encoding="utf-8") as f:
        json.dump(cache_out, f, ensure_ascii=False, indent=2)

    have = exact_matches = skipped_low = failed = 0
    for name, s in stops.items():
        s.pop("nearest_station", None)
        info = assigned.get(name)
        if not info:
            failed += 1
            continue
        if info.get("confidence") == "low":
            skipped_low += 1
            continue
        pick, km, is_exact = pick_railway(
            (info["lat"], info["lon"]), stations, name
        )
        if pick:
            if is_exact:
                exact_matches += 1
            s["nearest_station"] = {
                "name": pick["name"],
                "code": pick["code"] or "",
                "km": round(km, 1),
            }
            have += 1

    data["stops"] = stops
    with open("data/busjatri_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    report_summary = {
        "filled": len(report["filled"]),
        "fixed": len(report["fixed"]),
        "failed": report["failed"],
        "kept": len(report["kept"]),
        "railway_attached": have,
        "exact_name_matches": exact_matches,
        "low_skipped": skipped_low,
        "no_coord": failed,
        "samples_fixed": report["fixed"][:20],
        "samples_filled": report["filled"][:20],
    }
    with open("data/geocode_report.json", "w", encoding="utf-8") as f:
        json.dump(report_summary, f, ensure_ascii=False, indent=2)

    print(
        f"DONE filled={report_summary['filled']} fixed={report_summary['fixed']} "
        f"failed={len(report['failed'])} railway={have} exact={exact_matches} "
        f"low_skip={skipped_low}",
        flush=True,
    )


if __name__ == "__main__":
    main()
