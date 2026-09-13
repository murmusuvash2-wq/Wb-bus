#!/usr/bin/env python3
"""Fix hero bus animation: move route line to TOP of hero (above title),
add bus-stop dots, and make the bus drift with gentle suspension bob
+ brief pauses at the two stops. Idempotent.

Replaces the .hero-route-line / @keyframes driftBus block in css/style.css.
"""

import re

css_path = 'css/style.css'
css = open(css_path, encoding='utf-8').read()

MARKER = '/* bus-stop animation v2 */'

if MARKER in css:
    print('fix_animation: already applied')
else:
    # Replace the entire hero-route-line block (from selector to reduced-motion rule).
    # This matches both the original and any previously-patched version.
    pattern = re.compile(
        r'\.hero-route-line\s*\{.*?@media\s*\(\s*prefers-reduced-motion:\s*reduce\s*\)\s*\{[^}]*\.hero-route-line[^}]*\}',
        re.DOTALL,
    )
    new_block = (
        '.hero-route-line {\n'
        '  position: absolute; top: 22px; left: 0; width: 100%; height: 3px;\n'
        '  border-top: 3px dashed var(--line-strong); opacity: .5;\n'
        '}\n'
        '.hero-route-line::before, .hero-route-line::after {\n'
        '  content: ""; position: absolute; top: -5.5px; width: 10px; height: 10px;\n'
        '  border-radius: 50%; background: var(--bg); border: 2.5px solid var(--line-strong);\n'
        '  box-sizing: border-box;\n'
        '}\n'
        '.hero-route-line::before { left: 22%; }\n'
        '.hero-route-line::after { left: 76%; }\n'
        '.hero-route-line .icon {\n'
        '  position: absolute; top: -17px; left: 0; color: var(--amber); opacity: .75;\n'
        '  width: 26px; height: 26px;\n'
        '  filter: drop-shadow(0 2px 3px rgba(0,0,0,.18));\n'
        '  animation: driftBus 15s ease-in-out infinite;\n'
        '}\n'
        '@keyframes driftBus {\n' 
        '  0%   { left: -7%;  transform: translateY(0); }\n'
        '  6%   { transform: translateY(-2px); }\n'
        '  12%  { transform: translateY(0); }\n'
        '  18%  { left: 20%;  transform: translateY(-1px); }\n'
        '  24%  { left: 20%;  transform: translateY(0); }\n'
        '  30%  { transform: translateY(-2px); }\n'
        '  36%  { transform: translateY(0); }\n'
        '  55%  { left: 74%; transform: translateY(-1px); }\n'
        '  61%  { left: 74%;  transform: translateY(0); }\n'
        '  67%  { transform: translateY(-2px); }\n'
        '  73%  { transform: translateY(0); }\n'
        '  100% { left: 107%; transform: translateY(0); }\n'
        '}\n'
        '@media (prefers-reduced-motion: reduce) { .hero-route-line .icon { animation: none; left: 40%; } }\n'
        + MARKER
    )
    new_css, n = pattern.subn(new_block, css, count=1)
    if n == 0:
        # Fallback: if regex didn't match, append the block (old code may have been removed)
        new_css = css + '\n' + new_block
    open(css_path, 'w', encoding='utf-8').write(new_css)
    print(f'fix_animation: applied ({n} replacement)')
