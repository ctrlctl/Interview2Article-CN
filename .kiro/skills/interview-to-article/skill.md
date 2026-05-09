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

**Whisper fallback:**
- URL: `python $SCRIPTS/extract_srt.py <URL>`
- Local file: `python $SCRIPTS/extract_srt.py <file_path>`

**Model selection (assumes no dedicated GPU, CPU-only):**
- English source: use `small` (default) — adequate accuracy, ~5-10 min for a 13-min video
- Chinese source: use `medium` — significantly better for Chinese proper nouns, ~15-25 min on CPU

```bash
# Download auto-subtitles (preferred, instant)
yt-dlp --write-auto-sub --sub-lang en-orig --sub-format srt --skip-download -o "<output_folder>/drafts/%(id)s" <URL>

# Whisper fallback — English (default model)
python $SCRIPTS/extract_srt.py <URL>

# Whisper fallback — Chinese (medium model)
python $SCRIPTS/extract_srt.py <URL> auto medium
```

- Identify the dominant language (English / Chinese / mixed)
- Output: `<output_folder>/drafts/raw_transcript.md`

### Step 2: Topic Extraction

Quick pass over the raw transcript to identify main topic and sub-topics. This provides context for the correction step that follows.
Output: `<output_folder>/drafts/topics.md`

### Step 3: Correct Transcript

Using topic context + domain reference file, correct the raw transcript:

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
