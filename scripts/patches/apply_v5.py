#!/usr/bin/env python3
"""Splice v5 template functions into gen_seo_pages.py.
Replaces: header_html, footer_html, shell, bus_card, generate_route_page
Keeps: all data functions, jsonld/schema, route_stats, place pages, via pages, main
"""
import os, re

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(REPO, "scripts", "gen_seo_pages.py")
V5 = os.path.join(REPO, "scripts", "v5")

# Read original
with open(GEN, encoding="utf-8") as f:
    src = f.read()
lines = src.split("\n")

# Find function boundaries by searching for def lines
def find_def(name):
    for i, line in enumerate(lines):
        if line.strip().startswith(f"def {name}(") or line.strip() == f"def {name}():\n":
            return i
    raise ValueError(f"Function {name} not found")

i_header = find_def("header_html")
i_jsonld = find_def("jsonld")
i_buscard = find_def("bus_card")
i_grp = find_def("generate_route_page")
i_place = find_def("generate_place_page")

# Read new function files
with open(os.path.join(V5, "new_shell.txt"), encoding="utf-8") as f:
    new_shell = f.read()
with open(os.path.join(V5, "new_bus_card.txt"), encoding="utf-8") as f:
    new_bus_card = f.read()
with open(os.path.join(V5, "new_route_page.txt"), encoding="utf-8") as f:
    new_route_page = f.read()

# Splice
result = (
    "\n".join(lines[:i_header]) + "\n\n" +      # before header_html
    new_shell + "\n\n" +                         # header_html + footer_html + shell
    "\n".join(lines[i_jsonld:i_buscard]) + "\n\n" +  # jsonld through route_stops_html
    new_bus_card + "\n\n" +                      # bus_card
    new_route_page + "\n\n" +                     # _board_data + generate_route_page
    "\n".join(lines[i_place:]) + "\n"             # place pages + main
)

with open(GEN, "w", encoding="utf-8") as f:
    f.write(result)

print(f"Spliced gen_seo_pages.py: {len(result)} bytes")
print(f"  Replaced lines {i_header+1}-{i_jsonld} (header/footer/shell)")
print(f"  Kept lines {i_jsonld+1}-{i_buscard} (jsonld/schema/stats)")
print(f"  Replaced lines {i_buscard+1}-{i_grp} (bus_card)")
print(f"  Replaced lines {i_grp+1}-{i_place} (generate_route_page)")
print(f"  Kept lines {i_place+1}-end (place/via/main)")
