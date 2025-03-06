# AI FreeCell

![FreeCell AI](https://img.shields.io/badge/FreeCell-AI%20Solver-green)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)

A Python implementation of the classic FreeCell solitaire card game featuring both a standalone playable version and a powerful AI solver with multiple algorithms.

## Table of Contents
1. [Overview & Features](#overview--features)
2. [Installation](#installation)
3. [Interface & Controls](#interface--controls)
4. [Game Rules](#game-rules)
5. [Playing Modes](#playing-modes)
6. [AI Algorithms](#ai-algorithms)
7. [Advanced Features](#advanced-features)
8. [FreeCell Statistics](#freecell-statistics)
9. [Troubleshooting](#troubleshooting)

## Overview & Features

FreeCell is a solitaire card game with the rare quality that nearly all deals are solvable with perfect play. This project provides:

- **Interactive gameplay** with a clean graphical interface
- **Multiple AI solving algorithms** including A*, Greedy Best-First Search, BFS, DFS, IDS, and custom heuristics
- **Performance analytics** with detailed metrics on solution efficiency
- **Auto-move and Super Moves functionality** for easier gameplay
- **Save/load game states** with preset easy and hard games
- **Undo and hint features** for manual play
- **Visualization tools** for solution paths

## Installation

### Prerequisites
- Python 3.9 or higher
- Pygame and Psutil libraries

### Setup
```bash
git clone https://github.com/yourusername/freecell-ai.git
cd freecell-ai
pip install pygame psutil
python Freecell_comAutoMoves.py
```

## Interface & Controls

### Main Interface Elements
- **Top Bar**: Algorithm selection, Solve button, New Game button, Deck size options (52/28/12 cards), Difficulty options
- **Game Area**: Free Cells (top left), Foundations (top right), Cascades (center/bottom)
- **Bottom Bar**: Time counter, Move counter, Step/Pause controls, Game number/search box
- **Side Panel**: Play mode toggle, AutoMove settings, Hint and Undo buttons (in player mode)

### Controls
- **Mouse Controls**:
  - Left-click to select cards or activate buttons
  - Click a card then a destination to move it
  - Click the first card in a sequence to move multiple cards

- **Keyboard Shortcuts**:
  - **Space**: Pause/Resume the automatic solver
  - **N**: New Game
  - **S**: Step forward in solution
  - **B**: Step backward in solution
  - **+/-**: Adjust animation speed
  - **Enter**: Load a game (in search mode)
  - **Escape**: Cancel search mode

## Game Rules

### Objective
Move all cards to the four foundation piles, building up from Ace to King by suit.

### Card Movement Rules
1. **Free Cells**: Any card can move to an empty free cell
2. **Foundations**: Cards must be placed in ascending order (A-2-3-...-K) by suit
3. **Cascades**: Cards must be placed in descending order with alternating colors
4. **Supermoves**: The maximum number of cards movable as a sequence is calculated as:
   ```
   Max movable cards = (Empty Free Cells + 1) × 2^(Empty Cascades)
   ```

## Playing Modes

### Manual Play
1. Start the application and click "I want to play"
2. Select and move cards according to the rules
3. Use "Undo" to take back moves
4. Toggle "Auto On/Off" for automatic foundation moves
5. Use "Hint" to get a suggested move

### AI Solver Mode
1. Select an algorithm from the dropdown
2. Click "Solve" to start the solution process
3. Use Pause/Resume, Step, and Step Back to control playback
4. View arrows indicating moves and cards highlighted in yellow/green
5. Review performance metrics after solution completion

### Loading Games
1. Enter a game number in the search box (e.g game123.txt enter 123 in the search box)
2. Click "Load" or press Enter
3. Built-in games include Easy (164, 1187, 3148, 9998, 10913) and Hard (169, 5087, 20810, 29596, 44732)

## AI Algorithms

### A* Algorithm
- Uses both heuristic evaluation and path cost: `f(n) = g(n) + h(n)`
- Three variants with different heuristics (A*, A* Heu2, A* Heu3)
- Balanced performance with optimal solutions
- Default choice for most games

### Greedy Best-First Search
- Only considers heuristic value: `f(n) = h(n)`
- Faster but may produce longer solutions
- Good for quick solutions to easier games

### Breadth-First Search (BFS)
- Explores all nodes at current depth before moving deeper
- Guarantees shortest solution but memory intensive


### Depth-First Search (DFS)
- Explores branches as far as possible before backtracking
- Memory efficient but not guaranteed optimal
- Useful for deeply nested solutions

### Iterative Deepening Search (IDS)
- Performs DFS with increasing depth limits
- Combines BFS optimality with DFS space efficiency
- Good alternative to A* for complex games

### Weighted A* (WA*)
- Modified A* with weighted heuristic: `f(n) = g(n) + w × h(n)` where `w > 1`
- Finds good solutions faster than standard A*
- Use when speed matters more than perfect optimality

### Meta-heuristic
- Custom approach combining multiple evaluation factors
- Considers card arrangement patterns and strategic moves
- Balances solution quality and search time

## Advanced Features

### Auto-Moves
When enabled, cards automatically move to foundations when safe:
- Cards move if all lower ranks of all suits are already in the foundation
- Toggle in player mode with "Auto On/Off" or in solver mode with "AutoMove On/Off"

### Deck Size Options
- **52 cards**: Standard full deck
- **28 cards**: Reduced deck (A-7 of each suit)
- **12 cards**: Mini deck (A-3 of each suit)

### Performance Metrics
Solution analysis includes:
- Time taken and memory used
- States explored/generated
- Maximum queue size
- Solution length
- Maximum depth reached

## FreeCell Statistics

- Approximately 99.999% of all 52-card FreeCell deals are solvable
- With 4 free cells and 8 cascades, only about 1 in 84,000 deals is unsolvable
- The generalized form of FreeCell is NP-complete
- Approximately 1.75×10⁶⁴ distinct games exist after accounting for suit symmetry

## Troubleshooting

### Common Issues

#### Game Freezes During Solving
- Try a different algorithm
- Reduce the deck size
- Restart the application

#### Invalid Moves
- Ensure sequences alternate colors and follow descending order
- Check supermove limitations

#### Performance Problems
- Close other applications
- Try more efficient algorithms
- Reduce deck size

#### Game Loading Issues
- Verify the game number exists (e.g game123.txt)
- Check file format and permissions



