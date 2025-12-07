"""
MCTS.py implements a Monte Carlo Tree Search algorithm. 

It possesses two classes - TreeNode and MCTS - that together facilitate the search process.

# TODO: Explain the TreeNode and MCTS classes and their methods/defines.
Treenode = defines nodes & has helper functions
MCTS = algorithm ft. selection; expansion; simulation; backpropagation
"""
import actions as UNOActions
import UNOState
from Transitions import transition

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
		self.untried_actions = UNOActions.get_legal_actions(state)


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
		deterministic expansion bias you can pop a random action instead.
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
	Example usage of MCTS.

	mcts = POMDPMCTS(
		gamma = 0.99,
		c_param = 1.4,
		gen_model = uno_gen_model,
		legal_actions = legal_actions_from_observation,
		max_depth = 20,
	)

	best_action = mcts.plan(belief_particles, num_simulations=1000)
	# TODO: Uncertain on what is the .plan() method. Is that equivalent to .search()?
	"""

	def __init__(self, gamma, c_param, gen_model, legal_actions, max_depth):
		self.gamma = gamma
		self.c_param = c_param
		self.gen_model = gen_model
		self.legal_actions = legal_actions
		self.max_depth = max_depth


	def search(self, root_state, num_simulations):
		root = TreeNode(deepcopy(root_state))

		for i in range(num_simulations):
			node = root
			state = deepcopy(root.state)

			# Selection
			while not node.is_terminal() and node.is_fully_expanded():
				node = node.best_child(self.c_param)
				state = deepcopy(node.state)

			# Expansion
			if not node.is_terminal():
				if (not node.is_fully_expanded()):
					node = node.expand()
					state = deepcopy(node.state)

			# Simulation
			reward = self.rollout(deepcopy(state))

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


	def rollout(self, state):
		"""
		Perform a random rollout from `state` until terminal or max depth.
		Returns reward in [0,1] (1=player 0 wins in rollout, 0 otherwise).
		"""
		for depth in range(self.max_depth):
			actions = UNOActions.get_legal_actions(state)
			if not actions:
				break
			a = random.choice(actions)
			state = transition(state, a)
			# Win condition: player 0 has emptied hand
			if state.hand_cards is not None and len(state.hand_cards) == 0: # NOTE: Tune this later.
				return 1.0
		# Did not reach win within depth
		return 0.0

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
