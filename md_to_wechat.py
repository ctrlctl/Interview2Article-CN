"""Convert a Markdown file into WeChat-ready HTML with inline styles.

Inspired by the default theme of doocs/md (https://md.doocs.org). Generates a
self-contained HTML file where every element has inline CSS — this is required
because the WeChat editor strips <style> tags and external stylesheets.

Usage:
    python md_to_wechat.py <input.md> [output.html] [--theme default|warm]
                                                    [--inline-images]
                                                    [--copy]

Workflow:
    Fastest path:
        python md_to_wechat.py article.md --inline-images --copy
        # Done. Open WeChat editor, Ctrl+V.

    Or open the generated HTML in a browser and use the "一键复制" button
    at the top, then paste into WeChat.

Images:
    - Default: local image paths are kept. You upload them manually in the
      WeChat editor (safest — WeChat hosts them on its CDN permanently).
    - --inline-images: images are embedded as base64 data URIs in the HTML.
      The browser displays them normally. When you copy-paste into the WeChat
      editor, WeChat auto-uploads the embedded images to its CDN. This gives
      you a "one command, complete article" workflow with no third-party
      image hosting risk.
"""
import argparse
import base64
import io
import mimetypes
import re
import sys
from pathlib import Path

import markdown
from premailer import transform


# Force UTF-8 on stdout/stderr so Chinese text and arrow glyphs print correctly
# under Windows consoles still defaulting to cp1252.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


# ---------------------------------------------------------------------------
# Themes (inspired by doocs/md default style)
# ---------------------------------------------------------------------------

THEMES = {
    "default": {
        "primary": "#1e88e5",        # link / accent color
        "heading": "#1a1a1a",
        "body_text": "#3f3f3f",
        "muted": "#888888",
        "blockquote_bg": "#f7f7f7",
        "blockquote_border": "#1e88e5",
        "code_bg": "#f5f5f5",
        "code_text": "#c7254e",
        "table_head_bg": "#fafafa",
        "table_border": "#e8e8e8",
        "hr_color": "#e0e0e0",
    },
    "warm": {
        "primary": "#d97757",
        "heading": "#1a1a1a",
        "body_text": "#3f3f3f",
        "muted": "#888888",
        "blockquote_bg": "#fdf6f2",
        "blockquote_border": "#d97757",
        "code_bg": "#f5f0ec",
        "code_text": "#b84a2e",
        "table_head_bg": "#fdf6f2",
        "table_border": "#eadfd6",
        "hr_color": "#eadfd6",
    },
}


def build_css(theme):
    """Return a CSS string that premailer will inline onto every element.

    All sizes use px (not rem/em) because WeChat's mobile renderer handles px
    predictably. Line-height is relative, which is safe.
    """
    t = theme
    return f"""
    .wx-article {{
        max-width: 677px;
        margin: 0 auto;
        padding: 20px 16px;
        color: {t['body_text']};
        font-family: "Source Han Serif SC", "Noto Serif SC", "Songti SC",
                     "STSong", "SimSun", "Times New Roman", Georgia, serif;
        font-size: 16px;
        line-height: 1.85;
        letter-spacing: 0.05em;
        word-break: break-word;
    }}

    .wx-article h1 {{
        font-size: 24px;
        font-weight: 700;
        color: {t['heading']};
        text-align: center;
        margin: 28px 0 20px;
        padding-bottom: 12px;
        border-bottom: 2px solid {t['heading']};
        line-height: 1.4;
    }}
    .wx-article h2 {{
        font-size: 20px;
        font-weight: 700;
        color: {t['heading']};
        margin: 36px 0 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid {t['heading']};
        line-height: 1.4;
    }}
    .wx-article h3 {{
        font-size: 17px;
        font-weight: 700;
        color: {t['heading']};
        margin: 28px 0 12px;
        padding-left: 10px;
        border-left: 4px solid {t['primary']};
        line-height: 1.4;
    }}
    .wx-article h4 {{
        font-size: 15px;
        font-weight: 700;
        color: {t['heading']};
        margin: 20px 0 10px;
    }}

    .wx-article p {{
        margin: 14px 0;
        color: {t['body_text']};
    }}

    .wx-article strong {{
        color: {t['heading']};
        font-weight: 700;
    }}
    .wx-article em {{
        color: {t['muted']};
        font-style: normal;
    }}

    .wx-article a {{
        color: {t['primary']};
        text-decoration: none;
        border-bottom: 1px solid {t['primary']};
    }}

    .wx-article blockquote {{
        margin: 16px 0;
        padding: 12px 16px;
        background: {t['blockquote_bg']};
        border-left: 4px solid {t['blockquote_border']};
        color: {t['body_text']};
        font-size: 14px;
        border-radius: 0 4px 4px 0;
    }}
    .wx-article blockquote p {{
        margin: 6px 0;
    }}

    .wx-article ul, .wx-article ol {{
        margin: 14px 0;
        padding-left: 24px;
    }}
    .wx-article li {{
        margin: 6px 0;
    }}

    .wx-article hr {{
        margin: 28px 0;
        border: none;
        border-top: 1px solid {t['hr_color']};
    }}

    .wx-article img {{
        display: block;
        max-width: 100%;
        height: auto;
        margin: 16px auto;
        border-radius: 4px;
    }}

    .wx-article table {{
        width: 100%;
        margin: 16px 0;
        border-collapse: collapse;
        font-size: 14px;
    }}
    .wx-article th, .wx-article td {{
        padding: 8px 12px;
        border: 1px solid {t['table_border']};
        text-align: left;
    }}
    .wx-article th {{
        background: {t['table_head_bg']};
        color: {t['heading']};
        font-weight: 700;
    }}

    .wx-article code {{
        padding: 2px 6px;
        background: {t['code_bg']};
        color: {t['code_text']};
        border-radius: 3px;
        font-family: Consolas, Menlo, monospace;
        font-size: 13px;
    }}
    .wx-article pre {{
        margin: 16px 0;
        padding: 12px 16px;
        background: {t['code_bg']};
        border-radius: 4px;
        overflow-x: auto;
        font-size: 13px;
        line-height: 1.6;
    }}
    .wx-article pre code {{
        padding: 0;
        background: transparent;
        color: {t['body_text']};
    }}
    """


# ---------------------------------------------------------------------------
# Image inlining (base64 data URIs)
# ---------------------------------------------------------------------------

IMG_SRC_RE = re.compile(r'(<img [^>]*?src=")([^"]+)(")', re.IGNORECASE)


def inline_images(html, base_dir):
    """Replace <img src="local/path"> with base64 data URIs.

    Remote URLs (http://, https://, data:) are left alone. Missing local files
    are left alone with a warning on stderr.
    """
    def repl(m):
        prefix, src, suffix = m.group(1), m.group(2), m.group(3)
        if src.startswith(("http://", "https://", "data:")):
            return m.group(0)
        img_path = (base_dir / src).resolve()
        if not img_path.exists():
            print(f"  WARNING: image not found, leaving path as-is: {src}", file=sys.stderr)
            return m.group(0)
        mime, _ = mimetypes.guess_type(str(img_path))
        mime = mime or "image/jpeg"
        data = base64.b64encode(img_path.read_bytes()).decode("ascii")
        print(f"  inlined {src} ({img_path.stat().st_size // 1024} KB)", file=sys.stderr)
        return f"{prefix}data:{mime};base64,{data}{suffix}"

    return IMG_SRC_RE.sub(repl, html)


# ---------------------------------------------------------------------------
# Post-processing: caption lines + figure captions
# ---------------------------------------------------------------------------

CAPTION_LINE_RE = re.compile(
    r"<p>(<em>▲[^<]*</em>)</p>",
    flags=re.IGNORECASE,
)


def style_figure_captions(html):
    """Give caption paragraphs (e.g. '*▲ Neo Trinity*') a distinct center style."""
    def repl(m):
        inner = m.group(1)
        return (
            '<p style="text-align:center;color:#888;font-size:13px;'
            'margin:-6px 0 18px;">'
            + inner
            + "</p>"
        )

    return CAPTION_LINE_RE.sub(repl, html)


# ---------------------------------------------------------------------------
# Main conversion
# ---------------------------------------------------------------------------

# Outer shell (copy button + script). Never passed through premailer — these
# styles need to remain as a <style> block so the button stays styled in the
# local browser view. The copy handler only grabs the article <section>, so
# this shell never leaks into the WeChat paste.
OUTER_SHELL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ margin: 0; background: #f5f5f5; }}
        .wx-copy-bar {{
            position: sticky;
            top: 0;
            z-index: 99;
            background: #ffffff;
            border-bottom: 1px solid #e0e0e0;
            padding: 10px 16px;
            text-align: center;
            font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
        }}
        .wx-copy-bar button {{
            padding: 8px 24px;
            font-size: 14px;
            font-weight: 600;
            color: #fff;
            background: #07c160;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background 0.15s;
        }}
        .wx-copy-bar button:hover {{ background: #06ae56; }}
        .wx-copy-bar button:active {{ background: #059c4d; }}
        .wx-copy-bar .hint {{
            margin-left: 12px;
            color: #888;
            font-size: 13px;
        }}
        .wx-stage {{ background: #fff; }}
        @media print {{ .wx-copy-bar {{ display: none; }} }}
    </style>
    <script>
        function wxCopy() {{
            const node = document.getElementById('wx-article-root');
            const html = node.outerHTML;
            const text = node.innerText;
            const blobHtml = new Blob([html], {{ type: 'text/html' }});
            const blobText = new Blob([text], {{ type: 'text/plain' }});
            const item = new ClipboardItem({{
                'text/html': blobHtml,
                'text/plain': blobText,
            }});
            navigator.clipboard.write([item]).then(() => {{
                const btn = document.getElementById('wx-copy-btn');
                const original = btn.textContent;
                btn.textContent = '已复制 ✓ 去粘贴';
                btn.style.background = '#059c4d';
                setTimeout(() => {{
                    btn.textContent = original;
                    btn.style.background = '#07c160';
                }}, 2000);
            }}).catch(err => {{
                alert('复制失败：' + err + '\\n请改用 Ctrl+A / Ctrl+C 手动复制');
            }});
        }}
    </script>
</head>
<body>
<div class="wx-copy-bar">
    <button id="wx-copy-btn" onclick="wxCopy()">一键复制到公众号</button>
    <span class="hint">点击后打开公众号编辑器 Ctrl+V 粘贴</span>
</div>
<div class="wx-stage">
{article}
</div>
</body>
</html>
"""

# Inner article template — goes through premailer for CSS inlining.
ARTICLE_TEMPLATE = """<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{css}</style></head><body>
<section class="wx-article" id="wx-article-root">
{body}
</section>
</body></html>"""


def convert(md_text, theme_name="default", inline_images_base_dir=None):
    theme = THEMES.get(theme_name, THEMES["default"])

    md = markdown.Markdown(
        extensions=[
            "extra",          # tables, fenced code, etc.
            "sane_lists",
            "nl2br",          # single newline → <br> (WeChat-friendly)
            "codehilite",
        ],
        extension_configs={
            "codehilite": {"noclasses": True, "pygments_style": "friendly"},
        },
    )
    body = md.convert(md_text)
    body = style_figure_captions(body)

    if inline_images_base_dir is not None:
        body = inline_images(body, inline_images_base_dir)

    # Pull H1 as document title if present.
    title_match = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.IGNORECASE | re.DOTALL)
    title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip() if title_match else "WeChat Article"

    # Stage 1: render the article with its CSS and inline everything via premailer.
    css = build_css(theme)
    article_html = ARTICLE_TEMPLATE.format(css=css, body=body)
    inlined = transform(
        article_html,
        keep_style_tags=False,
        remove_classes=True,
        strip_important=False,
    )
    # Extract just the <section>…</section> (this is what the copy button grabs).
    article_section_match = re.search(
        r"<section[^>]*id=[\"']wx-article-root[\"'][^>]*>.*?</section>",
        inlined,
        flags=re.DOTALL | re.IGNORECASE,
    )
    article_section = article_section_match.group(0) if article_section_match else inlined

    # Stage 2: wrap the inlined article in the outer shell (copy button + script).
    return OUTER_SHELL.format(title=title, article=article_section), article_section


def copy_html_to_clipboard(html_fragment):
    """Put an HTML fragment on the Windows clipboard using CF_HTML format.

    This is the format WeChat / browsers / Word recognize as "rich text HTML
    paste". On Windows we use pywin32. On other platforms we print a message
    explaining manual copy.

    Returns True on success, False on failure.
    """
    if sys.platform != "win32":
        print(
            "ERROR: --copy currently implemented for Windows only. "
            "Open the HTML file in a browser and use the '一键复制' button instead.",
            file=sys.stderr,
        )
        return False

    try:
        import win32clipboard
    except ImportError:
        print(
            "ERROR: pywin32 not installed. Run: pip install --user pywin32",
            file=sys.stderr,
        )
        return False

    # Build CF_HTML payload. See:
    # https://learn.microsoft.com/en-us/windows/win32/dataxchg/html-clipboard-format
    header_template = (
        "Version:0.9\r\n"
        "StartHTML:{start_html:010d}\r\n"
        "EndHTML:{end_html:010d}\r\n"
        "StartFragment:{start_frag:010d}\r\n"
        "EndFragment:{end_frag:010d}\r\n"
    )
    prefix = "<html><body><!--StartFragment-->"
    suffix = "<!--EndFragment--></body></html>"
    # Measure lengths in UTF-8 bytes; CF_HTML offsets are byte offsets.
    header_placeholder = header_template.format(
        start_html=0, end_html=0, start_frag=0, end_frag=0,
    )
    header_len = len(header_placeholder.encode("utf-8"))
    start_html = header_len
    start_frag = start_html + len(prefix.encode("utf-8"))
    end_frag = start_frag + len(html_fragment.encode("utf-8"))
    end_html = end_frag + len(suffix.encode("utf-8"))

    header = header_template.format(
        start_html=start_html,
        end_html=end_html,
        start_frag=start_frag,
        end_frag=end_frag,
    )
    payload = (header + prefix + html_fragment + suffix).encode("utf-8")

    CF_HTML = win32clipboard.RegisterClipboardFormat("HTML Format")
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(CF_HTML, payload)
        # Also set plain text as a fallback for non-HTML-aware paste targets.
        plain = re.sub(r"<[^>]+>", "", html_fragment)
        plain = re.sub(r"\s+\n", "\n", plain)
        win32clipboard.SetClipboardData(
            win32clipboard.CF_UNICODETEXT, plain,
        )
    finally:
        win32clipboard.CloseClipboard()
    return True


def main():
    parser = argparse.ArgumentParser(description="Markdown → WeChat HTML")
    parser.add_argument("input", help="Input markdown file")
    parser.add_argument(
        "output", nargs="?", default=None,
        help="Output HTML file (default: <input>.html)",
    )
    parser.add_argument(
        "--theme", choices=list(THEMES.keys()), default="default",
        help="Color theme",
    )
    parser.add_argument(
        "--inline-images", action="store_true",
        help="Embed local images as base64 data URIs (one-command workflow; "
             "WeChat auto-uploads them to its CDN on paste)",
    )
    parser.add_argument(
        "--copy", action="store_true",
        help="After generating, copy the rendered HTML directly to the system "
             "clipboard. Go straight to WeChat editor and Ctrl+V. (Windows only)",
    )
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"ERROR: {in_path} not found", file=sys.stderr)
        sys.exit(1)

    out_path = Path(args.output) if args.output else in_path.with_suffix(".html")

    md_text = in_path.read_text(encoding="utf-8")
    base_dir = in_path.parent.resolve() if args.inline_images else None
    full_html, article_fragment = convert(
        md_text, theme_name=args.theme, inline_images_base_dir=base_dir,
    )
    out_path.write_text(full_html, encoding="utf-8")

    size_kb = out_path.stat().st_size // 1024
    print(f"OK → {out_path} ({size_kb} KB)")

    if args.copy:
        if copy_html_to_clipboard(article_fragment):
            frag_kb = len(article_fragment.encode("utf-8")) // 1024
            print(f"Clipboard: {frag_kb} KB of rendered HTML ready to paste.")
            print()
            print("Next: open the WeChat editor and press Ctrl+V.")
        else:
            print("Clipboard copy failed — falling back to the HTML file.",
                  file=sys.stderr)
            sys.exit(1)
        return

    print()
    print("Next steps:")
    print(f"  1. Open {out_path} in a browser")
    print("  2. Click the green '一键复制到公众号' button at the top")
    print("     (or Ctrl+A / Ctrl+C the article body manually)")
    print("  3. Paste into the WeChat Official Account editor")
    if args.inline_images:
        print("  4. WeChat auto-uploads embedded images to its CDN — done")
    else:
        print("  4. Replace local images via WeChat's built-in image uploader")
        print()
        print("Tip: re-run with --inline-images to skip the manual image step")


if __name__ == "__main__":
    main()
