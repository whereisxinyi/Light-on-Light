// The gift, as it travels in a link: {v:1, t: sentence, d: YYYY-MM-DD, s: svg},
// JSON → deflate-raw → base64url, with one leading flag character: 'z' for
// deflated, 'r' for raw. Written by make.html, read here. This file has an
// underscore so Vercel does not deploy it as a function of its own.
import { inflateRawSync } from 'node:zlib';

const MONTHS = ['JANUARY','FEBRUARY','MARCH','APRIL','MAY','JUNE','JULY',
                'AUGUST','SEPTEMBER','OCTOBER','NOVEMBER','DECEMBER'];

/* Injected markup is injected markup, whoever drew it — the same rules as the page. */
export function sanitizeSVG(raw) {
  return raw
    .replace(/<text[\s\S]*?<\/text>/gi, '')
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/\son\w+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)/gi, '')
    .replace(/javascript:/gi, '')
    .replace(/<(foreignObject|iframe|object|embed|image|use)[\s\S]*?(\/>|<\/\1>)/gi, '');
}

export function decode(p) {
  if (typeof p !== 'string' || p.length < 4 || p.length > 16000) throw new Error('bad payload');
  const flag = p[0];
  if (flag !== 'z' && flag !== 'r') throw new Error('bad payload');
  let buf = Buffer.from(p.slice(1).replace(/-/g, '+').replace(/_/g, '/'), 'base64');
  if (flag === 'z') buf = inflateRawSync(buf, { maxOutputLength: 96000 });
  const j = JSON.parse(buf.toString('utf8'));
  if (j.v !== 1 || typeof j.t !== 'string' || typeof j.s !== 'string' || typeof j.d !== 'string') throw new Error('bad payload');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(j.d)) throw new Error('bad payload');
  const text = j.t.replace(/\s+/g, ' ').trim();
  if (text.length < 2 || text.length > 200) throw new Error('bad payload');
  const svg = sanitizeSVG(j.s.trim());
  if (svg.indexOf('<svg') !== 0 || svg.length > 80000) throw new Error('bad payload');
  return { text, day: j.d, svg };
}

/* 06 SEPTEMBER 2026 — the card's date, from the sender's day, in any zone. */
export function stamp(day) {
  const [y, m, d] = day.split('-').map(Number);
  return String(d).padStart(2, '0') + ' ' + (MONTHS[m - 1] || '') + ' ' + y;
}

export function esc(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

export function origin(req) {
  const host = req.headers['x-forwarded-host'] || req.headers.host || 'light-on-light.vercel.app';
  const proto = /^(localhost|127\.)/.test(host) ? 'http' : 'https';
  return proto + '://' + host;
}
