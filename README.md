# Light on Light

A quiet three-layer site: an opening screen where the name drifts as light,
a "why this project" concept page, and an instrument that translates one
sentence into a hand-drawn visual gift.

Every page is a single self-contained HTML file — fonts embedded, zero
network requests. Open them from disk, from GitHub Pages, from anywhere.

## Layers

| Page | Layer |
|---|---|
| `index.html` | 01 — the opening: the name, come apart into light |
| `concept.html` | 02 — why this project |
| `make.html` | 03 — write one sentence, receive a visual gift |

## Two ways to serve it

**Static (GitHub Pages)** — works as-is. The gift page uses its built-in
generator (a port of the hand-drawn-quote-art method) and stamps each gift
`DRAWN LOCALLY`. No keys, no cost.

**With the LLM (Vercel)** — import this repo into Vercel, then:

```sh
vercel env add ANTHROPIC_API_KEY   # a key from console.anthropic.com
vercel --prod
```

`/api/translate` comes alive and every sentence is drawn by `claude-opus-5`
running the real hand-drawn-quote-art skill; gifts stamp `DRAWN BY CLAUDE`.
If the endpoint is unreachable the page falls back to the local generator —
the deploy never hard-breaks.

### Costs and safety

- Each gift is one `claude-opus-5` call (~2–4K input at cached rates after
  the first request, ~1–2K output) — a few cents per gift.
- `api/translate.js` has a naive per-instance rate limit (8 requests /
  10 min / IP). Serverless instances don't share memory, so treat it as a
  speed bump; for real protection add Upstash Ratelimit or Vercel KV.
- `vercel.json` sets `maxDuration: 300`. If your plan rejects that, lower
  it to 60 — generations at `effort: "low"` normally finish well inside it.
- The function returns only sanitized `<svg>` (no scripts, handlers, or
  external references), and the page sanitizes again before mounting.

## Local development

```sh
python3 server.py    # http://localhost:4180 — bridges /api/translate to the
                     # local `claude` CLI (Claude Code login, no API key)
python3 build.py     # rebuild the HTML from tokens.css / styles.css /
                     # concept.css / make.css — edit sources, not the HTML
```
