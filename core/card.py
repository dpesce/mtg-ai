from typing import Optional, List, Dict


class Card:
    def __init__(self, card_data: Dict):

        self.card_data = card_data

        # Required fields from MTGJSON structure
        self.uuid: str = card_data.get("uuid")
        self.name: str = card_data.get("name")
        self.types: List[str] = card_data.get("types", [])
        self.subtypes: List[str] = card_data.get("subtypes", [])
        self.mana_cost: Optional[str] = card_data.get("manaCost")
        self.converted_mana_cost: float = card_data.get("convertedManaCost", 0)
        self.colors: List[str] = card_data.get("colors", [])
        self.power: Optional[int] = self._safe_int(card_data.get("power"))
        self.toughness: Optional[int] = self._safe_int(card_data.get("toughness"))
        self.text: str = card_data.get("text", "")
        self.rarity: Optional[str] = card_data.get("rarity")

        # Runtime properties (not in MTGJSON)
        self.tapped: bool = False
        self.summoning_sick: bool = True
        self.zone: str = (
            "library"  # Possible: library, hand, battlefield, graveyard, exile
        )

    def copy(self) -> "Card":
        return Card(self.card_data)

    def _safe_int(self, val):
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    def is_creature(self) -> bool:
        return "Creature" in self.types

    def is_land(self) -> bool:
        return "Land" in self.types

    def __repr__(self):
        return f"<Card {self.name} ({self.mana_cost})>"
