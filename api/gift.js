// /g/<payload> — a gift, sent. Serves make.html with this card's own title,
// description and image in the head, so the link unfurls as the card in
// iMessage, WeChat, Slack, X; the page itself then opens the card from the
// same payload in its URL. No database: the card IS the link.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { decode, stamp, esc, origin } from './_lib/gift.js';

let page = null;

export default function handler(req, res) {
  const p = typeof req.query.p === 'string' ? req.query.p : '';
  let gift;
  try { gift = decode(p); }
  catch (e) {
    res.statusCode = 302;
    res.setHeader('Location', '/make.html');
    return res.end();
  }
  if (page === null) page = readFileSync(path.join(process.cwd(), 'make.html'), 'utf8');

  const base = origin(req);
  const url  = base + '/g/' + p;
  const img  = base + '/api/card?p=' + p;
  const title = esc(gift.text);
  const desc  = esc('A gift from Light on Light · ' + stamp(gift.day));

  const head =
    '<base href="/">\n' +
    '<meta name="description" content="' + desc + '">\n' +
    '<meta property="og:type" content="article">\n' +
    '<meta property="og:site_name" content="Light on Light">\n' +
    '<meta property="og:title" content="' + title + '">\n' +
    '<meta property="og:description" content="' + desc + '">\n' +
    '<meta property="og:url" content="' + esc(url) + '">\n' +
    '<meta property="og:image" content="' + esc(img) + '">\n' +
    '<meta property="og:image:width" content="1200">\n' +
    '<meta property="og:image:height" content="630">\n' +
    '<meta name="twitter:card" content="summary_large_image">\n' +
    '<meta name="twitter:title" content="' + title + '">\n' +
    '<meta name="twitter:image" content="' + esc(img) + '">';

  let html = page
    .replace(/<meta (?:property="og:[^"]*"|name="twitter:[^"]*"|name="description")[^>]*>\n?/g, '')
    .replace('<title>Light on Light</title>', '<title>' + title + ' — Light on Light</title>\n' + head);

  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.setHeader('Cache-Control', 'public, max-age=0, s-maxage=86400');
  res.end(html);
}
