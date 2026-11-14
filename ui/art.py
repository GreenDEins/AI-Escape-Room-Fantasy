"""
Procedural SVG artwork for the fantasy theme.

All illustrations are original vector art generated in Python. Building them in
code lets the scene react to the game state (drawer open, hidden message
revealed, door open) and keeps every random detail (stone blocks, books,
flagstones) deterministic thanks to fixed random seeds.

Public API:
    scene(drawer_open, lantern_taken, message_revealed, door_open) -> SVG string
    card(name) -> SVG string for a close-up illustration (see CARDS)
    to_data_uri(svg) -> data: URI usable in <img src="...">

SVG rendered through <img> cannot load web fonts, so text inside the art uses
Georgia / Times as a fallback serif.
"""

from __future__ import annotations

import base64
import math
import random
from functools import lru_cache

SERIF = "Georgia, 'Times New Roman', serif"

# ---------------------------------------------------------------------------
# Shared definitions: gradients, filters, patterns
# ---------------------------------------------------------------------------

DEFS = """
<defs>
  <linearGradient id="wall" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#2a2019"/><stop offset="1" stop-color="#17100b"/>
  </linearGradient>
  <linearGradient id="woodL" x1="0" x2="1">
    <stop offset="0" stop-color="#3a2211"/><stop offset=".45" stop-color="#6f4524"/><stop offset="1" stop-color="#341e0f"/>
  </linearGradient>
  <linearGradient id="woodD" x1="0" x2="1">
    <stop offset="0" stop-color="#1e1108"/><stop offset=".5" stop-color="#3f2614"/><stop offset="1" stop-color="#1b0f07"/>
  </linearGradient>
  <linearGradient id="woodTop" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#8a5a31"/><stop offset="1" stop-color="#4b2c15"/>
  </linearGradient>
  <linearGradient id="gold" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#fbe9a6"/><stop offset=".35" stop-color="#d7a746"/>
    <stop offset=".7" stop-color="#7f551a"/><stop offset="1" stop-color="#e9c46c"/>
  </linearGradient>
  <linearGradient id="goldV" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#f6dc8c"/><stop offset=".5" stop-color="#b8862e"/><stop offset="1" stop-color="#6a4610"/>
  </linearGradient>
  <linearGradient id="iron" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#6b6661"/><stop offset="1" stop-color="#26231f"/>
  </linearGradient>
  <linearGradient id="spine" x1="0" x2="1">
    <stop offset="0" stop-color="#000" stop-opacity=".45"/><stop offset=".3" stop-color="#fff" stop-opacity=".12"/>
    <stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".5"/>
  </linearGradient>
  <radialGradient id="flame" cx=".5" cy=".75" r=".65">
    <stop offset="0" stop-color="#fffbe0"/><stop offset=".3" stop-color="#ffd85c"/>
    <stop offset=".7" stop-color="#ff8a1e"/><stop offset="1" stop-color="#c2380e"/>
  </radialGradient>
  <radialGradient id="glowWarm">
    <stop offset="0" stop-color="#ffc56b" stop-opacity=".7"/><stop offset=".35" stop-color="#ff9a2e" stop-opacity=".25"/>
    <stop offset="1" stop-color="#ff7a00" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="glowViolet">
    <stop offset="0" stop-color="#efe4ff" stop-opacity=".95"/><stop offset=".35" stop-color="#a98bff" stop-opacity=".45"/>
    <stop offset="1" stop-color="#7a5cff" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="glowCyan">
    <stop offset="0" stop-color="#c9fbff" stop-opacity=".95"/><stop offset=".4" stop-color="#5fe3ff" stop-opacity=".35"/>
    <stop offset="1" stop-color="#5fe3ff" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="glowMoon">
    <stop offset="0" stop-color="#e8f0ff" stop-opacity=".9"/><stop offset=".4" stop-color="#9fb7ee" stop-opacity=".3"/>
    <stop offset="1" stop-color="#9fb7ee" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="night" cx=".5" cy=".25" r=".9">
    <stop offset="0" stop-color="#3d5288"/><stop offset=".6" stop-color="#16213f"/><stop offset="1" stop-color="#080c1a"/>
  </radialGradient>
  <linearGradient id="beam" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#c7d8ff" stop-opacity=".32"/><stop offset=".7" stop-color="#c7d8ff" stop-opacity=".08"/>
    <stop offset="1" stop-color="#c7d8ff" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#2c2119"/><stop offset="1" stop-color="#0f0a07"/>
  </linearGradient>
  <radialGradient id="rug" cx=".5" cy=".5" r=".55">
    <stop offset="0" stop-color="#8a2a2e"/><stop offset=".7" stop-color="#5a171b"/><stop offset="1" stop-color="#3a0e11"/>
  </radialGradient>
  <linearGradient id="parch" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#f4e7c3"/><stop offset=".6" stop-color="#e2c992"/><stop offset="1" stop-color="#c9a865"/>
  </linearGradient>
  <radialGradient id="vignette" cx=".5" cy=".48" r=".72">
    <stop offset=".5" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".88"/>
  </radialGradient>
  <radialGradient id="enamel" cx=".45" cy=".4" r=".7">
    <stop offset="0" stop-color="#fbf4e0"/><stop offset="1" stop-color="#d9caa2"/>
  </radialGradient>

  <filter id="stoneTex" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency=".045" numOctaves="4" seed="3" stitchTiles="stitch"/>
    <feColorMatrix values="0 0 0 0 .5  0 0 0 0 .42  0 0 0 0 .36  0 0 0 1.6 -.55"/>
  </filter>
  <filter id="grit" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="9" result="n"/>
    <feColorMatrix in="n" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.4 1.05" result="speck"/>
    <feComposite in="speck" in2="SourceGraphic" operator="in" result="s2"/>
    <feMerge><feMergeNode in="SourceGraphic"/><feMergeNode in="s2"/></feMerge>
  </filter>
  <filter id="grain" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency=".006 .22" numOctaves="3" seed="4" result="n"/>
    <feColorMatrix in="n" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.6 1.1" result="g"/>
    <feComposite in="g" in2="SourceGraphic" operator="in" result="g2"/>
    <feMerge><feMergeNode in="SourceGraphic"/><feMergeNode in="g2"/></feMerge>
  </filter>
  <filter id="bloom" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="3" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="blur2"><feGaussianBlur stdDeviation="2"/></filter>
  <filter id="blur5" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="5"/></filter>
  <filter id="blur12" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="12"/></filter>
  <filter id="softShadow" x="-20%" y="-20%" width="140%" height="160%">
    <feGaussianBlur stdDeviation="6"/>
  </filter>
</defs>
"""

LEATHERS = ["#5b2a22", "#3b4a33", "#2d3a52", "#5a4630", "#4a2f45", "#6b5236", "#2f4a4a",
            "#7a3a1e", "#3d2c22", "#55603c", "#40304f", "#6a2c2c"]


def _svg(w: int, h: int, body: str, extra_defs: str = "") -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'{DEFS}{extra_defs}{body}</svg>')


def to_data_uri(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def _f(x: float) -> str:
    return f"{x:.1f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

def stone_wall(x: float, y: float, w: float, h: float, seed: int = 7, row_h: float = 34) -> str:
    """Irregular ashlar blocks with mortar, bevel light and a noise texture."""
    rnd = random.Random(seed)
    out = [f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" fill="#120c08"/>']
    row = 0
    yy = y
    while yy < y + h:
        xx = x - (rnd.uniform(10, 50) if row % 2 else 0)
        while xx < x + w:
            bw = rnd.uniform(58, 112)
            base = rnd.randint(36, 52)
            r, g, b = base, int(base * .8), int(base * .66)
            c = f"#{r:02x}{g:02x}{b:02x}"
            out.append(f'<rect x="{_f(xx + 1.5)}" y="{_f(yy + 1.5)}" width="{_f(bw - 3)}" height="{_f(row_h - 3)}" rx="2.5" fill="{c}"/>')
            out.append(f'<path d="M{_f(xx + 3)} {_f(yy + 2.5)}h{_f(bw - 6)}" stroke="#fff" stroke-opacity=".07" stroke-width="1.5"/>')
            out.append(f'<path d="M{_f(xx + 3)} {_f(yy + row_h - 2.5)}h{_f(bw - 6)}" stroke="#000" stroke-opacity=".35" stroke-width="2"/>')
            if rnd.random() < .12:  # a crack
                cx = xx + rnd.uniform(10, bw - 20)
                out.append(f'<path d="M{_f(cx)} {_f(yy + 4)}l{_f(rnd.uniform(-6, 6))} 9l{_f(rnd.uniform(-5, 5))} 8" '
                           f'stroke="#0b0705" stroke-width="1.2" fill="none" opacity=".7"/>')
            xx += bw
        yy += row_h
        row += 1
    out.append(f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" filter="url(#stoneTex)" opacity=".55" '
               f'style="mix-blend-mode:multiply"/>')
    return f'<g>{"".join(out)}</g>'


def flame(x: float, y: float, s: float = 1, animate: bool = True, dur: float = .9) -> str:
    """A flickering flame whose base is at (x, y)."""
    anim = (f'<animateTransform attributeName="transform" type="scale" additive="sum" '
            f'values="1 1;1.07 .9;.94 1.08;1.03 .96;1 1" dur="{dur}s" repeatCount="indefinite"/>') if animate else ""
    return (f'<g transform="translate({_f(x)} {_f(y)}) scale({s})"><g>{anim}'
            f'<path d="M0 0c-9 0-13-8-11-15 2-8 8-10 8-19 5 5 6 9 6 13 2-3 2-6 1-10 7 6 10 14 8 21-1 6-5 10-12 10z" '
            f'fill="url(#flame)" filter="url(#bloom)"/>'
            f'<path d="M0-2c-4 0-6-4-5-7 1-4 4-5 4-9 4 4 6 7 5 11-1 3-2 5-4 5z" fill="#fffbe6" opacity=".9"/></g></g>')


def glow(x: float, y: float, r: float, grad: str = "glowWarm", animate: bool = True,
         values: str = ".85;1;.8;.95;.85", dur: float = 2.2) -> str:
    anim = (f'<animate attributeName="opacity" values="{values}" dur="{dur}s" repeatCount="indefinite"/>'
            if animate else "")
    return f'<circle cx="{_f(x)}" cy="{_f(y)}" r="{_f(r)}" fill="url(#{grad})">{anim}</circle>'


def sconce(x: float, y: float, animate: bool = True) -> str:
    """Iron wall sconce with a burning torch; (x, y) = top of the torch."""
    sparks = ""
    if animate:
        for i, (dx, d) in enumerate([(-3, 2.6), (4, 3.4), (0, 2.9)]):
            sparks += (f'<circle cx="{_f(x + dx)}" cy="{_f(y - 20)}" r="1.2" fill="#ffd27a">'
                       f'<animate attributeName="cy" values="{_f(y - 20)};{_f(y - 70)}" dur="{d}s" begin="{i * .9}s" repeatCount="indefinite"/>'
                       f'<animate attributeName="opacity" values="1;0" dur="{d}s" begin="{i * .9}s" repeatCount="indefinite"/></circle>')
    return f"""<g>
  <path d="M{_f(x - 4)} {_f(y + 40)}c-14 2-20 10-20 18 0 6 5 9 9 7" fill="none" stroke="url(#iron)" stroke-width="3.5"/>
  <rect x="{_f(x - 16)}" y="{_f(y + 52)}" width="10" height="26" rx="2" fill="url(#iron)"/>
  <path d="M{_f(x - 6)} {_f(y + 2)}h12l-3 46h-6z" fill="#4a3220"/>
  <path d="M{_f(x - 11)} {_f(y - 2)}h22l-4 10h-14z" fill="url(#iron)"/>
  <path d="M{_f(x - 11)} {_f(y - 2)}h22" stroke="#9a948c" stroke-width="1"/>
  {flame(x, y - 1, 1.15, animate)}
  {sparks}
</g>"""


# ---------------------------------------------------------------------------
# Objects (drawn in scene coordinates)
# ---------------------------------------------------------------------------

def _books_row(x0: float, x1: float, base: float, max_h: float, rnd: random.Random,
               marked: dict[float, tuple[str, str]] | None = None, numerals: bool = False) -> str:
    """Fill a shelf with books; `marked` maps x positions to (colour, numeral)."""
    out = []
    x = x0 + 2
    marked = dict(marked or {})
    while x < x1 - 8:
        hit = next((mx for mx in marked if abs(mx - x) < 9), None)
        if hit is not None:
            colour, num = marked.pop(hit)
            bw, bh = 18, max_h - 2
            out.append(f'<rect x="{_f(x)}" y="{_f(base - bh)}" width="{bw}" height="{_f(bh)}" rx="1.5" fill="{colour}"/>')
            out.append(f'<rect x="{_f(x)}" y="{_f(base - bh)}" width="{bw}" height="{_f(bh)}" fill="url(#spine)"/>')
            for yy in (base - bh + 4, base - 8):
                out.append(f'<rect x="{_f(x)}" y="{_f(yy)}" width="{bw}" height="2.5" fill="url(#gold)"/>')
            if numerals:
                out.append(f'<text x="{_f(x + bw / 2)}" y="{_f(base - bh / 2 + 5)}" font-family="{SERIF}" font-weight="bold" '
                           f'font-size="15" text-anchor="middle" fill="#f6dc8c">{num}</text>')
            else:
                out.append(f'<circle cx="{_f(x + bw / 2)}" cy="{_f(base - bh / 2)}" r="2.6" fill="url(#gold)"/>')
            x += bw + 1
            continue
        r = rnd.random()
        if r < .08:  # a gap with a leaning book
            bw, bh = rnd.uniform(9, 13), rnd.uniform(.7, .9) * max_h
            c = rnd.choice(LEATHERS)
            out.append(f'<g transform="rotate(-14 {_f(x + bw)} {_f(base)})"><rect x="{_f(x + 4)}" y="{_f(base - bh)}" '
                       f'width="{_f(bw)}" height="{_f(bh)}" rx="1.5" fill="{c}"/><rect x="{_f(x + 4)}" y="{_f(base - bh)}" '
                       f'width="{_f(bw)}" height="{_f(bh)}" fill="url(#spine)"/></g>')
            x += bw + 10
            continue
        if r < .14:  # a small horizontal stack
            sw = rnd.uniform(26, 36)
            for k in range(rnd.randint(2, 4)):
                c = rnd.choice(LEATHERS)
                out.append(f'<rect x="{_f(x + rnd.uniform(-1, 3))}" y="{_f(base - 7 * (k + 1))}" width="{_f(sw - rnd.uniform(0, 6))}" '
                           f'height="6.5" rx="1" fill="{c}" stroke="#000" stroke-opacity=".3"/>')
            x += sw + 3
            continue
        bw = rnd.uniform(8, 16)
        bh = rnd.uniform(.62, .97) * max_h
        c = rnd.choice(LEATHERS)
        out.append(f'<rect x="{_f(x)}" y="{_f(base - bh)}" width="{_f(bw)}" height="{_f(bh)}" rx="1.2" fill="{c}"/>')
        out.append(f'<rect x="{_f(x)}" y="{_f(base - bh)}" width="{_f(bw)}" height="{_f(bh)}" fill="url(#spine)"/>')
        if rnd.random() < .6:
            out.append(f'<rect x="{_f(x)}" y="{_f(base - bh + 5)}" width="{_f(bw)}" height="1.6" fill="#c9973a" opacity=".55"/>')
            out.append(f'<rect x="{_f(x)}" y="{_f(base - 7)}" width="{_f(bw)}" height="1.6" fill="#c9973a" opacity=".45"/>')
        x += bw + rnd.uniform(.3, 1.2)
    return "".join(out)


def bookshelf(numerals: bool = False) -> str:
    rnd = random.Random(21)
    x0, x1, top, bottom = 48, 330, 46, 362
    shelves = [118, 190, 262, 334]
    out = [
        f'<ellipse cx="{(x0 + x1) / 2}" cy="{bottom + 4}" rx="160" ry="10" fill="#000" opacity=".55" filter="url(#softShadow)"/>',
        f'<rect x="{x0}" y="{top}" width="{x1 - x0}" height="{bottom - top}" fill="url(#woodD)" filter="url(#grain)"/>',
        f'<rect x="{x0 + 12}" y="{top + 18}" width="{x1 - x0 - 24}" height="{bottom - top - 30}" fill="#140b05"/>',
        # crown moulding
        f'<path d="M{x0 - 10} {top + 2}h{x1 - x0 + 20}v-10h-{x1 - x0 + 20}z" fill="url(#woodTop)" filter="url(#grain)"/>',
        f'<path d="M{x0 - 6} {top - 8}q{(x1 - x0) / 2 + 6} -26 {x1 - x0 + 12} 0z" fill="url(#woodL)" filter="url(#grain)"/>',
        f'<circle cx="{(x0 + x1) / 2}" cy="{top - 18}" r="6" fill="url(#gold)"/>',
    ]
    prev = top + 18
    for i, s in enumerate(shelves):
        marked = None
        if i == 1:
            marked = {120: ("#2f7a46", "2"), 178: ("#a8302b", "5"), 238: ("#2c5aa6", "8")}
        out.append(_books_row(x0 + 12, x1 - 12, s, s - prev - 6, rnd, marked, numerals))
        out.append(f'<rect x="{x0 + 8}" y="{s}" width="{x1 - x0 - 16}" height="9" fill="url(#woodTop)" filter="url(#grain)"/>')
        out.append(f'<rect x="{x0 + 8}" y="{s + 9}" width="{x1 - x0 - 16}" height="5" fill="#000" opacity=".45"/>')
        prev = s + 9
    # side posts and inner shadow
    out += [
        f'<rect x="{x0}" y="{top}" width="12" height="{bottom - top}" fill="url(#woodL)" filter="url(#grain)"/>',
        f'<rect x="{x1 - 12}" y="{top}" width="12" height="{bottom - top}" fill="url(#woodL)" filter="url(#grain)"/>',
        f'<rect x="{x0 + 12}" y="{top + 18}" width="18" height="{bottom - top - 30}" fill="#000" opacity=".35"/>',
        # skull-like crystal orb and a candle stub on top shelf
        f'<circle cx="300" cy="102" r="12" fill="#cfd8e8" opacity=".75"/><circle cx="296" cy="98" r="4" fill="#fff" opacity=".7"/>'
        f'<path d="M288 114h24l-3 4h-18z" fill="url(#gold)"/>',
        # cobweb in the top-left corner
        f'<g stroke="#e8e0d0" stroke-opacity=".18" stroke-width=".8" fill="none">'
        f'<path d="M{x0 + 12} {top + 18}l40 26M{x0 + 12} {top + 18}l18 44M{x0 + 12} {top + 18}l46 8"/>'
        f'<path d="M{x0 + 24} {top + 26}q8 2 10 -4M{x0 + 34} {top + 33}q12 2 16 -6M{x0 + 20} {top + 38}q10 -2 14 -12"/></g>',
    ]
    return f'<g>{"".join(out)}</g>'


def painting(x: float = 392, y: float = 92, w: float = 190, h: float = 150) -> str:
    """Gilded painting of three scholars holding crimson, sapphire and emerald books."""
    ix, iy, iw, ih = x + 16, y + 16, w - 32, h - 32
    scholars = []
    for k, (robe, book, skin) in enumerate([("#4b2d5a", "#b8302b", "#d9b48a"),
                                             ("#5a4a2a", "#2c5aa6", "#c9a07a"),
                                             ("#28465a", "#2f7a46", "#d9b48a")]):
        cx = ix + iw * (k + .5) / 3
        base = iy + ih
        scholars.append(f"""
<g>
  <path d="M{_f(cx - 24)} {_f(base)}c2-30 8-52 24-58 16 6 22 28 24 58z" fill="{robe}"/>
  <path d="M{_f(cx - 24)} {_f(base)}c2-30 8-52 24-58" fill="none" stroke="#000" stroke-opacity=".3" stroke-width="3"/>
  <path d="M{_f(cx - 13)} {_f(base - 54)}c0-12 6-20 13-20s13 8 13 20c-4-4-8-6-13-6s-9 2-13 6z" fill="{robe}"/>
  <ellipse cx="{_f(cx)}" cy="{_f(base - 52)}" rx="8" ry="9.5" fill="{skin}"/>
  <path d="M{_f(cx - 8)} {_f(base - 50)}q8 6 16 0" stroke="#000" stroke-opacity=".25" fill="none"/>
  <path d="M{_f(cx - 12)} {_f(base - 30)}l12 -6 12 6v12l-12 -4 -12 4z" fill="{book}" stroke="#1a1008" stroke-width="1"/>
  <path d="M{_f(cx)} {_f(base - 36)}v12" stroke="#f6dc8c" stroke-width="1"/>
</g>""")
    return f"""<g>
  <rect x="{_f(x + 6)}" y="{_f(y + 10)}" width="{_f(w)}" height="{_f(h)}" fill="#000" opacity=".5" filter="url(#softShadow)"/>
  <rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" rx="3" fill="url(#gold)"/>
  <rect x="{_f(x + 5)}" y="{_f(y + 5)}" width="{_f(w - 10)}" height="{_f(h - 10)}" fill="none" stroke="#6a4610" stroke-width="2"/>
  <rect x="{_f(x + 10)}" y="{_f(y + 10)}" width="{_f(w - 20)}" height="{_f(h - 20)}" fill="none" stroke="#fbe9a6" stroke-opacity=".6" stroke-width="1"/>
  {"".join(f'<circle cx="{_f(px)}" cy="{_f(py)}" r="5" fill="url(#gold)" stroke="#6a4610"/>' for px, py in
           [(x + 8, y + 8), (x + w - 8, y + 8), (x + 8, y + h - 8), (x + w - 8, y + h - 8)])}
  <rect x="{_f(ix)}" y="{_f(iy)}" width="{_f(iw)}" height="{_f(ih)}" fill="#2a2a24"/>
  <rect x="{_f(ix)}" y="{_f(iy)}" width="{_f(iw)}" height="{_f(ih * .6)}" fill="#3a3a30"/>
  <path d="M{_f(ix + iw * .38)} {_f(iy + ih * .58)}v-34a{_f(iw * .12)} {_f(iw * .12)} 0 0 1 {_f(iw * .24)} 0v34z" fill="#5a6a7a" opacity=".55"/>
  <rect x="{_f(ix)}" y="{_f(iy + ih * .6)}" width="{_f(iw)}" height="{_f(ih * .4)}" fill="#3b2c1e"/>
  {"".join(scholars)}
  <rect x="{_f(ix)}" y="{_f(iy)}" width="{_f(iw)}" height="{_f(ih)}" fill="url(#vignette)" opacity=".6"/>
  <rect x="{_f(ix)}" y="{_f(iy)}" width="{_f(iw)}" height="{_f(ih)}" filter="url(#grit)" fill="#000" opacity=".12"/>
</g>"""


def clock_face(cx: float, cy: float, r: float, roman: bool = True) -> str:
    ticks = []
    for i in range(60):
        a = math.radians(i * 6)
        r1 = r * (.86 if i % 5 else .8)
        ticks.append(f'<path d="M{_f(cx + r1 * math.sin(a))} {_f(cy - r1 * math.cos(a))}L{_f(cx + r * .92 * math.sin(a))} '
                     f'{_f(cy - r * .92 * math.cos(a))}" stroke="#3a2a14" stroke-width="{1.4 if i % 5 == 0 else .6}"/>')
    nums = ""
    if roman:
        for i, n in enumerate(["XII", "I", "II", "III", "IIII", "V", "VI", "VII", "VIII", "IX", "X", "XI"]):
            a = math.radians(i * 30)
            nums += (f'<text x="{_f(cx + r * .64 * math.sin(a))}" y="{_f(cy - r * .64 * math.cos(a) + r * .07)}" '
                     f'font-family="{SERIF}" font-size="{_f(r * .19)}" text-anchor="middle" fill="#2a1c0c">{n}</text>')
    hour_a, min_a = 277.5, 90  # 9:15
    return f"""<g>
  <circle cx="{_f(cx)}" cy="{_f(cy)}" r="{_f(r * 1.12)}" fill="url(#gold)"/>
  <circle cx="{_f(cx)}" cy="{_f(cy)}" r="{_f(r * 1.04)}" fill="none" stroke="#6a4610" stroke-width="{_f(r * .04)}"/>
  <circle cx="{_f(cx)}" cy="{_f(cy)}" r="{_f(r)}" fill="url(#enamel)"/>
  {"".join(ticks)}{nums}
  <g stroke="#1e140a" stroke-linecap="round">
    <path d="M{_f(cx)} {_f(cy + r * .12)}V{_f(cy - r * .5)}" stroke-width="{_f(r * .08)}" transform="rotate({hour_a} {_f(cx)} {_f(cy)})"/>
    <path d="M{_f(cx)} {_f(cy + r * .15)}V{_f(cy - r * .78)}" stroke-width="{_f(r * .045)}" transform="rotate({min_a} {_f(cx)} {_f(cy)})"/>
  </g>
  <circle cx="{_f(cx)}" cy="{_f(cy)}" r="{_f(r * .07)}" fill="url(#gold)" stroke="#1e140a"/>
  <ellipse cx="{_f(cx - r * .35)}" cy="{_f(cy - r * .45)}" rx="{_f(r * .45)}" ry="{_f(r * .2)}" fill="#fff" opacity=".18" transform="rotate(-30 {_f(cx)} {_f(cy)})"/>
</g>"""


def grandfather_clock(cx: float = 757) -> str:
    return f"""<g>
  <ellipse cx="{cx}" cy="366" rx="58" ry="8" fill="#000" opacity=".6" filter="url(#softShadow)"/>
  <path d="M{cx - 44} 364v-18h88v18z" fill="url(#woodL)" filter="url(#grain)"/>
  <path d="M{cx - 36} 346v-170h72v170z" fill="url(#woodD)" filter="url(#grain)"/>
  <rect x="{cx - 24}" y="190" width="48" height="140" rx="22" fill="#0d0703" stroke="url(#gold)" stroke-width="2"/>
  <rect x="{cx - 24}" y="190" width="48" height="140" rx="22" fill="#9fb7ee" opacity=".06"/>
  <path d="M{cx} 194V300" stroke="url(#goldV)" stroke-width="2.5"/>
  <circle cx="{cx}" cy="305" r="13" fill="url(#gold)"/><circle cx="{cx - 4}" cy="301" r="4" fill="#fff" opacity=".45"/>
  <path d="M{cx - 44} 176h88v-112h-88z" fill="url(#woodL)" filter="url(#grain)"/>
  <path d="M{cx - 50} 66l14-24h18l12 14 12-14h18l14 24z" fill="url(#woodD)" filter="url(#grain)"/>
  <circle cx="{cx}" cy="44" r="6" fill="url(#gold)"/><path d="M{cx} 38v-10" stroke="url(#goldV)" stroke-width="3"/>
  {clock_face(cx, 120, 34)}
  <path d="M{cx - 30} 170h60" stroke="url(#gold)" stroke-width="3"/>
  <rect x="{cx - 20}" y="334" width="40" height="7" fill="url(#gold)" opacity=".9"/>
</g>"""


def desk(drawer_open: bool, lantern_taken: bool, revealed: bool, animate: bool = True) -> str:
    x0, x1, top = 832, 1012, 282
    drawer_y = 296 + (12 if drawer_open else 0)
    inside = ""
    if drawer_open:
        inside = f'<rect x="{x0 + 52}" y="296" width="76" height="12" fill="#070402"/>'
        if not lantern_taken:
            inside += (glow(x0 + 90, 300, 46, "glowViolet", animate, ".8;1;.85;1;.8", 3) +
                       f'<path d="M{x0 + 84} 306v-10h12v10z" fill="url(#goldV)"/><circle cx="{x0 + 90}" cy="301" r="3.5" fill="#e6d8ff"/>')
    reveal = ""
    if revealed:
        reveal = (glow(x0 + 70, top + 2, 60, "glowMoon", animate, ".6;.9;.6", 4) +
                  f'<g fill="#e6f0ff" filter="url(#bloom)" opacity=".95" font-family="{SERIF}" font-style="italic" font-size="7.5">'
                  f'<text x="{(x0 + x1) / 2 - 20}" y="{top + 8}" text-anchor="middle">The seal begins with 47</text></g>')
    return f"""<g>
  <ellipse cx="{(x0 + x1) / 2}" cy="368" rx="105" ry="9" fill="#000" opacity=".6" filter="url(#softShadow)"/>
  <path d="M{x0 + 10} 296c-6 22 6 40-2 68h12c-6-28 4-46 0-68z" fill="url(#woodD)"/>
  <path d="M{x1 - 22} 296c-6 22 6 40-2 68h12c-6-28 4-46 0-68z" fill="url(#woodD)"/>
  <rect x="{x0 + 4}" y="292" width="{x1 - x0 - 8}" height="30" fill="url(#woodD)" filter="url(#grain)"/>
  {inside}
  <g>
    <rect x="{x0 + 50}" y="{drawer_y}" width="80" height="22" rx="2" fill="url(#woodL)" filter="url(#grain)" stroke="#1a0e05"/>
    {"".join(f'<circle cx="{x0 + 74 + i * 16}" cy="{drawer_y + 11}" r="5" fill="url(#gold)" stroke="#5a3a10"/>'
             f'<path d="M{x0 + 74 + i * 16} {drawer_y + 7}v3" stroke="#2a1a08" stroke-width="1.2"/>' for i in range(3))}
  </g>
  <path d="M{x0 - 6} {top}h{x1 - x0 + 12}l-6 10h-{x1 - x0}z" fill="url(#woodTop)" filter="url(#grain)"/>
  <path d="M{x0 - 6} {top}h{x1 - x0 + 12}" stroke="#c99a5e" stroke-opacity=".5"/>
  {reveal}
  <!-- open book, parchment, inkwell and quill -->
  <path d="M{x0 + 20} {top - 1}l26-6 26 6-26 3z" fill="#e9dcb8" stroke="#7a6440" stroke-width=".8"/>
  <path d="M{x0 + 46} {top - 7}v9" stroke="#7a6440" stroke-width=".8"/>
  <path d="M{x0 + 88} {top - 1}l30-4 6 3-30 4z" fill="url(#parch)" stroke="#8a7550" stroke-width=".8"/>
  <path d="M{x0 + 132} {top}v-9h10v9z" fill="#14181f"/><path d="M{x0 + 137} {top - 9}l14-30" stroke="#e8e0d0" stroke-width="2"/>
  <path d="M{x0 + 141} {top - 18}q9-16 12-22q-2 12-10 24z" fill="#e8e0d0" opacity=".9"/>
  <!-- candle -->
  {glow(x1 - 24, top - 34, 70, "glowWarm", animate)}
  <ellipse cx="{x1 - 24}" cy="{top - 1}" rx="13" ry="3.5" fill="url(#gold)"/>
  <rect x="{x1 - 30}" y="{top - 30}" width="12" height="29" rx="2" fill="#efe6cc"/>
  <path d="M{x1 - 30} {top - 27}q2 8 1 12M{x1 - 19} {top - 25}q-2 6 0 10" stroke="#fff8e8" stroke-width="2" fill="none"/>
  {flame(x1 - 24, top - 31, .62, animate, .7)}
</g>"""


def window(animate: bool = True) -> str:
    x, y, w, h = 612, 34, 86, 120
    cx = x + w / 2
    stars = ""
    rnd = random.Random(5)
    for i in range(14):
        sx, sy = rnd.uniform(x + 6, x + w - 6), rnd.uniform(y + 10, y + h - 20)
        dur = rnd.uniform(2, 5)
        anim = (f'<animate attributeName="opacity" values="1;.2;1" dur="{dur:.1f}s" repeatCount="indefinite"/>'
                if animate else "")
        stars += f'<circle cx="{_f(sx)}" cy="{_f(sy)}" r="{_f(rnd.uniform(.6, 1.5))}" fill="#fff">{anim}</circle>'
    arch = f"M{x} {y + h}V{y + 44}a{w / 2} {w / 2} 0 0 1 {w} 0V{y + h}z"
    return f"""<g>
  <path d="{arch}" fill="#0f0a07" stroke="#3a2c22" stroke-width="16" stroke-linejoin="round"/>
  <clipPath id="winClip"><path d="{arch}"/></clipPath>
  <g clip-path="url(#winClip)">
    <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#night)"/>
    {stars}
    {glow(x + w * .68, y + 36, 30, "glowMoon", False)}
    <circle cx="{_f(x + w * .68)}" cy="{y + 36}" r="11" fill="#f3efd6"/>
    <circle cx="{_f(x + w * .68 + 5)}" cy="{y + 32}" r="10" fill="#26345a"/>
    <path d="M{x} {y + 92}q20-8 34 0t40-4 20 2v40h-94z" fill="#0b1020" opacity=".9"/>
  </g>
  <g stroke="#2a1d14" stroke-width="5" fill="none">
    <path d="{arch}"/><path d="M{cx} {y + 2}V{y + h}M{x} {y + 70}H{x + w}"/>
    <circle cx="{cx}" cy="{y + 40}" r="13"/>
  </g>
  <path d="M{x - 10} {y + h + 2}h{w + 20}v8h-{w + 20}z" fill="#3a2c22"/>
</g>"""


def moonbeam(animate: bool = True) -> str:
    motes = ""
    rnd = random.Random(11)
    for i in range(16):
        mx, my = rnd.uniform(560, 760), rnd.uniform(170, 350)
        d = rnd.uniform(6, 12)
        anim = (f'<animateTransform attributeName="transform" type="translate" values="0 0;{rnd.uniform(-12, 12):.0f} '
                f'{rnd.uniform(-30, -10):.0f};0 0" dur="{d:.1f}s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values=".1;.8;.1" dur="{d:.1f}s" repeatCount="indefinite"/>') if animate else ""
        motes += f'<circle cx="{_f(mx)}" cy="{_f(my)}" r="{_f(rnd.uniform(.7, 1.8))}" fill="#fff8e0" opacity=".5">{anim}</circle>'
    return f"""<g style="mix-blend-mode:screen">
  <polygon points="614,156 698,156 820,372 480,372" fill="url(#beam)" filter="url(#blur5)"/>
  <polygon points="640,156 660,156 700,372 600,372" fill="url(#beam)" opacity=".7"/>
  <ellipse cx="650" cy="380" rx="170" ry="16" fill="#c7d8ff" opacity=".07"/>
  {motes}
</g>"""


def rug() -> str:
    cx, cy = 600, 398
    fringe = "".join(f'<path d="M{_f(cx + 205 * math.cos(math.radians(a)))} {_f(cy + 26 * math.sin(math.radians(a)))}l'
                     f'{_f(6 * math.cos(math.radians(a)))} {_f(3 * math.sin(math.radians(a)))}" stroke="#c9b48a" stroke-width="1" opacity=".6"/>'
                     for a in range(0, 360, 6))
    return f"""<g>
  {fringe}
  <ellipse cx="{cx}" cy="{cy}" rx="205" ry="26" fill="url(#rug)"/>
  <ellipse cx="{cx}" cy="{cy}" rx="190" ry="21" fill="none" stroke="#c9973a" stroke-width="2" opacity=".8"/>
  <ellipse cx="{cx}" cy="{cy}" rx="176" ry="17" fill="none" stroke="#2a0a0c" stroke-width="5" stroke-dasharray="3 5"/>
  <ellipse cx="{cx}" cy="{cy}" rx="70" ry="8" fill="#3a0e11" stroke="#c9973a" stroke-width="1.2"/>
  <path d="M{cx - 40} {cy}l40 -6 40 6 -40 6z" fill="#7a2328" stroke="#c9973a" stroke-width="1"/>
  <ellipse cx="{cx}" cy="{cy}" rx="205" ry="26" filter="url(#grit)" fill="#000" opacity=".15"/>
</g>"""


def floor(x: float = 0, w: float = 1200, y: float = 362, h: float = 78) -> str:
    rnd = random.Random(3)
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#floor)"/>']
    vx = x + w / 2
    for i in range(-9, 10):
        bx = vx + i * 120
        out.append(f'<path d="M{_f(vx + i * 52)} {y}L{_f(bx)} {y + h}" stroke="#0a0604" stroke-width="2" opacity=".8"/>')
    for k, yy in enumerate([y + 14, y + 34, y + 60]):
        out.append(f'<path d="M{x} {yy}H{x + w}" stroke="#0a0604" stroke-width="{1.5 + k}" opacity=".8"/>')
    for _ in range(18):
        sx, sy = rnd.uniform(x, x + w), rnd.uniform(y + 4, y + h - 4)
        out.append(f'<ellipse cx="{_f(sx)}" cy="{_f(sy)}" rx="{_f(rnd.uniform(10, 40))}" ry="{_f(rnd.uniform(2, 5))}" '
                   f'fill="#000" opacity="{rnd.uniform(.1, .25):.2f}"/>')
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" filter="url(#stoneTex)" opacity=".4" style="mix-blend-mode:multiply"/>')
    out.append(f'<rect x="{x}" y="{y - 4}" width="{w}" height="8" fill="#0b0705"/>')
    return f'<g>{"".join(out)}</g>'


def door(open_: bool, animate: bool = True) -> str:
    cx, base, half, spring = 1134, 362, 54, 180   # spring = y where the arch starts
    r = half
    # voussoir stones of the stone arch
    stones = []
    n = 11
    for i in range(n):
        a0 = math.pi + math.pi * i / n
        a1 = math.pi + math.pi * (i + 1) / n
        ri, ro = r + 6, r + 30
        pts = [(cx + ri * math.cos(a0), spring + ri * math.sin(a0)), (cx + ro * math.cos(a0), spring + ro * math.sin(a0)),
               (cx + ro * math.cos(a1), spring + ro * math.sin(a1)), (cx + ri * math.cos(a1), spring + ri * math.sin(a1))]
        shade = 50 + (i % 3) * 6
        col = f"#{shade:02x}{int(shade * .8):02x}{int(shade * .66):02x}"
        stones.append(f'<polygon points="{" ".join(f"{_f(px)},{_f(py)}" for px, py in pts)}" fill="{col}" stroke="#120c08" stroke-width="2"/>')
    runes = "ᚱᚢᚾᛖᛟᚦᛉᚨᛗ"
    rune_marks = ""
    for i, ch in enumerate(runes):
        a = math.pi + math.pi * (i + 1) / (len(runes) + 1)
        rx, ry = cx + (r + 18) * math.cos(a), spring + (r + 18) * math.sin(a) + 4
        anim = (f'<animate attributeName="opacity" values=".35;1;.35" dur="3s" begin="{i * .25:.2f}s" repeatCount="indefinite"/>'
                if animate and not open_ else "")
        rune_marks += (f'<text x="{_f(rx)}" y="{_f(ry)}" font-family="{SERIF}" font-size="11" text-anchor="middle" '
                       f'fill="{"#7ef0ff" if not open_ else "#3a6a78"}" opacity=".8">{ch}{anim}</text>')
    jamb = (f'<rect x="{cx - r - 30}" y="{spring}" width="24" height="{base - spring}" fill="#3a2c22" stroke="#120c08" stroke-width="2"/>'
            f'<rect x="{cx + r + 6}" y="{spring}" width="24" height="{base - spring}" fill="#3a2c22" stroke="#120c08" stroke-width="2"/>')
    opening = f"M{cx - r} {base}V{spring}a{r} {r} 0 0 1 {2 * r} 0V{base}z"

    if not open_:
        step = 2 * r / 4
        planks = "".join(f'<path d="M{_f(cx - r + k * step)} {_f(spring - math.sqrt(max(r * r - (k * step - r) ** 2, 0)))}V{base}" '
                         f'stroke="#2a1a0c" stroke-width="2"/>' for k in range(1, 4))
        straps = "".join(
            f'<g><rect x="{cx - r}" y="{yy}" width="{2 * r}" height="11" fill="url(#iron)"/>'
            f'<path d="M{cx - r + 4} {yy + 5}c-10 0-12 -12 -4 -14M{cx + r - 4} {yy + 5}c10 0 12 -12 4 -14" stroke="url(#iron)" stroke-width="3" fill="none"/>'
            + "".join(f'<circle cx="{_f(cx - r + 8 + s * (2 * r - 16) / 6)}" cy="{yy + 5.5}" r="2.2" fill="#9a948c"/>' for s in range(7))
            + "</g>" for yy in (spring + 10, base - 50))
        lock_anim = '<animate attributeName="opacity" values=".55;.95;.55" dur="2.4s" repeatCount="indefinite"/>' if animate else ""
        panel = f"""
  <path d="{opening}" fill="url(#woodL)" filter="url(#grain)"/>
  {planks}{straps}
  <g>{glow(cx, 264, 44, "glowCyan", animate, ".5;.9;.5", 2.4)}</g>
  <rect x="{cx - 30}" y="250" width="60" height="28" rx="5" fill="#1b140e" stroke="url(#gold)" stroke-width="2.5"/>
  {"".join(f'<circle cx="{cx - 21 + i * 14}" cy="264" r="5.2" fill="#0d1a1f" stroke="#7ef0ff" stroke-width="1.2">{lock_anim}</circle>' for i in range(4))}
  <circle cx="{cx + 34}" cy="304" r="7" fill="none" stroke="url(#gold)" stroke-width="3.2"/>
  <circle cx="{cx + 34}" cy="297" r="3" fill="url(#gold)"/>"""
        spill = ""
    else:
        panel = f"""
  <clipPath id="doorOpen"><path d="{opening}"/></clipPath>
  <g clip-path="url(#doorOpen)">
    <rect x="{cx - r}" y="{spring - r}" width="{2 * r}" height="{base - spring + r}" fill="url(#night)"/>
    {"".join(f'<circle cx="{cx - r + 8 + (i * 37) % (2 * r - 12)}" cy="{spring - r + 10 + (i * 23) % 90}" r="1" fill="#fff"/>' for i in range(12))}
    <path d="M{cx - r} {base - 40}q40 -18 70 -6t60 -4v60h-130z" fill="#0b1020"/>
    <path d="M{cx - 18} {base}l10 -38h16l14 38z" fill="#8a9cc8" opacity=".35"/>
    {glow(cx, spring + 10, 70, "glowMoon", animate, ".5;.8;.5", 5)}
  </g>
  <path d="M{cx - r} {base}V{spring}q10 -40 18 -50V{base + 6}z" fill="url(#woodD)" filter="url(#grain)"/>
  <path d="M{cx - r + 4} {spring + 20}h12M{cx - r + 4} {base - 46}h12" stroke="url(#iron)" stroke-width="7"/>"""
        spill = f'<polygon points="{cx - r},{base} {cx + r},{base} {cx + 140},{base + 78} {cx - 210},{base + 78}" fill="#b8c8f0" opacity=".12" filter="url(#blur12)"/>'
    return f"""<g>
  <rect x="{cx - r - 40}" y="{spring - r - 40}" width="{2 * r + 80}" height="{base - spring + r + 40}" fill="#000" opacity=".35" filter="url(#softShadow)"/>
  {"".join(stones)}{jamb}
  {panel}
  {rune_marks}
  <path d="M{cx - r - 34} {base}h{2 * r + 68}v6h-{2 * r + 68}z" fill="#2a2019"/>
  {spill}
</g>"""


def ceiling(animate: bool = True) -> str:
    chain = "".join(f'<ellipse cx="470" cy="{6 + k * 7}" rx="2.4" ry="3.6" fill="none" stroke="#3a342e" stroke-width="1.6"/>'
                    for k in range(7))
    return f"""<g>
  <rect x="0" y="0" width="1200" height="26" fill="#120b06"/>
  <rect x="0" y="22" width="1200" height="8" fill="#2a190c"/>
  {"".join(f'<rect x="{bx}" y="0" width="34" height="34" fill="#1a1009"/><rect x="{bx}" y="30" width="34" height="5" fill="#000" opacity=".5"/>' for bx in range(40, 1200, 230))}
  {chain}
  <g transform="translate(470 58)">
    <path d="M-34 0h68l-10 10h-48z" fill="#2a2420"/><path d="M-30 0q30 -16 60 0" stroke="#2a2420" stroke-width="2.5" fill="none"/>
    {"".join(f'<rect x="{dx - 2.5}" y="-12" width="5" height="12" fill="#cfc4a8"/>' for dx in (-26, -9, 9, 26))}
  </g>
</g>"""


def foreground(animate: bool = True) -> str:
    """Dark silhouettes in front of the scene for depth."""
    return f"""<g filter="url(#blur2)">
  <path d="M0 440V392h40l6-10h70l4 12h30v46z" fill="#0b0704"/>
  <path d="M46 382h70M0 392h40M120 394h30" stroke="#8a5a2a" stroke-opacity=".55" stroke-width="2"/>
  <path d="M8 392h30M122 394h28" stroke="#3a2614" stroke-width="1.5"/>
  <rect x="132" y="372" width="10" height="22" fill="#2a2418"/>
</g>
{glow(137, 362, 34, "glowWarm", animate, ".6;.9;.6", 1.8)}
{flame(137, 371, .45, animate, .6)}"""


def lighting(animate: bool = True) -> str:
    return f"""<g style="mix-blend-mode:screen">
  {glow(365, 140, 170, "glowWarm", animate, ".75;.95;.7;.9;.75", 2.6)}
  {glow(1036, 152, 150, "glowWarm", animate, ".7;.9;.75;.95;.7", 3.1)}
</g>"""


# ---------------------------------------------------------------------------
# The full scene
# ---------------------------------------------------------------------------

@lru_cache(maxsize=32)
def scene(drawer_open: bool = False, lantern_taken: bool = False, message_revealed: bool = False,
          door_open: bool = False, animate: bool = True) -> str:
    return _svg(1200, 440, _scene_body(drawer_open, lantern_taken, message_revealed, door_open, animate) +
                '<rect width="1200" height="440" fill="url(#vignette)"/>')


def _scene_body(drawer_open: bool = False, lantern_taken: bool = False, message_revealed: bool = False,
                door_open: bool = False, animate: bool = True, numerals: bool = False) -> str:
    return f"""
{stone_wall(0, 26, 1200, 340)}
{ceiling(animate)}
{floor()}
{rug()}
{bookshelf(numerals)}
{sconce(365, 150, animate)}
{painting()}
{window(animate)}
{moonbeam(animate)}
{grandfather_clock()}
{sconce(1036, 160, animate)}
{desk(drawer_open, lantern_taken, message_revealed, animate)}
{door(door_open, animate)}
{lighting(animate)}
{foreground(animate)}
"""


# ---------------------------------------------------------------------------
# Close-up illustration cards (shown inside the Dungeon Master's messages)
# ---------------------------------------------------------------------------

CARD_W, CARD_H = 640, 260


def _card(body: str) -> str:
    return _svg(CARD_W, CARD_H, body + f'<rect width="{CARD_W}" height="{CARD_H}" fill="url(#vignette)" opacity=".85"/>')


def _crop(region: tuple[float, float, float, float], **state) -> str:
    """A close-up made by zooming into the full scene."""
    x, y, w, h = region
    body = _scene_body(**state)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{_f(x)} {_f(y)} {_f(w)} {_f(h)}" width="{CARD_W}" '
            f'height="{CARD_H}" preserveAspectRatio="xMidYMid slice">{DEFS}{body}'
            f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" fill="url(#vignette)" opacity=".75"/></svg>')


def _backdrop(seed: int = 31) -> str:
    return stone_wall(0, 0, CARD_W, CARD_H, seed=seed, row_h=44)


def _card_clock() -> str:
    plate = f"""
<g>
  <rect x="356" y="78" width="250" height="104" rx="8" fill="url(#gold)" stroke="#5a3a10" stroke-width="2"/>
  <rect x="364" y="86" width="234" height="88" rx="5" fill="none" stroke="#6a4610" stroke-width="1.5"/>
  {"".join(f'<circle cx="{px}" cy="{py}" r="3.5" fill="#6a4610"/>' for px, py in [(372, 94), (590, 94), (372, 166), (590, 166)])}
  <text x="481" y="124" font-family="{SERIF}" font-style="italic" font-size="21" text-anchor="middle" fill="#3a2508">When light fails,</text>
  <text x="481" y="152" font-family="{SERIF}" font-style="italic" font-size="21" text-anchor="middle" fill="#3a2508">time holds the end.</text>
</g>"""
    return _card(f"""{_backdrop(41)}
<rect x="0" y="0" width="{CARD_W}" height="{CARD_H}" fill="#1a0f07" opacity=".35"/>
<circle cx="190" cy="130" r="150" fill="url(#glowWarm)" opacity=".5"/>
<rect x="60" y="-10" width="260" height="290" fill="url(#woodD)" filter="url(#grain)"/>
{clock_face(190, 128, 98)}
<path d="M300 -10V270" stroke="url(#goldV)" stroke-width="4"/>
{plate}""")


def _card_rune_lock(animate: bool = True) -> str:
    dials = ""
    for i, ch in enumerate("ᚱᚢᚾᛖ"):
        cx = 216 + i * 70
        anim = (f'<animate attributeName="opacity" values=".6;1;.6" dur="2.6s" begin="{i * .3:.1f}s" repeatCount="indefinite"/>'
                if animate else "")
        dials += f"""
<g>
  {glow(cx, 132, 46, "glowCyan", animate, ".4;.8;.4", 2.6)}
  <circle cx="{cx}" cy="132" r="28" fill="#0d1a1f" stroke="url(#gold)" stroke-width="4"/>
  <circle cx="{cx}" cy="132" r="21" fill="none" stroke="#7ef0ff" stroke-opacity=".5" stroke-dasharray="2 4"/>
  <text x="{cx}" y="142" font-family="{SERIF}" font-size="28" text-anchor="middle" fill="#9ff6ff" filter="url(#bloom)">{ch}{anim}</text>
</g>"""
    return _card(f"""
<rect width="{CARD_W}" height="{CARD_H}" fill="url(#woodL)" filter="url(#grain)"/>
{"".join(f'<path d="M{x} 0V{CARD_H}" stroke="#2a1a0c" stroke-width="4"/>' for x in (120, 250, 390, 520))}
{"".join(f'<rect x="0" y="{y}" width="{CARD_W}" height="26" fill="url(#iron)"/>' + "".join(f'<circle cx="{18 + k * 40}" cy="{y + 13}" r="5" fill="#9a948c"/>' for k in range(16)) for y in (14, 222))}
<rect x="160" y="78" width="320" height="108" rx="12" fill="#1b140e" stroke="url(#gold)" stroke-width="6"/>
<rect x="172" y="90" width="296" height="84" rx="8" fill="none" stroke="#6a4610" stroke-width="2"/>
{dials}""")


def _card_note() -> str:
    return _card(f"""{_backdrop(52)}
<rect width="{CARD_W}" height="{CARD_H}" fill="url(#woodTop)" filter="url(#grain)" opacity=".92"/>
<circle cx="560" cy="40" r="160" fill="url(#glowWarm)" opacity=".7"/>
<g transform="rotate(-4 320 130)">
  <path d="M150 52l300-10 14 22-6 18 10 20-8 22 8 26-10 20 6 26-310 10-6-24 8-18-8-22 6-24-10-22 8-20z" fill="#000" opacity=".4" filter="url(#softShadow)" transform="translate(6 8)"/>
  <path d="M150 52l300-10 14 22-6 18 10 20-8 22 8 26-10 20 6 26-310 10-6-24 8-18-8-22 6-24-10-22 8-20z" fill="url(#parch)"/>
  <path d="M150 52l300-10 14 22-6 18 10 20-8 22 8 26-10 20 6 26-310 10-6-24 8-18-8-22 6-24-10-22 8-20z" fill="#000" opacity=".1" filter="url(#grit)"/>
  <text x="310" y="122" font-family="{SERIF}" font-style="italic" font-size="30" text-anchor="middle" fill="#3a2410">Order matters.</text>
  <text x="310" y="162" font-family="{SERIF}" font-style="italic" font-size="30" text-anchor="middle" fill="#3a2410">Ask the painting.</text>
  <circle cx="430" cy="196" r="18" fill="#8f1b1b"/><circle cx="430" cy="196" r="11" fill="none" stroke="#5a0a0a" stroke-width="2"/>
</g>""")


def _card_lantern(animate: bool = True) -> str:
    return _card(f"""
<rect width="{CARD_W}" height="{CARD_H}" fill="#1a0e18"/>
<path d="M0 260C120 200 200 230 320 190S540 210 640 170V260z" fill="#3a1438"/>
<path d="M0 260C140 220 220 250 340 215S560 235 640 205V260z" fill="#2a0e28"/>
{glow(320, 120, 170, "glowViolet", animate, ".75;1;.8;1;.75", 3)}
<g transform="translate(320 128) scale(1.6)">
  <path d="M-12 -70a12 12 0 0 1 24 0" fill="none" stroke="url(#goldV)" stroke-width="4"/>
  <path d="M-20 -60h40l-6 10h-28z" fill="url(#goldV)"/>
  <rect x="-18" y="-50" width="36" height="52" rx="4" fill="#cdbfff" fill-opacity=".22" stroke="url(#goldV)" stroke-width="4"/>
  <path d="M0 -50v52M-18 -24h36" stroke="url(#goldV)" stroke-width="2" opacity=".6"/>
  <path d="M0 -38l10 14-10 14-10-14z" fill="#f2ecff" stroke="#fff" stroke-width="1" filter="url(#bloom)"/>
  <path d="M-22 2h44l-4 12h-36z" fill="url(#goldV)"/>
</g>""")


def _card_rug() -> str:
    return _card(f"""
<rect width="{CARD_W}" height="{CARD_H}" fill="url(#floor)"/>
{floor(0, CARD_W, 0, CARD_H)}
<path d="M-20 260L120 40H700V260z" fill="url(#rug)"/>
<path d="M10 260L140 60H700" fill="none" stroke="#c9973a" stroke-width="5"/>
<path d="M40 260L158 80H700" fill="none" stroke="#2a0a0c" stroke-width="9" stroke-dasharray="6 10"/>
<path d="M420 40L640 40V200C560 160 480 120 420 40z" fill="#000" opacity=".5" filter="url(#softShadow)"/>
<path d="M440 40H640V170C560 150 500 110 440 40z" fill="#6a4a36" stroke="#c9973a" stroke-width="3"/>
<path d="M440 40H640V170C560 150 500 110 440 40z" fill="none" stroke="#3a2418" stroke-width="1" stroke-dasharray="1 5"/>
{"".join(f'<path d="M{455 + k * 18} 46Q{520 + k * 12} {90 + k * 6} 640 {60 + k * 11}" stroke="#4a3022" stroke-width="1" fill="none"/>' for k in range(8))}
<path d="M440 40C500 110 560 150 640 170" fill="none" stroke="#e8d7b0" stroke-width="2" opacity=".5"/>
<rect width="{CARD_W}" height="{CARD_H}" filter="url(#grit)" fill="#000" opacity=".12"/>
<g transform="translate(560 214)">
  <ellipse rx="7" ry="5.5" fill="#0b0705"/><circle cx="7" r="3.5" fill="#0b0705"/>
  <g stroke="#0b0705" stroke-width="1.6" fill="none">
    <path d="M-3 -3l-8 -8-4 4M0 -4l-2 -12-6 -2M3 -4l6 -10 6 0M5 -2l10 -6 4 4"/>
    <path d="M-3 3l-8 8-4 -4M0 4l-2 12-6 2M3 4l6 10 6 0M5 2l10 6 4 -4"/>
  </g>
</g>""")


def _card_bookshelf_numerals() -> str:
    rnd = random.Random(8)
    row = _books_row(10, 310, 112, 82, rnd, {110: ("#2f7a46", "2"), 152: ("#a8302b", "5"), 194: ("#2c5aa6", "8")}, True)
    return _card(f"""
<rect width="{CARD_W}" height="{CARD_H}" fill="#140b05"/>
<g transform="scale(2.08) translate(0 4)">
  <rect x="0" y="0" width="320" height="130" fill="#140b05"/>
  {row}
  <rect x="0" y="112" width="320" height="10" fill="url(#woodTop)" filter="url(#grain)"/>
  <rect x="0" y="0" width="320" height="8" fill="url(#woodTop)" filter="url(#grain)"/>
</g>
<circle cx="320" cy="60" r="220" fill="url(#glowWarm)" opacity=".35" style="mix-blend-mode:screen"/>""")


def _card_door_open(animate: bool = True) -> str:
    rnd = random.Random(17)
    stars = "".join(
        f'<circle cx="{_f(rnd.uniform(200, 440))}" cy="{_f(rnd.uniform(20, 150))}" r="{_f(rnd.uniform(.6, 1.6))}" fill="#fff">'
        + (f'<animate attributeName="opacity" values="1;.25;1" dur="{rnd.uniform(2, 5):.1f}s" repeatCount="indefinite"/>' if animate else "")
        + "</circle>" for _ in range(40))
    arch = "M200 260V120a120 120 0 0 1 240 0V260z"
    return _card(f"""{_backdrop(63)}
<clipPath id="openArch"><path d="{arch}"/></clipPath>
<g clip-path="url(#openArch)">
  <rect x="200" y="0" width="240" height="260" fill="url(#night)"/>
  {stars}
  {glow(370, 70, 60, "glowMoon", False)}
  <circle cx="370" cy="70" r="20" fill="#f3efd6"/><circle cx="379" cy="63" r="18" fill="#26345a"/>
  <path d="M200 200q60 -34 120 -12t120 -10v82h-240z" fill="#101a33"/>
  <path d="M200 222q80 -20 140 -4t100 -6v48h-240z" fill="#0a1022"/>
  <path d="M300 260l12 -54h16l12 54z" fill="#9fb2dd" opacity=".35"/>
  {"".join(f'<path d="M{x} {y}l6 -22 6 22z" fill="#060a16"/>' for x, y in [(214, 214), (228, 220), (404, 208), (420, 214)])}
</g>
<path d="{arch}" fill="none" stroke="#3a2c22" stroke-width="22"/>
<path d="{arch}" fill="none" stroke="#120c08" stroke-width="2"/>
<path d="M200 260V120q-14 -30 -30 -40V260z" fill="url(#woodD)" filter="url(#grain)"/>
<path d="M172 120h26M172 220h26" stroke="url(#iron)" stroke-width="9"/>
<polygon points="200,260 440,260 560,260 90,260" fill="#b8c8f0" opacity=".2"/>
{glow(320, 250, 160, "glowMoon", animate, ".35;.55;.35", 5)}
{"".join(f'<text x="{_f(320 + 136 * math.cos(math.pi + math.pi * (i + 1) / 8))}" y="{_f(124 + 136 * math.sin(math.pi + math.pi * (i + 1) / 8) + 5)}" font-family="{SERIF}" font-size="14" text-anchor="middle" fill="#3a6a78">{ch}</text>' for i, ch in enumerate("ᚱᚢᚾᛖᛟᚦᛉ"))}""")


@lru_cache(maxsize=None)
def card(name: str, animate: bool = True) -> str:
    """Close-up illustration by name. Unknown names raise KeyError."""
    crops = {
        "painting": ((290, 84, 394, 160), {}),
        "desk": ((750, 228, 345, 140), {}),
        "drawer_open": ((790, 236, 280, 114), {"drawer_open": True}),
        "reveal": ((800, 232, 260, 106), {"drawer_open": True, "lantern_taken": True, "message_revealed": True}),
        "window": ((560, 26, 330, 134), {}),
        "sconces": ((292, 104, 196, 80), {}),
        "bookshelf": ((40, 40, 300, 122), {}),
    }
    custom = {
        "bookshelf_close": _card_bookshelf_numerals,
        "clock": _card_clock,
        "door": lambda: _card_rune_lock(animate),
        "note": _card_note,
        "lantern": lambda: _card_lantern(animate),
        "rug": _card_rug,
        "door_open": lambda: _card_door_open(animate),
    }
    if name in crops:
        region, state = crops[name]
        return _crop(region, animate=animate, **state)
    return custom[name]()


CARDS = ["bookshelf", "bookshelf_close", "painting", "clock", "desk", "drawer_open", "reveal", "lantern", "note",
         "door", "door_open", "window", "sconces", "rug"]
