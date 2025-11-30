"""
State/action containers and transition helper for the UNO search space.

Transitions: S' <- T(S,A)

- Means, in state S, take action A, will go to state S'
- This is what generates the next state from the current state and the action

    Including transitions:
    - Cur_Top' = A.V_Card
    - Cur_Col' = A.Next_Col
    - Cur_Dir' = - Cur_Dir, when A = A.Rev
    - Skip' = 1, when A = A.Sk
    - Sum_Plus' += k, where k={2,4}, when A=A.Plus_N
    - Hand_Cards' = Hand_Cards.append(card), when A = A.GNC
    - UNO' = 1, when A = A.UNO

Observations: O <- O(S, A, S')

- Returns observable information from state-action -> state_transitions
- Based on partial observability: Player 0 knows own hand fully, 
  but only knows opponent hand sizes (not card identities)
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum, auto
from typing import Optional, Tuple


class ActionType(Enum):
    """Types of actions that can be taken from a state."""

    V_CARD = auto()
    NEXT_COLOR = auto()
    PLUS_N = auto()
    SKIP = auto()
    REVERSE = auto()
    GET_NEW_CARD = auto()
    UNO = auto()


@dataclass(frozen=True)
class UNOState:
    cur_color: Optional[str]
    cur_dir: int
    cur_top: Optional[str]
    skip: bool
    sum_plus: int
    hand_cards: Tuple[str, ...]
    opponents_cards_num: Tuple[int, ...]
    belief: Tuple[Tuple[str, ...], ...]
    uno: bool


@dataclass(frozen=True)
class UNOAction:
    type: ActionType
    card: Optional[str] = None
    next_color: Optional[str] = None
    plus_value: int = 0


@dataclass(frozen=True)
class UNOObservation:
    """
    Observable information from state-action -> state_transitions.
    
    Based on partial observability:
    - Player 0's own hand: fully known
    - Opponent hands: only sizes known (not card identities)
    - Public game state: cur_top, cur_color, cur_dir, etc.
    """
    # Own hand (fully observable for Player 0)
    own_hand: Tuple[str, ...]
    
    # Opponent hand sizes (observable, but not card identities)
    opponent_hand_sizes: Tuple[int, ...]
    
    # Public game state
    cur_top: Optional[str]  # Top card on discard pile
    cur_color: Optional[str]  # Current active color
    cur_dir: int  # Play direction (+1 clockwise, -1 counter-clockwise)
    skip: bool  # Whether next player is skipped
    sum_plus: int  # Accumulated draw cards
    uno: bool  # Whether UNO was called
    
    # Action taken (observable)
    action_taken: UNOAction
    
    # Belief state (probabilistic distribution over opponent hands)
    belief: Tuple[Tuple[str, ...], ...]


def transition(state: UNOState, action: UNOAction) -> UNOState:
    """
    Apply the provided action to the given state and return the next state.
    """

    if action.type is ActionType.V_CARD: 
        # Use a valid card from hand(same color or same number), will update the current top card and remove the card from hand
        if action.card is None:
            raise ValueError("V_CARD requires a concrete card")
        new_hand = _remove_card(state.hand_cards, action.card)
        return replace(state, cur_top=action.card, hand_cards=new_hand)

    if action.type is ActionType.NEXT_COLOR: 
        # Choose the next color for the wild card when play a wild card, wild card can be any color
        if action.next_color is None:
            raise ValueError("NEXT_COLOR must specify the chosen color")
        return replace(state, cur_color=action.next_color)

    if action.type is ActionType.PLUS_N: 
        # Play a +2 or +4 wild card, will add the plus value to the sum_plus
        if action.plus_value not in (2, 4):
            raise ValueError("PLUS_N must be either +2 or +4")
        return replace(state, sum_plus=state.sum_plus + action.plus_value)

    if action.type is ActionType.SKIP: 
        # Play a skip card, will skip next player, skip'= 1
        return replace(state, skip=True)

    if action.type is ActionType.REVERSE: 
        # Play a reverse card, will reverse the current direction
        return replace(state, cur_dir=-state.cur_dir)

    if action.type is ActionType.GET_NEW_CARD: 
        # Get a new card from the deck, when no valid cards in hand
        if action.card is None:
            raise ValueError("GET_NEW_CARD should specify the drawn card")
        return replace(state, hand_cards=state.hand_cards + (action.card,))

    if action.type is ActionType.UNO: 
        # When player has only left 2 hand cards, should do "UNO" action, announce to others; or else he will be penal by add 2 cards
        return replace(state, uno=True)

    raise ValueError(f"Unsupported action type: {action.type}")


def observation(state: UNOState, action: UNOAction, next_state: UNOState) -> UNOObservation:
    """
    Generate observation from state-action -> state_transitions.
    
    Returns observable information based on partial observability:
    - Player 0's own hand is fully known
    - Opponent hands: only sizes are known (not card identities)
    - Public game state is observable
    
    Args:
        state: Previous state S
        action: Action A taken
        next_state: Resulting state S' after transition
    
    Returns:
        UNOObservation containing all observable information
    """
    return UNOObservation(
        own_hand=next_state.hand_cards,  # Player 0's hand (fully observable)
        opponent_hand_sizes=next_state.opponents_cards_num,  # Only sizes observable
        cur_top=next_state.cur_top,  # Top discard card (public)
        cur_color=next_state.cur_color,  # Current color (public)
        cur_dir=next_state.cur_dir,  # Play direction (public)
        skip=next_state.skip,  # Skip status (public)
        sum_plus=next_state.sum_plus,  # Accumulated draw cards (public)
        uno=next_state.uno,  # UNO status (public)
        action_taken=action,  # Action that was taken (observable)
        belief=next_state.belief,  # Belief state over opponent hands
    )


def _remove_card(hand: Tuple[str, ...], card: str) -> Tuple[str, ...]:
    """Return a new tuple with one instance of `card` removed."""
    removed = False
    updated = []
    for c in hand:
        if not removed and c == card:
            removed = True
            continue
        updated.append(c)
    if not removed:
        raise ValueError(f"Card {card} not found in hand")
    return tuple(updated)

# Example usage:
# next_state = transition(current_state, action)
# obs = observation(current_state, action, next_state)