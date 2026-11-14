"""
Version 1 — Interactive AI Escape Room (Streamlit).

Run from the project root:  streamlit run version1/app.py

Architecture: Player -> Streamlit chat -> (system prompt + full history) -> Gemini -> reply.
The LLM is the only source of truth for the game: there is no inventory, no lock
state and no validation. The fantasy look comes from ui/theme.py.
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # project root, for ui/

from llm import GameMasterLLM  # noqa: E402
from prompts import ESCAPE_TAG, INTRO_TEXT, SYSTEM_PROMPT  # noqa: E402
from ui import theme  # noqa: E402

st.set_page_config(page_title="The Locked Library — V1", page_icon="🎲", layout="centered")
theme.apply_theme()


def reset_game() -> None:
    st.session_state.messages = [{"role": "assistant", "content": INTRO_TEXT}]
    st.session_state.escaped = False


if "messages" not in st.session_state:
    reset_game()

turns = sum(m["role"] == "user" for m in st.session_state.messages)

# ---------- Sidebar ----------
with st.sidebar:
    theme.sheet_header("Version 1 · the Dungeon Master decides")
    theme.stats([("Turn", str(turns)), ("Quests", "?"), ("Items", "?")])
    theme.section("Notice")
    st.markdown(
        '<div class="note-v1">In this version there is no character sheet. The Dungeon Master '
        '(the LLM) alone remembers your items and decides what succeeds.</div>',
        unsafe_allow_html=True,
    )
    theme.section("Actions")
    if st.button("↺ Begin a new adventure", use_container_width=True):
        reset_game()
        st.rerun()
    theme.section("How to play")
    theme.how_to_play()

theme.banner("The Locked Library", "A wizard's escape room", "Version 1")

# ---------- LLM client ----------
try:
    gm = GameMasterLLM(SYSTEM_PROMPT)
except RuntimeError as err:
    st.error(str(err))
    st.stop()

# ---------- Chat history ----------
for msg in st.session_state.messages:
    theme.chat_message(msg["role"], msg["content"].replace(ESCAPE_TAG, "").strip())

if st.session_state.escaped:
    theme.victory(turns)
    st.stop()

# ---------- Player turn ----------
if player_input := st.chat_input("What do you do, adventurer?"):
    st.session_state.messages.append({"role": "user", "content": player_input})
    theme.chat_message("user", player_input)

    with st.spinner("The Dungeon Master consults the tomes..."):
        try:
            reply = gm.reply(st.session_state.messages)
        except Exception as err:  # network / quota errors
            reply = f"*(The Dungeon Master falls silent — API error: {err})*"

    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Game completion: we rely on the LLM to emit the escape tag.
    if ESCAPE_TAG in reply:
        st.session_state.escaped = True
    st.rerun()
