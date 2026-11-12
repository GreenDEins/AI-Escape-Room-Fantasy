"""
Version 2 — structured game state.

The state is a plain Python dictionary, so it is easy to inspect, show in the
UI and serialise to JSON. Only the engine (engine.py) is allowed to change it;
the LLM never writes to it.
"""

import copy
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "game_config.json"


def load_config(path: Path | str = CONFIG_PATH) -> dict:
    """Load the game definition (room, objects, items, solutions, rules)."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def new_state(config: dict) -> dict:
    """Create a fresh game state for a new session."""
    locked = {obj_id: True for obj_id, obj in config["objects"].items() if "lock" in obj}
    return {
        "turn": 0,
        "inventory": [],            # item ids the player is carrying
        "visible_items": [],        # item ids the player has seen and can take
        "examined": [],             # object ids the player has examined
        "discovered": [],           # clue ids the player has found
        "solved": [],               # puzzle ids that are completed
        "locked": locked,           # {"drawer": True, "door": True}
        "code_attempts": {obj_id: 0 for obj_id in locked},
        "escaped": False,
        "history": [],              # [{turn, input, action, outcome}]
    }


def snapshot(state: dict) -> dict:
    """Deep copy — used by tests to check that a rejected action changed nothing."""
    return copy.deepcopy(state)


def public_view(state: dict, config: dict) -> dict:
    """The part of the state that is safe to show the player (no solutions)."""
    items = config["items"]
    return {
        "inventory": [items[i]["name"] for i in state["inventory"]],
        "solved_puzzles": [config["puzzles"][p] for p in state["solved"]],
        "door": "open" if not state["locked"].get("door", True) else "locked",
        "drawer": "open" if not state["locked"].get("drawer", True) else "locked",
        "turn": state["turn"],
        "escaped": state["escaped"],
    }
