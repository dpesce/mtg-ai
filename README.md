# MTG AI engine

An experimental AI-driven engine for simulating games of **Magic: The Gathering**, written in Python.  
The project focuses on rule enforcement, card logic, game state tracking, and AI training via self-play.

[![CI](https://github.com/dpesce/mtg-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/dpesce/mtg-ai/actions)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
[![codecov](https://codecov.io/github/dpesce/mtg-ai/branch/master/graph/badge.svg?token=AILG4KS1FD)](https://codecov.io/github/dpesce/mtg-ai)

---

## Features

- Turn-based structure with phase progression
- Mana cost parsing and payment logic
- Creature summoning, tapping, attacking
- Summoning sickness and attack logic
- Card data compatible with [MTGJSON](https://github.com/mtgjson/mtgjson)

---

## Requirements

- Python 3.11+

Install dependencies:
```
pip install -r requirements.txt
```

---

## Development Setup

Clone the repo and create a virtual environment:

```
git clone https://github.com/dpesce/mtg-ai.git
cd mtg-ai
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### CoreSubset data

Unit tests and CI use a tiny slice of MTGJSON instead of the 400 MB *AllPrintings.json*. If you plan to run local demos or add new cards:

```
# 1) Download the full MTGJSON dump (ignored by Git)
curl -L https://mtgjson.com/api/v5/AllPrintings.json -o data/AllPrintings.json

# 2) Generate / refresh the slim CoreSubset.json
python tools/make_core_subset.py
```

- `tools/make_core_subset.py` copies exactly one printing of every card listed in its `NEEDED_NAMES` set into `data/CoreSubset.json` (≈ few hundred KB).
- `CoreSubset.json` is committed so CI and tests start instantly.
- When you add new card names (e.g. in a decklist), append them to `NEEDED_NAMES`, rerun the script, and commit the updated subset.

---

## High-level roadmap

✅ Basic game mechanics: lands, creatures, combat

✅ Mana cost enforcement

⬜ Priority passing, stack, instants/sorceries

⬜ Basic AI agents for self-play

⬜ Expand card pool beyond test stubs

⬜ Neural network integration (RL, supervised fine-tuning)

⬜ Match simulation for training datasets

