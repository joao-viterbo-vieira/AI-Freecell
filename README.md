# FreeCell AI Solver & User Manual

![FreeCell AI](https://img.shields.io/badge/FreeCell-AI%20Solver-green)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Pygame](https://img.shields.io/badge/Pygame-2.0%2B-red)

A Python implementation of the classic FreeCell solitaire card game featuring both a standalone playable version and a powerful AI solver with multiple algorithms to analyze and solve games automatically.

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Interface Overview](#interface-overview)
5. [Game Rules](#game-rules)
6. [Playing Manually](#playing-manually)
7. [Using the AI Solver](#using-the-ai-solver)
8. [Game Controls](#game-controls)
9. [Save and Load Games](#save-and-load-games)
10. [Automated Features](#automated-features)
11. [Advanced Features](#advanced-features)
12. [AI Algorithms](#ai-algorithms)
13. [FreeCell Statistics](#freecell-statistics)
14. [Troubleshooting](#troubleshooting)
15. [License](#license)

## Overview

FreeCell is a solitaire card game with the rare quality that nearly all deals are solvable with perfect play. This project provides:

- **Interactive gameplay** with a clean graphical interface
- **Multiple AI solving algorithms** to analyze and solve games
- **Performance metrics** to compare algorithm efficiency
- **Auto-move functionality** for easier gameplay
- **Save/load game states** for continued play or analysis

## Features

- **Game Interface**
  - Intuitive drag-and-drop card movement
  - Highlighted valid moves
  - Automatic card movement to foundations when safe
  - Undo functionality
  - Timer and move counter

- **AI Solver**
  - Multiple algorithms:
    - A* (with three different heuristics)
    - Greedy Best-First Search
    - Breadth-First Search (BFS)
    - Depth-First Search (DFS)
    - Iterative Deepening Search (IDS)
    - Weighted A* (WA*)
    - Meta-heuristic

- **Analytics**
  - Detailed performance metrics
  - Solution path visualization
  - Step-by-step solution playback
  - Memory usage tracking
  - States explored/generated statistics

## Installation

### Prerequisites

- Python 3.9 or higher
- Pygame library
- Psutil library

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/freecell-ai.git
   cd freecell-ai
   ```

2. Install required packages:
   ```bash
   pip install pygame psutil
   ```

3. Run the game:
   ```bash
   python Freecell_comAutoMoves.py
   ```

## Interface Overview

The FreeCell AI interface consists of several key areas:

### Top Bar
- **Algorithm selection**: Choose between different solving algorithms
- **Solve button**: Start the automatic solver
- **New Game button**: Start a fresh game
- **Deck size options**: Select between 52, 28, or 12 cards
- **Difficulty options**: Choose between Easy and Hard preset games

### Main Game Area
- **Free Cells** (top left): Four cells for temporarily storing single cards
- **Foundations** (top right): Four piles (one per suit) where cards are built up from Ace to King
- **Cascades** (center/bottom): Eight columns where cards are dealt and gameplay occurs

### Bottom Bar
- **Time counter**: Shows elapsed time
- **Move counter**: Displays number of moves made
- **Step/Pause controls**: For controlling automatic solution playback
- **Game number**: Shows the current game number if loaded from a preset
- **Search box**: For entering a specific game number to load

### Side Panel
- **I want to play**: Switch to manual play mode
- **AutoMove On/Off**: Toggle automatic foundation moves
- **Hint**: Get a suggested move (in player mode)
- **Undo**: Take back the last move (in player mode)

## Game Rules

FreeCell is a solitaire card game played with a standard 52-card deck.

### Objective
Move all cards to the four foundation piles, building up from Ace to King by suit.

### Card Movement Rules
1. **Free Cells**: Any card can be moved to an empty free cell
2. **Foundations**: Cards must be placed in ascending order (A-2-3-...-K) by suit
3. **Cascades**: Cards must be placed in descending order with alternating colors
4. **Empty Cascades**: Any card can be moved to an empty cascade

### Supermoves
The maximum number of cards you can move as a sequence is determined by:
```
Max movable cards = (Empty Free Cells + 1) × 2^(Empty Cascades)
```

This is a key strategic element in FreeCell, allowing you to move sequences of properly arranged cards as a unit.

## Playing Manually

1. Start the application with `python Freecell_comAutoMoves.py`
2. Click the "I want to play" button to enter player mode
3. To move a card:
   - Click on the card you want to move
   - Click on the destination (foundation, free cell, or another cascade)
4. To move a sequence of cards:
   - Click on the first card in the sequence you want to move
   - Click on the destination cascade

### Undo Moves
Click the "Undo" button to take back your last move.

### Enable/Disable Auto Moves
Click the "Auto On"/"Auto Off" button to toggle automatic foundation moves.

## Using the AI Solver

1. Select an algorithm from the dropdown at the top
2. Click the "Solve" button to start the solution process
3. Control the solution playback using:
   - Pause/Resume button to halt or continue the automatic playback
   - Step button to move forward one step at a time
   - Step Back button to revert to the previous move

### Available Algorithms

| Algorithm | Strengths | When to Use |
|-----------|-----------|-------------|
| A* | Optimal solutions, balanced performance | Default choice for most games |
| A* Heu2 | Alternative heuristic | When standard A* is too slow |
| A* Heu3 | Alternative heuristic | When standard A* is too slow |
| Greedy | Fast but not always optimal | For quick solutions to easy games |
| BFS | Guaranteed optimal solution | For short, simple games |
| DFS | Memory efficient | For deeply nested solutions |
| IDS | Good balance of BFS/DFS | Alternative to A* for complex games |
| WA* | Faster than A* | When speed matters more than optimality |
| Meta | Custom heuristic | For games with tricky patterns |

### Solution Visualization
- While the solver is running, you'll see arrows indicating each move
- Recently moved cards are highlighted in green during paused playback
- The bottom of the screen shows statistics about the solution

## Game Controls

### Keyboard Shortcuts
- **Space**: Pause/Resume the automatic solver
- **N**: New Game
- **S**: Step forward in the solution
- **B**: Step backward in the solution
- **+/-**: Increase/Decrease animation speed
- **Enter**: Load a game (when in search mode)
- **Escape**: Cancel search mode

### Mouse Controls
- **Left-click on a card**: Select the card
- **Left-click on a destination**: Move the selected card there
- **Click on a sequence**: Select multiple cards (if they form a valid sequence)
- **Click on buttons**: Activate the corresponding feature

## Save and Load Games

### Loading a Specific Game
1. Enter a game number in the search box at the bottom left
2. Click "Load" or press Enter

### Included Game Difficulties
- **Easy games**: 164, 1187, 3148, 9998, 10913
- **Hard games**: 169, 5087, 20810, 29596, 44732

## Automated Features

### Auto-Moves
When enabled, the game automatically moves cards to foundations when safe:
- Cards will automatically move if all lower ranks of all suits are already in the foundation
- For example, a 5♠ will automatically move if all 4s of each suit are in the foundations

To toggle this feature:
- In player mode: Click the "Auto On"/"Auto Off" button
- In solver mode: Click the "AutoMove On"/"AutoMove Off" button

### Hints
In player mode, click the "Hint" button to get a suggested move. The suggestion will be shown with a yellow arrow.

## Advanced Features

### Animation Speed
Adjust the animation speed using the + and - keys:
- Faster: Press +
- Slower: Press -

The current animation speed is displayed at the bottom right.

### Deck Size Options
Choose from three different deck sizes:
- **52 cards**: Standard full deck
- **28 cards**: Reduced deck (A-7 of each suit)
- **12 cards**: Mini deck (A-3 of each suit)

This is useful for learning the game or testing algorithms on simpler puzzles.

### Performance Metrics
When a solution is found, detailed metrics are displayed:
- Time taken
- Memory used
- States explored
- Solution length
- And more

These metrics are also saved to solution files for later analysis.

## AI Algorithms

### A* Algorithm
- Uses heuristic evaluation plus path cost
- Three heuristic variants available (1, 2, and 3)
- Most efficient for finding optimal solutions
- Formula: f(n) = g(n) + h(n)

### Greedy Best-First Search
- Only considers heuristic value (not path cost)
- Often faster but may produce longer solutions
- Formula: f(n) = h(n)

### Breadth-First Search (BFS)
- Complete and optimal (for unweighted graphs)
- Explores all nodes at current depth before moving deeper
- Memory intensive but guarantees shortest solution

### Depth-First Search (DFS)
- Memory efficient
- Explores as far as possible along branches before backtracking
- May find solutions quickly but not guaranteed to be optimal

### Iterative Deepening Search (IDS)
- Combines advantages of BFS and DFS
- Performs DFS with increasing depth limits
- Optimal like BFS but more space-efficient

### Weighted A* (WA*)
- Modified A* giving more weight to the heuristic
- Often finds good solutions faster than standard A*
- Formula: f(n) = g(n) + w × h(n) where w > 1

### Meta-heuristic
- Custom heuristic combining multiple factors
- Considers card arrangement patterns and strategic moves
- Good balance between solution quality and search time

## FreeCell Statistics

- Of all possible 52-card FreeCell deals, approximately 99.999% are solvable
- With 4 free cells and 8 cascades, only about 1 in 84,000 deals is unsolvable
- The generalized form of FreeCell is NP-complete
- Approximately 1.75×10⁶⁴ distinct FreeCell games exist after accounting for suit symmetry

## Troubleshooting

### Common Issues

#### Game Freezes During Solving
- Try a different algorithm - some games are too complex for certain algorithms
- Reduce the deck size to test with simpler games
- Restart the application

#### Incorrect or Invalid Moves
- Check that you're following the rules for card placement
- Remember that sequences must alternate colors and be in descending order
- Make sure you're not exceeding the maximum movable cards for supermoves

#### Performance Issues
- Close other applications to free up memory
- Try using more efficient algorithms (Greedy or WA* instead of BFS)
- Consider reducing the deck size for faster solutions

#### Game Numbers Not Loading
- Verify that the game number exists in the games directory
- Check that the game file format matches the expected format
- Ensure you have read permissions for the games directory

### Contact Support
If you encounter persistent issues, please file an issue on the project's GitHub repository with:
- A detailed description of the problem
- Steps to reproduce the issue
- The game number (if applicable)
- Any error messages displayed

## License

This project is licensed under the MIT License - see the LICENSE file for details.
