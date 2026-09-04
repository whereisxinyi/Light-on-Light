#!/usr/bin/env python3
"""
Build the bank: the drawings the page falls back to when the studio is out.

    python3 bank/generate.py                # every anchor, every seed sentence
    python3 bank/generate.py moon rain      # only these anchors
    python3 bank/generate.py --engine claude

Engine: Gemini if GEMINI_API_KEY is in the environment or ../.env.bank,
otherwise the local `claude` CLI (Haiku 4.5), exactly as server.py runs it.
Each drawing is sanitised (no text, no script, no frame rules) and saved as
bank/svg/<anchor>-<nn>.svg; bank/manifest.json lists them with keep: null
until the curation page decides. Re-running skips what exists.
"""
import json, os, pathlib, re, shutil, subprocess, sys, time, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SVG_DIR = HERE / "svg"
MANIFEST = HERE / "manifest.json"
SKILL_MD = pathlib.Path.home() / ".claude/skills/hand-drawn-quote-art/SKILL.md"

RULES = """
---

OUTPUT RULES — these override anything else:
- Reply with ONLY one <svg> element. No prose, no markdown fences, no title
  outside the SVG.
- viewBox="0 0 680 680". First child: <rect width="680" height="680"
  fill="#fdfdfb"/>. Ink is #1a1a1a only.
- NO TEXT of any kind in the SVG — no <text>, no lettering drawn as paths,
  no quotation marks. The page sets the sentence beneath the drawing itself.
- NO frame, border or box around the drawing. The drawing floats on the
  paper; the page provides the plate.
- Hand-drawn feel per the skill: stroke-dasharray breaks, irregular beziers,
  the whole drawing rotated 1-2 degrees (once).
- No <script>, no event handlers, no external references, no <image>.
"""

# Twenty anchors. The first nine are the page's own; the rest are the words
# people actually reach for that the page could not yet draw. Six sentences
# each, four English and two Chinese, spread across the skill's three modes.
SEEDS = {
  "rings":    ["Attention is the rarest kind of care.", "I am trying to stay in the room I am in.",
               "Listen, and the noise sorts itself.", "Hold still and the water clears.",
               "专注是最稀有的温柔。", "安静下来，世界才开始说话。"],
  "bleed":    ["Writing bleeds into everything.", "Some feelings spill before they are named.",
               "The ink knows where to go before I do.", "Everything I touch leaves a stain of me.",
               "有些话说出来就晕开了。", "墨比我先知道要去哪里。"],
  "spiral":   ["Every year I return to the same door.", "Memory turns, and turns again.",
               "I keep beginning at the beginning.", "The world goes round and I go with it.",
               "我总是回到同一个开始。", "记忆是一圈一圈的。"],
  "sprout":   ["What if I grow as a plant?", "Roots first, then whatever comes.",
               "Something green is starting in me.", "Let it grow crooked, it is still growing.",
               "先扎根，再说别的。", "有什么在我身上发芽了。"],
  "horizon":  ["I need some space.", "The sea remembers every name it was given.",
               "There is more sky than I can use.", "Far away is also a place.",
               "我需要一点空间。", "远方也是一个地方。"],
  "thread":   ["What if I'm a poem?", "Every word is a step on a road I cannot see.",
               "Follow the line and it becomes a story.", "I lost the thread but kept walking.",
               "我把线弄丢了，但还在走。", "每个字都是一步。"],
  "scatter":  ["I forgot what I was going to say.", "Fleeting things are still things.",
               "By evening the morning is gone.", "It slipped away while I was looking.",
               "刚想说什么，就忘了。", "转眼就散了。"],
  "weight":   ["Some days are heavier than they look.", "I carry more than I put down.",
               "Gravity has opinions about me.", "Put it down; it will still be there.",
               "有些日子比看起来重。", "先放下，它还会在。"],
  "contrast": ["I want to rest, but the list keeps growing.", "Half of me leaves, half stays.",
               "Loud outside, quiet inside.", "It is not the same, and yet it is.",
               "想休息，可清单还在变长。", "一半想走，一半想留。"],
  "moon":     ["The moon does not owe us a full face.", "Tonight I am mostly shadow.",
               "Night keeps what the day drops.", "What if I begin again at midnight?",
               "月亮不欠我们一张圆脸。", "夜里把白天掉的都收起来。"],
  "rain":     ["It rained and I let it.", "Small rain, all afternoon, no reason.",
               "Every drop lands where it was always going.", "I like weather that admits it is weather.",
               "下雨了，我就让它下。", "每一滴都落在它本来要去的地方。"],
  "window":   ["The window keeps a different sky than mine.", "I watched the light move across the wall.",
               "Something about the light today.", "Glass between me and the morning.",
               "窗户留着另一片天。", "今天的光有点不一样。"],
  "door":     ["Memory is a room with the door left open.", "I keep a door I never close.",
               "Not every exit is a leaving.", "Someone knocked and I answered late.",
               "记忆是一间门没关的房间。", "不是每次出门都是离开。"],
  "bridge":   ["Between us there is a bridge nobody built.", "I am halfway across and not looking down.",
               "Words are the bridge I keep repairing.", "Two shores, one crossing.",
               "我们之间有一座没人修的桥。", "走到一半，不往下看。"],
  "mountain": ["The mountain does not hurry.", "I climbed nothing today and that is fine.",
               "Some distances are meant to stay distant.", "Rest is also a summit.",
               "山不着急。", "有些远是用来看的。"],
  "fire":     ["A small fire is still a fire.", "I kept the match, not the flame.",
               "Something in me is still lit.", "Burn slow, last long.",
               "小火也是火。", "我留着火柴，没留火。"],
  "hand":     ["Say it once and it stays in the hand.", "I should call my mother.",
               "What we hold, holds us back a little.", "An open hand is also a shape.",
               "我该给妈妈打个电话。", "手张开也是一种形状。"],
  "home":     ["Home is where the light is left on.", "I am learning to be a house.",
               "Nothing you do not name stays.", "A roof is a promise about rain.",
               "家是留着灯的地方。", "没有名字的东西留不下来。"],
  "wait":     ["What if rest is the work?", "I am waiting, and the waiting is also mine.",
               "Patience is a slow kind of speed.", "The kettle knows something I don't.",
               "等待也是我的。", "如果休息就是工作呢？"],
  "farewell": ["Everything passing leaves a line.", "Goodbye is a long word said quickly.",
               "I let it go the way you let go of a kite.", "Some endings are just quieter middles.",
               "所有经过的，都留下一道线。", "再见是一个说得很快的长词。"],
}

def skill_text():
    return SKILL_MD.read_text(encoding="utf-8") if SKILL_MD.exists() else ""

def env_key():
    k = os.environ.get("GEMINI_API_KEY")
    if k: return k
    for name in (".env.bank", ".env.local"):
        p = ROOT / name
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"')
    return None

def sanitize(svg):
    svg = re.sub(r"<text[\s\S]*?</text>", "", svg, flags=re.I)
    svg = re.sub(r"<script[\s\S]*?</script>", "", svg, flags=re.I)
    svg = re.sub(r"\son\w+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", "", svg, flags=re.I)
    svg = re.sub(r"javascript:", "", svg, flags=re.I)
    svg = re.sub(r"<image[\s\S]*?>", "", svg, flags=re.I)
    return svg.strip()

def ask_gemini(key, sentence):
    models = ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-2.5-flash-lite", "gemini-2.5-flash"]
    body = json.dumps({
        "systemInstruction": {"parts": [{"text": skill_text() + RULES}]},
        "contents": [{"role": "user", "parts": [{"text":
            "TASK — apply the method above to this exact sentence, once, silently, then output the SVG:\n\n    「" + sentence + "」"}]}],
        "generationConfig": {"maxOutputTokens": 8192, "temperature": 1},
    }).encode()
    errs = []
    for model in models:
        for attempt in range(2):
            req = urllib.request.Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                data=body, headers={"Content-Type": "application/json", "x-goog-api-key": key})
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    data = json.load(r)
                text = "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
                m = re.search(r"<svg[\s\S]*?</svg>", text, re.I)
                if m: return m.group(0), "gemini"
                errs.append(f"{model}: no svg")
            except Exception as e:  # noqa
                errs.append(f"{model}: {str(e)[:80]}")
                time.sleep(1.5)
    raise RuntimeError(" | ".join(errs))

def ask_claude(sentence):
    cli = shutil.which("claude")
    if not cli: raise RuntimeError("claude CLI not on PATH")
    prompt = (skill_text() + RULES +
              "\n\nTASK — apply the method above to this exact sentence, once, silently, then output the SVG:\n\n    「" + sentence + "」\n")
    proc = subprocess.run([cli, "-p", "--model", "claude-haiku-4-5", "--output-format", "text"],
                          input=prompt, capture_output=True, text=True, timeout=180, cwd=str(ROOT))
    if proc.returncode != 0: raise RuntimeError(proc.stderr[:200])
    m = re.search(r"<svg[\s\S]*?</svg>", proc.stdout, re.I)
    if not m: raise RuntimeError("no svg in claude output")
    return m.group(0), "claude"

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    engine = "gemini" if env_key() else "claude"
    if "--engine" in sys.argv: engine = sys.argv[sys.argv.index("--engine") + 1]
    key = env_key()
    anchors = args or list(SEEDS)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"items": []}
    have = {it["file"] for it in manifest["items"]}
    SVG_DIR.mkdir(exist_ok=True)
    print(f"engine: {engine} · anchors: {len(anchors)}")
    for anchor in anchors:
        for i, sentence in enumerate(SEEDS[anchor]):
            fname = f"{anchor}-{i+1:02d}.svg"
            if fname in have: continue
            t0 = time.time()
            try:
                svg, via = ask_gemini(key, sentence) if engine == "gemini" else ask_claude(sentence)
            except Exception as e:
                print(f"  ✗ {fname}: {e}"); continue
            svg = sanitize(svg)
            (SVG_DIR / fname).write_text(svg, encoding="utf-8")
            manifest["items"].append({"file": fname, "anchor": anchor, "sentence": sentence,
                                      "engine": via, "keep": None, "bytes": len(svg.encode())})
            MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  ✓ {fname}  {len(svg):>5} B  {time.time()-t0:4.1f}s  {sentence}")
    print("done:", len(manifest["items"]), "drawings in the bank")

if __name__ == "__main__":
    main()
