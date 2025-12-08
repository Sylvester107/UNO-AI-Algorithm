"""
MCTS.py implements a Monte Carlo Tree Search algorithm. 

It possesses two classes - TreeNode and MCTS - that together facilitate the search process.

Treenode = defines nodes & has helper functions
MCTS = algorithm ft. selection; expansion; simulation; backpropagation
"""
import actions as UNOActions
import UNOState
from Transitions import transition, UNOState as TransitionsUNOState, observation, UNOObservation, ActionType
from dataclasses import replace as dataclass_replace

import math
import random
from copy import deepcopy


class TreeNode:	
	"""
	Node in the Monte Carlo search tree.

	Each TreeNode stores a game `state`, a pointer to its `parent`,
	the `action` that led to this state (None for the root), a list of
	`children`, and statistics used by MCTS (`visits`, `score`).

	`untried_actions` holds the legal actions from this state that have
	not yet been expanded into children.
	"""

	def __init__(self, state, parent = None, action = None):
		"""
		Initialize a tree node.

		Args:
			state: Game state object for this node.
			parent: Parent TreeNode (None for root).
			action: Action applied on parent to get to this state.
		"""
		self.state = state
		self.parent = parent
		self.action = action
		self.children = []
		self.visits = 0
		self.score = 0.0
		# List of actions that can be expanded from this node
		# Only generate actions if it's Player 0's turn
		if state.current_player == 0:
			# Filter out explicit UNO declarations; uno.py already handles UNO calls
			# when the player reaches one card, so keeping them here causes MCTS
			# to pick a no-op action that maps to "invalid" in integration.
			actions = UNOActions.get_legal_actions(state)
			self.untried_actions = [
				a for a in actions if a.type != UNOActions.ActionType.UNO
			]
			# If we filtered everything (corner case), fall back to the original list
			if not self.untried_actions:
				self.untried_actions = actions
		else:
			self.untried_actions = []  # Opponent turns handled in rollout
		# Belief particles for POMDP (initialized later)
		self.belief_particles = []


	def is_terminal(self):
		"""
		Return True if this node corresponds to a terminal state.

		Uses the `get_legal_actions` helper: if there are no legal actions
		available, the state is considered terminal.
		"""
		if UNOActions.get_legal_actions(self.state) is None or len(UNOActions.get_legal_actions(self.state)) == 0:
			return True
		return False


	def is_fully_expanded(self):
		"""
		Return True if all legal actions from this node have been expanded.

		A node is fully expanded when `untried_actions` is empty.
		"""
		if len(self.untried_actions) == 0:
			return True
		return False


	def best_child(self, c_param):
		"""
		Select and return the best child using the UCB1 formula.

		UCB1 = (score/visits) + c_param * sqrt( log(self_visits) / child_visits )
		Children with zero visits are treated as having infinite score so
		that they are explored at least once.

		Args:
			c_param: UCB1 parameter.

		Returns:
			The child TreeNode with highest UCB1 value.
		"""
		best_score = -float('inf')
		best = None
		for child in self.children:
			if child.visits == 0:
				score = float('inf')
			else:
				exploit = child.score / child.visits
				explore = c_param * math.sqrt(math.log(self.visits) / child.visits)
				score = exploit + explore
			
			if score > best_score:
				best_score = score
				best = child
		
		return best


	def expand(self):
		"""
		Expand one untried action and add the resulting child node.

		NOTE: the current implementation pops the last action; to avoid
		deterministic expansion bias, we can pop a random action instead.
		"""
		if not self.untried_actions:
			return None
		action = self.untried_actions.pop()
		next_state = transition(self.state, action)
		child = TreeNode(deepcopy(next_state), parent=self, action=action)
		self.children.append(child)
		return child


class MCTS:	
	"""
	POMDP-aware Monte Carlo Tree Search for UNO.
	
	This MCTS implementation uses particle filtering to handle partial observability.
	Each node maintains belief particles representing possible opponent hands.
	
	Example usage:
		mcts = MCTS(
			gamma = 0.99,
			c_param = 1.4,
			max_depth = 20,
			num_particles = 100
		)
		
		best_action = mcts.search(root_state, belief_particles, num_simulations=1000)
	"""

	def __init__(self, gamma, c_param, max_depth, num_particles=100):
		"""
		Initialize POMDP MCTS.
		
		Args:
			gamma: Discount factor for backpropagation
			c_param: UCB1 exploration parameter
			max_depth: Maximum depth for rollout
			num_particles: Number of belief particles to maintain
		"""
		self.gamma = gamma
		self.c_param = c_param
		self.max_depth = max_depth
		self.num_particles = num_particles


	def search(self, root_state, belief_particles, num_simulations):
		"""
		Perform MCTS search from root state with belief particles.
		
		Args:
			root_state: Root game state (from Player 0's perspective)
			belief_particles: List of belief particles (possible opponent hands)
			num_simulations: Number of MCTS simulations to run
			
		Returns:
			Best action to take
		"""
		root = TreeNode(deepcopy(root_state))
		root.belief_particles = belief_particles  # Store belief at root

		for i in range(num_simulations):
			# Sample a particle for this simulation
			if belief_particles:
				sampled_particle = random.choice(belief_particles)
			else:
				sampled_particle = None
			
			node = root
			state = deepcopy(root.state)
			current_belief = belief_particles.copy() if belief_particles else []

			# Selection
			while not node.is_terminal():
				# If the node is marked fully expanded but has no children
				# (e.g., opponent nodes where we don't expand actions),
				# stop selection and move to rollout from this node.
				if node.is_fully_expanded():
					if not node.children:
						break
					next_node = node.best_child(self.c_param)
					if next_node is None:
						break
					node = next_node
					state = deepcopy(node.state)
					# Update belief based on path taken
					if hasattr(node, 'belief_particles'):
						current_belief = node.belief_particles
				else:
					break

			# Expansion
			if not node.is_terminal():
				if (not node.is_fully_expanded()):
					node = node.expand()
					state = deepcopy(node.state)
					# Initialize belief for new node
					if not hasattr(node, 'belief_particles'):
						node.belief_particles = current_belief.copy() if current_belief else []

			# Simulation with belief
			reward = self.rollout(deepcopy(state), current_belief.copy() if current_belief else [])

			# Backpropagation
			self.backpropagate(node, reward)

		# After simulations, pick best action (most visits)
		best = None
		best_visits = -1
		for child in root.children:
			if child.visits > best_visits:
				best_visits = child.visits
				best = child

		if best is None:
			return None

		return best.action


	def rollout(self, state, belief_particles):
		"""
		Perform a random rollout from `state` until terminal or max depth.
		Uses belief particles to simulate opponent hands in POMDP setting.
		
		Returns reward in [0,1] (1=player 0 wins in rollout, 0 otherwise).
		
		Args:
			state: Current game state
			belief_particles: List of belief particles (possible opponent hands)
		"""
		from UNOState import sample_opponent_hand_from_belief, update_belief_state
		
		current_belief = belief_particles.copy() if belief_particles else []
		
		for depth in range(self.max_depth):
			# Check if it's Player 0's turn
			if state.current_player == 0:
				# Player 0's turn: use real hand to generate legal actions
				actions = UNOActions.get_legal_actions(state)
				if not actions:
					break
				a = random.choice(actions)
				previous_state = deepcopy(state)
				
				# If action is GET_NEW_CARD and card is None, simulate drawing a card
				if a.type == UNOActions.ActionType.GET_NEW_CARD and a.card is None:
					drawn_card = self._simulate_draw_card()
					a = UNOActions.UNOAction(type=UNOActions.ActionType.GET_NEW_CARD, card=drawn_card)
				
				state = transition(state, a)
				
				# Update belief based on Player 0's action (if it reveals information)
				# Create observation from the transition
				obs = observation(
					previous_state,
					a,
					state,
					action_player=0,  # Player 0 took the action
					observed_discard_history=None,  # Not tracking history in rollout
					opponent_drew=None  # Player 0 played, didn't draw
				)
				current_belief = update_belief_state(
					current_belief,
					observation=obs,
					player_0_hand=state.hand_cards,
					opponents_cards_num=state.opponents_cards_num
				)
				
				# Win condition: player 0 has emptied hand
				if state.hand_cards is not None and len(state.hand_cards) == 0:
					return 1.0
			else:
				# Opponent's turn: use belief particles to simulate
				opponent_idx = state.current_player - 1  # Convert to opponent index (0-indexed)
				
				# Sample opponent hand from belief
				if current_belief:
					opponent_hand = sample_opponent_hand_from_belief(current_belief, opponent_idx)
				else:
					opponent_hand = tuple()  # Empty hand if no belief
				
				# Save previous state before simulation
				previous_state = deepcopy(state)
				
				# Simulate opponent turn with sampled hand
				state, played_card, action = self._simulate_opponent_turn_with_belief(
					state, opponent_hand, opponent_idx
				)
				
				# Update belief based on observation (opponent played a card or drew)
				if action:
					# Create observation from the transition
					obs = observation(
						previous_state,
						action,
						state,
						action_player=previous_state.current_player,  # The opponent who took action
						observed_discard_history=None,  # Not tracking history in rollout
						opponent_drew=opponent_idx if not played_card else None  # Opponent drew if didn't play
					)
					current_belief = update_belief_state(
						current_belief,
						observation=obs,
						player_0_hand=state.hand_cards,
						opponents_cards_num=state.opponents_cards_num
					)
				
				# Check if opponent won
				if opponent_idx < len(state.opponents_cards_num) and state.opponents_cards_num[opponent_idx] == 0:
					return 0.0  # Opponent won, Player 0 loses
		
		# Did not reach win within depth
		return 0.0
	
	def _simulate_opponent_turn_with_belief(self, state, opponent_hand, opponent_idx):
		"""
		Simulate an opponent's turn using their sampled hand from belief.
		
		Args:
			state: Current game state
			opponent_hand: Sampled opponent hand from belief particles
			opponent_idx: Index of opponent (0-indexed relative to opponents)
			
		Returns:
			Tuple of (new_state, played_card, action) where:
			- played_card is the card played (None if drew)
			- action is the UNOAction taken
		"""
		from actions import is_card_playable, parse_card
		
		# Find playable cards in opponent's hand
		playable_cards = []
		for card_str in opponent_hand:
			if is_card_playable(card_str, state):
				playable_cards.append(card_str)
		
		if playable_cards and random.random() < 0.8:  # 80% chance to play if possible
			# Opponent plays a card (random strategy from playable cards)
			played_card = random.choice(playable_cards)
			
			# Create a temporary state with opponent's hand for transition
			# We need to swap hand_cards temporarily to use transition function
			temp_state = dataclass_replace(state, hand_cards=tuple(opponent_hand))
			
			# Create action and transition
			action = UNOActions.UNOAction(type=UNOActions.ActionType.V_CARD, card=played_card)
			new_state = transition(temp_state, action)
			
			# Restore Player 0's hand (transition modified it)
			# We need to get Player 0's hand from original state
			new_state = dataclass_replace(new_state, hand_cards=state.hand_cards)
			
			# If Wild card, also choose color
			card_color, card_type = parse_card(played_card)
			if card_color == 'Wild':
				colors = ['Blue', 'Green', 'Red', 'Yellow']
				color_action = UNOActions.UNOAction(
					type=UNOActions.ActionType.NEXT_COLOR,
					next_color=random.choice(colors)
				)
				new_state = transition(new_state, color_action)
				# Restore hand again after color choice
				new_state = dataclass_replace(new_state, hand_cards=state.hand_cards)
			
			# Update opponent hand size (simulate removing card)
			opponent_sizes = list(new_state.opponents_cards_num)
			if opponent_idx < len(opponent_sizes) and opponent_sizes[opponent_idx] > 0:
				opponent_sizes[opponent_idx] -= 1
			
			new_state = dataclass_replace(
				new_state,
				opponents_cards_num=tuple(opponent_sizes)
			)
			
			return new_state, played_card, action
		else:
			# Opponent draws a card
			drawn_card = self._simulate_draw_card()
			# For drawing, we don't need to modify hand_cards
			action = UNOActions.UNOAction(type=UNOActions.ActionType.GET_NEW_CARD, card=drawn_card)
			# Create temp state for transition (transition expects current player's hand)
			temp_state = dataclass_replace(state, hand_cards=tuple(opponent_hand))
			new_state = transition(temp_state, action)
			# Restore Player 0's hand
			new_state = dataclass_replace(new_state, hand_cards=state.hand_cards)
			
			# Update opponent hand size (simulate adding card)
			opponent_sizes = list(new_state.opponents_cards_num)
			if opponent_idx < len(opponent_sizes):
				opponent_sizes[opponent_idx] += 1
			
			new_state = dataclass_replace(
				new_state,
				opponents_cards_num=tuple(opponent_sizes)
			)
			
			return new_state, None, action
	
	def _simulate_draw_card(self):
		"""Simulate drawing a card from deck (simplified - returns random card)."""
		# This is a placeholder - in practice, sample from remaining deck based on belief
		colors = ['Blue', 'Green', 'Red', 'Yellow', 'Wild']
		types = ['0','1','2','3','4','5','6','7','8','9','Skip','Draw Two','Reverse','Wild','Draw Four']
		return f"{random.choice(colors)}-{random.choice(types)}"

	def backpropagate(self, node, reward):
		"""
		Propagate reward up to root, updating visits and score.
		"""
		discount = 1.0
		while node is not None:
			node.visits += 1
			node.score += reward * discount
			discount *= self.gamma
			node = node.parent
