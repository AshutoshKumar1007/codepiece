# Codepiece

4-player, 2-team trick-taking card game engine with an RL environment wrapper.

---

## Rules (short version)

- 2 teams: `{P0, P2}` vs `{P1, P3}` — standard 52-card deck, 13 cards each
- **Bidding:** players bid (8–13) or pass. Highest bidder picks trump. All-pass forces a bid of 7.
- **Trick play:** bidding team must win at least `bid` tricks. Defenders need `14 - bid` to stop them.
- **Mandatory overtake:** if an opponent is currently winning the trick and you can beat them, you must.

Full rules and edge cases in [`engine/README.md`](engine/README.md).

---

## Structure

```
codepiece/
├── engine/       # core game logic (Game, Judger, Round, Dealer, Player, utils)
├── envs/         # RLCard-style RL environment wrapper
└── agents/       # RandomAgent, HeuristicAgent, HumanAgent
```

---

## Install

```bash
pip install git+https://YOUR_TOKEN@github.com/YOU/codepiece.git
```

---

## Quick Start

```python
from engine.game import CodePieceGame
from agents import RandomAgent

game = CodePieceGame()
game.configure(seed=42)
state, pid = game.init_game()

agents = [RandomAgent(i) for i in range(4)]

while not game.is_over():
    action = agents[pid].step(state)
    state, pid = game.step(action)

print(game.get_payoffs())
```

---

## Status

- [x] Game engine
- [x] RL environment wrapper (`CodePieceEnv`)
- [x] Random + Heuristic agents
- [ ] RL agent (WIP)