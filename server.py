#!/usr/bin/env python3
"""
Light on Light — local studio server.

    python3 server.py            # http://localhost:4180

Serves the static pages AND exposes POST /api/translate, which hands the
sentence to the REAL hand-drawn-quote-art skill via the local `claude` CLI
(headless `-p` mode). No API key, no deployment: it rides the same Claude
Code login this machine already has.

The browser page falls back to its built-in generator when this endpoint is
unreachable (double-clicked file, CLI missing, timeout), so the pages stay
usable as plain files. This server is what makes the gift LLM-drawn.

Local only. Binds 127.0.0.1 — do not expose this port; anyone who can POST
to it can spend your Claude quota.
"""

import json
import pathlib
import re
import shutil
import subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = pathlib.Path(__file__).resolve().parent
PORT = 4180
SKILL_MD = pathlib.Path.home() / ".claude/skills/hand-drawn-quote-art/SKILL.md"
CLI_TIMEOUT = 150  # seconds; claude -p usually answers well inside this

SVG_RE = re.compile(r"<svg[\s\S]*?</svg>", re.IGNORECASE)


def skill_text() -> str:
    if SKILL_MD.exists():
        return SKILL_MD.read_text(encoding="utf-8")
    return ""


PROMPT = """{skill}

---

TASK — apply the method above to this exact sentence, once, silently:

    「{sentence}」

Follow the skill's own pipeline: pick the visual anchor, check the three
modes in their priority order (pun > contrast > literal), keep 1–2 visual
elements plus the sentence, leave generous whitespace.

OUTPUT RULES — these override anything else:
- Reply with ONLY one <svg> element. No prose, no markdown fences, no title
  outside the SVG.
- viewBox="0 0 680 680". First child: <rect width="680" height="680"
  fill="#fdfdfb"/>. Ink is #1a1a1a only.
- Text uses font-family="Segoe Print, Bradley Hand, Comic Sans MS, cursive".
  If the sentence is Chinese, hand-set the Chinese directly.
- Hand-drawn feel per the skill: stroke-dasharray breaks, irregular beziers,
  the whole text block rotated 1–2 degrees (once, not per glyph).
- No <script>, no event handlers, no external references, no <image>.
"""


def draw_with_claude(sentence: str) -> str:
    """Run the skill through claude -p. Returns SVG markup or raises."""
    cli = shutil.which("claude")
    if not cli:
        raise RuntimeError("claude CLI not on PATH")
    prompt = PROMPT.format(skill=skill_text(), sentence=sentence)
    # Prompt goes over stdin: the skill file opens with `---` frontmatter,
    # which argv-parsing reads as an option and chokes on.
    proc = subprocess.run(
        [cli, "-p", "--output-format", "text"],
        input=prompt, capture_output=True, text=True,
        timeout=CLI_TIMEOUT, cwd=str(HERE),
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude exited {proc.returncode}: {proc.stderr[:300]}")
    m = SVG_RE.search(proc.stdout)
    if not m:
        raise RuntimeError("no <svg> in claude output")
    svg = m.group(0)
    # Belt and braces: strip anything executable before it reaches a browser.
    svg = re.sub(r"<script[\s\S]*?</script>", "", svg, flags=re.I)
    svg = re.sub(r"\son\w+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", "", svg, flags=re.I)
    svg = re.sub(r"javascript:", "", svg, flags=re.I)
    svg = re.sub(r"<image[\s\S]*?>", "", svg, flags=re.I)
    return svg


class Studio(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(HERE), **kw)

    def do_POST(self):
        if self.path != "/api/translate":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            sentence = str(body.get("text", "")).strip()[:180]
            if len(sentence) < 2:
                raise ValueError("empty sentence")
            svg = draw_with_claude(sentence)
            payload = {"svg": svg, "via": "claude"}
            code = 200
        except Exception as e:  # noqa: BLE001 — every failure means "fall back"
            payload = {"error": str(e)[:200]}
            code = 502
        data = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):  # quieter logs, keep POSTs visible
        if self.command == "POST":
            super().log_message(fmt, *args)


if __name__ == "__main__":
    print(f"Light on Light studio · http://localhost:{PORT}"
          f" · skill file {'found' if SKILL_MD.exists() else 'MISSING'}"
          f" · claude CLI {'found' if shutil.which('claude') else 'MISSING'}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Studio).serve_forever()
