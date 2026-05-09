"""Fetch a product image via DuckDuckGo image search and save it locally.

Usage:
    python fetch_product_image.py "Bastl Instruments Neo Trinity" [out_dir]

Prints a markdown snippet on stdout on success.

Exit codes:
    0 — success, markdown snippet printed on stdout
    2 — search returned zero usable results after retries (no images at all, or
        every result failed to download). Emits a <!-- IMAGE_NEEDED --> placeholder
        on stdout so the caller can paste it straight into the article.
    3 — upstream search transport failed after all retries (network / DDG outage).
        Prints a clear error to stderr. The agent should decide whether to retry
        later with different phrasing or stop and ask the user.

No API key required.
"""
import re
import sys
import time
from pathlib import Path

import requests
from ddgs import DDGS
from ddgs.exceptions import DDGSException


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

MAX_SEARCH_ATTEMPTS = 3
SEARCH_BACKOFF_SECONDS = (2, 4, 8)


def slugify(text, max_len=60):
    """Make a filesystem-safe slug from a query string."""
    s = re.sub(r"[^\w\-\u4e00-\u9fff]+", "_", text.strip())
    s = s.strip("_")
    return s[:max_len] or "image"


def search_with_retry(query, max_attempts=MAX_SEARCH_ATTEMPTS, max_results=5):
    """Search DDG images with up to `max_attempts` retries on transport errors.

    Returns the (possibly empty) results list. Raises DDGSException if every
    attempt fails with a transport error — the caller should treat that as a
    hard outage, not a "no results" case.
    """
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            with DDGS() as ddgs:
                return list(ddgs.images(query, max_results=max_results, safesearch="moderate"))
        except DDGSException as e:
            last_exc = e
            if attempt < max_attempts:
                wait = SEARCH_BACKOFF_SECONDS[min(attempt - 1, len(SEARCH_BACKOFF_SECONDS) - 1)]
                print(
                    f"  search attempt {attempt}/{max_attempts} failed: {e}; retrying in {wait}s",
                    file=sys.stderr,
                )
                time.sleep(wait)
            else:
                print(
                    f"  search attempt {attempt}/{max_attempts} failed: {e}; giving up",
                    file=sys.stderr,
                )
    # All attempts exhausted.
    raise last_exc


def search_and_download(query, out_dir="images", max_download_attempts=5):
    """Search for `query` on DDG images, download the first one that works.

    Returns a dict on success, or None if the search returned zero usable
    results (every result failed to download).
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    results = search_with_retry(query, max_results=max_download_attempts)

    if not results:
        return None

    for r in results:
        url = r.get("image")
        if not url:
            continue
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"  skip {url[:60]}... ({e})", file=sys.stderr)
            continue

        ctype = resp.headers.get("Content-Type", "").lower()
        if "jpeg" in ctype or "jpg" in ctype:
            ext = ".jpg"
        elif "png" in ctype:
            ext = ".png"
        elif "webp" in ctype:
            ext = ".webp"
        else:
            # Skip odd content types; keep trying.
            continue

        filename = slugify(query) + ext
        filepath = out_path / filename
        filepath.write_bytes(resp.content)
        return {
            "path": str(filepath).replace("\\", "/"),
            "source_url": url,
            "query": query,
        }

    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_product_image.py <query> [out_dir]", file=sys.stderr)
        sys.exit(1)

    query = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "images"

    print(f"Searching: {query}", file=sys.stderr)

    try:
        result = search_and_download(query, out_dir=out_dir)
    except DDGSException as e:
        # Transport failure after retries. Clear error, distinct exit code so
        # the agent can distinguish "network is down" from "no matches found".
        print(
            f"ERROR: image search transport failed after {MAX_SEARCH_ATTEMPTS} attempts: {e}",
            file=sys.stderr,
        )
        print(
            "The DuckDuckGo / Bing backend is unreachable or rate-limited. "
            "Retry later or search manually.",
            file=sys.stderr,
        )
        sys.exit(3)

    if result is None:
        # Search worked but produced no usable image. Placeholder, non-fatal.
        print(f"<!-- IMAGE_NEEDED: {query} -->")
        sys.exit(2)

    # Success: emit a markdown snippet ready to paste into the article.
    print(f"![{query}]({result['path']})")
    print(f"*▲ {query}*")
    print(f"<!-- source: {result['source_url']} -->")


if __name__ == "__main__":
    main()
