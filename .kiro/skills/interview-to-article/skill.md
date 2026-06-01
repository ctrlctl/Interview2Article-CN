# Interview to Article Skill

## Description

Convert video/audio interviews into polished WeChat Official Account articles and Xiaohongshu image carousels. Handles transcription, brand/product recognition, bilingual formatting, image insertion, and multi-platform output.

## Domain References

Load `references/domain-*.md` at project start for domain-specific brand names, terminology, and image search tips.

**Available:** `references/domain-synth.md` — Synthesizers & electronic music gear

If no matching domain file exists, research the domain (search for key brands, terminology, common products mentioned in the transcript) and generate a basic `domain-*.md` file before proceeding to Step 3. This ensures brand/product correction has a reference to work from.

## Project Structure

```
.kiro/skills/interview-to-article/
├── skill.md
├── scripts/
│   ├── extract_srt.py        # Transcribe via yt-dlp + Whisper
│   ├── fetch_product_image.py # DuckDuckGo image search
│   ├── launch_editor.py      # Dual-pane WeChat editor
│   ├── md_to_wechat.py       # Markdown -> WeChat HTML
│   ├── render_xhs.py         # Markdown -> XHS image carousel
│   └── transcribe_audio.py   # Whisper-only transcription
└── references/

<YYMMDD>_<Author>_<Title>/       # Output per project, e.g. 260508_sonicstate_MakeNoise_Plexiphon
├── final_article.md           # Final Markdown (source of truth)
├── wechat/                    # WeChat HTML (ready to paste)
├── xhs/                       # XHS images (ready to post)
├── images/                    # Product images
└── drafts/                    # Intermediate files
```

**Script invocation:**
```bash
SCRIPTS=.kiro/skills/interview-to-article/scripts
python $SCRIPTS/<script>.py <args>
```

---

## Workflow

### Step 1: Transcribe & Detect Language

**Input types:**
- Video URL (YouTube, Bilibili, etc.)
- Local video/audio file (unreleased content)
- Existing transcript file (SRT, VTT, TXT)

**For URLs — try auto-subtitles first:**
1. Run `yt-dlp --list-subs <URL>` to check available subtitles
2. If auto-generated subtitles exist (e.g. `en-orig`, `zh-Hans`), download them: `yt-dlp --write-auto-sub --sub-lang <lang> --sub-format srt --skip-download <URL>`
3. Review subtitle quality — if coherent and complete, use directly (skip Whisper)
4. If no subtitles available, or quality is poor (garbled, incomplete), fall back to Whisper transcription

**Whisper fallback — use `transcribe` MCP tool (whisper-mcp-server):**
```
transcribe(source="<URL or file path>", language="auto", model_name="medium", output_format="timestamped")
```
- Language defaults to `auto` — the server samples 30s from the middle of the audio to detect the dominant language
- For Chinese source, use `model_name="medium"` (better for proper nouns)
- For English source, `model_name="small"` is adequate

```bash
# Download auto-subtitles (preferred, instant)
yt-dlp --write-auto-sub --sub-lang en-orig --sub-format srt --skip-download -o "<output_folder>/drafts/%(id)s" <URL>
```

- Identify the dominant language (English / Chinese / mixed)
- Output: `<output_folder>/drafts/raw_transcript.md`

### Step 2: Topic Extraction

Quick pass over the raw transcript to identify main topic and sub-topics. This provides context for the correction step that follows.
Output: `<output_folder>/drafts/topics.md`

### Step 3: Correct Transcript

⚠️ **禁止将整篇转录稿一次性读入上下文。必须分块逐段处理。**

#### 分块规则

1. 用 `wc -l <output_folder>/drafts/raw_transcript.md` 查看总行数
2. 按每块 80-120 行切分（在 Q&A 边界切割，不要在一个回答中间断开）
3. 逐块处理：每次只读取一个 chunk，完成纠错后写入临时文件 `/tmp/corrected_01.md`、`/tmp/corrected_02.md`...
4. ⚠️ **写入文件后，不要将已处理内容保留在对话上下文中。下一块处理时只需读取新的原文chunk。**
5. 所有块处理完成后，合并覆盖 `drafts/raw_transcript.md`

#### 每块处理内容

Using topic context + domain reference file, correct the chunk:

- Fix misrecognized brand/product names (e.g. "Hong Chi" → "MengQi", "Caso" → "Kastle")
- Fix person names, technical terms, proper nouns
- Fix obvious speech recognition errors where context makes the correct word clear
- Mark uncertain segments with `<!--REVIEW: ...-->`
- Output the **corrected transcript** back into `drafts/raw_transcript.md` (overwrite), plus `drafts/brands_products.md` and `drafts/review_needed.md`

**Golden Rule:** When in doubt, leave it unchanged.

### Step 4: Highlights Extraction

From the **corrected** transcript, extract 5-10 key takeaways:
- Notable opinions or insights from the interviewee
- Key product mentions with one-sentence context
- Memorable quotes

These become the "Highlights" section of the article — scannable, high-value content for readers who won't read the full interview.

### Step 5: Article Drafting

⚠️ **禁止将整篇纠错后转录稿一次性读入上下文。必须分块逐段起草。**

1. 先读取 `drafts/topics.md` 和 `drafts/brands_products.md`（短文件，常驻上下文作为参考）
2. 按 Q&A 对为单位切分，每块 3-5 个 Q&A 对
3. 逐块起草：每次只读取一个 chunk，写入 `/tmp/draft_01.md`、`/tmp/draft_02.md`...
4. ⚠️ **写入文件后，不要将已起草内容保留在对话上下文中。**
5. 所有块完成后，合并并补充头部结构（标题、intro、highlights、guest intro），保存为 `drafts/article_draft.md`

Output: `<output_folder>/drafts/article_draft.md`

#### Language Handling

- **English source:** Bilingual output. `Q (EN):` / `Q (CN):` / `A (EN):` / `A (CN):` labels.
- **Chinese source (with English terms inline):** Chinese only. No translation. Use `Q:` / `A:` or bold speaker names.
- **Mixed:** Bilingual output.

#### Article Structure

```
# Title
### Subtitle

> Source / 来源: [channel name] — [original video title]
> Link / 链接: [URL as plain text]
> Author / 作者: [interviewer/channel]
> 
> 免责声明：本文基于原视频内容整理，仅供学习参考。强烈推荐观看原视频获取完整体验。如有侵权请联系删除。

## Intro (2-4 sentences, bilingual if applicable)
---
## Highlights (5-10 bold-label + one-sentence takeaways)
---
## Guest Introduction (name, #role hashtags, bio)
---
## Full Interview
### [Topic cluster]
[Q&A pairs or paragraph pairs]
### [Topic cluster]
...
---
Credits (interviewer, editor, source URL again)
```

#### Topic Clustering

Group adjacent segments by theme (2-5 exchanges per group). Give each a concise heading. Keep original order.

#### Formatting Rules

- `#` title, `##` sections, `###` topic clusters
- **Bold** brand/product names on first mention
- Preserve speaker's words verbatim
- Images only in full interview body, not in highlights/intro
- No clickable external links in the final article — WeChat strips them. Use plain text for URLs (e.g. credits section can mention the source URL as text, not as a markdown link)

### Step 6: Product Image Insertion

**Which products to fetch images for:**
Review `drafts/brands_products.md` and select ALL products that are relevant to the interview topic — not just the main product being announced. If the interviewee mentions related products (previous collaborations, comparisons, recommended pairings), fetch images for those too. The goal is product promotion: every product worth showcasing should have a visual.

Example: In a Make Noise Plexiphon interview where Morphagene, Spectraphon, and Mimeophon are mentioned as prior collaborations, fetch images for all four — not just Plexiphon.

```bash
python $SCRIPTS/fetch_product_image.py "<Brand> <Product> <modifier>" <output_folder>/images
```

- Exit 0: paste markdown snippet into article at first mention
- Exit 2: retry with reformulated query once, then use placeholder
- Exit 3: ask user (network failure)

**Image placement:** Insert at first mention in the full interview body. If a product is only mentioned in passing (one word, no discussion), skip the image.

### Step 7: Review & Final Output

Review formatting, translation accuracy, image placement. Output: `<output_folder>/final_article.md`

### Step 8: Multi-Platform Output

#### WeChat HTML

```bash
# Direct copy to clipboard (Windows)
python $SCRIPTS/md_to_wechat.py <output_folder>/final_article.md --inline-images --copy

# Generate HTML file
python $SCRIPTS/md_to_wechat.py <output_folder>/final_article.md -o <output_folder>/wechat/article.html --inline-images

# Launch editor for review
python $SCRIPTS/launch_editor.py <output_folder>/final_article.md
```

Flags: `--theme default|warm`, `--inline-images`, `--copy`

#### Xiaohongshu Images

```bash
python $SCRIPTS/render_xhs.py <output_folder>/final_article.md <output_folder>/xhs/
```

Produces 1080x1440px PNGs. Max 20 per XHS post.

---

## Key Principles

1. **Preserve the original** — keep the speaker's voice
2. **Conservative edits** — only correct what you're confident about
3. **Brand accuracy** — cross-reference domain file, flag uncertainties
4. **Rich media** — product images at first mention in interview body
5. **Bilingual when needed** — only for English/mixed source; Chinese stays Chinese
6. **分块处理，不累积上下文** — 长转录稿必须分块处理，每块独立读取→处理→写文件，已处理内容不保留在对话上下文中
