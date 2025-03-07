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
10. [LLM Performance Analysis](#LLM-Performance-Analysis)
11. [Designing a FreeCell LLM Agent: Architecture and Potential](#designing-a-freecell-LLM-agent-architecture-and-potential)



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
git clone https://github.com/joao-viterbo-vieira/ai-freecell.git
cd ai-freecell
pip install pygame psutil
python Freecell.py
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
6. If a supermove is possible and you want to select just the front card, click in the lower part of the front card
7. At any moment the player can click "Solve" and the AI Solver will solve the rest of the game

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
- Combines BFS optimality with DFS space efficiency
- Good alternative to A* for complex games

### Weighted A* (WA*)
- Modified A* with weighted heuristic: `f(n) = g(n) + w × h(n)` where `w > 1`
- Finds good solutions faster than standard A*
- Use when speed matters more than perfect optimality

### Meta-heuristic (Meta, Meta2)
- Custom approach combining multiple evaluation factors
- Considers card arrangement patterns and strategic moves
- Balances solution quality and search time

## Advanced Features

### Cards solving visualization
- View the solution step-by-step with full control over playback speed
- Pause at any point to examine the board state
- Navigate forward and backward through solution moves
- Adjust animation speed to see moves quickly or study them in detail (keys +/-)

### Super Moves
Automatically identifies and executes multi-step card sequences
- Moves multiple cards as a stack when a valid destination is available
- Reduces the number of manual moves needed for common sequences
- Highlights potential super moves on the board when available

### Auto-Moves
When enabled, cards automatically move to foundations when safe:
- Cards move if all lower ranks of all suits are already in the foundation
- Toggle in player mode with "Auto On/Off" or in solver mode with "AutoMove On/Off"

### Undo Moves (single player mode)
- Revert any mistake with unlimited undo capability
- Track and restore exact board states after each move
- Maintain game statistics even after undoing moves
- Quick undo shortcut available via keyboard or button press


### Deck Size and Difficulty Options
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


### Complete Output File
The system generates a file in the "solutions" folder containing the initial position, all performance metrics, and a complete sequence of all moves performed to solve the game.

### Game Import Instructions
To import a custom game:

- Create a text file in the "games" folder with name format "gamesXXX.txt" (where XXX is a number)
- Enter card arrangement using the following format:
  ```
  3♣ 2♠ 2♣ A♦ 3♥ 2♥ 3♦ 3♠
  2♦ A♥ A♠ A♣
  ```

- Save the file and select it from the game loader menu
- The system supports standard card notation with suit symbols (♣, ♠, ♥, ♦) and will automatically process the layout according to the specified format.


## FreeCell Statistics

- Approximately 99.999% of all 52-card FreeCell deals are solvable
- With 4 free cells and 8 cascades, only about 1 in 84,000 deals is unsolvable
- The generalized form of FreeCell is NP-complete
- Approximately 1.75×10⁶⁴ distinct games exist after accounting for suit symmetry

## Troubleshooting

### Common Issues

#### Game Freezes During Solving / Performance Problems
- Try a different algorithm
- Reduce the deck size
- Restart the application
- Close other applications
- The user can also change the number of nodes used by doing CTRL + F and searching for "0000" in the code

#### Invalid Moves
- Ensure sequences alternate colors and follow descending order
- Check supermove limitations

#### Game Loading Issues
- Verify the game number exists (e.g game123.txt)
- Check file format and permissions

## LLM Performance Analysis

- `LLMs_tests/FreeCell_Solver_Prompt.txt` - Contains the prompt used for the LLMs, incorporating best practices of prompt engineering, including the goal, input format, return format, context dump, and rules.

- `LLMs_tests/results_LLMs.txt` - Contains the raw output from each model's solution attempt, including timing information

### The Puzzle

This analysis examines how different Large Language Models (LLMs) performed when solving a simple FreeCell solitaire puzzle (12 card game).

### Card Layout

The puzzle that all models attempted to solve had the following layout:

```
A♥ 3♥ 2♥ A♦ A♣ A♠ 3♠ 3♦
2♦ 2♠ 2♣ 3♣
```

### Results (Zero-shot)

| Model | Time | Moves | Success |
|-------|------|-------|---------|
| Claude 3.7 Sonnet (extended thinking) | 1m 36s | 13 | ✅ |
| Grok3 | 1m 10s | 14 | ✅ |
| O3-mini-high | 1m 12s | 13 | ✅ |
| O3-mini | 20s | 12 | ✅ |
| O1 | 41s | 12 | ✅ |
| Deepseek-r1 | 2m 58s | 15 | ✅ |
| ChatGPT-4o (2025-01-29) | - | - | ❌ |
| ChatGPT-4.5-Preview | - | - | ❌ |
| Gemini 2.0 Flash Thinking | - | - | ❌ |
| Gemini 2.0 Pro | - | - | ❌ |
| Claude 3.7 (without extended thinking) | - | - | ❌ |
| Qwen-max-2025-01-25 | - | - | ❌ |
| Llama-3.3-70b-instruct | - | - | ❌ |
| Mistral-large-2411 | - | - | ❌ |

### Key Observations

1. **Solution Efficiency**:
   - O3-mini and O1 found the most efficient solutions (12 moves)
   - Deepseek-r1 took the longest time and path (15 moves)
   - Most successful models found solutions in 12-14 moves

2. **Processing Time**:
   - O3-mini solved it fastest (20 seconds)
   - Deepseek-r1 took longest (nearly 3 minutes)
   - Extended thinking made a critical difference for Claude 3.7

3. **Success Rate**:
   - 6 out of 14 tested models successfully solved the puzzle (All reasoning models)
   - Several top LLMs (including ChatGPT-4o, Gemini 2.0 Flash Thinking, and standard Claude 3.7) failed

4. **Time vs. Efficiency Correlation**:
   - Interestingly, longer processing time didn't always yield more efficient solutions
   - O3-mini found one of the most efficient solutions in the shortest time

### Conclusions
This benchmark reveals significant differences in how LLMs handle rule-based strategic planning tasks. The results suggest that specialized reasoning capabilities may be more important than overall model size for game-solving tasks like simple FreeCell games (12 cards). However, LLMs are still not reliable for this type of reasoning. While they can succeed in some simple cases if they possess reasoning capabilities and are given enough time to think, their performance varies. Repeating these tests may yield different results, but only zero-shot attempts on the first try for each task were considered.

## Designing a FreeCell LLM Agent: Architecture and Potential

The design concept for a FreeCell LLM Agent presents an innovative approach to game assistance through a function-calling architecture. This agent would combine:

### Customized Personality
A prompt-engineered personality that's friendly, funny, and educational.

### Function-Based Game Understanding
Six core functions provide the LLM with complete game awareness:

- **Getting valid moves and board state**
- **Executing moves and suggesting hints**
- **Finding complete solution paths**
- **Supporting voice interaction**

This architecture solves a key challenge in game-playing LLMs: how to give models accurate, real-time game state information without hallucination. By exposing specific game functions to the LLM, it can make informed decisions based on the actual game state rather than its internal understanding of FreeCell rules.

The design represents a promising bridge between traditional game-solving algorithms and natural language interfaces, potentially making complex puzzle games more accessible to casual players.
