from __future__ import annotations
from functools import lru_cache
import json
from pathlib import Path
from typing import Dict, Any, cast

# --------------------------------------------------------------
# Resolve a JSON path in this priority:
#   1) <repo_root>/cards/CoreSubset.json
#   2) <repo_root>/cards/AllPrintings.json
#   3) <package_dir>/cards/CoreSubset.json
#   4) <package_dir>/cards/AllPrintings.json
#   else raise FileNotFoundError with guidance.
# --------------------------------------------------------------
_pkg_dir = Path(__file__).resolve().parent               # mtg_ai/
_root_dir = _pkg_dir.parent                               # project root
_search_dirs = [_root_dir / "cards", _pkg_dir / "cards"]

_JSON_PATH: Path | None = None
for directory in _search_dirs:
    core = directory / "CoreSubset.json"
    full = directory / "AllPrintings.json"
    if core.exists():
        _JSON_PATH = core
        break
    if full.exists():
        _JSON_PATH = full
        break

if _JSON_PATH is None:
    raise FileNotFoundError(
        "Neither CoreSubset.json nor AllPrintings.json found in "
        f"{_search_dirs}.  Download AllPrintings or run "
        "`python tools/make_core_subset.py`."
    )

# --------------------------------------------------------------


@lru_cache(maxsize=1)
def load_raw_json() -> Dict[str, Any]:
    path = cast(Path, _JSON_PATH)
    with path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return cast(Dict[str, Any], raw)


@lru_cache(maxsize=1)
def build_name_index() -> Dict[str, Dict[str, Any]]:
    """
    Returns {card_name.lower(): canonical_printing_dict}
    For duplicates we pick the first printing we encounter.
    """
    raw = load_raw_json()
    index: Dict[str, Dict[str, Any]] = {}
    for set_data in raw["data"].values():
        for card in set_data["cards"]:
            name_key = card["name"].lower()
            index.setdefault(name_key, card)   # keep earliest
    return index


def get_card_template_by_name(name: str) -> Dict[str, Any]:
    idx = build_name_index()
    key = name.lower()
    if key not in idx:
        raise KeyError(f"Card “{name}” not found in DB.")
    return idx[key]
