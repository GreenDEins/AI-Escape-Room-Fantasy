"""
Version 1 — Interactive AI Escape Room (Streamlit).

Run:  streamlit run version1/app.py

Architecture: Player -> Streamlit chat -> (system prompt + full history) -> Gemini -> reply.
The LLM is the only source of truth for the game.
"""

import streamlit as st

from llm import GameMasterLLM
from prompts import ESCAPE_TAG, INTRO_TEXT, SYSTEM_PROMPT

st.set_page_config(page_title="AI Escape Room — V1", page_icon="🔐")


def reset_game() -> None:
    st.session_state.messages = [{"role": "assistant", "content": INTRO_TEXT}]
    st.session_state.escaped = False


if "messages" not in st.session_state:
    reset_game()

# ---------- Sidebar: instructions and restart ----------
with st.sidebar:
    st.header("How to play")
    st.markdown(
        """
Type what you want to do in plain English, for example:

- *look around*
- *examine the bookshelf*
- *take the flashlight*
- *enter 123 on the drawer*

Find clues, solve three puzzles and unlock the door.
"""
    )
    if st.button("🔄 Restart game", use_container_width=True):
        reset_game()
        st.rerun()
    st.caption("Version 1 — the LLM alone runs the game.")

st.title("🔐 The Locked Library")
st.caption("Version 1 · LLM Game Master")

# ---------- LLM client ----------
try:
    gm = GameMasterLLM(SYSTEM_PROMPT)
except RuntimeError as err:
    st.error(str(err))
    st.stop()

# ---------- Chat history ----------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"].replace(ESCAPE_TAG, "").strip())

if st.session_state.escaped:
    st.success("🎉 You escaped the library! Press **Restart game** to play again.")
    st.stop()

# ---------- Player turn ----------
if player_input := st.chat_input("What do you do?"):
    st.session_state.messages.append({"role": "user", "content": player_input})
    with st.chat_message("user"):
        st.markdown(player_input)

    with st.chat_message("assistant"):
        with st.spinner("The Game Master is thinking..."):
            try:
                reply = gm.reply(st.session_state.messages)
            except Exception as err:  # network / quota errors
                reply = f"*(The Game Master is silent — API error: {err})*"
        st.markdown(reply.replace(ESCAPE_TAG, "").strip())

    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Game completion: we rely on the LLM to emit the escape tag.
    if ESCAPE_TAG in reply:
        st.session_state.escaped = True
        st.rerun()
