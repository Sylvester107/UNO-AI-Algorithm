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

from typing import Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from uno import UnoCardGameState, UnoCard, UnoCardGamePlayer

from Transitions import UNOState


def card_to_string(card) -> str:
    """
    Convert UnoCard to string representation.
    
    Format: "Color-Type" (e.g., "Blue-5", "Red-Skip", "Wild-Draw Four")
    
    Args:
        card: UnoCard instance (or any object with cardcolor and cardtype attributes)
        
    Returns:
        String representation of the card
    """
    return f"{card.cardcolor}-{card.cardtype}"


def string_to_card(card_str: str):
    """
    Convert string representation back to UnoCard.
    
    Args:
        card_str: String in format "Color-Type"
        
    Returns:
        UnoCard instance
    """
    # Import here to avoid circular dependency
    from uno import UnoCard
    parts = card_str.split("-", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid card string format: {card_str}")
    color, cardtype = parts
    return UnoCard(color, cardtype)


def game_state_to_uno_state(
    game,
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


def get_playable_cards(game, player_index: int = 0) -> list[str]:
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


def get_opponent_hand_sizes(game, player_index: int = 0) -> Tuple[int, ...]:
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


def get_all_uno_cards() -> list[str]:
    """
    Get a list of all possible UNO cards in the deck.
    
    Returns:
        List of all card strings in format "Color-Type"
    """
    colors = ['Blue', 'Green', 'Red', 'Yellow']
    types = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'Skip', 'Draw Two', 'Reverse']
    wild_types = ['Wild', 'Draw Four']
    
    cards = []
    # Each color has: 1 zero, 2 of each 1-9, 2 of each action card
    for color in colors:
        cards.append(f"{color}-0")  # One zero
        for t in types[1:]:  # 1-9 and action cards
            cards.extend([f"{color}-{t}", f"{color}-{t}"])  # Two of each
    
    # Wild cards: 4 Wild, 4 Wild Draw Four
    for _ in range(4):
        cards.append("Wild-Wild")
        cards.append("Wild-Draw Four")
    
    return cards


def initialize_belief_particles(
    player_0_hand: Tuple[str, ...],
    opponents_cards_num: Tuple[int, ...],
    observed_discard_cards: Optional[Tuple[str, ...]] = None,
    num_particles: int = 100
) -> list[Tuple[Tuple[str, ...], ...]]:
    """
    Initialize belief particles for POMDP.
    
    IMPORTANT: Player 0 does NOT know what's in the draw pile!
    We can only use:
    - Player 0's known hand
    - Cards observed in discard pile (only top is visible, but we track what we've seen)
    - Opponent hand sizes
    
    We sample from the full UNO deck, excluding only what we KNOW:
    - Cards in Player 0's hand
    - Cards we've observed being played (in discard pile)
    
    Args:
        player_0_hand: Player 0's hand (known cards to exclude)
        opponents_cards_num: Number of cards each opponent has
        observed_discard_cards: Cards Player 0 has observed being played (from observation)
        num_particles: Number of particles to generate
        
    Returns:
        List of particles, each particle is a tuple of opponent hands
    """
    import random
    
    # Get all possible cards in a UNO deck
    all_cards = get_all_uno_cards()
    
    # Cards that Player 0 KNOWS about (in their hand or observed in discard)
    known_cards = list(player_0_hand)
    if observed_discard_cards:
        known_cards.extend(observed_discard_cards)
    
    # For each particle, we sample from the full deck
    # We don't know what's in the draw pile, so we sample uniformly
    # from all cards, excluding only what we know
    particles = []
    for _ in range(num_particles):
        # Create a deck excluding known cards
        # Note: We remove one instance of each known card (cards can appear multiple times)
        deck_copy = all_cards.copy()
        for card in known_cards:
            if card in deck_copy:
                deck_copy.remove(card)
        
        # Shuffle the remaining cards
        random.shuffle(deck_copy)
        
        # Deal cards to opponents (sample without replacement)
        opponent_hands = []
        card_idx = 0
        total_cards_needed = sum(opponents_cards_num)
        
        # If we don't have enough cards, pad with random cards from full deck
        # (this handles the case where we've seen many cards)
        if len(deck_copy) < total_cards_needed:
            # Add more cards from full deck (allowing duplicates of unknown cards)
            while len(deck_copy) < total_cards_needed:
                # Sample a card that's not in known cards
                candidate = random.choice(all_cards)
                if candidate not in known_cards:
                    deck_copy.append(candidate)
        
        for num_cards in opponents_cards_num:
            hand = tuple(deck_copy[card_idx:card_idx + num_cards])
            opponent_hands.append(hand)
            card_idx += num_cards
        
        particles.append(tuple(opponent_hands))
    
    return particles


def update_belief_state(
    current_belief_particles: list[Tuple[Tuple[str, ...], ...]],
    observation,  # UNOObservation - use type annotation without import to avoid circular dependency
    player_0_hand: Tuple[str, ...],
    opponents_cards_num: Tuple[int, ...]
) -> list[Tuple[Tuple[str, ...], ...]]:
    """
    Update belief state particles based on observations using particle filtering.
    
    This implements a proper particle filter for POMDP:
    1. When opponent plays a card: filter particles where that opponent has that card
    2. When opponent draws: update particles to reflect new hand size
    3. Resample particles to maintain diversity
    
    IMPORTANT: This is a "basic" implementation because:
    - It doesn't consider opponent strategies (e.g., opponents prefer certain cards)
    - It doesn't use sophisticated probability distributions
    - It doesn't consider card frequencies in the deck
    - A more advanced implementation would:
      * Weight particles by likelihood based on opponent behavior
      * Use importance sampling
      * Consider card probabilities based on deck composition
      * Learn opponent strategies from history
    
    Args:
        current_belief_particles: Current belief particles
        observation: UNOObservation containing all observable information
        player_0_hand: Player 0's current hand
        opponents_cards_num: Current number of cards each opponent has
        
    Returns:
        Updated belief particles
    """
    import random
    # Import here to avoid circular dependency
    try:
        from Transitions import UNOObservation, ActionType
        import actions as UNOActions
    except ImportError:
        # If import fails, use string comparison
        ActionType = None
        UNOActions = None
    
    if not current_belief_particles:
        # Initialize if empty
        return initialize_belief_particles(
            player_0_hand, 
            opponents_cards_num, 
            observation.observed_discard_cards,
            num_particles=100
        )
    
    updated_particles = []
    
    # Filter particles based on observations
    for particle in current_belief_particles:
        is_valid = True
        
        # Check 1: Opponent hand sizes must match
        if len(particle) != len(opponents_cards_num):
            is_valid = False
        else:
            for i, (opp_hand, expected_size) in enumerate(zip(particle, opponents_cards_num)):
                if len(opp_hand) != expected_size:
                    is_valid = False
                    break
        
        # Check 2: If opponent played a card, that opponent must have it
        if is_valid and ActionType and observation.action_taken.type == ActionType.V_CARD:
            if observation.action_player > 0:  # Opponent played
                opponent_idx = observation.action_player - 1  # Convert to opponent index
                played_card = observation.action_taken.card
                
                if opponent_idx < len(particle):
                    if played_card not in particle[opponent_idx]:
                        # This particle is inconsistent - opponent played a card they don't have
                        is_valid = False
                    else:
                        # Remove the played card from this particle's hand
                        # (for next iteration, we'll need to update the particle)
                        pass
        
        # Check 3: If opponent drew, their hand size should increase
        # (This is already checked above via opponents_cards_num)
        
        if is_valid:
            updated_particles.append(particle)
    
    # Update particles: remove played cards from opponent hands
    if ActionType and observation.action_taken.type == ActionType.V_CARD and observation.action_player > 0:
        opponent_idx = observation.action_player - 1
        played_card = observation.action_taken.card
        updated_particles = [
            tuple(
                tuple(c for c in hand if c != played_card) if i == opponent_idx else hand
                for i, hand in enumerate(particle)
            )
            for particle in updated_particles
        ]
    
    # If too few particles remain, resample
    if len(updated_particles) < len(current_belief_particles) * 0.3:
        # Resample with replacement
        if updated_particles:
            updated_particles = random.choices(
                updated_particles, 
                k=len(current_belief_particles)
            )
        else:
            # Reinitialize if all particles invalid
            updated_particles = initialize_belief_particles(
                player_0_hand, 
                opponents_cards_num, 
                observation.observed_discard_cards,
                num_particles=len(current_belief_particles)
            )
    
    return updated_particles


def sample_opponent_hand_from_belief(
    belief_particles: list[Tuple[Tuple[str, ...], ...]],
    opponent_index: int
) -> Tuple[str, ...]:
    """
    Sample an opponent's hand from belief particles.
    
    Args:
        belief_particles: Current belief particles
        opponent_index: Index of opponent (0-indexed relative to opponents)
        
    Returns:
        Sampled hand for the opponent
    """
    import random
    
    if not belief_particles:
        return tuple()
    
    # Randomly select a particle and return that opponent's hand
    particle = random.choice(belief_particles)
    if opponent_index < len(particle):
        return particle[opponent_index]
    return tuple()


# Example usage:
if __name__ == "__main__":
    # Import uno module to access UnoCardGameState
    from uno import UnoCardGameState
    
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

