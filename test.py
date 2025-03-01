import random
import sys
import time
import math
from collections import deque
import heapq
import pygame
import datetime

# Initialize pygame
pygame.init()

# Constants
CARD_WIDTH = 80
CARD_HEIGHT = 120
CARD_MARGIN = 10
ANIMATION_SPEED = 10

# Screen dimensions
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)  # More vibrant green for background
RED = (255, 0, 0)  # Bright red for hearts/diamonds
BLUE = (0, 0, 255)  # Bright blue
GRAY = (220, 220, 220)
DARK_GRAY = (60, 60, 60)
LIGHT_GRAY = (240, 240, 240)
HIGHLIGHT = (255, 255, 150)  # Yellow highlight
SELECTION = (255, 255, 0, 128)  # Semi-transparent yellow for selection
TOP_BAR_COLOR = (200, 200, 200)
BUTTON_COLOR = (0, 0, 220)
BUTTON_TEXT_COLOR = (255, 255, 255)

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("FreeCellAI - An AI-Ready FreeCellGame")

# Font
font = pygame.font.SysFont("Arial", 22, bold=True)
small_font = pygame.font.SysFont("Arial", 16)
mini_font = pygame.font.SysFont("Arial", 14)
large_font = pygame.font.SysFont("Arial", 28, bold=True)
card_font = pygame.font.SysFont("Arial", 20, bold=True)
card_small_font = pygame.font.SysFont("Arial", 16, bold=True)

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

    def get_display_symbol(self):
        """Get the display symbol for the card's suit and rank"""
        suits_display = {"H": "♥", "D": "♦", "C": "♣", "S": "♠"}
        ranks_display = {1: "A", 11: "J", 12: "Q", 13: "K"}
        rank_str = ranks_display.get(self.rank, str(self.rank))
        suit_str = suits_display[self.suit]
        return rank_str, suit_str

    def draw(self, x, y, highlighted=False, selected=False):
        # Draw card background
        bg_color = HIGHLIGHT if highlighted else WHITE
        pygame.draw.rect(screen, bg_color, (x, y, CARD_WIDTH, CARD_HEIGHT))
        border_color = DARK_GRAY
        pygame.draw.rect(screen, border_color, (x, y, CARD_WIDTH, CARD_HEIGHT), 1)

        # Get card display values
        rank_str, suit_str = self.get_display_symbol()

        # Draw rank at top-left
        rank_text = card_font.render(rank_str, True, self.color)
        screen.blit(rank_text, (x + 5, y + 5))

        # Draw suit at top-left
        suit_text = card_font.render(suit_str, True, self.color)
        screen.blit(suit_text, (x + 5 + rank_text.get_width(), y + 5))

        # For number cards (not face cards), draw a larger suit in the middle
        if self.rank <= 10:
            big_suit = large_font.render(suit_str, True, self.color)
            screen.blit(
                big_suit,
                (
                    x + CARD_WIDTH // 2 - big_suit.get_width() // 2,
                    y + CARD_HEIGHT // 2 - big_suit.get_height() // 2,
                ),
            )

        # Draw rank+suit at the bottom-right (upside down)
        bottom_text = card_small_font.render(f"{rank_str}{suit_str}", True, self.color)
        screen.blit(
            bottom_text,
            (
                x + CARD_WIDTH - bottom_text.get_width() - 5,
                y + CARD_HEIGHT - bottom_text.get_height() - 5,
            ),
        )

        # Draw selection overlay if selected
        if selected:
            selection_surface = pygame.Surface(
                (CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA
            )
            selection_surface.fill(SELECTION)
            screen.blit(selection_surface, (x, y))


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
        self.start_time = time.time()
        self.total_moves = 0

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
            self.start_time = initial_state.start_time
            self.total_moves = initial_state.total_moves

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

        # Reset time and moves
        self.start_time = time.time()
        self.total_moves = 0
        self.moves = []

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

        # Record the move and increment move counter
        self.moves.append(move)
        self.total_moves += 1

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

    def draw(
        self,
        highlight_move=None,
        stats=None,
        algorithm="A*",
        human_mode=False,
        selected_card=None,
        selected_source=None,
        has_solution=False,
        hint_move=None,
    ):
        screen.fill(GREEN)

        # Draw title
        title = font.render("FreeCel Solver", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - 60, 10))

        # Draw algorithm and mode info
        mode_text = "Human Play Mode" if human_mode else f"Algorithm: {algorithm}"
        algo_text = font.render(mode_text, True, WHITE)
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

            # Check if this free cell contains the selected card
            is_selected = (
                human_mode
                and selected_source
                and selected_source[0] == "free_cell"
                and selected_source[1] == i
            )

            # Draw cell background
            cell_color = GRAY
            pygame.draw.rect(screen, cell_color, (x, y, CARD_WIDTH, CARD_HEIGHT))

            # Draw border - blue for highlighted cells, dark gray for normal
            border_color = BLUE if is_highlighted or is_selected else DARK_GRAY
            border_width = 3 if is_highlighted or is_selected else 1
            pygame.draw.rect(
                screen, border_color, (x, y, CARD_WIDTH, CARD_HEIGHT), border_width
            )

            if card:
                card.draw(x, y, is_highlighted, is_selected)

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

                # Check if this card is the selected card in human mode
                is_selected = (
                    human_mode
                    and selected_source
                    and selected_source[0] == "cascade"
                    and selected_source[1] == i
                )

                # If we're selecting from a cascade, we need to check if this card is part of the selection
                # We only select cards from this card to the bottom of the cascade
                if is_selected and j >= selected_source[2]:
                    is_selected = True
                else:
                    is_selected = False

                # Draw card with optional highlighting and selection
                card.draw(x, card_y, is_highlighted, is_selected)

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

        # Draw Human Play button alongside algorithm buttons
        algorithm_buttons = [
            ("A*", BLUE if not human_mode else DARK_GRAY, 50),
            ("Best-First", (0, 70, 140) if not human_mode else DARK_GRAY, 170),
            ("BFS", (140, 0, 140) if not human_mode else DARK_GRAY, 290),
            ("DFS", (140, 70, 0) if not human_mode else DARK_GRAY, 410),
            ("Human Play", (0, 140, 0) if human_mode else DARK_GRAY, 530),
            ("New Game", RED, 650),  # Moved New Game button to the right
        ]

        for label, color, x_pos in algorithm_buttons:
            # Determine button width based on text length
            btn_width = 110
            if label in ["Best-First", "Human Play", "New Game"]:
                btn_width = 120

            # Create button rectangle with proper spacing
            btn_rect = pygame.Rect(x_pos, button_y, btn_width, button_height)

            # Draw button with improved resolution
            pygame.draw.rect(screen, color, btn_rect)
            pygame.draw.rect(
                screen, BLACK, btn_rect, 1
            )  # Add thin border for better definition

            # Button text depends on the button type
            if label == "Human Play":
                btn_text = small_font.render(label, True, WHITE)
            elif label == "New Game":
                btn_text = small_font.render(label, True, WHITE)
            else:
                btn_text = small_font.render(f"Solve with {label}", True, WHITE)

            text_x = x_pos + (btn_width - btn_text.get_width()) // 2
            text_y = button_y + (button_height - btn_text.get_height()) // 2
            screen.blit(btn_text, (text_x, text_y))

        # Right-aligned controls
        # Step button (only visible in AI mode)
        if not human_mode and has_solution:
            step_btn_width = 100
            step_rect = pygame.Rect(
                SCREEN_WIDTH - step_btn_width - 20,
                button_y,
                step_btn_width,
                button_height,
            )
            pygame.draw.rect(screen, (0, 140, 0), step_rect)
            pygame.draw.rect(screen, BLACK, step_rect, 1)
            step_text = small_font.render("Step", True, WHITE)
            screen.blit(step_text, (SCREEN_WIDTH - step_btn_width + 15, button_y + 10))

            # Pause button (minimal, only visible in AI mode)
            pause_btn_width = 100
            pause_rect = pygame.Rect(
                SCREEN_WIDTH - step_btn_width - pause_btn_width - 30,
                button_y,
                pause_btn_width,
                button_height,
            )
            pygame.draw.rect(screen, DARK_GRAY, pause_rect)
            pygame.draw.rect(screen, BLACK, pause_rect, 1)
            pause_text = small_font.render(
                "Pause" if not paused else "Resume", True, WHITE
            )
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

        # Display human play instructions and additional buttons if in human mode
        if human_mode:
            # Draw hint and complete buttons at bottom
            hint_btn_rect = pygame.Rect(50, SCREEN_HEIGHT - 120, 100, 40)
            pygame.draw.rect(screen, (0, 120, 120), hint_btn_rect)
            pygame.draw.rect(screen, BLACK, hint_btn_rect, 1)
            hint_text = small_font.render("Hint", True, WHITE)
            screen.blit(hint_text, (50 + 30, SCREEN_HEIGHT - 120 + 10))

            complete_btn_rect = pygame.Rect(200, SCREEN_HEIGHT - 120, 150, 40)
            pygame.draw.rect(screen, (120, 60, 0), complete_btn_rect)
            pygame.draw.rect(screen, BLACK, complete_btn_rect, 1)
            complete_text = small_font.render("Complete Game", True, WHITE)
            screen.blit(complete_text, (200 + 15, SCREEN_HEIGHT - 120 + 10))

            algo_btn_rect = pygame.Rect(400, SCREEN_HEIGHT - 120, 100, 40)
            pygame.draw.rect(screen, BLUE, algo_btn_rect)
            pygame.draw.rect(screen, BLACK, algo_btn_rect, 1)
            algo_text = small_font.render(f"Using: {algorithm}", True, WHITE)
            screen.blit(algo_text, (400 + 5, SCREEN_HEIGHT - 120 + 10))

            # Draw hint move if available
            if hint_move:
                self.draw_hint(hint_move)

            # Player instructions
            if selected_card:
                instruction_text = mini_font.render(
                    "Click on a valid destination to place the selected card",
                    True,
                    WHITE,
                )
            else:
                instruction_text = mini_font.render(
                    "Click on a card to select it", True, WHITE
                )
            screen.blit(instruction_text, (SCREEN_WIDTH - 400, button_y - 30))

        # Simple info at the bottom
        key_info = (
            "Shortcuts: Space=Pause, N=New Game, S=Step, +/- = Speed, H=Human Mode"
        )
        info_text = mini_font.render(key_info, True, WHITE)
        screen.blit(info_text, (50, SCREEN_HEIGHT - 20))

        pygame.display.flip()

    def draw_hint(self, hint_move):
        """Draw a visual representation of the hint move"""
        # First get source and destination positions
        source_pos = None
        dest_pos = None

        move_type = hint_move[0]
        source_type = hint_move[1]
        source_idx = hint_move[2]

        # Get source position
        if source_type == "cascade":
            cascade_x = 50 + source_idx * (CARD_WIDTH + CARD_MARGIN)
            if move_type == "supermove":
                # For supermoves, get the bottom card of the sequence
                _, _, _, _, num_cards = hint_move
                card_idx = len(self.cascades[source_idx]) - num_cards
            else:
                # For regular moves, get the bottom card
                card_idx = len(self.cascades[source_idx]) - 1

            card_y = 250 + card_idx * 30
            source_pos = (cascade_x + CARD_WIDTH // 2, card_y + CARD_HEIGHT // 2)
        else:  # free_cell
            cell_x = 50 + source_idx * (CARD_WIDTH + CARD_MARGIN)
            cell_y = 100
            source_pos = (cell_x + CARD_WIDTH // 2, cell_y + CARD_HEIGHT // 2)

        # Get destination position
        if move_type == "foundation":
            dest = hint_move[3]  # suit
            suit_idx = ["H", "D", "C", "S"].index(dest)
            dest_x = (
                SCREEN_WIDTH - 50 - CARD_WIDTH - suit_idx * (CARD_WIDTH + CARD_MARGIN)
            )
            dest_y = 100
            dest_pos = (dest_x + CARD_WIDTH // 2, dest_y + CARD_HEIGHT // 2)
        elif move_type == "free_cell":
            dest = hint_move[3]  # free cell index
            dest_x = 50 + dest * (CARD_WIDTH + CARD_MARGIN)
            dest_y = 100
            dest_pos = (dest_x + CARD_WIDTH // 2, dest_y + CARD_HEIGHT // 2)
        else:  # cascade or supermove
            if move_type == "supermove":
                dest_idx = hint_move[3]
            else:
                dest_idx = hint_move[3]

            dest_x = 50 + dest_idx * (CARD_WIDTH + CARD_MARGIN)
            if self.cascades[dest_idx]:
                # Position at the bottom of the destination cascade
                card_idx = len(self.cascades[dest_idx]) - 1
                dest_y = 250 + card_idx * 30
            else:
                # Position at the empty cascade
                dest_y = 250
            dest_pos = (dest_x + CARD_WIDTH // 2, dest_y + CARD_HEIGHT // 2)

        # Draw a pulsing hint arrow
        pulse = (math.sin(time.time() * 5) + 1) * 0.5  # Value between 0 and 1
        arrow_color = (int(255 * pulse), int(255 * pulse), 0)  # Yellow pulsing effect

        if source_pos and dest_pos:
            # Draw the line connecting source and destination
            pygame.draw.line(screen, arrow_color, source_pos, dest_pos, 3)

            # Draw a small arrow at the destination end
            arrow_size = 10
            angle = pygame.math.Vector2(
                dest_pos[0] - source_pos[0], dest_pos[1] - source_pos[1]
            ).normalize()
            pygame.draw.polygon(
                screen,
                arrow_color,
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

            # Draw "Hint" text near the arrow
            midpoint = (
                (source_pos[0] + dest_pos[0]) // 2,
                (source_pos[1] + dest_pos[1]) // 2,
            )
            hint_text = small_font.render("HINT", True, arrow_color)
            screen.blit(hint_text, (midpoint[0] - 20, midpoint[1] - 20))

    # Helper functions for human player interaction
    def get_card_location(self, x, y):
        """
        Determine what card (if any) was clicked based on the coordinates.
        Returns a tuple (location_type, location_index, [card_index]) if a card was clicked,
        or None if no card was clicked.
        """
        # Check free cells
        for i in range(4):
            cell_x = 50 + i * (CARD_WIDTH + CARD_MARGIN)
            cell_y = 100
            if (
                cell_x <= x <= cell_x + CARD_WIDTH
                and cell_y <= y <= cell_y + CARD_HEIGHT
            ):
                return ("free_cell", i)

        # Check foundations
        for i, suit in enumerate(["H", "D", "C", "S"]):
            foundation_x = (
                SCREEN_WIDTH - 50 - CARD_WIDTH - i * (CARD_WIDTH + CARD_MARGIN)
            )
            foundation_y = 100
            if (
                foundation_x <= x <= foundation_x + CARD_WIDTH
                and foundation_y <= y <= foundation_y + CARD_HEIGHT
            ):
                return ("foundation", suit)

        # Check cascades
        for i, cascade in enumerate(self.cascades):
            cascade_x = 50 + i * (CARD_WIDTH + CARD_MARGIN)
            cascade_y = 250

            # Check if click is within the cascade's vertical bounds
            for j, card in enumerate(cascade):
                card_y = cascade_y + j * 30

                # The last card in a cascade is fully visible
                if j == len(cascade) - 1:
                    if (
                        cascade_x <= x <= cascade_x + CARD_WIDTH
                        and card_y <= y <= card_y + CARD_HEIGHT
                    ):
                        return ("cascade", i, j)
                # Other cards are partially visible (just check the visible portion)
                else:
                    if (
                        cascade_x <= x <= cascade_x + CARD_WIDTH
                        and card_y <= y <= card_y + 30
                    ):
                        return ("cascade", i, j)

        # No card was clicked
        return None

    def validate_human_move(self, source, destination):
        """
        Validate if a human player's move from source to destination is legal.
        If valid, returns the move tuple. Otherwise, returns None.
        """
        # Check if we have valid source and destination
        if not source or not destination:
            return None

        source_type, source_idx = source[0], source[1]
        dest_type, dest_idx = destination[0], destination[1]

        # Handle invalid source types
        if source_type not in ["cascade", "free_cell"]:
            return None

        # Handle invalid destination types
        if dest_type not in ["cascade", "free_cell", "foundation"]:
            return None

        # Get the source card
        if source_type == "cascade":
            # Make sure source_idx is a valid cascade index
            if (
                not isinstance(source_idx, int)
                or source_idx < 0
                or source_idx >= len(self.cascades)
            ):
                return None

            # Make sure we have cards in this cascade
            if not self.cascades[source_idx]:
                return None

            card_idx = source[2]
            # For cascades, we might be moving multiple cards
            if card_idx < len(self.cascades[source_idx]) - 1:
                # We're selecting a card that's not at the bottom of the cascade
                # Check if it forms a valid sequence with cards below it
                sequence = self.cascades[source_idx][card_idx:]
                if not self._is_valid_sequence(sequence):
                    return None

                # Check if we can move this many cards
                max_movable = self.max_cards_movable(
                    dest_idx
                    if dest_type == "cascade" and not self.cascades[dest_idx]
                    else None
                )
                if len(sequence) > max_movable:
                    return None

                # For sequence moves, we can only move to empty cascades or cascades with compatible cards
                if dest_type != "cascade":
                    return None

                # Make sure dest_idx is a valid cascade index
                if (
                    not isinstance(dest_idx, int)
                    or dest_idx < 0
                    or dest_idx >= len(self.cascades)
                ):
                    return None

                # If destination cascade is empty, the move is valid
                if not self.cascades[dest_idx]:
                    return ("supermove", "cascade", source_idx, dest_idx, len(sequence))

                # If destination cascade is not empty, check if bottom card of sequence is compatible
                bottom_seq_card = sequence[0]
                top_dest_card = self.cascades[dest_idx][-1]
                if (
                    bottom_seq_card.rank == top_dest_card.rank - 1
                    and bottom_seq_card.color != top_dest_card.color
                ):
                    return ("supermove", "cascade", source_idx, dest_idx, len(sequence))

                return None

            # We're selecting the bottom card of a cascade
            card = self.cascades[source_idx][-1]
        else:  # free_cell
            # Make sure source_idx is a valid free cell index
            if (
                not isinstance(source_idx, int)
                or source_idx < 0
                or source_idx >= len(self.free_cells)
            ):
                return None

            card = self.free_cells[source_idx]
            if card is None:
                return None

        # Now validate the destination
        if dest_type == "foundation":
            # Check if the card can be moved to the foundation
            if card.suit == dest_idx and self.can_move_to_foundation(card):
                return ("foundation", source_type, source_idx, dest_idx)
        elif dest_type == "free_cell":
            # Can only move to an empty free cell
            if self.free_cells[dest_idx] is None:
                return ("free_cell", source_type, source_idx, dest_idx)
        else:  # cascade
            # Check if the card can be moved to the cascade
            if self.can_move_to_cascade(card, dest_idx):
                return ("cascade", source_type, source_idx, dest_idx)

        return None

    def handle_human_click(self, x, y, selected_source):
        """
        Handle a mouse click in human play mode.
        If no card is currently selected, selects a card.
        If a card is already selected, tries to move it to the clicked destination.

        Returns a tuple (move, new_selected_source) where:
        - move is the move made (or None if no move was made)
        - new_selected_source is the new selected source (or None if no card is selected)
        """
        clicked_location = self.get_card_location(x, y)

        # If no location was clicked, deselect any selection
        if clicked_location is None:
            return None, None

        # If no card is currently selected, select the clicked card
        if selected_source is None:
            # Don't allow selecting empty free cells, foundations, or empty cascades
            if clicked_location[0] == "free_cell" and (
                not isinstance(clicked_location[1], int)
                or clicked_location[1] < 0
                or clicked_location[1] >= len(self.free_cells)
                or self.free_cells[clicked_location[1]] is None
            ):
                return None, None

            if clicked_location[0] == "foundation":
                return None, None

            if clicked_location[0] == "cascade" and (
                not isinstance(clicked_location[1], int)
                or clicked_location[1] < 0
                or clicked_location[1] >= len(self.cascades)
                or not self.cascades[clicked_location[1]]
            ):
                return None, None

            return None, clicked_location

        # If a card is already selected, try to move it to the clicked destination
        else:
            # If clicking on the same location, deselect
            if (
                clicked_location[0] == selected_source[0]
                and clicked_location[1] == selected_source[1]
            ):
                if (
                    clicked_location[0] == "cascade"
                    and len(clicked_location) > 2
                    and len(selected_source) > 2
                ):
                    # For cascades, check if we're clicking on the same card
                    if clicked_location[2] == selected_source[2]:
                        return None, None
                else:
                    return None, None

            # Try to validate and make the move
            move = self.validate_human_move(selected_source, clicked_location)
            if move:
                self.make_move(move)
                return move, None
            else:
                # If the move is invalid, select the new location instead
                # But only if it's a valid source (card that can be moved)
                if (
                    clicked_location[0] == "free_cell"
                    and isinstance(clicked_location[1], int)
                    and 0 <= clicked_location[1] < len(self.free_cells)
                    and self.free_cells[clicked_location[1]] is not None
                ):
                    return None, clicked_location
                elif (
                    clicked_location[0] == "cascade"
                    and isinstance(clicked_location[1], int)
                    and 0 <= clicked_location[1] < len(self.cascades)
                    and self.cascades[clicked_location[1]]
                ):
                    return None, clicked_location
                else:
                    return None, None


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

    # Human play mode variables
    human_mode = False
    selected_source = (
        None  # The currently selected card source (location_type, index, [card_index])
    )
    last_human_move = None  # The last move made by the human player
    hint_move = None  # The current hint move to display
    hint_time = 0  # Time when hint was last shown

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
                    selected_source = None
                    last_human_move = None
                    hint_move = None

                elif (
                    event.key == pygame.K_s
                    and solution
                    and solution_index < len(solution)
                    and not human_mode
                ):
                    # Step forward
                    move = solution[solution_index]
                    game.make_move(move)
                    solution_index += 1

                elif event.key == pygame.K_h:
                    # Toggle human mode
                    human_mode = not human_mode
                    solving = False
                    selected_source = None
                    last_human_move = None
                    hint_move = None

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

                # Handle human mode special buttons (hint, complete, algorithm)
                if human_mode:
                    # Hint button
                    if (
                        50 <= x <= 150
                        and SCREEN_HEIGHT - 120 <= y <= SCREEN_HEIGHT - 80
                    ):
                        print(f"Getting hint using {current_algorithm}...")
                        # Use the current algorithm to get a hint
                        hint_solution, _ = solve_freecell(
                            game, current_algorithm.lower().replace("-", "")
                        )
                        if hint_solution:
                            hint_move = hint_solution[0]
                            hint_time = current_time
                            print(f"Hint: {hint_move}")
                        else:
                            print("No hint available")

                    # Complete game button
                    elif (
                        200 <= x <= 350
                        and SCREEN_HEIGHT - 120 <= y <= SCREEN_HEIGHT - 80
                    ):
                        print(f"Completing game using {current_algorithm}...")
                        # Switch to AI mode and solve from current position
                        human_mode = False
                        solution, states_explored = solve_freecell(
                            game, current_algorithm.lower().replace("-", "")
                        )
                        if solution:
                            print(
                                f"Solution found with {len(solution)} moves! Explored {states_explored} states."
                            )
                            stats = (solution, states_explored)
                            solving = True
                            solution_index = 0
                            paused = False
                            selected_source = None
                        else:
                            print(
                                f"No solution found. Explored {states_explored} states."
                            )
                            # Switch back to human mode
                            human_mode = True

                    # Algorithm selection for hints/complete
                    elif (
                        400 <= x <= 500
                        and SCREEN_HEIGHT - 120 <= y <= SCREEN_HEIGHT - 80
                    ):
                        # Cycle through algorithms: A* -> Best-First -> BFS -> DFS -> A*
                        if current_algorithm == "A*":
                            current_algorithm = "Best-First"
                        elif current_algorithm == "Best-First":
                            current_algorithm = "BFS"
                        elif current_algorithm == "BFS":
                            current_algorithm = "DFS"
                        else:
                            current_algorithm = "A*"
                        print(f"Selected algorithm: {current_algorithm}")

                # Check algorithm and control buttons
                if button_y <= y <= button_y + button_height:
                    # A* button
                    if 50 <= x <= 160:
                        if not human_mode:
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
                        if not human_mode:
                            print("Solving with Best-First...")
                            solving = True
                            paused = False
                            current_algorithm = "Best-First"
                            solution, states_explored = solve_freecell(
                                game, "bestfirst"
                            )
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
                        if not human_mode:
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
                        if not human_mode:
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

                    # Human Play button
                    elif 530 <= x <= 650:
                        human_mode = True
                        solving = False
                        selected_source = None
                        last_human_move = None
                        hint_move = None

                    # New Game button
                    elif 650 <= x <= 770:
                        game = FreeCellGame()
                        solution = None
                        solution_index = 0
                        solving = False
                        stats = None
                        selected_source = None
                        last_human_move = None
                        hint_move = None

                    # Hint button (in human mode)
                    elif (
                        human_mode
                        and 50 <= x <= 150
                        and SCREEN_HEIGHT - 120 <= y <= SCREEN_HEIGHT - 80
                    ):
                        print(f"Getting hint using {current_algorithm}...")
                        # Use the current algorithm to get a hint
                        hint_solution, _ = solve_freecell(
                            game, current_algorithm.lower().replace("-", "")
                        )
                        if hint_solution:
                            hint_move = hint_solution[0]
                            hint_time = current_time
                            print(f"Hint: {hint_move}")
                        else:
                            print("No hint available")

                    # Complete game button (in human mode)
                    elif (
                        human_mode
                        and 200 <= x <= 350
                        and SCREEN_HEIGHT - 120 <= y <= SCREEN_HEIGHT - 80
                    ):
                        print(f"Completing game using {current_algorithm}...")
                        # Switch to AI mode and solve from current position
                        human_mode = False
                        solution, states_explored = solve_freecell(
                            game, current_algorithm.lower().replace("-", "")
                        )
                        if solution:
                            print(
                                f"Solution found with {len(solution)} moves! Explored {states_explored} states."
                            )
                            stats = (solution, states_explored)
                            solving = True
                            solution_index = 0
                            paused = False
                        else:
                            print(
                                f"No solution found. Explored {states_explored} states."
                            )
                            # Switch back to human mode
                            human_mode = True

                    # Algorithm selection for hints/complete (in human mode)
                    elif (
                        human_mode
                        and 400 <= x <= 500
                        and SCREEN_HEIGHT - 120 <= y <= SCREEN_HEIGHT - 80
                    ):
                        # Cycle through algorithms: A* -> Best-First -> BFS -> DFS -> A*
                        if current_algorithm == "A*":
                            current_algorithm = "Best-First"
                        elif current_algorithm == "Best-First":
                            current_algorithm = "BFS"
                        elif current_algorithm == "BFS":
                            current_algorithm = "DFS"
                        else:
                            current_algorithm = "A*"
                        print(f"Selected algorithm: {current_algorithm}")

                    # Pause button (only in AI mode)
                    elif (
                        not human_mode and SCREEN_WIDTH - 230 <= x <= SCREEN_WIDTH - 130
                    ):
                        paused = not paused

                    # Step button (only in AI mode)
                    elif (
                        not human_mode and SCREEN_WIDTH - 120 <= x <= SCREEN_WIDTH - 20
                    ):
                        if solution and solution_index < len(solution):
                            move = solution[solution_index]
                            game.make_move(move)
                            solution_index += 1

                # Handle human player card clicks
                elif human_mode:
                    move, new_selected_source = game.handle_human_click(
                        x, y, selected_source
                    )
                    if move:
                        last_human_move = move
                        hint_move = None  # Clear any hint when a move is made
                        last_move_time = current_time
                    selected_source = new_selected_source

                    # Check if game is solved
                    if game.is_solved():
                        print("Congratulations! You solved the puzzle!")

        # Process automatic solution steps if not paused and not in human mode
        if (
            solving
            and solution
            and solution_index < len(solution)
            and not paused
            and not human_mode
        ):
            # Check if it's time for the next move
            if current_time - last_move_time >= animation_delay:
                highlight_move = solution[solution_index]
                game.draw(
                    highlight_move=highlight_move,
                    stats=stats,
                    algorithm=current_algorithm,
                    human_mode=human_mode,
                    selected_card=None,
                    selected_source=selected_source,
                    has_solution=solution is not None,
                    hint_move=None,
                )
                pygame.display.flip()
                time.sleep(0.2)  # Brief pause to show the highlighted move

                game.make_move(highlight_move)
                solution_index += 1
                last_move_time = current_time

                if solution_index >= len(solution):
                    solving = False
        else:
            # Clear the hint after 3 seconds
            if hint_move and current_time - hint_time > 3.0:
                hint_move = None

            # Regular drawing without animation delay
            game.draw(
                stats=stats,
                algorithm=current_algorithm,
                highlight_move=last_human_move
                if human_mode
                else (
                    solution[solution_index - 1]
                    if solution
                    and solution_index > 0
                    and solution_index < len(solution)
                    else None
                ),
                human_mode=human_mode,
                selected_card=None,
                selected_source=selected_source,
                has_solution=solution is not None,
                hint_move=hint_move,
            )

            # Clear the last human move after a short display
            if last_human_move and current_time - last_move_time > 0.5:
                last_human_move = None

        # Cap the frame rate
        clock.tick(60)


if __name__ == "__main__":
    main()
