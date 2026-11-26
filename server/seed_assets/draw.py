"""Draws the demo product illustrations used by seed.py.

    uv run python seed_assets/draw.py

Images are drawn at 2x and downsampled for smooth edges. HOTSPOTS holds the
part coordinates (as % of width / height) that seed.py places dots at.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).parent
W, H, S = 1200, 800, 2  # final size and supersampling factor


def canvas(bg=(246, 248, 252)):
    img = Image.new("RGB", (W * S, H * S), bg)
    return img, ImageDraw.Draw(img)


def P(*pts):
    return [(x * S, y * S) for x, y in pts]


def shadow(img, box, blur=30, color=(0, 0, 0, 60)):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse([v * S for v in box], fill=color)
    layer = layer.filter(ImageFilter.GaussianBlur(blur * S))
    img.paste(layer, (0, 0), layer)


def finish(img, name):
    img.resize((W, H), Image.LANCZOS).save(OUT / name, optimize=True)


def shoe():
    img, d = canvas()
    shadow(img, (150, 590, 1100, 650))
    # outsole + tread
    d.rounded_rectangle([v * S for v in (140, 560, 1090, 625)], radius=30 * S, fill=(52, 56, 64))
    for x in range(180, 1060, 34):
        d.line(P((x, 600), (x + 16, 622)), fill=(36, 39, 45), width=6 * S)
    # midsole
    d.rounded_rectangle([v * S for v in (150, 525, 1085, 570)], radius=22 * S, fill=(238, 236, 230))
    # leather upper
    upper = P((175, 535), (165, 330), (205, 262), (320, 248), (410, 300), (500, 290), (560, 268),
              (700, 300), (860, 372), (990, 420), (1062, 470), (1078, 535))
    d.polygon(upper, fill=(140, 86, 48))
    # toe cap (lighter)
    d.polygon(P((900, 392), (990, 420), (1062, 470), (1078, 535), (890, 535), (860, 470)), fill=(176, 118, 72))
    d.line(P((900, 392), (860, 470), (890, 535)), fill=(110, 66, 36), width=4 * S)
    # heel counter + heel tab
    d.polygon(P((175, 535), (165, 330), (205, 262), (250, 258), (290, 535)), fill=(118, 70, 38))
    d.rounded_rectangle([v * S for v in (196, 196, 236, 280)], radius=14 * S, fill=(60, 60, 70))
    d.rounded_rectangle([v * S for v in (206, 208, 226, 262)], radius=8 * S, fill=(246, 248, 252))
    # collar padding
    d.line(P((205, 264), (320, 252), (408, 302)), fill=(92, 54, 30), width=14 * S)
    # tongue
    d.polygon(P((540, 286), (596, 160), (666, 170), (668, 300)), fill=(160, 102, 60))
    d.line(P((596, 160), (666, 170)), fill=(110, 66, 36), width=6 * S)
    # stitching
    for x in range(200, 1050, 26):
        t = (x - 200) / 850
        y = 512 - 6 * t
        d.line(P((x, y), (x + 13, y)), fill=(232, 210, 170), width=3 * S)
    # eyelets + laces
    top = [(565, 292), (612, 300), (660, 314), (708, 330), (756, 346)]
    bottom = [(560, 352), (610, 366), (660, 382), (710, 398), (760, 412)]
    for a, b in zip(top, bottom[1:]):
        d.line(P(a, b), fill=(250, 250, 250), width=8 * S)
    for a, b in zip(bottom, top[1:]):
        d.line(P(a, b), fill=(235, 235, 235), width=8 * S)
    for pt in top + bottom:
        x, y = pt
        d.ellipse([v * S for v in (x - 9, y - 9, x + 9, y + 9)], fill=(205, 170, 90), outline=(90, 60, 30), width=2 * S)
    d.line(P((568, 292), (540, 230), (520, 200)), fill=(250, 250, 250), width=7 * S)
    d.line(P((570, 292), (600, 236), (630, 222)), fill=(250, 250, 250), width=7 * S)
    finish(img, "shoe.png")


def phone():
    img, d = canvas()
    for cx in (370, 830):
        shadow(img, (cx - 180, 700, cx + 180, 760))
    # front
    d.rounded_rectangle([v * S for v in (220, 70, 520, 720)], radius=48 * S, fill=(30, 32, 38))
    # wallpaper, clipped to the rounded screen
    screen_box = [v * S for v in (236, 86, 504, 704)]
    wall = Image.new("RGB", img.size, (60, 110, 200))
    wd = ImageDraw.Draw(wall)
    for i, col in enumerate([(88, 140, 230), (120, 170, 240), (150, 200, 250)]):
        wd.ellipse([v * S for v in (180 + i * 60, 260 + i * 90, 560 - i * 40, 640 + i * 20)], fill=col)
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(screen_box, radius=38 * S, fill=255)
    img.paste(wall, (0, 0), mask)
    d.rounded_rectangle([v * S for v in (330, 100, 410, 124)], radius=12 * S, fill=(18, 18, 22))
    d.rounded_rectangle([v * S for v in (320, 690, 420, 700)], radius=4 * S, fill=(18, 18, 22))
    for x in range(330, 412, 12):
        d.ellipse([v * S for v in (x, 708, x + 6, 714)], fill=(90, 90, 100))
    d.rounded_rectangle([v * S for v in (214, 210, 222, 280)], radius=3 * S, fill=(70, 72, 80))
    d.rounded_rectangle([v * S for v in (518, 190, 526, 240)], radius=3 * S, fill=(70, 72, 80))
    # back
    d.rounded_rectangle([v * S for v in (680, 70, 980, 720)], radius=48 * S, fill=(150, 160, 175))
    d.rounded_rectangle([v * S for v in (690, 80, 970, 710)], radius=40 * S, fill=(196, 206, 222))
    d.rounded_rectangle([v * S for v in (712, 104, 862, 274)], radius=34 * S, fill=(40, 42, 50))
    for cx, cy, r in ((752, 150, 30), (822, 150, 30), (752, 226, 30)):
        d.ellipse([v * S for v in (cx - r, cy - r, cx + r, cy + r)], fill=(20, 20, 24), outline=(110, 115, 125), width=4 * S)
        d.ellipse([v * S for v in (cx - 12, cy - 12, cx + 12, cy + 12)], fill=(50, 70, 110))
    d.ellipse([v * S for v in (810, 214, 834, 238)], fill=(250, 240, 200))
    d.rounded_rectangle([v * S for v in (760, 360, 900, 560)], radius=18 * S, outline=(170, 180, 196), width=4 * S)
    d.line(P((815, 430), (800, 465), (830, 465), (812, 505)), fill=(170, 180, 196), width=6 * S)
    finish(img, "phone.png")


def headphones():
    img, d = canvas()
    shadow(img, (300, 700, 900, 760))
    d.arc([v * S for v in (300, 80, 900, 700)], start=180, end=360, fill=(45, 48, 56), width=46 * S)
    d.arc([v * S for v in (318, 98, 882, 682)], start=200, end=340, fill=(90, 94, 104), width=18 * S)
    for x in (300, 900):
        d.rounded_rectangle([v * S for v in (x - 18, 380, x + 18, 470)], radius=10 * S, fill=(150, 155, 165))
    for cx in (300, 900):
        d.ellipse([v * S for v in (cx - 120, 430, cx + 120, 700)], fill=(38, 40, 48))
        inner = 1 if cx < 600 else -1
        d.ellipse([v * S for v in (cx - 90 + 40 * inner, 460, cx + 90 + 40 * inner, 670)], fill=(110, 112, 122))
        d.ellipse([v * S for v in (cx - 60 + 40 * inner, 490, cx + 60 + 40 * inner, 640)], fill=(70, 72, 80))
    d.ellipse([v * S for v in (240, 540, 270, 570)], fill=(60, 200, 120))
    d.line(P((215, 640), (150, 700), (110, 760)), fill=(40, 40, 46), width=10 * S)
    d.line(P((900, 640), (960, 700), (1010, 700)), fill=(60, 62, 70), width=12 * S)
    d.ellipse([v * S for v in (998, 684, 1034, 718)], fill=(30, 30, 34))
    finish(img, "headphones.png")


if __name__ == "__main__":
    shoe()
    phone()
    headphones()
    print("Wrote shoe.png, phone.png, headphones.png to", OUT)
