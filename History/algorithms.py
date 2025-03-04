import heapq
from collections import deque
from PerformaceMetrics import PerformanceMetrics

from Freecell_Work import FreeCellGame


# Solver using A* search
def solve_freecell_astar(game):
    metrics = PerformanceMetrics()
    metrics.start()

    # Priority queue for A* search - f(n) = g(n) + h(n)
    # Where g(n) is the path cost (number of moves) and h(n) is the heuristic
    queue = [(game.heuristic3(), id(game), game, [])]
    heapq.heapify(queue)

    # Set to keep track of visited states
    visited = set()
    visited.add(hash(game))

    # Maximum number of states to explore
    max_states = 500000
    metrics.states_explored = 0
    metrics.states_generated = 1  # Count initial state
    metrics.max_queue_size = 1  # Initial queue size

    while queue and metrics.states_explored < max_states:
        _, _, current_game, moves = heapq.heappop(queue)
        metrics.states_explored += 1

        # Update max depth
        metrics.max_depth_reached = max(metrics.max_depth_reached, len(moves))

        # Check if the game is solved
        if current_game.is_solved():
            metrics.stop(moves)
            return moves, metrics

        # Get all valid moves from the current state
        valid_moves = current_game.get_valid_moves()

        for move in valid_moves:
            # Create a new game state by making the move
            new_game = FreeCellGame(current_game)
            new_game.make_move(move)
            metrics.states_generated += 1

            # Skip if we've seen this state before
            new_hash = hash(new_game)
            if new_hash in visited:
                continue

            # Add the new state to the queue
            new_moves = moves + [move]
            # A* uses f(n) = g(n) + h(n) for sorting
            heapq.heappush(
                queue,
                (
                    new_game.heuristic3() + len(new_moves),
                    id(new_game),
                    new_game,
                    new_moves,
                ),
            )
            visited.add(new_hash)

            # Update max queue size
            metrics.max_queue_size = max(metrics.max_queue_size, len(queue))

    metrics.stop()
    return None, metrics  # No solution found within constraints


# Solver using Best-First Search
def solve_freecell_bestfirst(game):
    metrics = PerformanceMetrics()
    metrics.start()

    # Priority queue for Best-First search - only uses h(n)
    # Unlike A*, Best-First only considers the heuristic value, not the path cost
    queue = [(game.heuristic(), id(game), game, [])]
    heapq.heapify(queue)

    # Set to keep track of visited states
    visited = set()
    visited.add(hash(game))

    # Maximum number of states to explore
    max_states = 15000
    metrics.states_explored = 0
    metrics.states_generated = 1  # Count initial state
    metrics.max_queue_size = 1  # Initial queue size

    while queue and metrics.states_explored < max_states:
        _, _, current_game, moves = heapq.heappop(queue)
        metrics.states_explored += 1

        # Update max depth
        metrics.max_depth_reached = max(metrics.max_depth_reached, len(moves))

        # Check if the game is solved
        if current_game.is_solved():
            metrics.stop(moves)
            return moves, metrics

        # Get all valid moves from the current state
        valid_moves = current_game.get_valid_moves()

        for move in valid_moves:
            # Create a new game state by making the move
            new_game = FreeCellGame(current_game)
            new_game.make_move(move)
            metrics.states_generated += 1

            # Skip if we've seen this state before
            new_hash = hash(new_game)
            if new_hash in visited:
                continue

            # Add the new state to the queue
            new_moves = moves + [move]
            # Best-First only uses the heuristic h(n) for sorting, ignoring path length
            heapq.heappush(
                queue, (new_game.heuristic(), id(new_game), new_game, new_moves)
            )
            visited.add(new_hash)

            # Update max queue size
            metrics.max_queue_size = max(metrics.max_queue_size, len(queue))

    metrics.stop()
    return None, metrics  # No solution found within constraints


# Solver using Breadth-First Search (BFS)
def solve_freecell_bfs(game):
    metrics = PerformanceMetrics()
    metrics.start()

    # Queue for BFS (FIFO)
    queue = deque([(game, [])])

    # Set to keep track of visited states
    visited = set()
    visited.add(hash(game))

    # Maximum number of states to explore
    max_states = 15000
    metrics.states_explored = 0
    metrics.states_generated = 1  # Count initial state
    metrics.max_queue_size = 1  # Initial queue size

    while queue and metrics.states_explored < max_states:
        current_game, moves = queue.popleft()  # FIFO queue - get the oldest state first
        metrics.states_explored += 1

        # Update max depth
        metrics.max_depth_reached = max(metrics.max_depth_reached, len(moves))

        # Check if the game is solved
        if current_game.is_solved():
            metrics.stop(moves)
            return moves, metrics

        # Get all valid moves from the current state
        valid_moves = current_game.get_valid_moves()

        for move in valid_moves:
            # Create a new game state by making the move
            new_game = FreeCellGame(current_game)
            new_game.make_move(move)
            metrics.states_generated += 1

            # Skip if we've seen this state before
            new_hash = hash(new_game)
            if new_hash in visited:
                continue

            # Add the new state to the queue
            new_moves = moves + [move]
            queue.append((new_game, new_moves))
            visited.add(new_hash)

            # Update max queue size
            metrics.max_queue_size = max(metrics.max_queue_size, len(queue))

    metrics.stop()
    return None, metrics  # No solution found within constraints


# Solver using Depth-First Search (DFS)
def solve_freecell_dfs(game):
    metrics = PerformanceMetrics()
    metrics.start()

    # Stack for DFS (LIFO)
    stack = [(game, [])]

    # Set to keep track of visited states
    visited = set()
    visited.add(hash(game))

    # Maximum number of states to explore
    max_states = 15000
    # To prevent infinite depth, we'll also set a maximum depth limit
    max_depth = 50
    metrics.states_explored = 0
    metrics.states_generated = 1  # Count initial state
    metrics.max_queue_size = 1  # Initial stack size

    while stack and metrics.states_explored < max_states:
        current_game, moves = stack.pop()  # LIFO stack - get the newest state first
        metrics.states_explored += 1

        # Update max depth
        metrics.max_depth_reached = max(metrics.max_depth_reached, len(moves))

        # Skip if we've gone too deep
        if len(moves) > max_depth:
            continue

        # Check if the game is solved
        if current_game.is_solved():
            metrics.stop(moves)
            return moves, metrics

        # Get all valid moves from the current state
        valid_moves = current_game.get_valid_moves()

        # For DFS, we explore moves in reverse order to prioritize
        # moves that are more likely to reach a solution
        for move in reversed(valid_moves):
            # Create a new game state by making the move
            new_game = FreeCellGame(current_game)
            new_game.make_move(move)
            metrics.states_generated += 1

            # Skip if we've seen this state before
            new_hash = hash(new_game)
            if new_hash in visited:
                continue

            # Add the new state to the stack
            new_moves = moves + [move]
            stack.append((new_game, new_moves))
            visited.add(new_hash)

            # Update max queue size
            metrics.max_queue_size = max(metrics.max_queue_size, len(stack))

    metrics.stop()
    return None, metrics  # No solution found within constraints


# Wrapper function to call the selected algorithm
def solve_freecell(game, algorithm="astar"):
    if algorithm == "astar":
        return solve_freecell_astar(game)
    elif algorithm == "bestfirst":
        return solve_freecell_bestfirst(game)
    elif algorithm == "bfs":
        return solve_freecell_bfs(game)
    elif algorithm == "dfs":
        return solve_freecell_dfs(game)
    else:
        print(f"Unknown algorithm: {algorithm}, defaulting to A*")
        return solve_freecell_astar(game)
