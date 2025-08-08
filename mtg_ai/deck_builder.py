from typing import List
from pathlib import Path
from dataclasses import dataclass

from .card_db import get_card_template_by_name
from .card import Card


@dataclass
class Deck:
    name: str
    cards: List[Card]


def _make_copies(template: dict, n: int) -> List[Card]:
    return [Card(template).copy() for _ in range(n)]


def load_deck_from_lines(lines: List[str], *, deck_name: str = "Unnamed") -> Deck:
    cards: List[Card] = []
    for raw in lines:
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        qty_str, *name_parts = raw.split()
        qty = int(qty_str)
        card_name = " ".join(name_parts)
        template = get_card_template_by_name(card_name)
        cards.extend(_make_copies(template, qty))
    if len(cards) < 60:
        raise ValueError("Deck must contain at least 60 cards.")
    return Deck(deck_name, cards)


def load_deck_from_file(path: Path) -> Deck:
    return load_deck_from_lines(path.read_text().splitlines(), deck_name=path.stem)
