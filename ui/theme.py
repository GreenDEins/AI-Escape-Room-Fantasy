"""
Shared fantasy ("tabletop RPG") look for both versions of the game.

Everything visual lives here so the game logic stays clean:
- bundled OFL fonts (Cinzel, Cinzel Decorative, IM Fell English), embedded as base64
- seamless stone / parchment / leather textures (ui/assets/textures, built by scripts/build_textures.py)
- the living scene banner and close-up illustration cards (ui/art.py)
- avatars, item icons and ornaments (original SVG art in ui/assets)
- small HTML builders for the character sheet, dice roll and victory scroll

The apps only call these helpers; nothing here knows the puzzle solutions.
"""

from __future__ import annotations

import base64
import html
from functools import lru_cache
from pathlib import Path

import streamlit as st

from ui import art

UI_DIR = Path(__file__).parent
ASSETS = UI_DIR / "assets"
FONTS = UI_DIR / "fonts"
TEXTURES = ASSETS / "textures"

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
    """data: URI for an SVG file in ui/assets (so it works inside st.markdown HTML)."""
    return f"data:image/svg+xml;base64,{_b64(ASSETS / f'{name}.svg')}"


def _jpg_uri(name: str) -> str:
    return f"data:image/jpeg;base64,{_b64(TEXTURES / f'{name}.jpg')}"


def icon(name: str, size: int = 28, alt: str = "") -> str:
    return f'<img src="{svg_uri(name)}" width="{size}" height="{size}" alt="{html.escape(alt)}" class="rpg-icon">'


# Ornamental gold corner (top-left orientation); the other three are rotations.
_CORNER = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fbe9a6"/>
<stop offset=".5" stop-color="#c9973a"/><stop offset="1" stop-color="#7a5418"/></linearGradient></defs>
<g transform="rotate({rot} 32 32)" fill="none" stroke="url(#g)" stroke-linecap="round">
<path d="M4 60V12q0-8 8-8h48" stroke-width="3"/>
<path d="M10 54V18q0-8 8-8h36" stroke-width="1.2" opacity=".8"/>
<path d="M4 30q14 0 14-14t14-12" stroke-width="2"/>
<path d="M18 16q6 2 6 8-6 0-8-6" stroke-width="1.6"/>
<circle cx="12" cy="12" r="4" fill="url(#g)" stroke="none"/>
<path d="M22 4l3 3-3 3-3-3z" fill="url(#g)" stroke="none"/><path d="M4 22l3 3-3 3-3-3z" fill="url(#g)" stroke="none"/>
</g></svg>"""


@lru_cache(maxsize=4)
def corner_uri(rot: int) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(_CORNER.replace("{rot}", str(rot)).encode()).decode()


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
  --crimson:#8b1e1e; --night:#120c08;
  --serif:'IM Fell English', Georgia, 'Times New Roman', serif;
  --caps:'Cinzel', Georgia, serif; --title:'Cinzel Decorative', 'Cinzel', Georgia, serif;
  --corners: url(__C0__) top left / 34px no-repeat, url(__C90__) top right / 34px no-repeat,
             url(__C270__) bottom left / 34px no-repeat, url(__C180__) bottom right / 34px no-repeat;
}

/* ---------- page: torch-lit dungeon wall ---------- */
.stApp{
  background:
    radial-gradient(ellipse 70% 45% at 50% 0%, rgba(255,160,60,.18), transparent 70%),
    radial-gradient(ellipse 40% 60% at 0% 40%, rgba(255,140,40,.10), transparent 70%),
    radial-gradient(ellipse 40% 60% at 100% 40%, rgba(255,140,40,.10), transparent 70%),
    radial-gradient(ellipse at 50% 50%, transparent 40%, rgba(0,0,0,.85) 100%),
    linear-gradient(rgba(10,6,4,.35), rgba(10,6,4,.6)),
    url(__STONE__) center / 384px repeat;
  background-attachment: fixed;
  color:#e9dcc0;
}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stToolbar"], [data-testid="stDecoration"], footer{display:none !important;}
.block-container{max-width:940px; padding-top:1.2rem; padding-bottom:7rem;}

html, body, .stApp, .stMarkdown, p, li, label, textarea, input{font-family:var(--serif);}
h1,h2,h3,h4{font-family:var(--caps) !important; letter-spacing:.04em;}

/* ---------- banner: the living scene ---------- */
.rpg-banner{position:relative; margin:0 0 1.4rem; padding:10px; border-radius:16px;
  background:linear-gradient(145deg,#f6dc8c,#9a6a22 30%,#f0cf78 55%,#6a4610 80%,#d4a64a);
  box-shadow:0 0 0 2px #0b0705, 0 22px 50px rgba(0,0,0,.75), 0 0 60px rgba(255,170,70,.12);}
.rpg-banner .frame{position:relative; border-radius:9px; overflow:hidden; box-shadow:inset 0 0 0 2px #2a1a08;}
.rpg-banner img.scene{display:block; width:100%; height:auto;}
.rpg-banner .corner{position:absolute; width:46px; height:46px; z-index:3; pointer-events:none;}
.rpg-banner .tl{top:-6px; left:-6px} .rpg-banner .tr{top:-6px; right:-6px}
.rpg-banner .bl{bottom:-6px; left:-6px} .rpg-banner .br{bottom:-6px; right:-6px}
.rpg-banner .title{position:absolute; left:0; right:0; bottom:0; padding:3.2rem 1.4rem .9rem; text-align:center;
  background:linear-gradient(transparent, rgba(8,5,3,.55) 35%, rgba(8,5,3,.94));}
.rpg-banner h1{font-family:var(--title) !important; color:var(--gold-hi); font-size:2.5rem; margin:0; padding:0; line-height:1.1;
  background:linear-gradient(#fff6cf, #f0c96a 55%, #b07a26); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
  filter:drop-shadow(0 2px 0 #2a1704) drop-shadow(0 0 14px rgba(255,190,90,.45));}
.rpg-banner .sub{font-family:var(--serif); font-style:italic; color:#e3d2aa; font-size:1.1rem; margin-top:.2rem;}
.rpg-banner .sub::before,.rpg-banner .sub::after{content:" ❦ "; color:var(--gold); font-style:normal;}
.rpg-banner .badge{position:absolute; top:14px; right:16px; z-index:2; font-family:var(--caps); font-size:.72rem; letter-spacing:.14em;
  color:var(--gold-hi); background:rgba(10,6,4,.78); border:1px solid var(--gold-lo); padding:.28rem .7rem; border-radius:20px;}

/* ---------- chat messages ---------- */
[data-testid="stChatMessage"]{border-radius:6px; padding:1.15rem 1.3rem; margin-bottom:1rem; gap:1rem; position:relative;}
[data-testid="stChatMessage"] > div:first-child img, [data-testid="stChatMessage"] > img{
  width:52px !important; height:52px !important; border-radius:50%; box-shadow:0 0 0 2px #2a1a08, 0 4px 10px rgba(0,0,0,.55);}
[data-testid="stChatMessage"] > div:first-child:has(img){width:52px !important; height:52px !important;}

/* the Dungeon Master speaks on aged parchment */
[data-testid="stChatMessage"]:has(.dm-mark){
  background: var(--corners),
    radial-gradient(ellipse at 50% 40%, transparent 55%, rgba(110,60,15,.45) 100%),
    url(__PARCH__) center / 420px repeat;
  box-shadow: inset 0 0 0 1px rgba(90,55,15,.55), inset 0 0 38px rgba(100,55,10,.55), 0 10px 26px rgba(0,0,0,.55);
}
[data-testid="stChatMessage"]:has(.dm-mark) *{color:var(--ink) !important;}
[data-testid="stChatMessage"]:has(.dm-mark) p{font-size:1.14rem; line-height:1.6;}
[data-testid="stChatMessage"]:has(.dm-mark) .stMarkdown:last-child p:first-child::first-letter{
  font-family:var(--title); float:left; font-size:2.9rem; line-height:.86; padding:.25rem .5rem 0 0; color:var(--crimson) !important;
  text-shadow:1px 1px 0 rgba(212,166,74,.7);}

/* the adventurer speaks on dark tooled leather */
[data-testid="stChatMessage"]:has(.hero-mark){
  background: linear-gradient(rgba(20,12,6,.35), rgba(20,12,6,.55)), url(__LEATHER__) center / 300px repeat;
  box-shadow: inset 0 0 0 1px #5a3d22, inset 0 0 0 5px rgba(0,0,0,.25), 0 6px 18px rgba(0,0,0,.5);
}
[data-testid="stChatMessage"]:has(.hero-mark)::after{content:""; position:absolute; inset:6px; border:1px dashed rgba(212,166,74,.35);
  border-radius:4px; pointer-events:none;}
[data-testid="stChatMessage"]:has(.hero-mark) p{color:#f1e2bf !important; font-style:italic; font-size:1.1rem;}
.dm-mark,.hero-mark{display:none;}
.speaker{font-family:var(--caps) !important; font-size:.72rem; letter-spacing:.18em; text-transform:uppercase; opacity:.7; margin-bottom:.3rem;}

/* illustration card inside a DM message */
.art-card{margin:.6rem 0 .9rem; border-radius:6px; overflow:hidden; position:relative;
  box-shadow:0 0 0 2px #2a1a08, 0 0 0 4px #b8862e, 0 0 0 5px #2a1a08, 0 8px 18px rgba(0,0,0,.45);}
.art-card img{display:block; width:100%; aspect-ratio:640/260; object-fit:cover;}

/* dice roll inside a DM message */
.dice-roll{display:flex; align-items:center; gap:.8rem; margin:.1rem 0 .6rem;}
.dice-roll img{animation:roll .9s cubic-bezier(.2,.8,.3,1); filter:drop-shadow(0 3px 4px rgba(0,0,0,.45));}
.dice-roll .num{font-family:var(--title); font-size:2.1rem; color:var(--crimson) !important; line-height:1;}
.dice-roll .lbl{font-family:var(--caps); font-size:.8rem; letter-spacing:.12em;}
@keyframes roll{from{transform:rotate(-540deg) scale(.4); opacity:0;} to{transform:rotate(0) scale(1); opacity:1;}}

/* ---------- chat input: a bronze plaque ---------- */
[data-testid="stBottom"], [data-testid="stBottom"] > div{background:transparent !important;}
[data-testid="stBottomBlockContainer"]{background:linear-gradient(transparent, rgba(8,5,3,.96) 40%); max-width:940px;}
[data-testid="stChatInput"]{
  background:linear-gradient(rgba(24,15,8,.92), rgba(16,10,5,.96)), url(__LEATHER__) center / 300px repeat !important;
  border:2px solid var(--gold-lo) !important; border-radius:12px !important;
  box-shadow:0 0 0 1px #000, inset 0 1px 0 rgba(246,220,140,.25), 0 0 26px rgba(212,166,74,.18);}
[data-testid="stChatInput"]:focus-within{border-color:var(--gold) !important; box-shadow:0 0 0 1px #000, 0 0 30px rgba(246,220,140,.35);}
[data-testid="stChatInput"] textarea{color:#f3e4c0 !important; font-size:1.1rem !important; caret-color:var(--gold-hi);}
[data-testid="stChatInput"] textarea::placeholder{color:#a58c63 !important; font-style:italic;}
[data-testid="stChatInput"] button{background:linear-gradient(#e0b55a,#8a5d1c) !important; color:#1a0f05 !important; border-radius:8px !important;}

/* ---------- sidebar: a character sheet bound in leather ---------- */
[data-testid="stSidebar"]{
  background:
    radial-gradient(ellipse at 50% 0%, rgba(212,166,74,.16), transparent 45%),
    linear-gradient(rgba(14,8,4,.25), rgba(14,8,4,.55)),
    url(__LEATHER__) center / 300px repeat;
  border-right:3px solid var(--gold-lo); box-shadow:inset -8px 0 18px rgba(0,0,0,.5);
}
[data-testid="stSidebar"] > div:first-child{background:transparent;}
[data-testid="stSidebar"] *{color:#e6d5b0;}
.portrait{display:block; width:96px; height:96px; margin:.2rem auto .3rem; border-radius:50%;
  box-shadow:0 0 0 3px #2a1a08, 0 0 0 6px #c9973a, 0 0 0 7px #2a1a08, 0 0 24px rgba(246,220,140,.25);}
.sheet-title{font-family:var(--title); font-size:1.3rem; text-align:center; margin:.35rem 0 0;
  background:linear-gradient(#fff6cf,#d9a845); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;}
.sheet-sub{font-family:var(--serif); font-style:italic; text-align:center; opacity:.75; margin-bottom:.5rem;}
.sec{font-family:var(--caps); color:var(--gold) !important; font-size:.85rem; letter-spacing:.2em; text-transform:uppercase;
  display:flex; align-items:center; gap:.5rem; margin:1.15rem 0 .5rem;}
.sec::before,.sec::after{content:""; flex:1; height:1px; background:linear-gradient(90deg, transparent, var(--gold), transparent);}
.stat-row{display:flex; gap:.5rem;}
.stat{flex:1; text-align:center; background:rgba(0,0,0,.4); border:1px solid #5a3d22; border-radius:10px; padding:.45rem .2rem;
  box-shadow:inset 0 0 10px rgba(0,0,0,.6);}
.stat .v{font-family:var(--caps); font-weight:700; font-size:1.35rem; color:var(--gold-hi) !important; line-height:1.1;}
.stat .k{font-family:var(--caps); font-size:.62rem; letter-spacing:.14em; opacity:.75;}
.ward{display:flex; align-items:center; gap:.55rem; padding:.35rem .55rem; border-radius:8px; background:rgba(0,0,0,.3);
  margin-bottom:.35rem; border:1px solid rgba(90,61,34,.6);}
.ward .state{margin-left:auto; font-family:var(--caps); font-size:.7rem; letter-spacing:.12em;}
.ward .state.sealed{color:#e2a35a !important;} .ward .state.open{color:#8ee0a0 !important;}
.inv{display:grid; grid-template-columns:repeat(2,1fr); gap:.5rem;}
.slot{border-radius:10px; min-height:82px; display:flex; flex-direction:column; align-items:center; justify-content:center;
  background:radial-gradient(circle, rgba(0,0,0,.2), rgba(0,0,0,.5)); text-align:center; padding:.35rem; font-size:.85rem;
  box-shadow:inset 0 0 0 1px #5a3d22, inset 0 0 14px rgba(0,0,0,.7);}
.slot.full{background:radial-gradient(circle, rgba(212,166,74,.22), rgba(0,0,0,.45));
  box-shadow:inset 0 0 0 1px var(--gold), inset 0 0 14px rgba(0,0,0,.5), 0 0 12px rgba(212,166,74,.18);}
.slot.full img{filter:drop-shadow(0 0 6px rgba(246,220,140,.35));}
.slot.empty{opacity:.42; font-style:italic;}
.quest{display:flex; gap:.55rem; align-items:flex-start; margin:.3rem 0; font-size:1.02rem;}
.quest .box{font-family:var(--caps); color:var(--gold) !important; width:1rem; flex:none;}
.quest.done .box{color:#8ee0a0 !important; text-shadow:0 0 8px rgba(142,224,160,.6);}
.quest.done span:last-child{text-decoration:line-through; opacity:.6;}
.howto{font-size:.95rem; line-height:1.45; opacity:.9;}
.howto code{display:inline-block; white-space:nowrap; margin:.2rem .15rem 0 0; background:rgba(0,0,0,.45);
  color:var(--gold-hi) !important; border:1px solid #5a3d22; border-radius:5px; padding:.05rem .35rem; font-size:.8rem;}
.note-v1{border:1px solid #6a2a20; background:rgba(120,30,20,.2); border-radius:10px; padding:.6rem .75rem; font-size:.92rem;}

/* buttons */
.stButton > button{font-family:var(--caps) !important; letter-spacing:.08em; border-radius:10px;
  background:linear-gradient(#4a3018, #22160c); color:var(--gold-hi) !important; border:1px solid var(--gold-lo);
  box-shadow:inset 0 1px 0 rgba(246,220,140,.2), 0 3px 8px rgba(0,0,0,.4);}
.stButton > button:hover{border-color:var(--gold-hi); box-shadow:0 0 16px rgba(246,220,140,.3); color:#fff !important;}
.stButton > button p{color:inherit !important;}
[data-testid="stExpander"]{border:1px solid #4a3220 !important; border-radius:10px; background:rgba(0,0,0,.3);}
[data-testid="stAlert"]{background:rgba(60,30,8,.85) !important; border:1px solid var(--gold-lo); border-radius:10px;}
[data-testid="stSpinner"] *{color:var(--gold-hi) !important; font-style:italic;}

/* ---------- victory scroll ---------- */
.victory{position:relative; margin:1.6rem auto 0; max-width:640px; text-align:center; color:var(--ink);
  padding:2.4rem 2.2rem 2.6rem; border-radius:4px;
  background: var(--corners), radial-gradient(ellipse at 50% 45%, transparent 50%, rgba(110,60,15,.5) 100%), url(__PARCH__) center / 420px repeat;
  box-shadow:inset 0 0 50px rgba(110,70,20,.55), 0 24px 60px rgba(0,0,0,.7);}
.victory::before,.victory::after{content:""; position:absolute; left:-14px; right:-14px; height:22px; border-radius:11px;
  background:linear-gradient(#e8c98a,#8a5d2a 60%,#5a3a18); box-shadow:0 4px 10px rgba(0,0,0,.5);}
.victory::before{top:-12px} .victory::after{bottom:-12px}
.victory *{color:var(--ink) !important;}
.victory h2{font-family:var(--title) !important; font-size:2.1rem; margin:.2rem 0; color:var(--crimson) !important;}
.victory .seal{position:absolute; right:-20px; bottom:-30px; width:104px; transform:rotate(-12deg); filter:drop-shadow(0 4px 6px rgba(0,0,0,.5)); z-index:2;}
.victory .xp{font-family:var(--caps); letter-spacing:.16em; margin-top:.7rem;}

@media (max-width: 700px){
  .rpg-banner h1{font-size:1.5rem;} .rpg-banner .sub{font-size:.9rem;} .rpg-banner .title{padding:1.6rem .8rem .5rem;}
  .rpg-banner .badge{font-size:.6rem; top:8px; right:8px;}
  [data-testid="stChatMessage"]{padding:.9rem .9rem;}
}
"""


@lru_cache(maxsize=1)
def _stylesheet() -> str:
    css = (CSS.replace("__STONE__", _jpg_uri("stone")).replace("__PARCH__", _jpg_uri("parchment"))
           .replace("__LEATHER__", _jpg_uri("leather")))
    for rot in (0, 90, 180, 270):
        css = css.replace(f"__C{rot}__", corner_uri(rot))
    return f"<style>{_font_faces()}\n{css}</style>"


def apply_theme() -> None:
    """Inject fonts and the stylesheet. Call once per rerun, right after set_page_config."""
    st.markdown(_stylesheet(), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Page pieces
# ---------------------------------------------------------------------------

@lru_cache(maxsize=32)
def _scene_uri(drawer_open: bool, lantern_taken: bool, message_revealed: bool, door_open: bool) -> str:
    return art.to_data_uri(art.scene(drawer_open, lantern_taken, message_revealed, door_open))


def banner(title: str, subtitle: str, badge: str, *, drawer_open: bool = False, lantern_taken: bool = False,
           message_revealed: bool = False, door_open: bool = False) -> None:
    """The illustrated scene. In Version 2 it reflects the game state."""
    scene = _scene_uri(drawer_open, lantern_taken, message_revealed, door_open)
    corners = "".join(f'<img class="corner {cls}" src="{corner_uri(rot)}" alt="">'
                      for cls, rot in [("tl", 0), ("tr", 90), ("br", 180), ("bl", 270)])
    st.markdown(
        f"""<div class="rpg-banner">{corners}<div class="frame">
  <img class="scene" src="{scene}" alt="Illustration of the wizard's library">
  <div class="badge">{html.escape(badge)}</div>
  <div class="title"><h1>{html.escape(title)}</h1><div class="sub">{html.escape(subtitle)}</div></div>
</div></div>""",
        unsafe_allow_html=True,
    )


@lru_cache(maxsize=None)
def art_card_html(name: str) -> str:
    return f'<div class="art-card"><img src="{art.to_data_uri(art.card(name))}" alt="{html.escape(name)}"></div>'


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
    return (f'<div class="dice-roll">{icon("d20", 56, "d20")}'
            f'<div><div class="num">{roll}</div><div class="lbl">{html.escape(flavour)}</div></div></div>')


# ---------------------------------------------------------------------------
# Sidebar ("character sheet") pieces
# ---------------------------------------------------------------------------

def sheet_header(subtitle: str) -> None:
    st.markdown(
        f'<img class="portrait" src="data:image/png;base64,{_b64(ASSETS / "hero.png")}" alt="Adventurer portrait">'
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
    cells = [f'<div class="slot full">{icon(ic, 42, name)}<div>{html.escape(name)}</div></div>' for name, ic in items]
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
