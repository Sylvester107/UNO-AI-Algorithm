# Natural language description of GameState
for detailed understanding of the Game check the Game_description.md

A Gamestate Includes
- player Information: Each player's hands(cards), score and whether they are a bot( a bot in this case is the other players our algorithm will be playing with)

- Deck state: Draw pile(ordered List of cards), discard pile(top card is visible)

- Turn state: current player index (pnow), play direction(clockwise but can go anticlockwise), active color(colornow), last color(last color)

- Command state: whether the toop discard's command is still active(commandsvalid)

- Round state: current round number

# Mathematical description of Gamestate

# Natural language description of GameState
for detailed understanding of the Game check the Game_description.md

A Gamestate Includes
- player Information: Each player's hands(cards), score and whether they are a bot( a bot in this case is the other players our algorithm will be playing with)

- Deck state: Draw pile(ordered List of cards), discard pile(top card is visible)

- Turn state: current player index (pnow), play direction(clockwise but can go anticlockwise), active color(colornow), last color(last color)

- Command state: whether the toop discard's command is still active(commandsvalid)

- Round state: current round number

# Mathematical description of Gamestate

Let \( s = (P, D, T, C, R) \) where:

- **Players \(P\)**: \( P = \{p_0, p_1, p_2, p_3\} \). Each player \( p_i = (H_i, S_i, B_i) \) with:
  - \( H_i = \{c_1, c_2, \dots, c_{|H_i|}\} \): hand (set or multiset) of Uno cards.
  - \( S_i \in \mathbb{Z}_{\ge 0} \): cumulative score.
  - \( B_i \in \{0, 1\} \): bot indicator (1 for bot, 0 for the MCTS agent).
- **Deck \(D\)**: \( D = (D_{\text{draw}}, D_{\text{discard}}) \).
  - \( D_{\text{draw}} = [c_1, c_2, \dots, c_n] \): ordered draw pile (top is the last element).
  - \( D_{\text{discard}} = [c_1, \dots, c_k] \): discard pile (top card is \( c_k \)).
- **Turn state \(T\)**: \( T = (p_{\text{now}}, d, c_{\text{now}}, c_{\text{last}}, v) \).
  - \( p_{\text{now}} \in \{0, 1, 2, 3\} \): index of the player to act.
  - \( d \in \{+1, -1\} \): play direction (clockwise/counter-clockwise).
  - \( c_{\text{now}} \in \{\text{Blue}, \text{Green}, \text{Red}, \text{Yellow}, \text{Wild}\} \): active color.
  - \( c_{\text{last}} \in \{\text{Blue}, \text{Green}, \text{Red}, \text{Yellow}, \text{Wild}\} \): previous color before the latest change.
  - \( v \in \{0, 1\} \): whether the command on the top discard is still pending (1) or already resolved (0).
- **Card definition \(C\)**:
  - Each card \( c = (\text{color}, \text{type}) \) where \( \text{color} \in \{\text{Blue}, \text{Green}, \text{Red}, \text{Yellow}, \text{Wild}\} \) and \( \text{type} \in \{0-9, \text{Skip}, \text{Reverse}, \text{Draw Two}, \text{Wild}, \text{Draw Four}\} \).
- **Round \(R\)**: \( R \in \mathbb{Z}_{>0} \) is the current round number in the race to 500 points.

## Partial Observability

- Player 0 (the MCTS agent) knows \( H_0 \) exactly.
- For opponents \( i \in \{1,2,3\} \), only \( |H_i| \) (hand size) is known; card identities are hidden.
- Hidden hands can be inferred probabilistically using:
  - Cards currently in our hand \( H_0 \).
  - Cards visible in \( D_{\text{discard}} \) and any revealed draws.
  - The remaining unseen cards relative to the initial 108-card deck composition.