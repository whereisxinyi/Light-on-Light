// /api/card?p=<payload> — the card as a 1200×630 picture, for the link's
// unfurl. The sentence on the left in the voice of the thoughts, the date
// and the series mark under it, the drawing on its plate on the right: the
// same template as the export, turned on its side. Drawn by satori and
// rasterised by resvg; the two faces ride along as TTFs.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import satori from 'satori';
import { Resvg } from '@resvg/resvg-js';
import { decode, stamp } from './_lib/gift.js';

let fonts = null;
function loadFonts() {
  if (fonts) return fonts;
  const dir = path.join(process.cwd(), 'api', '_lib', 'fonts');
  fonts = [
    { name: 'Instrument Serif', data: readFileSync(path.join(dir, 'InstrumentSerif-Italic.ttf')), style: 'italic', weight: 400 },
    { name: 'Courier Prime',    data: readFileSync(path.join(dir, 'CourierPrime-Regular.ttf')),    style: 'normal', weight: 400 },
  ];
  return fonts;
}

const h = (type, props, ...children) =>
  ({ type, props: { ...props, children: children.length === 1 ? children[0] : children } });

export default async function handler(req, res) {
  const p = typeof req.query.p === 'string' ? req.query.p : '';
  let gift;
  try { gift = decode(p); }
  catch (e) { res.statusCode = 404; return res.end('no such gift'); }

  const n = gift.text.length;
  const size = n > 150 ? 30 : n > 100 ? 36 : n > 60 ? 42 : 48;
  const art = 'data:image/svg+xml;base64,' + Buffer.from(gift.svg, 'utf8').toString('base64');

  const tree =
    h('div', { style: { width: 1200, height: 630, display: 'flex', background: '#f5f1ea', fontFamily: 'Instrument Serif' } },
      h('div', { style: { display: 'flex', flexDirection: 'column', justifyContent: 'center', width: 620, padding: '64px 56px 64px 80px', overflow: 'hidden' } },
        h('div', { style: { fontSize: size, lineHeight: 1.25, color: '#2a2521', fontStyle: 'italic' } }, gift.text),
        h('div', { style: { marginTop: 40, fontFamily: 'Courier Prime', fontSize: 17, letterSpacing: 4, color: '#4a443c' } }, stamp(gift.day)),
        h('div', { style: { marginTop: 8,  fontFamily: 'Courier Prime', fontSize: 14, letterSpacing: 4, color: '#7d766b' } }, 'LIGHT ON LIGHT')),
      h('div', { style: { display: 'flex', alignItems: 'center', justifyContent: 'center', width: 580, height: 630 } },
        h('div', { style: { display: 'flex', width: 500, height: 500, background: '#fdfdfb', boxShadow: '0 1px 0 #dcdad6, 0 24px 48px -32px rgba(42,37,33,0.45)' } },
          h('img', { src: art, width: 500, height: 500 }))));

  const svg = await satori(tree, { width: 1200, height: 630, fonts: loadFonts() });
  const png = new Resvg(svg, { fitTo: { mode: 'width', value: 1200 } }).render().asPng();

  res.setHeader('Content-Type', 'image/png');
  res.setHeader('Cache-Control', 'public, max-age=86400, s-maxage=31536000, immutable');
  res.end(Buffer.from(png));
}
