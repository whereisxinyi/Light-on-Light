# Light on Light

**Live: <https://whereisxinyi.github.io/Light-on-Light/>**

A quiet three-layer site: an opening screen where the name drifts as light,
a "why this project" concept page, and an instrument that translates one
sentence into a hand-drawn visual gift.

Every page is a single self-contained HTML file — fonts embedded, zero
network requests. Open them from disk, from GitHub Pages, from anywhere.

## Layers

| Layer | Live | Source |
|---|---|---|
| 01 — the opening: the name, come apart into light | [open](https://whereisxinyi.github.io/Light-on-Light/) | [`index.html`](index.html) |
| 02 — why this project | [open](https://whereisxinyi.github.io/Light-on-Light/concept.html) | [`concept.html`](concept.html) |
| 03 — write one sentence, receive a visual gift | [open](https://whereisxinyi.github.io/Light-on-Light/make.html) | [`make.html`](make.html) |

Also live on Vercel: <https://light-on-light.vercel.app/> — same pages,
plus the cloud drawing endpoint.

## How the gift gets drawn

[`make.html`](make.html) looks for its studio in this order:

1. **Same origin** — `/api/translate` (running [`server.py`](server.py)
   locally, or the Vercel site itself)
2. **The owner's machine** — `http://localhost:4180`. Run
   [`server.py`](server.py) on your computer, open either live site, and
   every gift is drawn by Claude (Haiku 4.5) through your own Claude Code
   login — no API key. The CORS allowlist only admits this project's
   origins, so other websites can't reach your machine.
3. **The cloud** — the Vercel function
   ([`api/translate.js`](api/translate.js)) drawing with **Gemini Flash**
   on a free-tier `GEMINI_API_KEY`. This is what every other visitor gets.
4. **Built-in generator** — if all three studios are unreachable, the
   in-page port of the hand-drawn-quote-art method takes over.

Gifts are always stamped honestly: `DRAWN BY CLAUDE`, `DRAWN BY GEMINI`,
or `DRAWN LOCALLY`.

## Cloud setup (one env var)

The Vercel function needs a free Gemini key: create one at
<https://aistudio.google.com/apikey>, then

```sh
vercel env add GEMINI_API_KEY production
vercel --prod
```

(`GEMINI_MODEL` optionally overrides the default `gemini-flash-latest`.)
The function has a per-instance rate limit and returns only sanitized SVG.

## Use it with your own Claude (no API key)

```sh
git clone https://github.com/whereisxinyi/Light-on-Light.git
cd Light-on-Light
python3 server.py
```

Then open the live site in the same machine's browser — the page finds the
studio at `localhost:4180` and `claude -p` draws the gifts.

## Development

```sh
python3 server.py    # http://localhost:4180 — pages + /api/translate bridge
python3 build.py     # rebuild the HTML from tokens.css / styles.css /
                     # concept.css / make.css — edit sources, not the HTML
```
