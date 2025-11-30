
Summary_NOV_30:
1. UNOState.py 
•	Converts UnoCardGameState (from uno.py) → UNOState (for search algorithms)
•	Handles card string conversion
•	Manages partial observability (Player 0's hand fully known, opponents only sizes)
2. Transitions.py 
•	Defines UNOState, UNOAction, ActionType
•	transition() function: S' = T(S, A)
•	observation() function: O = O(S, A, S')
3. actions.py 
•	get_legal_actions(): Generates all legal actions from a state
•	is_action_valid(): Validates specific actions
•	is_card_playable(): Checks if a card can be played
•	get_color_choice_actions(): Actions for choosing color after Wild cards
•	Helper functions for card effects and Wild card detection
Next steps: MCTS
1.	MCTS.py — Monte Carlo Tree Search implementation
•	Node structure (state, visits, wins, children)
•	Selection (UCB1)
•	Expansion (add new nodes)
•	Simulation (random playouts)
•	Backpropagation (update statistics)
•	Handle partial observability (belief state)

2.	Integration
•	Connect MCTS with actions.py for legal moves
•	Use transition() from Transitions.py for state updates
•	Use UNOState.py to convert between game states

•	NB: we'll need to track ‘sum_plus’, ‘skip’, and ‘uno’ separately as you play the game, since ‘uno.py’ doesn't explicitly maintain these as state variables.

•	Code belief
