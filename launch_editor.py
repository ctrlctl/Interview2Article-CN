"""Launch a local dual-pane editor for WeChat article drafts.

Left pane: editable Markdown (your draft).
Right pane: live-rendered WeChat preview with a "copy" button.

Usage:
    python launch_editor.py <input.md> [--theme default|warm]
                                       [--port 8765]

The page opens automatically in the default browser. The server runs in the
foreground — Ctrl+C to stop. Markdown changes auto-save back to <input.md>.
"""
import argparse
import json
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import md_to_wechat as mw


# Shell UI for the dual-pane editor. Kept small and self-contained.
EDITOR_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>WeChat Article Editor</title>
<style>
    * { box-sizing: border-box; }
    html, body { height: 100%; margin: 0; font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; }
    .toolbar {
        display: flex; align-items: center; justify-content: space-between;
        padding: 10px 16px; background: #fafafa; border-bottom: 1px solid #e0e0e0;
        position: sticky; top: 0; z-index: 10;
    }
    .toolbar .title { font-weight: 600; color: #333; font-size: 14px; }
    .toolbar .status { color: #888; font-size: 12px; margin-left: 12px; }
    .toolbar button {
        padding: 8px 20px; font-size: 14px; font-weight: 600; color: #fff;
        background: #07c160; border: none; border-radius: 4px; cursor: pointer;
        transition: background 0.15s;
    }
    .toolbar button:hover { background: #06ae56; }
    .toolbar button:active { background: #059c4d; }
    .panes {
        display: flex; height: calc(100vh - 53px);
    }
    .pane { flex: 1; overflow: auto; position: relative; }
    .pane-left {
        border-right: 1px solid #e0e0e0; background: #fff;
    }
    .pane-left textarea {
        width: 100%; height: 100%; border: none; outline: none; resize: none;
        padding: 20px; font-family: Consolas, Menlo, "Courier New", monospace;
        font-size: 14px; line-height: 1.7; color: #333;
    }
    .pane-right { background: #f5f5f5; padding: 20px; }
    .preview-card {
        background: #fff; border-radius: 6px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        overflow: hidden;
    }
</style>
</head>
<body>
    <div class="toolbar">
        <div>
            <span class="title">WeChat 公众号文章编辑器</span>
            <span class="status" id="status">已就绪</span>
        </div>
        <button id="copyBtn" onclick="copyForWeChat()">复制到公众号</button>
    </div>
    <div class="panes">
        <div class="pane pane-left">
            <textarea id="md" spellcheck="false" placeholder="在这里编辑 Markdown..."></textarea>
        </div>
        <div class="pane pane-right">
            <div class="preview-card" id="preview">加载中...</div>
        </div>
    </div>
<script>
    const mdEl = document.getElementById('md');
    const previewEl = document.getElementById('preview');
    const statusEl = document.getElementById('status');

    let renderTimer = null;
    let saveTimer = null;
    let lastRenderedText = null;

    async function render() {
        const text = mdEl.value;
        if (text === lastRenderedText) return;
        lastRenderedText = text;
        statusEl.textContent = '渲染中...';
        try {
            const resp = await fetch('/render', {
                method: 'POST',
                headers: { 'Content-Type': 'text/plain; charset=utf-8' },
                body: text,
            });
            const html = await resp.text();
            previewEl.innerHTML = html;
            statusEl.textContent = '已渲染';
        } catch (e) {
            statusEl.textContent = '渲染失败：' + e;
        }
    }

    async function save() {
        try {
            await fetch('/save', {
                method: 'POST',
                headers: { 'Content-Type': 'text/plain; charset=utf-8' },
                body: mdEl.value,
            });
            statusEl.textContent = '已保存 · ' + new Date().toLocaleTimeString();
        } catch (e) {
            statusEl.textContent = '保存失败：' + e;
        }
    }

    mdEl.addEventListener('input', () => {
        clearTimeout(renderTimer);
        clearTimeout(saveTimer);
        renderTimer = setTimeout(render, 300);
        saveTimer = setTimeout(save, 1000);
    });

    async function copyForWeChat() {
        // The preview-card's first child is the rendered <section id="wx-article-root">.
        const node = document.getElementById('wx-article-root');
        if (!node) {
            alert('还没渲染出内容');
            return;
        }
        const html = node.outerHTML;
        const text = node.innerText;
        try {
            const blobHtml = new Blob([html], { type: 'text/html' });
            const blobText = new Blob([text], { type: 'text/plain' });
            await navigator.clipboard.write([
                new ClipboardItem({ 'text/html': blobHtml, 'text/plain': blobText })
            ]);
            const btn = document.getElementById('copyBtn');
            const original = btn.textContent;
            btn.textContent = '已复制 ✓ 去粘贴';
            setTimeout(() => { btn.textContent = original; }, 2000);
        } catch (e) {
            alert('复制失败：' + e + '\n请在右侧手动 Ctrl+A / Ctrl+C');
        }
    }

    // Load initial markdown from the server.
    (async () => {
        const resp = await fetch('/md');
        mdEl.value = await resp.text();
        render();
    })();
</script>
</body>
</html>
"""


def make_handler(md_path: Path, theme_name: str):
    """Create a request handler bound to the given markdown file."""

    base_dir = md_path.parent.resolve()

    class Handler(BaseHTTPRequestHandler):
        # Silence default noisy per-request logging; keep errors visible.
        def log_message(self, fmt, *args):
            pass

        def _send_text(self, body: str, content_type="text/html; charset=utf-8", code=200):
            payload = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/" or path == "/editor":
                self._send_text(EDITOR_HTML)
            elif path == "/md":
                text = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
                self._send_text(text, content_type="text/plain; charset=utf-8")
            else:
                self._send_text("Not found", code=404, content_type="text/plain; charset=utf-8")

        def do_POST(self):
            path = urlparse(self.path).path
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")

            if path == "/render":
                try:
                    _full, article_fragment = mw.convert(
                        body,
                        theme_name=theme_name,
                        inline_images_base_dir=base_dir,
                    )
                    self._send_text(article_fragment)
                except Exception as e:
                    err = f'<div style="padding:20px;color:#c00;">渲染出错：{e}</div>'
                    self._send_text(err, code=500)
            elif path == "/save":
                md_path.write_text(body, encoding="utf-8")
                self._send_text("ok", content_type="text/plain; charset=utf-8")
            else:
                self._send_text("Not found", code=404, content_type="text/plain; charset=utf-8")

    return Handler


def main():
    parser = argparse.ArgumentParser(description="Dual-pane WeChat article editor")
    parser.add_argument("input", help="Markdown file to edit")
    parser.add_argument("--theme", choices=list(mw.THEMES.keys()), default="default")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true",
                        help="Don't auto-open the browser")
    args = parser.parse_args()

    md_path = Path(args.input).resolve()
    if not md_path.exists():
        # Create an empty file so save path works immediately.
        md_path.write_text("# 新文章\n\n在此开始编辑\n", encoding="utf-8")

    handler = make_handler(md_path, args.theme)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    url = f"http://127.0.0.1:{args.port}/"

    print(f"Editor running at {url}")
    print(f"Editing: {md_path}")
    print("Ctrl+C to stop.")

    if not args.no_browser:
        # Short delay so the server is ready when the browser hits it.
        threading.Thread(
            target=lambda: (time.sleep(0.4), webbrowser.open(url)),
            daemon=True,
        ).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
        server.shutdown()


if __name__ == "__main__":
    main()
