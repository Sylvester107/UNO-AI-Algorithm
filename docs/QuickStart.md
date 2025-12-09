---
layout: default
title: Quick Start
nav_order: 2
---

# Quick Start Guide

## How to Play

### Running the Game

**With MCTS AI Agent (Default):**
```bash
python uno.py
```
Player 0 will be controlled automatically by the MCTS AI agent.

**Without AI Agent (Manual Control):**
```bash
python uno.py --no_mcts
```
Player 0 requires manual clicking to play cards. Click on a card in your hand to play it.

### Game Overview

- **Players**: 4 players total (Player 0 + 3 bots)
- **Objective**: Be the first to score 500 points by winning rounds
- **Winning a Round**: Discard all your cards first
- **Scoring**: Winner gains points equal to the sum of all opponents' remaining card values

### Basic Gameplay

1. **Starting the Game**: A rules window will appear first. Press Enter/Return to close it and begin.

2. **Your Turn**: 
   - If using MCTS (default): The AI automatically selects and plays cards
   - If using `--no_mcts`: Click on a playable card from your hand to play it

3. **Playing Cards**: 
   - Match the top discard card by **color** or **number/symbol**
   - Wild cards can be played anytime (choose a color)
   - If no playable cards, you must draw from the deck

4. **Special Cards**:
   - **Skip**: Next player misses their turn
   - **Reverse**: Changes play direction
   - **Draw Two**: Next player draws 2 cards and skips turn
   - **Wild Draw Four**: Next player draws 4 cards (can be challenged)

5. **Saying UNO**: When you have 1 card left, the game automatically announces "UNO!"

6. **Winning**: First player to discard all cards wins the round and scores points. First to reach 500 points wins the game.

### Game Interface

- **Left Side**: Game board showing all players, discard pile, and draw pile
- **Right Side**: 
  - Game log (shows all actions)
  - Color buttons (for choosing Wild card colors)
  - Challenge button (for challenging Draw Four cards)

### Quick Tips

- The game runs multiple rounds automatically (default: 10 rounds)
- Watch the game log on the right to see all actions
- If a Draw Four is played against you, you have 5 seconds to click "Challenge" if you suspect the player had a matching color card
- The game ends when a player reaches 500 points or after the specified number of rounds

### Command Line Options

For advanced usage with custom MCTS parameters:
```bash
python uno.py --help
```

Common options:
- `--num_rounds N`: Play N rounds (default: 10)
- `--num_simulations N`: MCTS simulation count (default: 500, higher = better AI but slower)
- `--no_mcts`: Disable AI, use manual clicking
 