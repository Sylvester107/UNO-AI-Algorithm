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

1. Players (P)
P = {p0, p1, p2, p3}
Each player pi is a tuple:
pi = (Hi, Si, Bi)
Hi — hand of cards
Hi = {c1, c2, ..., c|Hi|}
Si — cumulative score (non-negative integer)

Bi — bot indicator
1 = bot
0 = MCTS agent

2. Deck (D)
D = (Ddraw, Ddiscard)
Draw pile
Ddraw = [c1, c2, ..., cn]   (top is the last element)
Discard pile
Ddiscard = [c1, ..., ck]   (top is ck)

3. Turn State (T)
T = (p_now, dir, c_now, c_last, v)
p_now — index of current player
{0, 1, 2, 3}
dir — play direction
+1 (clockwise)
-1 (counter-clockwise)
c_now — active color
{Blue, Green, Red, Yellow, Wild}

c_last — previous color before last change
same domain as c_now
v — command resolution flag
1 = top discard card's command is pending
0 = already resolved

4. Card Definition (C)
Each card is a tuple:
c = (color, type)
Colors
{Blue, Green, Red, Yellow, Wild}
Types
{0–9, Skip, Reverse, Draw Two, Wild, Draw Four}

5. Round (R)
R > 0
The current round number in the race to 500 points.

## Partial Observability
Player 0 (the MCTS agent) has full knowledge of its own hand:
H0   (all card identities known)

Opponent hands (players 1, 2, and 3)
Only the hand size is known:
|Hi|   for i ∈ {1, 2, 3}
The identity of the cards is hidden.
Inference of hidden hands is based on:
The cards in our hand H0

Cards visible in the discard pile:
Ddiscard

Cards revealed through draw actions
The remaining cards in the deck, computed relative to the initial 108-card Uno deck
This allows the agent to maintain a probabilistic belief state over the unknown hands of players 1–3.