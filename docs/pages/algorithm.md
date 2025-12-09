---
layout: default
title: Algorithm design
nav_order: 3
---

## Design idea
Our Algorithm uses the following core concepts

- **state representation**: How the game state is encoded
- **action policy**: How the next move is selected
- **Seearch or learning method**: MCTS

## Architecture
### 1. input representation
State = players, deck (draw/discard), turn data (current player, direction, active/last color), command flag (whether the top discard’s effect is still pending), and round number.
Players carry hand, cumulative score, and a bot flag (Player 0 is the MCTS agent).
Cards are (color, type) with standard UNO colors and types.

**Partial observability:** Player 0 knows its own hand; opponents’ hand sizes only. Beliefs come from known cards (own hand, discard pile) and observed draws relative to the 108-card deck.

### Transition

A **transition** applies a chosen action to the current UNO state to produce the next state.
**Actions include:** playing a card, choosing a color after a wild, adding draw penalties (+2/+4), skipping, reversing direction, drawing a card, and declaring UNO.

Playing a card updates the top discard, sets the active color (unless it’s a wild), triggers its effect (skip, reverse, draw penalties), and advances turn order according to the effect and direction.
Choosing a color finalizes a wild play; draw actions add the drawn card to your hand; skip/reverse/draw penalties adjust who moves next and how many cards must be taken.
An **observation** is the “what we can see” snapshot after a transition: agent's hand, opponents’ hand sizes (just counts), current top card/color, direction, skip status, accumulated draw penalties, whether UNO was called, and who acted. This fuels belief updates about hidden opponent cards.

### Decision logic
- Build a search tree from the current state. Each edge is an action; each node is a possible game state.
- Simulate many playouts:
**Selection:** Follow the tree along the best-looking child nodes (balancing “tried and good” vs “not tried yet”).
**Expansion:** When a node still has untried actions for Player 0, pick one, apply a transition, and add the resulting state as a child.

**Rollout:** From there, play out the game randomly (within rules) until a depth limit or someone wins. For opponents, sample likely hands from your belief and make plausible plays or draws.
Belief updates: After each simulated action, form an observation (what was seen) and update the guessed distributions of opponent hands.

**Backpropagation:** If Player 0 wins the simulated playout, propagate that success back up the path; otherwise propagate failure. Discount future rewards to favor nearer wins.
After many simulations, pick the action from the root whose child was visited the most. This is the decision the MCTS recommends, using the accumulated experience of simulated games and belief updates about hidden cards.

### 3. Training our simulation

**number of simulations**
The MCTS player runs a fixed number of playouts each time it must choose a move. That count is `num_simulations`, defaulting to 500 (configurable when constructing MCTSPlayer). Every decision cycle it does up to that many simulated games from the current state to estimate action quality.

**Heuristics**
- **Tree selection heuristic (UCB1):** When walking down the search tree, it balances “how good” vs. “how unexplored” each child is. This is controlled by `c_param` (default 1.4). Higher values explore more; lower values exploit more.

- **Expansion Policy:** Rollout/playout policy:
For Player 0 turns, it samples a legal action uniformly at random (no domain-specific scoring during rollout). For opponent turns, it samples an opponent hand from the belief particles and then:
With 80% chance, plays a random playable card (if any); otherwise draws.
If a wild is played, it picks a random color.
Drawing a card in rollouts is stubbed as “draw a random color/type,” not sampled from the exact remaining deck.

- **Belief Handling** : Belief handling (partial observability): Before each playout, it picks one belief particle (a hypothetical deal of opponent cards). After each simulated action, it forms an observation (what would be visible: top card, color, who acted, whether someone drew, etc.) and updates the belief set to stay consistent with observed info.

- **Depth Limited:**  Rollouts stop at max_depth (default 20). If no win/loss is reached by then, that playout counts as a failure for Player 0.

- **Reward function:**
The rollout returns 1.0 if Player 0 wins (empties its hand) during the simulated playout; otherwise 0.0. Backpropagation discounts that reward up the path by gamma (default 0.99), so earlier wins carry slightly more weight than far-future wins.
Final move choice: after all simulations, it picks the root child that was visited the most, reflecting the action that looked most promising across all playouts.

### 4. Output

The MCTS search returns a recommended action for Player 0. The current implementation returns a single `UNOAction` (or None), chosen as the root child with the most visits.

The action includes:
Action type (play a card, draw, choose color, etc.)
Card details (if playing a card)
Color choice (if choosing color for a wild)
Draw penalty value (if applicable)