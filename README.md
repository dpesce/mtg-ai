# MTG AI engine

An experimental AI-driven engine for simulating games of **Magic: The Gathering**, written in Python.  
The project focuses on rule enforcement, card logic, game state tracking, and AI training via self-play.

[![CI](https://github.com/dpesce/mtg-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/dpesce/mtg-ai/actions)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

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
- No third-party libraries required (yet)

Install dependencies (if any are added later):
```
pip install -r requirements.txt
```

---

## High-level roadmap

✅ Basic game mechanics: lands, creatures, combat

✅ Mana cost enforcement

⬜ Priority passing, stack, instants/sorceries

⬜ Basic AI agents for self-play

⬜ Expand card pool beyond test stubs

⬜ Neural network integration (RL, supervised fine-tuning)

⬜ Match simulation for training datasets

