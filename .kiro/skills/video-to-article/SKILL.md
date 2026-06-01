# Video/Audio to WeChat Article Skill

## Description
Use this skill whenever the user wants to convert a video or audio file into a polished WeChat Official Account (公众号) article. Triggers: '转成公众号文章', '视频转文章', '音频转文章', 'video to article', 'transcribe and format', '字幕转文章', '采访稿整理', or any request involving transcribing media and producing a formatted bilingual article with brand/product recognition.

## Workflow

You are an expert media-to-article agent. Follow these steps precisely. At each step, output intermediate results so the user can review.

---

### Step 1: Transcribe (语音转文字)

1. Check if the user has provided a video/audio file path, URL, or transcript file.
2. **If a URL or local file is provided:**
   - Use the `transcribe` MCP tool (whisper-mcp-server):
     ```
     transcribe(source="<URL or file path>", language="auto", model_name="medium", output_format="timestamped")
     ```
   - Language defaults to `auto` — the server samples 30s from the middle of the audio to detect the dominant language (important for videos where intro language differs from main content, e.g. a Chinese host opening an English interview).
   - Override only if detection fails: `transcribe(source="...", language="zh")`
   - If the URL is not supported by yt-dlp (e.g., WeChat 视频号), inform the user and ask them to provide the video file or transcript manually.
3. **If a transcript/subtitle file (SRT, VTT, TXT) is provided:**
   - Use it directly.
4. Parse the transcription output and save as `raw_transcript.md` in the workspace.

**Important:** Preserve the original spoken content as faithfully as possible. This is an interview transcript — do NOT over-edit.

---

### Step 2: Topic Extraction (提取主题)

1. Read through the full transcript.
2. Identify the main topic, sub-topics, and key discussion points.
3. Output a `topics.md` file containing:
   - Main topic (一句话概括)
   - Sub-topics list
   - Key quotes worth highlighting
4. This topic context will guide the polishing in Step 3.

---

### Step 3: Polish & Error Correction (润色与纠错)

⚠️ **禁止将整篇转录稿一次性读入上下文。必须分块逐段处理。**

#### 分块规则

1. 用 `wc -l raw_transcript.md` 查看总行数
2. 按每块 80-120 行切分（在 Q&A 边界切割，不要在一个回答中间断开）
3. 逐块处理：每次只读取一个 chunk，完成纠错后写入临时文件 `/tmp/polished_01.md`、`/tmp/polished_02.md`...
4. ⚠️ **写入文件后，不要将已处理内容保留在对话上下文中。下一块处理时只需读取新的原文chunk。**

#### 每块处理内容

1. **Brand & Product Names (品牌与产品识别):**
   - Identify all brand names and product names mentioned.
   - Correct any misrecognized brand/product names (e.g., "苹果手机" misheard as "平果手机").
   - Append to `brands_products.md` with format:
     ```
     | Brand/品牌 | Products/产品 | First Mention Location |
     ```

2. **Context-based Correction (基于主题的纠错):**
   - Use the topic context from Step 2 to fix obvious transcription errors.
   - Only fix errors you are confident about based on context.
   - Do NOT rephrase or rewrite the speaker's words — preserve the interview style.

3. **Uncertain Segments (需人工确认的片段):**
   - Mark any segments where you cannot confidently determine the correct text.
   - Use this format: `<!--REVIEW: 原文"xxx"，可能是"yyy"，请确认-->`
   - Append to `review_needed.md`.

#### 合并

所有块处理完成后，读取所有 `/tmp/polished_*.md` 文件，合并为完整的纠错后转录稿，保存为 `polished_transcript.md`。

**Golden Rule:** 宁可少改，不可多改。保留采访稿原貌。

---

### Step 4: Article Drafting (文章起草)

⚠️ **禁止将整篇纠错后转录稿一次性读入上下文。必须分块逐段起草。**

#### 分块起草流程

1. 先读取 `topics.md` 和 `brands_products.md`（这两个文件短，可以常驻上下文作为参考）
2. 按 Q&A 对为单位切分 `polished_transcript.md`，每块 3-5 个 Q&A 对
3. 逐块起草：每次只读取一个 chunk，按下方格式规则起草该块内容，写入临时文件 `/tmp/draft_01.md`、`/tmp/draft_02.md`...
4. ⚠️ **写入文件后，不要将已起草内容保留在对话上下文中。**
5. 所有块起草完成后，合并为完整文章，补充头部结构（标题、摘要、金句、受访者介绍），保存为 `article_draft.md`

Produce `article_draft.md`. The structure is fixed; the language handling adapts to the source audio.

#### 4a. Language Handling

Determine the dominant language from Step 1's transcription result:

- **Source is English (e.g. an international guest with a Chinese host)**: every interview paragraph is bilingual — Chinese translation as the primary prose, English original as a quoted block beneath. Body copy is Chinese; the quote block preserves the speaker's exact words.
- **Source is Chinese**: keep the article fully Chinese. Do NOT fabricate an English translation. Summary, headings, section names all Chinese.
- **Mixed (host opens in Chinese, main interview in another language)**: treat the dominant language of the main body as the source, and follow the rule above. Intro/closing remarks by the host get integrated in Chinese regardless.

#### 4b. Article Structure (five sections, in order)

```markdown
# [大标题]

> [一段摘要，2-4 句话，点出受访对象、场合和亮点]

---

## 精选金句

> "句子 1"
> —— 讲话人

> "句子 2"
> —— 讲话人

(3-5 条即可。优先选受访者的观点型表述，而不是事实描述。)

---

## 受访者介绍

- **[受访者 A]**（身份/头衔）
- **[受访者 B]**（身份/头衔）

[可加一两句背景：品牌/机构、代表作、与本次采访的关联]

---

## 采访全文

### [小主题一]

**Q：[问题]**

[回答段落]

> *[英文原话，仅在原文为英文时出现]*

**Q：[问题]**

[回答段落]

### [小主题二]

...

---

## [收尾 / 品牌产品表 / 可选]
```

#### 4c. Topic Clustering (问题聚类)

The interview transcript usually comes out as Q1, Q2, ... Q12 in sequence. Do NOT render them as a flat list. Group them:

1. Read through `topics.md` and the full transcript.
2. Group adjacent questions that share a theme (usually 1-4 Qs per group).
3. Give each group a short H3 heading (`###`) that names the theme, e.g. `### 对中国模块社区的印象`, `### 品牌哲学：好玩、紧凑、启发`, `### Kastle 系列的十年`.
4. Under each H3, keep the Q&A pairs in their original order.
5. If a question truly stands alone and doesn't cluster with neighbors, give it its own H3 anyway.

**Rule of thumb:** An interview with 10-15 questions becomes 4-7 thematic sections.

#### 4d. Formatting rules

- Use `#` for main title, `##` for the five top-level sections, `###` for sub-topic clusters inside 采访全文
- **Bold** all brand and product names on first mention
- Keep the interview tone — do not over-polish
- Preserve as much original text as possible; correction-only edits (per Step 3) are the exception
- The 精选金句 block should quote the person verbatim — no paraphrasing
- Preserve as much original text as possible

---

### Step 5: Product Image Insertion (产品图片插入)

Use the bundled `fetch_product_image.py` helper (DuckDuckGo image search, no API key required) to download product images and insert them into the article.

**Setup (one-time, if not already installed):**
```bash
pip install --user ddgs requests
```

**Per-product workflow:**

1. For each product identified in `brands_products.md`, run:
   ```bash
   python fetch_product_image.py "<Brand> <Product> <modifier>"
   ```
   For example:
   ```bash
   python fetch_product_image.py "Bastl Instruments Neo Trinity module"
   python fetch_product_image.py "Elektron Digitone first generation"
   ```
2. The script prints a ready-to-paste markdown snippet on success:
   ```markdown
   ![Query](images/slug.jpg)
   *▲ Query*
   <!-- source: https://... -->
   ```
3. Insert the snippet near the paragraph where the product is FIRST mentioned.
4. If multiple products are mentioned in one paragraph, place images in order of mention.
5. If a product is mentioned multiple times, only insert the image at the FIRST mention.

**Exit codes — what the agent should do:**

| Exit | Meaning | Agent action |
|------|---------|--------------|
| `0` | Image downloaded, markdown snippet on stdout | Paste snippet into article |
| `2` | Search ran but no usable image (zero results or all downloads failed). Stdout contains `<!-- IMAGE_NEEDED: ... -->` | First try a reformulated query once (e.g. more specific brand + version, drop extra words, try the official site name). If still exit 2, paste the placeholder and move on. |
| `3` | Transport failure (DDG / Bing unreachable) after 3 internal retries. Clear error on stderr | **Do not loop.** The script already retried 3 times with backoff. Either (a) pause and retry this single query once after ~30 seconds, or (b) stop and tell the user the image search backend is down and ask whether to continue with placeholders or try again later. |

**Query tips for better first-hit accuracy:**
- Include both brand and product name: `"Bastl Neo Trinity"` beats `"Neo Trinity"`
- Add a disambiguator for common words: `module`, `synthesizer`, `pedal`, `first generation`, etc.
- For products with multiple versions, specify: `"Elektron Digitone first generation"` not just `"Digitone"`

**Review before publishing:**
- Quickly eyeball each downloaded image — DDG usually returns the official product shot first, but occasionally returns a tutorial thumbnail or wrong version.
- If a result is wrong, delete the file and re-run with a better query (e.g., add `site:brand.com` or a year).
- All images land in `./images/` so they're easy to re-upload to WeChat during final formatting.

---

### Step 6: Review & Final Output (审校与最终输出)

1. Re-read the entire article for:
   - Formatting consistency (headings, spacing, bold brands)
   - Translation accuracy (bilingual alignment)
   - Image placement correctness
   - Any remaining `<!--REVIEW-->` tags — list them for the user
2. Output the final article as `final_article.md`.
3. Provide a summary to the user:
   - Total brands/products identified
   - Number of segments needing human review
   - Article word count (Chinese / English)

---

### Step 7: WeChat Formatting (公众号排版)

After the article draft is ready, the default is to **launch the dual-pane editor** so the user can review and fine-tune before copying. The editor auto-saves edits back to the markdown file.

**Setup (one-time):**
```bash
pip install --user markdown premailer pygments pywin32
```
(`pywin32` is only needed for the `--copy` flag on Windows.)

**Default path — launch the editor:**
```bash
python launch_editor.py final_article.md
```

This opens a browser window with:
- **Left pane**: editable Markdown (your draft). Changes auto-save to the file after ~1 second of idle.
- **Right pane**: live-rendered WeChat preview, debounced at 300 ms.
- **Top-right button "复制到公众号"**: writes the rendered rich-text HTML to the clipboard (same CF_HTML mechanism as `md_to_wechat.py --copy`). Switch to the WeChat editor and `Ctrl+V`.

The user can:
- Manually edit the markdown right there
- Come back to chat and ask the agent to make changes (the file on disk is the source of truth; next preview refresh picks it up)
- Copy and paste when satisfied

**Scripted path — no editor, just emit HTML / copy:**

Use `md_to_wechat.py` directly when you don't need a review step (e.g. batch processing, or when the user explicitly asks to skip the editor):

```bash
python md_to_wechat.py final_article.md --inline-images --copy
# Windows: clipboard ready, go straight to WeChat editor + Ctrl+V.

python md_to_wechat.py final_article.md --inline-images
# Cross-platform: open the HTML, click the green "一键复制" button.
```

**Flags for both tools:**
- `--theme default` (cool blue) or `--theme warm` (warm orange)

`md_to_wechat.py`-only flags:
- `--inline-images` — embed local images as base64 data URIs. WeChat auto-uploads them to its own CDN on paste, producing permanent `mmbiz.qpic.cn` URLs.
- `--copy` — push rendered HTML straight to the Windows clipboard (requires `pywin32`).

**Paste verification (first time only):**
1. In the WeChat editor, click any image — its URL should become `https://mmbiz.qpic.cn/...`. If it's still `data:image/...`, WeChat didn't auto-ingest the base64 — fall back to manually uploading via the editor's image button.
2. Confirm headings, quotes, and tables render identically to the preview.

**Why this works:**
- Every CSS rule is flattened into `style=""` attributes via `premailer` — survives WeChat's sanitizer, which strips `<style>` tags
- Max width 677px (WeChat's rendered column)
- Figure captions (`*▲ product*` lines) auto-styled as centered muted text
- Serif Chinese fonts (Source Han Serif SC / Songti / SimSun) with English fallbacks — renders correctly on both iOS and Android WeChat
- No external resources, no third-party image hosts — fully self-contained

**Why not a third-party image host?**

Services like sm.ms, imgbb, catbox all have dealbreakers:
- **sm.ms** no longer allows anonymous uploads
- **catbox.moe** is frequently unreachable on mainland China networks
- **imgbb** requires an API key
- Any free host can disappear — every historical WeChat article referencing it then shows broken images *forever*, since published WeChat articles can't have their images edited.

Inlining base64 sidesteps this: the image never leaves the user's machine until WeChat itself ingests it.

---

## Output Files Summary

| File | Description |
|------|-------------|
| `raw_transcript.md` | Raw transcription with timestamps |
| `topics.md` | Extracted topics and key points |
| `brands_products.md` | Brand and product name registry |
| `review_needed.md` | Segments needing human confirmation |
| `polished_transcript.md` | Error-corrected transcript (merged from chunks) |
| `article_draft.md` | Bilingual article draft |
| `final_article.md` | Final polished article ready for formatting |

## Key Principles

1. **保留原文** — This is an interview transcript. Preserve the speaker's voice.
2. **宁缺毋滥** — Only correct what you're confident about. Mark the rest for review.
3. **品牌准确** — Brand and product names must be accurate. When in doubt, flag it.
4. **图文并茂** — Images enhance the article but must be correctly placed.
5. **双语对照** — Bilingual format serves a wider audience.
6. **分块处理，不累积上下文** — 长转录稿必须分块处理，每块独立读取→处理→写文件，已处理内容不保留在对话上下文中。上下文中只传递文件路径，不传递大段原文或译文。
