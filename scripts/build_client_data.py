#!/usr/bin/env python3
"""Build the small initial browser index and lazy-loaded bus detail payload."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = json.loads((ROOT / "data/busjatri_data.json").read_text(encoding="utf-8"))
search_fields = ("id", "bus_name", "bus_type", "origin", "destination", "departure_time", "total_stoppages")
search_buses = [{k: bus.get(k) for k in search_fields} for bus in source["buses"]]
index = {
    "meta": source["meta"],
    "buses": search_buses,
    "routes": source["routes"],
    "stops": source["stops"],
}
(ROOT / "data/app-index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
(ROOT / "data/bus-details.json").write_text(json.dumps({b["id"]: b for b in source["buses"]}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("Built app-index.json and bus-details.json")
print("Initial index bytes:", (ROOT / "data/app-index.json").stat().st_size)
print("Lazy detail bytes:", (ROOT / "data/bus-details.json").stat().st_size)
