# Light on Light

**Live: <https://whereisxinyi.github.io/Light-on-Light/>**

A quiet three-layer site: an opening screen where the name drifts as light,
a "why this project" concept page, and an instrument that translates one
sentence into a hand-drawn visual gift.

Pages embed their fonts and styles. Live drawing requires access to the
cloud studio; sharing and exporting preserve the generated artwork.

## Layers

| Layer | Live | Source |
|---|---|---|
| 01 — the opening: the name, come apart into light | [open](https://whereisxinyi.github.io/Light-on-Light/) | [`index.html`](index.html) |
| 02 — why this project | [open](https://whereisxinyi.github.io/Light-on-Light/concept.html) | [`concept.html`](concept.html) |
| 03 — write one sentence, receive a visual gift | [open](https://whereisxinyi.github.io/Light-on-Light/make.html) | [`make.html`](make.html) |

Also live on Vercel: <https://light-on-light.vercel.app/> — same pages,
plus the cloud drawing endpoint.

## How the gift gets drawn

Visitors submit a sentence to `/api/translate` on Vercel. GitHub Pages and
file previews call the same cloud endpoint directly; local development calls
its own studio. Public visitors never probe their computer's localhost.

The page waits for a newly generated SVG before opening the gift. It shows a
visible generation message and Cancel control while waiting. A failed or
timed-out request keeps the sentence and offers Try again. Gallery and
built-in drawings are never substituted for a live request.

The cloud tries the configured Gemini model followed by its built-in model
chain. Timeouts, unavailable models, and invalid SVG output advance to the
next model within a 120-second server budget. The browser allows 165 seconds,
including response parsing; the local Claude CLI has a 150-second limit.
Provider access errors stop the chain and visitors see a retryable error.

Generated SVG provenance remains inspectable on `#plate[data-via]`.

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

Deployment files (`api/`, `package.json`, `vercel.json`, `README.md`) are
maintained directly and preserved by `build.py`. The make page markup and
script live in `MAKE_BODY` and `MAKE_JS` inside `build.py`.

Run regression tests with `node --test tests/generation.test.js`.
