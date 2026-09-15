#!/usr/bin/env python3
"""Splice the v6 animated index page generation into gen_seo_pages.py.

Replaces the old index-page section (from `by_origin = defaultdict(list)`
up to the SITEMAP marker) with the contents of
scripts/v5/new_index_part1.txt + scripts/v5/new_index_part2.txt.
"""

import py_compile

GEN = "scripts/gen_seo_pages.py"
START = "by_origin = defaultdict(list)"
END = "# ------------------------------------------------------------\n# SITEMAP"


def main() -> None:
    with open(GEN, encoding="utf-8") as f:
        code = f.read()

    with open("scripts/v5/new_index_part1.txt", encoding="utf-8") as f:
        part1 = f.read()

    with open("scripts/v5/new_index_part2.txt", encoding="utf-8") as f:
        part2 = f.read()

    new_code = part1 + part2

    si = code.find(START)
    ei = code.find(END)

    if si < 0:
        raise SystemExit("START marker not found in gen_seo_pages.py")
    if ei < 0:
        raise SystemExit("END marker not found in gen_seo_pages.py")
    if ei <= si:
        raise SystemExit("END marker appears before START marker")

    spliced = code[:si] + new_code.strip() + "\n\n\n" + code[ei:]

    with open(GEN, "w", encoding="utf-8") as f:
        f.write(spliced)

    py_compile.compile(GEN, doraise=True)
    print(
        "OK: spliced v6 index page "
        f"(replaced {ei - si} chars, inserted {len(new_code)} chars)"
    )


if __name__ == "__main__":
    main()
