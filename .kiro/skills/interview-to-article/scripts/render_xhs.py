#!/usr/bin/env python3
"""Render Markdown article into a sequence of Xiaohongshu-ready images (1080x1440px, 3:4).

Usage:
    python render_xhs.py <input.md> <output_dir/>

Dependencies: pillow
"""

import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ─── Config ──────────────────────────────────────────────────────────────────

WIDTH = 1080
HEIGHT = 1440
PADDING_X = 90
PADDING_Y = 110
CONTENT_WIDTH = WIDTH - 2 * PADDING_X
BG_COLOR = "#fffdf9"
TEXT_COLOR = "#2c2c2c"
HEADING_COLOR = "#1a1a1a"
ACCENT_COLOR = "#4a6741"
MUTED_COLOR = "#888888"
BOLD_COLOR = "#2b5797"
SEPARATOR_COLOR = "#e0dcd6"
TABLE_BORDER_COLOR = "#d0ccc6"
TABLE_HEADER_BG = "#f3f0eb"

FONT_SIZE_BODY = 32
FONT_SIZE_H1 = 44
FONT_SIZE_H2 = 38
FONT_SIZE_H3 = 34
FONT_SIZE_QUOTE = 28
FONT_SIZE_TABLE = 26
LINE_SPACING = 2.1

FONT_CANDIDATES = [
    "/mnt/c/Windows/Fonts/NotoSerifSC-VF.ttf",
    "C:/Windows/Fonts/NotoSerifSC-VF.ttf",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSerifCJK-Regular.ttc",
    "C:/Windows/Fonts/simsun.ttc",
]

FONT_CANDIDATES_BOLD = [
    "/mnt/c/Windows/Fonts/NotoSerifSC-VF.ttf",
    "C:/Windows/Fonts/NotoSerifSC-VF.ttf",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSerifCJK-Bold.ttc",
    "C:/Windows/Fonts/simhei.ttf",
]


def load_font(candidates, size, bold=False):
    for path in candidates:
        try:
            f = ImageFont.truetype(path, size)
            try:
                axes = f.get_variation_axes()
                if axes:
                    f.set_variation_by_axes([700 if bold else 400])
            except (AttributeError, OSError):
                pass
            return f
        except (OSError, IOError):
            continue
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except (OSError, IOError):
        return ImageFont.load_default()


def get_fonts():
    return {
        "body": load_font(FONT_CANDIDATES, FONT_SIZE_BODY),
        "bold": load_font(FONT_CANDIDATES_BOLD, FONT_SIZE_BODY, bold=True),
        "h1": load_font(FONT_CANDIDATES_BOLD, FONT_SIZE_H1, bold=True),
        "h2": load_font(FONT_CANDIDATES_BOLD, FONT_SIZE_H2, bold=True),
        "h3": load_font(FONT_CANDIDATES_BOLD, FONT_SIZE_H3, bold=True),
        "quote": load_font(FONT_CANDIDATES, FONT_SIZE_QUOTE),
        "table": load_font(FONT_CANDIDATES, FONT_SIZE_TABLE),
        "table_bold": load_font(FONT_CANDIDATES_BOLD, FONT_SIZE_TABLE, bold=True),
    }


# ─── Markdown Parsing ────────────────────────────────────────────────────────

def strip_md_preprocessing(md_text):
    """Remove style blocks and HTML comments, but preserve image and link syntax."""
    md_text = re.sub(r'<style>.*?</style>', '', md_text, flags=re.DOTALL)
    md_text = re.sub(r'<!--.*?-->', '', md_text, flags=re.DOTALL)
    md_text = re.sub(r'<[^>]+>', '', md_text)
    # Convert links to plain text, but NOT images (![...](...)  starts with !)
    md_text = re.sub(r'(?<!!)\[([^\]]+)\]\([^)]+\)', r'\1', md_text)
    # Unescape markdown escapes (e.g. \# -> #)
    md_text = re.sub(r'\\([#*_`])', r'\1', md_text)
    return md_text


def parse_md_to_blocks(md_text):
    """Parse Markdown into a list of render blocks."""
    md_text = strip_md_preprocessing(md_text)

    blocks = []
    lines = md_text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        # Empty line
        if not line:
            blocks.append({"type": "spacer", "height": int(FONT_SIZE_BODY * 0.5)})
            i += 1
            continue

        # Headings
        if line.startswith('# ') and not line.startswith('## '):
            blocks.append({"type": "h1", "text": line[2:].strip()})
            i += 1
            continue
        if line.startswith('## '):
            blocks.append({"type": "h2", "text": line[3:].strip()})
            i += 1
            continue
        if line.startswith('### '):
            blocks.append({"type": "h3", "text": line[4:].strip()})
            i += 1
            continue
        if line.startswith('#### '):
            blocks.append({"type": "h3", "text": line[5:].strip()})
            i += 1
            continue

        # Separator
        if re.match(r'^-{3,}$', line) or re.match(r'^\*{3,}$', line):
            blocks.append({"type": "separator"})
            i += 1
            continue

        # Image (must check before paragraph)
        img_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)', line)
        if img_match:
            blocks.append({"type": "image", "alt": img_match.group(1), "path": img_match.group(2)})
            i += 1
            continue

        # Caption line (*▲ ...*)
        if re.match(r'^\*▲', line):
            caption = re.sub(r'^\*', '', line).rstrip('*').strip()
            blocks.append({"type": "caption", "text": caption})
            i += 1
            continue

        # Table (lines starting with |)
        if line.startswith('|'):
            table_rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                row_line = lines[i].strip()
                # Skip separator rows (|---|---|)
                if re.match(r'^\|[\s\-:|]+\|$', row_line):
                    i += 1
                    continue
                cells = [c.strip() for c in row_line.strip('|').split('|')]
                table_rows.append(cells)
                i += 1
            if table_rows:
                blocks.append({"type": "table", "rows": table_rows})
            continue

        # Blockquote
        if line.startswith('>'):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                quote_lines.append(re.sub(r'^>\s?', '', lines[i]).strip())
                i += 1
            text = ' '.join(l for l in quote_lines if l)
            if text:
                blocks.append({"type": "quote", "text": text})
            continue

        # List item
        if re.match(r'^[-*]\s+', line) and not re.match(r'^\*\*', line):
            while i < len(lines) and re.match(r'^[-*]\s+', lines[i].strip()) and not re.match(r'^\*\*', lines[i].strip()):
                item_text = re.sub(r'^[-*]\s+', '', lines[i].strip())
                blocks.append({"type": "list_item", "text": item_text})
                i += 1
            continue

        # Paragraph (collect consecutive non-empty lines)
        para_lines = []
        while i < len(lines) and lines[i].strip():
            cur = lines[i]
            if re.match(r'^#{1,3}\s+', cur):
                break
            if re.match(r'^-{3,}\s*$', cur.strip()):
                break
            if re.match(r'^\*{3,}\s*$', cur.strip()):
                break
            if cur.strip().startswith('>'):
                break
            if re.match(r'^!\[', cur.strip()):
                break
            if cur.strip().startswith('|') and '|' in cur.strip()[1:]:
                break
            if re.match(r'^[-*]\s+', cur.strip()) and not re.match(r'^\*\*', cur.strip()):
                break
            para_lines.append(cur.strip())
            i += 1
        text = ' '.join(para_lines)
        if text.strip():
            blocks.append({"type": "paragraph", "text": text})

    return blocks


# ─── Inline Formatting ───────────────────────────────────────────────────────

def parse_inline(text):
    """Parse inline formatting into segments: [(text, style), ...]
    Handles **bold**, `code`, and *italic* (rendered as normal).
    """
    segments = []
    # Split on bold and code patterns
    parts = re.split(r'(`[^`]+`|\*\*[^*]+\*\*)', text)
    for part in parts:
        if not part:
            continue
        if part.startswith('`') and part.endswith('`'):
            segments.append((part[1:-1], 'bold'))  # render code as bold for XHS
        elif part.startswith('**') and part.endswith('**'):
            segments.append((part[2:-2], 'bold'))
        else:
            # Strip remaining single * (italic markers)
            clean = re.sub(r'\*([^*]+)\*', r'\1', part)
            if clean:
                segments.append((clean, 'normal'))
    return segments if segments else [("", 'normal')]


# ─── Text Wrapping ───────────────────────────────────────────────────────────

def wrap_rich(segments, fonts, max_width, draw):
    """Word-wrap rich text segments by pixel width. Returns list of line-segment lists."""
    lines = []
    cur_line = []
    cur_w = 0

    for text, style in segments:
        font = fonts["bold"] if style == 'bold' else fonts["body"]
        for char in text:
            cw = draw.textbbox((0, 0), char, font=font)[2]
            if cur_w + cw > max_width and cur_line:
                lines.append(cur_line)
                cur_line = []
                cur_w = 0
            if cur_line and cur_line[-1][1] == style:
                cur_line[-1] = (cur_line[-1][0] + char, style)
            else:
                cur_line.append((char, style))
            cur_w += cw

    if cur_line:
        lines.append(cur_line)
    return lines


def wrap_plain(text, font, max_width, draw):
    """Word-wrap plain text by pixel width."""
    lines = []
    cur = ""
    for char in text:
        test = cur + char
        w = draw.textbbox((0, 0), test, font=font)[2]
        if w > max_width and cur:
            lines.append(cur)
            cur = char
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def draw_rich_line(segs, fonts, draw, x, y):
    """Draw one line of rich text."""
    cx = x
    for text, style in segs:
        font = fonts["bold"] if style == 'bold' else fonts["body"]
        color = BOLD_COLOR if style == 'bold' else TEXT_COLOR
        draw.text((cx, y), text, font=font, fill=color)
        cx += draw.textbbox((0, 0), text, font=font)[2]


# ─── Block Height Estimation ─────────────────────────────────────────────────

def _resolve_path(p, md_dir):
    if md_dir is None:
        return None
    path = Path(p)
    if not path.is_absolute():
        path = md_dir / path
    return path


def block_height(block, fonts, draw, md_dir=None):
    line_h = int(FONT_SIZE_BODY * LINE_SPACING)

    if block["type"] == "spacer":
        return block["height"]
    if block["type"] == "separator":
        return int(FONT_SIZE_BODY * 1.8)
    if block["type"] == "h1":
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', block["text"])
        n = len(wrap_plain(text, fonts["h1"], CONTENT_WIDTH, draw))
        return n * int(FONT_SIZE_H1 * LINE_SPACING) + 30
    if block["type"] == "h2":
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', block["text"])
        n = len(wrap_plain(text, fonts["h2"], CONTENT_WIDTH, draw))
        return n * int(FONT_SIZE_H2 * LINE_SPACING) + 24
    if block["type"] == "h3":
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', block["text"])
        n = len(wrap_plain(text, fonts["h3"], CONTENT_WIDTH, draw))
        return n * int(FONT_SIZE_H3 * LINE_SPACING) + 20
    if block["type"] == "paragraph":
        segs = parse_inline(block["text"])
        n = len(wrap_rich(segs, fonts, CONTENT_WIDTH, draw))
        return n * line_h
    if block["type"] == "list_item":
        segs = parse_inline(block["text"])
        n = len(wrap_rich(segs, fonts, CONTENT_WIDTH - 44, draw))
        return n * line_h
    if block["type"] == "quote":
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', block["text"])
        n = len(wrap_plain(text, fonts["quote"], CONTENT_WIDTH - 40, draw))
        return n * int(FONT_SIZE_QUOTE * LINE_SPACING) + 30
    if block["type"] == "caption":
        return int(FONT_SIZE_QUOTE * 1.8)
    if block["type"] == "image":
        img_path = _resolve_path(block["path"], md_dir)
        if img_path and img_path.exists():
            img = Image.open(img_path)
            max_img_h = (HEIGHT - 2 * PADDING_Y) // 2  # cap at half page
            scale = min(CONTENT_WIDTH / img.width, max_img_h / img.height)
            return int(img.height * scale) + 24
        return 0
    if block["type"] == "table":
        rows = block["rows"]
        if not rows:
            return 0
        row_h = int(FONT_SIZE_TABLE * 2.2)
        return len(rows) * row_h + 4  # +4 for borders
    return 0


# ─── Block Drawing ───────────────────────────────────────────────────────────

def draw_block(block, fonts, draw, x, y, canvas=None, md_dir=None):
    """Draw a block at (x, y), return height consumed."""
    line_h = int(FONT_SIZE_BODY * LINE_SPACING)

    if block["type"] == "spacer":
        return block["height"]

    if block["type"] == "separator":
        sy = y + int(FONT_SIZE_BODY * 0.9)
        draw.line([(x + 100, sy), (x + CONTENT_WIDTH - 100, sy)], fill=SEPARATOR_COLOR, width=2)
        return int(FONT_SIZE_BODY * 1.8)

    if block["type"] == "h1":
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', block["text"])
        lines = wrap_plain(text, fonts["h1"], CONTENT_WIDTH, draw)
        lh = int(FONT_SIZE_H1 * LINE_SPACING)
        for i, ln in enumerate(lines):
            draw.text((x, y + i * lh), ln, font=fonts["h1"], fill=HEADING_COLOR)
        total = len(lines) * lh
        draw.line([(x, y + total + 8), (x + 80, y + total + 8)], fill=ACCENT_COLOR, width=3)
        return total + 30

    if block["type"] == "h2":
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', block["text"])
        lines = wrap_plain(text, fonts["h2"], CONTENT_WIDTH, draw)
        lh = int(FONT_SIZE_H2 * LINE_SPACING)
        for i, ln in enumerate(lines):
            draw.text((x, y + i * lh), ln, font=fonts["h2"], fill=HEADING_COLOR)
        total = len(lines) * lh
        draw.line([(x, y + total + 6), (x + 60, y + total + 6)], fill=ACCENT_COLOR, width=2)
        return total + 24

    if block["type"] == "h3":
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', block["text"])
        lines = wrap_plain(text, fonts["h3"], CONTENT_WIDTH, draw)
        lh = int(FONT_SIZE_H3 * LINE_SPACING)
        bar_top = y + 4
        bar_bot = y + len(lines) * lh - 4
        draw.line([(x, bar_top), (x, bar_bot)], fill=ACCENT_COLOR, width=4)
        for i, ln in enumerate(lines):
            draw.text((x + 16, y + i * lh), ln, font=fonts["h3"], fill=HEADING_COLOR)
        return len(lines) * lh + 20

    if block["type"] == "paragraph":
        segs = parse_inline(block["text"])
        lines = wrap_rich(segs, fonts, CONTENT_WIDTH, draw)
        for i, line_segs in enumerate(lines):
            draw_rich_line(line_segs, fonts, draw, x, y + i * line_h)
        return len(lines) * line_h

    if block["type"] == "list_item":
        indent = 44
        bullet_y = y + int(FONT_SIZE_BODY * 0.5)
        draw.ellipse([(x + 10, bullet_y), (x + 22, bullet_y + 12)], fill=ACCENT_COLOR)
        segs = parse_inline(block["text"])
        lines = wrap_rich(segs, fonts, CONTENT_WIDTH - indent, draw)
        for i, line_segs in enumerate(lines):
            draw_rich_line(line_segs, fonts, draw, x + indent, y + i * line_h)
        return len(lines) * line_h

    if block["type"] == "quote":
        text = block["text"]
        # Strip bold markers for display
        text_clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        qlines = wrap_plain(text_clean, fonts["quote"], CONTENT_WIDTH - 40, draw)
        qlh = int(FONT_SIZE_QUOTE * LINE_SPACING)
        total_h = len(qlines) * qlh + 20
        draw.line([(x + 4, y + 6), (x + 4, y + total_h - 6)], fill=ACCENT_COLOR, width=3)
        for i, ln in enumerate(qlines):
            draw.text((x + 24, y + 10 + i * qlh), ln, font=fonts["quote"], fill=MUTED_COLOR)
        return total_h

    if block["type"] == "caption":
        text = block["text"]
        bbox = draw.textbbox((0, 0), text, font=fonts["quote"])
        tw = bbox[2] - bbox[0]
        cx = x + (CONTENT_WIDTH - tw) // 2
        draw.text((cx, y), text, font=fonts["quote"], fill=MUTED_COLOR)
        return int(FONT_SIZE_QUOTE * 1.8)

    if block["type"] == "image" and canvas is not None:
        img_path = _resolve_path(block["path"], md_dir)
        if img_path and img_path.exists():
            img = Image.open(img_path).convert("RGB")
            max_img_h = (HEIGHT - 2 * PADDING_Y) // 2
            scale = min(CONTENT_WIDTH / img.width, max_img_h / img.height)
            new_w = int(img.width * scale)
            new_h = int(img.height * scale)
            resized = img.resize((new_w, new_h), Image.LANCZOS)
            # Center horizontally if narrower than content width
            offset_x = x + (CONTENT_WIDTH - new_w) // 2
            canvas.paste(resized, (offset_x, y + 12))
            return new_h + 24
        return 0

    if block["type"] == "table":
        rows = block["rows"]
        if not rows:
            return 0
        num_cols = max(len(r) for r in rows)
        col_w = CONTENT_WIDTH // num_cols
        row_h = int(FONT_SIZE_TABLE * 2.2)
        total_h = len(rows) * row_h

        for ri, row in enumerate(rows):
            ry = y + ri * row_h
            is_header = (ri == 0)
            # Header background
            if is_header:
                draw.rectangle([(x, ry), (x + CONTENT_WIDTH, ry + row_h)], fill=TABLE_HEADER_BG)
            # Row border
            draw.line([(x, ry + row_h), (x + CONTENT_WIDTH, ry + row_h)], fill=TABLE_BORDER_COLOR, width=1)
            # Cells
            for ci, cell in enumerate(row):
                if ci >= num_cols:
                    break
                cx = x + ci * col_w + 12
                # Strip bold markers
                cell_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', cell)
                font = fonts["table_bold"] if is_header or '**' in cell else fonts["table"]
                # Truncate if too wide
                max_cell_w = col_w - 24
                display = cell_text
                while draw.textbbox((0, 0), display, font=font)[2] > max_cell_w and len(display) > 1:
                    display = display[:-1]
                if display != cell_text:
                    display += "..."
                text_y = ry + (row_h - FONT_SIZE_TABLE) // 2
                draw.text((cx, text_y), display, font=font, fill=TEXT_COLOR)
            # Column borders
            for ci in range(1, num_cols):
                bx = x + ci * col_w
                draw.line([(bx, ry), (bx, ry + row_h)], fill=TABLE_BORDER_COLOR, width=1)

        # Outer border
        draw.rectangle([(x, y), (x + CONTENT_WIDTH, y + total_h)], outline=TABLE_BORDER_COLOR, width=1)
        return total_h + 4

    return 0


# ─── Pagination ──────────────────────────────────────────────────────────────

def paginate(blocks, fonts, md_dir=None):
    tmp = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(tmp)
    max_h = HEIGHT - 2 * PADDING_Y

    pages = []
    cur_page = []
    cur_h = 0

    i = 0
    while i < len(blocks):
        b = blocks[i]
        h = block_height(b, fonts, draw, md_dir)

        # Keep headings with following content
        if b["type"] in ("h1", "h2", "h3") and i + 1 < len(blocks):
            next_i = i + 1
            while next_i < len(blocks) and blocks[next_i]["type"] == "spacer":
                next_i += 1
            if next_i < len(blocks):
                group_h = h
                for j in range(i + 1, next_i + 1):
                    group_h += block_height(blocks[j], fonts, draw, md_dir)
                if cur_h + group_h > max_h and group_h <= max_h and cur_page:
                    pages.append(cur_page)
                    cur_page = []
                    cur_h = 0

        if cur_h + h > max_h and cur_page:
            pages.append(cur_page)
            cur_page = []
            cur_h = 0

        cur_page.append(b)
        cur_h += h
        i += 1

    if cur_page:
        pages.append(cur_page)
    return pages


# ─── Page Rendering ──────────────────────────────────────────────────────────

def render_page(page_blocks, fonts, page_num, total_pages, md_dir=None):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    y = PADDING_Y
    for b in page_blocks:
        h = draw_block(b, fonts, draw, PADDING_X, y, canvas=img, md_dir=md_dir)
        y += h

    # Page number bottom-right
    ptext = f"{page_num}/{total_pages}"
    bbox = draw.textbbox((0, 0), ptext, font=fonts["body"])
    pw = bbox[2] - bbox[0]
    draw.text((WIDTH - PADDING_X - pw, HEIGHT - PADDING_Y + 30), ptext,
              font=fonts["body"], fill=MUTED_COLOR)

    return img


# ─── Main ────────────────────────────────────────────────────────────────────

def render_md_to_images(md_path, output_dir):
    md_path = Path(md_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    md_dir = md_path.parent
    md_text = md_path.read_text(encoding="utf-8")
    blocks = parse_md_to_blocks(md_text)

    # Remove spacers between image and caption so they stay tight
    cleaned = []
    for i, b in enumerate(blocks):
        if (b["type"] == "spacer" and i > 0 and i < len(blocks) - 1
                and blocks[i - 1]["type"] == "image"
                and blocks[i + 1]["type"] == "caption"):
            continue
        cleaned.append(b)
    blocks = cleaned

    fonts = get_fonts()
    pages = paginate(blocks, fonts, md_dir)

    for i, page_blocks in enumerate(pages, 1):
        img = render_page(page_blocks, fonts, i, len(pages), md_dir)
        img.save(output_dir / f"{i:02d}.png", "PNG")
        print(f"  saved: {output_dir / f'{i:02d}.png'}")

    print(f"Total: {len(pages)} images")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.md> <output_dir/>")
        sys.exit(1)
    render_md_to_images(sys.argv[1], sys.argv[2])
