import random
import sys
import time
from collections import deque
import heapq
import pygame

from PerformanceMetrics import PerformanceMetrics


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
GREEN = (0, 128, 0)  # Darker green for background
RED = (180, 0, 0)  # Muted red
BLUE = (0, 0, 180)  # Muted blue
GRAY = (200, 200, 200)
DARK_GRAY = (169, 169, 169)
HIGHLIGHT = (220, 220, 150)  # Subtle highlight color

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("FreeCel Solver")

# Font
font = pygame.font.SysFont("Arial", 22)
small_font = pygame.font.SysFont("Arial", 18, bold=True)
mini_font = pygame.font.SysFont("Arial", 14)


# Animation Control
animation_delay = 0.5  # seconds between moves
paused = False

# Game timer
game_timer = 0.0


class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.color = RED if suit in ["H", "D"] else BLACK
        self.selected = False

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

        # Prepare rank string
        ranks = {1: "A", 11: "J", 12: "Q", 13: "K"}
        rank_str = ranks.get(self.rank, str(self.rank))

        # Suit symbols map
        suit_symbols = {"H": "♥", "D": "♦", "C": "♣", "S": "♠"}

        # Draw rank and suit at top-left
        rank_text = small_font.render(rank_str, True, self.color)
        suit_text = small_font.render(suit_symbols[self.suit], True, self.color)

        screen.blit(rank_text, (x + 5, y + 5))
        screen.blit(suit_text, (x + 5 + rank_text.get_width(), y + 5))

        # Draw large suit in center
        big_suit = font.render(suit_symbols[self.suit], True, self.color)
        screen.blit(
            big_suit,
            (
                x + CARD_WIDTH // 2 - big_suit.get_width() // 2,
                y + CARD_HEIGHT // 2 - big_suit.get_height() // 2,
            ),
        )

        # Draw rank and suit at bottom-right (inverted)
        bottom_rank = small_font.render(rank_str, True, self.color)
        bottom_suit = small_font.render(suit_symbols[self.suit], True, self.color)

        # Position at bottom right
        screen.blit(
            bottom_suit,
            (
                x + CARD_WIDTH - 5 - bottom_suit.get_width() - bottom_rank.get_width(),
                y + CARD_HEIGHT - 25,
            ),
        )
        screen.blit(
            bottom_rank,
            (x + CARD_WIDTH - 5 - bottom_rank.get_width(), y + CARD_HEIGHT - 25),
        )


# Game state class
class FreeCellGame:
    def __init__(self, initial_state=None, deck_size=52):
        self.cascades = [[] for _ in range(8)]
        self.free_cells = [None] * 4
        self.foundations = {"H": [], "D": [], "C": [], "S": []}
        self.moves = []
        self.deck_size = deck_size  # Store deck size (52, 28, or 12)

        if initial_state is None:
            self.new_game()
        else:
            for i in range(8):
                self.cascades[i] = initial_state.cascades[i].copy()
            self.free_cells = initial_state.free_cells.copy()
            for suit in self.foundations:
                self.foundations[suit] = initial_state.foundations[suit].copy()
            self.deck_size = initial_state.deck_size

    def new_game(self):
        suits = ["H", "D", "C", "S"]
        if self.deck_size == 52:
            ranks = list(range(1, 14))  # 1 (Ace) to 13 (King)
        elif self.deck_size == 28:
            ranks = list(range(1, 8))   # 1 (Ace) to 7
        elif self.deck_size == 12:
            ranks = list(range(1, 4))   # 1 (Ace) to 3
        else:
            raise ValueError("Invalid deck size")

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

    def _is_valid_sequence(self, cards):
        """
        Check if a list of cards forms a valid sequence (alternating colors, descending rank).
        Cards should be ordered from top (index 0) to bottom (last index).
        """
        if len(cards) <= 1:
            return True

        for i in range(len(cards) - 1):
            upper_card = cards[i]
            lower_card = cards[i + 1]
            # Check if upper_card is one rank lower and opposite color than lower_card
            if not (
                upper_card.rank + 1 == lower_card.rank
                and upper_card.color != lower_card.color
            ):
                return False
        return True

    def max_cards_movable(self, dest_idx=None):
        """
        Calculate the maximum number of cards that can be moved at once
        based on available free cells and empty cascades.

        Args:
            dest_idx: If provided, exclude this cascade from empty cascades count if it's empty

        Returns:
            Maximum number of cards that can be moved
        """
        # Count free cells
        num_free_cells = self.free_cells.count(None)

        # Count empty cascades (excluding the destination if it's empty)
        num_empty_cascades = 0
        for i, cascade in enumerate(self.cascades):
            if not cascade and (dest_idx is None or i != dest_idx):
                num_empty_cascades += 1

        # Formula: (free cells + 1) * 2^(empty cascades)
        return (num_free_cells + 1) * (2**num_empty_cascades)

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

        # Add supermove detection - only from cascades to cascades
        for src_idx, src_cascade in enumerate(self.cascades):
            if len(src_cascade) <= 1:  # Need at least 2 cards for a supermove
                continue

            for dest_idx, dest_cascade in enumerate(self.cascades):
                if src_idx == dest_idx:  # Can't move to the same cascade
                    continue

                # Calculate max movable cards for this specific destination
                max_movable = self.max_cards_movable(
                    dest_idx if not dest_cascade else None
                )

                # If we can't move multiple cards, skip supermove check
                if max_movable <= 1:
                    continue

                # Check for valid card sequences from various positions in the cascade
                for start_idx in range(len(src_cascade) - 2, -1, -1):
                    sequence = src_cascade[start_idx:]
                    sequence_length = len(sequence)

                    # If sequence length exceeds what we can move, skip to the next starting position
                    if sequence_length > max_movable:
                        continue

                    # Check if this sequence forms a valid sequence
                    if not self._is_valid_sequence(sequence):
                        continue

                    # Empty destination is always valid for a sequence
                    if not dest_cascade:
                        valid_moves.append(
                            ("supermove", "cascade", src_idx, dest_idx, sequence_length)
                        )
                        continue

                    # If destination is not empty, check if bottom card of sequence can be placed
                    bottom_seq_card = sequence[0]
                    top_dest_card = dest_cascade[-1]

                    if (
                        bottom_seq_card.rank == top_dest_card.rank - 1
                        and bottom_seq_card.color != top_dest_card.color
                    ):
                        valid_moves.append(
                            ("supermove", "cascade", src_idx, dest_idx, sequence_length)
                        )

        return valid_moves

    def make_move(self, move):
        move_type = move[0]

        if move_type == "supermove":
            # For supermoves: move = ("supermove", "cascade", source_idx, dest_idx, num_cards)
            _, source_type, source_idx, dest_idx, num_cards = move

            # Get the starting index in the source cascade
            start_idx = len(self.cascades[source_idx]) - num_cards

            # Get the cards to move
            cards_to_move = self.cascades[source_idx][start_idx:]

            # Remove cards from source
            self.cascades[source_idx] = self.cascades[source_idx][:start_idx]

            # Add cards to destination
            self.cascades[dest_idx].extend(cards_to_move)
        else:
            # Original code for single card moves
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

    def heuristic2(self):
        # Count cards that aren't in foundations yet
        cards_not_in_foundations = 0
        for suit in ["H", "D", "C", "S"]:
            cards_not_in_foundations += 13 - len(self.foundations[suit])

        # Basic admissible estimate
        # Each card will need at least 1 move to go to foundation
        return cards_not_in_foundations

    def heuristic3(self):
        cards_in_foundations = {
            suit: set(card.rank for card in self.foundations[suit])
            for suit in ["H", "D", "C", "S"]
        }

        # Calculate the minimum number of moves for each card
        total_min_moves = 0

        for cascade in self.cascades:
            for card in cascade:
                # A card can only move to foundation when all cards below are already there
                prereqs_missing = sum(
                    1
                    for r in range(1, card.rank)
                    if r not in cards_in_foundations[card.suit]
                )
                # Each card requires at least 1 move (more if prerequisites missing)
                min_moves = max(1, prereqs_missing)
                total_min_moves += min_moves

        # Similar for free cells
        for card in self.free_cells:
            if card is not None:
                prereqs_missing = sum(
                    1
                    for r in range(1, card.rank)
                    if r not in cards_in_foundations[card.suit]
                )
                min_moves = max(1, prereqs_missing)
                total_min_moves += min_moves

        return total_min_moves

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

        # Draw top control panel
        top_panel_height = 60
        top_panel_color = DARK_GRAY
        pygame.draw.rect(screen, top_panel_color, (0, 0, SCREEN_WIDTH, top_panel_height))

        # Algorithm dropdown display
        algo_label = small_font.render("Algorithm:", True, WHITE)
        screen.blit(algo_label, (20, 20))
        algo_rect = pygame.Rect(120, 15, 150, 30)
        pygame.draw.rect(screen, WHITE, algo_rect)
        pygame.draw.rect(screen, BLACK, algo_rect, 1)
        algo_text = small_font.render(algorithm, True, BLACK)
        screen.blit(algo_text, (algo_rect.x + 10, algo_rect.y + 5))

        # Solve button
        solve_rect = pygame.Rect(290, 15, 100, 30)
        pygame.draw.rect(screen, BLUE, solve_rect)
        pygame.draw.rect(screen, BLACK, solve_rect, 1)
        solve_text = small_font.render("Solve", True, WHITE)
        screen.blit(solve_text, (solve_rect.x + 30, solve_rect.y + 5))

        # New Game button
        new_game_rect = pygame.Rect(410, 15, 120, 30)
        pygame.draw.rect(screen, BLUE, new_game_rect)
        pygame.draw.rect(screen, BLACK, new_game_rect, 1)
        new_game_text = small_font.render("New Game", True, WHITE)
        screen.blit(new_game_text, (new_game_rect.x + 20, new_game_rect.y + 5))

        # Deck size radio buttons
        deck_sizes = [("52", 52), ("28", 28), ("12", 12)]
        deck_start_x = 550
        for i, (label, size) in enumerate(deck_sizes):
            x = deck_start_x + i * 60
            pygame.draw.circle(screen, WHITE, (x, 30), 10)
            if self.deck_size == size:
                pygame.draw.circle(screen, BLUE, (x, 30), 7)
            pygame.draw.circle(screen, BLACK, (x, 30), 10, 1)
            size_text = small_font.render(label, True, WHITE)
            screen.blit(size_text, (x + 15, 25))

        # Timer display
        timer_text = small_font.render(f"Time: {game_timer:.1f}s", True, WHITE)
        screen.blit(timer_text, (SCREEN_WIDTH - 150, 20))

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
                move_type, source_type, source_idx, dest = (
                    highlight_move[0],
                    highlight_move[1],
                    highlight_move[2],
                    highlight_move[3],
                )
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
                move_type = highlight_move[0]
                if move_type == "foundation":
                    _, source_type, source_idx, dest = highlight_move
                    if dest == suit:
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
                    move_type = highlight_move[0]

                    if move_type == "supermove":
                        # For supermoves: highlight_move = ("supermove", "cascade", source_idx, dest_idx, num_cards)
                        _, source_type, source_idx, dest_idx, num_cards = highlight_move

                        # Highlight source cards that are part of the supermove
                        if source_idx == i and j >= len(cascade) - num_cards:
                            is_highlighted = True
                            if (
                                j == len(cascade) - num_cards
                            ):  # Only set source_pos for the bottom card of the sequence
                                source_pos = (
                                    x + CARD_WIDTH // 2,
                                    card_y + CARD_HEIGHT // 2,
                                )

                        # Highlight destination
                        if dest_idx == i and j == len(cascade) - 1:
                            is_highlighted = True
                            dest_pos = (x + CARD_WIDTH // 2, card_y + CARD_HEIGHT // 2)
                    else:
                        # Original highlight logic for regular moves
                        move_type, source_type, source_idx, dest = highlight_move
                        if (
                            source_type == "cascade"
                            and source_idx == i
                            and j == len(cascade) - 1
                        ):
                            is_highlighted = True
                            source_pos = (
                                x + CARD_WIDTH // 2,
                                card_y + CARD_HEIGHT // 2,
                            )
                        elif (
                            move_type == "cascade"
                            and dest == i
                            and j == len(cascade) - 1
                        ):
                            is_highlighted = True
                            dest_pos = (x + CARD_WIDTH // 2, card_y + CARD_HEIGHT // 2)

                # Draw card with optional highlighting
                card.draw(x, card_y, is_highlighted)

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

        # Bottom controls panel
        button_y = SCREEN_HEIGHT - 60
        button_height = 40

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
    max_states = 150000
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


# Main game loop
def main():
    global animation_delay, paused, game_timer

    deck_size = 52  # Default deck size
    game = FreeCellGame(deck_size=deck_size)
    solution = None
    solution_index = 0
    solving = False
    current_algorithm = "A*"
    stats = None
    clock = pygame.time.Clock()
    last_move_time = 0

    game_timer = 0.0
    start_time = time.time()
    algorithms = ["A*", "Best-First", "BFS", "DFS"]
    algorithm_index = 0

    while True:
        current_time = time.time()

        if not paused and not solving and solution is None:
            game_timer = current_time - start_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_n:
                    game = FreeCellGame(deck_size=deck_size)
                    solution = None
                    solution_index = 0
                    solving = False
                    stats = None
                    start_time = time.time()
                    game_timer = 0.0
                elif event.key == pygame.K_s and solution and solution_index < len(solution):
                    move = solution[solution_index]
                    game.make_move(move)
                    solution_index += 1
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    animation_delay = max(0.1, animation_delay - 0.1)
                elif event.key == pygame.K_MINUS:
                    animation_delay = min(2.0, animation_delay + 0.1)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                x, y = pygame.mouse.get_pos()

                if 0 <= y <= 60:
                    # Algorithm selection
                    if 120 <= x <= 270 and 15 <= y <= 45:
                        algorithm_index = (algorithm_index + 1) % len(algorithms)
                        current_algorithm = algorithms[algorithm_index]

                    # Solve button
                    elif 290 <= x <= 390 and 15 <= y <= 45:
                        print(f"Solving with {current_algorithm}...")
                        solving = True
                        paused = False
                        algo_map = {"A*": "astar", "Best-First": "bestfirst", "BFS": "bfs", "DFS": "dfs"}
                        algo_key = algo_map.get(current_algorithm, "astar")
                        solution_data, metrics = solve_freecell(game, algo_key)
                        solution = solution_data
                        solution_index = 0
                        if solution:
                            print(f"{current_algorithm} solution found with {len(solution)} moves!")
                            metrics.print_report(current_algorithm)
                            stats = (solution, metrics.states_explored)
                        else:
                            print(f"No {current_algorithm} solution found.")
                            metrics.print_report(f"{current_algorithm} (No Solution)")
                            solving = False

                    # New Game button
                    elif 410 <= x <= 530 and 15 <= y <= 45:
                        game = FreeCellGame(deck_size=deck_size)
                        solution = None
                        solution_index = 0
                        solving = False
                        stats = None
                        start_time = time.time()
                        game_timer = 0.0

                    # Deck size radio buttons
                    elif 15 <= y <= 45:
                        if 540 <= x <= 560:  # 52 cards
                            deck_size = 52
                            game = FreeCellGame(deck_size=deck_size)
                            solution = None
                            solution_index = 0
                            solving = False
                            stats = None
                            start_time = time.time()
                            game_timer = 0.0
                        elif 600 <= x <= 620:  # 28 cards
                            deck_size = 28
                            game = FreeCellGame(deck_size=deck_size)
                            solution = None
                            solution_index = 0
                            solving = False
                            stats = None
                            start_time = time.time()
                            game_timer = 0.0
                        elif 660 <= x <= 680:  # 12 cards
                            deck_size = 12
                            game = FreeCellGame(deck_size=deck_size)
                            solution = None
                            solution_index = 0
                            solving = False
                            stats = None
                            start_time = time.time()
                            game_timer = 0.0

                # Bottom controls (unchanged)
                button_y = SCREEN_HEIGHT - 60
                button_height = 40
                if button_y <= y <= button_y + button_height:
                    if SCREEN_WIDTH - 230 <= x <= SCREEN_WIDTH - 130:
                        paused = not paused
                    elif SCREEN_WIDTH - 120 <= x <= SCREEN_WIDTH - 20:
                        if solution and solution_index < len(solution):
                            move = solution[solution_index]
                            game.make_move(move)
                            solution_index += 1

        if solving and solution and solution_index < len(solution) and not paused:
            if current_time - last_move_time >= animation_delay:
                highlight_move = solution[solution_index]
                game.draw(highlight_move=highlight_move, stats=stats, algorithm=current_algorithm)
                pygame.display.flip()
                time.sleep(0.2)
                game.make_move(highlight_move)
                solution_index += 1
                last_move_time = current_time
                if solution_index >= len(solution):
                    solving = False
        else:
            game.draw(
                stats=stats,
                algorithm=current_algorithm,
                highlight_move=solution[solution_index - 1] if solution and solution_index > 0 and solution_index < len(solution) else None,
            )

        clock.tick(60)

if __name__ == "__main__":
    main()
