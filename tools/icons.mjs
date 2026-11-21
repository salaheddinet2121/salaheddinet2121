// Export dither-icons (github.com/vijayksingh/dither-icons, MIT) as standalone SVGs
// for the README. GitHub shows SVGs through <img>, where hover never fires, so the
// hover-only motion is rewritten to replay on its own: play, rest, play again.
//
//   npm install && node tools/icons.mjs
import { createElement as h } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { DitherIcon } from '@unlocalhosted/dither-icons';
import { mkdirSync, writeFileSync } from 'node:fs';

const COLOR = '#448FF4';
const PERIOD = 4200; // ms between replays
const ICONS = { user: 0, sparkles: 300, layers: 700, code: 1100, chart: 1500, mail: 1900, heart: 2300 };

// Scale every keyframe stop of one @keyframes block by `k` and hold the final pose to 100%.
function rescaleKeyframes(css, durations) {
  return css.replace(/@keyframes ([\w-]+)\{((?:[^{}]*\{[^{}]*\})*)\}/g, (block, name, body) => {
    if (!durations.has(name)) return block;
    const k = durations.get(name) / PERIOD;
    const stops = [...body.matchAll(/([^{}]+)\{([^{}]*)\}/g)].map(([, sel, decl]) => [sel, decl]);
    const scaled = stops.map(([sel, decl]) => {
      const s = sel.split(',').map(p => {
        const v = p.trim() === 'from' ? 0 : p.trim() === 'to' ? 100 : parseFloat(p);
        return `${+(v * k).toFixed(3)}%`;
      });
      return `${s.join(',')}{${decl}}`;
    });
    const last = stops.at(-1)[1].replace(/animation-timing-function:[^;}]+;?/, '');
    return `@keyframes ${name}{${scaled.join('')}100%{${last}}}`;
  });
}

mkdirSync('assets/icons', { recursive: true });
for (const [name, delay] of Object.entries(ICONS)) {
  let svg = renderToStaticMarkup(h(DitherIcon, { name, size: 40, color: COLOR, title: name }));
  const durations = new Map();
  svg = svg
    .replaceAll(':is(:hover,:focus-visible)', '')
    .replace(/animation:([\w-]+) (\d+)ms ([^;}]+?) both/g, (_, anim, ms, ease) => {
      durations.set(anim, +ms);
      return `animation:${anim} ${PERIOD}ms ${ease} ${delay}ms infinite both`;
    });
  svg = rescaleKeyframes(svg, durations);
  writeFileSync(`assets/icons/${name}.svg`, svg);
  console.log(name, (svg.length / 1024).toFixed(0) + ' KB', durations.size + ' tracks');
}
