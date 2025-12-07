"""
MCTS.py implements a Monte Carlo Tree Search algorithm. 

It possesses two classes - TreeNode and MCTS - that together facilitate the search process.

# TODO: Explain the TreeNode and MCTS classes and their methods/defines.
"""
import actions
import UNOState

import math
import random
from copy import deepcopy


class TreeNode:	
	def __init__(self, state, parent = None, action = None):
		self.state = state
		self.parent = parent
		self.action = action
		self.children = []
		self.visits = 0
		self.score = 0.0
		self.untried_actions = actions.get_legal_actions(state)


	def is_terminal(self):
		if actions.get_legal_actions(self.state) is None or len(actions.get_legal_actions(self.state)) == 0:
			return True
		return False


	def is_fully_expanded(self):
		if len(self.untried_actions) == 0:
			return True
		return False


	def best_child(self, c_param):
		# NOTE: UCB1
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
		action = self.untried_actions.pop()
		next_state = deepcopy(self.state)
		child = TreeNode(next_state, parent=self, action_from_parent=action)
		self.children.append(child)
		return child


"""
Example usage of MCTS.

mcts = MCTS(
	gamma = 0.99,
	c_param = 1.4,
	gen_model = uno_gen_model,
	legal_actions = legal_actions_from_observation,
	max_depth = 20,
)

best_action = mcts.plan(belief_particles, num_simulations=1000)
"""
