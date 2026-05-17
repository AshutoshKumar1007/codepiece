# Codepiece Game Rules and Engine Notes

## Overview
Codepiece is a 4-player, 2-team trick-taking game with two phases:
1. Bidding phase
2. Trick-play phase

Teams are fixed by seat parity:
- Team 0: players `0` and `2`
- Team 1: players `1` and `3`

A standard 52-card deck is used and each player gets 13 cards.

## Phase 1: Bidding
- Dealer deals 13 cards to each player.
- Bidding starts from the player to the left of the dealer and proceeds clockwise.
- Bidding ends when the dealer has had their turn (after one complete round).
- Legal bids are `8` to `13`.
- `7` is not a regular bid. It is only used as a default fallback.
- On a turn, a player can:
  - `pass`, or
  - place a higher bid than the current highest bid.
- A player may outbid even a teammate.

Bidding ends as follows:
- If at least one bid was made: the highest bidder wins after dealer's turn.
- If all four players pass in the first round: starter (left of dealer) is forced to accept default bid `7`.

The final highest bidder becomes the bidding side leader and chooses trump suit.

## Trump Selection
- The winning bidder chooses one trump suit from `S`, `H`, `D`, `C`.
- Opposite team becomes the defending team.

## Phase 2: Trick Play
- Trick play starts with the winning bidder leading the first trick.
- The winner of each trick leads the next trick.
- Standard follow-suit rule:
  - If player has cards of led suit, they must play that suit.
  - If not, they may play any suit, including trump.

### Mandatory Overtake Rule
When it is your turn in a trick:
- If the currently winning card belongs to the opponent team, and
- you have at least one legal card that can beat it (following suit rules),
- then you MUST play a beating card.

Important clarifications:
- If your teammate is currently winning the trick, you may play any otherwise legal card.
- If you cannot beat the opponent's winning card (even after considering trump), you play any legal card following the suit rules.
- Legal cards are determined first by the follow-suit rule, then the mandatory overtake rule is applied within those legal cards.

## Trick Winner Logic
Within a trick:
- Higher rank wins when comparing cards of the same suit.
- Any trump beats non-trump cards.
- If no trump is involved, highest card of led suit wins.

Rank order is:
`2 < 3 < 4 < 5 < 6 < 7 < 8 < 9 < T < J < Q < K < A`

## End Conditions
Game can end in two ways:
1. Normal end: all 13 tricks completed.
2. Early end: defenders secure enough tricks to make bid impossible.

If winning bid is `B`, bidding side must win at least `B` tricks.
Defenders succeed once they reach `14 - B` tricks.

So if bid is `8`, defenders need `6` tricks to stop bidding side.

## Scoring/Penalty (Current Engine Version)
- If defenders succeed: bidding team gets penalty `2 * bid`.
- If bidding team succeeds: defending team gets penalty `bid`.

Engine payoffs are assigned per player by team:
- Positive for team that succeeds in objective.
- Negative for team that fails.

## Action Format in Engine
Actions are plain strings:
- Bidding: `pass`, `bid_8` ... `bid_13`
- Trump: `trump_S`, `trump_H`, `trump_D`, `trump_C`
- Trick play: card codes like `AS`, `TD`, `7H`

## Exposed Game State (per player)
State includes:
- current phase
- current player id
- own hand
- legal actions
- bid/trump info
- tricks won by both teams
- current trick cards
- bidding history
- terminal winner/payoff when game is over

## Clarifications Needed (Potential Ambiguities)
Please confirm these if you want strict official behavior:
1. All-pass handling: implemented as forced default `7` for first bidder after all 4 pass.
2. Bidding closure: implemented to end after dealer's turn (one complete round).
3. Mandatory overtake applies only when opponent currently leads trick and overtaking is possible.
4. Scoring is single-round signed payoff based on penalty amount, not cumulative match scoring.

## Code Structure
The game implementation is modular:

### Core Files
- `game.py`: Main game engine with phase management
- `judger.py`: Legal action computation and payoff calculation
- `dealer.py`: Card dealing and shuffling
- `player.py`: Player state management

### Utils Module
- `utils/card_utils.py`: Card encoding/decoding and comparison functions
  - 52-dimensional one-hot encoding for RL
  - String representations for debugging
  - Card beating logic
- `utils/actions.py`: Action classes for different phases
  - `BidAction`: Bidding phase actions
  - `TrumpAction`: Trump selection actions
  - `PlayAction`: Card play actions

### Key Features
- **Dual Representation**: Cards are tracked in both string format (for debugging) and one-hot encoding (for RL efficiency)
- **Modular Actions**: Separate action classes for each game phase ensure clean separation of concerns
- **Optimized Legal Moves**: Efficient computation of legal actions with proper constraint enforcement
- **Team-Aware Logic**: Trick resolution tracks winning team to properly implement mandatory overtake rule

<!-- If any of these should be changed, only small edits in `game.py` and `judger.py` are needed. -->