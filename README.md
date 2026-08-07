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

## How the gift gets drawn

[`make.html`](make.html) looks for its studio in this order:

1. **Same origin** — `/api/translate` (running [`server.py`](server.py)
   locally, or a serverless deploy of [`api/translate.js`](api/translate.js))
2. **The owner's machine** — `http://localhost:4180`. Run
   [`server.py`](server.py) on your computer, open the live site, and every
   gift is drawn by Claude through your own Claude Code login — no API key,
   no hosting bill. [`server.py`](server.py)'s CORS allowlist only admits
   this site's origin, so other websites can't reach your machine.
3. **Built-in generator** — everyone else gets the in-page port of the
   hand-drawn-quote-art method. Gifts are stamped `DRAWN BY CLAUDE` or
   `DRAWN LOCALLY` so it's always honest about which hand drew it.

## Use it with your own Claude (no API key)

```sh
git clone https://github.com/whereisxinyi/Light-on-Light.git
cd Light-on-Light
python3 server.py
```

Then open <https://whereisxinyi.github.io/Light-on-Light/make.html> in the
same machine's browser. That's it — the page finds the studio at
`localhost:4180` and `claude -p` (your Claude Code login) draws the gifts.

## Optional: serverless deploy (Vercel)

For gifts drawn by Claude even when your machine is off, import this repo
into [Vercel](https://vercel.com/new), add an `ANTHROPIC_API_KEY`
environment variable, and deploy — [`api/translate.js`](api/translate.js)
takes over as the same-origin studio. Each gift is one `claude-opus-5`
call (a few cents); the function carries a naive per-instance rate limit
and returns only sanitized SVG.

## Development

```sh
python3 server.py    # http://localhost:4180 — pages + /api/translate bridge
python3 build.py     # rebuild the HTML from tokens.css / styles.css /
                     # concept.css / make.css — edit sources, not the HTML
```
