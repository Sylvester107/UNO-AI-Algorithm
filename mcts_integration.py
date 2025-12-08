"""
MCTS Integration for UNO Game

This module integrates POMDP MCTS algorithm with the uno.py game.
It allows Player 0 to use MCTS for decision making instead of manual clicking.

Usage:
    from mcts_integration import MCTSPlayer
    
    # Create MCTS player
    mcts_player = MCTSPlayer(
        gamma=0.99,
        c_param=1.4,
        max_depth=20,
        num_particles=100,
        num_simulations=500
    )
    
    # In uno.py, when it's Player 0's turn:
    if game.players[game.pnow].name == 'Player':
        action = mcts_player.get_action(game)
        # Execute action in game
"""

from typing import Optional, Tuple, List, TYPE_CHECKING

if TYPE_CHECKING:
    from uno import UnoCardGameState, UnoCard

from UNOState import (
    game_state_to_uno_state, 
    card_to_string,
    initialize_belief_particles,
    update_belief_state
)
from Transitions import UNOState, UNOAction, ActionType, observation
from MCTS import MCTS
from actions import get_legal_actions
import actions as UNOActions


class MCTSPlayer:
    """
    MCTS-based player for UNO game.
    
    This class maintains belief state and uses MCTS to select actions.
    """
    
    def __init__(
        self,
        gamma: float = 0.99,
        c_param: float = 1.4,
        max_depth: int = 20,
        num_particles: int = 100,
        num_simulations: int = 500
    ):
        """
        Initialize MCTS player.
        
        Args:
            gamma: Discount factor for MCTS
            c_param: UCB1 exploration parameter
            max_depth: Maximum depth for rollout
            num_particles: Number of belief particles
            num_simulations: Number of MCTS simulations per decision
        """
        self.mcts = MCTS(gamma, c_param, max_depth, num_particles)
        self.num_simulations = num_simulations
        self.num_particles = num_particles
        
        # Maintain belief state across turns
        self.belief_particles: List[Tuple[Tuple[str, ...], ...]] = []
        self.observed_discard_history: Tuple[str, ...] = tuple()
        
        # Track game state variables not in UnoCardGameState
        self.sum_plus: int = 0
        self.skip: bool = False
        self.uno: bool = False
    
    def get_action(self, game) -> Optional[int]:
        """
        Get the best action using MCTS.
        
        Args:
            game: Current game state from uno.py (UnoCardGameState)
            
        Returns:
            Index of card to play (in player's hand), or None to draw
        """
        # Convert game state to UNOState
        uno_state = game_state_to_uno_state(
            game,
            player_index=0,
            sum_plus=self.sum_plus,
            skip=self.skip,
            uno=self.uno,
            belief=tuple()  # Belief is maintained separately
        )
        
        # Initialize or update belief particles
        if not self.belief_particles:
            # First time: initialize belief
            self.belief_particles = initialize_belief_particles(
                player_0_hand=uno_state.hand_cards,
                opponents_cards_num=uno_state.opponents_cards_num,
                observed_discard_cards=self.observed_discard_history,
                num_particles=self.num_particles
            )
        
        # Run MCTS to get best action
        best_action = self.mcts.search(
            uno_state,
            self.belief_particles,
            self.num_simulations
        )
        
        if best_action is None:
            return None
        
        # Convert action to card index
        if best_action.type == ActionType.V_CARD and best_action.card:
            # Find card index in hand
            card_str = best_action.card
            for i, card in enumerate(game.players[0].hand):
                if card_to_string(card) == card_str:
                    return i
        
        # If action is GET_NEW_CARD, return None to draw
        if best_action.type == ActionType.GET_NEW_CARD:
            return None
        
        return None
    
    def update_belief(self, game, action_taken: UNOAction, action_player: int):
        """
        Update belief state based on observation after an action.
        
        Args:
            game: Current game state (UnoCardGameState) - already updated by uno.py
            action_taken: Action that was taken
            action_player: Index of player who took the action (0, 1, 2, or 3)
        """
        # The game state has already been updated by uno.py when this is called
        # So we just need to get the current state and create observation
        
        # Get current state (after action has been applied in game)
        current_state = game_state_to_uno_state(
            game,
            player_index=0,
            sum_plus=self.sum_plus,
            skip=self.skip,
            uno=self.uno
        )
        
        # Create a previous state for observation (simplified - we don't need exact previous state)
        # We just need the observation structure
        prev_state = current_state  # Simplified: use current state as previous
        
        # Get observation
        obs = observation(
            prev_state,
            action_taken,
            current_state,
            action_player=action_player,
            observed_discard_history=self.observed_discard_history,
            opponent_drew=action_player if action_taken.type == ActionType.GET_NEW_CARD and action_player > 0 else None
        )
        
        # Update observed discard history
        if action_taken.type == ActionType.V_CARD and action_taken.card:
            self.observed_discard_history = self.observed_discard_history + (action_taken.card,)
        
        # Update belief particles
        self.belief_particles = update_belief_state(
            self.belief_particles,
            observation=obs,
            player_0_hand=current_state.hand_cards,
            opponents_cards_num=current_state.opponents_cards_num
        )
        
        # Update tracked state variables from current game state
        # Note: sum_plus, skip, uno are not directly tracked in UnoCardGameState
        # We'll infer them from the game state or keep them as is
        # For now, we'll update based on the action taken
        if action_taken.type == ActionType.PLUS_N:
            self.sum_plus += action_taken.plus_value
        elif action_taken.type == ActionType.SKIP:
            self.skip = True
        elif action_taken.type == ActionType.UNO:
            self.uno = True
    
    def reset(self):
        """Reset belief state for a new game."""
        self.belief_particles = []
        self.observed_discard_history = tuple()
        self.sum_plus = 0
        self.skip = False
        self.uno = False


def create_mcts_action_from_card_index(game, card_index: int) -> UNOAction:
    """
    Create UNOAction from card index in player's hand.
    
    Args:
        game: Current game state
        card_index: Index of card in Player 0's hand
        
    Returns:
        UNOAction for playing that card
    """
    if card_index is None or card_index < 0 or card_index >= len(game.players[0].hand):
        return UNOAction(type=ActionType.GET_NEW_CARD, card=None)
    
    card = game.players[0].hand[card_index]
    card_str = card_to_string(card)
    return UNOAction(type=ActionType.V_CARD, card=card_str)


def execute_mcts_action(game, action: UNOAction) -> bool:
    """
    Execute an MCTS action in the game.
    
    Args:
        game: Current game state
        action: Action to execute
        
    Returns:
        True if action was executed successfully
    """
    if action.type == ActionType.V_CARD and action.card:
        # Find card in hand and play it
        for i, card in enumerate(game.players[0].hand):
            if card_to_string(card) == action.card:
                game.discard(i)
                
                # If Wild card, choose color (use preferred color)
                card_color, card_type = action.card.split('-', 1)
                if card_color == 'Wild':
                    # Choose color based on hand
                    from uno import preferredcolor
                    hand = game.players[0].hand
                    chosen_color = preferredcolor(hand) if hand else 'Blue'
                    # Update color (this would need to be done in game state)
                    game.colornow = chosen_color
                
                return True
    
    elif action.type == ActionType.GET_NEW_CARD:
        # Draw a card
        game.drawcardsfromdeck(1)
        return True
    
    return False

