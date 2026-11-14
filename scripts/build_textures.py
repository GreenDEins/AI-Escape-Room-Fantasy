"""
Builds the seamless background textures used by the UI (ui/assets/textures/*.jpg).

The textures are procedural SVG (fractal noise with stitchTiles="stitch", so the
tiles repeat without seams) rasterised with the pre-installed Chromium via
Playwright. The JPEGs are committed, so you only need this script if you want
to change the look:

    python scripts/build_textures.py
"""

from __future__ import annotations

import base64
import random
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "ui" / "assets" / "textures"
SIZE = 512


def stone() -> str:
    """Dark dungeon wall: ashlar blocks with mortar, worn edges and grime."""
    rnd = random.Random(12)
    rows, row_h = 8, SIZE / 8
    blocks = []
    for r in range(rows):
        widths: list[float] = []
        while sum(widths) < SIZE - 150:
            widths.append(rnd.uniform(70, 150))
        widths.append(SIZE - sum(widths))   # each row is exactly one tile wide
        x = -rnd.uniform(0, 60)
        for w in widths:
            shade = rnd.randint(30, 44)
            c = f"#{shade:02x}{int(shade * .82):02x}{int(shade * .7):02x}"
            for dx in (-SIZE, 0, SIZE):  # wrap horizontally so the tile is seamless
                blocks.append(f'<rect x="{x + dx + 2}" y="{r * row_h + 2}" width="{w - 4}" height="{row_h - 4}" rx="3" fill="{c}"/>')
                blocks.append(f'<path d="M{x + dx + 4} {r * row_h + 3}h{w - 8}" stroke="#fff" stroke-opacity=".05" stroke-width="2"/>')
                blocks.append(f'<path d="M{x + dx + 4} {(r + 1) * row_h - 3}h{w - 8}" stroke="#000" stroke-opacity=".4" stroke-width="2.5"/>')
            x += w
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}">
<defs>
  <filter id="n" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency=".035" numOctaves="5" seed="4" stitchTiles="stitch"/>
    <feColorMatrix values="0 0 0 0 .45  0 0 0 0 .38  0 0 0 0 .32  0 0 0 1.7 -.6"/>
  </filter>
  <filter id="f" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency=".8" numOctaves="2" seed="2" stitchTiles="stitch"/>
    <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.2 .75"/>
  </filter>
</defs>
<rect width="{SIZE}" height="{SIZE}" fill="#0e0906"/>
{"".join(blocks)}
<rect width="{SIZE}" height="{SIZE}" filter="url(#n)" style="mix-blend-mode:multiply" opacity=".8"/>
<rect width="{SIZE}" height="{SIZE}" filter="url(#f)" opacity=".5"/>
</svg>"""


def parchment() -> str:
    """Aged parchment: warm base, fibres, blotches and fine grain."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}">
<defs>
  <filter id="blot" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency=".012" numOctaves="4" seed="7" stitchTiles="stitch"/>
    <feColorMatrix values="0 0 0 0 .55  0 0 0 0 .38  0 0 0 0 .16  0 0 0 1.3 -.45"/>
  </filter>
  <filter id="fibre" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency=".004 .09" numOctaves="3" seed="3" stitchTiles="stitch"/>
    <feColorMatrix values="0 0 0 0 .45  0 0 0 0 .3  0 0 0 0 .12  0 0 0 1.4 -.6"/>
  </filter>
  <filter id="grain" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="5" stitchTiles="stitch"/>
    <feColorMatrix values="0 0 0 0 .3  0 0 0 0 .2  0 0 0 0 .08  0 0 0 -1 .55"/>
  </filter>
</defs>
<rect width="{SIZE}" height="{SIZE}" fill="#ecdcb2"/>
<rect width="{SIZE}" height="{SIZE}" filter="url(#blot)" opacity=".7"/>
<rect width="{SIZE}" height="{SIZE}" filter="url(#fibre)" opacity=".35"/>
<rect width="{SIZE}" height="{SIZE}" filter="url(#grain)" opacity=".35"/>
</svg>"""


def leather() -> str:
    """Dark tooled leather for the character sheet."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}">
<defs>
  <filter id="pores" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="turbulence" baseFrequency=".06" numOctaves="3" seed="8" stitchTiles="stitch"/>
    <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -2.2 1.1"/>
  </filter>
  <filter id="mottle" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency=".01" numOctaves="3" seed="6" stitchTiles="stitch"/>
    <feColorMatrix values="0 0 0 0 .32  0 0 0 0 .19  0 0 0 0 .1  0 0 0 1.2 -.4"/>
  </filter>
</defs>
<rect width="{SIZE}" height="{SIZE}" fill="#22150c"/>
<rect width="{SIZE}" height="{SIZE}" filter="url(#mottle)" opacity=".45"/>
<rect width="{SIZE}" height="{SIZE}" filter="url(#pores)" opacity=".35"/>
</svg>"""


def render(svg: str, out: Path) -> None:
    uri = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    html = f"<html><body style='margin:0'><img src='{uri}' width='{SIZE}' height='{SIZE}' style='display:block'></body></html>"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": SIZE, "height": SIZE})
        page.set_content(html)
        page.wait_for_timeout(300)
        page.screenshot(path=str(out), type="jpeg", quality=82)
        browser.close()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in [("stone", stone), ("parchment", parchment), ("leather", leather)]:
        render(fn(), OUT / f"{name}.jpg")
        print("wrote", (OUT / f"{name}.jpg").relative_to(OUT.parent.parent.parent))


if __name__ == "__main__":
    main()
