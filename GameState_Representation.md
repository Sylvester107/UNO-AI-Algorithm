# Game State Representation

> For detailed understanding of the game, check `Game_description.md`

## Natural Language Description

A game state includes the following components:

- **Player Information**: Each player's hand (cards), score, and whether they are a bot (the other players our algorithm will be playing with)

- **Deck State**: Draw pile (ordered list of cards), discard pile (top card is visible)

- **Turn State**: Current player index (`pnow`), play direction (clockwise but can go anticlockwise), active color (`colornow`), last color (`lastcolor`)

- **Command State**: Whether the top discard's command is still active (`commandsvalid`)

- **Round State**: Current round number

---

## Mathematical Description

### 1. Players (P)

\[ P = \{p_0, p_1, p_2, p_3\} \]

Each player \( p_i \) is a tuple:

\[ p_i = (H_i, S_i, B_i) \]

- **\( H_i \)**: Hand of cards
  \[ H_i = \{c_1, c_2, \ldots, c_{|H_i|}\} \]

- **\( S_i \)**: Cumulative score (non-negative integer)
  \[ S_i \in \mathbb{Z}_{\geq 0} \]

- **\( B_i \)**: Bot indicator
  - \( B_i = 1 \): Bot player
  - \( B_i = 0 \): MCTS agent (Player 0)

---

### 2. Deck (D)

\[ D = (D_{\text{draw}}, D_{\text{discard}}) \]

- **Draw Pile** \( D_{\text{draw}} \):
  \[ D_{\text{draw}} = [c_1, c_2, \ldots, c_n] \]
  *(Note: Top card is the last element)*

- **Discard Pile** \( D_{\text{discard}} \):
  \[ D_{\text{discard}} = [c_1, \ldots, c_k] \]
  *(Note: Top card is \( c_k \))*

---

### 3. Turn State (T)

\[ T = (p_{\text{now}}, d, c_{\text{now}}, c_{\text{last}}, v) \]

- **\( p_{\text{now}} \)**: Index of current player
  \[ p_{\text{now}} \in \{0, 1, 2, 3\} \]

- **\( d \)**: Play direction
  - \( d = +1 \): Clockwise
  - \( d = -1 \): Counter-clockwise

- **\( c_{\text{now}} \)**: Active color
  \[ c_{\text{now}} \in \{\text{Blue}, \text{Green}, \text{Red}, \text{Yellow}, \text{Wild}\} \]

- **\( c_{\text{last}} \)**: Previous color before last change
  \[ c_{\text{last}} \in \{\text{Blue}, \text{Green}, \text{Red}, \text{Yellow}, \text{Wild}\} \]

- **\( v \)**: Command resolution flag
  - \( v = 1 \): Top discard card's command is pending
  - \( v = 0 \): Command already resolved

---

### 4. Card Definition (C)

Each card is a tuple:

\[ c = (\text{color}, \text{type}) \]

- **Colors**:
  \[ \text{color} \in \{\text{Blue}, \text{Green}, \text{Red}, \text{Yellow}, \text{Wild}\} \]

- **Types**:
  \[ \text{type} \in \{0\text{--}9, \text{Skip}, \text{Reverse}, \text{Draw Two}, \text{Wild}, \text{Draw Four}\} \]

---

### 5. Round (R)

\[ R \in \mathbb{Z}_{> 0} \]

The current round number in the race to 500 points.

---

## Partial Observability

### Known Information

**Player 0 (MCTS agent)** has full knowledge of its own hand:
- \( H_0 \): All card identities are known

**Opponent hands** (players 1, 2, and 3):
- Only hand size is known: \( |H_i| \) for \( i \in \{1, 2, 3\} \)
- Card identities are **hidden**

### Inference Sources

Hidden hands can be inferred probabilistically using:

1. **Cards in our hand**: \( H_0 \)
2. **Cards visible in discard pile**: \( D_{\text{discard}} \)
3. **Cards revealed through draw actions**: Observable draws
4. **Remaining deck composition**: Computed relative to the initial 108-card Uno deck

This allows the agent to maintain a **probabilistic belief state** over the unknown hands of players 1–3.