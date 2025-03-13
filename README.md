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

Below is an overview of the algorithms tested for solving FreeCell-like problems (e.g., 12-game2.txt, 28-game3.txt, 52 cards-game4.txt). Each algorithm is described in terms of its core principle, performance, memory usage, and ability to reach solutions for different deck sizes. We also present a comparative analysis for easy and hard setups (5 easy, 4 hard) with a maximum of 500,000 states explored.


### A* Algorithm

- **Principle**: Uses both path cost \(g(n)\) and heuristic \(h(n)\):  
  \
    f(n) = g(n) + h(n)
  \

- **Variants**:  
  - **A * Heuristic 1**:  
    - Managed to solve with 12 cards and achieved the best (optimal) solution there.  
    - Failed to solve 28- and 52-card problems in our tests.  
    - Used a fair amount of memory and time, reaching a depth of ~14/16 for larger decks.

  - **A * Heuristic 2** (A* Heu2):  
    - Generally the best performer for random deals.  
    - Solves up to 52 cards efficiently, with strong solutions (often optimal).  
    - Very good balance of speed and memory usage—top choice overall.

  - **A * Heuristic 3** (A* Heu3):  
    - Second-best A* approach, producing solutions slightly worse than Heuristic 2.  
    - Very similar memory usage and time to Heuristic 2, but solutions are somewhat less optimal.

#### Performance Notes (Heuristic 2 and Heuristic 3) with 52-Card Deals

- **Easy Setups (5 tested)**:  
  - **Heuristic 2**: Excellent solutions, near-optimal results, moderate memory/time.  
  - **Heuristic 3**: Slightly worse solutions than Heuristic 2, but still fast and memory-friendly.

- **Hard Setups (4 tested)**:  
  - **Heuristic 2**: Solved 3 out of 4; good solutions, fast on average, and low memory usage.  
  - **Heuristic 3**: Solved all 4 with solutions a bit far from optimal. Averaged ~47 seconds, ~300 MB memory.

---

### Greedy Search

- **Principle**: Considers only the heuristic value \(h(n)\):  
  \
    f(n) = h(n)
  \
- **Pros**: Faster in simpler cases due to ignoring path cost.  
- **Cons**: Often produces longer (suboptimal) solutions, can still be expensive in harder setups.

#### Performance Notes

- For 52-card deals, solutions tend to be much worse than A*.  
- Required significant time for difficult deals and occasionally high memory usage.  
- In the hard setups, solved only 2 of 4, with poor solution quality and memory costs comparable to Weighted A*.

---
### Breadth-First Search (BFS)

- **Principle**: Explores all nodes at a given depth before moving deeper.
- **Pros**: Guarantees the shortest solution (if it finds one).
- **Cons**: Extremely memory-intensive; not suitable for FreeCell-scale problems.

#### Performance Notes

- Even with just 12 cards (which has a minimal solution of 12 moves), BFS only reached ~5 moves without automoves (or ~8 with automoves).  
- Could not solve any deals; memory usage is prohibitive.

---
### Depth-First Search (DFS)

- **Principle**: Explores one branch fully before backtracking.
- **Pros**: Very low memory usage.
- **Cons**: Not guaranteed optimal, can get stuck in deep paths.

#### Performance Notes

- For 12 cards, it found a 92-move solution (without automoves), which is very long compared to optimal.  
- Cannot solve problems beyond ~12 cards; simply too large to handle.

---
### Iterative Deepening Search (IDS)

- **Principle**: Repeatedly runs DFS with increasing depth limits, combining BFS optimality with DFS memory efficiency.
- **Pros**: In theory, can find optimal solutions with reduced memory usage compared to BFS.
- **Cons**: Potentially high time cost due to repeated expansions.

#### Performance Notes

- Achieved a 72-move solution for 12 cards (better than DFS).  
- Failed to solve significantly larger problems (e.g., 28 cards or more) in tests.  
- Tends to exceed the defined state limits and still not reach a solution, consuming a lot of time.

---
### “Empty to Empty” Optimization (Disables unnecessary moves between empty spaces)

- **Principle**: When enabled, eliminates unnecessary moves between empty cascades.
- **Performance Notes**:  
  - Helps reduce the number of moves significantly for the 12-card problem (e.g., 12-game2.txt) for DFS and IDS algorithms.  
  - Primarily beneficial in small setups.

---
### Weighted A* (WA*)

- **Principle**: A* variant with a weighted heuristic:  
  \
    f(n) = g(n) + w \times h(n), \quad w > 1
  \
- **Pros**: Can find decent solutions more quickly than standard A* when \(w\) is not too high, reducing search effort.
- **Cons**: Solutions are suboptimal compared to regular A*; can still be time-consuming in some cases.

#### Performance Notes

- With 52 cards, it took around 17 seconds without automoves, while A* Heuristic 2 took only ~1.4 seconds.  
- Uses less memory compared to BFS, but solutions are worse than A* Heuristic 3.  
- In the easy setups, sometimes matched or exceeded the known solutions while maintaining moderate memory/time.  
- In the hard setups, solved all 4 but with worse solutions than Heuristic 3, higher memory usage, and time similar to Greedy.

---
### Meta-Heuristics (Meta, Meta2)

- **Principle**: Custom approaches that integrate multiple factors (e.g., card arrangement patterns, strategic moves, partial heuristics).
- **Pros**: Potential for flexible adaptation; can significantly reduce search time or memory usage depending on the design.
- **Cons**: Highly sensitive to how heuristics are combined; some variants might fail on certain deals or produce suboptimal solutions.

### Meta 1

- For easy setups, it used more time/memory than expected, producing solutions that were not as good as A*.  
- In the hard setups, it only solved 1 of the 4 problems, used a large amount of memory (up to 10× more than Greedy), and produced poor-quality solutions.

### Meta 2 (Improved Meta-Heuristic)

- **Easy Setups**:  
  - Recorded the lowest average time among all algorithms, even faster than A* Heuristic 3 (previously the fastest).  
  - Found better solutions than A* Heuristic 3, though still slightly below A* Heuristic 2.  
  - Consumed relatively little memory.

- **Hard Setups**:  
  - Solved 2 of the 4 difficult setups (improvement over Meta 1, which solved only 1).  
  - Required little time and memory for those it solved.  
  - Nevertheless, it failed to solve the remaining 2 hard deals.


---
### Automoves

- **Observation**: Automoves generally have a positive impact on solution quality, helping reduce the manual moves needed.  
- **Caveat**: For certain algorithms (DFS, IDS, Greedy), automoves can significantly affect run times, sometimes prolonging the search despite improving solution quality.

---
### Conclusions

1. **Uninformed Searches (BFS, DFS, IDS)**  
   - Ineffective for FreeCell-scale problems, either running out of memory (BFS) or failing to find any solution (DFS, IDS) for larger decks.  
   - Even at 12 cards, they often produce poor or partial solutions; “Empty to Empty” can help slightly, but only for small deals.

2. **A * with Heuristic 2**  
   - Remains the top algorithm overall for random deals, striking the best balance between speed, memory, and solution quality.  
   - However, it did fail to solve 1 out of 4 difficult setups in our tests.

3. **A * with Heuristic 3**  
   - Second-best behind Heuristic 2.  
   - Solved all 4 difficult deals but took more time/memory than it did with easy scenarios, and solutions were slightly worse than Heu2.

4. **Weighted A***  
   - Potentially faster than standard A* for some deals, but solutions remain suboptimal.  

5. **Greedy**  
   - Faster on simpler deals but performed poorly on more complex ones, using large amounts of memory/time.

6. **Meta-Heuristic 1**  
   - Inconsistent; solved only 1 of 4 hard setups.  
   - High memory usage in tough scenarios.

7. **Meta-Heuristic 2**  
   - Very good for easy setups: fastest on average, with solutions surpassing A* Heuristic 3 yet still below A* Heuristic 2.  
   - Better than Meta 1 on hard setups, solving 2 of 4 deals.  
   - Low time and memory for those solved but did not cover all hard cases.

8. **General Recommendation**  
   - **A* Heuristic 2** is the safest bet for a wide variety of deals, offering an excellent trade-off of performance and solution quality.  
   - For extremely difficult setups, consider combining heuristics or advanced optimizations (e.g., meta-heuristic approaches) to improve coverage and success rates.  
   - Meta-Heuristic 2 shows promise in speeding up solution times for certain deals, though it is not as reliable as the top A* methods.
  
---

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

### Empty-to-Empty Optimization (E2E)
When enabled, eliminates unnecessary moves between empty cascades:
- Disables unnecessary moves between empty spaces
- Significantly improves performance of uninformed search algorithms (DFS and IDS)
- Toggle with "E2E Moves Off/On" button in both player and solver modes

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
