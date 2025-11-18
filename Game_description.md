## First we describe in few words how the UNO Game is Played, if you already know the game skip this section
The official Game rules description is taken from [The Rosetta UNO Game](https://rosettacode.org/wiki/Uno_(Card_Game)/Python)  This will serve as the foundation for our algorithm, our Gamestate description will be based on this code

=====
### Official Rules For Uno Card Game 

**Objective**
- First player to score 500 points wins. Points are collected by going out (playing every card in your hand) and adding up the values of the cards left in opponents’ hands.

**Deck makeup**
- 108 cards total.
- Colors: red, yellow, green, blue; each color has one 0, two each of 1–9, two Skips, two Draw Twos, and two Reverses.
- Four Wild and four Wild Draw Four cards (colorless). Skip, Draw Two, Reverse, Wild, and Wild Draw Four are action cards.

**Starting a round**
- Deal seven cards to every player.
- Flip the top card of the remaining deck to seed the discard pile.
- Dealer’s left-hand neighbor normally starts, unless the flipped card is an action/Wild card—apply its “first discard” effect (see Action cards) before play begins.

**Turn options**
- Play a card that matches the discard pile’s top card by color, number, or symbol.
- Play any Wild (respecting the Wild Draw Four restriction).
- Draw the top card from the deck and immediately play it if legal; otherwise keep it and end the turn.
- Cards are discarded face-up; play proceeds clockwise unless affected by an action card.

**Action cards (hand play vs. first discard)**
- **Skip**: next player misses their turn; if flipped first, the player left of the dealer misses the opening turn.
- **Reverse**: change direction of play; if flipped first, the dealer plays first and direction becomes counterclockwise.
- **Draw Two**: next player draws two cards and skips their turn; if flipped first, the player left of the dealer draws two and skips.
- **Wild**: current player chooses the next color; if flipped first, the player left of the dealer chooses the opening color and plays a matching card.
- **Wild Draw Four**: current player chooses the next color and the next player draws four plus skips; if flipped first, return it to the deck, shuffle, and flip a new starting card.
A player who draws from the deck must either play or keep that card and may play no other card from their hand on that turn.

A player may play a Wild card at any time, even if that player has other playable cards.

A player may play a Wild Draw Four card only if that player has no cards matching the current color. The player may have cards of a different color matching the current number or symbol or a Wild card and still play the Wild Draw Four card. 

A player who plays a Wild Draw Four may be challenged by the next player in sequence (see Penalties) to prove that their hand meets this condition.

If the entire deck is used during play, the top discard is set aside and the rest of the pile is shuffled to create a new deck. Play then proceeds normally.

It is illegal to trade cards of any sort with another player.
A player who plays their next-to-last-card must call "uno" as a warning to the other players.

The first player to get rid of their last card ("going out") wins the hand and scores points for the cards held by the other players.
Number cards count their face value, all action cards count 20, and Wild and Wild Draw Four cards count 50. If a Draw Two or Wild Draw Four card is played to go out, the next player in the sequence must draw the appropriate number of cards before the score is tallied.
The first player to score 500 points wins the game.

Penalties
=========
If a player does not call "uno" after laying down their next-to-last card and is caught before the next player in sequence takes a turn (i.e., plays a card from their hand, draws from the deck, or touches the discard pile), they must draw two cards as a penalty. 

If the player is not caught in time (subject to interpretation) or remembers to call "uno" before being caught, they suffer no penalty.
If a player plays a Wild Draw Four card, the following player can challenge its use. 

The player who used the Wild Draw Four must privately show their hand to the challenging player, in order to demonstrate that they had no matching colored cards. If the challenge is correct, then the challenged player draws four cards instead. If the challenge is wrong, then the challenger must draw six cards; the four cards they were already required to draw plus two more cards.



# Natural language description of GameState
A Gamestate Includes
- player Information: Each player's hands(cards), score and whether they are a bot( a bot in this case is the other players our algorithm will be playing with)

- Deck state: Draw pile(ordered List of cards), discard pile(top card is visible)

- Turn state: current player index (pnow), play direction(clockwise but can go anticlockwise), active color(colornow), last color(last color)

- Command state: whether the toop discard's command is still active(commandsvalid)

- Round state: current round number
