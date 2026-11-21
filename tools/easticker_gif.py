"""Render assets/projects/easticker.gif: Easticker stickers popping onto a
lavender scene, captured frame by frame with headless Chrome.

    python3 tools/easticker_gif.py [path/to/easticker] [path/to/eastikcer_site]
"""
import subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
LIB = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT.parent / "easticker")
SITE = Path(sys.argv[2] if len(sys.argv) > 2 else ROOT.parent / "eastikcer_site")
OUT = ROOT / "assets" / "projects" / "easticker.gif"

LOOP = 4.0       # seconds
FRAMES = 40
# sticker, x, y, width, resting rotation (deg), stagger (s)
STICKERS = [
    ("saudi-arabia/dallah.svg",   392,  18, 118,  8, 0.00),
    ("algeria/algeria-flag.svg",  506,  30,  84, -9, 0.18),
    ("saudi-arabia/camel.svg",    318, 132, 150, -6, 0.36),
    ("algeria/mint-teapot.svg",   474, 140, 104,  7, 0.54),
    ("algeria/yaz.svg",           322,  22,  70, -12, 0.72),
    ("saudi-arabia/dates.svg",    250, 214,  78,  10, 0.90),
]


def keyframes(i, rot, delay):
    a = delay / LOOP * 100
    pop, settle = a + 6, a + 10
    out_start, out_end = 88 + i * 1.2, 94 + i * 1.2
    return f"""@keyframes s{i}{{
  0%,{a:.2f}%{{transform:translateY(-40px) scale(.2) rotate({rot-30}deg);opacity:0}}
  {pop:.2f}%{{transform:translateY(4px) scale(1.12) rotate({rot+4}deg);opacity:1}}
  {settle:.2f}%{{transform:translateY(0) scale(1) rotate({rot}deg);opacity:1}}
  {(settle+out_start)/2:.2f}%{{transform:translateY(-6px) scale(1.02) rotate({rot+3}deg);opacity:1}}
  {out_start:.2f}%{{transform:translateY(0) scale(1) rotate({rot}deg);opacity:1}}
  {out_end:.2f}%,100%{{transform:translateY(10px) scale(.3) rotate({rot+25}deg);opacity:0}}
}}"""


def page():
    css, imgs = [], []
    for i, (src, x, y, w, rot, d) in enumerate(STICKERS):
        css.append(keyframes(i, rot, d))
        imgs.append(f'<img class="st" src="file://{LIB / "stickers" / src}" '
                    f'style="left:{x}px;top:{y}px;width:{w}px;animation:s{i} {LOOP}s linear infinite">')
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0}}
.scene{{position:relative;width:600px;height:315px;overflow:hidden;
  background:linear-gradient(180deg,#f7f1fd 0%,#eedff9 60%,#e2c9f3 100%);font-family:'Outfit','Noto Sans',sans-serif}}
.dune{{position:absolute;left:-40px;right:-40px;border-radius:50%}}
.d1{{bottom:-120px;height:190px;background:#dcbcf0}}
.d2{{bottom:-150px;height:190px;left:200px;background:#c99ae6}}
.logo{{position:absolute;left:30px;top:30px;width:170px}}
h1{{position:absolute;left:30px;top:94px;margin:0;font-size:31px;line-height:1.08;color:#1d0b2b;font-weight:800;letter-spacing:-.5px}}
p{{position:absolute;left:30px;top:174px;margin:0;width:230px;font-size:13.5px;line-height:1.45;color:#5a4569}}
.pill{{position:absolute;left:30px;top:242px;padding:6px 12px;border-radius:999px;background:#1d0b2b;color:#f3e8ff;
  font:600 12.5px ui-monospace,'DejaVu Sans Mono',monospace}}
.st{{position:absolute;transform-origin:50% 60%;filter:drop-shadow(0 6px 8px rgba(60,20,90,.22))}}
{''.join(css)}
</style></head><body><div class="scene">
<div class="dune d1"></div><div class="dune d2"></div>
<img class="logo" src="file://{SITE / 'public/brand/full-logo.svg'}">
<h1>Stickers with<br>an Arabic soul.</h1>
<p>Hand-drawn React stickers: drop them in, drag them around, peel them off.</p>
<div class="pill">$ npm i easticker</div>
{''.join(imgs)}
</div>
<script>
const t = parseFloat(location.hash.slice(1)) || 0;
addEventListener('load', () => document.getAnimations().forEach(a => {{ a.pause(); a.currentTime = t; }}));
</script></body></html>"""


def main():
    tmp = Path(tempfile.mkdtemp())
    html = tmp / "scene.html"
    html.write_text(page())
    frames = []
    for k in range(FRAMES):
        t = LOOP * 1000 * k / FRAMES
        png = tmp / f"f{k:03}.png"
        subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--allow-file-access-from-files", "--force-device-scale-factor=2",
                        "--window-size=600,315", "--virtual-time-budget=800",
                        f"--screenshot={png}", f"file://{html}#{t}"],
                       check=True, capture_output=True)
        im = Image.open(png).convert("RGB").resize((600, 315), Image.LANCZOS)
        frames.append(im)
    pal = frames[FRAMES // 2].quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    q[0].save(OUT, save_all=True, append_images=q[1:], duration=int(LOOP * 1000 / FRAMES), loop=0, optimize=True)
    frames[FRAMES // 2].save(tmp / "mid.png")
    print(OUT, f"{OUT.stat().st_size/1024:.0f} KB", tmp / "mid.png")


if __name__ == "__main__":
    main()
