#!/usr/bin/env python3
"""Generate og-image.png (1200x630 branded social share card).

Run from repo root. Requires pillow + fonts-beng-extra (Mukti Bold)
and the DejaVu fonts (usually preinstalled)."""
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
CREAM = (247, 234, 216)
SURFACE = (255, 252, 247)
AMBER = (184, 121, 31)
AMBER_INK = (122, 78, 14)
INK = (52, 43, 29)

img = Image.new('RGB', (W, H), CREAM)
d = ImageDraw.Draw(img)

f_disp = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', 96)
f_disp2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', 34)
f_bn = ImageFont.truetype('/usr/share/fonts/truetype/fonts-beng-extra/Muktibold.ttf', 40)
f_bn_s = ImageFont.truetype('/usr/share/fonts/truetype/fonts-beng-extra/Muktibold.ttf', 26)
f_mono = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26)

# card with ticket-stub notches
x0, y0, x1, y1 = 60, 60, W - 60, H - 60
d.rounded_rectangle([x0, y0, x1, y1], 28, fill=SURFACE, outline=(216, 199, 170), width=3)
for cy in (H // 2,):
    d.ellipse([x0 - 26, cy - 26, x0 + 26, cy + 26], fill=CREAM, outline=(216, 199, 170), width=3)
    d.ellipse([x1 - 26, cy - 26, x1 + 26, cy + 26], fill=CREAM, outline=(216, 199, 170), width=3)

# bus icon
bx, by = 140, 150
d.rounded_rectangle([bx, by, bx + 190, by + 105], 18, fill=AMBER)
d.rounded_rectangle([bx + 22, by + 18, bx + 92, by + 58], 8, fill=SURFACE)
d.rounded_rectangle([bx + 106, by + 18, bx + 168, by + 58], 8, fill=SURFACE)
d.ellipse([bx + 30, by + 82, bx + 72, by + 124], fill=INK)
d.ellipse([bx + 118, by + 82, bx + 160, by + 124], fill=INK)

# wordmark
d.text((380, 128), 'Bus', font=f_disp, fill=INK)
w = d.textlength('Bus', font=f_disp)
d.text((380 + w, 128), 'Jatri', font=f_disp, fill=AMBER)

# dashed divider
y = 340
for xd in range(x0 + 50, x1 - 40, 26):
    d.line([xd, y, xd + 14, y], fill=(216, 199, 170), width=4)

# tagline
d.text((140, 385), 'West Bengal Bus Timetable', font=f_disp2, fill=INK)
d.text((140, 432), '\u09aa\u09b6\u09cd\u099a\u09bf\u09ae\u09ac\u0999\u09cd\u0997\u09c7\u09b0 \u09ac\u09be\u09b8 \u099f\u09be\u0987\u09ae \u099f\u09c7\u09ac\u09b2', font=f_bn, fill=AMBER_INK)

# stats pills
pill_y = 505

def pill(x, parts):
    total = sum(d.textlength(t, font=f) for t, f in parts) + 44
    d.rounded_rectangle([x, pill_y, x + total, pill_y + 52], 26, outline=AMBER, width=3)
    cx = x + 22
    for t, f in parts:
        d.text((cx, pill_y + 13), t, font=f, fill=AMBER_INK)
        cx += d.textlength(t, font=f)
    return x + total + 22

x = pill(140, [('330+ ROUTES', f_mono)])
x = pill(x, [('460+ PAGES', f_mono)])
pill(x, [('EN \u00b7 ', f_mono), ('\u09ac\u09be\u0982\u09b2\u09be', f_bn_s)])

img = img.convert('RGB').quantize(colors=128, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
img.save('og-image.png', optimize=True)
print('og-image.png generated')
