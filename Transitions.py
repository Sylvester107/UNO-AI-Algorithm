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
    current_player: int = 0  # Current player index (0-3), default is Player 0
    num_players: int = 4  # Total number of players


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
    - Discard pile: only top card is visible (history not fully observable)
    - Draw pile: completely unobservable (size and contents unknown)
    
    IMPORTANT: Player 0 does NOT know:
    - What cards are in the draw pile
    - What cards opponents have (only sizes)
    - Full discard pile history (only top card visible)
    """
    # Own hand (fully observable for Player 0)
    own_hand: Tuple[str, ...]
    
    # Opponent hand sizes (observable, but not card identities)
    opponent_hand_sizes: Tuple[int, ...]
    
    # Public game state
    cur_top: Optional[str]  # Top card on discard pile (only top is visible)
    cur_color: Optional[str]  # Current active color
    cur_dir: int  # Play direction (+1 clockwise, -1 counter-clockwise)
    skip: bool  # Whether next player is skipped
    sum_plus: int  # Accumulated draw cards
    uno: bool  # Whether UNO was called
    
    # Action taken (observable)
    action_taken: UNOAction
    
    # Who took the action (observable - important for belief updates)
    action_player: int  # Player index who took the action (0, 1, 2, or 3)
    
    # Cards visible in discard pile (only top card, but we track what we've seen)
    # This is what Player 0 has observed so far (not the full discard pile)
    observed_discard_cards: Tuple[str, ...]  # Cards that have been played and are visible
    
    # Information about draws (if opponent drew, we know they drew but not what)
    opponent_drew: Optional[int] = None  # Index of opponent who drew (if any)
    
    # Belief state (probabilistic distribution over opponent hands)
    # NOTE: This is computed/updated based on observations, not directly observable
    belief: Tuple[Tuple[str, ...], ...] = tuple()


def _next_player_index(current: int, direction: int, num_players: int) -> int:
    """Calculate next player index based on direction."""
    return (current + direction) % num_players


def transition(state: UNOState, action: UNOAction) -> UNOState:
    """
    Apply the provided action to the given state and return the next state.
    
    This function handles:
    - Card playing and color updates
    - Special card effects (Skip, Reverse, Draw Two/Four)
    - Player turn rotation
    - Multi-step actions (Wild cards require color choice)
    """

    if action.type is ActionType.V_CARD: 
        # Play a valid card from hand
        if action.card is None:
            raise ValueError("V_CARD requires a concrete card")
        
        new_hand = _remove_card(state.hand_cards, action.card)
        card_color, card_type = _parse_card_string(action.card)
        
        # Update cur_top with the played card
        new_state = replace(state, cur_top=action.card, hand_cards=new_hand)
        
        # Update cur_color: if not Wild card, use card's color
        if card_color != 'Wild':
            new_state = replace(new_state, cur_color=card_color)
        
        # Handle card effects based on card type
        # NOTE: In UNO, when play a card, its effect happens immediately
        if card_type == 'Skip':
            # Skip next player: advance to player after next
            next_p = _next_player_index(state.current_player, state.cur_dir, state.num_players)
            new_state = replace(new_state, skip=True, current_player=next_p)
        elif card_type == 'Reverse':
            # Reverse direction and skip current player (they already played)
            new_dir = -state.cur_dir
            # In 2-player game, Reverse acts like Skip; in 4-player, it reverses direction
            if state.num_players == 2:
                # Skip next player
                next_p = _next_player_index(state.current_player, new_dir, state.num_players)
                new_state = replace(new_state, cur_dir=new_dir, current_player=next_p, skip=True)
            else:
                # Just reverse direction, current player already played
                new_state = replace(new_state, cur_dir=new_dir)
        elif card_type == 'Draw Two':
            # Next player draws 2 cards
            new_state = replace(new_state, sum_plus=state.sum_plus + 2)
        elif card_type == 'Draw Four':
            # Next player draws 4 cards
            new_state = replace(new_state, sum_plus=state.sum_plus + 4)
        elif card_type == 'Wild':
            # Wild card requires color choice (handled by NEXT_COLOR action)
            # cur_color stays as is until NEXT_COLOR is called
            pass
        
        # After playing a card, move to next player (unless Skip/Reverse already handled it)
        if card_type not in ['Skip', 'Reverse']:
            # Normal card or Draw Two/Four: move to next player
            next_p = _next_player_index(state.current_player, new_state.cur_dir, state.num_players)
            new_state = replace(new_state, current_player=next_p)
        elif card_type == 'Reverse' and state.num_players > 2:
            # Reverse in 4-player: direction reversed, but current player already played
            # Next player is determined by new direction
            next_p = _next_player_index(state.current_player, new_state.cur_dir, state.num_players)
            new_state = replace(new_state, current_player=next_p)
        # Skip and Reverse (2-player) already updated current_player above
        
        return new_state

    if action.type is ActionType.NEXT_COLOR: 
        # Choose the next color for the wild card
        if action.next_color is None:
            raise ValueError("NEXT_COLOR must specify the chosen color")
        return replace(state, cur_color=action.next_color)

    if action.type is ActionType.PLUS_N: 
        # Play a +2 or +4 card (usually combined with V_CARD, but can be separate)
        if action.plus_value not in (2, 4):
            raise ValueError("PLUS_N must be either +2 or +4")
        return replace(state, sum_plus=state.sum_plus + action.plus_value)

    if action.type is ActionType.SKIP: 
        # Skip next player (usually combined with V_CARD)
        next_p = _next_player_index(state.current_player, state.cur_dir, state.num_players)
        return replace(state, skip=True, current_player=next_p)

    if action.type is ActionType.REVERSE: 
        # Reverse direction (usually combined with V_CARD)
        new_dir = -state.cur_dir
        if state.num_players == 2:
            # In 2-player, Reverse acts like Skip
            next_p = _next_player_index(state.current_player, new_dir, state.num_players)
            return replace(state, cur_dir=new_dir, current_player=next_p, skip=True)
        else:
            return replace(state, cur_dir=new_dir)

    if action.type is ActionType.GET_NEW_CARD: 
        # Draw a new card from the deck
        if action.card is None:
            raise ValueError("GET_NEW_CARD should specify the drawn card")
        return replace(state, hand_cards=state.hand_cards + (action.card,))

    if action.type is ActionType.UNO: 
        # Call UNO when down to 1 card
        return replace(state, uno=True)

    raise ValueError(f"Unsupported action type: {action.type}")


def _parse_card_string(card_str: str) -> tuple[str, str]:
    """Parse card string into (color, type)."""
    parts = card_str.split("-", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid card format: {card_str}")
    return parts[0], parts[1]


def observation(
    state: UNOState, 
    action: UNOAction, 
    next_state: UNOState,
    action_player: int,
    observed_discard_history: Optional[Tuple[str, ...]] = None,
    opponent_drew: Optional[int] = None
) -> UNOObservation:
    """
    Generate observation from state-action -> state_transitions.
    
    IMPORTANT: This function should be called after each transition to get
    the observable information, which is then used to update belief state.
    """
    """
    Generate observation from state-action -> state_transitions.
    
    Returns observable information based on partial observability:
    - Player 0's own hand is fully known
    - Opponent hands: only sizes are known (not card identities)
    - Public game state is observable
    - Only top card of discard pile is visible (not full history)
    - Draw pile is completely unobservable
    
    Args:
        state: Previous state S
        action: Action A taken
        next_state: Resulting state S' after transition
        action_player: Index of player who took the action (0, 1, 2, or 3)
        observed_discard_history: History of cards Player 0 has observed being played
        opponent_drew: Index of opponent who drew a card (if any)
    
    Returns:
        UNOObservation containing all observable information
    """
    # Update observed discard history
    if observed_discard_history is None:
        observed_discard_history = tuple()
    
    # If a card was played, add it to observed history
    if action.type == ActionType.V_CARD and action.card:
        observed_discard_history = observed_discard_history + (action.card,)
    
    return UNOObservation(
        own_hand=next_state.hand_cards,  # Player 0's hand (fully observable)
        opponent_hand_sizes=next_state.opponents_cards_num,  # Only sizes observable
        cur_top=next_state.cur_top,  # Top discard card (public, only top visible)
        cur_color=next_state.cur_color,  # Current color (public)
        cur_dir=next_state.cur_dir,  # Play direction (public)
        skip=next_state.skip,  # Skip status (public)
        sum_plus=next_state.sum_plus,  # Accumulated draw cards (public)
        uno=next_state.uno,  # UNO status (public)
        action_taken=action,  # Action that was taken (observable)
        action_player=action_player,  # Who took the action (observable)
        observed_discard_cards=observed_discard_history,  # Cards Player 0 has seen played
        opponent_drew=opponent_drew,  # If opponent drew (we know they drew, not what)
        belief=next_state.belief,  # Belief state (computed, not directly observable)
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