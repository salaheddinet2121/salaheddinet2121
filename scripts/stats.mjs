// Build assets/stats.svg from the GitHub GraphQL API: an ASCII terminal card with
// contribution numbers, streaks, top languages and a Bayer-dithered heatmap.
// No dependencies. Run by .github/workflows/stats.yml every day.
//
//   GITHUB_TOKEN=... node scripts/stats.mjs [login]
import { writeFileSync } from 'node:fs';

const LOGIN = process.argv[2] || process.env.PROFILE_LOGIN || 'salaheddinet2121';
const TOKEN = process.env.GH_STATS_TOKEN || process.env.GITHUB_TOKEN;
if (!TOKEN) throw new Error('Set GITHUB_TOKEN (or GH_STATS_TOKEN)');

const C = { bg: '#10102B', panel: '#14163A', line: '#2A2F66', ink: '#F9FCFF', muted: '#8FB8F8', dim: '#5F6A97', blue: '#448FF4', deep: '#1F67DA', pale: '#DEEFFF' };

const query = `query($login:String!){
  user(login:$login){
    createdAt
    contributionsCollection{
      contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } }
      totalCommitContributions restrictedContributionsCount
    }
    repositories(ownerAffiliations:OWNER, first:100, orderBy:{field:PUSHED_AT,direction:DESC}){
      totalCount
      nodes{ isFork languages(first:6, orderBy:{field:SIZE,direction:DESC}){ edges{ size node{ name } } } }
    }
  }
}`;

const res = await fetch('https://api.github.com/graphql', {
  method: 'POST',
  headers: { Authorization: `bearer ${TOKEN}`, 'Content-Type': 'application/json', 'User-Agent': 'profile-stats' },
  body: JSON.stringify({ query, variables: { login: LOGIN } }),
});
const json = await res.json();
if (json.errors || !json.data?.user) throw new Error(JSON.stringify(json.errors ?? json));
const user = json.data.user;
const cal = user.contributionsCollection.contributionCalendar;

// ---- numbers -----------------------------------------------------------------
const days = cal.weeks.flatMap(w => w.contributionDays);
let longest = 0, run = 0;
for (const d of days) { run = d.contributionCount ? run + 1 : 0; longest = Math.max(longest, run); }
let current = 0;
for (let i = days.length - 1; i >= 0; i--) {
  if (days[i].contributionCount) current++;
  else if (i === days.length - 1) continue; // today may still be empty
  else break;
}
const best = days.reduce((a, d) => (d.contributionCount > a.contributionCount ? d : a), days[0]);
const activeDays = days.filter(d => d.contributionCount).length;

const langBytes = new Map();
for (const r of user.repositories.nodes) {
  if (r.isFork) continue;
  for (const e of r.languages.edges) langBytes.set(e.node.name, (langBytes.get(e.node.name) ?? 0) + e.size);
}
const totalBytes = [...langBytes.values()].reduce((a, b) => a + b, 0) || 1;
const langs = [...langBytes].sort((a, b) => b[1] - a[1]).slice(0, 5).map(([name, b]) => [name, b / totalBytes]);

// ---- svg helpers -----------------------------------------------------------------
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const fmt = n => n.toLocaleString('en-US');
const W = 900, PAD = 32, CH = 8.4; // CH: width of one monospace char at 14px
const text = (x, y, s, fill = C.ink, extra = '') => `<text x="${x}" y="${y}" fill="${fill}" ${extra}>${esc(s)}</text>`;

// Bayer 4x4: level n lights the n cells whose threshold is below n/16.
const B4 = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5];
const LEVELS = [1, 4, 7, 11, 16];
const patterns = LEVELS.map((lit, i) => {
  const px = B4.map((t, k) => (t < lit ? `<rect x="${(k % 4) * 2.5}" y="${Math.floor(k / 4) * 2.5}" width="2.5" height="2.5"/>` : '')).join('');
  const fill = i === 0 ? C.line : i === LEVELS.length - 1 ? C.pale : C.blue;
  return `<pattern id="d${i}" width="10" height="10" patternUnits="userSpaceOnUse"><rect width="10" height="10" fill="${C.panel}"/><g fill="${fill}">${px}</g></pattern>`;
}).join('');

const max = Math.max(...days.map(d => d.contributionCount), 1);
const level = n => (n === 0 ? 0 : Math.min(4, 1 + Math.floor(Math.sqrt(n / max) * 3.999)));

// ---- layout -------------------------------------------------------------------
const lines = [];
let y = PAD + 30;
const header = `┌─ ${LOGIN}@github ~ $ stats --year `;
lines.push(text(PAD, y, header + '─'.repeat(Math.floor((W - 2 * PAD) / CH) - header.length - 1) + '┐', C.dim));
y += 34;

const rows = [
  ['contributions (last year)', fmt(cal.totalContributions)],
  ['active days', `${activeDays}/${days.length}`],
  ['current streak', `${current} day${current === 1 ? '' : 's'}`],
  ['longest streak', `${longest} days`],
  ['best day', `${best.contributionCount} on ${best.date}`],
  ['repositories', fmt(user.repositories.totalCount)],
];
rows.forEach(([label, value], i) => {
  const leader = ' ' + '.'.repeat(Math.max(2, 42 - label.length - value.length)) + ' ';
  lines.push(`<text x="${PAD + 18}" y="${y + i * 24}"><tspan fill="${C.muted}">${esc(label)}</tspan><tspan fill="${C.dim}">${leader}</tspan><tspan fill="${C.ink}" font-weight="700">${esc(value)}</tspan></text>`);
});

const rx = PAD + 18 + 47 * CH;
lines.push(text(rx, y, '# top languages', C.dim));
langs.forEach(([name, share], i) => {
  const cells = 16, on = Math.max(1, Math.round(share * cells));
  const bar = '█'.repeat(on) + '░'.repeat(cells - on);
  const yy = y + (i + 1) * 24;
  lines.push(`<text x="${rx}" y="${yy}"><tspan fill="${C.muted}">${esc(name.toLowerCase().padEnd(11).slice(0, 11))}</tspan><tspan fill="${C.blue}">${bar}</tspan><tspan fill="${C.ink}"> ${String(Math.round(share * 100)).padStart(2)}%</tspan></text>`);
});
y += rows.length * 24 + 18;

// heatmap
const cell = 12, gap = 2.6, gridX = PAD + 18;
lines.push(text(PAD + 18, y, '# contributions, one dithered cell per day', C.dim));
y += 14;
const rects = cal.weeks.map((w, wi) => w.contributionDays.map((d) => {
  const dow = new Date(d.date + 'T00:00:00Z').getUTCDay();
  return `<rect x="${gridX + wi * (cell + gap)}" y="${y + dow * (cell + gap)}" width="${cell}" height="${cell}" fill="url(#d${level(d.contributionCount)})"><title>${d.date}: ${d.contributionCount}</title></rect>`;
}).join('')).join('');
lines.push(`<g>${rects}</g>`);
y += 7 * (cell + gap) + 26;

const legendX = W - PAD - 18 - 34 - 5 * 16;
const legend = LEVELS.map((_, i) => `<rect x="${legendX + i * 16}" y="${y - 11}" width="12" height="12" fill="url(#d${i})"/>`).join('');
const updated = new Date().toISOString().slice(0, 10);
lines.push(text(PAD + 18, y, `updated ${updated} · via api.github.com/graphql`, C.dim));
lines.push(text(legendX - 8, y, 'less', C.dim, 'text-anchor="end"'), legend, text(legendX + 5 * 16 + 4, y, 'more', C.dim));
y += 26;
lines.push(text(PAD, y, '└' + '─'.repeat(Math.floor((W - 2 * PAD) / CH) - 2) + '┘', C.dim));
lines.push(`<text x="${PAD + 18}" y="${y + 30}" fill="${C.blue}">$ <tspan class="cur">█</tspan></text>`);
const H = y + 50;
const sideX = [PAD + 4, PAD + (Math.floor((W - 2 * PAD) / CH) - 1) * CH + 4];
lines.push(sideX.map(x => `<line x1="${x}" y1="${PAD + 34}" x2="${x}" y2="${y - 14}" stroke="${C.dim}" stroke-width="1.2"/>`).join(''));

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="GitHub stats for ${LOGIN}: ${cal.totalContributions} contributions in the last year">
<style>text{font:14px ui-monospace,SFMono-Regular,'JetBrains Mono',Menlo,Consolas,'DejaVu Sans Mono',monospace;white-space:pre}.cur{animation:b 1.1s steps(1) infinite}@keyframes b{50%{opacity:0}}</style>
<defs>${patterns}</defs>
<rect width="${W}" height="${H}" rx="14" fill="${C.bg}"/>
${lines.join('\n')}
</svg>`;

writeFileSync('assets/stats.svg', svg);
console.log(`assets/stats.svg · ${cal.totalContributions} contributions · streak ${current}/${longest} · ${langs.map(l => l[0]).join(', ')}`);
