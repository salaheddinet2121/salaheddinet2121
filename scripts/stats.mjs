// Refresh the Activity section from the GitHub GraphQL API: the three numbers
// (contributions, current streak, longest streak) are written into README.md as real
// text between the STATS markers, and only the Bayer-dithered heatmap is an image
// (assets/heatmap-{light,dark}.svg). No dependencies. Run daily by .github/workflows/stats.yml.
//
//   GITHUB_TOKEN=... node scripts/stats.mjs [login]
import { readFileSync, writeFileSync } from 'node:fs';

const LOGIN = process.argv[2] || process.env.PROFILE_LOGIN || 'salaheddinet2121';
const TOKEN = process.env.GH_STATS_TOKEN || process.env.GITHUB_TOKEN;
if (!TOKEN) throw new Error('Set GITHUB_TOKEN (or GH_STATS_TOKEN)');

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

// ---- heatmap svg (the only image: numbers live in README.md as real text) ----------
const B4 = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5];
const LEVELS = [0, 5, 9, 13, 16];
const max = Math.max(...days.map(d => d.contributionCount), 1);
const level = n => (n === 0 ? 0 : Math.min(4, 1 + Math.floor(Math.sqrt(n / max) * 3.999)));
const THEMES = {
  light: { empty: '#EDEDEB', blue: '#448FF4', deep: '#1F67DA' },
  dark: { empty: '#1E1E24', blue: '#448FF4', deep: '#8FB8F8' },
};

function heatmap(t) {
  const cell = 12, gap = 3, weeks = cal.weeks.length;
  const W = weeks * (cell + gap) - gap, H = 7 * (cell + gap) - gap;
  const patterns = LEVELS.map((lit, i) => {
    const px = B4.map((th, k) => (th < lit ? `<rect x="${(k % 4) * 3}" y="${Math.floor(k / 4) * 3}" width="3" height="3"/>` : '')).join('');
    return `<pattern id="d${i}" width="12" height="12" patternUnits="userSpaceOnUse"><rect width="12" height="12" fill="${t.empty}"/><g fill="${i === 4 ? t.deep : t.blue}">${px}</g></pattern>`;
  }).join('');
  const cells = cal.weeks.map((w, wi) => w.contributionDays.map(d => {
    const dow = new Date(d.date + 'T00:00:00Z').getUTCDay();
    return `<rect x="${wi * (cell + gap)}" y="${dow * (cell + gap)}" width="${cell}" height="${cell}" rx="2" fill="url(#d${level(d.contributionCount)})"><title>${d.date}: ${d.contributionCount}</title></rect>`;
  }).join('')).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="Contribution heatmap for the last year"><defs>${patterns}</defs>${cells}</svg>`;
}
for (const [name, t] of Object.entries(THEMES)) writeFileSync(`assets/heatmap-${name}.svg`, heatmap(t));

// ---- README block between the STATS markers --------------------------------------
const block = `<!-- STATS:START -->
**${cal.totalContributions.toLocaleString('en-US')}** contributions in the last year &nbsp;·&nbsp; **<ins>${current.n} days</ins>** current streak <sub>${range(current)}</sub> &nbsp;·&nbsp; **${longest.n} days** longest streak <sub>${range(longest)}</sub>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/heatmap-dark.svg">
  <img src="assets/heatmap-light.svg" width="100%" alt="Contribution heatmap: ${cal.totalContributions} contributions in the last year, one dithered blue square per day">
</picture>
<!-- STATS:END -->`;
const readme = readFileSync('README.md', 'utf8');
writeFileSync('README.md', readme.replace(/<!-- STATS:START -->[\s\S]*?<!-- STATS:END -->/, block));
console.log(`stats: ${cal.totalContributions} contributions · streak ${current.n} · longest ${longest.n}`);
