// /api/translate — the studio, deployable.
// Vercel serverless function (Node). Calls the Anthropic API directly with the
// official SDK; the hand-drawn-quote-art skill text rides as a cached system
// prompt, so every request after the first reads it at ~0.1x price.
import Anthropic from "@anthropic-ai/sdk";

const SKILL = `---
name: hand-drawn-quote-art
description: 黑白手绘风插画配图方案生成器——参考 Jon Gray《Stay Sturdy》一类"极简线条/圆点/涂鸦 + 手写体短句"的插画书风格，把一句喜欢的话转化为可执行的视觉创作方案并生成SVG预览图。当用户提到"手绘插画"、"quote插画"、"引文插画"、"艺术书"、"黑白插画"、"配图方案"、"每日一图一句话"、"插画+文字"、"这句话怎么配图"时立即触发。也适用于用户说"这段话能不能做成插画"、"帮我想个插画点子"、"帮我出几个方案"、"这句话我想画个图"等表达。即使用户只是粘贴了一段喜欢的话说"帮我配个图"，只要意图是把一句引文转化为极简手绘黑白插画方案，都应触发此skill。覆盖从关键词提取、三种构思模式选择，到用 mcp__visualize__show_widget 生成SVG预览的完整流程。
---

# 黑白手绘引文插画生成器

这个 skill 封装的是一套"从一句话到一张插画"的具体方法论，参考的是 Jon Gray（《Stay Sturdy》一书作者）那种极简手绘线条 + 手写体短句的风格。这类风格的高级感不来自画技，而来自**一个聪明的图文咬合点 + 克制的留白**——所以整个流程的重点是先想清楚"点子"，再动笔，不要一上来就堆细节。

## 整体流程

1. **拿到一句话** —— 如果用户没给，先问他们最近喜欢的一句话/quote（中英文都行，控制在1-2句以内；太长的话要先帮用户挑出最值得做视觉主体的那一句，其余降级为辅助小字或干脆不放）。

2. **提取一个"视觉锚点"关键词或短语** —— 从句子里挑一个自带图形联想的词，不是随便挑最重要的词，而是挑那个**能变成具体形状、动作或空间关系**的词。判断标准：这个词能不能在脑子里立刻浮现出一个简笔画？能就是好锚点。
   - 例："world" → 圆/螺旋（包裹感），"worthy" → 靶心/勋章（成就感），"attention" → 聚焦的同心圈，"bleed" → 墨迹晕染
   - 如果句子里没有明显的具象词，退而求其次找一个**空间/动作关系**（谁围绕谁、谁对比谁、什么在扩散/收缩）

3. **选构思模式** —— 三种模式不是并列选项，是有优先级的判断顺序，按顺序检查，命中哪个就用哪个（如果用户要多方案对比，可以三个都生成）：

   **模式一·字面锚点**（默认兜底模式，适用范围最广）
   把关键词直接变成图形符号，文字手写体环绕或紧贴图形排布。图形不需要"画得像"，越简化越好——一个点、一组同心圈、一条螺旋线就够了。这是最容易执行也最不容易出错的模式，没有更好的点子时就用它。

   **模式二·双关谐音**（优先级最高，命中就优先用）
   检查关键词是否同时有字面义和比喻义（比如 bleed 既是"流血/渗出"又是"（情绪、影响）蔓延"）。如果有，就把字面义画出来，让读者自己联想到比喻义——这种"话没说满"的处理是这类风格最出彩的地方，比直白图解高级得多。

   **模式三·对比并置**
   如果句子里明确出现了两个相对/相反的意象或概念（比如"structure" vs "mundane moment"，"公司"vs"家里"，"计划"vs"意外"），把画面分成两半，用不同的视觉语言表现两边（一边整齐规则，一边随性涂鸦），中间用一条手绘分割线连接，暗示"是同一双眼睛在看两种东西"。

4. **生成 SVG 预览** —— 用 \`mcp__visualize__show_widget\` 渲染，风格规范如下（这些不是随意选的，是黑白手绘引文插画这个品类的视觉语言，偏离了就不像这个调性了）：

   - **纯黑白**：墨色用 \`#1a1a1a\`，纸色背景用 \`#fdfdfb\`，不用灰阶渐变、不用第二种颜色
   - **手写体字体栈**：\`Segoe Print, Bradley Hand, Comic Sans MS, cursive\`
   - **手绘感做法**（这几个技巧组合使用，纯规整的图形会显得像UI图标而不是插画）：
     - 圆环/线条用 \`stroke-dasharray\` 打断成虚线/点状，避免死板的实线
     - 墨迹、涂鸦类元素用不规则贝塞尔曲线 \`<path>\`（手动写几个不对称的控制点，不要用正圆/正方形）
     - 文字整体加 1-2 度的轻微 \`transform="rotate(...)"\`，模拟手写时的自然倾斜，不要每个字母单独转（那样会显得抖动过度、廉价）
   - **极简**：一张作品只保留 1-2 个视觉元素 + 一句话文字。留白比画面内容更重要——如果犹豫要不要加一个元素，答案通常是不加
   - **画布**：\`viewBox="0 0 680 680"\` 方形画布，一次 widget 调用只放一个 \`<svg>\`

   具体的 SVG 写法参考 \`assets/examples/\` 目录下的三个示例文件（对应字面锚点、双关谐音、对比并置三种模式各一个真实生成过的例子），生成新作品前可以打开看一眼手法。

## 给建议时的原则

- 如果用户给的话比较长（三句以上），主动建议只截取最有画面感的一句作为主视觉，其余弱化处理，不要试图把整段话都塞进一张图
- 不要一次性堆太多方案选项让用户挑花眼——默认给 1 个最贴合的方案；用户明确要"多方案对比"时再给 2-3 个
- 生成完预览后，提醒用户这是构图demo，真正手绘时线条要故意画得更"手抖"、更随性，比 SVG 版本里更不完美——机器生成的规整感和真正手绘的自然感之间总有差距，要提前说明避免用户误以为这就是最终成品该有的精确度
- 如果用户是在攒一个系列（"每日一图一句话"这类），提醒他们保持跨作品的一致性：同一套墨色、同一套字体栈、类似的留白比例，这样系列放在一起才会有统一的辨识度，而不是每天风格漂移
`;

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

const client = new Anthropic(); // ANTHROPIC_API_KEY from the environment

// Naive per-instance rate limit. Serverless instances don't share memory, so
// this is a speed bump, not a wall — for real limiting put Upstash/KV here.
const hits = new Map();
const WINDOW_MS = 10 * 60 * 1000;
const MAX_HITS = 8;

export default async function handler(req, res) {
  if (req.method !== "POST") {
    res.status(405).json({ error: "POST only" });
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

  try {
    // Streaming keeps the connection alive for however long the drawing takes;
    // finalMessage() hands back the complete response.
    const stream = client.messages.stream({
      model: "claude-opus-5",
      max_tokens: 8000,
      // Latency-sensitive interactive page; low effort is ample for one
      // 680x680 line drawing. Raise to "medium" if quality feels thin.
      output_config: { effort: "low" },
      system: [
        {
          type: "text",
          text: SKILL + RULES,
          cache_control: { type: "ephemeral" }, // stable prefix — skill + rules
        },
      ],
      messages: [
        {
          role: "user",
          content:
            "TASK — apply the method above to this exact sentence, once, " +
            "silently, then output the SVG:\n\n    「" + sentence + "」",
        },
      ],
    });
    const message = await stream.finalMessage();

    if (message.stop_reason === "refusal") {
      res.status(502).json({ error: "the model declined this sentence" });
      return;
    }

    const text = message.content
      .filter((b) => b.type === "text")
      .map((b) => b.text)
      .join("");
    const match = text.match(/<svg[\s\S]*?<\/svg>/i);
    if (!match) {
      res.status(502).json({ error: "no svg in model output" });
      return;
    }

    // Belt and braces before it reaches any browser.
    const svg = match[0]
      .replace(/<script[\s\S]*?<\/script>/gi, "")
      .replace(/\son\w+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)/gi, "")
      .replace(/javascript:/gi, "")
      .replace(/<image[\s\S]*?>/gi, "");

    res.status(200).json({ svg, via: "claude" });
  } catch (err) {
    res.status(502).json({ error: String(err?.message || err).slice(0, 200) });
  }
}
