from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, Set

ROOT = Path(__file__).resolve().parents[1]          # repo root
RAW = ROOT / "cards" / "AllPrintings.json"           # huge file (git-ignored)
OUT = ROOT / "cards" / "CoreSubset.json"             # tiny file (checked in)

# ── 1) Add or remove card names here ─────────────────────────────────────────
NEEDED_NAMES: Set[str] = {
    "Forest", "Mountain",
    "Grizzly Bears", "Runeclaw Bear", "Raging Goblin",
    "Goblin Raider", "Hill Giant", "Gray Ogre",
    "Centaur Courser", "Nessian Courser", "Craw Wurm",
    "Territorial Baloth", "Kalonian Tusker", "Elvish Warrior",
    "Coal Stoker", "Flame Spirit", "Vulshok Berserker",
    "Ember Beast", "Ironroot Warlord",
    "Giant Growth", "Pillage",
}
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    raw: Dict[str, Any] = json.loads(RAW.read_text(encoding="utf-8"))
    remaining: Set[str] = {n.lower() for n in NEEDED_NAMES}
    slim: Dict[str, Any] = {"data": {}}

    # Iterate sets in alphabetic order for determinism
    for set_code in sorted(raw["data"].keys()):
        if not remaining:
            break  # found them all
        set_blob = raw["data"][set_code]
        kept_cards = []
        for card in set_blob["cards"]:
            name_key = card["name"].lower()
            if name_key in remaining:
                kept_cards.append(card)
                remaining.remove(name_key)
        if kept_cards:
            slim["data"][set_code] = {
                "code": set_code,
                "name": set_blob["name"],
                "cards": kept_cards,
            }

    if remaining:
        raise RuntimeError(
            f"These cards were not found in AllPrintings.json: {sorted(remaining)}"
        )

    OUT.write_text(json.dumps(slim, indent=2))
    card_count = sum(len(s["cards"]) for s in slim["data"].values())
    print(f"Wrote {OUT.relative_to(ROOT)} with {card_count} cards "
          f"({OUT.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
