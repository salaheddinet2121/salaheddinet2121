// Build assets/stats-{light,dark}.svg from the GitHub GraphQL API: three big numbers
// (contributions, current streak, longest streak) over a Bayer-dithered heatmap,
// in Geist on a grey shell + card. No dependencies. Run daily by .github/workflows/stats.yml.
//
//   GITHUB_TOKEN=... node scripts/stats.mjs [login]
import { readFileSync, writeFileSync } from 'node:fs';

const LOGIN = process.argv[2] || process.env.PROFILE_LOGIN || 'salaheddinet2121';
const TOKEN = process.env.GH_STATS_TOKEN || process.env.GITHUB_TOKEN;
if (!TOKEN) throw new Error('Set GITHUB_TOKEN (or GH_STATS_TOKEN)');
const FONT = readFileSync(new URL('../tools/fonts/Geist-Variable.woff2', import.meta.url)).toString('base64');

const THEMES = {
  // same tokens as tools/cards.py
  light: { card: '#FFFFFF', border: '#E4E4E0', ink: '#161513', muted: '#6B675F', line: '#ECECE9', empty: '#EDEDEB', blue: '#448FF4', deep: '#1F67DA', glow: null },
  dark: { card: '#0B0B0E', border: '#26262C', ink: '#F5F5F4', muted: '#8B877D', line: '#1E1E24', empty: '#1A1A1F', blue: '#448FF4', deep: '#8FB8F8', glow: '#2B4BFF' },
};

const query = `query($login:String!){ user(login:$login){
  contributionsCollection{ contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } } }
} }`;
const res = await fetch('https://api.github.com/graphql', {
  method: 'POST',
  headers: { Authorization: `bearer ${TOKEN}`, 'Content-Type': 'application/json', 'User-Agent': 'profile-stats' },
  body: JSON.stringify({ query, variables: { login: LOGIN } }),
});
const json = await res.json();
if (json.errors || !json.data?.user) throw new Error(JSON.stringify(json.errors ?? json));
const cal = json.data.user.contributionsCollection.contributionCalendar;
const days = cal.weeks.flatMap(w => w.contributionDays);

// ---- streaks ------------------------------------------------------------------------
let longest = { n: 0, from: null, to: null }, run = { n: 0, from: null };
for (const d of days) {
  if (d.contributionCount) {
    run = run.n ? { n: run.n + 1, from: run.from } : { n: 1, from: d.date };
    if (run.n > longest.n) longest = { n: run.n, from: run.from, to: d.date };
  } else run = { n: 0, from: null };
}
let current = { n: 0, from: null, to: null };
for (let i = days.length - 1; i >= 0; i--) {
  if (days[i].contributionCount) { current = { n: current.n + 1, from: days[i].date, to: current.to ?? days[i].date }; }
  else if (i === days.length - 1) continue; // today may still be empty
  else break;
}
const fmtDate = iso => new Date(iso + 'T00:00:00Z').toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });
const range = s => (s.n ? `${fmtDate(s.from)} – ${fmtDate(s.to)}` : 'start one today');

// ---- svg --------------------------------------------------------------------------
const W = 900, S = 0, PAD = 40;
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
const B4 = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5];
const LEVELS = [0, 5, 9, 13, 16];
const max = Math.max(...days.map(d => d.contributionCount), 1);
const level = n => (n === 0 ? 0 : Math.min(4, 1 + Math.floor(Math.sqrt(n / max) * 3.999)));

function render(t) {
  const cw = W - 2 * S;
  const colW = (cw - 2 * PAD) / 3;
  const stats = [
    { big: cal.totalContributions.toLocaleString('en-US'), label: 'Contributions', sub: 'in the last year' },
    { big: String(current.n), label: 'Current streak', sub: range(current), accent: true },
    { big: String(longest.n), label: 'Longest streak', sub: range(longest) },
  ];
  const top = S + PAD + 30;
  let body = `<text x="${PAD}" y="${PAD + 10}" font-size="14" font-weight="500" fill="${t.muted}">08 · Activity</text>`;
  body += stats.map((s, i) => {
    const cx = S + PAD + colW * i + colW / 2;
    const sep = i ? `<line x1="${S + PAD + colW * i}" y1="${top + 4}" x2="${S + PAD + colW * i}" y2="${top + 104}" stroke="${t.line}"/>` : '';
    return sep +
      `<text x="${cx}" y="${top + 52}" text-anchor="middle" font-size="46" font-weight="600" letter-spacing="-1.6" fill="${s.accent ? t.blue : t.ink}">${esc(s.big)}</text>` +
      `<text x="${cx}" y="${top + 80}" text-anchor="middle" font-size="15" font-weight="500" fill="${t.ink}">${esc(s.label)}</text>` +
      `<text x="${cx}" y="${top + 101}" text-anchor="middle" font-size="13" fill="${t.muted}">${esc(s.sub)}</text>`;
  }).join('');

  // heatmap: one Bayer-dithered cell per day
  const patterns = LEVELS.map((lit, i) => {
    const px = B4.map((th, k) => (th < lit ? `<rect x="${(k % 4) * 2.5}" y="${Math.floor(k / 4) * 2.5}" width="2.5" height="2.5"/>` : '')).join('');
    return `<pattern id="d${i}" width="10" height="10" patternUnits="userSpaceOnUse"><rect width="10" height="10" fill="${t.empty}"/><g fill="${i === 4 ? t.deep : t.blue}">${px}</g></pattern>`;
  }).join('');
  const weeks = cal.weeks.length, gap = 3;
  const cell = Math.floor((cw - 2 * PAD - (weeks - 1) * gap) / weeks);
  const gx = S + (cw - (weeks * cell + (weeks - 1) * gap)) / 2, gy = top + 140;
  body += `<line x1="${S + PAD}" y1="${gy - 18}" x2="${W - S - PAD}" y2="${gy - 18}" stroke="${t.line}"/>`;
  body += cal.weeks.map((w, wi) => w.contributionDays.map(d => {
    const dow = new Date(d.date + 'T00:00:00Z').getUTCDay();
    return `<rect x="${gx + wi * (cell + gap)}" y="${gy + dow * (cell + gap)}" width="${cell}" height="${cell}" rx="2" fill="url(#d${level(d.contributionCount)})"><title>${d.date}: ${d.contributionCount}</title></rect>`;
  }).join('')).join('');
  const H = gy + 7 * (cell + gap) - gap + PAD + S;

  const glow = t.glow ? `<radialGradient id="g" cx="92%" cy="0%" r="65%"><stop offset="0" stop-color="${t.glow}" stop-opacity=".22"/><stop offset="1" stop-color="${t.glow}" stop-opacity="0"/></radialGradient>` : '';
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="GitHub stats for ${LOGIN}: ${cal.totalContributions} contributions in the last year, current streak ${current.n} days, longest streak ${longest.n} days">
<defs><style>@font-face{font-family:Geist;src:url(data:font/woff2;base64,${FONT}) format('woff2');font-weight:100 900}
text{font-family:Geist,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif}</style>${patterns}${glow}</defs>
<rect x=".5" y=".5" width="${W - 1}" height="${H - 1}" rx="18" fill="${t.card}" stroke="${t.border}"/>
${t.glow ? `<rect x=".5" y=".5" width="${W - 1}" height="${H - 1}" rx="18" fill="url(#g)"/>` : ''}
${body}
</svg>`;
}

for (const [name, t] of Object.entries(THEMES)) writeFileSync(`assets/stats-${name}.svg`, render(t));
console.log(`stats: ${cal.totalContributions} contributions · streak ${current.n} · longest ${longest.n}`);
