# UNO Game with MCTS AI - User Guide

## Quick Start

### Basic Usage

```bash
# Run the game with default parameters
python uno.py
```

### View Help Information

```bash
python uno.py --help
```

## Command Line Arguments

### MCTS Algorithm Parameters

#### `--gamma` (float, default: 0.99)
- **Description**: Discount factor for MCTS, used for reward decay during backpropagation
- **Range**: Typically between 0.9 and 1.0
- **Example**: 
  ```bash
  python uno.py --gamma 0.95
  ```

#### `--c_param` (float, default: 1.4)
- **Description**: Exploration parameter for UCB1 algorithm, controls exploration-exploitation balance
- **Range**: Typically between 1.0 and 2.0
  - Smaller values: More biased towards exploiting known good actions
  - Larger values: More biased towards exploring unknown actions
- **Example**:
  ```bash
  python uno.py --c_param 2.0
  ```

#### `--max_depth` (int, default: 20)
- **Description**: Maximum depth for MCTS rollout, limits the depth of simulation search
- **Range**: Recommended 10-30, larger values search deeper but take longer
- **Example**:
  ```bash
  python uno.py --max_depth 25
  ```

#### `--num_particles` (int, default: 100)
- **Description**: Number of belief particles for POMDP (Partially Observable Markov Decision Process)
- **Description**: Used to handle uncertainty about opponent hands
- **Range**: Recommended 50-200, more particles are more accurate but slower
- **Example**:
  ```bash
  python uno.py --num_particles 150
  ```

#### `--num_simulations` (int, default: 500)
- **Description**: Number of MCTS simulations per decision
- **Description**: This is the most important performance parameter, directly affects AI decision quality
- **Range**: Recommended 100-2000
  - Few (100-300): Fast decisions, suitable for testing
  - Medium (500-1000): Balanced quality and speed
  - Many (1000+): High-quality decisions, but time-consuming
- **Example**:
  ```bash
  python uno.py --num_simulations 1000
  ```

### Game Control Parameters

#### `--use_mcts` (flag, default: True)
- **Description**: Enable MCTS AI to control Player 0
- **Description**: This is the default behavior, usually no need to explicitly specify
- **Example**: Enabled by default, no additional parameter needed

#### `--no_mcts`
- **Description**: Disable MCTS, use manual clicking to control Player 0
- **Description**: With this option, Player 0 requires manual clicking to play cards
- **Example**:
  ```bash
  python uno.py --no_mcts
  ```

#### `--num_rounds` (int, default: 10)
- **Description**: Number of rounds to play
- **Range**: Any positive integer
- **Description**: Game will also end early if any player reaches 500 points
- **Example**:
  ```bash
  python uno.py --num_rounds 5
  ```

## Usage Examples

### 1. Quick Test (Single Round, Fast Simulation)
Suitable for quickly testing if code modifications work correctly:
```bash
python uno.py --num_rounds 1 --num_simulations 50
```

### 2. Standard Game (Medium Intensity)
Configuration balancing quality and speed:
```bash
python uno.py --num_rounds 10 --num_simulations 500
```

### 3. High-Quality Game (High Intensity)
Pursuing best performance, requires longer thinking time:
```bash
python uno.py --num_rounds 20 --num_simulations 1000 --num_particles 150
```

### 4. Manual Game Mode
If you want to manually control Player 0:
```bash
python uno.py --no_mcts --num_rounds 5
```

### 5. Experiment with Different MCTS Parameters
Test the impact of different parameter combinations on performance:
```bash
# More aggressive exploration
python uno.py --c_param 2.0 --num_simulations 800

# More conservative exploitation
python uno.py --c_param 1.0 --num_simulations 800

# Deeper search
python uno.py --max_depth 30 --num_simulations 500
```

### 6. Complete Parameter Configuration Example (Default)
```bash
python uno.py \
    --gamma 0.99 \
    --c_param 1.4 \
    --max_depth 20 \
    --num_particles 100 \
    --num_simulations 500 \
    --num_rounds 10
```

## Game Rules

### Basic Setup
- **Number of Players**: 4 (Player 0 + Bot1 + Bot2 + Bot3)
- **Initial Hand**: 7 cards per player
- **Win Condition**: 
  - First player to discard all cards wins the current round
  - Gains the sum of all other players' card point values for that round
  - First player to reach 500 points wins the entire game

### Player 0 (MCTS AI)
- Uses MCTS algorithm for automatic decision-making by default
- Can choose to use `--no_mcts` to switch to manual control

### Bot Players
- Bot1, Bot2, Bot3 use simple strategies to automatically play cards
- Will challenge Draw Four cards at appropriate times

## Output Information

The game displays during runtime:
1. **Initialization Information**: MCTS parameter configuration
2. **Round Logs**: Operation records for each round
3. **Statistics**: 
   - Winner of each round
   - Player 0's win rate
   - Cumulative scores of all players

### Example Output
```
============================================================
MCTS Player initialized with parameters:
  gamma: 0.99
  c_param: 1.4
  max_depth: 20
  num_particles: 100
  num_simulations: 500
  USE_MCTS: True
============================================================

[LOG] Player Bot1 is dealer.
[LOG] Player Bot2 starts play.
...
```

## Technical Details

### MCTS Algorithm
- Supports POMDP (Partially Observable Markov Decision Process)
- Uses Particle Filter to handle uncertainty about opponent hands

### State Representation
- Uses `UNOState` to represent game state
- Maintains belief particles to represent possible opponent hand distributions

### Dependencies
The following Python libraries are required (all are standard library):
- `tkinter` (GUI, usually included with Python)
- `argparse` (command-line argument parsing, Python standard library)
- `threading` (multithreading, Python standard library)
- `random`, `time`, `collections`, `dataclasses`, `enum`, `typing`, `copy`, `math` (standard library)

## File Structure

Main game files:
- `uno.py`: Main game file and GUI
- `MCTS.py`: MCTS algorithm implementation
- `mcts_integration.py`: Integration of MCTS with the game
- `UNOState.py`: Game state representation and belief management
- `Transitions.py`: State transition functions
- `actions.py`: Action definitions and legality checking
