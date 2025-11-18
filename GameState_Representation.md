# Natural language description of GameState
for detailed understanding of the Game check the Game_description.md

A Gamestate Includes
- player Information: Each player's hands(cards), score and whether they are a bot( a bot in this case is the other players our algorithm will be playing with)

- Deck state: Draw pile(ordered List of cards), discard pile(top card is visible)

- Turn state: current player index (pnow), play direction(clockwise but can go anticlockwise), active color(colornow), last color(last color)

- Command state: whether the toop discard's command is still active(commandsvalid)

- Round state: current round number