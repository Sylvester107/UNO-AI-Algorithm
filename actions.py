"""
actions.py - Generate all legal actions from a UNOState.

This module provides functions to:
1. Generate all legal actions from a given state
2. Check if specific actions are valid
3. Handle UNO game rules for action legality

Dependencies:
- Transitions.py: UNOState, UNOAction, ActionType
"""

from __future__ import annotations

from typing import List, Optional
from Transitions import UNOState, UNOAction, ActionType

# Valid colors in UNO
VALID_COLORS = ['Blue', 'Green', 'Red', 'Yellow']


def parse_card(card_str: str) -> tuple[str, str]:
    """
    Parse a card string into (color, type).
    
    Args:
        card_str: Card string in format "Color-Type" (e.g., "Blue-5", "Wild-Draw Four")
        
    Returns:
        Tuple of (color, type)
    """
    parts = card_str.split("-", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid card format: {card_str}")
    return parts[0], parts[1]


def is_card_playable(card_str: str, state: UNOState) -> bool:
    """
    Check if a card is playable given the current state.
    
    A card is playable if:
    - It matches the current color (cur_color)
    - It matches the top discard card's type
    - It is a Wild card (can be played at any time)
    
    Special case: Wild Draw Four can only be played if player has no cards
    matching the current color.
    
    Args:
        card_str: Card string to check
        state: Current game state
        
    Returns:
        True if card is playable, False otherwise
    """
    if state.cur_top is None:
        return False
    
    card_color, card_type = parse_card(card_str)
    top_color, top_type = parse_card(state.cur_top)
    
    # Wild cards can always be played (except Draw Four has restrictions)
    if card_color == 'Wild':
        if card_type == 'Draw Four':
            # Wild Draw Four: can only play if no cards match current color
            return not _has_color_match(state.hand_cards, state.cur_color)
        else:
            # Regular Wild card: can always be played
            return True
    
    # Check if card matches current color
    if card_color == state.cur_color:
        return True
    
    # Check if card matches top card's type
    if card_type == top_type:
        return True
    
    return False


def _has_color_match(hand_cards: tuple[str, ...], color: Optional[str]) -> bool:
    """
    Check if hand has any cards matching the given color.
    
    Args:
        hand_cards: Player's hand
        color: Color to match
        
    Returns:
        True if hand has at least one card of the given color
    """
    if color is None:
        return False
    
    for card_str in hand_cards:
        card_color, _ = parse_card(card_str)
        if card_color == color:
            return True
    return False


def get_legal_actions(state: UNOState, available_draw_cards: Optional[List[str]] = None) -> List[UNOAction]:
    """
    Generate all legal actions from the current state.
    
    Legal actions include:
    1. Playing valid cards from hand (V_CARD)
    2. Drawing a card if no valid cards (GET_NEW_CARD)
    3. Calling UNO if down to 1 card (UNO)
    
    Note: 
    - When playing action cards (Skip, Reverse, Draw Two/Four), the card effects
      are determined by the card type itself. The transition function handles these.
    - NEXT_COLOR actions are generated separately after playing a Wild card using
      get_color_choice_actions().
    - For Wild cards, you'll need to play V_CARD first, then NEXT_COLOR.
    
    Args:
        state: Current game state
        available_draw_cards: Optional list of cards that could be drawn.
                              If None, assumes drawing is possible but card is unknown.
    
    Returns:
        List of legal UNOAction objects
    """
    actions: List[UNOAction] = []
    
    # Find all playable cards in hand
    playable_cards = []
    for card_str in state.hand_cards:
        if is_card_playable(card_str, state):
            playable_cards.append(card_str)
    
    # Add actions for playing each playable card
    # Note: Playing a card (V_CARD) is the primary action. The card's effects
    # (Skip, Reverse, Draw Two/Four) are handled by the card type itself.
    for card_str in playable_cards:
        card_color, card_type = parse_card(card_str)
        
        # For all playable cards, add V_CARD action
        actions.append(UNOAction(type=ActionType.V_CARD, card=card_str))
        
        # For Wild cards, also need to choose color (handled separately after playing)
        # For Draw Two/Four, the PLUS_N effect is implicit in the card type
    
    # If no playable cards, must draw
    if len(playable_cards) == 0:
        if available_draw_cards is not None:
            # If we know what cards could be drawn, create actions for each
            for drawn_card in available_draw_cards:
                actions.append(UNOAction(type=ActionType.GET_NEW_CARD, card=drawn_card))
        else:
            # Unknown draw - create a placeholder action
            # In practice, you'd need to sample from the deck or use belief state
            actions.append(UNOAction(type=ActionType.GET_NEW_CARD, card=None))
    
    # UNO action: must be called when down to 1 card (after playing second-to-last)
    # This is typically handled separately, but we include it here
    if len(state.hand_cards) == 1 and not state.uno:
        actions.append(UNOAction(type=ActionType.UNO))
    
    return actions


def get_color_choice_actions() -> List[UNOAction]:
    """
    Generate actions for choosing a color after playing a Wild card.
    
    Returns:
        List of NEXT_COLOR actions for each valid color
    """
    return [
        UNOAction(type=ActionType.NEXT_COLOR, next_color=color)
        for color in VALID_COLORS
    ]


def is_action_valid(action: UNOAction, state: UNOState) -> bool:
    """
    Check if a specific action is valid in the current state.
    
    Args:
        action: Action to validate
        state: Current game state
        
    Returns:
        True if action is valid, False otherwise
    """
    if action.type == ActionType.V_CARD:
        if action.card is None:
            return False
        return action.card in state.hand_cards and is_card_playable(action.card, state)
    
    elif action.type == ActionType.NEXT_COLOR:
        return action.next_color in VALID_COLORS
    
    elif action.type == ActionType.PLUS_N:
        if action.plus_value not in (2, 4):
            return False
        if action.card is None:
            return False
        return action.card in state.hand_cards and is_card_playable(action.card, state)
    
    elif action.type == ActionType.SKIP:
        if action.card is None:
            return False
        card_color, card_type = parse_card(action.card)
        return card_type == 'Skip' and action.card in state.hand_cards
    
    elif action.type == ActionType.REVERSE:
        if action.card is None:
            return False
        card_color, card_type = parse_card(action.card)
        return card_type == 'Reverse' and action.card in state.hand_cards
    
    elif action.type == ActionType.GET_NEW_CARD:
        # Can only draw if no playable cards
        playable = [c for c in state.hand_cards if is_card_playable(c, state)]
        return len(playable) == 0
    
    elif action.type == ActionType.UNO:
        # Can call UNO when down to 1 card
        return len(state.hand_cards) == 1 and not state.uno
    
    return False


def filter_legal_actions(actions: List[UNOAction], state: UNOState) -> List[UNOAction]:
    """
    Filter a list of actions to only include legal ones.
    
    Args:
        actions: List of actions to filter
        state: Current game state
        
    Returns:
        List of legal actions
    """
    return [action for action in actions if is_action_valid(action, state)]


def get_card_effects(card_str: str) -> List[ActionType]:
    """
    Get the action types that need to be applied when playing a card.
    
    This helps determine what additional actions (beyond V_CARD) are needed
    when playing a specific card.
    
    Args:
        card_str: Card string to check
        
    Returns:
        List of ActionType that should be applied after playing this card
    """
    _, card_type = parse_card(card_str)
    effects = []
    
    if card_type == 'Skip':
        effects.append(ActionType.SKIP)
    elif card_type == 'Reverse':
        effects.append(ActionType.REVERSE)
    elif card_type == 'Draw Two':
        effects.append(ActionType.PLUS_N)  # plus_value=2
    elif card_type == 'Draw Four':
        effects.append(ActionType.PLUS_N)  # plus_value=4
    
    return effects


def is_wild_card(card_str: str) -> bool:
    """
    Check if a card is a Wild card (requires color choice).
    
    Args:
        card_str: Card string to check
        
    Returns:
        True if card is Wild or Wild Draw Four
    """
    card_color, _ = parse_card(card_str)
    return card_color == 'Wild'


# Example usage:
if __name__ == "__main__":
    # Example state
    from Transitions import UNOState
    
    example_state = UNOState(
        cur_color='Blue',
        cur_dir=1,
        cur_top='Blue-5',
        skip=False,
        sum_plus=0,
        hand_cards=('Blue-7', 'Red-5', 'Wild-Wild', 'Green-Skip'),
        opponents_cards_num=(7, 7, 7),
        belief=(tuple(), tuple(), tuple()),
        uno=False
    )
    
    legal_actions = get_legal_actions(example_state)
    print(f"Legal actions from example state: {len(legal_actions)}")
    for action in legal_actions:
        print(f"  - {action.type.name}: {action.card}")

