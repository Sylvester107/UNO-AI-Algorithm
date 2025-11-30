"""
UNOState.py : this brigdes  uno.py game implementation and Transitions.py search space.

This module converts UnoCardGameState (from uno.py) to UNOState (from Transitions.py)
for use in search algorithms: MCTS in our case.

Dependencies:
- Transitions.py: Provides UNOState, UNOAction, ActionType, UNOObservation
- uno.py: Provides UnoCardGameState, UnoCard, UnoCardGamePlayer

The conversion handles:
1. Card representation: UnoCard -> string format (e.g., "Blue-5", "Wild-Draw Four")
2. Game state mapping: UnoCardGameState -> UNOState
3. Partial observability: Only Player 0's hand is fully known
4. Belief state: Probabilistic distribution over opponent hands
"""

from __future__ import annotations

from typing import Optional, Tuple
from uno import UnoCardGameState, UnoCard, UnoCardGamePlayer
from Transitions import UNOState


def card_to_string(card: UnoCard) -> str:
    """
    Convert UnoCard to string representation.
    
    Format: "Color-Type" (e.g., "Blue-5", "Red-Skip", "Wild-Draw Four")
    
    Args:
        card: UnoCard instance
        
    Returns:
        String representation of the card
    """
    return f"{card.cardcolor}-{card.cardtype}"


def string_to_card(card_str: str) -> UnoCard:
    """
    Convert string representation back to UnoCard.
    
    Args:
        card_str: String in format "Color-Type"
        
    Returns:
        UnoCard instance
    """
    parts = card_str.split("-", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid card string format: {card_str}")
    color, cardtype = parts
    return UnoCard(color, cardtype)


def game_state_to_uno_state(
    game: UnoCardGameState,
    player_index: int = 0,
    sum_plus: int = 0,
    skip: bool = False,
    uno: bool = False,
    belief: Optional[Tuple[Tuple[str, ...], ...]] = None
) -> UNOState:
    """
    Convert UnoCardGameState (from uno.py) to UNOState (from Transitions.py).
    
    This function bridges the game implementation with the search algorithm's
    state representation. It extracts the relevant information from the game
    state and formats it according to the UNOState structure.
    
    Args:
        game: UnoCardGameState instance from uno.py
        player_index: Index of the player whose perspective this state represents (default: 0)
        sum_plus: Accumulated draw cards from +2/+4 actions (default: 0)
        skip: Whether the next player should be skipped (default: False)
        uno: Whether UNO was called (default: False)
        belief: Probabilistic belief over opponent hands. If None, initialized as empty tuples.
                Format: Tuple of tuples, one per opponent, each containing possible card strings.
        
    Returns:
        UNOState instance ready for use in search algorithms
        
    Notes:
        - Player 0's hand is fully observable
        - Opponent hands are only partially observable (only sizes known)
        - The belief state should be maintained separately and updated based on observations
    """
    # Get Player 0's hand (fully observable)
    player_hand = game.players[player_index].hand
    hand_cards = tuple(card_to_string(card) for card in player_hand)
    
    # Get opponent hand sizes (only sizes are observable, not card identities)
    opponents_cards_num = tuple(
        len(game.players[i].hand) 
        for i in range(len(game.players)) 
        if i != player_index
    )
    
    # Get top card on discard pile
    if game.discardpile:
        cur_top = card_to_string(game.discardpile[-1])
    else:
        cur_top = None
    
    # Get current color
    cur_color = game.colornow if game.colornow else None
    
    # Convert clockwise boolean to direction integer
    # clockwise=True -> cur_dir=1, clockwise=False -> cur_dir=-1
    cur_dir = 1 if game.clockwise else -1
    
    # Initialize belief state if not provided
    if belief is None:
        # Create empty belief tuples for each opponent
        belief = tuple(tuple() for _ in range(len(game.players) - 1))
    
    return UNOState(
        cur_color=cur_color,
        cur_dir=cur_dir,
        cur_top=cur_top,
        skip=skip,
        sum_plus=sum_plus,
        hand_cards=hand_cards,
        opponents_cards_num=opponents_cards_num,
        belief=belief,
        uno=uno
    )


def get_playable_cards(game: UnoCardGameState, player_index: int = 0) -> list[str]:
    """
    Get list of playable cards for the given player in string format.
    
    A card is playable if:
    - It matches the current color (colornow)
    - It matches the top discard card's type
    - It is a Wild card (can be played at any time)
    
    Args:
        game: UnoCardGameState instance
        player_index: Index of the player (default: 0)
        
    Returns:
        List of playable card strings
    """
    if not game.discardpile:
        return []
    
    hand = game.players[player_index].hand
    top_card = game.discardpile[-1]
    mcolor = game.colornow
    mtype = top_card.cardtype
    
    playable = []
    for card in hand:
        if (card.cardcolor == mcolor or 
            card.cardtype == mtype or 
            card.cardcolor == 'Wild'):
            playable.append(card_to_string(card))
    
    return playable


def get_opponent_hand_sizes(game: UnoCardGameState, player_index: int = 0) -> Tuple[int, ...]:
    """
    Get the number of cards each opponent has.
    
    Args:
        game: UnoCardGameState instance
        player_index: Index of the current player (default: 0)
        
    Returns:
        Tuple of opponent hand sizes
    """
    return tuple(
        len(game.players[i].hand)
        for i in range(len(game.players))
        if i != player_index
    )


def update_belief_state(
    current_belief: Tuple[Tuple[str, ...], ...],
    observed_card: Optional[str] = None,
    opponent_drew: Optional[int] = None,
    opponent_played: Optional[str] = None,
    discard_pile: Optional[list[UnoCard]] = None,
    draw_pile_size: Optional[int] = None
) -> Tuple[Tuple[str, ...], ...]:
    """
    Update belief state based on observations.
    
    This is a placeholder for belief state updates. In a full implementation,
    this would use probabilistic inference to update the distribution over
    opponent hands based on:
    - Cards drawn from deck
    - Cards played by opponents
    - Cards visible in discard pile
    - Remaining deck composition
    
    Args:
        current_belief: Current belief state
        observed_card: Card that was observed (e.g., drawn or played)
        opponent_drew: Index of opponent who drew a card
        opponent_played: Card string that an opponent played
        discard_pile: Current discard pile (to infer what cards are out)
        draw_pile_size: Size of draw pile (for probability calculations)
        
    Returns:
        Updated belief state
    """
    # TODO: Implement probabilistic belief update
    # For now, return the current belief unchanged
    return current_belief


# Example usage:
if __name__ == "__main__":
    # Create a game state
    game = UnoCardGameState()
    
    # Convert to UNOState format
    uno_state = game_state_to_uno_state(game, player_index=0)
    
    print("UNOState created:")
    print(f"  Current color: {uno_state.cur_color}")
    print(f"  Current direction: {uno_state.cur_dir}")
    print(f"  Top card: {uno_state.cur_top}")
    print(f"  Hand size: {len(uno_state.hand_cards)}")
    print(f"  Opponent hand sizes: {uno_state.opponents_cards_num}")
    print(f"  Playable cards: {get_playable_cards(game)}")

