"""
Shared fantasy ("tabletop RPG") look for both versions of the game.

Everything visual lives here so the game logic stays clean:
- bundled OFL fonts (Cinzel, Cinzel Decorative, IM Fell English), embedded as base64
- parchment / dark-leather CSS for Streamlit's chat and sidebar
- the illustrated room banner, avatars and item icons (original SVG art in ui/assets)
- small HTML builders for the character sheet, dice roll and victory scroll

The apps only call these helpers; nothing here knows the puzzle solutions.
"""

from __future__ import annotations

import base64
import html
from functools import lru_cache
from pathlib import Path

import streamlit as st

UI_DIR = Path(__file__).parent
ASSETS = UI_DIR / "assets"
FONTS = UI_DIR / "fonts"

AVATARS = {
    "assistant": str(ASSETS / "dm.png"),   # the Dungeon Master
    "user": str(ASSETS / "hero.png"),      # the adventurer
}


# ---------------------------------------------------------------------------
# Asset helpers
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def _b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def svg_uri(name: str) -> str:
    """data: URI for an SVG in ui/assets (so it works inside st.markdown HTML)."""
    return f"data:image/svg+xml;base64,{_b64(ASSETS / f'{name}.svg')}"


def icon(name: str, size: int = 28, alt: str = "") -> str:
    return f'<img src="{svg_uri(name)}" width="{size}" height="{size}" alt="{html.escape(alt)}" class="rpg-icon">'


@lru_cache(maxsize=1)
def _font_faces() -> str:
    faces = [
        ("Cinzel Decorative", "cinzel-decorative-latin-700-normal.woff2", 700, "normal"),
        ("Cinzel", "cinzel-latin-400-normal.woff2", 400, "normal"),
        ("Cinzel", "cinzel-latin-700-normal.woff2", 700, "normal"),
        ("IM Fell English", "im-fell-english-latin-400-normal.woff2", 400, "normal"),
        ("IM Fell English", "im-fell-english-latin-400-italic.woff2", 400, "italic"),
    ]
    return "\n".join(
        f"@font-face{{font-family:'{fam}';src:url(data:font/woff2;base64,{_b64(FONTS / f)}) format('woff2');"
        f"font-weight:{w};font-style:{s};font-display:swap;}}"
        for fam, f, w, s in faces
    )


# ---------------------------------------------------------------------------
# Global stylesheet
# ---------------------------------------------------------------------------

CSS = """
:root{
  --ink:#2b1a0e; --ink-soft:#5a3d22; --gold:#d4a64a; --gold-hi:#f6dc8c; --gold-lo:#7a5418;
  --crimson:#8b1e1e; --night:#120c08; --leather:#2a1b10; --parchment:#efe0bb;
  --serif:'IM Fell English', Georgia, 'Times New Roman', serif;
  --caps:'Cinzel', Georgia, serif; --title:'Cinzel Decorative', 'Cinzel', Georgia, serif;
}

/* ---------- page background: torch-lit stone ---------- */
.stApp{
  background:
    radial-gradient(ellipse at 50% -10%, rgba(255,170,60,.16), transparent 55%),
    radial-gradient(ellipse at 50% 120%, rgba(0,0,0,.9), transparent 60%),
    repeating-linear-gradient(0deg, rgba(0,0,0,.25) 0 2px, transparent 2px 46px),
    repeating-linear-gradient(90deg, rgba(0,0,0,.18) 0 2px, transparent 2px 92px),
    linear-gradient(#1d140e, #0e0906);
  color:#e9dcc0;
}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stToolbar"], [data-testid="stDecoration"], footer{display:none !important;}
.block-container{max-width:920px; padding-top:1.4rem; padding-bottom:7rem;}

html, body, .stApp, .stMarkdown, p, li, label, textarea, input{font-family:var(--serif);}
h1,h2,h3,h4{font-family:var(--caps) !important; letter-spacing:.04em;}

/* ---------- banner ---------- */
.rpg-banner{position:relative; border-radius:14px; overflow:hidden; margin-bottom:1.2rem;
  border:2px solid var(--gold-lo); box-shadow:0 0 0 4px #0b0705, 0 0 0 5px var(--gold-lo), 0 18px 40px rgba(0,0,0,.6);}
.rpg-banner img.scene{display:block; width:100%; height:auto;}
.rpg-banner .title{position:absolute; left:0; right:0; bottom:0; padding:2.2rem 1.4rem .9rem;
  background:linear-gradient(transparent, rgba(8,5,3,.92)); text-align:center;}
.rpg-banner h1{font-family:var(--title) !important; color:var(--gold-hi); font-size:2.3rem; margin:0; padding:0;
  text-shadow:0 2px 0 #3a2608, 0 0 18px rgba(255,190,90,.45);}
.rpg-banner .sub{font-family:var(--serif); font-style:italic; color:#d9c7a0; font-size:1.05rem; margin-top:.15rem;}
.rpg-banner .badge{position:absolute; top:12px; right:12px; font-family:var(--caps); font-size:.72rem; letter-spacing:.12em;
  color:var(--gold-hi); background:rgba(10,6,4,.75); border:1px solid var(--gold-lo); padding:.25rem .6rem; border-radius:20px;}

/* ---------- chat messages ---------- */
[data-testid="stChatMessage"]{border-radius:12px; padding:1rem 1.1rem; margin-bottom:.9rem; gap:.9rem;}
[data-testid="stChatMessage"] > img, [data-testid="stChatMessage"] > div:first-child img{
  width:46px !important; height:46px !important; border-radius:50%; box-shadow:0 2px 8px rgba(0,0,0,.5);}
[data-testid="stChatMessage"] > div:first-child:has(img){width:46px !important; height:46px !important;}
[data-testid="stChatMessage"]:has(.dm-mark){
  background:
    radial-gradient(ellipse at 20% 0%, rgba(255,255,255,.35), transparent 60%),
    radial-gradient(ellipse at 100% 100%, rgba(120,80,30,.28), transparent 55%),
    linear-gradient(135deg, #f3e6c4, #e2cc98);
  border:1px solid #a88446; box-shadow:inset 0 0 28px rgba(110,70,20,.35), 0 8px 22px rgba(0,0,0,.45);
}
[data-testid="stChatMessage"]:has(.dm-mark) *{color:var(--ink) !important;}
[data-testid="stChatMessage"]:has(.dm-mark) p{font-size:1.12rem; line-height:1.55;}
[data-testid="stChatMessage"]:has(.dm-mark) .stMarkdown:last-child p:first-child::first-letter{
  font-family:var(--title); float:left; font-size:2.6rem; line-height:.9; padding:.2rem .45rem 0 0; color:var(--crimson) !important;}
[data-testid="stChatMessage"]:has(.hero-mark){
  background:linear-gradient(135deg, #2f2015, #1d130c); border:1px solid #5a3d22;
  box-shadow:0 6px 18px rgba(0,0,0,.45);
}
[data-testid="stChatMessage"]:has(.hero-mark) p{color:#f1e2bf !important; font-style:italic; font-size:1.08rem;}
.dm-mark,.hero-mark{display:none;}
.speaker{font-family:var(--caps) !important; font-size:.72rem; letter-spacing:.16em; text-transform:uppercase; opacity:.7; margin-bottom:.15rem;}

/* dice roll inside a DM message */
.dice-roll{display:flex; align-items:center; gap:.8rem; margin:.1rem 0 .5rem;}
.dice-roll img{animation:roll .9s cubic-bezier(.2,.8,.3,1);}
.dice-roll .num{font-family:var(--title); font-size:2rem; color:var(--crimson) !important; line-height:1;}
.dice-roll .lbl{font-family:var(--caps); font-size:.8rem; letter-spacing:.1em;}
@keyframes roll{from{transform:rotate(-540deg) scale(.4); opacity:0;} to{transform:rotate(0) scale(1); opacity:1;}}

/* ---------- chat input ---------- */
[data-testid="stBottom"], [data-testid="stBottom"] > div{background:transparent !important;}
[data-testid="stBottomBlockContainer"]{background:linear-gradient(transparent, rgba(10,6,4,.95) 35%); max-width:920px;}
[data-testid="stChatInput"]{background:#1f150d !important; border:1px solid var(--gold-lo) !important; border-radius:12px !important;
  box-shadow:0 0 0 1px #000, 0 0 22px rgba(212,166,74,.15);}
[data-testid="stChatInput"] textarea{color:#f3e4c0 !important; font-size:1.08rem !important; caret-color:var(--gold-hi);}
[data-testid="stChatInput"] textarea::placeholder{color:#a58c63 !important; font-style:italic;}
[data-testid="stChatInput"] button{background:var(--gold-lo) !important; color:#fff !important;}

/* ---------- sidebar: a character sheet on dark leather ---------- */
[data-testid="stSidebar"]{
  background:
    radial-gradient(ellipse at 50% 0%, rgba(212,166,74,.12), transparent 50%),
    repeating-linear-gradient(45deg, rgba(255,255,255,.012) 0 3px, transparent 3px 7px),
    linear-gradient(#24170e, #140d08);
  border-right:2px solid var(--gold-lo);
}
[data-testid="stSidebar"] *{color:#e6d5b0;}
.sheet-title{font-family:var(--title); color:var(--gold-hi) !important; font-size:1.25rem; text-align:center; margin:.2rem 0 0;}
.sheet-sub{font-family:var(--serif); font-style:italic; text-align:center; opacity:.75; margin-bottom:.4rem;}
.sec{font-family:var(--caps); color:var(--gold) !important; font-size:.85rem; letter-spacing:.18em; text-transform:uppercase;
  display:flex; align-items:center; gap:.5rem; margin:1.1rem 0 .45rem;}
.sec::before,.sec::after{content:""; flex:1; height:1px; background:linear-gradient(90deg, transparent, var(--gold-lo), transparent);}
.stat-row{display:flex; gap:.5rem;}
.stat{flex:1; text-align:center; background:rgba(0,0,0,.35); border:1px solid #4a3220; border-radius:10px; padding:.45rem .2rem;}
.stat .v{font-family:var(--caps); font-weight:700; font-size:1.35rem; color:var(--gold-hi) !important; line-height:1.1;}
.stat .k{font-family:var(--caps); font-size:.62rem; letter-spacing:.14em; opacity:.75;}
.ward{display:flex; align-items:center; gap:.55rem; padding:.3rem .5rem; border-radius:8px; background:rgba(0,0,0,.25); margin-bottom:.3rem;}
.ward .state{margin-left:auto; font-family:var(--caps); font-size:.7rem; letter-spacing:.12em;}
.ward .state.sealed{color:#e2a35a !important;} .ward .state.open{color:#8ee0a0 !important;}
.inv{display:grid; grid-template-columns:repeat(2,1fr); gap:.45rem;}
.slot{border:1px dashed #5a3d22; border-radius:10px; min-height:74px; display:flex; flex-direction:column; align-items:center; justify-content:center;
  background:rgba(0,0,0,.28); text-align:center; padding:.35rem; font-size:.85rem;}
.slot.full{border-style:solid; border-color:var(--gold-lo); background:radial-gradient(circle, rgba(212,166,74,.16), rgba(0,0,0,.3));}
.slot.empty{opacity:.4; font-style:italic;}
.quest{display:flex; gap:.5rem; align-items:flex-start; margin:.25rem 0; font-size:1rem;}
.quest .box{font-family:var(--caps); color:var(--gold) !important; width:1rem; flex:none;}
.quest.done span:last-child{text-decoration:line-through; opacity:.6;}
.howto{font-size:.95rem; line-height:1.45; opacity:.9;}
.howto code{display:inline-block; white-space:nowrap; margin:.18rem .15rem 0 0; background:rgba(0,0,0,.4);
  color:var(--gold-hi) !important; border:1px solid #4a3220; border-radius:5px; padding:.05rem .35rem; font-size:.8rem;}
.note-v1{border:1px solid #6a2a20; background:rgba(120,30,20,.18); border-radius:10px; padding:.55rem .7rem; font-size:.92rem;}

/* buttons */
.stButton > button{font-family:var(--caps) !important; letter-spacing:.08em; border-radius:10px;
  background:linear-gradient(#3a2614, #22160c); color:var(--gold-hi) !important; border:1px solid var(--gold-lo);}
.stButton > button:hover{border-color:var(--gold-hi); box-shadow:0 0 14px rgba(246,220,140,.25); color:#fff !important;}
.stButton > button p{color:inherit !important;}
[data-testid="stExpander"]{border:1px solid #4a3220 !important; border-radius:10px; background:rgba(0,0,0,.25);}

/* ---------- victory scroll ---------- */
.victory{position:relative; margin:1.4rem auto 0; max-width:620px; text-align:center; color:var(--ink);
  padding:2.2rem 2rem 2.4rem; border-radius:6px;
  background:radial-gradient(ellipse at 50% 30%, #f7ecd0, #dcc28a 80%);
  box-shadow:inset 0 0 40px rgba(110,70,20,.45), 0 20px 50px rgba(0,0,0,.6);
  border-top:14px solid #b08a4a; border-bottom:14px solid #b08a4a;}
.victory *{color:var(--ink) !important;}
.victory h2{font-family:var(--title) !important; font-size:2rem; margin:.2rem 0; color:var(--crimson) !important;}
.victory .seal{position:absolute; right:-18px; bottom:-26px; width:96px; transform:rotate(-12deg); filter:drop-shadow(0 4px 6px rgba(0,0,0,.5));}
.victory .xp{font-family:var(--caps); letter-spacing:.14em; margin-top:.6rem;}
"""


def apply_theme() -> None:
    """Inject fonts and the stylesheet. Call once per rerun, right after set_page_config."""
    st.markdown(f"<style>{_font_faces()}\n{CSS}</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Page pieces
# ---------------------------------------------------------------------------

def banner(title: str, subtitle: str, badge: str) -> None:
    st.markdown(
        f"""<div class="rpg-banner">
  <img class="scene" src="{svg_uri('scene')}" alt="Illustration of the wizard's library">
  <div class="badge">{html.escape(badge)}</div>
  <div class="title"><h1>{html.escape(title)}</h1><div class="sub">{html.escape(subtitle)}</div></div>
</div>""",
        unsafe_allow_html=True,
    )


def chat_message(role: str, content: str, extra_html: str = "") -> None:
    """Render one message as a parchment (DM) or leather (player) card."""
    with st.chat_message(role, avatar=AVATARS[role]):
        mark = "dm-mark" if role == "assistant" else "hero-mark"
        who = "Dungeon Master" if role == "assistant" else "You"
        st.markdown(f'<span class="{mark}"></span><div class="speaker">{who}</div>{extra_html}',
                    unsafe_allow_html=True)
        st.markdown(content)


def dice_html(roll: int, label: str = "Insight check") -> str:
    flavour = {20: "Natural 20!", 1: "Natural 1…"}.get(roll, label)
    return (f'<div class="dice-roll">{icon("d20", 52, "d20")}'
            f'<div><div class="num">{roll}</div><div class="lbl">{html.escape(flavour)}</div></div></div>')


# ---------------------------------------------------------------------------
# Sidebar ("character sheet") pieces
# ---------------------------------------------------------------------------

def sheet_header(subtitle: str) -> None:
    st.markdown(
        f'<div style="text-align:center">{icon("d20", 54, "d20")}</div>'
        f'<div class="sheet-title">Adventurer\'s Sheet</div><div class="sheet-sub">{html.escape(subtitle)}</div>',
        unsafe_allow_html=True,
    )


def section(title: str) -> None:
    st.markdown(f'<div class="sec">{html.escape(title)}</div>', unsafe_allow_html=True)


def stats(pairs: list[tuple[str, str]]) -> None:
    cells = "".join(f'<div class="stat"><div class="v">{html.escape(v)}</div><div class="k">{html.escape(k)}</div></div>'
                    for k, v in pairs)
    st.markdown(f'<div class="stat-row">{cells}</div>', unsafe_allow_html=True)


def wards(rows: list[tuple[str, bool]]) -> None:
    out = []
    for name, is_open in rows:
        lock = icon("lock_open" if is_open else "lock_closed", 22, "lock")
        state = '<span class="state open">Open</span>' if is_open else '<span class="state sealed">Sealed</span>'
        out.append(f'<div class="ward">{lock}<span>{html.escape(name)}</span>{state}</div>')
    st.markdown("".join(out), unsafe_allow_html=True)


def inventory(items: list[tuple[str, str]], slots: int = 4) -> None:
    """items: list of (display name, icon name)."""
    cells = [f'<div class="slot full">{icon(ic, 40, name)}<div>{html.escape(name)}</div></div>' for name, ic in items]
    cells += ['<div class="slot empty">empty</div>'] * max(0, slots - len(items))
    st.markdown(f'<div class="inv">{"".join(cells)}</div>', unsafe_allow_html=True)


def quest_log(quests: list[tuple[str, bool]]) -> None:
    rows = "".join(
        f'<div class="quest{" done" if done else ""}"><span class="box">{"✦" if done else "◇"}</span><span>{html.escape(q)}</span></div>'
        for q, done in quests)
    st.markdown(rows, unsafe_allow_html=True)


def how_to_play() -> None:
    st.markdown(
        '<div class="howto">Speak your actions aloud, adventurer:<br>'
        '<code>look around</code><code>examine the painting</code><code>take the parchment</code>'
        '<code>use the lantern on the desk</code><code>enter 123 on the drawer</code></div>',
        unsafe_allow_html=True,
    )


def victory(turns: int) -> None:
    xp = max(100, 1000 - turns * 25)
    st.markdown(
        f"""<div class="victory">
  <div class="speaker">Quest complete</div>
  <h2>The Seal Is Broken</h2>
  <p>The runes fall silent and the archmage's prison releases you into the night.
  You escaped in <b>{turns}</b> turns.</p>
  <div class="xp">✦ {xp} XP earned ✦</div>
  <img class="seal" src="{svg_uri('seal')}" alt="wax seal">
</div>""",
        unsafe_allow_html=True,
    )
