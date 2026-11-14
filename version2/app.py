"""
Version 2 — Reliable AI Escape Room (Streamlit).

Run from the project root:  streamlit run version2/app.py

Pipeline for every player message:
    text -> HybridParser -> Action -> GameEngine (validates + updates state)
         -> Result(facts) -> Narrator (LLM describes facts) -> chat

Works without an API key too: the rule parser and plain-text narration are used.
The fantasy look (fonts, parchment, art) comes from ui/theme.py.
"""

import os
import random
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # project root, for ui/

from engine import Action, GameEngine  # noqa: E402
from narrator import Narrator  # noqa: E402
from parser import HybridParser, LLMParser, RuleParser  # noqa: E402
from state import load_config, new_state  # noqa: E402
from ui import theme  # noqa: E402

load_dotenv()
st.set_page_config(page_title="The Locked Library", page_icon="🎲", layout="centered")
theme.apply_theme()

CONFIG = load_config()


@st.cache_resource
def get_llm_client():
    """Return a Gemini client, or None to run in offline mode."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or os.getenv("ESCAPE_ROOM_OFFLINE") == "1":
        return None
    from google import genai
    from google.genai import types
    # Fail fast instead of hanging: at most 30 s per request and 2 attempts.
    # On any error the narrator falls back to plain text and the UI shows why.
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(
        timeout=30_000, retry_options=types.HttpRetryOptions(attempts=2, max_delay=5)))


client = get_llm_client()
model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


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


# Which close-up illustration (ui/art.py) to show for a successful action.
EXAMINE_ART = {"bookshelf": "bookshelf_close", "painting": "painting", "clock": "clock", "desk": "desk",
               "drawer": "desk", "rug": "rug", "sconces": "sconces", "window": "window", "door": "door",
               "torn_note": "note", "moon_lantern": "lantern"}


def pick_art(action: Action, result) -> str | None:
    """Purely cosmetic: choose an illustration for the Dungeon Master's reply."""
    if not result.ok:
        return None
    lantern_waiting = (not state["locked"]["drawer"]) and "moon_lantern" not in state["inventory"]
    if result.outcome == "escaped":
        return "door_open"
    if result.outcome == "unlocked":
        return "drawer_open"
    if result.outcome in ("puzzle_solved", "use") and action.target == "desk" and action.item == "moon_lantern":
        return "reveal"
    if result.outcome == "take":
        return EXAMINE_ART.get(action.target)
    if result.outcome in ("examine", "examine_item", "open"):
        if action.target in ("desk", "drawer") and lantern_waiting:
            return "drawer_open"
        return EXAMINE_ART.get(action.target)
    return None


def play_turn(player_text: str, action: Action | None = None, dice: int | None = None) -> None:
    """Run one turn through parser -> engine -> narrator and store both messages."""
    st.session_state.messages.append({"role": "user", "content": player_text})
    parsed_by = "button"
    if action is None:
        action, parsed_by = parser.parse(player_text)
    result = engine.process(action, player_text)
    recent = [m["content"] for m in st.session_state.messages if m["role"] == "assistant"]
    reply = narrator.narrate(result, player_text, recent)

    st.session_state.messages.append({"role": "assistant", "content": reply, "dice": dice,
                                      "art": pick_art(action, result)})
    st.session_state.debug_log.append({
        "input": player_text,
        "action": action.to_dict(),
        "parsed_by": parsed_by,
        "outcome": result.outcome,
        "facts": result.facts,
        "narration": narrator.last_source,
        "llm_error": narrator.last_error,
    })


# ---------- Sidebar: the adventurer's sheet ----------
with st.sidebar:
    theme.sheet_header("Version 2 · the rules are enforced")

    solved = sum(p in state["solved"] for p in CONFIG["puzzles"])
    theme.stats([("Turn", str(state["turn"])), ("Quests", f"{solved}/{len(CONFIG['puzzles'])}"),
                 ("Items", str(len(state["inventory"])))])

    theme.section("Wards")
    theme.wards([("Desk drawer", not state["locked"]["drawer"]), ("Rune door", not state["locked"]["door"])])

    theme.section("Inventory")
    theme.inventory([(CONFIG["items"][i]["name"], CONFIG["items"][i].get("icon", "note")) for i in state["inventory"]])

    theme.section("Quest log")
    theme.quest_log([(label, pid in state["solved"]) for pid, label in CONFIG["puzzles"].items()])

    theme.section("Actions")
    roll_clicked = st.button("🎲 Roll for Insight (hint)", use_container_width=True, disabled=state["escaped"])
    if st.button("↺ Begin a new adventure", use_container_width=True):
        reset_game()
        st.rerun()

    theme.section("How to play")
    theme.how_to_play()

    st.caption(f"Narrator: {'Gemini · ' + model if client else 'offline (plain text)'}")
    with st.expander("Arcane ledger (debug state)"):
        st.json({k: v for k, v in state.items() if k != "history"})
        st.json(st.session_state.debug_log[-5:])

if roll_clicked:
    with st.spinner("The dice tumble across the table..."):
        play_turn("I study the room for anything I might have missed.", Action("hint"), dice=random.randint(1, 20))
    st.rerun()

# ---------- Main stage ----------
theme.banner(CONFIG["title"], CONFIG.get("subtitle", ""), "Version 2",
             drawer_open=not state["locked"]["drawer"], lantern_taken="moon_lantern" in state["inventory"],
             message_revealed="moonlight_puzzle" in state["solved"], door_open=state["escaped"])

for msg in st.session_state.messages:
    extra = theme.dice_html(msg["dice"]) if msg.get("dice") else ""
    if msg.get("art"):
        extra += theme.art_card_html(msg["art"])
    theme.chat_message(msg["role"], msg["content"], extra)

last_turn = st.session_state.debug_log[-1] if st.session_state.debug_log else {}
if last_turn.get("llm_error"):
    st.warning("Gemini could not narrate this turn, so the plain game text is shown instead. "
               f"Error: {last_turn['llm_error']}")

if state["escaped"]:
    theme.victory(state["turn"])
    st.stop()

if player_input := st.chat_input("What do you do, adventurer?"):
    theme.chat_message("user", player_input)
    with st.spinner("The Dungeon Master weighs your fate..."):
        play_turn(player_input)
    st.rerun()
