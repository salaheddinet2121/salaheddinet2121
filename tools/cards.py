"""Build the README cards in light and dark versions:
assets/about-{light,dark}.svg and assets/experience-{light,dark}.svg.

Design: grey shell + white card, tight Geist headlines, one keyword underlined
with a pen stroke, soft neutral tiles and pills. Geist (SIL OFL) is embedded in
each SVG so it renders the same for every visitor.

    python3 tools/cards.py
"""
import base64
import io
from functools import lru_cache
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "tools" / "fonts" / "Geist-Variable.woff2"
FONT_B64 = base64.b64encode(FONT.read_bytes()).decode()

# ---- content ------------------------------------------------------------------
ABOUT = {
    "status": "Open to opportunities",
    "where": "Montpellier, France",
    "headline": ["I build web products end to end,", "and {automate} everything around them."],
    "lede": [
        "DevOps enthusiast, full-stack developer and software engineer. Speaks Arabic, French, English.",
        "Into automation, AI agents and security, with a soft spot for Arabic UI.",
    ],
    "facts": ["20+ projects delivered", "3 internships", "University of Montpellier"],
}

EXPERIENCE = [
    {"company": "Octodet", "role": "Software Developer", "place": "Remote", "kind": "Internship",
     "date": "Jan → Jun 2025",
     "points": ["Automation, prompt engineering and AI agents (LLMs, LLMOps, web scraping)",
                "Security and vulnerability management",
                "Built Scruti, a security project"],
     "tags": ["Python", "osquery", "Elasticsearch", "Ansible", "LLMs"]},
    {"company": "GTFT", "role": "Software Engineer", "place": "Illizi, Algeria", "kind": "Internship",
     "date": "Dec 2024",
     "points": ["Network infrastructure and virtualization for server management",
                "Server replication, risk prevention and disaster recovery",
                "Software management and deployment"],
     "tags": ["Networking", "Virtualization", "Replication"]},
    {"company": "Sonatrach", "role": "Software Engineer", "place": "Skikda, Algeria", "kind": "Internship",
     "date": "Jul 2024",
     "points": ["Automated backup scripts for the company servers",
                "Oracle database administration: monitoring, maintenance, security",
                "Supported the infrastructure team on enterprise applications"],
     "tags": ["Shell", "Oracle", "Sysadmin"]},
]

THEMES = {
    "light": dict(shell="#F5F5F5", card="#FFFFFF", ink="#161513", soft="#2E2C28", muted="#57544D",
                  tile="#F2F2F1", line="#E8E8E6", pen="#448FF4", ok="#269A5A", okbg="#E8F5EE", glow=None),
    "dark": dict(shell="#141417", card="#0B0B0E", ink="#F5F5F4", soft="#D9D8D4", muted="#8B877D",
                 tile="#18181C", line="#232329", pen="#448FF4", ok="#3FB950", okbg="#10241A", glow="#2B4BFF"),
}

W = 900
SHELL = 12      # grey shell around the white card
PAD = 44        # card padding
TRACK = -0.035  # headline letter-spacing, em


# ---- text measuring with the real font -----------------------------------------------
@lru_cache(maxsize=None)
def face(weight):
    f = TTFont(io.BytesIO(FONT.read_bytes()))
    return instantiateVariableFont(f, {"wght": weight})


def width(text, size, weight=400, track=0.0):
    f = face(weight)
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    adv = sum(hmtx[cmap.get(ord(c), cmap[ord("?")])][0] for c in text)
    return adv * size / upm + track * size * len(text)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---- primitives -------------------------------------------------------------------
def text(x, y, s, size, weight, fill, track=0.0, anchor="start"):
    ls = f' letter-spacing="{track * size:.2f}"' if track else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}"'
            f'{ls} text-anchor="{anchor}">{esc(s)}</text>')


def pill(x, y, label, t, size=14, weight=500, dot=None, h=34, fill=None, color=None):
    pad = 16
    dw = 16 if dot else 0
    w = width(label, size, weight) + 2 * pad + dw
    out = f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{fill or t["tile"]}"/>'
    if dot:
        out += f'<circle cx="{x + pad + 4:.1f}" cy="{y + h / 2}" r="4.5" fill="{dot}"/>'
    out += text(x + pad + dw, y + h / 2 + size * 0.36, label, size, weight, color or t["soft"])
    return w, out


def check(cx, cy, t):
    return (f'<circle cx="{cx}" cy="{cy}" r="10" fill="{t["ok"]}"/>'
            f'<path d="M{cx - 4.2} {cy + .2} l2.9 2.9 l5.6 -5.8" fill="none" stroke="#fff" stroke-width="2"'
            f' stroke-linecap="round" stroke-linejoin="round"/>')


def pen(x1, x2, y, t):
    """Hand-drawn underline: a slightly bowed, tapered stroke."""
    w = x2 - x1
    return (f'<path d="M{x1 - 2:.1f} {y + 1.5:.1f} C {x1 + w * .3:.1f} {y - 2.5:.1f}, {x1 + w * .65:.1f} {y - 1:.1f},'
            f' {x2 + 4:.1f} {y - 3.5:.1f}" fill="none" stroke="{t["pen"]}" stroke-width="5" stroke-linecap="round"/>')


def flag_dz(x, y):
    return (f'<g transform="translate({x} {y})"><rect width="9" height="14" fill="#006633"/>'
            f'<rect x="9" width="9" height="14" fill="#FFF"/><circle cx="9" cy="7" r="4" fill="#D21034"/>'
            f'<circle cx="10.1" cy="7" r="3.2" fill="#FFF"/><path d="M11.4 5.5l.42 1 1.08.05-.85.66.3 1.05-.93-.62-.9.62.3-1.05'
            f'-.85-.66 1.08-.05z" fill="#D21034"/></g>')


def flag_fr(x, y):
    return (f'<g transform="translate({x} {y})"><rect width="6" height="14" fill="#1F4DD8"/>'
            f'<rect x="6" width="6" height="14" fill="#FFF"/><rect x="12" width="6" height="14" fill="#E63946"/></g>')


def frame(H, t, body, label):
    glow = ""
    if t["glow"]:
        glow = (f'<radialGradient id="g" cx="88%" cy="0%" r="70%"><stop offset="0" stop-color="{t["glow"]}" stop-opacity=".28"/>'
                f'<stop offset="1" stop-color="{t["glow"]}" stop-opacity="0"/></radialGradient>')
    cw, ch = W - 2 * SHELL, H - 2 * SHELL
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(label)}">
<defs><style>@font-face{{font-family:Geist;src:url(data:font/woff2;base64,{FONT_B64}) format('woff2');font-weight:100 900}}
text{{font-family:Geist,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif}}</style>
<filter id="s" x="-5%" y="-5%" width="110%" height="120%"><feDropShadow dx="0" dy="6" stdDeviation="10" flood-color="#000" flood-opacity="{.06 if not t['glow'] else .4}"/></filter>{glow}</defs>
<rect width="{W}" height="{H}" rx="28" fill="{t['shell']}"/>
<rect x="{SHELL}" y="{SHELL}" width="{cw}" height="{ch}" rx="20" fill="{t['card']}" filter="url(#s)"/>
{f'<rect x="{SHELL}" y="{SHELL}" width="{cw}" height="{ch}" rx="20" fill="url(#g)"/>' if t['glow'] else ''}
{body}
</svg>"""


# ---- about ------------------------------------------------------------------------
def about(t):
    x0, inner = SHELL + PAD, W - 2 * (SHELL + PAD)
    y = SHELL + PAD
    parts = []

    w, p = pill(x0, y, ABOUT["status"], t, dot=t["ok"], fill=t["okbg"], color=t["ok"] if t["glow"] else "#1E7A47")
    parts.append(p)
    _, p = pill(x0 + w + 10, y, ABOUT["where"], t, dot=None)
    parts.append(p)
    # flags after the location pill: from Algeria, now in France
    fx = x0 + w + 10 + width(ABOUT["where"], 14, 500) + 32 + 8
    parts.append(flag_dz(fx, y + 10) + text(fx + 24, y + 21.5, "→", 13, 500, t["muted"]) + flag_fr(fx + 42, y + 10))

    # headline, sized so the longest line fits
    lines = [l.replace("{", "").replace("}", "") for l in ABOUT["headline"]]
    size = min(46, int(inner / max(width(l, 1, 600, TRACK) for l in lines)))
    y += 34 + 30 + size
    for raw, plain in zip(ABOUT["headline"], lines):
        parts.append(text(x0, y, plain, size, 600, t["ink"], TRACK))
        if "{" in raw:
            pre, key = raw.split("{")[0], raw.split("{")[1].split("}")[0]
            a = x0 + width(pre, size, 600, TRACK)
            parts.insert(0, pen(a, a + width(key, size, 600, TRACK), y + size * 0.2, t))
        y += size * 1.12
    y += 10
    for l in ABOUT["lede"]:
        parts.append(text(x0, y, l, 17, 400, t["muted"]))
        y += 26
    y += 18

    # facts: tiles with a check
    x = x0
    for f in ABOUT["facts"]:
        tw = width(f, 14.5, 500) + 56
        if x + tw > x0 + inner:
            x, y = x0, y + 52
        parts.append(f'<rect x="{x:.1f}" y="{y}" width="{tw:.1f}" height="42" rx="14" fill="{t["tile"]}"/>'
                     + check(x + 22, y + 21, t) + text(x + 40, y + 26, f, 14.5, 500, t["ink"]))
        x += tw + 10
    H = int(y + 42 + PAD + SHELL)
    label = (f"About me. {ABOUT['status']}. {ABOUT['where']}, originally from Algeria. "
             + " ".join(lines) + " " + " ".join(ABOUT["lede"]) + " " + ". ".join(ABOUT["facts"]) + ".")
    return frame(H, t, "\n".join(parts), label)


# ---- experience -------------------------------------------------------------------------
def experience(t):
    x0 = SHELL + PAD
    col = x0 + 190
    y = SHELL + PAD
    parts = []
    for i, e in enumerate(EXPERIENCE):
        if i:
            parts.append(f'<line x1="{x0}" y1="{y - 26}" x2="{W - SHELL - PAD}" y2="{y - 26}" stroke="{t["line"]}"/>')
        _, p = pill(x0, y - 2, e["date"], t, size=13.5, weight=500, h=32)
        parts.append(p)
        parts.append(text(x0 + 2, y + 52, e["kind"], 13.5, 400, t["muted"]))
        parts.append(text(col, y + 22, e["company"], 26, 600, t["ink"], TRACK))
        parts.append(text(col, y + 48, f'{e["role"]} · {e["place"]}', 15, 400, t["muted"]))
        py = y + 84
        for pt in e["points"]:
            parts.append(f'<rect x="{col}" y="{py - 6}" width="8" height="2" rx="1" fill="{t["pen"]}"/>'
                         + text(col + 18, py, pt, 15.5, 400, t["soft"]))
            py += 27
        x = col
        py += 2
        for tag in e["tags"]:
            w, p = pill(x, py, tag, t, size=13, weight=500, h=30)
            parts.append(p)
            x += w + 8
        y = py + 30 + 56
    H = int(y - 56 + PAD + SHELL)
    label = "Experience. " + " ".join(
        f'{e["role"]} at {e["company"]}, {e["kind"].lower()}, {e["place"]}, {e["date"]}: ' + "; ".join(e["points"]) + "."
        for e in EXPERIENCE)
    return frame(H, t, "\n".join(parts), label)


def main():
    for name, t in THEMES.items():
        (ROOT / f"assets/about-{name}.svg").write_text(about(t))
        (ROOT / f"assets/experience-{name}.svg").write_text(experience(t))
    print("assets/about-{light,dark}.svg  assets/experience-{light,dark}.svg")


if __name__ == "__main__":
    main()
