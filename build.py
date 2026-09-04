#!/usr/bin/env python3
"""
Build Light on Light's opening screen into a single self-contained index.html.

    python3 build.py

Inlines tokens.css + styles.css + the swarm generator + both webfonts
(base64 woff2, latin subsets) so the result opens straight from Finder with
zero network requests. Sources stay readable; index.html is the artifact.

Fonts are cached in ./_fonts/ after the first run. Delete that folder to
re-fetch. Instrument Serif and Geist Mono are both SIL OFL 1.1, which
permits embedding.
"""

import base64
import json
import pathlib
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
FONT_DIR = HERE / "_fonts"

# Latin subsets only — the page renders "Light on Light" and "LAYER 01",
# plus single latin letters in the swarm. Nothing else is needed.
FONTS = {
    "instrumentserif.woff2":
        "https://fonts.gstatic.com/s/instrumentserif/v5/"
        "jizBRFtNs2ka5fXjeivQ4LroWlx-6zUTjnTLgNs.woff2",
    "geistmono.woff2":
        "https://fonts.gstatic.com/s/geistmono/v6/"
        "or3yQ6H-1_WfwkMZI_qYPLs1a-t7PU0AbeE9KK5U5Cl4PuCTfNg.woff2",
    # Newsreader — the text face. Static instances (no opsz axis: 22–25 KB each
    # instead of 60), regular + medium + italic.
    "newsreader.woff2":        "https://fonts.gstatic.com/s/newsreader/v26/cY9qfjOCX1hbuyalUrK49dLac06G1ZGsZBtoBCzBDXXD9JVF438weI_wC-ZFHDWwgUii.woff2",
    "newsreader-medium.woff2": "https://fonts.gstatic.com/s/newsreader/v26/cY9qfjOCX1hbuyalUrK49dLac06G1ZGsZBtoBCzBDXXD9JVF438wSo_wC-ZFHDWwgUii.woff2",
    "newsreader-italic.woff2": "https://fonts.gstatic.com/s/newsreader/v26/cY9kfjOCX1hbuyalUrK439vogqC9yFZCYg7oRZaLP4obnf7fTXglsMwoT9ZHFjSShVCjzSY.woff2",
}
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def font_b64(name: str) -> str:
    FONT_DIR.mkdir(exist_ok=True)
    path = FONT_DIR / name
    if not path.exists():
        req = urllib.request.Request(FONTS[name], headers={"User-Agent": UA})
        with urllib.request.urlopen(req) as r:
            path.write_bytes(r.read())
        print(f"  fetched {name} ({path.stat().st_size:,} bytes)")
    return base64.b64encode(path.read_bytes()).decode()


FACES = """/* ------------------------------------------------------------
   Fonts, embedded. Latin subsets of Instrument Serif (display), Newsreader
   (text: regular, medium, italic) and Geist Mono, base64'd so this file
   needs no network at all — open it from Finder, from a USB stick, from a
   plane. All three are SIL Open Font License 1.1, which permits embedding.
   ------------------------------------------------------------ */
@font-face {
  font-family: "Instrument Serif";
  font-style: normal; font-weight: 400; font-display: swap;
  src: url(data:font/woff2;base64,__SERIF__) format("woff2");
}
@font-face {
  font-family: "Geist Mono";
  font-style: normal; font-weight: 400; font-display: swap;
  src: url(data:font/woff2;base64,__MONO__) format("woff2");
}
@font-face {
  font-family: "Newsreader";
  font-style: normal; font-weight: 400; font-display: swap;
  src: url(data:font/woff2;base64,__NR__) format("woff2");
}
@font-face {
  font-family: "Newsreader";
  font-style: normal; font-weight: 500; font-display: swap;
  src: url(data:font/woff2;base64,__NRM__) format("woff2");
}
@font-face {
  font-family: "Newsreader";
  font-style: italic; font-weight: 400; font-display: swap;
  src: url(data:font/woff2;base64,__NRI__) format("woff2");
}
"""

SWARM_JS = """
/* ------------------------------------------------------------
   The swarm generator.
   Builds the field of pixel lights and loose letters, dealing every
   element its own position, travel, size, opacity, blur, and four
   independent periods. Negative delays start each one mid-cycle, so
   nothing is ever in step. Runs once at load; after that the whole
   thing is CSS — no rAF loop, no scroll listener, no per-frame JS.
   ------------------------------------------------------------ */
(function () {
  var field = document.querySelector('.swarm');
  if (!field) return;

  var R      = function (a, b) { return a + Math.random() * (b - a); };
  var chance = function (p) { return Math.random() < p; };
  var clamp  = function (v, lo, hi) { return Math.max(lo, Math.min(hi, v)); };

  /* Density follows viewport AREA, not a phone/desktop switch — a 1440 window
     and a 1920 window shouldn't get the same handful of motes. Decided once,
     at load: regenerating on resize would visibly reshuffle the field. */
  var area     = window.innerWidth * window.innerHeight;
  var PX_COUNT = Math.round(clamp(area / 15000,  24, 72));
  var CH_COUNT = Math.round(clamp(area / 105000,  5, 13));
  /* The name, come apart. Repeats weight the commoner letters. */
  var LETTERS  = ['l', 'i', 'g', 'h', 't', 'o', 'n', 'L', 'g', 'h', 't'];

  function mote(kind) {
    var m = document.createElement('span');
    var b = document.createElement('span');
    var d = document.createElement('span');
    m.className = 'mote mote--' + kind;
    b.className = 'mote__b';
    d.className = 'mote__d';
    b.appendChild(d);
    m.appendChild(b);

    /* Custom properties inherit, so everything is set once, on the outer
       node, and the three animating levels each read what they need. */
    var set = function (k, v) { m.style.setProperty(k, v); };

    /* drift — the long wander that gathers and disperses the field */
    set('--x',  R(-6, 102).toFixed(2) + '%');
    set('--y',  R(-6, 98).toFixed(2)  + '%');
    set('--dx', R(-16, 16).toFixed(1) + 'vw');
    set('--dy', R(-13, 13).toFixed(1) + 'vh');
    set('--t1', R(15, 34).toFixed(1)   + 's');
    set('--d1', (-R(0, 34)).toFixed(1) + 's');

    /* bob — the bounce and swell riding on top of the drift. A third get a
       short, snappy toss (--ease-out, reversed by `alternate`, so it throws
       and falls); the rest just swell. */
    var springy = chance(0.34);
    set('--by', R(-3.4, 3.4).toFixed(2) + 'vh');
    set('--bs', R(0.58, 1.55).toFixed(2));
    set('--t2', (springy ? R(1.1, 3) : R(3, 7.5)).toFixed(2) + 's');
    set('--d2', (-R(0, 7.5)).toFixed(2) + 's');
    if (springy) m.style.setProperty('--e2', 'var(--ease-out)');

    /* Two thirds pulse without ever leaving — they hold a floor. One third
       goes all the way to nothing and comes back, the way the reference
       empties its field. Without the floor EVERY mote would sit near zero
       half the time, which halves the density you actually perceive. */
    var vanishes = chance(0.34);

    if (kind === 'px') {
      /* One in seven is a light; the rest are dust. Lights are SMALL and
         bright — a point, not a block. Dust may be larger and duller. An
         amber square big enough to read as a shape stops being light and
         starts looking like a UI error, which is what the first pass did. */
      var lit = chance(0.15);
      set('--c', lit ? 'var(--color-accent)'
                     : (chance(0.5) ? 'var(--color-ink-2)' : 'var(--color-neutral)'));
      set('--s', (lit ? R(1.5, 3.4) : R(2, 6.5)).toFixed(2) + 'px');
      var o = lit ? R(0.45, 0.78) : R(0.18, 0.52);
      set('--o', o.toFixed(3));
      set('--o0', (vanishes ? 0 : o * R(0.3, 0.58)).toFixed(3));
      /* A third twinkle fast, the rest breathe. The 0.9s floor is per
         iteration, and `alternate` means a full on-off cycle is 1.8s —
         about 0.55 Hz, well under the 3 Hz photosensitivity threshold.
         That threshold is the one thing this effect must not cross. */
      var fast = chance(0.36);
      set('--t3', (fast ? R(0.9, 2.4) : R(3.2, 9)).toFixed(2) + 's');
      set('--d3', (-R(0, 9)).toFixed(2) + 's');
    } else {
      set('--c', chance(0.2) ? 'var(--color-accent)' : 'var(--color-ink)');
      set('--s',  R(1.2, 5).toFixed(2)   + 'rem');
      var lo = R(0.09, 0.26);
      set('--o',  lo.toFixed(3));
      set('--o0', (vanishes ? 0 : lo * R(0.25, 0.5)).toFixed(3));
      set('--bl', R(0, 2.6).toFixed(2)   + 'px');   /* blur reads as depth */
      set('--t3', R(4.5, 12).toFixed(2)  + 's');
      set('--d3', (-R(0, 12)).toFixed(2) + 's');
      d.textContent = LETTERS[Math.floor(Math.random() * LETTERS.length)];
    }
    return m;
  }

  var frag = document.createDocumentFragment();
  var i;
  for (i = 0; i < PX_COUNT; i++) frag.appendChild(mote('px'));
  for (i = 0; i < CH_COUNT; i++) frag.appendChild(mote('ch'));
  field.appendChild(frag);
})();
"""

CONCEPT_JS = """
/* ------------------------------------------------------------
   Layer 02's two fields.

   `storm`  — the thoughts arriving. Each is dealt a position, a size, a
              blur, a drift, and its own flash cycle. The cycles are long
              (18–34s) but the visible window inside each is short (~36%),
              so at any moment only a handful are lit. That ratio is what
              makes it read as "occasional" rather than "a marquee".
   `sunk`   — the same voice, buried. Drifts down through the dark section
              and dims out. The pain point, said in motion.

   Runs once at load. After that it is all CSS — no rAF, no scroll listener.
   ------------------------------------------------------------ */
(function () {
  var R      = function (a, b) { return a + Math.random() * (b - a); };
  var chance = function (p) { return Math.random() < p; };

  /* The brief supplied the first three. The rest are written in the same
     register — first person, fragmentary, specific enough to be somebody's. */
  var THOUGHTS = [
    'What if I grow as a plant?',
    "What if I'm a poem?",
    'I need some space\\u2026',
    'What if silence has a colour?',
    'I should call my mother.',
    'What if the sea remembers?',
    'Why did I keep this?',
    "What if I'm early, not late?",
    'Something about the light today.',
    'What if rest is the work?',
    'I forgot what I was going to say.',
    'What if I begin again on a Tuesday?',
    'What if nobody is watching?',
    'The word for this in another language.'
  ];

  function shuffled() {
    var a = THOUGHTS.slice(), i, j, t;
    for (i = a.length - 1; i > 0; i--) {
      j = Math.floor(Math.random() * (i + 1));
      t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  var narrow = window.innerWidth < 640;

  /* ---- storm ---- */
  var storm = document.querySelector('.storm__field');
  if (storm) {
    var pool  = shuffled();
    var count = Math.min(pool.length, narrow ? 5 :
                Math.max(7, Math.round(window.innerWidth * window.innerHeight / 105000)));
    var frag  = document.createDocumentFragment();

    /* Each thought owns a horizontal band and jitters inside it. Fully random
       y collides constantly once the column is narrow — two thoughts lit in the
       same place is unreadable, and no amount of tuning opacity fixes it.
       Banding rules the collision out structurally. */
    var band = 64 / count;

    for (var i = 0; i < count; i++) {
      var p = document.createElement('span');
      var t = document.createElement('span');
      p.className = 'pop';
      t.className = 'pop__t';
      t.textContent = pool[i];
      p.appendChild(t);

      var set = function (el) { return function (k, v) { el.style.setProperty(k, v); }; }(p);

      /* Kept clear of the bottom-left corner, where the note sits. */
      set('--x', (narrow ? R(3, 22) : R(4, 70)).toFixed(2) + '%');
      set('--y', (10 + i * band + R(0.1, 0.55) * band).toFixed(2) + '%');   /* 10%: air under the wordmark */
      /* Drift stays under half a band so it can't wander into a neighbour. */
      set('--dx', R(-5, 5).toFixed(2) + 'vw');
      set('--dy', (narrow ? R(-1.4, 1.4) : R(-3, 3)).toFixed(2) + 'vh');
      set('--t1', R(20, 38).toFixed(1) + 's');
      set('--d1', (-R(0, 38)).toFixed(1) + 's');

      /* A few sit further back — smaller and fainter. (Not blurred: see the
         note on .pop__t in concept.css.) */
      var near = chance(0.55);
      /* Capped under the note's size: a thought is texture behind the
         narrator's line, never a second headline. And never amber — the
         accent lands on the turn and the invitation, nowhere else. */
      set('--s',  (near ? R(1.1, 1.5) : R(0.95, 1.1)).toFixed(2) + 'rem');
      set('--o',  (near ? R(0.62, 0.9) : R(0.3, 0.5)).toFixed(2));
      set('--c',  'var(--color-ink)');

      set('--t2', R(18, 34).toFixed(1)   + 's');
      set('--d2', (-R(0, 34)).toFixed(1) + 's');

      frag.appendChild(p);
    }
    storm.appendChild(frag);
  }

  /* ---- the dark field ----
     Dense on purpose: the whole pool of thoughts, popping in and sinking out
     of the dark. This field IS the pain point — it replaces the sentence that
     used to say it. Banded so nothing overlaps; held to one side of the copy
     column so the lede always wins. */
  var dark = document.querySelector('.swarm-dark');
  if (dark) {
    var pool2  = shuffled();
    var many   = narrow ? 6 : pool2.length;
    /* Desktop: the upper 56% of the night — the lede is top-left, the turn
       bottom-right, so the field lives beside the lede and above the turn.
       Narrow: one column, so the field takes the gap between the two. */
    var sband  = (narrow ? 24 : 52) / many;
    var sfrom  = narrow ? 36 : 4;
    var frag2  = document.createDocumentFragment();
    for (var k = 0; k < many; k++) {
      var s = document.createElement('span');
      s.className = 'sunk__t';
      s.textContent = pool2[k];
      s.style.setProperty('--x',  (narrow ? R(6, 40) : R(38, 80)).toFixed(2) + '%');
      s.style.setProperty('--y',  (sfrom + k * sband + R(0.1, 0.5) * sband).toFixed(2) + '%');
      s.style.setProperty('--s',  R(0.95, 1.45).toFixed(2) + 'rem');
      s.style.setProperty('--o',  (narrow ? R(0.12, 0.24) : R(0.24, 0.5)).toFixed(2));
      s.style.setProperty('--t1', R(9, 16).toFixed(1)    + 's');
      s.style.setProperty('--d1', (-R(0, 16)).toFixed(1) + 's');
      frag2.appendChild(s);
    }
    dark.appendChild(frag2);
  }

  /* ---- plates ----
     Floating, heavily blurred photographs behind the turn.

     THESE ARE SWAPPABLE SLOTS. Each plate paints whatever is in --img.
     With no --img it falls back to one of the soft two-stop fields below,
     which at this blur is what a photograph looks like anyway. To use
     real pictures, set --img on the plate:  --img: url('./photos/01.jpg')
     Nothing else has to change.

     Restraint is structural, not by eye: opacity is capped at 0.34,
     saturation pulled to 0.55, and the blur floor is high enough that no
     plate can resolve into a subject that competes with the question. */
  var plates = document.querySelector('.plates');
  if (plates) {
    var FIELDS = [
      'radial-gradient(118% 92% at 32% 26%, color-mix(in oklch, var(--color-accent) 30%, transparent), transparent 74%),' +
      'radial-gradient(104% 84% at 74% 72%, color-mix(in oklch, var(--color-paper-3) 40%, transparent), transparent 72%)',

      'radial-gradient(110% 96% at 68% 30%, color-mix(in oklch, var(--color-glow) 46%, transparent), transparent 70%),' +
      'radial-gradient(96% 88% at 28% 74%, color-mix(in oklch, var(--color-neutral) 34%, transparent), transparent 74%)',

      'radial-gradient(124% 88% at 46% 68%, color-mix(in oklch, var(--color-paper-3) 52%, transparent), transparent 72%),' +
      'radial-gradient(90% 80% at 76% 22%, color-mix(in oklch, var(--color-accent) 22%, transparent), transparent 70%)',

      'radial-gradient(112% 90% at 24% 58%, color-mix(in oklch, var(--color-glow) 38%, transparent), transparent 72%),' +
      'radial-gradient(100% 86% at 70% 34%, color-mix(in oklch, var(--color-paper-3) 36%, transparent), transparent 74%)'
    ];
    var RATIOS = ['4 / 3', '3 / 4', '1 / 1', '16 / 10', '5 / 4'];

    var pcount = narrow ? 3 : 5;
    var pband  = 66 / pcount;   /* from 24% down: the plates belong to the turn */
    var frag3  = document.createDocumentFragment();
    for (var n = 0; n < pcount; n++) {
      var pl = document.createElement('span');
      pl.className = 'plate';
      var ps = function (el) { return function (k, v) { el.style.setProperty(k, v); }; }(pl);
      ps('--img', FIELDS[n % FIELDS.length]);
      ps('--ar',  RATIOS[Math.floor(Math.random() * RATIOS.length)]);
      ps('--x',   R(-6, 74).toFixed(2) + '%');
      ps('--y',   (24 + n * pband + R(0.05, 0.4) * pband).toFixed(2) + '%');
      ps('--w',   (narrow ? R(46, 78) : R(20, 40)).toFixed(1) + 'vw');
      ps('--bl',  R(14, 22).toFixed(1) + 'px');   /* the fields are already soft; heavy blur only cost frames */
      ps('--o',   R(0.18, 0.34).toFixed(2));
      ps('--dx',  R(-4, 4).toFixed(2) + 'vw');
      ps('--dy',  R(-3, 3).toFixed(2) + 'vh');
      ps('--t',   R(26, 46).toFixed(1)   + 's');
      ps('--d',   (-R(0, 46)).toFixed(1) + 's');
      frag3.appendChild(pl);
    }
    plates.appendChild(frag3);
  }
})();
"""

CONCEPT_BODY = """
<a class="skip" href="#invite">Skip to the invitation</a>

<!-- Grain source — the same paper as layer 01. -->
<svg class="filters" aria-hidden="true" focusable="false" width="0" height="0">
  <filter id="grain">
    <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/>
    <feColorMatrix type="saturate" values="0"/>
  </filter>
</svg>
<div class="grain" aria-hidden="true"></div>

<header class="mast">
  <h1 class="mast__h"><a href="./index.html">Light on Light</a></h1>
  <p class="mast__layer">LAYER 02 &mdash; WHY THIS PROJECT</p>
</header>

<main>

  <!-- Thoughts arriving. Populated by the generator below. -->
  <section class="storm">
    <div class="storm__field" aria-hidden="true"></div>
    <p class="storm__note">Thoughts arrive all day. You keep almost none of them.</p>
  </section>

  <!-- Night · one dark section, two moments. The light goes out over a dusk
       band at the top, the pain and the turn share one field (so no thought
       or plate is ever sliced at a seam), and the light comes back over a
       dawn band at the bottom, into the idea. -->
  <section class="night">
    <div class="swarm-dark" aria-hidden="true"></div>
    <div class="plates" aria-hidden="true"></div>
    <p class="beat__lede night__pain">Thoughts arrive in the shower, on the platform, halfway
      through someone else&rsquo;s sentence. Then the feed arrives, and by lunch
      there is nothing left to remember.</p>
    <h2 class="beat__turn night__turn">What if an image could <span class="lit">respond</span>
      to a thought?</h2>
  </section>

  <!-- The idea. Paper, fully back. -->
  <section class="beat beat--light">
    <h2 class="beat__ask">How can fleeting thoughts become meaningful memories?</h2>
  </section>

  <!-- The last fold. Layer 01's haze comes back here, quieter, so the page
       ends on the paper it began on. -->
  <section class="give" id="invite">
    <div class="haze" aria-hidden="true">
      <span class="haze__l haze__l--a"></span>
      <span class="haze__l haze__l--c"></span>
      <span class="haze__glow"></span>
    </div>
  </section>

  <!-- The invitation. Sticky, not fixed: it rides the bottom edge of the
       viewport the whole way down, then settles here as the page's last
       element instead of hovering over the colophon. -->
  <div class="dock">
    <a class="cta" href="./make.html">Unwrap My Gift</a>
  </div>

</main>

<footer class="colophon">
  <span>Light on Light</span>
  <span class="colophon__sep" aria-hidden="true">&middot;</span>
  <span>Layer 02</span>
  <span class="colophon__sep" aria-hidden="true">&middot;</span>
  <a href="./index.html">Back to the beginning</a>
</footer>

<!-- The substrate. Beneath the paper, the name as the machine holds it:
     a bitmap that flickers like something still running. -->
<aside class="substrate" aria-hidden="true">
  <canvas class="substrate__px" id="substrate"></canvas>
</aside>
"""

BODY = """
<!-- Grain source. Generated, desaturated, and multiplied over the whole field. -->
<svg class="filters" aria-hidden="true" focusable="false" width="0" height="0">
  <filter id="grain">
    <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/>
    <feColorMatrix type="saturate" values="0"/>
  </filter>
</svg>

<main class="field">

  <!-- The seam: LAYER 01's own progress. It grows, recedes, and never
       completes, because the layer isn't finished forming. -->
  <span class="seam" aria-hidden="true"></span>

  <!-- The ground: 透明层叠 — three multiply layers, one screen-blend light,
       one grain. The mass with weight. -->
  <div class="haze" aria-hidden="true">
    <span class="haze__l haze__l--a"></span>
    <span class="haze__l haze__l--b"></span>
    <span class="haze__l haze__l--c"></span>
    <span class="haze__glow"></span>
    <span class="haze__grain"></span>
  </div>

  <!-- The name, come apart. Populated by the generator below. -->
  <div class="swarm" aria-hidden="true"></div>

  <h1 class="mark">
    <a class="mark__link" href="./concept.html">Light on Light</a>
  </h1>

  <p class="stamp" aria-hidden="true">LAYER 01</p>

</main>
"""


MAKE_BODY = """
<a class="skip" href="#field">Skip to writing</a>

<!-- Grain source — the same paper as layers 01 and 02. -->
<svg class="filters" aria-hidden="true" focusable="false" width="0" height="0">
  <filter id="grain">
    <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/>
    <feColorMatrix type="saturate" values="0"/>
  </filter>
</svg>
<div class="grain" aria-hidden="true"></div>

<header class="mast">
  <h1 class="mast__h"><a href="./index.html">Light on Light</a></h1>
  <p class="mast__layer" id="stamp">LAYER 03 &mdash; YOUR VISUAL GIFT</p>
</header>

<main class="stage">

  <!-- Layer 01's haze, quieter. You write on the paper the name settled on. -->
  <div class="haze" aria-hidden="true">
    <span class="haze__l haze__l--a"></span>
    <span class="haze__l haze__l--c"></span>
    <span class="haze__glow"></span>
  </div>

  <!-- INPUT · low and left, where layer 01 put the wordmark. -->
  <section class="panel panel--ask">
    <form class="ask" id="ask" autocomplete="off">
      <h2 class="ask__greet">What passed through your mind today?</h2>
      <div class="ask__row">
        <label class="sr" for="field">Your thought</label>
        <textarea class="ask__field" id="field" name="thought" rows="1" maxlength="180"
                  placeholder="One sentence is enough"></textarea>
        <button class="cta ask__go" id="go" type="submit" disabled>Translate it</button>
      </div>
    </form>
  </section>

  <!-- FORMING — no spinner. The sentence comes apart and gathers; the
       stamp in the masthead says what is happening. -->
  <div class="forming" aria-hidden="true">
    <div class="forming__field" id="sparks"></div>
    <p class="forming__echo" id="echo"></p>
  </div>

  <!-- GIFT · the mount. Sentence, date and the two actions on one side,
       the plate on the other; the whole thing sized to sit inside one screen. -->
  <section class="panel panel--gift">
    <figure class="gift" id="gift">
      <figcaption class="gift__line" id="giftLine"></figcaption>
      <div class="gift__plate" id="plate" role="img" aria-label="A hand-drawn illustration made from your sentence"></div>
      <div class="gift__meta">
        <span class="gift__rule" aria-hidden="true"></span>
        <span id="giftDate"></span>
        <span class="gift__via" id="giftVia"></span>
      </div>
      <div class="gift__actions">
        <button class="cta" id="export" type="button">Export</button>
        <button class="gift__again" id="again" type="button">Write another</button>
        <button class="gift__again" id="redraw" type="button" hidden>Try the studio again</button>
      </div>
    </figure>
  </section>

</main>

<p class="sr" id="live" role="status" aria-live="polite"></p>

<footer class="colophon">
  <span>Light on Light</span>
  <span class="colophon__sep" aria-hidden="true">&middot;</span>
  <span>Layer 03</span>
  <span class="colophon__sep" aria-hidden="true">&middot;</span>
  <a href="./concept.html">Why this project</a>
</footer>

<!-- The substrate. Beneath the paper, the name as the machine holds it:
     a bitmap that flickers like something still running. -->
<aside class="substrate" aria-hidden="true">
  <canvas class="substrate__px" id="substrate"></canvas>
</aside>
"""


SUBSTRATE_JS = r"""
/* ------------------------------------------------------------
   The substrate.
   Beneath the paper the name exists as a bitmap — the way the machine
   holds it — and it flickers the way something still running does: a
   cell dims for a frame or three and recovers, a read head sweeps through
   the word, a caret blinks after the last letter. Canvas, ~12 fps, drawn
   only while on screen; one still frame under reduced motion. No cell
   ever flickers faster than the read head passes, well under 3 Hz.
   ------------------------------------------------------------ */
(function () {
  var canvas = document.getElementById('substrate');
  if (!canvas || !canvas.getContext) return;
  var ctx = canvas.getContext('2d');
  /* Fewer, larger cells on a phone: a 3px cell is a texture, not a letter. */
  var narrow = window.innerWidth < 640;
  var COLS = narrow ? 72 : 112, ROWS = narrow ? 15 : 22, GAP = 0.18, TEXT = 'Light on Light';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var css = getComputedStyle(document.documentElement);
  var tok = function (name, fb) { var v = css.getPropertyValue(name).trim(); return v || fb; };
  var LIGHT = tok('--color-ink-paper', '#e8e2da');
  var AMBER = tok('--color-accent', '#c07a2a');

  var cells = [], caret = { c: 0, r: 0 }, cw = 0;

  /* Rasterise the wordmark at cell resolution and keep every cell the
     letters touch. Edge cells keep their partial coverage as a dimmer base,
     which is what makes it read as the serif face and not a blob. */
  function sample() {
    var off = document.createElement('canvas');
    off.width = COLS; off.height = ROWS;
    var o = off.getContext('2d');
    var size = ROWS * 0.86, face = '"Instrument Serif", Georgia, serif';
    o.font = size + 'px ' + face;
    var w = o.measureText(TEXT).width, maxW = COLS - 8;
    if (w > maxW) { size *= maxW / w; o.font = size + 'px ' + face; w = o.measureText(TEXT).width; }
    var x = Math.floor((COLS - w) / 2), y = Math.round(ROWS * 0.74);
    o.fillStyle = '#fff';
    o.fillText(TEXT, x, y);
    var d = o.getImageData(0, 0, COLS, ROWS).data;
    cells = [];
    for (var r = 0; r < ROWS; r++) {
      for (var c = 0; c < COLS; c++) {
        var a = d[(r * COLS + c) * 4 + 3] / 255;
        if (a < 0.22) continue;
        cells.push({ c: c, r: r, base: 0.45 + 0.5 * Math.min(1, a * 1.15),
                     amber: Math.random() < 0.025, dip: 0, left: 0 });
      }
    }
    caret.c = Math.min(COLS - 2, Math.ceil(x + w) + 2);
    caret.r = y;
  }

  function layout() {
    var dpr = Math.min(2, window.devicePixelRatio || 1);
    var cssW = canvas.clientWidth || canvas.parentNode.clientWidth || 600;
    cw = cssW / COLS;
    canvas.width = Math.round(cssW * dpr);
    canvas.height = Math.round(cw * ROWS * dpr);
    canvas.style.height = (cw * ROWS) + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  var sweep = -4, caretOn = true, frame = 0, last = 0, running = false, onScreen = false, raf = 0;

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    var pad = cw * GAP, s = cw - pad * 2;
    for (var i = 0; i < cells.length; i++) {
      var k = cells[i], b = k.base;
      if (!reduce) {
        if (k.left > 0) { b = k.dip; k.left--; }
        else if (Math.random() < 0.002) { k.dip = 0.06 + Math.random() * 0.24; k.left = 1 + Math.floor(Math.random() * 3); }
        var dc = Math.abs(k.c - sweep);
        if (dc < 3) b = Math.min(1, b + (3 - dc) * 0.14);
      }
      ctx.globalAlpha = b;
      ctx.fillStyle = k.amber ? AMBER : LIGHT;
      ctx.fillRect(k.c * cw + pad, k.r * cw + pad, s, s);
    }
    if (caretOn || reduce) {
      ctx.globalAlpha = 0.9;
      ctx.fillStyle = AMBER;
      ctx.fillRect(caret.c * cw + pad, (caret.r - 3) * cw + pad, s, cw * 4 - pad * 2);
    }
    ctx.globalAlpha = 1;
  }

  function tick(now) {
    if (!running) return;
    raf = requestAnimationFrame(tick);
    if (now - last < 83) return;            /* ~12 fps is plenty for a bitmap */
    last = now; frame++;
    sweep += 0.6; if (sweep > COLS + 6) sweep = -4;   /* one pass ≈ 16 s */
    if (frame % 11 === 0) caretOn = !caretOn;         /* ≈ 0.55 Hz */
    draw();
  }
  function start() { if (running || reduce || !onScreen || document.hidden) return; running = true; raf = requestAnimationFrame(tick); }
  function stop()  { running = false; cancelAnimationFrame(raf); }

  function boot() {
    layout(); sample(); draw();
    if (reduce) return;
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) {
        onScreen = es[0].isIntersecting; onScreen ? start() : stop();
      }, { threshold: 0.05 }).observe(canvas);
    } else { onScreen = true; start(); }
    document.addEventListener('visibilitychange', function () { document.hidden ? stop() : start(); });
    var rt;
    window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(function () { layout(); draw(); }, 120); });
  }
  /* Sample only once the real face is in, or the bitmap is Georgia's. */
  var ready = (document.fonts && document.fonts.load) ? document.fonts.load('20px "Instrument Serif"') : Promise.resolve();
  ready.then(boot, boot);
})();
"""


MAKE_JS = r"""
/* ============================================================================
   Layer 03 — the instrument.

   WHAT THIS IS, HONESTLY
   `hand-drawn-quote-art` is a Claude Code skill: it runs in an agent, not in a
   browser, so this page cannot call it. What it does instead is carry the
   skill's METHOD across — the anchor-word extraction, the three-mode priority,
   and the whole visual specification (ink #1a1a1a on paper #fdfdfb, the
   handwriting stack, dashes instead of solid strokes, irregular beziers,
   1–2 degrees of tilt, one or two elements and no more, a 680 square).

   The judgement is therefore a lookup, not an LLM's reading. It is good on the
   concrete words people actually reach for and plain on the ones it has never
   seen — where it falls back to Mode 1, exactly as the skill instructs. The
   studio chain above it (Claude locally, Gemini in the cloud) is the real
   thing; this generator is the always-there floor beneath both.

   SEEDED, NOT RANDOM
   Every random draw comes from a hash of your sentence. The same thought
   always makes the same picture. A gift should be determined by the thing it
   is a gift about.
   ============================================================================ */
(function () {
  'use strict';

  var $ = function (id) { return document.getElementById(id); };
  var body = document.body;

  /* ---------- seeded randomness ---------- */
  function hash(str) {
    var h = 2166136261 >>> 0;
    for (var i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 16777619) >>> 0;
    }
    return h >>> 0;
  }
  function rngFrom(seed) {
    var a = seed >>> 0;
    return function () {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      var t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }

  /* ---------- the skill's step 2: find a visual anchor ----------
     Not the most important word — the one that can become a shape. */
  var STOP = ('a an the and or but if of to in on at for with from into over '
    + 'is am are was were be been being do does did done have has had i me my '
    + 'you your he she it we they them this that these those there here what '
    + 'when where why how not no yes so as by up out just very really some any '
    + 'about would could should will can may might must its it’s '
    + "i'm i’m i've i’ve don't don’t didn't didn’t isn't isn’t it's can't can’t "
    + "won't won’t you're you’re that's that’s there's there’s").split(' ');

  /* Crude, deliberately: enough to see through a plural or a tense so that
     "bleeds" reaches the pun list that only knows "bleed". A real stemmer
     would be more than this lookup deserves. */
  function stems(w) {
    var out = [w];
    if (/ies$/.test(w)) out.push(w.slice(0, -3) + 'y');
    if (/ing$/.test(w)) { out.push(w.slice(0, -3)); out.push(w.slice(0, -3) + 'e'); }
    if (/ed$/.test(w))  { out.push(w.slice(0, -2)); out.push(w.slice(0, -1)); }
    if (/e?s$/.test(w)) { out.push(w.replace(/e?s$/, '')); out.push(w.slice(0, -1)); }
    return out;
  }

  /* word -> shape. Each shape is a drawing the skill would recognise. */
  var ANCHOR = {
    rings:   'attention focus centre center notice listen watch quiet still hold wait patience present ' +
             'aware awake careful care mind minds mindful concentrate around circle',
    bleed:   'bleed spread soak leak seep spill ink stain blur everything through spreads bleeds ' +
             'saturate flood pour drown wash',
    spiral:  'again return world back repeat cycle turn spin round loop memory remember returning ' +
             'circles orbit endless forever begin beginning start',
    sprout:  'grow grows growing plant plants seed seeds root roots tree leaf leaves bloom flower ' +
             'garden spring alive become becoming green branch',
    horizon: 'space room breathe breath sea ocean sky far distance horizon alone empty quiet ' +
             'silence wide open outside field air light morning',
    thread:  'thread path way line walk road journey follow lost find story trail wander drift ' +
             'route trace connect between across poem poems word words song songs letter ' +
             'sentence write writing wrote read reading language name',
    scatter: 'forget forgot scatter gone lose lost disappear fade vanish leave leaving fleeting ' +
             'moment brief passing slip escape almost never',
    weight:  'weight heavy carry hold burden load lift press down pull gravity anchor sink deep'
  };

  /* Words with a literal AND a figurative sense — the skill's Mode 2, its
     highest-priority mode. Drawing the literal one and letting the reader
     arrive at the other is where this style earns its keep. */
  var PUNS = ('bleed grow root plant weight light hold break drift seed spark thread anchor bloom '
    + 'fall reach current shadow space run fold carry water burn sink float land ground touch').split(' ');

  /* Mode 3 fires when the sentence sets two things against each other. */
  var CONTRAST_MARKS = [' but ', ' yet ', ' versus ', ' vs ', ' instead of ', ' rather than ',
                        ' and not ', ' or ', ' between '];

  /* The same maps for Chinese. There are no spaces to split on, so these are
     matched as substrings of the whole sentence; the longest hit per shape
     wins, and longer hits beat shorter ones across shapes (清晨 beats 光).
     Without this table every Chinese sentence missed every anchor and fell
     into the same default rings — a wall of near-identical gifts. */
  var ANCHOR_ZH = {
    rings:   '专注 注意 倾听 聆听 安静 宁静 平静 耐心 等待 当下 中心 凝视 目光 守护 陪伴 圆 环',
    bleed:   '晕开 蔓延 弥漫 淹没 流淌 渗 墨 染 浸 洇',
    spiral:  '重复 循环 旋转 回来 回去 记忆 回忆 永远 又一次 再一次 开始 轮回 归 绕',
    sprout:  '生长 成长 种子 种下 扎根 开花 发芽 生命 成为 长出 根 树 叶 花 春 绿 枝',
    horizon: '呼吸 大海 天空 远方 距离 地平线 孤独 独自 空旷 辽阔 田野 清晨 阳光 黎明 自由 海 风 光 晨',
    thread:  '旅程 旅行 跟随 迷路 寻找 找到 故事 文字 句子 语言 名字 连接 线 路 诗 字 词 歌 信 写 读 桥',
    scatter: '忘记 遗忘 散落 消失 淡去 逝去 离开 瞬间 短暂 溜走 错过 飘散 流逝 来不及',
    weight:  '重量 沉重 背负 负担 举起 下沉 深处 放下 扛 压 锚'
  };
  var PUNS_ZH = '光 重 根 线 沉 深 流 落 散 长 断 种 背 转 空 浮 烧 触 折'.split(' ');
  var CONTRAST_ZH = ['但', '却', '而是', '而不是', '与其', '宁可', '宁愿', '还是', '可是',
                     '然而', '反而', '不如'];

  function candsZH(text) {
    var out = [];
    for (var key in ANCHOR_ZH) {
      var list = ANCHOR_ZH[key].split(' ');
      var best = null;
      for (var i = 0; i < list.length; i++) {
        if (text.indexOf(list[i]) > -1 && (!best || list[i].length > best.length)) best = list[i];
      }
      if (best) {
        out.push({ word: best, shape: key,
                   pun: PUNS_ZH.some(function (p) { return best.indexOf(p) > -1; }) });
      }
    }
    out.sort(function (a, b) { return b.word.length - a.word.length; });
    return out;
  }

  function words(text) {
    return text.toLowerCase().replace(/[^\p{L}\p{N}\s'’]/gu, ' ')
               .split(/\s+/).filter(Boolean);
  }

  function analyse(text) {
    var w = words(text);
    var meaty = w.filter(function (x) { return STOP.indexOf(x) === -1 && x.length > 2; });

    /* Collect every word that maps to a shape, then choose.
       The skill puts Mode 2 first — "命中就优先用" — so a word with a double
       sense beats an earlier word without one. Scanning left-to-right and
       taking the first hit gets "Writing bleeds into everything" wrong: it
       lands on `writing` and throws away the pun the whole line is built on. */
    var cands = [];
    for (var i = 0; i < meaty.length; i++) {
      var forms = stems(meaty[i]);
      for (var key in ANCHOR) {
        var list = ANCHOR[key].split(' ');
        if (forms.some(function (f) { return list.indexOf(f) > -1; })) {
          cands.push({ word: meaty[i], shape: key,
                       pun: forms.some(function (f) { return PUNS.indexOf(f) > -1; }) });
          break;
        }
      }
    }
    if (/[一-鿿]/.test(text)) { cands = cands.concat(candsZH(text)); }
    var chosen = cands.filter(function (c) { return c.pun; })[0] || cands[0] || null;
    var anchor = chosen ? chosen.word : null;
    var shape  = chosen ? chosen.shape : null;

    var lower = ' ' + text.toLowerCase() + ' ';
    var hasContrast = CONTRAST_MARKS.some(function (m) { return lower.indexOf(m) > -1; })
                   || CONTRAST_ZH.some(function (m) { return text.indexOf(m) > -1; });
    var isPun = !!(chosen && chosen.pun);

    /* The skill's priority order, checked in order: 2 beats 3 beats 1. */
    var mode = isPun ? 2 : (hasContrast ? 3 : 1);
    if (!shape) { shape = 'rings'; }          /* Mode 1 is the fallback, per the skill */
    if (mode === 3) { shape = 'contrast'; }

    return { anchor: anchor || (meaty[0] || 'thought'), shape: shape, mode: mode };
  }

  /* ---------- hand-drawn primitives ----------
     Regular geometry reads as a UI icon. Everything below is nudged
     off-true on purpose: broken strokes, asymmetric control points. */
  var INK = '#1a1a1a';

  function jitterPath(pts, r, amt) {
    var d = '';
    for (var i = 0; i < pts.length; i++) {
      var x = pts[i][0] + (r() - 0.5) * amt;
      var y = pts[i][1] + (r() - 0.5) * amt;
      if (i === 0) { d += 'M' + x.toFixed(1) + ' ' + y.toFixed(1); }
      else {
        var px = pts[i - 1][0], py = pts[i - 1][1];
        var cx = (px + x) / 2 + (r() - 0.5) * amt * 1.6;
        var cy = (py + y) / 2 + (r() - 0.5) * amt * 1.6;
        d += ' Q' + cx.toFixed(1) + ' ' + cy.toFixed(1) + ' ' + x.toFixed(1) + ' ' + y.toFixed(1);
      }
    }
    return d;
  }
  function stroke(d, w, dash) {
    return '<path d="' + d + '" fill="none" stroke="' + INK + '" stroke-width="' + w +
           '" stroke-linecap="round"' + (dash ? ' stroke-dasharray="' + dash + '"' : '') + '/>';
  }
  function dot(x, y, r) {
    return '<circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="' + r.toFixed(1) + '" fill="' + INK + '"/>';
  }
  function blob(cx, cy, rad, r) {
    var pts = [], n = 13;
    for (var i = 0; i < n; i++) {
      var a = (i / n) * Math.PI * 2;
      var rr = rad * (0.74 + r() * 0.46);
      pts.push([cx + Math.cos(a) * rr, cy + Math.sin(a) * rr]);
    }
    pts.push(pts[0]);
    return '<path d="' + jitterPath(pts, r, 8) + ' Z" fill="' + INK + '"/>';
  }

  /* ---------- the eight drawings ---------- */
  var SHAPES = {
    rings: function (r) {
      var out = [], n = 4 + Math.floor(r() * 2);
      for (var i = 0; i < n; i++) {
        var rad = 58 + i * (44 + r() * 14);
        out.push('<circle cx="340" cy="352" r="' + rad.toFixed(0) + '" fill="none" stroke="' + INK +
                 '" stroke-width="2.2" stroke-dasharray="' + (3 + i) + ' ' + (9 + i) + '"/>');
      }
      out.push(dot(340, 352, 4.5));
      return out;
    },
    bleed: function (r) {
      var out = [blob(340, 340, 104, r)];
      var n = 14 + Math.floor(r() * 6);
      for (var i = 0; i < n; i++) {
        var a = r() * Math.PI * 2, d = 165 + r() * 250;
        out.push(dot(340 + Math.cos(a) * d, 340 + Math.sin(a) * d * 0.88, 2 + r() * 4.5));
      }
      return out;
    },
    spiral: function (r) {
      var pts = [], turns = 3.2 + r() * 0.9;
      for (var i = 0; i <= 130; i++) {
        var t = i / 130, a = t * Math.PI * 2 * turns, rad = 16 + t * 236;
        pts.push([340 + Math.cos(a) * rad, 344 + Math.sin(a) * rad]);
      }
      return [stroke(jitterPath(pts, r, 3), 2.2, '5 9'), dot(340, 344, 4)];
    },
    sprout: function (r) {
      var stem = [];
      for (var i = 0; i <= 10; i++) {
        var t = i / 10;
        stem.push([340 + Math.sin(t * 2.3) * 40, 588 - t * 452]);
      }
      var out = [stroke(jitterPath(stem, r, 5), 2.6, null)];
      for (var k = 0; k < 3; k++) {
        var y = 470 - k * 132, dir = k % 2 ? 1 : -1;
        var leaf = [[340, y], [340 + dir * 92, y - 48], [340 + dir * 158, y - 8],
                    [340 + dir * 74, y + 30], [340, y]];
        out.push(stroke(jitterPath(leaf, r, 7), 2.2, '4 9'));
      }
      out.push(dot(340, 596, 5));
      return out;
    },
    horizon: function (r) {
      var line = [];
      for (var i = 0; i <= 10; i++) { line.push([70 + i * 54, 430]); }
      var out = [stroke(jitterPath(line, r, 5), 2.2, null)];
      out.push(stroke(jitterPath([[340, 430], [338, 352], [342, 286]], r, 6), 2, '4 10'));
      for (var i = 0; i < 7; i++) {
        out.push(dot(140 + r() * 400, 180 + r() * 150, 2 + r() * 3));
      }
      return out;
    },
    thread: function (r) {
      var pts = [];
      for (var i = 0; i <= 16; i++) {
        var t = i / 16;
        pts.push([90 + t * 500, 380 + Math.sin(t * 5.4) * 122]);
      }
      var out = [stroke(jitterPath(pts, r, 7), 2.2, '6 10')];
      out.push('<circle cx="' + (90 + 0.62 * 500).toFixed(0) + '" cy="' +
               (380 + Math.sin(0.62 * 5.4) * 122).toFixed(0) +
               '" r="15" fill="none" stroke="' + INK + '" stroke-width="2.2"/>');
      return out;
    },
    scatter: function (r) {
      var out = [blob(238, 356, 40, r)];
      var n = 20 + Math.floor(r() * 8);
      for (var i = 0; i < n; i++) {
        var t = i / n;
        out.push(dot(268 + t * 330 + (r() - 0.5) * 60,
                     356 + (r() - 0.5) * 250 * t + 10, Math.max(1.4, 6 * (1 - t))));
      }
      return out;
    },
    weight: function (r) {
      var out = [blob(340, 470, 116, r)];
      for (var i = 0; i < 6; i++) {
        var y = 292 - i * 46;
        out.push(stroke(jitterPath([[196 - i * 20, y], [484 + i * 20, y]], r, 5), 2.2,
                        (3 + i) + ' ' + (8 + i)));
      }
      return out;
    },
    /* Mode 3 — one eye looking at two kinds of thing. */
    contrast: function (r) {
      var out = [];
      for (var i = 0; i <= 5; i++) {
        out.push(stroke(jitterPath([[76, 196 + i * 60], [286, 196 + i * 60]], r, 2), 1.6, '2 6'));
        out.push(stroke(jitterPath([[76 + i * 42, 196], [76 + i * 42, 496]], r, 2), 1.6, '2 6'));
      }
      out.push(stroke(jitterPath([[340, 168], [336, 300], [344, 420], [338, 528]], r, 7), 2, '4 9'));
      var sc = [];
      for (var k = 0; k <= 22; k++) {
        var t = k / 22;
        sc.push([420 + Math.sin(t * 11) * 88 + t * 70, 250 + Math.cos(t * 8.5) * 96 + t * 40]);
      }
      out.push(stroke(jitterPath(sc, r, 9), 2.2, null));
      return out;
    }
  };

  /* ---------- assemble the plate ---------- */
  function draw(text) {
    var a = analyse(text);
    var r = rngFrom(hash(text.trim().toLowerCase()));
    var parts = SHAPES[a.shape](r);
    var tilt = (r() * 2 - 1) * 1.4;                    /* the skill's 1–2 degrees, once */
    var inner = parts.map(function (p, i) {
      return p.replace(/^<(\w+)/, '<$1 data-i style="--i:' + i + '"');
    }).join('');
    var svg =
      '<svg viewBox="0 0 680 680" role="img" xmlns="http://www.w3.org/2000/svg">' +
      '<rect x="0" y="0" width="680" height="680" fill="#fdfdfb"/>' +
      '<g transform="rotate(' + tilt.toFixed(2) + ' 340 340)">' + inner + '</g></svg>';
    return { svg: svg, meta: a };
  }

  /* ---------- state ---------- */
  var field = $('field'), go = $('go'), live = $('live'), form = $('ask');
  var current = { text: '', date: '' };

  var layerStamp = $('stamp'), LAYER_STAMP = layerStamp.textContent;
  function setState(s) {
    body.dataset.state = s;
    layerStamp.textContent = s === 'forming' ? 'LAYER 03 \u2014 GENERATING\u2026' : LAYER_STAMP;
    if (s === 'forming') { live.textContent = 'Translating your sentence.'; }
    if (s === 'gift') { live.textContent = 'Your gift is ready. Export saves it as a JPG.'; }
  }

  field.addEventListener('input', function () {
    body.dataset.ready = field.value.trim().length > 1 ? 'yes' : 'no';
    go.disabled = field.value.trim().length < 2;
  });
  /* Enter sends; Shift+Enter makes a new line. */
  field.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); }
  });

  function stamp(d) {
    var M = ['JANUARY','FEBRUARY','MARCH','APRIL','MAY','JUNE','JULY',
             'AUGUST','SEPTEMBER','OCTOBER','NOVEMBER','DECEMBER'];
    return String(d.getDate()).padStart(2, '0') + ' ' + M[d.getMonth()] + ' ' + d.getFullYear();
  }

  /* ---------- forming: dissolve, then gather. No spinner. ---------- */
  function sow(text) {
    var host = $('sparks');
    host.textContent = '';
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce) return;
    var r = rngFrom(hash(text) ^ 0x9e37);
    var n = Math.min(52, 16 + text.length);
    var frag = document.createDocumentFragment();
    for (var i = 0; i < n; i++) {
      var s = document.createElement('span');
      s.className = 'spark';
      var x = 8 + r() * 84, y = 26 + r() * 48;
      s.style.setProperty('--x', x.toFixed(2) + '%');
      s.style.setProperty('--y', y.toFixed(2) + '%');
      /* everything travels toward the middle, where the plate will be */
      s.style.setProperty('--gx', ((50 - x) * 0.9).toFixed(2) + 'vw');
      s.style.setProperty('--gy', ((50 - y) * 0.62).toFixed(2) + 'vh');
      s.style.setProperty('--s', (1.6 + r() * 3.6).toFixed(2) + 'px');
      s.style.setProperty('--o', (0.2 + r() * 0.5).toFixed(2));
      s.style.setProperty('--c', r() < 0.16 ? 'var(--color-accent)' : 'var(--color-ink-2)');
      s.style.setProperty('--t', (2.6 + r() * 2.4).toFixed(2) + 's');
      s.style.setProperty('--d', (-r() * 4).toFixed(2) + 's');
      frag.appendChild(s);
    }
    host.appendChild(frag);
  }

  /* Injected markup is injected markup, whoever drew it. */
  function sanitizeSVG(raw) {
    return raw
      .replace(/<script[\s\S]*?<\/script>/gi, '')
      .replace(/\son\w+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)/gi, '')
      .replace(/javascript:/gi, '');
  }

  function present(text, art) {
    var d = new Date();
    current.text = text;
    current.date = stamp(d);
    $('giftLine').textContent = text;          /* textContent, never innerHTML */
    var plate = $('plate');
    plate.innerHTML = art.svg;
    /* Assemble centre-outward whoever drew it: deal data-i to the top-level
       strokes so the CSS stagger also applies to SVGs that arrive without it. */
    var root = plate.querySelector('svg');
    if (root) {
      var host = root.querySelector('g') || root;
      var idx = 0;
      Array.prototype.forEach.call(host.children, function (el) {
        if (el.tagName.toLowerCase() === 'rect') return;
        el.setAttribute('data-i', '');
        el.style.setProperty('--i', idx++);
      });
    }
    /* Left on the element on purpose: who drew it, and (for local draws)
       which anchor and mode fired. Inspectable rather than mysterious. */
    plate.dataset.via = art.via;
    if (art.meta) {
      plate.dataset.anchor = art.meta.anchor;
      plate.dataset.mode = String(art.meta.mode);
      plate.dataset.shape = art.meta.shape;
    }
    $('giftDate').textContent = current.date;
    /* One universal stamp — the gift is signed by the project, not the
       engine. Which hand actually drew it stays recorded on
       plate.dataset.via (claude / gemini / local) for anyone who inspects. */
    $('giftVia').textContent = 'DRAWN BY \u201CLight on Light\u201D' +
      (art.via === 'local' ? ' \u00B7 OFFLINE' : '');   /* the built-in floor is not the product's ceiling; say so */
    $('redraw').hidden = art.via !== 'local';            /* …and offer the studio again */
    setState('gift');
  }

  /* The real skill, through the studio server (server.py → claude -p).
     The studio can live in two places, tried in order:
       1. same origin — server.py locally, or a serverless deploy
       2. the owner's own machine at http://localhost:4180 — browsers treat
          localhost as a trustworthy origin, so even the HTTPS public page
          may call it; server.py's CORS allowlist decides who is let in.
     So the owner opens the public site with server.py running and gifts are
     drawn by Claude on her own login; every other visitor quietly falls
     through to the cloud studio or the built-in generator. The forming state holds as long
     as it takes; there is no spinner to lie with, only the gathering. */
  function callStudio(url, text) {
    var ctrl = new AbortController();
    var kill = setTimeout(function () { ctrl.abort(); }, 160000);
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text }),
      signal: ctrl.signal
    }).then(function (r) {
      clearTimeout(kill);
      if (!r.ok) throw new Error('studio ' + r.status);
      return r.json();
    }).then(function (j) {
      if (!j.svg || j.svg.indexOf('<svg') !== 0) throw new Error('no svg');
      return { svg: sanitizeSVG(j.svg), via: j.via || 'claude', meta: null };
    });
  }

  /* Three studios, tried in order:
       1. same origin            — server.py locally, or the Vercel site itself
       2. the owner's machine    — localhost:4180 → her own Claude login
       3. the cloud              — the Vercel function → Gemini Flash
     So the owner's Claude wins when her server is up; everyone else still
     gets an LLM-drawn gift from the cloud; and only if all three are down
     does the built-in generator take over. */
  function askClaude(text) {
    var home = 'http://localhost:4180';
    var cloud = 'https://light-on-light.vercel.app';
    return callStudio('/api/translate', text)['catch'](function (err) {
      if (window.location.origin === home) throw err;   /* already tried it */
      return callStudio(home + '/api/translate', text);
    })['catch'](function (err) {
      if (window.location.origin === cloud) throw err;  /* already tried it */
      return callStudio(cloud + '/api/translate', text);
    });
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var text = field.value.trim().replace(/\s+/g, ' ');
    if (text.length < 2) return;

    $('echo').textContent = text;
    sow(text);
    setState('forming');

    /* Claude first; the built-in generator only when the studio is
       unreachable (double-clicked file, CLI missing, timeout). The gift
       always says which hand drew it. */
    var art = askClaude(text)['catch'](function () {
      var local = draw(text);
      return { svg: local.svg, via: 'local', meta: local.meta };
    });
    var floor = new Promise(function (res) { setTimeout(res, 2600); });
    Promise.all([art, floor]).then(function (v) { present(text, v[0]); });
  });

  /* Same sentence, another knock on the studio's door. The free-tier cloud
     fails in bursts, so a second try a minute later usually draws. */
  $('redraw').addEventListener('click', function () {
    field.value = current.text;
    body.dataset.ready = 'yes';
    go.disabled = false;
    form.requestSubmit();
  });

  $('again').addEventListener('click', function () {
    field.value = '';
    body.dataset.ready = 'no';
    go.disabled = true;
    setState('input');
    field.focus();
  });

  /* ---------- export ----------
     ONE fixed template, always. Same ground, same plate, same margins, same
     date position, same type. That is what makes a year of these read as one
     body of work instead of a folder of unrelated pictures. */
  var CARD = { w: 1080, h: 1400, scale: 2 };

  function cssVar(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }

  function wrap(ctx, text, maxW) {
    var out = [], line = '', w = text.split(' ');
    for (var i = 0; i < w.length; i++) {
      var test = line ? line + ' ' + w[i] : w[i];
      if (ctx.measureText(test).width > maxW && line) { out.push(line); line = w[i]; }
      else { line = test; }
    }
    if (line) out.push(line);
    return out.slice(0, 4);
  }

  $('export').addEventListener('click', function () {
    var btn = this;
    btn.disabled = true;
    var svgMarkup = $('plate').innerHTML;
    var blobUrl = URL.createObjectURL(new Blob([svgMarkup], { type: 'image/svg+xml;charset=utf-8' }));
    var img = new Image();

    img.onload = function () {
      var c = document.createElement('canvas');
      c.width = CARD.w * CARD.scale;
      c.height = CARD.h * CARD.scale;
      var ctx = c.getContext('2d');
      ctx.scale(CARD.scale, CARD.scale);

      /* ground — the site's warm paper; the plate is a print in a mount */
      ctx.fillStyle = cssVar('--color-paper') || '#f7f3ee';
      ctx.fillRect(0, 0, CARD.w, CARD.h);

      /* the sentence, in the skill's hand, tilted once */
      ctx.save();
      ctx.translate(CARD.w / 2, 0);
      ctx.rotate(-0.7 * Math.PI / 180);
      ctx.fillStyle = cssVar('--color-plate-ink') || '#1a1a1a';
      ctx.textAlign = 'center';
      ctx.font = 'italic 40px ' + (cssVar('--font-voice') || 'serif');   /* same voice as on screen */
      var lines = wrap(ctx, current.text, CARD.w - 220);
      var top = 156 - (lines.length - 1) * 27;
      lines.forEach(function (l, i) { ctx.fillText(l, 0, top + i * 54); });
      ctx.restore();

      /* the plate. 156 above the sentence, 88 below the series mark: the card
         sits INTO itself rather than floating in the middle of its own frame. */
      var P = { x: 140, y: 300, s: 800 };
      ctx.fillStyle = cssVar('--color-plate-paper') || '#fdfdfb';
      ctx.fillRect(P.x, P.y, P.s, P.s);
      ctx.drawImage(img, P.x, P.y, P.s, P.s);
      ctx.strokeStyle = cssVar('--color-rule') || '#d8d2c8';
      ctx.lineWidth = 1;
      ctx.strokeRect(P.x + 0.5, P.y + 0.5, P.s - 1, P.s - 1);

      /* rule, date, series mark */
      ctx.fillStyle = cssVar('--color-rule') || '#d8d2c8';
      ctx.fillRect(CARD.w / 2 - 20, 1218, 40, 1);
      ctx.textAlign = 'center';
      ctx.fillStyle = cssVar('--color-ink-2') || '#4a443c';
      ctx.font = '17px ' + (cssVar('--font-mono') || 'monospace');
      ctx.fillText(spaced(current.date), CARD.w / 2, 1270);
      ctx.fillStyle = cssVar('--color-muted') || '#7d766b';
      ctx.font = '14px ' + (cssVar('--font-mono') || 'monospace');
      ctx.fillText(spaced('LIGHT ON LIGHT'), CARD.w / 2, 1312);

      var a = document.createElement('a');
      a.download = 'light-on-light-' + isoDay() + '.jpg';
      a.href = c.toDataURL('image/jpeg', 0.92);
      a.click();
      URL.revokeObjectURL(blobUrl);
      btn.disabled = false;
      live.textContent = 'Saved as JPG.';
    };
    img.onerror = function () {
      URL.revokeObjectURL(blobUrl);
      btn.disabled = false;
      live.textContent = 'That illustration could not be rendered. Try writing another.';
    };
    img.src = blobUrl;
  });

  function spaced(s) { return s.split('').join(' '); }
  function isoDay() {
    var d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') +
           '-' + String(d.getDate()).padStart(2, '0');
  }

  setState('input');
  body.dataset.ready = 'no';
})();
"""


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>__TITLE__</title>
<meta name="description" content="__DESC__">
<meta name="color-scheme" content="light">
<!-- The mark: the same semicolon whereisxinyi.github.io wears, verbatim, so the
     two sites share one icon. Inline SVG: still zero network requests. -->
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect x='1.5' y='1.5' width='61' height='61' rx='14' fill='%23ffffff' stroke='%23dcdad6' stroke-width='2'/%3E%3Ctext x='32' y='46' text-anchor='middle' font-family='Fraunces,Georgia,serif' font-size='44' font-weight='600' fill='%23241f1c'%3E;%3C/text%3E%3C/svg%3E">
<link rel="apple-touch-icon" href="./apple-touch-icon.png">

<style>
__FACES__
__TOKENS__
__STYLES__
</style>
</head>
<body>
__BODY__
<script>__JS__</script>
</body>
</html>
"""


def render(out_name, title, desc, css_file, body, js, faces, tokens):
    styles = (HERE / css_file).read_text(encoding="utf-8")
    html = (PAGE
            .replace("__TITLE__", title)
            .replace("__DESC__", desc)
            .replace("__FACES__", faces)
            .replace("__TOKENS__", tokens)
            .replace("__STYLES__", styles)
            .replace("__BODY__", body)
            .replace("__JS__", js))
    out = HERE / out_name
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out.name} — {len(html.encode('utf-8')):,} bytes")


DEPLOY_API_JS = r"""// /api/translate — the studio, deployable.
// Vercel serverless function (Node 18+). Calls Gemini Flash over plain REST —
// no npm dependencies at all. The hand-drawn-quote-art skill text rides as the
// system instruction. Set GEMINI_API_KEY in the project env (free keys at
// aistudio.google.com/apikey); GEMINI_MODEL, if set, is tried first, ahead
// of the built-in model chain.

const SKILL = `__SKILL__`;

const RULES = `
---

OUTPUT RULES — these override anything else:
- Reply with ONLY one <svg> element. No prose, no markdown fences, no title
  outside the SVG.
- viewBox="0 0 680 680". First child: <rect width="680" height="680"
  fill="#fdfdfb"/>. Ink is #1a1a1a only.
- Text uses font-family="Segoe Print, Bradley Hand, Comic Sans MS, cursive".
  If the sentence is Chinese, hand-set the Chinese directly.
- Hand-drawn feel per the skill: stroke-dasharray breaks, irregular beziers,
  the whole text block rotated 1-2 degrees (once, not per glyph).
- No <script>, no event handlers, no external references, no <image>.
`;

// Origins allowed to call this function from another site — the GitHub Pages
// mirror, local dev, and pages opened straight from disk. Same-origin calls
// (the Vercel site itself) don't need CORS at all.
const ALLOWED_ORIGINS = new Set([
  "https://whereisxinyi.github.io",
  "http://localhost:4180",
  "http://127.0.0.1:4180",
  "null",
]);

function cors(req, res) {
  const origin = req.headers.origin || "";
  if (ALLOWED_ORIGINS.has(origin)) {
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Vary", "Origin");
  }
}

// Naive per-instance rate limit. Serverless instances don't share memory, so
// this is a speed bump, not a wall — for real limiting put Upstash/KV here.
const hits = new Map();
const WINDOW_MS = 10 * 60 * 1000;
const MAX_HITS = 10;

export default async function handler(req, res) {
  cors(req, res);

  if (req.method === "OPTIONS") {
    res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");
    res.setHeader("Access-Control-Max-Age", "86400");
    res.status(204).end();
    return;
  }
  if (req.method !== "POST") {
    res.status(405).json({ error: "POST only" });
    return;
  }

  const key = process.env.GEMINI_API_KEY;
  if (!key) {
    res.status(502).json({ error: "GEMINI_API_KEY is not configured" });
    return;
  }

  const ip =
    String(req.headers["x-forwarded-for"] || "").split(",")[0].trim() ||
    "unknown";
  const now = Date.now();
  const recent = (hits.get(ip) || []).filter((t) => now - t < WINDOW_MS);
  if (recent.length >= MAX_HITS) {
    res.status(429).json({ error: "rate limited — try again in a few minutes" });
    return;
  }
  recent.push(now);
  hits.set(ip, recent);

  const sentence = String(req.body?.text ?? "").trim().slice(0, 180);
  if (sentence.length < 2) {
    res.status(400).json({ error: "empty sentence" });
    return;
  }

  // Free-tier Gemini 503s ("high demand") come and go per model, so one
  // model, one attempt means one bad minute drops every visitor to the
  // page's built-in generator. Walk a chain instead — two tries per model,
  // a short breath between — before giving up.
  // Aliases first (they track whatever Google currently points them at),
  // then pinned stable models. Retired ids 404 and the chain just moves on.
  const MODELS = [...new Set([
    process.env.GEMINI_MODEL,
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
  ].filter(Boolean))];

  const ask = (model) =>
    fetch(
      "https://generativelanguage.googleapis.com/v1beta/models/" +
        model + ":generateContent",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-goog-api-key": key,
        },
        body: JSON.stringify({
          systemInstruction: { parts: [{ text: SKILL + RULES }] },
          contents: [
            {
              role: "user",
              parts: [
                {
                  text:
                    "TASK — apply the method above to this exact sentence, " +
                    "once, silently, then output the SVG:\n\n    「" +
                    sentence + "」",
                },
              ],
            },
          ],
          generationConfig: { maxOutputTokens: 8192, temperature: 1 },
        }),
      },
    );

  try {
    let r = null;
    const errs = [];
    outer: for (const model of MODELS) {
      for (let attempt = 0; attempt < 2; attempt++) {
        let resp;
        try {
          resp = await ask(model);
        } catch (e) {
          errs.push(model + ": " + String(e?.message || e).slice(0, 80));
          continue;
        }
        if (resp.ok) { r = resp; break outer; }
        errs.push(model + " " + resp.status + ": " +
          (await resp.text()).replace(/\s+/g, " ").slice(0, 80));
        // 4xx other than 429 (retired model, bad request) won't heal on
        // retry — move straight to the next model in the chain.
        if (resp.status !== 429 && resp.status < 500) break;
        await new Promise((t) => setTimeout(t, 1200));
      }
    }

    if (!r) {
      // Every model's failure, so one look at this payload tells the whole
      // story instead of only the last link in the chain.
      res.status(502).json({ error: errs.join(" | ") || "gemini unavailable" });
      return;
    }

    const data = await r.json();
    const text = (data.candidates?.[0]?.content?.parts || [])
      .map((p) => p.text || "")
      .join("");
    const match = text.match(/<svg[\s\S]*?<\/svg>/i);
    if (!match) {
      res.status(502).json({ error: "no svg in model output" });
      return;
    }

    // Belt and braces before it reaches any browser.
    const svg = match[0]
      .replace(/<script[\s\S]*?<\/script>/gi, "")
      .replace(/\son\w+\s*=\s*("[^"]*"|\'[^\']*\'|[^\s>]+)/gi, "")
      .replace(/javascript:/gi, "")
      .replace(/<image[\s\S]*?>/gi, "");

    res.status(200).json({ svg, via: "gemini" });
  } catch (err) {
    res.status(502).json({ error: String(err?.message || err).slice(0, 200) });
  }
}
"""

DEPLOY_README = """# Light on Light

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

Every gift carries the same signature — `DRAWN BY “Light on Light”` —
whichever studio drew it; the engine (claude / gemini / local) is recorded
on the artwork element's `data-via` attribute for anyone who inspects.

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
"""


def deploy() -> None:
    """Write the deployable pieces at the repo root: api/, package.json,
    vercel.json, README. GitHub Pages ignores them; Vercel picks them up."""
    (HERE / "api").mkdir(exist_ok=True)

    # Inline the skill text into the function as a JS template literal.
    skill_js = (skill_text()
                .replace("\\", "\\\\")
                .replace("`", "\\`")
                .replace("${", "\\${"))
    (HERE / "api" / "translate.js").write_text(
        DEPLOY_API_JS.replace("__SKILL__", skill_js), encoding="utf-8")

    (HERE / "package.json").write_text(json.dumps({
        "name": "light-on-light",
        "private": True,
        "type": "module",
    }, indent=2) + "\n", encoding="utf-8")

    (HERE / "vercel.json").write_text(json.dumps({
        "functions": {"api/translate.js": {"maxDuration": 300}},
    }, indent=2) + "\n", encoding="utf-8")

    (HERE / "README.md").write_text(DEPLOY_README, encoding="utf-8")
    print("wrote api/translate.js + package.json + vercel.json + README.md")


def skill_text() -> str:
    p = pathlib.Path.home() / ".claude/skills/hand-drawn-quote-art/SKILL.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def main() -> None:
    tokens = (HERE / "tokens.css").read_text(encoding="utf-8").replace(
        " * Every colour and font in styles.css references a token from this file.\n",
        " * Every colour and font below references a token from this block.\n")

    faces = (FACES
             .replace("__SERIF__", font_b64("instrumentserif.woff2"))
             .replace("__MONO__",  font_b64("geistmono.woff2"))
             .replace("__NR__",    font_b64("newsreader.woff2"))
             .replace("__NRM__",   font_b64("newsreader-medium.woff2"))
             .replace("__NRI__",   font_b64("newsreader-italic.woff2")))

    render("index.html", "Light on Light", "Light on Light.",
           "styles.css", BODY, SWARM_JS, faces, tokens)

    render("concept.html",
           "Light on Light",
           "Thoughts arrive all day. You keep almost none of them.",
           "concept.css", CONCEPT_BODY, CONCEPT_JS + SUBSTRATE_JS, faces, tokens)

    render("make.html",
           "Light on Light",
           "What passed through your mind today?",
           "make.css", MAKE_BODY, MAKE_JS + SUBSTRATE_JS, faces, tokens)

    deploy()


if __name__ == "__main__":
    main()
