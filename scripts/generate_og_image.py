#!/usr/bin/env python3
"""Regenerate website/public/og-image.png (1200x630 Open Graph share card).

The card is referenced by website/src/app/layout.tsx (and the shared
detail-route metadata) as the OG/Twitter image for ao.moss.land. Rerun this
script only when the design needs to change, then commit the new PNG —
the image is a static asset; nothing generates it at build time.

Design: dark terminal window on #0d1117, MOSS :: AO wordmark in the site's
green (#39ff14) / cyan (#00ffff), JetBrains Mono (the site font), tagline
"Agentic Orchestrator · Mossland". Rendered at 2x and downscaled with
LANCZOS so the type stays crisp; output is ~58 KB.

Requires Pillow (`pip install pillow`). The JetBrains Mono variable font is
fetched once from the google/fonts repo (the same upstream the site pulls
via next/font) into ~/.cache/moss-ao/ and reused afterwards.
"""
import os
import sys
import urllib.request

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(REPO_ROOT, "website", "public", "og-image.png")

FONT_URL = (
    "https://github.com/google/fonts/raw/main/ofl/jetbrainsmono/"
    "JetBrainsMono%5Bwght%5D.ttf"
)
FONT_CACHE = os.path.join(
    os.path.expanduser("~"), ".cache", "moss-ao", "JetBrainsMono[wght].ttf"
)

S = 2  # supersample factor
W, H = 1200 * S, 630 * S

BG = "#0d1117"
WINDOW_FILL = "#010409"
WINDOW_BORDER = "#30363d"
TITLEBAR_LINE = "#21262d"
GREEN = "#39ff14"
CYAN = "#00ffff"
GRAY = "#8b949e"
LIGHT = "#c9d1d9"
DIM_TEAL = (1, 117, 120)
DOT_RED = "#ff5f56"
DOT_YELLOW = "#ffbd2e"
DOT_GREEN = "#27c93f"


def ensure_font() -> str:
    if not os.path.exists(FONT_CACHE):
        os.makedirs(os.path.dirname(FONT_CACHE), exist_ok=True)
        print(f"fetching JetBrains Mono -> {FONT_CACHE}", file=sys.stderr)
        urllib.request.urlretrieve(FONT_URL, FONT_CACHE)
    return FONT_CACHE


def font(path: str, size: int, weight: str = "Regular") -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(path, size)
    f.set_variation_by_name(weight)
    return f


def main() -> None:
    font_path = ensure_font()

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # Terminal window
    wx0, wy0, wx1, wy1 = 170, 130, W - 170, H - 130
    d.rounded_rectangle(
        (wx0, wy0, wx1, wy1),
        radius=24,
        fill=WINDOW_FILL,
        outline=WINDOW_BORDER,
        width=3,
    )

    # Title bar: traffic-light dots + hostname over a hairline
    bar_cy = wy0 + 46
    for i, color in enumerate((DOT_RED, DOT_YELLOW, DOT_GREEN)):
        cx = wx0 + 62 + i * 58
        d.ellipse((cx - 15, bar_cy - 15, cx + 15, bar_cy + 15), fill=color)
    d.text(
        ((wx0 + wx1) // 2, bar_cy),
        "ao.moss.land",
        font=font(font_path, 30, "Medium"),
        fill=GRAY,
        anchor="mm",
    )
    d.line((wx0 + 3, wy0 + 92, wx1 - 3, wy0 + 92), fill=TITLEBAR_LINE, width=2)

    left = wx0 + 100

    # Prompt line
    prompt_f = font(font_path, 44)
    x = left
    d.text((x, 330), "$", font=prompt_f, fill=GREEN)
    x += d.textlength("$ ", font=prompt_f)
    d.text((x, 330), "moss ao --orchestrate", font=prompt_f, fill=GRAY)

    # Wordmark
    mark_f = font(font_path, 250, "ExtraBold")
    x = left
    for text, color in (("MOSS", GREEN), (" :: ", GRAY), ("AO", CYAN)):
        d.text((x, 450), text, font=mark_f, fill=color)
        x += d.textlength(text, font=mark_f)

    # Tagline
    d.text(
        (left, 850),
        "Agentic Orchestrator · Mossland",
        font=font(font_path, 66, "Medium"),
        fill=LIGHT,
    )

    # Pipeline status line + block cursor
    pipe_f = font(font_path, 44)
    pipe = "signals → trends → debate → ideas → plans"
    d.text((left, 985), pipe, font=pipe_f, fill=DIM_TEAL)
    cx = left + d.textlength(pipe + "  ", font=pipe_f)
    d.rectangle((cx, 985, cx + 26, 985 + 52), fill=GREEN)

    out = img.resize((1200, 630), Image.LANCZOS)
    out.save(OUT_PATH, optimize=True)
    print(f"wrote {OUT_PATH} ({os.path.getsize(OUT_PATH)} bytes, {out.size[0]}x{out.size[1]})")


if __name__ == "__main__":
    main()
