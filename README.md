# FreeCell AI

A Python implementation of the classic FreeCell solitaire game with both a standalone playable version and an AI-powered solver using multiple algorithms.

## Overview

This project provides two main components:
- `only_game.py`: A standalone version of FreeCell for manual play
- `freecellAI_UI.py`: An enhanced version featuring four AI solving algorithms

## Game Rules

FreeCell is a solitaire card game played with a standard 52-card deck. Unlike most solitaire games, very few deals are unsolvable, and all cards are dealt face-up from the beginning.

- **Setup**: Cards are dealt into eight cascades (four with seven cards, four with six cards)
- **Cells**: Four open cells for temporary card storage
- **Foundations**: Four foundation piles (one for each suit) built from Ace to King
- **Movement**: Cards can be moved one at a time, built on tableaus in descending order with alternating colors
- **Supermoves**: While physical moves are one card at a time, the game allows moving sequences through intermediate locations
- **Goal**: Move all cards to their foundation piles

## AI Algorithms

The `freecellAI_UI.py` program implements four different search algorithms to solve FreeCell puzzles:

### 1. Best First Search
- Evaluates moves based on a heuristic function
- Prioritizes promising states based on estimated distance to goal
- Good balance between efficiency and solution quality
- Implementation applies domain-specific knowledge to guide the search

### 2. A* Algorithm
- Combines Best First Search with path cost consideration
- Evaluates states using f(n) = g(n) + h(n) where:
  - g(n) is the cost so far to reach the state
  - h(n) is the estimated cost to the goal
- Guaranteed to find the optimal solution if h(n) is admissible
- Most efficient algorithm for finding optimal solutions

### 3. Breadth-First Search (BFS)
- Explores all neighbor nodes at present depth before moving to nodes at the next depth
- Complete: guarantees finding a solution if one exists
- Optimal for unweighted graphs
- Can be memory-intensive for complex FreeCell positions

### 4. Depth-First Search (DFS)
- Explores as far as possible along each branch before backtracking
- Memory efficient compared to BFS
- May find solutions faster in some cases, but not guaranteed to find the optimal solution
- Implementation includes depth limiting to prevent infinite searches

## Supermove Implementation (ideia de implemetação???)

The AI algorithms account for FreeCell's supermove capability, where multiple cards can be moved in sequence:
- Maximum movable cards: C = 2ᴹ × (N+1)
  - M = number of empty cascades
  - N = number of empty cells
- Cards movable to empty cascade: C/2
- Algorithms properly evaluate supermoves to find efficient solutions

## Game Numbering

The implementation supports numbered games, compatible with Microsoft FreeCell's random number generator, allowing players to recreate specific deals.

## Usage

### Playing Manually
```
python only_game.py
```

### Using AI Solvers
```
python freecellAI_UI.py
```

After launching, select an algorithm and either:
1. Start a new random game
2. Enter a specific game number
3. Continue from current game state

## Requirements

- Python 3.9+
- Pygame (for UI)

## Complexity

While the standard 52-card FreeCell game has a finite state space, the generalized version is NP-complete. Some interesting facts:
- ~99.999% of FreeCell deals are solvable
- There are approximately 1.75×10⁶⁴ distinct games after accounting for suit symmetry
- Only 1 in ~84,000 random deals is unsolvable

## Performance Comparison

The four algorithms offer different trade-offs:
- Best First: Fast solutions, moderate memory usage, reasonably optimal paths
- A*: Optimal solutions, higher memory usage, can be slower for complex positions
- BFS: Complete solutions, high memory usage, optimal for unweighted paths
- DFS: Memory efficient, can quickly find solutions in some cases, path optimality not guaranteed

## Future Improvements

- Optimized heuristics for faster solving
- Parallel search implementations
- Machine learning enhancements
- Advanced visualization of solving process

## License

[Your License Information]