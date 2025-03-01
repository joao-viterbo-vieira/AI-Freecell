import random
import sys
import time
from collections import deque
import heapq
import pygame

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

# Initialize pygame
pygame.init()

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("FreeCel - Single Player with AI Solver")

# Font
font = pygame.font.SysFont("Arial", 22)
small_font = pygame.font.SysFont("Arial", 16)
mini_font = pygame.font.SysFont("Arial", 14)

# Game Control
animation_delay = 0.5  # seconds between moves
paused = False
game_timer = 0.0


# Performance Metrics class (to replace the imported one)
class PerformanceMetrics:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.states_explored = 0
        self.states_generated = 0
        self.max_queue_size = 0
        self.max_depth_reached = 0
        self.solution_length = 0

    def start(self):
        self.start_time = time.time()

    def stop(self, solution=None):
        self.end_time = time.time()
        if solution:
            self.solution_length = len(solution)

    def print_report(self, algorithm_name):
        print(f"\n--- {algorithm_name} Performance Report ---")
        print(f"Time taken: {self.end_time - self.start_time:.2f} seconds")
        print(f"States explored: {self.states_explored}")
        print(f"States generated: {self.states_generated}")
        print(f"Max queue size: {self.max_queue_size}")
        print(f"Max depth reached: {self.max_depth_reached}")
        if self.solution_length:
            print(f"Solution length: {self.solution_length} moves")


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
    def __init__(self, initial_state=None):
        # Cascades (8 columns)
        self.cascades = [[] for _ in range(8)]
        # Free cells (4 individual cells)
        self.free_cells = [None] * 4
        # Foundations (4 piles, one for each suit)
        self.foundations = {"H": [], "D": [], "C": [], "S": []}
        self.moves = []

        # For player interaction
        self.selected_card = None
        self.selected_source = None
        self.selected_index = None

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

        # Reset selection
        self.selected_card = None
        self.selected_source = None
        self.selected_index = None

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

        # Reset selection after making a move
        self.selected_card = None
        self.selected_source = None
        self.selected_index = None

    def select_card(self, source_type, source_idx, card_idx=None):
        """Select a card for movement"""
        if source_type == "cascade":
            if card_idx is None:
                card_idx = len(self.cascades[source_idx]) - 1

            if card_idx >= 0 and card_idx < len(self.cascades[source_idx]):
                self.selected_card = self.cascades[source_idx][card_idx]
                self.selected_source = source_type
                self.selected_index = source_idx
                # Additional index for cascades to know which card in the cascade
                self.selected_card_idx = card_idx
                return True

        elif source_type == "free_cell":
            if self.free_cells[source_idx] is not None:
                self.selected_card = self.free_cells[source_idx]
                self.selected_source = source_type
                self.selected_index = source_idx
                return True

        return False

    def try_move_selected_card(self, dest_type, dest_idx):
        """Try to move the currently selected card to the destination"""
        if self.selected_card is None:
            return False

        # Handle foundation moves
        if dest_type == "foundation":
            if self.can_move_to_foundation(self.selected_card):
                suit = self.selected_card.suit
                move = ("foundation", self.selected_source, self.selected_index, suit)
                self.make_move(move)
                return True

        # Handle free cell moves
        elif dest_type == "free_cell":
            if self.free_cells[dest_idx] is None:
                move = (
                    "free_cell",
                    self.selected_source,
                    self.selected_index,
                    dest_idx,
                )
                self.make_move(move)
                return True

        # Handle cascade moves
        elif dest_type == "cascade":
            if self.can_move_to_cascade(self.selected_card, dest_idx):
                # Check if it's a supermove
                if (
                    self.selected_source == "cascade"
                    and hasattr(self, "selected_card_idx")
                    and self.selected_card_idx
                    < len(self.cascades[self.selected_index]) - 1
                ):
                    # Calculate number of cards to move
                    num_cards = (
                        len(self.cascades[self.selected_index]) - self.selected_card_idx
                    )

                    # Check if this is a valid supermove
                    if num_cards <= self.max_cards_movable(
                        dest_idx if not self.cascades[dest_idx] else None
                    ):
                        sequence = self.cascades[self.selected_index][
                            self.selected_card_idx :
                        ]
                        if self._is_valid_sequence(sequence):
                            move = (
                                "supermove",
                                "cascade",
                                self.selected_index,
                                dest_idx,
                                num_cards,
                            )
                            self.make_move(move)
                            return True

                # Regular single card move
                move = ("cascade", self.selected_source, self.selected_index, dest_idx)
                self.make_move(move)
                return True

        return False

    def auto_move_to_foundation(self):
        """Automatically move cards to foundations when possible"""
        made_move = False

        # Check free cells
        for i, card in enumerate(self.free_cells):
            if card is not None and self.can_move_to_foundation(card):
                move = ("foundation", "free_cell", i, card.suit)
                self.make_move(move)
                made_move = True

        # Check cascades
        for i, cascade in enumerate(self.cascades):
            if cascade:
                card = cascade[-1]
                if self.can_move_to_foundation(card):
                    move = ("foundation", "cascade", i, card.suit)
                    self.make_move(move)
                    made_move = True

        return made_move

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

    def heuristic3(self):
        """Advanced admissible heuristic for A* search"""
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

    def draw(self, highlight_move=None, stats=None, algorithm="A*", mouse_pos=None):
        screen.fill(GREEN)

        # Draw top control panel with new layout
        top_panel_height = 60
        top_panel_color = DARK_GRAY
        pygame.draw.rect(
            screen, top_panel_color, (0, 0, SCREEN_WIDTH, top_panel_height)
        )

        # Algorithm dropdown display
        algo_label = small_font.render("Algorithm:", True, WHITE)
        screen.blit(algo_label, (20, 20))

        # Draw algorithm selection display
        algo_rect = pygame.Rect(120, 15, 150, 30)
        pygame.draw.rect(screen, WHITE, algo_rect)
        pygame.draw.rect(screen, BLACK, algo_rect, 1)
        algo_text = small_font.render(algorithm, True, BLACK)
        screen.blit(algo_text, (algo_rect.x + 10, algo_rect.y + 5))

        # Draw Solve button
        solve_rect = pygame.Rect(290, 15, 100, 30)
        pygame.draw.rect(screen, BLUE, solve_rect)
        pygame.draw.rect(screen, BLACK, solve_rect, 1)
        solve_text = small_font.render("Solve", True, WHITE)
        screen.blit(solve_text, (solve_rect.x + 30, solve_rect.y + 5))

        # Draw New Game button
        new_game_rect = pygame.Rect(410, 15, 120, 30)
        pygame.draw.rect(screen, BLUE, new_game_rect)
        pygame.draw.rect(screen, BLACK, new_game_rect, 1)
        new_game_text = small_font.render("New Game", True, WHITE)
        screen.blit(new_game_text, (new_game_rect.x + 20, new_game_rect.y + 5))

        # Draw Auto Move button
        auto_move_rect = pygame.Rect(550, 15, 120, 30)
        pygame.draw.rect(screen, BLUE, auto_move_rect)
        pygame.draw.rect(screen, BLACK, auto_move_rect, 1)
        auto_move_text = small_font.render("Auto Move", True, WHITE)
        screen.blit(auto_move_text, (auto_move_rect.x + 20, auto_move_rect.y + 5))

        # Timer display in top right
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
            is_selected = (
                self.selected_source == "free_cell" and self.selected_index == i
            )
            is_hovered = (
                mouse_pos
                and x <= mouse_pos[0] <= x + CARD_WIDTH
                and y <= mouse_pos[1] <= y + CARD_HEIGHT
            )

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
            cell_color = HIGHLIGHT if is_selected or is_hovered else GRAY
            pygame.draw.rect(screen, cell_color, (x, y, CARD_WIDTH, CARD_HEIGHT))

            # Draw border
            border_color = BLUE if is_highlighted or is_selected else DARK_GRAY
            border_width = 3 if is_highlighted or is_selected else 1
            pygame.draw.rect(
                screen, border_color, (x, y, CARD_WIDTH, CARD_HEIGHT), border_width
            )

            if card:
                card.draw(x, y, is_highlighted or is_selected)

            # Label the free cell
            label = mini_font.render(f"Free Cell {i + 1}", True, WHITE)
            screen.blit(label, (x, y - 20))

        # Draw foundations
        for i, suit in enumerate(["H", "D", "C", "S"]):
            x = SCREEN_WIDTH - 50 - CARD_WIDTH - i * (CARD_WIDTH + CARD_MARGIN)
            y = 100

            # Check if this foundation is highlighted or hovered
            is_highlighted = False
            is_hovered = (
                mouse_pos
                and x <= mouse_pos[0] <= x + CARD_WIDTH
                and y <= mouse_pos[1] <= y + CARD_HEIGHT
            )

            if highlight_move:
                move_type = highlight_move[0]
                if move_type == "foundation":
                    _, source_type, source_idx, dest = highlight_move
                    if dest == suit:
                        is_highlighted = True
                        dest_pos = (x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2)

            # Draw foundation background
            cell_color = HIGHLIGHT if is_hovered else GRAY
            pygame.draw.rect(screen, cell_color, (x, y, CARD_WIDTH, CARD_HEIGHT))

            # Draw border
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

            # Check if empty cascade is hovered
            if not cascade:
                is_hovered = (
                    mouse_pos
                    and x <= mouse_pos[0] <= x + CARD_WIDTH
                    and y <= mouse_pos[1] <= y + CARD_HEIGHT
                )
                if is_hovered:
                    pygame.draw.rect(screen, HIGHLIGHT, (x, y, CARD_WIDTH, CARD_HEIGHT))
                    pygame.draw.rect(screen, BLUE, (x, y, CARD_WIDTH, CARD_HEIGHT), 2)

            # Draw cards in cascade
            for j, card in enumerate(cascade):
                card_y = y + j * 30  # Overlap cards

                # Check if card is hovered
                is_hovered = (
                    mouse_pos
                    and x <= mouse_pos[0] <= x + CARD_WIDTH
                    and card_y <= mouse_pos[1] <= card_y + CARD_HEIGHT
                )

                # Check if card is selected
                is_selected = (
                    self.selected_source == "cascade"
                    and self.selected_index == i
                    and hasattr(self, "selected_card_idx")
                    and j >= self.selected_card_idx
                )

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
                card.draw(x, card_y, is_highlighted or is_selected or is_hovered)

                # If card is highlighted, add blue border on top
                if is_highlighted or is_selected:
                    pygame.draw.rect(
                        screen, BLUE, (x, card_y, CARD_WIDTH, CARD_HEIGHT), 3
                    )
                elif is_hovered:
                    pygame.draw.rect(
                        screen, BLUE, (x, card_y, CARD_WIDTH, CARD_HEIGHT), 2
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

        # Display selected card info
        if self.selected_card:
            selected_text = mini_font.render(
                f"Selected: {self.selected_card} from {self.selected_source} {self.selected_index + 1}",
                True,
                WHITE,
            )
            screen.blit(selected_text, (50, SCREEN_HEIGHT - 60))

        # Display game status
        status_text = ""
        if self.is_solved():
            status_text = "Game Solved! Congratulations!"
        elif stats:
            solution, states = stats
            status_text = f"Solution: {len(solution)} moves, {states} states explored"

        if status_text:
            status_render = small_font.render(status_text, True, WHITE)
            screen.blit(status_render, (50, SCREEN_HEIGHT - 90))

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
    max_states = 50000
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


# Function to get object at a specific position
def get_object_at_position(game, x, y):
    # Check free cells
    for i in range(4):
        cell_x = 50 + i * (CARD_WIDTH + CARD_MARGIN)
        cell_y = 100
        if cell_x <= x <= cell_x + CARD_WIDTH and cell_y <= y <= cell_y + CARD_HEIGHT:
            return ("free_cell", i)

    # Check foundations
    for i, suit in enumerate(["H", "D", "C", "S"]):
        found_x = SCREEN_WIDTH - 50 - CARD_WIDTH - i * (CARD_WIDTH + CARD_MARGIN)
        found_y = 100
        if (
            found_x <= x <= found_x + CARD_WIDTH
            and found_y <= y <= found_y + CARD_HEIGHT
        ):
            return ("foundation", suit)

    # Check cascades
    for i, cascade in enumerate(game.cascades):
        cascade_x = 50 + i * (CARD_WIDTH + CARD_MARGIN)
        cascade_base_y = 250

        # Check if clicked on empty cascade
        if (
            not cascade
            and cascade_x <= x <= cascade_x + CARD_WIDTH
            and cascade_base_y <= y <= cascade_base_y + CARD_HEIGHT
        ):
            return ("cascade", i, -1)  # -1 indicates empty cascade

        # Check each card in the cascade
        for j, card in enumerate(cascade):
            card_y = cascade_base_y + j * 30

            # If this is the last card or if the click is within this card's visible area (not overlapped)
            if j == len(cascade) - 1 or (card_y <= y < card_y + 30):
                if (
                    cascade_x <= x <= cascade_x + CARD_WIDTH
                    and card_y <= y <= card_y + CARD_HEIGHT
                ):
                    return ("cascade", i, j)

    return None


# Main game loop
def main():
    global animation_delay, paused, game_timer

    game = FreeCellGame()
    solution = None
    solution_index = 0
    solving = False
    current_algorithm = "A*"
    stats = None
    clock = pygame.time.Clock()
    last_move_time = 0

    # Initialize timer variables
    game_timer = 0.0
    start_time = time.time()
    algorithms = ["A*", "Best-First", "BFS", "DFS"]
    algorithm_index = 0

    while True:
        current_time = time.time()
        mouse_pos = pygame.mouse.get_pos()  # Get current mouse position

        # Update timer when game is running
        if not paused and not solving and solution is None:
            game_timer = current_time - start_time

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
                    # Reset timer
                    start_time = time.time()
                    game_timer = 0.0

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

                # Escape key to deselect
                elif event.key == pygame.K_ESCAPE:
                    game.selected_card = None
                    game.selected_source = None
                    game.selected_index = None
                    if hasattr(game, "selected_card_idx"):
                        delattr(game, "selected_card_idx")

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                x, y = pygame.mouse.get_pos()

                # Top control panel events
                if 0 <= y <= 60:
                    # Algorithm selection box
                    if 120 <= x <= 270 and 15 <= y <= 45:
                        algorithm_index = (algorithm_index + 1) % len(algorithms)
                        current_algorithm = algorithms[algorithm_index]

                    # Solve button
                    elif 290 <= x <= 390 and 15 <= y <= 45:
                        print(f"Solving with {current_algorithm}...")
                        solving = True
                        paused = False

                        # Map algorithm name to function call
                        algo_map = {
                            "A*": "astar",
                            "Best-First": "bestfirst",
                            "BFS": "bfs",
                            "DFS": "dfs",
                        }

                        algo_key = algo_map.get(current_algorithm, "astar")
                        solution_data, metrics = solve_freecell(game, algo_key)
                        solution = solution_data
                        solution_index = 0

                        if solution:
                            print(
                                f"{current_algorithm} solution found with {len(solution)} moves!"
                            )
                            metrics.print_report(current_algorithm)
                            stats = (solution, metrics.states_explored)
                        else:
                            print(f"No {current_algorithm} solution found.")
                            metrics.print_report(f"{current_algorithm} (No Solution)")
                            solving = False

                    # New Game button
                    elif 410 <= x <= 530 and 15 <= y <= 45:
                        game = FreeCellGame()
                        solution = None
                        solution_index = 0
                        solving = False
                        stats = None
                        # Reset timer
                        start_time = time.time()
                        game_timer = 0.0

                    # Auto Move button
                    elif 550 <= x <= 670 and 15 <= y <= 45:
                        # Keep moving cards to foundations until no more moves are possible
                        while game.auto_move_to_foundation():
                            pass

                # Bottom control panel events
                button_y = SCREEN_HEIGHT - 60
                button_height = 40

                if button_y <= y <= button_y + button_height:
                    # Pause button
                    if SCREEN_WIDTH - 230 <= x <= SCREEN_WIDTH - 130:
                        paused = not paused

                    # Step button
                    elif SCREEN_WIDTH - 120 <= x <= SCREEN_WIDTH - 20:
                        if solution and solution_index < len(solution):
                            move = solution[solution_index]
                            game.make_move(move)
                            solution_index += 1

                # Handle gameplay clicks
                else:
                    clicked_obj = get_object_at_position(game, x, y)

                    if clicked_obj:
                        # Handle player moves based on click
                        if clicked_obj[0] == "cascade":
                            cascade_idx = clicked_obj[1]
                            card_idx = clicked_obj[2]

                            # If we already have a card selected
                            if game.selected_card:
                                # Try to move selected card to this cascade
                                if game.try_move_selected_card("cascade", cascade_idx):
                                    pass  # Move successful
                                else:
                                    # Select this card instead
                                    if card_idx >= 0 and card_idx < len(
                                        game.cascades[cascade_idx]
                                    ):
                                        game.select_card(
                                            "cascade", cascade_idx, card_idx
                                        )
                            elif card_idx >= 0 and card_idx < len(
                                game.cascades[cascade_idx]
                            ):
                                # Select the card
                                game.select_card("cascade", cascade_idx, card_idx)

                        elif clicked_obj[0] == "free_cell":
                            cell_idx = clicked_obj[1]

                            # If we already have a card selected
                            if game.selected_card:
                                # Try to move selected card to this free cell
                                game.try_move_selected_card("free_cell", cell_idx)
                            elif game.free_cells[cell_idx] is not None:
                                # Select the card in the free cell
                                game.select_card("free_cell", cell_idx)

                        elif clicked_obj[0] == "foundation":
                            suit = clicked_obj[1]

                            # If we have a card selected, try to move it to the foundation
                            if game.selected_card and game.selected_card.suit == suit:
                                game.try_move_selected_card("foundation", None)

        # Process automatic solution steps if not paused
        if solving and solution and solution_index < len(solution) and not paused:
            # Check if it's time for the next move
            if current_time - last_move_time >= animation_delay:
                highlight_move = solution[solution_index]
                game.draw(
                    highlight_move=highlight_move,
                    stats=stats,
                    algorithm=current_algorithm,
                    mouse_pos=mouse_pos,
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
                mouse_pos=mouse_pos,
                highlight_move=solution[solution_index - 1]
                if solution and solution_index > 0 and solution_index < len(solution)
                else None,
            )

        # Cap the frame rate
        clock.tick(60)


if __name__ == "__main__":
    main()
