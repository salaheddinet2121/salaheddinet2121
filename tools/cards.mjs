// Build the designed README cards: assets/about.svg and assets/experience.svg.
// Edit the data below, then run:  node tools/cards.mjs
import { writeFileSync } from 'node:fs';

const ABOUT = {
  name: "Salah Eddine M'hamda Bouloudani",
  roles: ['DevOps enthusiast', 'Full-stack developer', 'Software engineer'],
  status: 'Open to opportunities',
  tiles: [
    { label: 'Based in', value: 'Montpellier, France', sub: 'originally from Algeria', flags: ['fr', 'dz'] },
    { label: 'Studying at', value: 'University of Montpellier', sub: 'Occitanie, France' },
    { label: 'Track record', value: '20+ projects delivered', sub: 'websites, funnels, automations' },
    { label: 'Focus', value: 'Automation & AI agents', sub: 'prompt engineering · security' },
    { label: 'Experience', value: '3 internships', sub: 'Octodet · GTFT · Sonatrach' },
    { label: 'Languages', value: 'Arabic · French · English', sub: 'and Arabic-first UI design' },
  ],
};

const EXPERIENCE = [
  {
    date: ['Jan 2025', 'Jun 2025'], role: 'Software Developer', company: 'Octodet', meta: 'Internship · Remote',
    bullets: [
      'Automation, prompt engineering and AI agents (LLMs, LLMOps, web scraping)',
      'Security and vulnerability management',
      'Built Scruti, a security project',
    ],
    tags: ['python', 'osquery', 'elasticsearch', 'ansible', 'llms'],
  },
  {
    date: ['Dec 2024'], role: 'Software Engineer', company: 'GTFT', meta: 'Internship · Illizi, Algeria',
    bullets: [
      'Network infrastructure and virtualization for server management',
      'Server replication, risk prevention and disaster recovery',
      'Software management and deployment',
    ],
    tags: ['networking', 'virtualization', 'replication'],
  },
  {
    date: ['Jul 2024'], role: 'Software Engineer', company: 'Sonatrach', meta: 'Internship · Skikda, Algeria',
    bullets: [
      'Automated backup scripts for the company servers',
      'Oracle database administration: monitoring, maintenance, security',
      'Supported the infrastructure team on enterprise applications',
    ],
    tags: ['shell', 'oracle', 'sysadmin'],
  },
];

// ---- design tokens --------------------------------------------------------------
const C = { bg: '#10102B', tile: '#16183F', stroke: '#2A2F66', ink: '#F9FCFF', soft: '#C9D8F5', muted: '#8C9AC4', blue: '#448FF4', pale: '#DEEFFF' };
const W = 900, PAD = 32;
const SANS = `-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif`;
const MONO = `ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace`;
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const style = `<style>
  .sans{font-family:${SANS}} .mono{font-family:${MONO}}
  .eyebrow{font:600 11px ${SANS};letter-spacing:.14em;fill:${C.muted}}
  .pulse{animation:p 2.4s ease-in-out infinite;transform-origin:center;transform-box:fill-box}
  @keyframes p{0%,100%{opacity:1}50%{opacity:.35}}
</style>`;

// A chip with monospace text, so its width is predictable without measuring.
function chip(x, y, text, { fs = 12, fill = 'none', stroke = C.stroke, color = C.soft } = {}) {
  const w = Math.round(text.length * fs * 0.6 + 20), h = fs + 12;
  return {
    w,
    svg: `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${h / 2}" fill="${fill}" stroke="${stroke}"/>` +
      `<text x="${x + w / 2}" y="${y + h / 2 + fs * 0.36}" text-anchor="middle" class="mono" font-size="${fs}" fill="${color}">${esc(text)}</text>`,
  };
}
function chips(x, y, list, opts) {
  let out = '';
  for (const t of list) { const c = chip(x, y, t, opts); out += c.svg; x += c.w + 8; }
  return out;
}

const FLAGS = {
  fr: (x, y) => `<g transform="translate(${x} ${y})"><rect width="7" height="14" fill="#1F4DD8"/><rect x="7" width="7" height="14" fill="#FFF"/><rect x="14" width="7" height="14" fill="#E63946"/><rect width="21" height="14" fill="none" stroke="#ffffff33"/></g>`,
  dz: (x, y) => `<g transform="translate(${x} ${y})"><rect width="10.5" height="14" fill="#006633"/><rect x="10.5" width="10.5" height="14" fill="#FFF"/>` +
    `<circle cx="10.5" cy="7" r="4.2" fill="#D21034"/><circle cx="11.7" cy="7" r="3.4" fill="#FFF"/><circle cx="11.7" cy="7" r="3.4" fill="none"/>` +
    `<path d="M13.2 5.4l.45 1.1 1.15.05-.9.7.33 1.12-.98-.66-.97.66.32-1.12-.9-.7 1.15-.05z" fill="#D21034"/><rect width="21" height="14" fill="none" stroke="#ffffff33"/></g>`,
};

// ---- about ------------------------------------------------------------------------
function about() {
  const parts = [];
  parts.push(`<text x="${PAD}" y="${PAD + 22}" class="sans" font-size="26" font-weight="700" fill="${C.ink}">${esc(ABOUT.name)}</text>`);
  parts.push(chips(PAD, PAD + 38, ABOUT.roles, { fs: 12, stroke: C.blue, color: C.pale }));

  // status pill, top right
  const st = ABOUT.status, sw = Math.round(st.length * 7.2 + 44);
  parts.push(`<g transform="translate(${W - PAD - sw} ${PAD - 2})"><rect width="${sw}" height="30" rx="15" fill="#13341F" stroke="#2EA043"/>` +
    `<circle class="pulse" cx="16" cy="15" r="4.5" fill="#3FB950"/><text x="30" y="19.5" class="sans" font-size="13" font-weight="600" fill="#AFF5B4">${esc(st)}</text></g>`);

  const top = PAD + 92, cols = 3, gap = 14;
  const tw = (W - 2 * PAD - gap * (cols - 1)) / cols, th = 86;
  ABOUT.tiles.forEach((t, i) => {
    const x = PAD + (i % cols) * (tw + gap), y = top + Math.floor(i / cols) * (th + gap);
    let flags = '';
    (t.flags ?? []).forEach((f, k) => { flags += FLAGS[f](x + tw - 18 - 21 - k * 27, y + 16); });
    parts.push(`<rect x="${x}" y="${y}" width="${tw}" height="${th}" rx="12" fill="${C.tile}" stroke="${C.stroke}"/>` + flags +
      `<text x="${x + 18}" y="${y + 27}" class="eyebrow">${esc(t.label.toUpperCase())}</text>` +
      `<text x="${x + 18}" y="${y + 52}" class="sans" font-size="16" font-weight="600" fill="${C.ink}">${esc(t.value)}</text>` +
      `<text x="${x + 18}" y="${y + 72}" class="sans" font-size="12.5" fill="${C.muted}">${esc(t.sub)}</text>`);
  });
  const H = top + 2 * th + gap + PAD;
  return wrap(H, parts.join('\n'), `About me: ${ABOUT.name}. ${ABOUT.roles.join(', ')}. ${ABOUT.status}. ` +
    ABOUT.tiles.map(t => `${t.label}: ${t.value} (${t.sub})`).join('. '));
}

// ---- experience -------------------------------------------------------------------
function experience() {
  const parts = [];
  const lineX = 160, textX = lineX + 30;
  let y = PAD + 12;
  const starts = [];
  for (const e of EXPERIENCE) {
    starts.push(y);
    parts.push(e.date.map((d, k) => `<text x="${lineX - 24}" y="${y + 6 + k * 18}" text-anchor="end" class="sans" font-size="13" font-weight="${k ? 400 : 600}" fill="${k ? C.muted : C.soft}">${k ? '→ ' : ''}${esc(d)}</text>`).join(''));
    parts.push(`<circle cx="${lineX}" cy="${y + 1}" r="7" fill="${C.bg}" stroke="${C.blue}" stroke-width="2.5"/><circle cx="${lineX}" cy="${y + 1}" r="3" fill="${C.blue}"/>`);
    parts.push(`<text x="${textX}" y="${y + 7}" class="sans" font-size="18" font-weight="700" fill="${C.ink}">${esc(e.role)}<tspan fill="${C.muted}" font-weight="400"> at </tspan><tspan fill="${C.blue}">${esc(e.company)}</tspan></text>`);
    parts.push(`<text x="${textX}" y="${y + 28}" class="sans" font-size="12.5" fill="${C.muted}">${esc(e.meta)}</text>`);
    let by = y + 56;
    for (const b of e.bullets) {
      parts.push(`<rect x="${textX + 1}" y="${by - 5}" width="5" height="5" rx="1" fill="${C.blue}"/><text x="${textX + 16}" y="${by}" class="sans" font-size="14" fill="${C.soft}">${esc(b)}</text>`);
      by += 23;
    }
    parts.push(chips(textX, by - 4, e.tags, { fs: 11.5 }));
    y = by + 52;
  }
  const end = y - 52 + 20;
  parts.unshift(`<line x1="${lineX}" y1="${starts[0]}" x2="${lineX}" y2="${end}" stroke="${C.stroke}" stroke-width="2"/>`);
  const H = end + PAD - 8;
  return wrap(H, parts.join('\n'), 'Experience. ' + EXPERIENCE.map(e =>
    `${e.role} at ${e.company} (${e.meta}, ${e.date.join(' to ')}): ${e.bullets.join('; ')}.`).join(' '));
}

function wrap(H, body, label) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label)}">
${style}
<rect width="${W}" height="${H}" rx="16" fill="${C.bg}"/>
${body}
</svg>`;
}

writeFileSync('assets/about.svg', about());
writeFileSync('assets/experience.svg', experience());
console.log('assets/about.svg, assets/experience.svg');
