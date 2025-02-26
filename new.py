import random
import sys
import time
from collections import deque
import heapq
import pygame

# Initialize pygame
pygame.init()

# Constants
CARD_WIDTH = 80
CARD_HEIGHT = 120
CARD_MARGIN = 10
ANIMATION_SPEED = 10

# Screen dimensions
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 100, 0)  # Darker green for background
RED = (180, 0, 0)  # Muted red
BLUE = (0, 0, 180)  # Muted blue
GRAY = (200, 200, 200)
DARK_GRAY = (60, 60, 60)
HIGHLIGHT = (220, 220, 150)  # Subtle highlight color

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("FreeCel Solver")

# Font
font = pygame.font.SysFont("Arial", 22)
small_font = pygame.font.SysFont("Arial", 16)
mini_font = pygame.font.SysFont("Arial", 14)

# Animation Control
animation_delay = 0.5  # seconds between moves
paused = False


# Card class
class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.color = RED if suit in ["H", "D"] else BLACK

    def __str__(self):
        ranks = {1: "A", 11: "J", 12: "Q", 13: "K"}
        rank_str = ranks.get(self.rank, str(self.rank))
        return f"{rank_str}{self.suit}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if other is None:
            return False
        return self.suit == other.suit and self.rank == other.rank

    def __hash__(self):
        return hash((self.suit, self.rank))

    def draw(self, x, y, highlighted=False):
        # Draw card background
        bg_color = HIGHLIGHT if highlighted else WHITE
        pygame.draw.rect(screen, bg_color, (x, y, CARD_WIDTH, CARD_HEIGHT))
        border_color = DARK_GRAY
        pygame.draw.rect(screen, border_color, (x, y, CARD_WIDTH, CARD_HEIGHT), 1)

        # Draw card value
        ranks = {1: "A", 11: "J", 12: "Q", 13: "K"}
        rank_str = ranks.get(self.rank, str(self.rank))
        suit_symbols = {"H": "♥", "D": "♦", "C": "♣", "S": "♠"}

        # Draw rank at top-left
        rank_text = small_font.render(rank_str, True, self.color)
        screen.blit(rank_text, (x + 5, y + 5))

        # Draw suit at top-left
        suit_text = small_font.render(suit_symbols[self.suit], True, self.color)
        screen.blit(suit_text, (x + 5, y + 25))

        # Draw large suit in the middle
        big_suit = font.render(suit_symbols[self.suit], True, self.color)
        screen.blit(big_suit, (x + CARD_WIDTH // 2 - 10, y + CARD_HEIGHT // 2 - 15))


# Game state class
class FreeCellGame:
    def __init__(self, initial_state=None):
        # Cascades (8 columns)
        self.cascades = [[] for _ in range(8)]
        # Free cells (4 individual cells)
        self.free_cells = [None] * 4
        # Foundations (4 piles, one for each suit)
        self.foundations = {"H": [], "D": [], "C": [], "S": []}
        self.moves = []

        # If no initial state is provided, create a new game
        if initial_state is None:
            self.new_game()
        else:
            # Copy the provided state
            for i in range(8):
                self.cascades[i] = initial_state.cascades[i].copy()
            self.free_cells = initial_state.free_cells.copy()
            for suit in self.foundations:
                self.foundations[suit] = initial_state.foundations[suit].copy()

    def new_game(self):
        # Create a deck of cards
        suits = ["H", "D", "C", "S"]
        ranks = list(range(1, 14))  # 1 (Ace) to 13 (King)

        deck = [Card(suit, rank) for suit in suits for rank in ranks]
        random.shuffle(deck)

        # Deal cards to the cascades
        for i, card in enumerate(deck):
            cascade_idx = i % 8
            self.cascades[cascade_idx].append(card)

    def is_solved(self):
        # Check if all foundations have 13 cards each
        for suit in self.foundations:
            if len(self.foundations[suit]) != 13:
                return False
        return True

    def can_move_to_foundation(self, card):
        if card is None:
            return False

        foundation = self.foundations[card.suit]

        # If foundation is empty, we can only place an Ace
        if not foundation:
            return card.rank == 1

        # Otherwise, the card must be one rank higher than the top card
        return card.rank == foundation[-1].rank + 1

    def can_move_to_cascade(self, card, cascade_idx):
        if card is None:
            return False

        cascade = self.cascades[cascade_idx]

        # If cascade is empty, any card can be placed
        if not cascade:
            return True

        # Otherwise, the card must be one rank lower and different color
        top_card = cascade[-1]
        return card.rank == top_card.rank - 1 and (
            (card.color == RED and top_card.color == BLACK)
            or (card.color == BLACK and top_card.color == RED)
        )

    def get_valid_moves(self):
        valid_moves = []

        # Check all possible source cards (from cascades and free cells)
        for source_type in ["cascade", "free_cell"]:
            if source_type == "cascade":
                sources = [
                    (i, card)
                    for i, cascade in enumerate(self.cascades)
                    for j, card in enumerate(cascade)
                    if j == len(cascade) - 1
                ]
            else:  # free_cell
                sources = [
                    (i, card)
                    for i, card in enumerate(self.free_cells)
                    if card is not None
                ]

            for source_idx, card in sources:
                # Check if card can be moved to a foundation
                if self.can_move_to_foundation(card):
                    valid_moves.append(
                        ("foundation", source_type, source_idx, card.suit)
                    )

                # Check if card can be moved to a free cell
                if source_type == "cascade":  # Can only move from cascade to free cell
                    for i, cell in enumerate(self.free_cells):
                        if cell is None:
                            valid_moves.append(
                                ("free_cell", source_type, source_idx, i)
                            )
                            break  # Only need one free cell

                # Check if card can be moved to another cascade
                for i, cascade in enumerate(self.cascades):
                    if (
                        source_type != "cascade" or i != source_idx
                    ) and self.can_move_to_cascade(card, i):
                        valid_moves.append(("cascade", source_type, source_idx, i))

        return valid_moves

    def make_move(self, move):
        move_type, source_type, source_idx, dest = move

        # Get the card from the source
        if source_type == "cascade":
            card = self.cascades[source_idx].pop()
        else:  # free_cell
            card = self.free_cells[source_idx]
            self.free_cells[source_idx] = None

        # Place the card in the destination
        if move_type == "foundation":
            self.foundations[dest].append(card)
        elif move_type == "free_cell":
            self.free_cells[dest] = card
        else:  # cascade
            self.cascades[dest].append(card)

        # Record the move
        self.moves.append(move)

    def heuristic(self):
        """
        A heuristic function to estimate how close the game is to being solved.
        Lower scores are better.
        """
        score = 0

        # Score for cards in foundations (prefer more cards in foundations)
        for suit in self.foundations:
            score -= len(self.foundations[suit]) * 10

        # Score for cards in free cells (prefer fewer cards in free cells)
        for cell in self.free_cells:
            if cell is not None:
                score += 5

        # Score for cards in cascades (prefer ordered cards)
        for cascade in self.cascades:
            for i in range(len(cascade) - 1):
                card = cascade[i]
                next_card = cascade[i + 1]

                # Penalty for unordered cards
                if not (
                    card.rank == next_card.rank + 1
                    and (
                        (card.color == RED and next_card.color == BLACK)
                        or (card.color == BLACK and next_card.color == RED)
                    )
                ):
                    score += 1

        return score

    def __lt__(self, other):
        # Required for heapq
        return self.heuristic() < other.heuristic()

    def __eq__(self, other):
        # Compare all components of the game state
        if not isinstance(other, FreeCellGame):
            return False

        return (
            self.cascades == other.cascades
            and self.free_cells == other.free_cells
            and self.foundations == other.foundations
        )

    def __hash__(self):
        # Hash for state comparison (needed for visited set)
        cascades_tuple = tuple(tuple(col) for col in self.cascades)
        free_cells_tuple = tuple(self.free_cells)
        foundations_tuple = tuple(
            (suit, tuple(self.foundations[suit]))
            for suit in sorted(self.foundations.keys())
        )

        return hash((cascades_tuple, free_cells_tuple, foundations_tuple))

    def draw(self, highlight_move=None, stats=None, algorithm="A*"):
        screen.fill(GREEN)

        # Draw title
        title = font.render("FreeCel Solver", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - 60, 10))

        # Draw algorithm info
        algo_text = font.render(f"Algorithm: {algorithm}", True, WHITE)
        screen.blit(algo_text, (SCREEN_WIDTH // 2 - 60, 40))

        # Draw stats if available (minimized)
        if stats:
            moves, states = stats
            stats_text = mini_font.render(
                f"Moves: {len(moves)} | States: {states}", True, WHITE
            )
            screen.blit(stats_text, (SCREEN_WIDTH // 2 - 80, 70))

        # Source and destination positions for drawing the movement line
        source_pos = None
        dest_pos = None

        # Draw free cells
        for i, card in enumerate(self.free_cells):
            x = 50 + i * (CARD_WIDTH + CARD_MARGIN)
            y = 100

            # Check if this free cell is highlighted in the current move
            is_highlighted = False
            if highlight_move:
                move_type, source_type, source_idx, dest = highlight_move
                if move_type == "free_cell" and dest == i:
                    is_highlighted = True
                    dest_pos = (x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2)
                elif source_type == "free_cell" and source_idx == i:
                    is_highlighted = True
                    source_pos = (x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2)

            # Draw cell background
            cell_color = GRAY
            pygame.draw.rect(screen, cell_color, (x, y, CARD_WIDTH, CARD_HEIGHT))

            # Draw border - blue for highlighted cells, dark gray for normal
            border_color = BLUE if is_highlighted else DARK_GRAY
            border_width = 3 if is_highlighted else 1
            pygame.draw.rect(
                screen, border_color, (x, y, CARD_WIDTH, CARD_HEIGHT), border_width
            )

            if card:
                card.draw(x, y, is_highlighted)

            # Label the free cell
            label = mini_font.render(f"Free Cell {i + 1}", True, WHITE)
            screen.blit(label, (x, y - 20))

        # Draw foundations
        for i, suit in enumerate(["H", "D", "C", "S"]):
            x = SCREEN_WIDTH - 50 - CARD_WIDTH - i * (CARD_WIDTH + CARD_MARGIN)
            y = 100

            # Check if this foundation is highlighted in the current move
            is_highlighted = False
            if highlight_move:
                move_type, source_type, source_idx, dest = highlight_move
                if move_type == "foundation" and dest == suit:
                    is_highlighted = True
                    dest_pos = (x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2)

            # Draw foundation background
            cell_color = GRAY
            pygame.draw.rect(screen, cell_color, (x, y, CARD_WIDTH, CARD_HEIGHT))

            # Draw border - blue for highlighted foundations, dark gray for normal
            border_color = BLUE if is_highlighted else DARK_GRAY
            border_width = 3 if is_highlighted else 1
            pygame.draw.rect(
                screen, border_color, (x, y, CARD_WIDTH, CARD_HEIGHT), border_width
            )

            if self.foundations[suit]:
                self.foundations[suit][-1].draw(x, y, is_highlighted)
            else:
                # Draw suit symbol
                suit_symbols = {"H": "♥", "D": "♦", "C": "♣", "S": "♠"}
                suit_color = RED if suit in ["H", "D"] else BLACK
                suit_text = font.render(suit_symbols[suit], True, suit_color)
                screen.blit(
                    suit_text, (x + CARD_WIDTH // 2 - 10, y + CARD_HEIGHT // 2 - 15)
                )

            # Label the foundation
            label = mini_font.render(f"{suit} Foundation", True, WHITE)
            screen.blit(label, (x, y - 20))

        # Draw cascades
        for i, cascade in enumerate(self.cascades):
            x = 50 + i * (CARD_WIDTH + CARD_MARGIN)
            y = 250

            # Draw cascade label
            label = mini_font.render(f"Cascade {i + 1}", True, WHITE)
            screen.blit(label, (x, y - 20))

            # Draw cascade outline (minimal)
            pygame.draw.rect(screen, GRAY, (x, y, CARD_WIDTH, CARD_HEIGHT), 1)

            # Draw cards in cascade
            for j, card in enumerate(cascade):
                card_y = y + j * 30  # Overlap cards

                # Highlight the card if it's part of the current move
                is_highlighted = False
                if highlight_move:
                    move_type, source_type, source_idx, dest = highlight_move
                    if (
                        source_type == "cascade"
                        and source_idx == i
                        and j == len(cascade) - 1
                    ):
                        is_highlighted = True
                        source_pos = (x + CARD_WIDTH // 2, card_y + CARD_HEIGHT // 2)
                    elif move_type == "cascade" and dest == i and j == len(cascade) - 1:
                        is_highlighted = True
                        dest_pos = (x + CARD_WIDTH // 2, card_y + CARD_HEIGHT // 2)

                # Draw card with optional blue border
                card.draw(x, card_y, False)  # Draw the card normally

                # If card is highlighted, add blue border on top
                if is_highlighted:
                    pygame.draw.rect(
                        screen, BLUE, (x, card_y, CARD_WIDTH, CARD_HEIGHT), 3
                    )

        # Draw line between source and destination if both exist
        if highlight_move and source_pos and dest_pos:
            # Draw the line connecting source and destination
            pygame.draw.line(screen, BLUE, source_pos, dest_pos, 3)

            # Draw a small arrow at the destination end
            arrow_size = 8
            angle = pygame.math.Vector2(
                dest_pos[0] - source_pos[0], dest_pos[1] - source_pos[1]
            ).normalize()
            pygame.draw.polygon(
                screen,
                BLUE,
                [
                    dest_pos,
                    (
                        int(
                            dest_pos[0]
                            - arrow_size * angle.x
                            + arrow_size * angle.y / 2
                        ),
                        int(
                            dest_pos[1]
                            - arrow_size * angle.y
                            - arrow_size * angle.x / 2
                        ),
                    ),
                    (
                        int(
                            dest_pos[0]
                            - arrow_size * angle.x
                            - arrow_size * angle.y / 2
                        ),
                        int(
                            dest_pos[1]
                            - arrow_size * angle.y
                            + arrow_size * angle.x / 2
                        ),
                    ),
                ],
            )

        # Draw simplified control panel at the bottom - reorganized to prevent overlapping
        button_y = SCREEN_HEIGHT - 60
        button_height = 40
        button_margin = 10

        # Draw algorithm buttons (minimalist style) with improved spacing
        algorithm_buttons = [
            ("A*", BLUE, 50),
            ("Best-First", (0, 70, 140), 170),
            ("BFS", (140, 0, 140), 290),
            ("DFS", (140, 70, 0), 410),
            ("New Game", RED, 530),  # Moved New Game button next to DFS
        ]

        for label, color, x_pos in algorithm_buttons:
            # Determine button width based on text length
            btn_width = 110
            if label == "Best-First":
                btn_width = 120
            elif label == "New Game":
                btn_width = 120

            # Create button rectangle with proper spacing
            btn_rect = pygame.Rect(x_pos, button_y, btn_width, button_height)

            # Draw button with improved resolution
            pygame.draw.rect(screen, color, btn_rect)
            pygame.draw.rect(
                screen, BLACK, btn_rect, 1
            )  # Add thin border for better definition

            # Render text with proper centering
            btn_text = small_font.render(
                f"Solve with {label}" if label not in ["New Game"] else label,
                True,
                WHITE,
            )
            text_x = x_pos + (btn_width - btn_text.get_width()) // 2
            text_y = button_y + (button_height - btn_text.get_height()) // 2
            screen.blit(btn_text, (text_x, text_y))

        # Right-aligned controls
        # Step button
        step_btn_width = 100
        step_rect = pygame.Rect(
            SCREEN_WIDTH - step_btn_width - 20, button_y, step_btn_width, button_height
        )
        pygame.draw.rect(screen, (0, 140, 0), step_rect)
        pygame.draw.rect(screen, BLACK, step_rect, 1)
        step_text = small_font.render("Step", True, WHITE)
        screen.blit(step_text, (SCREEN_WIDTH - step_btn_width + 15, button_y + 10))

        # Pause button (minimal)
        pause_btn_width = 100
        pause_rect = pygame.Rect(
            SCREEN_WIDTH - step_btn_width - pause_btn_width - 30,
            button_y,
            pause_btn_width,
            button_height,
        )
        pygame.draw.rect(screen, DARK_GRAY, pause_rect)
        pygame.draw.rect(screen, BLACK, pause_rect, 1)
        pause_text = small_font.render("Pause" if not paused else "Resume", True, WHITE)
        screen.blit(
            pause_text,
            (SCREEN_WIDTH - step_btn_width - pause_btn_width - 10, button_y + 10),
        )

        # Minimal animation speed control (above the buttons)
        control_panel_rect = pygame.Rect(SCREEN_WIDTH - 230, button_y - 50, 210, 30)
        pygame.draw.rect(screen, DARK_GRAY, control_panel_rect)
        pygame.draw.rect(screen, BLACK, control_panel_rect, 1)
        speed_text = mini_font.render(
            f"Animation Speed: {animation_delay:.1f}s", True, WHITE
        )
        screen.blit(speed_text, (SCREEN_WIDTH - 220, button_y - 45))

        # Simple info at the bottom
        info_text = mini_font.render(
            "Shortcuts: Space=Pause, N=New Game, S=Step, +/- = Speed", True, WHITE
        )
        screen.blit(info_text, (50, SCREEN_HEIGHT - 20))

        pygame.display.flip()


# Solver using A* search
def solve_freecell_astar(game):
    # Priority queue for A* search - f(n) = g(n) + h(n)
    # Where g(n) is the path cost (number of moves) and h(n) is the heuristic
    queue = [(game.heuristic(), id(game), game, [])]
    heapq.heapify(queue)

    # Set to keep track of visited states
    visited = set()
    visited.add(hash(game))

    # Maximum number of states to explore
    max_states = 15000
    states_explored = 0

    while queue and states_explored < max_states:
        _, _, current_game, moves = heapq.heappop(queue)
        states_explored += 1

        # Check if the game is solved
        if current_game.is_solved():
            return moves, states_explored

        # Get all valid moves from the current state
        valid_moves = current_game.get_valid_moves()

        for move in valid_moves:
            # Create a new game state by making the move
            new_game = FreeCellGame(current_game)
            new_game.make_move(move)

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
                    new_game.heuristic() + len(new_moves),
                    id(new_game),
                    new_game,
                    new_moves,
                ),
            )
            visited.add(new_hash)

    return None, states_explored  # No solution found within constraints


# Solver using Best-First Search
def solve_freecell_bestfirst(game):
    # Priority queue for Best-First search - only uses h(n)
    # Unlike A*, Best-First only considers the heuristic value, not the path cost
    queue = [(game.heuristic(), id(game), game, [])]
    heapq.heapify(queue)

    # Set to keep track of visited states
    visited = set()
    visited.add(hash(game))

    # Maximum number of states to explore
    max_states = 15000
    states_explored = 0

    while queue and states_explored < max_states:
        _, _, current_game, moves = heapq.heappop(queue)
        states_explored += 1

        # Check if the game is solved
        if current_game.is_solved():
            return moves, states_explored

        # Get all valid moves from the current state
        valid_moves = current_game.get_valid_moves()

        for move in valid_moves:
            # Create a new game state by making the move
            new_game = FreeCellGame(current_game)
            new_game.make_move(move)

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

    return None, states_explored  # No solution found within constraints


# Solver using Breadth-First Search (BFS)
def solve_freecell_bfs(game):
    # Queue for BFS (FIFO)
    queue = deque([(game, [])])

    # Set to keep track of visited states
    visited = set()
    visited.add(hash(game))

    # Maximum number of states to explore
    max_states = 15000
    states_explored = 0

    while queue and states_explored < max_states:
        current_game, moves = queue.popleft()  # FIFO queue - get the oldest state first
        states_explored += 1

        # Check if the game is solved
        if current_game.is_solved():
            return moves, states_explored

        # Get all valid moves from the current state
        valid_moves = current_game.get_valid_moves()

        for move in valid_moves:
            # Create a new game state by making the move
            new_game = FreeCellGame(current_game)
            new_game.make_move(move)

            # Skip if we've seen this state before
            new_hash = hash(new_game)
            if new_hash in visited:
                continue

            # Add the new state to the queue
            new_moves = moves + [move]
            queue.append((new_game, new_moves))
            visited.add(new_hash)

    return None, states_explored  # No solution found within constraints


# Solver using Depth-First Search (DFS)
def solve_freecell_dfs(game):
    # Stack for DFS (LIFO)
    stack = [(game, [])]

    # Set to keep track of visited states
    visited = set()
    visited.add(hash(game))

    # Maximum number of states to explore
    max_states = 15000
    # To prevent infinite depth, we'll also set a maximum depth limit
    max_depth = 50
    states_explored = 0

    while stack and states_explored < max_states:
        current_game, moves = stack.pop()  # LIFO stack - get the newest state first
        states_explored += 1

        # Skip if we've gone too deep
        if len(moves) > max_depth:
            continue

        # Check if the game is solved
        if current_game.is_solved():
            return moves, states_explored

        # Get all valid moves from the current state
        valid_moves = current_game.get_valid_moves()

        # For DFS, we explore moves in reverse order to prioritize
        # moves that are more likely to reach a solution
        for move in reversed(valid_moves):
            # Create a new game state by making the move
            new_game = FreeCellGame(current_game)
            new_game.make_move(move)

            # Skip if we've seen this state before
            new_hash = hash(new_game)
            if new_hash in visited:
                continue

            # Add the new state to the stack
            new_moves = moves + [move]
            stack.append((new_game, new_moves))
            visited.add(new_hash)

    return None, states_explored  # No solution found within constraints


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


# Main game loop
def main():
    global animation_delay, paused

    game = FreeCellGame()
    solution = None
    solution_index = 0
    solving = False
    current_algorithm = "A*"
    stats = None
    clock = pygame.time.Clock()
    last_move_time = 0

    while True:
        current_time = time.time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                # Keyboard shortcuts
                if event.key == pygame.K_SPACE:
                    # Toggle pause
                    paused = not paused

                elif event.key == pygame.K_n:
                    # New game
                    game = FreeCellGame()
                    solution = None
                    solution_index = 0
                    solving = False
                    stats = None

                elif (
                    event.key == pygame.K_s
                    and solution
                    and solution_index < len(solution)
                ):
                    # Step forward
                    move = solution[solution_index]
                    game.make_move(move)
                    solution_index += 1

                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    # Speed up animation
                    animation_delay = max(0.1, animation_delay - 0.1)

                elif event.key == pygame.K_MINUS:
                    # Slow down animation
                    animation_delay = min(2.0, animation_delay + 0.1)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                x, y = pygame.mouse.get_pos()
                button_y = SCREEN_HEIGHT - 60
                button_height = 40

                # Check algorithm buttons
                if button_y <= y <= button_y + button_height:
                    # A* button
                    if 50 <= x <= 160:
                        print("Solving with A*...")
                        solving = True
                        paused = False
                        current_algorithm = "A*"
                        solution, states_explored = solve_freecell(game, "astar")
                        solution_index = 0
                        if solution:
                            print(
                                f"A* solution found with {len(solution)} moves! Explored {states_explored} states."
                            )
                            stats = (solution, states_explored)
                        else:
                            print(
                                f"No A* solution found. Explored {states_explored} states."
                            )
                            solving = False

                    # Best-First button
                    elif 170 <= x <= 290:
                        print("Solving with Best-First...")
                        solving = True
                        paused = False
                        current_algorithm = "Best-First"
                        solution, states_explored = solve_freecell(game, "bestfirst")
                        solution_index = 0
                        if solution:
                            print(
                                f"Best-First solution found with {len(solution)} moves! Explored {states_explored} states."
                            )
                            stats = (solution, states_explored)
                        else:
                            print(
                                f"No Best-First solution found. Explored {states_explored} states."
                            )
                            solving = False

                    # BFS button
                    elif 290 <= x <= 400:
                        print("Solving with BFS...")
                        solving = True
                        paused = False
                        current_algorithm = "BFS"
                        solution, states_explored = solve_freecell(game, "bfs")
                        solution_index = 0
                        if solution:
                            print(
                                f"BFS solution found with {len(solution)} moves! Explored {states_explored} states."
                            )
                            stats = (solution, states_explored)
                        else:
                            print(
                                f"No BFS solution found. Explored {states_explored} states."
                            )
                            solving = False

                    # DFS button
                    elif 410 <= x <= 520:
                        print("Solving with DFS...")
                        solving = True
                        paused = False
                        current_algorithm = "DFS"
                        solution, states_explored = solve_freecell(game, "dfs")
                        solution_index = 0
                        if solution:
                            print(
                                f"DFS solution found with {len(solution)} moves! Explored {states_explored} states."
                            )
                            stats = (solution, states_explored)
                        else:
                            print(
                                f"No DFS solution found. Explored {states_explored} states."
                            )
                            solving = False

                    # New Game button (now next to DFS)
                    elif 530 <= x <= 650:
                        game = FreeCellGame()
                        solution = None
                        solution_index = 0
                        solving = False
                        stats = None

                    # Pause button
                    elif SCREEN_WIDTH - 230 <= x <= SCREEN_WIDTH - 130:
                        paused = not paused

                    # Step button
                    elif SCREEN_WIDTH - 120 <= x <= SCREEN_WIDTH - 20:
                        if solution and solution_index < len(solution):
                            move = solution[solution_index]
                            game.make_move(move)
                            solution_index += 1

        # Process automatic solution steps if not paused
        if solving and solution and solution_index < len(solution) and not paused:
            # Check if it's time for the next move
            if current_time - last_move_time >= animation_delay:
                highlight_move = solution[solution_index]
                game.draw(
                    highlight_move=highlight_move,
                    stats=stats,
                    algorithm=current_algorithm,
                )
                pygame.display.flip()
                time.sleep(0.2)  # Brief pause to show the highlighted move

                game.make_move(highlight_move)
                solution_index += 1
                last_move_time = current_time

                if solution_index >= len(solution):
                    solving = False
        else:
            # Regular drawing without animation delay
            game.draw(
                stats=stats,
                algorithm=current_algorithm,
                highlight_move=solution[solution_index - 1]
                if solution and solution_index > 0 and solution_index < len(solution)
                else None,
            )

        # Cap the frame rate
        clock.tick(60)


if __name__ == "__main__":
    main()
