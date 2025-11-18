## First we describe in few words how the UNO Game is Played, if you already know the game skip this section
The official Game rules description is taken from [The Rosetta UNO Game](https://rosettacode.org/wiki/Uno_(Card_Game)/Python)  This will serve as the foundation for our algorithm, our Gamestate description will be based on this code

=====
### Official Rules For Uno Card Game 

The aim of the game is to be the first player to score 500 points, achieved (usually over several rounds of play) by being the first to play all of one's own cards and scoring points for the cards still held by the other players.
The deck consists of 108 cards: four each of "Wild" and "Wild Draw Four", and 25 each of four colors (red, yellow, green, blue). Each color consists of one zero, two each of 1 through 9, and two each of "Skip", "Draw Two", and "Reverse". These last three types are known as "action cards".
To start a hand, seven cards are dealt to each player, and the top card of the remaining deck is flipped over and set aside to begin the discard pile. The player to the dealer's left plays first unless the first card on the discard pile is an action or Wild card (see below). On a player's turn, they must do one of the following:
*    play one card matching the discard in color, number, or symbol
*    play a Wild card, or a playable Wild Draw Four card (see restriction below)
*    draw the top card from the deck, then play it if possible
Cards are played by laying them face-up on top of the discard pile. Play proceeds clockwise around the table.
Action or Wild cards have the following effects:
| Card | Effect when played from hand | Effect as first discard |
| --- | --- | --- |
| Skip | Next player in sequence misses a turn | Player to dealer's left misses a turn |
| Reverse | Order of play switches directions (clockwise to counterclockwise, or vice versa) | Dealer plays first; play proceeds counterclockwise |
| Draw Two | Next player in sequence draws two cards and misses a turn | Player to dealer's left draws two cards and misses a turn |
| Wild | Player declares the next color to be matched; current color may be chosen | Player to dealer's left declares the first color to be matched and plays a card in it |
| Wild Draw Four | Player declares the next color to be matched; next player in sequence draws four | Return card to the deck, shuffle, flip top card to start discard pile |
A player who draws from the deck must either play or keep that card and may play no other card from their hand on that turn.
A player may play a Wild card at any time, even if that player has other playable cards.
A player may play a Wild Draw Four card only if that player has no cards matching the current color. The player may have cards of a different color matching the current number or symbol or a Wild card and still play the Wild Draw Four card.[5] A player who plays a Wild Draw Four may be challenged by the next player in sequence (see Penalties) to prove that their hand meets this condition.
If the entire deck is used during play, the top discard is set aside and the rest of the pile is shuffled to create a new deck. Play then proceeds normally.
It is illegal to trade cards of any sort with another player.
A player who plays their next-to-last-card must call "uno" as a warning to the other players.[6]
The first player to get rid of their last card ("going out") wins the hand and scores points for the cards held by the other players. Number cards count their face value, all action cards count 20, and Wild and Wild Draw Four cards count 50. If a Draw Two or Wild Draw Four card is played to go out, the next player in the sequence must draw the appropriate number of cards before the score is tallied.
The first player to score 500 points wins the game.

Penalties
=========
If a player does not call "uno" after laying down their next-to-last card and is caught before the next player in sequence takes a turn (i.e., plays a card from their hand, draws from the deck, or touches the discard pile), they must draw two cards as a penalty. If the player is not caught in time (subject to interpretation) or remembers to call "uno" before being caught, they suffer no penalty.
If a player plays a Wild Draw Four card, the following player can challenge its use. The player who used the Wild Draw Four must privately show their hand to the challenging player, in order to demonstrate that they had no matching colored cards. If the challenge is correct, then the challenged player draws four cards instead. If the challenge is wrong, then the challenger must draw six cards; the four cards they were already required to draw plus two more cards.



# Natural language description of GameState
A Gamestate Includes
- player Information: Each player's hands(cards), score and whether they are a bot( a bot in this case is the other players our algorithm will be playing with)

- Deck state: Draw pile(ordered List of cards), discard pile(top card is visible)

- Turn state: current player index (pnow), play direction(clockwise but can go anticlockwise), active color(colornow), last color(last color)

- Command state: whether the toop discard's command is still active(commandsvalid)

- Round state: current round number