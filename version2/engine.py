"""
Version 2 — game engine and action validation.

This is the core of Version 2. Python — not the LLM — decides whether an
action succeeds. Every handler:

1. validates the action against the config and the current state,
2. changes the state only if the action is legal,
3. returns a Result with plain-language *facts* about what happened.

The LLM narrator later turns those facts into atmospheric prose, but it can
never change the outcome.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

VERBS = {
    "look", "examine", "take", "use", "enter_code", "open",
    "inventory", "hint", "help", "meta", "claim", "unknown",
}


@dataclass
class Action:
    """A structured player action produced by the parser."""
    verb: str
    target: str | None = None      # resolved object/item id, if any
    item: str | None = None        # resolved item id for "use X on Y"
    code: str | None = None        # digits for enter_code
    raw_target: str | None = None  # the player's own word if it could not be resolved

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class Result:
    """What the engine decided. `facts` is the only thing the narrator sees."""
    ok: bool
    outcome: str                       # machine-readable outcome code
    facts: list[str] = field(default_factory=list)
    escaped: bool = False


HELP_TEXT = (
    "You can: look around, examine <thing>, take <item>, use <item> on <thing>, "
    "enter <code> on <drawer/door>, open <thing>, check your inventory, or ask for a hint."
)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class GameEngine:
    def __init__(self, config: dict, state: dict):
        self.config = config
        self.state = state
        self.objects = config["objects"]
        self.items = config["items"]

    # ----- public entry point -------------------------------------------------

    def process(self, action: Action, raw_input: str = "") -> Result:
        """Validate and apply one action, record it in the history."""
        if self.state["escaped"]:
            result = Result(False, "game_over", ["You have already escaped. Restart to play again."])
        else:
            handler = getattr(self, f"_do_{action.verb}", self._do_unknown)
            result = handler(action)

        self.state["turn"] += 1
        self.state["history"].append({
            "turn": self.state["turn"],
            "input": raw_input,
            "action": action.to_dict(),
            "outcome": result.outcome,
        })
        return result

    # ----- helpers ------------------------------------------------------------

    def _name(self, entity_id: str) -> str:
        if entity_id in self.objects:
            return self.objects[entity_id]["name"]
        if entity_id in self.items:
            return self.items[entity_id]["name"]
        return entity_id

    def _item_is_reachable(self, item_id: str) -> bool:
        """The player knows about this item (it was revealed or is carried)."""
        return item_id in self.state["visible_items"] or item_id in self.state["inventory"]

    def _not_here(self, action: Action) -> Result:
        # Never use the canonical name here: it could leak a hidden item ("UV flashlight").
        if action.raw_target:
            text = f"There is no '{action.raw_target}' here."
        else:
            text = "You don't see anything like that here."
        return Result(False, "unknown_target", [text + " You can only interact with what is in the room."])

    def _add_unique(self, key: str, value: str) -> bool:
        if value not in self.state[key]:
            self.state[key].append(value)
            return True
        return False

    def _object_description(self, obj_id: str) -> str:
        obj = self.objects[obj_id]
        if "lock" in obj:
            return obj["description_locked"] if self.state["locked"][obj_id] else obj["description_open"]
        return obj["description"]

    def _contents_line(self, obj_id: str) -> str | None:
        """Items still lying inside an open container."""
        remaining = [i for i in self.objects[obj_id].get("contains", [])
                     if i not in self.state["inventory"]]
        if not remaining:
            return None
        names = ", ".join(self.items[i]["name"] for i in remaining)
        return f"Inside you can see: {names}."

    # ----- action handlers ----------------------------------------------------

    def _do_look(self, action: Action) -> Result:
        facts = [self.config["room_description"]]
        loose = [i for i in self.state["visible_items"] if i not in self.state["inventory"]]
        if loose:
            facts.append("Items you have spotted: " + ", ".join(self.items[i]["name"] for i in loose) + ".")
        return Result(True, "look", facts)

    def _do_examine(self, action: Action) -> Result:
        target = action.target
        if target is None:
            return self._not_here(action) if action.raw_target else Result(
                False, "missing_target", ["Examine what? Name an object in the room."])

        # Examining an item
        if target in self.items:
            if not self._item_is_reachable(target):
                return self._not_here(action)
            return Result(True, "examine_item", [self.items[target]["description"]])

        if target not in self.objects:
            return self._not_here(action)

        obj = self.objects[target]
        facts = [self._object_description(target)]
        self._add_unique("examined", target)

        effects = obj.get("on_examine", {})
        for item_id in effects.get("reveal_items", []):
            if item_id not in self.state["inventory"]:
                self._add_unique("visible_items", item_id)
        if "discover" in effects:
            self._add_unique("discovered", effects["discover"])
        if "solves" in effects and self._add_unique("solved", effects["solves"]):
            facts.append("You feel you have understood an important clue.")

        if "lock" in obj and not self.state["locked"][target]:
            line = self._contents_line(target)
            if line:
                facts.append(line)
        return Result(True, "examine", facts)

    def _do_take(self, action: Action) -> Result:
        target = action.target
        if target is None:
            return self._not_here(action) if action.raw_target else Result(
                False, "missing_target", ["Take what?"])
        if target in self.objects:
            return Result(False, "not_takeable", [f"The {self._name(target)} cannot be carried."])
        if target not in self.items or not self._item_is_reachable(target):
            # Do not reveal that a hidden item exists before it is discovered.
            return self._not_here(action)
        if target in self.state["inventory"]:
            return Result(False, "already_have", [f"You already have the {self._name(target)}."])

        self.state["inventory"].append(target)
        self.state["visible_items"].remove(target)
        return Result(True, "take", [f"You take the {self._name(target)}.", self.items[target]["description"]])

    def _do_use(self, action: Action) -> Result:
        item, target = action.item, action.target
        if item is None:
            if action.raw_target:
                return Result(False, "not_in_inventory",
                              [f"You don't have any '{action.raw_target}'. "
                               "You can only use items you have picked up."])
            return Result(False, "missing_item", ["Use what? Name an item you are carrying."])
        if item in self.objects:
            return Result(False, "not_an_item", [f"The {self._name(item)} is not something you can use like that."])
        if item not in self.items:
            return self._not_here(Action("use", raw_target=action.raw_target or item))
        if item not in self.state["inventory"]:
            # Covers both "never seen" and "seen but not picked up".
            return Result(False, "not_in_inventory",
                          ["You are not carrying that. You can only use items you have picked up."])
        if target is None:
            return Result(False, "missing_target", [f"Use the {self._name(item)} on what?"])
        if target not in self.objects:
            return self._not_here(Action("use", target=target, raw_target=action.raw_target))

        for rule in self.config["interactions"]:
            if rule["item"] == item and rule["target"] == target:
                solves = rule.get("solves")
                if solves:
                    first_time = self._add_unique("solved", solves)
                    text = rule["text"] if first_time else rule.get("repeat_text", rule["text"])
                    return Result(True, "puzzle_solved" if first_time else "use", [text])
                return Result(True, "use", [rule["text"]])

        return Result(False, "no_effect",
                      [f"You use the {self._name(item)} on the {self._name(target)}. Nothing happens."])

    def _do_enter_code(self, action: Action) -> Result:
        code = (action.code or "").strip()
        target = action.target
        if not code.isdigit():
            return Result(False, "bad_code", ["Codes must be made of digits only."])

        locks = {oid: o["lock"] for oid, o in self.objects.items() if "lock" in o}
        if target is None:
            # Infer the lock from the number of digits.
            matches = [oid for oid, lock in locks.items() if lock["digits"] == len(code)]
            target = matches[0] if len(matches) == 1 else None
            if target is None:
                return Result(False, "missing_target", ["Which lock do you want to enter the code on?"])
        if target not in locks:
            if target in self.objects:
                return Result(False, "no_lock", [f"The {self._name(target)} has no code lock."])
            return self._not_here(action)

        lock = locks[target]
        name = self._name(target)
        if not self.state["locked"][target]:
            return Result(False, "already_open", [f"The {name} is already unlocked."])
        if len(code) != lock["digits"]:
            return Result(False, "wrong_length", [f"The {name} lock takes exactly {lock['digits']} digits."])

        self.state["code_attempts"][target] += 1
        rejected = Result(False, "wrong_code",
                          [f"You enter {code} on the {name}. The lock does not open."])

        if code != lock["code"]:
            return rejected

        missing = [p for p in lock.get("requires_solved", []) if p not in self.state["solved"]]
        if missing:
            # Correct digits, but the required puzzles are not done (guessed or leaked code).
            # Same message as a wrong code, so the player learns nothing from it.
            rejected.outcome = "code_without_prerequisites"
            return rejected

        # Success
        self.state["locked"][target] = False
        self._add_unique("solved", lock["solves"])
        facts = [obj_text for obj_text in [self.objects[target].get("on_unlock")] if obj_text]
        for item_id in self.objects[target].get("contains", []):
            self._add_unique("visible_items", item_id)
        if self.objects[target].get("is_exit"):
            self.state["escaped"] = True
            return Result(True, "escaped", facts, escaped=True)
        return Result(True, "unlocked", facts)

    def _do_open(self, action: Action) -> Result:
        target = action.target
        if target is None or target not in self.objects:
            return self._not_here(action) if (action.raw_target or target) else Result(
                False, "missing_target", ["Open what?"])
        obj = self.objects[target]
        if "lock" not in obj:
            return Result(False, "cannot_open", [f"The {self._name(target)} cannot be opened."])
        if self.state["locked"][target]:
            digits = obj["lock"]["digits"]
            return Result(False, "locked",
                          [f"The {self._name(target)} is locked. It needs a {digits}-digit code."])
        facts = [self._object_description(target)]
        line = self._contents_line(target)
        if line:
            facts.append(line)
        return Result(True, "open", facts)

    def _do_inventory(self, action: Action) -> Result:
        if not self.state["inventory"]:
            return Result(True, "inventory", ["You are not carrying anything."])
        names = ", ".join(self._name(i) for i in self.state["inventory"])
        return Result(True, "inventory", [f"You are carrying: {names}."])

    def _do_hint(self, action: Action) -> Result:
        s = self.state
        for hint in self.config["hints"]:
            if hint.get("unless_solved") in s["solved"]:
                continue
            if hint.get("unless_discovered") in s["discovered"]:
                continue
            if hint.get("unless_inventory") in s["inventory"]:
                continue
            return Result(True, "hint", [f"Hint: {hint['text']}"])
        return Result(True, "hint", ["You have everything you need. Trust what you have found."])

    def _do_help(self, action: Action) -> Result:
        return Result(True, "help", [HELP_TEXT])

    def _do_meta(self, action: Action) -> Result:
        # Admin claims, prompt injection, requests for solutions.
        return Result(False, "rejected_meta", [
            "The room keeps its secrets. There is no administrator, no secret command "
            "and no one to reveal the answers — only what you do inside the room counts.",
        ])

    def _do_claim(self, action: Action) -> Result:
        solved = [self.config["puzzles"][p] for p in self.state["solved"]]
        progress = ("Completed so far: " + "; ".join(solved) + ".") if solved else "You have not solved any puzzle yet."
        return Result(False, "rejected_claim",
                      ["Saying something is done does not make it so. " + progress])

    def _do_unknown(self, action: Action) -> Result:
        return Result(False, "unknown_action", ["Nothing happens. " + HELP_TEXT])
