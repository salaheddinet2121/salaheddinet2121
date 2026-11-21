"""Render assets/banner.gif: the Dither shader (fbm Perlin waves + Bayer 8x8)
ported to numpy, in a blue palette, with the name written over it in
ASCII dither blocks. The wave offset travels on a circle so the GIF loops.

    python3 tools/banner.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "banner.gif"

W, H = 1200, 380          # output size in px
CELL = 3                  # dither pixel size
FRAMES = 48
FRAME_MS = 70
LOOP_RADIUS = 0.35        # how far the wave offset travels per loop

# ink, deep blue, blue, pale blue
PALETTE = ["#10102B", "#1F67DA", "#448FF4", "#DEEFFF"]
TEXT = "#F9FCFF"
MUTED = "#8FB8F8"

WAVE_FREQ, WAVE_AMP = 3.0, 0.3
CONTRAST, BRIGHTNESS = 1.05, -0.04

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


# ---- shader port -----------------------------------------------------------
def mod289(x):
    return x - np.floor(x * (1.0 / 289.0)) * 289.0


def permute(x):
    return mod289(((x * 34.0) + 1.0) * x)


def fade(t):
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def cnoise(px, py):
    pix, piy = np.floor(px), np.floor(py)
    pfx, pfy = px - pix, py - piy
    ix = mod289(np.stack([pix, pix + 1, pix, pix + 1]))
    iy = mod289(np.stack([piy, piy, piy + 1, piy + 1]))
    fx = np.stack([pfx, pfx - 1, pfx, pfx - 1])
    fy = np.stack([pfy, pfy, pfy - 1, pfy - 1])
    i = permute(permute(ix) + iy)
    gx = (i * (1.0 / 41.0)) % 1.0 * 2.0 - 1.0
    gy = np.abs(gx) - 0.5
    gx = gx - np.floor(gx + 0.5)
    norm = 1.79284291400159 - 0.85373472095314 * (gx * gx + gy * gy)
    gx, gy = gx * norm, gy * norm
    n = gx * fx + gy * fy  # n00, n10, n01, n11
    ux, uy = fade(pfx), fade(pfy)
    nx0 = n[0] + (n[1] - n[0]) * ux
    nx1 = n[2] + (n[3] - n[2]) * ux
    return 2.3 * (nx0 + (nx1 - nx0) * uy)


def fbm(px, py):
    value = np.zeros_like(px)
    amp = 1.0
    for _ in range(4):
        value += amp * np.abs(cnoise(px, py))
        px, py = px * WAVE_FREQ, py * WAVE_FREQ
        amp *= WAVE_AMP
    return value


BAYER8 = np.array([
    0, 48, 12, 60, 3, 51, 15, 63, 32, 16, 44, 28, 35, 19, 47, 31,
    8, 56, 4, 52, 11, 59, 7, 55, 40, 24, 36, 20, 43, 27, 39, 23,
    2, 50, 14, 62, 1, 49, 13, 61, 34, 18, 46, 30, 33, 17, 45, 29,
    10, 58, 6, 54, 9, 57, 5, 53, 42, 26, 38, 22, 41, 25, 37, 21,
]).reshape(8, 8) / 64.0


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ---- text: name as ASCII dither blocks --------------------------------------
def ascii_blocks(word, px_height=11):
    """Rasterise `word` small, then map coverage to block characters."""
    font = ImageFont.truetype(SANS_BOLD, px_height + 3)
    box = font.getbbox(word)
    img = Image.new("L", (box[2] - box[0] + 2, px_height + 2), 0)
    ImageDraw.Draw(img).text((1 - box[0], 1 - box[1]), word, font=font, fill=255)
    a = np.asarray(img) / 255.0
    ramp = " ░▒▓█"
    return ["".join(ramp[min(4, int(v * 4.99))] for v in row).rstrip() for row in a]


def text_layer(cols, rows):
    """Return (RGBA overlay, clearing mask in cell space)."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    lines = ascii_blocks("SALAH EDDINE")
    glyph = ImageFont.truetype(MONO, 9)
    cw, ch = 7, 9
    block_w = max(len(l) for l in lines) * cw
    block_h = len(lines) * ch
    x0 = (W - block_w) // 2
    y0 = 92
    for r, line in enumerate(lines):
        for c, chx in enumerate(line):
            if chx != " ":
                draw.text((x0 + c * cw, y0 + r * ch), chx, font=glyph, fill=TEXT)

    sub = ImageFont.truetype(MONO_BOLD, 17)
    small = ImageFont.truetype(MONO, 14)
    rows_txt = [
        (sub, "> full-stack web dev · devops enthusiast · ai adopter_", TEXT),
        (small, "automation · security · arabic ui design · creative code  //  montpellier, fr", MUTED),
    ]
    y = y0 + block_h + 26
    half = max(block_w, *(draw.textlength(t, font=f) for f, t, _ in rows_txt)) / 2
    for font, txt, color in rows_txt:
        w = draw.textlength(txt, font=font)
        draw.text(((W - w) / 2, y), txt, font=font, fill=color)
        y += 28

    # clearing: where the text sits, the dither field gets "erased"
    m = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(m)
    md.rounded_rectangle((W / 2 - half - 60, y0 - 34, W / 2 + half + 60, y + 24), radius=40, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(38)).resize((cols, rows), Image.BILINEAR)
    return overlay, np.asarray(m) / 255.0


# ---- render -----------------------------------------------------------------
def main():
    cols, rows = W // CELL, H // CELL
    aspect = W / H
    jj, ii = np.mgrid[0:rows, 0:cols].astype(np.float64)
    ux = (ii / cols - 0.5) * aspect
    uy = (jj / rows - 0.5)
    thr = BAYER8[(jj % 8).astype(int), (ii % 8).astype(int)] - 0.25

    overlay, clearing = text_layer(cols, rows)
    pal = np.array([hex_rgb(c) for c in PALETTE], dtype=np.uint8)
    n = len(PALETTE)

    frames = []
    for k in range(FRAMES):
        a = 2 * np.pi * k / FRAMES
        ox, oy = LOOP_RADIUS * np.cos(a), LOOP_RADIUS * np.sin(a)
        inner = fbm(ux - ox, uy - oy)
        f = fbm(ux + inner, uy + inner)
        f -= 0.7 * clearing                      # the "erase" effect
        f = (f - 0.5) * CONTRAST + 0.5 + BRIGHTNESS
        f = np.clip(f, 0, 1)
        v = f + thr / (n - 1)
        bias = 0.2 * (1 - np.clip((v - 0.45) / 0.35, 0, 1) ** 2 * (3 - 2 * np.clip((v - 0.45) / 0.35, 0, 1)))
        v = np.clip(v - bias, 0, 1)
        idx = np.floor(v * (n - 1) + 0.5).astype(int)
        img = Image.fromarray(pal[idx], "RGB").resize((W, H), Image.NEAREST)
        img.paste(overlay, (0, 0), overlay)
        frames.append(img.quantize(colors=32, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=FRAME_MS,
                   loop=0, optimize=True, disposal=1)
    print(f"{OUT} {OUT.stat().st_size / 1024:.0f} KB")
    frames[0].convert("RGB").save(OUT.with_name("banner-frame.png"))


if __name__ == "__main__":
    main()
