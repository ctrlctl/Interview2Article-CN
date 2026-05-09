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

<YYMMDD>_<ShortName>/         # Output per project
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

- URL: `python $SCRIPTS/extract_srt.py <URL>` (yt-dlp + Whisper, auto language detection)
- Local file: `python $SCRIPTS/extract_srt.py <file_path>`
- Existing transcript: use directly
- Identify the dominant language (English / Chinese / mixed) — this determines bilingual vs Chinese-only output in later steps
- Output: `<output_folder>/drafts/raw_transcript.md`

**Model selection (assumes no dedicated GPU, CPU-only):**
- English source: use `small` (default) — adequate accuracy, ~5-10 min for a 13-min video
- Chinese source: use `medium` — significantly better for Chinese proper nouns, ~15-25 min on CPU

```bash
# English (default)
python $SCRIPTS/extract_srt.py <URL>

# Chinese — specify medium model
python $SCRIPTS/extract_srt.py <URL> auto medium
```

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
Credits
```

#### Topic Clustering

Group adjacent segments by theme (2-5 exchanges per group). Give each a concise heading. Keep original order.

#### Formatting Rules

- `#` title, `##` sections, `###` topic clusters
- **Bold** brand/product names on first mention
- Preserve speaker's words verbatim
- Images only in full interview body, not in highlights/intro

### Step 6: Product Image Insertion

```bash
python $SCRIPTS/fetch_product_image.py "<Brand> <Product> <modifier>" <output_folder>/images
```

- Exit 0: paste markdown snippet into article at first mention
- Exit 2: retry with reformulated query once, then use placeholder
- Exit 3: ask user (network failure)

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
