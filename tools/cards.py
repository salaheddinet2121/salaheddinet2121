"""The profile's design system: every README section is a card drawn from the
same tokens and primitives, in a light and a dark version.

  01 About · 02 Experience · 03 Featured builds · 04 Client work
  05 Side projects (animated GIF) · 06 Stack · 07 Certifications
  (08 Activity is drawn by scripts/stats.mjs with the same tokens.)

One flat card per section: no frame around cards, no cards inside cards.
Inside a card, structure comes from hairlines, type and pills only.

    python3 tools/cards.py            # all cards
    python3 tools/cards.py --no-gif   # skip the side-projects GIF (slow)
"""
import base64
import io
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw, ImageSequence

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "tools" / "fonts" / "Geist-Variable.woff2"
FONT_B64 = base64.b64encode(FONT.read_bytes()).decode()
ICONS = ROOT / "tools" / "skillicons"

# =================================================================== tokens
THEMES = {
    "light": dict(page="#FFFFFF", card="#FFFFFF", border="#E4E4E0", hair="#ECECE9", ink="#161513", soft="#2E2C28",
                  muted="#6B675F", pill="#F2F2F0", blue="#448FF4", ok="#1E7A47", okdot="#269A5A", okbg="#E8F5EE", glow=None),
    "dark": dict(page="#0D1117", card="#0B0B0E", border="#26262C", hair="#1E1E24", ink="#F5F5F4", soft="#D9D8D4",
                 muted="#8B877D", pill="#18181D", blue="#448FF4", ok="#7EE2A0", okdot="#3FB950", okbg="#10241A", glow="#2B4BFF"),
}
W = 900          # card width
PAD = 40         # card padding
RADIUS = 18
TRACK = -0.035   # display letter-spacing (em)
IN = W - 2 * PAD

# =================================================================== content
ABOUT = {
    "status": "Open to opportunities",
    "headline": ["I build web products end to end,", "and {automate} everything around them."],
    "lede": "DevOps enthusiast, full-stack developer and software engineer.",
    "now": {"label": "Now", "name": "Velytrix", "logo": "velytrix.png", "status": "Current",
            "what": "My studio: landing pages and local SEO for small businesses", "link": "velytrix.fr · launching soon"},
    "facts": [
        ("Based in", "Montpellier, France", "from Algeria", True),
        ("Focus", "Automation, AI agents", "and security", False),
        ("Track record", "20+ projects", "delivered for clients", False),
        ("Languages", "Arabic, French", "and English", False),
    ],
}

EXPERIENCE = [
    {"company": "Octodet", "role": "Software Developer", "place": "Remote", "kind": "Internship", "date": "Jan → Jun 2025",
     "points": ["Automation, prompt engineering and AI agents (LLMs, LLMOps, web scraping)",
                "Security and vulnerability management",
                "Built Scruti, a security project"],
     "tags": ["Python", "osquery", "Elasticsearch", "Ansible", "LLMs"]},
    {"company": "GTFT", "role": "Software Engineer", "place": "Illizi, Algeria", "kind": "Internship", "date": "Dec 2024",
     "points": ["Network infrastructure and virtualization for server management",
                "Server replication, risk prevention and disaster recovery",
                "Software management and deployment"],
     "tags": ["Networking", "Virtualization", "Replication"]},
    {"company": "Sonatrach", "role": "Software Engineer", "place": "Skikda, Algeria", "kind": "Internship", "date": "Jul 2024",
     "points": ["Automated backup scripts for the company servers",
                "Oracle database administration: monitoring, maintenance, security",
                "Supported the infrastructure team on enterprise applications"],
     "tags": ["Shell", "Oracle", "Sysadmin"]},
]

BUILDS = [
    {"name": "Scrollia Automation", "status": ("In production", "ok"),
     "what": "Social media pipeline for the Scrollia agency: pulls content from Google Drive, writes captions "
             "with AI, renders branded thumbnails, then schedules and publishes to several platforms. "
             "A Next.js dashboard reviews and retries posts.",
     "tags": ["Python", "FastAPI", "Next.js", "LLMs", "Docker", "Coolify"]},
    {"name": "Scruti", "status": ("Built at Octodet", "blue"),
     "what": "Security and vulnerability management project, built during my internship at Octodet.",
     "tags": ["osquery", "Elasticsearch", "Ansible", "Python", "LLMs"]},
]

CLIENTS = [
    {"name": "Scrollia", "logo": "scrollia.png", "what": "Agency site for branding, growth and SEO, in French and English", "note": "scrollia.fr ↗"},
    {"name": "Courage Formation", "logo": "courage-formation.png", "what": "Training centre website and lead funnel", "note": "courageformation.fr ↗"},
    {"name": "Paroliamo", "logo": "paroliamo.png", "what": "Training centre website in four languages", "note": "4 languages"},
]
CLIENTS_MORE = "And 15+ more sites, landing pages, CRMs and automations for training centres, consultants and local businesses."

SIDE = [
    {"name": "Florii", "ar": "فلوري", "logo": "florii-logo.svg", "gif": "florii.gif",
     "what": "Type a name and its letters grow into a garden, Arabic first."},
    {"name": "Easticker", "ar": "إيستيكر", "logo": "easticker-logo.svg", "gif": "easticker.gif",
     "what": "Hand-drawn React stickers with an Arabic soul."},
]
SIDE_SOON = "More Arabic UI projects on the way."

STACK = [
    ("Web", ["ts", "js", "react", "nextjs", "astro", "tailwind", "nodejs", "html", "css"],
     "TypeScript, JavaScript, React, Next.js, Astro, Tailwind, Node.js, HTML, CSS"),
    ("DevOps", ["docker", "ansible", "githubactions", "cloudflare", "linux", "bash", "git"],
     "Docker, Coolify, Ansible, GitHub Actions, Cloudflare Workers, Linux, Shell, Git"),
    ("Security", ["elasticsearch"], "osquery, Elasticsearch, vulnerability management"),
    ("AI & automation", ["python"], "Python, LLMs, AI agents, CrewAI, prompt engineering, LLMOps, web scraping"),
    ("Data & cloud", ["sqlite", "aws", "azure"], "Oracle, SQLite, AWS, Azure"),
    ("Design", ["figma"], "Figma, Canva, UI/UX, design systems, branding, Arabic (RTL), French and English layouts"),
]

CERTS = [
    ("Nov 2025", "Evaluating AI Agents: From Metrics to Real-World Impact", "365 Data Science"),
    ("Nov 2025", "Intro to Microsoft Azure", "365 Data Science"),
    ("Feb 2025", "Multi Agent Systems", "CrewAI"),
    ("Dec 2024", "AWS Academy Graduate: Cloud Foundations", "AWS Academy"),
]


# =================================================================== measuring
@lru_cache(maxsize=None)
def face(weight):
    return instantiateVariableFont(TTFont(io.BytesIO(FONT.read_bytes())), {"wght": weight})


def width(s, size, weight=400, track=0.0):
    f = face(weight)
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    adv = sum(hmtx[cmap.get(ord(c), cmap[ord("?")])][0] for c in s)
    return adv * size / upm + track * size * len(s)


def wrap(s, size, weight, maxw):
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if cur and width(trial, size, weight) > maxw:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def b64(path):
    return base64.b64encode(Path(path).read_bytes()).decode()


# =================================================================== primitives
def text(x, y, s, size, weight, fill, track=0.0, anchor="start"):
    ls = f' letter-spacing="{track * size:.2f}"' if track else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}"{ls}'
            f' text-anchor="{anchor}">{esc(s)}</text>')


def para(x, y, s, size, weight, fill, maxw, lh):
    out = []
    for line in wrap(s, size, weight, maxw):
        out.append(text(x, y, line, size, weight, fill))
        y += lh
    return "".join(out), y


def pill(x, y, label, t, tone=None, size=13, h=28):
    """Neutral pill, or a status pill with a dot (tone: ok | blue)."""
    pad, dot = 12, 14 if tone else 0
    w = width(label, size, 500) + 2 * pad + dot
    fill = t["okbg"] if tone == "ok" else t["pill"]
    color = t["ok"] if tone == "ok" else t["soft"]
    out = f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{fill}"/>'
    if tone:
        out += f'<circle cx="{x + pad + 3.5:.1f}" cy="{y + h / 2:.1f}" r="3.5" fill="{t["okdot"] if tone == "ok" else t["blue"]}"/>'
    out += text(x + pad + dot, y + h / 2 + size * 0.36, label, size, 500, color)
    return w, out


def pills(x, y, labels, t, gap=6):
    out = ""
    for lab in labels:
        w, p = pill(x, y, lab, t)
        out += p
        x += w + gap
    return out


def hline(y, t, x1=PAD, x2=W - PAD):
    return f'<line x1="{x1}" y1="{y:.1f}" x2="{x2}" y2="{y:.1f}" stroke="{t["hair"]}"/>'


def vline(x, y1, y2, t):
    return f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" stroke="{t["hair"]}"/>'


def eyebrow(n, label, t):
    return text(PAD, PAD + 10, f"{n:02d} · {label}", 14, 500, t["muted"])


def pen(x1, x2, y, t):
    w = x2 - x1
    return (f'<path d="M{x1 - 2:.1f} {y + 1.5:.1f} C {x1 + w * .3:.1f} {y - 2.5:.1f}, {x1 + w * .65:.1f} {y - 1:.1f},'
            f' {x2 + 4:.1f} {y - 3.5:.1f}" fill="none" stroke="{t["blue"]}" stroke-width="4.5" stroke-linecap="round"/>')


def flags(x, y):
    dz = (f'<g transform="translate({x:.1f} {y:.1f})"><rect width="9" height="13" fill="#006633"/><rect x="9" width="9" height="13" fill="#FFF"/>'
          f'<circle cx="9" cy="6.5" r="3.8" fill="#D21034"/><circle cx="10" cy="6.5" r="3" fill="#FFF"/>'
          f'<path d="M11.3 5.1l.4.95 1 .05-.8.62.28 1-.88-.58-.85.58.28-1-.8-.62 1-.05z" fill="#D21034"/></g>')
    fr = (f'<g transform="translate({x + 24:.1f} {y:.1f})"><rect width="6" height="13" fill="#1F4DD8"/><rect x="6" width="6" height="13" fill="#FFF"/>'
          f'<rect x="12" width="6" height="13" fill="#E63946"/></g>')
    return dz + fr


def card(H, t, body, label):
    glow = ""
    if t["glow"]:
        glow = (f'<radialGradient id="g" cx="92%" cy="0%" r="65%"><stop offset="0" stop-color="{t["glow"]}" stop-opacity=".22"/>'
                f'<stop offset="1" stop-color="{t["glow"]}" stop-opacity="0"/></radialGradient>')
    H = int(H)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(label)}">
<defs><style>@font-face{{font-family:Geist;src:url(data:font/woff2;base64,{FONT_B64}) format('woff2');font-weight:100 900}}
text{{font-family:Geist,-apple-system,'Segoe UI',Helvetica,Arial,'Noto Sans Arabic',sans-serif}}</style>{glow}</defs>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="{RADIUS}" fill="{t['card']}" stroke="{t['border']}"/>
{f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="{RADIUS}" fill="url(#g)"/>' if t['glow'] else ''}
{body}
</svg>"""


# =================================================================== cards
def about(t):
    parts = [eyebrow(1, "About", t)]
    sw, _ = pill(0, 0, ABOUT["status"], t, "ok", size=13.5, h=30)
    _, sp = pill(W - PAD - sw, PAD - 6, ABOUT["status"], t, "ok", size=13.5, h=30)
    parts.append(sp)

    lines = [l.replace("{", "").replace("}", "") for l in ABOUT["headline"]]
    size = min(42, int(IN / max(width(l, 1, 600, TRACK) for l in lines)))
    y = PAD + 46 + size
    for raw, plain in zip(ABOUT["headline"], lines):
        if "{" in raw:
            pre, key = raw.split("{")[0], raw.split("{")[1].split("}")[0]
            a = PAD + width(pre, size, 600, TRACK)
            parts.append(pen(a, a + width(key, size, 600, TRACK), y + size * 0.2, t))
        parts.append(text(PAD, y, plain, size, 600, t["ink"], TRACK))
        y += size * 1.14
    parts.append(text(PAD, y + 6, ABOUT["lede"], 17, 400, t["muted"]))
    y += 40
    parts.append(hline(y, t))

    # now: current work
    n = ABOUT["now"]
    ny = y + 24
    parts.append(f'<clipPath id="now"><rect x="{PAD}" y="{ny}" width="44" height="44" rx="11"/></clipPath>'
                 f'<image href="data:image/png;base64,{b64(ROOT / "assets/clients" / n["logo"])}" x="{PAD}" y="{ny}"'
                 f' width="44" height="44" clip-path="url(#now)"/>')
    parts.append(text(PAD + 60, ny + 18, n["label"], 13, 500, t["muted"]))
    parts.append(text(PAD + 60, ny + 40, n["name"], 18, 600, t["ink"], -0.02))
    nw = width(n["name"], 18, 600, -0.02)
    _, sp = pill(PAD + 60 + nw + 10, ny + 22, n["status"], t, "ok", size=12, h=24)
    parts.append(sp)
    parts.append(text(W - PAD, ny + 18, n["what"], 14, 400, t["soft"], anchor="end"))
    parts.append(text(W - PAD, ny + 40, n["link"], 13.5, 500, t["blue"], anchor="end"))
    y = ny + 44 + 24
    parts.append(hline(y, t))

    cw = IN / len(ABOUT["facts"])
    fy = y + 28
    for i, (label, value, sub, has_flags) in enumerate(ABOUT["facts"]):
        x = PAD + i * cw + (0 if i == 0 else 20)
        if i:
            parts.append(vline(PAD + i * cw, y + 18, y + 98, t))
        parts.append(text(x, fy + 4, label, 13, 500, t["muted"]))
        parts.append(text(x, fy + 30, value, 16, 600, t["ink"], -0.01))
        parts.append(text(x, fy + 52, sub, 14, 400, t["muted"]))
        if has_flags:
            parts.append(flags(x + width(sub, 14, 400) + 8, fy + 41))
    H = y + 98 + PAD - 18
    label = (f"About. {ABOUT['status']}. " + " ".join(lines) + " " + ABOUT["lede"] + " "
             + f"Now: {n['name']}, {n['what']} ({n['link']}). "
             + ". ".join(f"{a}: {b} {c}" for a, b, c, _ in ABOUT["facts"]) + ".")
    return card(H, t, "\n".join(parts), label)


def experience(t):
    parts = [eyebrow(2, "Experience", t)]
    col = PAD + 180
    y = PAD + 52
    for i, e in enumerate(EXPERIENCE):
        if i:
            parts.append(hline(y - 30, t))
        _, p = pill(PAD, y - 4, e["date"], t)
        parts.append(p)
        parts.append(text(PAD + 2, y + 46, e["kind"], 13.5, 400, t["muted"]))
        parts.append(text(col, y + 18, e["company"], 24, 600, t["ink"], TRACK))
        parts.append(text(col, y + 42, f'{e["role"]} · {e["place"]}', 15, 400, t["muted"]))
        py = y + 76
        for pt in e["points"]:
            parts.append(f'<rect x="{col}" y="{py - 5.5:.1f}" width="8" height="2" rx="1" fill="{t["blue"]}"/>'
                         + text(col + 18, py, pt, 15, 400, t["soft"]))
            py += 26
        parts.append(pills(col, py - 4, e["tags"], t))
        y = py + 24 + 60
    H = y - 60 + PAD - 10
    label = "Experience. " + " ".join(
        f'{e["role"]} at {e["company"]}, {e["kind"].lower()}, {e["place"]}, {e["date"]}: ' + "; ".join(e["points"]) + "."
        for e in EXPERIENCE)
    return card(H, t, "\n".join(parts), label)


def builds(t):
    parts = [eyebrow(3, "Featured builds", t)]
    cw = (IN - 40) / 2
    top = PAD + 44
    bottoms = []
    for i, b in enumerate(BUILDS):
        x = PAD + i * (cw + 40)
        parts.append(text(x, top + 22, b["name"], 22, 600, t["ink"], TRACK))
        _, p = pill(x, top + 38, b["status"][0], t, b["status"][1])
        parts.append(p)
        body, y = para(x, top + 96, b["what"], 15, 400, t["soft"], cw, 23)
        parts.append(body)
        tx, ty = x, y + 4
        for tag in b["tags"]:
            w, p = pill(tx, ty, tag, t)
            if tx + w > x + cw:
                tx, ty = x, ty + 36
                w, p = pill(tx, ty, tag, t)
            parts.append(p)
            tx += w + 6
        bottoms.append(ty + 28)
    parts.append(vline(PAD + cw + 20, top, max(bottoms), t))
    H = max(bottoms) + PAD
    label = "Featured builds. " + " ".join(f'{b["name"]} ({b["status"][0]}): {b["what"]}' for b in BUILDS)
    return card(H, t, "\n".join(parts), label)


def clients(t):
    parts = [eyebrow(4, "Client work", t)]
    cw = IN / len(CLIENTS)
    top = PAD + 44
    bottoms = []
    for i, c in enumerate(CLIENTS):
        x = PAD + i * cw + (0 if i == 0 else 20)
        inner = cw - 20 - (0 if i == 0 else 20)
        parts.append(f'<clipPath id="c{i}"><rect x="{x:.1f}" y="{top}" width="44" height="44" rx="11"/></clipPath>'
                     f'<image href="data:image/png;base64,{b64(ROOT / "assets/clients" / c["logo"])}" x="{x:.1f}" y="{top}"'
                     f' width="44" height="44" clip-path="url(#c{i})"/>')
        parts.append(text(x, top + 72, c["name"], 17, 600, t["ink"], -0.02))
        body, y = para(x, top + 96, c["what"], 14, 400, t["muted"], inner, 20)
        parts.append(body)
        bottoms.append(y)
    by = max(bottoms) + 8
    for i, c in enumerate(CLIENTS):
        x = PAD + i * cw + (0 if i == 0 else 20)
        parts.append(text(x, by + 6, c["note"], 13.5, 500, t["blue"] if "↗" in c["note"] else t["soft"]))
        if i:
            parts.append(vline(PAD + i * cw, top, by + 12, t))
    parts.append(hline(by + 36, t))
    parts.append(text(PAD, by + 66, CLIENTS_MORE, 14, 400, t["muted"]))
    H = by + 66 + PAD - 8
    label = "Client work. " + " ".join(f'{c["name"]}: {c["what"]}.' for c in CLIENTS) + " " + CLIENTS_MORE
    return card(H, t, "\n".join(parts), label)


def stack(t, theme):
    parts = [eyebrow(6, "Stack", t)]
    y = PAD + 40
    for i, (label, icons, names) in enumerate(STACK):
        if i:
            parts.append(hline(y, t))
        y += 20
        parts.append(text(PAD, y + 22, label, 15, 600, t["ink"], -0.01))
        x = PAD + 170
        for ic in icons:
            parts.append(f'<image href="data:image/svg+xml;base64,{b64(ICONS / theme / (ic + ".svg"))}" x="{x}" y="{y}" width="32" height="32"/>')
            x += 40
        body, ny = para(PAD + 170, y + 54, names, 13.5, 400, t["muted"], IN - 170, 19)
        parts.append(body)
        y = ny - 19 + 22
    H = y + PAD - 22
    label = "Stack. " + " ".join(f"{a}: {c}." for a, _, c in STACK)
    return card(H, t, "\n".join(parts), label)


def certs(t):
    parts = [eyebrow(7, "Certifications", t)]
    y = PAD + 44
    for i, (date, title, issuer) in enumerate(CERTS):
        if i:
            parts.append(hline(y - 22, t))
        parts.append(text(PAD, y + 4, date, 14, 500, t["muted"]))
        parts.append(text(PAD + 110, y + 4, title, 15.5, 500, t["ink"], -0.01))
        parts.append(text(W - PAD, y + 4, issuer, 14, 400, t["muted"], anchor="end"))
        y += 46
    H = y - 46 + 4 + PAD
    label = "Certifications. " + " ".join(f"{a}: {b}, {c}." for a, b, c in CERTS)
    return card(H, t, "\n".join(parts), label)


# =================================================================== side projects (animated)
GW, GH = 390, 205   # size of each project animation inside the card


def side_svg(t):
    parts = [eyebrow(5, "Side projects · Arabic UI", t)]
    top = PAD + 44
    for i, p in enumerate(SIDE):
        x = PAD + i * (IN - GW)
        parts.append(f'<rect x="{x}" y="{top}" width="{GW}" height="{GH}" rx="12" fill="{t["pill"]}"/>')
        parts.append(f'<image href="data:image/svg+xml;base64,{b64(ROOT / "assets/projects" / p["logo"])}" x="{x}" y="{top + GH + 20}" width="34" height="34"/>')
        parts.append(f'<text x="{x + 46}" y="{top + GH + 43}" font-size="18" font-weight="600" fill="{t["ink"]}">{esc(p["name"])}'
                     f'<tspan fill="{t["muted"]}" font-weight="400"> · {p["ar"]}</tspan></text>')
        parts.append(text(x, top + GH + 80, p["what"], 14.5, 400, t["muted"]))
    y = top + GH + 108
    parts.append(hline(y, t))
    w, pp = pill(PAD, y + 22, "Coming soon", t, "blue")
    parts.append(pp + text(PAD + w + 12, y + 41, SIDE_SOON, 14.5, 400, t["soft"]))
    H = y + 22 + 28 + PAD - 4
    return card(H, t, "\n".join(parts), "Side projects"), int(H), top


def frames_of(gif, n, period_ms):
    seq = [(f.convert("RGB").copy(), f.info.get("duration", 100)) for f in ImageSequence.Iterator(Image.open(gif))]
    total = sum(d for _, d in seq)
    out = []
    for k in range(n):
        tms, acc = (k * period_ms / n) % total, 0
        for fr, d in seq:
            acc += d
            if acc > tms:
                out.append(fr)
                break
    return out


def side_gif(theme, t):
    svg, H, top = side_svg(t)
    tmp = Path(tempfile.mkdtemp())
    (tmp / "c.svg").write_text(svg)
    (tmp / "c.html").write_text(f'<body style="margin:0;background:{t["page"]}"><img src="c.svg"></body>')
    png = tmp / "c.png"
    subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--allow-file-access-from-files", f"--window-size={W},{H}", "--virtual-time-budget=1000",
                    f"--screenshot={png}", f"file://{tmp / 'c.html'}"], check=True, capture_output=True)
    base = Image.open(png).convert("RGB")
    mask = Image.new("L", (GW, GH), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, GW - 1, GH - 1), radius=12, fill=255)
    N, PERIOD = 40, 4000
    tracks = [frames_of(ROOT / "assets/projects" / p["gif"], N, PERIOD) for p in SIDE]
    out = []
    for k in range(N):
        fr = base.copy()
        for i, tr in enumerate(tracks):
            src = tr[k]
            s = max(GW / src.width, GH / src.height)   # cover-fit
            r = src.resize((round(src.width * s), round(src.height * s)), Image.LANCZOS)
            ox, oy = (r.width - GW) // 2, (r.height - GH) // 2
            fr.paste(r.crop((ox, oy, ox + GW, oy + GH)), (PAD + i * (IN - GW), top), mask)
        out.append(fr.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
    dst = ROOT / f"assets/side-{theme}.gif"
    out[0].save(dst, save_all=True, append_images=out[1:], duration=PERIOD // N, loop=0, optimize=True)
    print(f"{dst.name} {dst.stat().st_size / 1024:.0f} KB")


# =================================================================== main
def main():
    for theme, t in THEMES.items():
        for name, svg in [("about", about(t)), ("experience", experience(t)), ("builds", builds(t)),
                          ("clients", clients(t)), ("stack", stack(t, theme)), ("certs", certs(t))]:
            (ROOT / f"assets/{name}-{theme}.svg").write_text(svg)
        if "--no-gif" not in sys.argv:
            side_gif(theme, t)
    print("cards: about, experience, builds, clients, side, stack, certs × light/dark")


if __name__ == "__main__":
    main()
