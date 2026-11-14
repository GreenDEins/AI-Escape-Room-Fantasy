"""The procedural artwork must always be well-formed SVG, in every game state."""

import itertools
import sys
import xml.dom.minidom
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # project root, for ui/

from ui import art  # noqa: E402


@pytest.mark.parametrize("flags", list(itertools.product([False, True], repeat=4)))
def test_scene_is_valid_svg_in_every_state(flags):
    xml.dom.minidom.parseString(art.scene(*flags))


@pytest.mark.parametrize("name", art.CARDS)
def test_cards_are_valid_svg(name):
    xml.dom.minidom.parseString(art.card(name))


def test_scene_reflects_state():
    closed, opened = art.scene(), art.scene(door_open=True)
    assert "doorOpen" not in closed and "doorOpen" in opened
    assert "The seal begins with 47" not in closed
    assert "The seal begins with 47" in art.scene(message_revealed=True)


def test_unknown_card_raises():
    with pytest.raises(KeyError):
        art.card("dragon")
