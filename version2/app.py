"""
Version 2 — Reliable AI Escape Room (Streamlit).

Run:  streamlit run version2/app.py

Pipeline for every player message:
    text -> HybridParser -> Action -> GameEngine (validates + updates state)
         -> Result(facts) -> Narrator (LLM describes facts) -> chat

Works without an API key too: the rule parser and plain-text narration are used.
"""

import json
import os

import streamlit as st
from dotenv import load_dotenv

from engine import GameEngine
from narrator import Narrator
from parser import HybridParser, LLMParser, RuleParser
from state import load_config, new_state, public_view

load_dotenv()
st.set_page_config(page_title="AI Escape Room — V2", page_icon="🔐")

CONFIG = load_config()


@st.cache_resource
def get_llm_client():
    """Return a Gemini client, or None to run in offline mode."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or os.getenv("ESCAPE_ROOM_OFFLINE") == "1":
        return None
    from google import genai
    return genai.Client(api_key=api_key)


client = get_llm_client()
model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def reset_game() -> None:
    st.session_state.state = new_state(CONFIG)
    st.session_state.messages = [{"role": "assistant", "content": CONFIG["intro"]}]
    st.session_state.debug_log = []


if "state" not in st.session_state:
    reset_game()

state = st.session_state.state
engine = GameEngine(CONFIG, state)
parser = HybridParser(RuleParser(CONFIG), LLMParser(client, model, CONFIG) if client else None)
narrator = Narrator(CONFIG, client, model)

# ---------- Sidebar ----------
with st.sidebar:
    st.header("How to play")
    st.markdown(
        """
Describe what you do in plain English:
*look around · examine the painting · take the note ·
use the flashlight on the desk · enter 123 on the drawer · hint*
"""
    )
    if st.button("🔄 Restart game", use_container_width=True):
        reset_game()
        st.rerun()

    view = public_view(state, CONFIG)
    st.subheader("Status")
    st.markdown(f"🚪 Door: **{view['door']}**  \n🗄️ Drawer: **{view['drawer']}**  \n⏱️ Turn: {view['turn']}")
    st.subheader("Inventory")
    st.markdown("\n".join(f"- {i}" for i in view["inventory"]) or "_empty_")
    st.subheader("Puzzles")
    for pid, label in CONFIG["puzzles"].items():
        st.markdown(f"{'✅' if pid in state['solved'] else '⬜'} {label}")

    st.divider()
    st.caption(f"Narrator: {'Gemini (' + model + ')' if client else 'offline (plain text)'}")
    with st.expander("🔧 Debug: game state"):
        st.json({k: v for k, v in state.items() if k != "history"})
        st.json(st.session_state.debug_log[-5:])

st.title("🔐 The Locked Library")
st.caption("Version 2 · Python game engine + LLM narrator")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if state["escaped"]:
    st.success(f"🎉 You escaped in {state['turn']} turns! Press **Restart game** to play again.")
    st.balloons()
    st.stop()

if player_input := st.chat_input("What do you do?"):
    st.session_state.messages.append({"role": "user", "content": player_input})

    action, parsed_by = parser.parse(player_input)
    result = engine.process(action, player_input)
    recent = [m["content"] for m in st.session_state.messages if m["role"] == "assistant"]
    reply = narrator.narrate(result, player_input, recent)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.debug_log.append({
        "input": player_input,
        "action": action.to_dict(),
        "parsed_by": parsed_by,
        "outcome": result.outcome,
        "facts": result.facts,
        "narration": narrator.last_source,
    })
    st.rerun()
