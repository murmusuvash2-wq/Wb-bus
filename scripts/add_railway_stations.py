#!/usr/bin/env python3
"""Attach nearest railway station to every bus stop — route-aware geocoding.

Combines current repo improvements with multi-candidate route validation:

  • Station list: state filter OR West Bengal bbox (rescues null-state stations)
  • Exact station-name match within 15 km preferred over slightly closer halt
  • Cache reuse (only missing / null coords re-geocoded; SKIP_GEOCODE=1 to skip)
  • Multi-candidate Open-Meteo (not first WB hit)
  • Scoring: name exactness, district, feature type, population
  • Route-aware: neighbouring stops + origin/destination corridor boost
  • Preserve existing good coords unless new candidate is materially stronger
  • Confidence high / medium / low — railway only attached for medium+
  • No public override file (deterministic scoring only)

Writes:
  data/stop_coords.json  — name -> {lat, lon, confidence, score, source}
  data/busjatri_data.json — stops[name].nearest_station = {name, code, km}

Run from repo root:
  python3 scripts/add_railway_stations.py
  SKIP_GEOCODE=1 python3 scripts/add_railway_stations.py   # reuse cache only
"""
from __future__ import annotations

import json
import math
import os
import re
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

STATIONS_URL = "https://raw.githubusercontent.com/datameet/railways/master/stations.json"
STATES = {"West Bengal", "Jharkhand", "Bihar", "Odisha", "Assam", "Sikkim"}
# generous West Bengal + border buffer (rescues state=None stations)
WB_LAT = (21.0, 27.5)
WB_LON = (85.2, 90.2)
UA = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; BusJatriUpdater/2.1; "
        "+https://github.com/murmusuvash2-wq/busjatri)"
    )
}

HIGH_MIN = 70
MEDIUM_MIN = 40
REPLACE_MARGIN = 15
CORRIDOR_KM = 35
NEIGHBOUR_WINDOW = 2
NAME_MATCH_STATION_KM = 15


def haversine(a, b):
    R = 6371.0
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (
        math.sin((la2 - la1) / 2) ** 2
        + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(h))


def get(url, timeout=45):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


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
    }
    return aliases.get(s, s)


def norm_tokens(s):
    s = re.sub(r"[^a-z0-9\s]", " ", (s or "").lower())
    return re.sub(r"\s+", " ", s).strip()


def name_similarity(stop, candidate_name):
    a, b = norm_tokens(stop), norm_tokens(candidate_name)
    if not a or not b:
        return 0
    if a == b:
        return 40
    if a in b or b in a:
        return 28
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0
    inter = len(ta & tb)
    return int(18 * inter / max(len(ta), len(tb)))


def feature_bonus(r):
    ft = (r.get("feature_code") or r.get("feature_class") or "").upper()
    if ft in ("RSTN", "RSTP", "STN"):
        return 15
    if ft in ("PPL", "PPLA", "PPLA2", "PPLA3", "PPLA4", "PPLC"):
        return 12
    if ft.startswith("P"):
        return 8
    if ft.startswith("A"):
        return 3
    return 5


def base_score(stop_name, district, r):
    lat, lon = r["latitude"], r["longitude"]
    if not in_wb(lat, lon):
        return -1
    score = name_similarity(stop_name, r.get("name") or "")
    admin = " ".join(
        filter(
            None,
            [r.get("admin1"), r.get("admin2"), r.get("admin3"), r.get("admin4")],
        )
    ).lower()
    if "west bengal" in admin or (r.get("admin1") or "").lower() == "west bengal":
        score += 15
    if district and district.lower() in admin:
        score += 12
    score += feature_bonus(r)
    pop = r.get("population") or 0
    if pop >= 50000:
        score += 8
    elif pop >= 10000:
        score += 5
    elif pop >= 2000:
        score += 2
    return score


def fetch_candidates(name, district):
    queries = []
    if district:
        queries.append(f"{name}, {district}, West Bengal, India")
        queries.append(f"{name}, {district} district, India")
    queries.append(f"{name}, West Bengal, India")
    queries.append(f"{name} railway station, West Bengal, India")
    queries.append(f"{name}, India")

    seen = set()
    candidates = []
    for q in queries:
        try:
            url = (
                "https://geocoding-api.open-meteo.com/v1/search?"
                + urllib.parse.urlencode(
                    {"name": q, "count": 10, "language": "en", "format": "json"}
                )
            )
            d = json.loads(get(url))
            for r in d.get("results") or []:
                key = (round(r["latitude"], 4), round(r["longitude"], 4))
                if key in seen:
                    continue
                seen.add(key)
                sc = base_score(name, district, r)
                if sc < 0:
                    continue
                candidates.append(
                    {
                        "score": sc,
                        "lat": r["latitude"],
                        "lon": r["longitude"],
                        "name": r.get("name"),
                        "population": r.get("population") or 0,
                    }
                )
            if len(candidates) >= 3:
                break
        except Exception:
            continue
        time.sleep(0.04)
    candidates.sort(key=lambda x: -x["score"])
    return candidates[:10]


def load_stations():
    raw = json.loads(get(STATIONS_URL))
    out, rescued = [], 0
    for f in raw.get("features") or []:
        p, g = f.get("properties") or {}, f.get("geometry") or {}
        c = g.get("coordinates") if g else None
        if not c or len(c) < 2:
            continue
        lat, lon = c[1], c[0]
        if p.get("state") in STATES or in_wb(lat, lon):
            out.append(
                {"name": p.get("name"), "code": p.get("code"), "lat": lat, "lon": lon}
            )
            if p.get("state") is None:
                rescued += 1
    print(f"stations rescued by bbox despite null state: {rescued}", flush=True)
    return out


def build_route_neighbours(buses):
    neighbours = defaultdict(set)
    for b in buses or []:
        stops = [s.get("name") for s in (b.get("stoppages") or []) if s.get("name")]
        if not stops:
            origin, dest = b.get("origin"), b.get("destination")
            stops = [x for x in (origin, dest) if x]
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


def route_boost(candidate, neighbour_coords):
    if not neighbour_coords:
        return 0
    lat, lon = candidate["lat"], candidate["lon"]
    distances = [haversine((lat, lon), nc) for nc in neighbour_coords if nc]
    if not distances:
        return 0
    nearest = min(distances)
    if nearest <= 8:
        return 25
    if nearest <= 15:
        return 18
    if nearest <= CORRIDOR_KM:
        return 10
    if nearest <= 60:
        return 0
    return -20


def confidence_label(score):
    if score >= HIGH_MIN:
        return "high"
    if score >= MEDIUM_MIN:
        return "medium"
    return "low"


def load_existing_cache(path):
    """Support both legacy [lat,lon] and new dict formats."""
    if not os.path.isfile(path):
        return {}
    try:
        raw = json.load(open(path))
    except Exception:
        return {}
    out = {}
    for name, val in raw.items():
        if val is None:
            continue
        if isinstance(val, (list, tuple)) and len(val) >= 2:
            out[name] = {
                "lat": val[0],
                "lon": val[1],
                "confidence": "medium",
                "score": 50,
                "source": "legacy",
            }
        elif isinstance(val, dict) and "lat" in val and "lon" in val:
            out[name] = val
    return out


def pick_railway(coord, stations, stop_name):
    """Prefer station with matching name (even if coords are off), else nearest."""
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
    if exact is not None and ed <= 50:
        return exact, ed, True
    return best, bd, False


def main():
    data = json.load(open("data/busjatri_data.json"))
    stations = load_stations()
    print(f"stations loaded: {len(stations)}", flush=True)

    stops = data.get("stops") or {}
    buses = data.get("buses") or []

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

    neighbours = build_route_neighbours(buses)
    existing = load_existing_cache("data/stop_coords.json")
    print(
        f"stops={len(stops)} existing_coords={len(existing)} "
        f"with_neighbours={sum(1 for n in stops if neighbours.get(n))}",
        flush=True,
    )

    skip_net = bool(os.environ.get("SKIP_GEOCODE"))
    todo = [n for n in stops if n not in existing]
    candidate_map = {}

    if skip_net:
        print("SKIP_GEOCODE=1 — using cache only", flush=True)
    elif todo:
        print(f"Phase 1: fetching candidates for {len(todo)} stops…", flush=True)

        def work(name):
            return name, fetch_candidates(name, districts.get(name))

        done = 0
        with ThreadPoolExecutor(max_workers=6) as ex:
            futs = {ex.submit(work, n): n for n in todo}
            for fut in as_completed(futs):
                name, cands = fut.result()
                candidate_map[name] = cands
                done += 1
                if done % 80 == 0:
                    print(f"  candidates {done}/{len(todo)}", flush=True)
    else:
        print("All stops already have coords in cache", flush=True)

    for name in stops:
        if name not in candidate_map and name in existing:
            ex = existing[name]
            candidate_map[name] = [
                {
                    "score": ex.get("score", 50),
                    "lat": ex["lat"],
                    "lon": ex["lon"],
                    "name": name,
                    "population": 0,
                }
            ]

    print("Phase 2: route-aware scoring…", flush=True)
    assigned = {}

    for name, info in existing.items():
        if info.get("confidence") == "high" and name in stops:
            assigned[name] = dict(info)

    def neighbour_coords_for(name):
        coords = []
        for nb in neighbours.get(name) or []:
            if nb in assigned:
                coords.append((assigned[nb]["lat"], assigned[nb]["lon"]))
            elif nb in existing and existing[nb].get("confidence") in (
                "high",
                "medium",
            ):
                coords.append((existing[nb]["lat"], existing[nb]["lon"]))
        return coords

    for pass_i in range(3):
        order = sorted(
            stops.keys(),
            key=lambda n: (
                0 if n in assigned else 1,
                -len(neighbours.get(n) or []),
                n,
            ),
        )
        for name in order:
            cands = candidate_map.get(name) or []
            if not cands and name not in existing:
                continue

            nb_coords = neighbour_coords_for(name)
            best, best_total = None, -1e9
            for c in cands:
                total = c["score"] + route_boost(c, nb_coords)
                if total > best_total:
                    best_total = total
                    best = c

            if name in existing:
                ex = existing[name]
                ex_score = ex.get("score", 50)
                if nb_coords:
                    dmin = min(
                        haversine((ex["lat"], ex["lon"]), nc) for nc in nb_coords
                    )
                    if dmin <= CORRIDOR_KM:
                        ex_score += 10
                    elif dmin > 80:
                        ex_score -= 15
                if best is None or ex_score + REPLACE_MARGIN >= best_total:
                    if best is None or ex_score >= best_total - REPLACE_MARGIN:
                        assigned[name] = {
                            "lat": ex["lat"],
                            "lon": ex["lon"],
                            "confidence": confidence_label(ex_score),
                            "score": round(ex_score, 1),
                            "source": ex.get("source", "preserved"),
                        }
                        continue

            if best is None:
                continue
            conf = confidence_label(best_total)
            prev = assigned.get(name)
            if prev and prev.get("score", 0) + 5 >= best_total:
                continue
            assigned[name] = {
                "lat": best["lat"],
                "lon": best["lon"],
                "confidence": conf,
                "score": round(best_total, 1),
                "source": "open-meteo+route",
                "matched_name": best.get("name"),
            }

        print(
            f"  pass {pass_i + 1}: assigned={len(assigned)} "
            f"high={sum(1 for v in assigned.values() if v['confidence']=='high')} "
            f"medium={sum(1 for v in assigned.values() if v['confidence']=='medium')} "
            f"low={sum(1 for v in assigned.values() if v['confidence']=='low')}",
            flush=True,
        )

    cache_out = {}
    for n in sorted(assigned):
        info = assigned[n]
        cache_out[n] = {
            "lat": info["lat"],
            "lon": info["lon"],
            "confidence": info["confidence"],
            "score": info["score"],
            "source": info.get("source", ""),
        }
    os.makedirs("data", exist_ok=True)
    with open("data/stop_coords.json", "w", encoding="utf-8") as f:
        json.dump(cache_out, f, ensure_ascii=False, indent=2)

    have = failed = skipped_low = exact_matches = 0
    for name, s in stops.items():
        s.pop("nearest_station", None)
        info = assigned.get(name)
        if not info:
            failed += 1
            continue
        if info["confidence"] == "low":
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

    print(
        f"DONE coords={len(assigned)} railway_attached={have} "
        f"exact_name_matches={exact_matches} no_coord={failed} "
        f"low_skipped={skipped_low}",
        flush=True,
    )


if __name__ == "__main__":
    main()
