import random
import sys
import time
from collections import deque
import heapq
import pygame
import os

from PerformanceMetrics_Mac import (
    PerformanceMetrics,
)  # Assuming typo in original; should be "PerformanceMetrics"

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
GREEN = (0, 128, 0)
RED = (180, 0, 0)
BLUE = (0, 0, 180)
GRAY = (200, 200, 200)
DARK_GRAY = (169, 169, 169)
HIGHLIGHT = (220, 220, 150)
LIGHT_GREEN = (144, 238, 144)
LIGHT_ORANGE = (255, 165, 0)
LIGHT_RED = (255, 99, 71)
YELLOW = (255, 255, 0)
STEP_HIGHLIGHT = (0, 255, 0)  # Green for recently moved card in paused auto-solve

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("FreeCell Solver")

# Font
font = pygame.font.SysFont("Arial", 22)
small_font = pygame.font.SysFont("Arial", 18, bold=True)
mini_font = pygame.font.SysFont("Arial", 14)

# Animation Control
animation_delay = 0.5
paused = False
player_mode = False
selected_card = None
selected_source = None
# New variables for supermove selection
selected_sequence = None
selected_sequence_source = None
solving = False
last_moved_card = None  # Tracks the last moved card in paused auto-solve mode

# Game timer
game_timer = 0.0

# Search functionality
search_active = False
search_text = ""
current_game_number = None  # Keep track of the current game number

# Auto-move control
auto_move_enabled = True  # Default: auto-moves are enabled
auto_move_count = 0  # Track number of auto-moves for display
auto_move_display_time = 0  # Track when auto-moves happened


class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.color = RED if suit in ["H", "D"] else BLACK
        self.selected = False

    def __str__(self):
        ranks = {1: "A", 11: "J", 12: "Q", 13: "K"}
        return f"{ranks.get(self.rank, str(self.rank))}{self.suit}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return (
            isinstance(other, Card)
            and self.suit == other.suit
            and self.rank == other.rank
        )

    def __hash__(self):
        return hash((self.suit, self.rank))

    def draw(self, x, y, highlighted=False):
        bg_color = HIGHLIGHT if highlighted else WHITE
        pygame.draw.rect(screen, bg_color, (x, y, CARD_WIDTH, CARD_HEIGHT))
        pygame.draw.rect(screen, DARK_GRAY, (x, y, CARD_WIDTH, CARD_HEIGHT), 1)

        ranks = {1: "A", 11: "J", 12: "Q", 13: "K"}
        rank_str = ranks.get(self.rank, str(self.rank))
        suit_symbols = {"H": "♥", "D": "♦", "C": "♣", "S": "♠"}

        rank_text = small_font.render(rank_str, True, self.color)
        suit_text = small_font.render(suit_symbols[self.suit], True, self.color)
        screen.blit(rank_text, (x + 5, y + 5))
        screen.blit(suit_text, (x + 5 + rank_text.get_width(), y + 5))

        big_suit = font.render(suit_symbols[self.suit], True, self.color)
        screen.blit(
            big_suit,
            (
                x + CARD_WIDTH // 2 - big_suit.get_width() // 2,
                y + CARD_HEIGHT // 2 - big_suit.get_height() // 2,
            ),
        )

        bottom_rank = small_font.render(rank_str, True, self.color)
        bottom_suit = small_font.render(suit_symbols[self.suit], True, self.color)
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


class FreeCellGame:
    def __init__(self, initial_state=None, deck_size=52, difficulty=None):
        self.cascades = [[] for _ in range(8)]
        self.free_cells = [None] * 4
        self.foundations = {"H": [], "D": [], "C": [], "S": []}
        self.moves = []
        self.deck_size = deck_size
        self.difficulty = difficulty

        if initial_state is None:
            if difficulty is not None:
                self.setup_difficulty(difficulty)
            else:
                self.new_game()
        else:
            for i in range(8):
                self.cascades[i] = initial_state.cascades[i].copy()
            self.free_cells = initial_state.free_cells.copy()
            for suit in self.foundations:
                self.foundations[suit] = initial_state.foundations[suit].copy()
            self.deck_size = initial_state.deck_size

    def setup_difficulty(self, difficulty):
        self.difficulty = difficulty
        self.cascades = [[] for _ in range(8)]
        self.free_cells = [None] * 4
        self.foundations = {"H": [], "D": [], "C": [], "S": []}
        if difficulty == "easy":
            self.cascades[0] = [Card("H", 1), Card("H", 2), Card("H", 3)]
            self.cascades[1] = [Card("D", 1), Card("D", 2), Card("D", 3)]
        elif difficulty == "medium":
            self.cascades[0] = [Card("H", 1), Card("S", 2), Card("H", 3), Card("S", 4)]
            self.cascades[1] = [Card("D", 1), Card("C", 2), Card("D", 3), Card("C", 4)]
        elif difficulty == "hard":
            self.cascades[0] = [
                Card("H", 1),
                Card("S", 2),
                Card("H", 3),
                Card("S", 4),
                Card("H", 5),
            ]
            self.cascades[1] = [
                Card("D", 1),
                Card("C", 2),
                Card("D", 3),
                Card("C", 4),
                Card("D", 5),
            ]
        else:
            self.new_game()

    def new_game(self):
        suits = ["H", "D", "C", "S"]
        ranks = list(
            range(1, 14 if self.deck_size == 52 else 8 if self.deck_size == 28 else 4)
        )
        deck = [Card(suit, rank) for suit in suits for rank in ranks]
        random.shuffle(deck)
        for i, card in enumerate(deck):
            self.cascades[i % 8].append(card)

    def is_solved(self):
        return not any(self.cascades) and not any(self.free_cells)

    def can_move_to_foundation(self, card):
        if not card:
            return False
        foundation = self.foundations[card.suit]
        return (
            not foundation
            and card.rank == 1
            or (foundation and card.rank == foundation[-1].rank + 1)
        )

    def can_safely_move_to_foundation(self, card):
        """
        Checks if a card can be safely moved to the foundation.
        Aces should always be moved to the foundation.
        For other cards, they can only be moved if all lower-ranked cards
        of the same suit are already in the foundation.

        Parameters:
        card (Card): The card to check

        Returns:
        bool: True if the card can be safely moved to foundation, False otherwise
        """
        if not card:
            return False

        # First check if the card can be moved to foundation at all
        if not self.can_move_to_foundation(card):
            return False

        # Aces should always be moved to the foundation
        if card.rank == 1:
            return True

        # For other cards, check if all lower cards of the same suit are in foundation
        # This means there should be (rank - 1) cards in that suit's foundation
        required_foundation_size = card.rank - 1
        if len(self.foundations[card.suit]) != required_foundation_size:
            return False

        return True

    def auto_move_to_foundation(self):
        """
        Automatically moves cards to foundation when it's safe to do so.
        Returns the number of auto-moves made.
        """
        global auto_move_enabled, last_moved_card

        if not auto_move_enabled:
            return 0

        moves_made = 0
        auto_move_happened = True

        while auto_move_happened:
            auto_move_happened = False

            # Check cascades
            for i, cascade in enumerate(self.cascades):
                if not cascade:
                    continue

                card = cascade[-1]
                if self.can_safely_move_to_foundation(card):
                    self.make_move(("foundation", "cascade", i, card.suit))
                    if solving and paused:
                        last_moved_card = ("foundation", card.suit, card)
                    moves_made += 1
                    auto_move_happened = True
                    break

            if auto_move_happened:
                continue

            # Check free cells
            for i, card in enumerate(self.free_cells):
                if not card:
                    continue

                if self.can_safely_move_to_foundation(card):
                    self.make_move(("foundation", "free_cell", i, card.suit))
                    if solving and paused:
                        last_moved_card = ("foundation", card.suit, card)
                    moves_made += 1
                    auto_move_happened = True
                    break

        return moves_made

    def make_move_with_auto(self, move):
        """
        Makes a move and then automatically moves any cards that can safely go to foundation.
        Returns the total number of moves made (including auto-moves).
        """
        global last_moved_card, auto_move_count, auto_move_display_time

        # Make the original move
        self.make_move(move)
        moves_made = 1

        # Then do any automatic foundation moves
        auto_moves = self.auto_move_to_foundation()
        auto_move_count = auto_moves

        if auto_moves > 0:
            auto_move_display_time = time.time()

        return moves_made + auto_moves

    def can_move_to_cascade(self, card, cascade_idx):
        if not card:
            return False
        cascade = self.cascades[cascade_idx]
        if not cascade:
            return True
        top_card = cascade[-1]
        return card.rank == top_card.rank - 1 and card.color != top_card.color

    def _is_valid_sequence(self, cards):
        """
        Check if a sequence of cards forms a valid descending sequence with alternating colors.
        """
        if len(cards) <= 1:
            return True
        for i in range(len(cards) - 1):
            # Check that each card has a rank one higher than the next card and a different color
            if not (
                cards[i].rank == cards[i + 1].rank + 1
                and cards[i].color != cards[i + 1].color
            ):
                return False
        return True

    def max_cards_movable(self, dest_idx=None):
        num_free_cells = self.free_cells.count(None)
        num_empty_cascades = sum(
            1
            for i, cascade in enumerate(self.cascades)
            if not cascade and (dest_idx is None or i != dest_idx)
        )
        return (num_free_cells + 1) * (2**num_empty_cascades)

    def get_valid_moves(self):
        valid_moves = []
        for source_type in ["cascade", "free_cell"]:
            sources = (
                [(i, cascade[-1]) for i, cascade in enumerate(self.cascades) if cascade]
                if source_type == "cascade"
                else [(i, card) for i, card in enumerate(self.free_cells) if card]
            )
            for source_idx, card in sources:
                if self.can_move_to_foundation(card):
                    valid_moves.append(
                        ("foundation", source_type, source_idx, card.suit)
                    )
                if source_type == "cascade":
                    for i, cell in enumerate(self.free_cells):
                        if cell is None:
                            valid_moves.append(
                                ("free_cell", source_type, source_idx, i)
                            )
                            break
                for i in range(8):
                    if (
                        source_type != "cascade" or i != source_idx
                    ) and self.can_move_to_cascade(card, i):
                        valid_moves.append(("cascade", source_type, source_idx, i))

        for src_idx, src_cascade in enumerate(self.cascades):
            if len(src_cascade) <= 1:
                continue
            for dest_idx in range(8):
                if src_idx == dest_idx:
                    continue
                max_movable = self.max_cards_movable(
                    dest_idx if not self.cascades[dest_idx] else None
                )
                for start_idx in range(len(src_cascade) - 2, -1, -1):
                    sequence = src_cascade[start_idx:]
                    if len(sequence) > max_movable or not self._is_valid_sequence(
                        sequence
                    ):
                        continue
                    if not self.cascades[dest_idx] or (
                        sequence[0].rank == self.cascades[dest_idx][-1].rank - 1
                        and sequence[0].color != self.cascades[dest_idx][-1].color
                    ):
                        valid_moves.append(
                            ("supermove", "cascade", src_idx, dest_idx, len(sequence))
                        )
        return valid_moves

    def make_move(self, move):
        global last_moved_card
        move_type, source_type, source_idx, dest = move[0], move[1], move[2], move[3]
        if move_type == "supermove":
            num_cards = move[4]
            cards = self.cascades[source_idx][-num_cards:]
            self.cascades[source_idx] = self.cascades[source_idx][:-num_cards]
            self.cascades[dest].extend(cards)
            if solving and paused:  # Only update in paused auto-solve mode
                last_moved_card = ("cascade", dest, cards[-1])
        else:
            card = (
                self.cascades[source_idx].pop()
                if source_type == "cascade"
                else self.free_cells[source_idx]
            )
            if source_type == "free_cell":
                self.free_cells[source_idx] = None
            if move_type == "foundation":
                self.foundations[dest].append(card)
                if solving and paused:
                    last_moved_card = ("foundation", dest, card)
            elif move_type == "free_cell":
                self.free_cells[dest] = card
                if solving and paused:
                    last_moved_card = ("free_cell", dest, card)
            else:
                self.cascades[dest].append(card)
                if solving and paused:
                    last_moved_card = ("cascade", dest, card)
        self.moves.append(move)

    def handle_click(self, x, y):
        global selected_card, selected_source, hint_move, selected_sequence, selected_sequence_source, auto_move_enabled, auto_move_count, auto_move_display_time

        # Check for auto-move toggle button click

        auto_toggle_rect = pygame.Rect(SCREEN_WIDTH - 340, SCREEN_HEIGHT - 60, 100, 40)
        if auto_toggle_rect.collidepoint((x, y)):
            auto_move_enabled = not auto_move_enabled
            return

        # If no card is selected and no sequence is selected
        if selected_card is None and selected_sequence is None:
            for i, cascade in enumerate(self.cascades):
                if (
                    cascade
                    and 50 + i * (CARD_WIDTH + CARD_MARGIN)
                    <= x
                    <= 50 + i * (CARD_WIDTH + CARD_MARGIN) + CARD_WIDTH
                ):
                    # Find which card in the cascade was clicked
                    for j in range(len(cascade)):
                        card_y = 250 + j * 30
                        if card_y <= y <= card_y + CARD_HEIGHT:
                            # If clicked on a card that's not the last one, check if it's part of a valid sequence
                            if j < len(cascade) - 1:
                                sequence = cascade[j:]
                                if (
                                    self._is_valid_sequence(sequence)
                                    and len(sequence) <= self.max_cards_movable()
                                ):
                                    # Select the sequence for a supermove
                                    selected_sequence = sequence
                                    selected_sequence_source = ("cascade", i, j)
                                    return
                            # Otherwise select just the last card for a regular move
                            if j == len(cascade) - 1:
                                selected_card = cascade[-1]
                                selected_source = ("cascade", i)
                                return

                    # If clicked on the cascade area but not on a specific card
                    card_y = 250 + (len(cascade) - 1) * 30
                    if 250 <= y <= card_y + CARD_HEIGHT:
                        selected_card = cascade[-1]
                        selected_source = ("cascade", i)
                        return

            for i, card in enumerate(self.free_cells):
                if (
                    card
                    and 50 + i * (CARD_WIDTH + CARD_MARGIN)
                    <= x
                    <= 50 + i * (CARD_WIDTH + CARD_MARGIN) + CARD_WIDTH
                    and 100 <= y <= 220
                ):
                    selected_card = card
                    selected_source = ("free_cell", i)
                    return

        # If a card or sequence is selected
        else:
            move_made = False

            # If a sequence is selected
            if selected_sequence is not None:
                for i in range(8):
                    cascade_x = 50 + i * (CARD_WIDTH + CARD_MARGIN)
                    if cascade_x <= x <= cascade_x + CARD_WIDTH and 250 <= y:
                        src_idx = selected_sequence_source[1]
                        src_start_idx = selected_sequence_source[2]

                        # Check if the sequence can be moved to this cascade
                        if src_idx != i and (
                            not self.cascades[i]
                            or (
                                selected_sequence[0].rank
                                == self.cascades[i][-1].rank - 1
                                and selected_sequence[0].color
                                != self.cascades[i][-1].color
                            )
                        ):
                            # Make the supermove
                            num_cards = len(selected_sequence)
                            self.make_move_with_auto(
                                ("supermove", "cascade", src_idx, i, num_cards)
                            )
                            move_made = True

            # If a single card is selected
            else:
                for i, suit in enumerate(["H", "D", "C", "S"]):
                    if (
                        SCREEN_WIDTH - 50 - CARD_WIDTH - i * (CARD_WIDTH + CARD_MARGIN)
                        <= x
                        <= SCREEN_WIDTH - 50 - i * (CARD_WIDTH + CARD_MARGIN)
                        and 100 <= y <= 220
                    ):
                        if self.can_move_to_foundation(selected_card):
                            self.make_move_with_auto(
                                (
                                    "foundation",
                                    selected_source[0],
                                    selected_source[1],
                                    suit,
                                )
                            )
                            move_made = True
                for i in range(8):
                    cascade_x = 50 + i * (CARD_WIDTH + CARD_MARGIN)
                    if cascade_x <= x <= cascade_x + CARD_WIDTH and 250 <= y:
                        if self.can_move_to_cascade(selected_card, i):
                            self.make_move_with_auto(
                                ("cascade", selected_source[0], selected_source[1], i)
                            )
                            move_made = True
                for i in range(4):
                    if (
                        50 + i * (CARD_WIDTH + CARD_MARGIN)
                        <= x
                        <= 50 + i * (CARD_WIDTH + CARD_MARGIN) + CARD_WIDTH
                        and 100 <= y <= 220
                    ):
                        if (
                            self.free_cells[i] is None
                            and selected_source[0] == "cascade"
                        ):
                            self.make_move_with_auto(
                                ("free_cell", selected_source[0], selected_source[1], i)
                            )
                            move_made = True

            if move_made:
                selected_card = selected_source = selected_sequence = (
                    selected_sequence_source
                ) = hint_move = None
            else:
                selected_card = selected_source = selected_sequence = (
                    selected_sequence_source
                ) = None  # Unselect if move is invalid

    def heuristic(self):
        score = 0
        for suit in self.foundations:
            score -= len(self.foundations[suit]) * 10
        for cell in self.free_cells:
            if cell:
                score += 5
        for cascade in self.cascades:
            for i in range(len(cascade) - 1):
                if not (
                    cascade[i].rank == cascade[i + 1].rank + 1
                    and cascade[i].color != cascade[i + 1].color
                ):
                    score += 1
        return score

    def heuristic3(self):
        cards_in_foundations = {
            suit: set(card.rank for card in self.foundations[suit])
            for suit in ["H", "D", "C", "S"]
        }
        total_min_moves = 0
        for cascade in self.cascades:
            for card in cascade:
                total_min_moves += max(
                    1,
                    sum(
                        1
                        for r in range(1, card.rank)
                        if r not in cards_in_foundations[card.suit]
                    ),
                )
        for card in self.free_cells:
            if card:
                total_min_moves += max(
                    1,
                    sum(
                        1
                        for r in range(1, card.rank)
                        if r not in cards_in_foundations[card.suit]
                    ),
                )
        return total_min_moves

    def __lt__(self, other):
        return self.heuristic() < other.heuristic()

    def __eq__(self, other):
        return (
            isinstance(other, FreeCellGame)
            and self.cascades == other.cascades
            and self.free_cells == other.free_cells
            and self.foundations == other.foundations
        )

    def __hash__(self):
        return hash(
            (
                tuple(tuple(c) for c in self.cascades),
                tuple(self.free_cells),
                tuple(
                    (suit, tuple(self.foundations[suit]))
                    for suit in sorted(self.foundations)
                ),
            )
        )

    def draw(
        self,
        highlight_move=None,
        stats=None,
        algorithm="A*",
        hint_move=None,
        auto_moves=None,
    ):
        screen.fill(GREEN)
        pygame.draw.rect(screen, DARK_GRAY, (0, 0, SCREEN_WIDTH, 60))

        algo_label = small_font.render("Algorithm:", True, WHITE)
        screen.blit(algo_label, (20, 20))
        algo_rect = pygame.Rect(120, 15, 150, 30)
        pygame.draw.rect(screen, WHITE, algo_rect)
        pygame.draw.rect(screen, BLACK, algo_rect, 1)
        algo_text = small_font.render(algorithm, True, BLACK)
        screen.blit(algo_text, (algo_rect.x + 10, algo_rect.y + 5))

        game_ended = self.is_solved() or (player_mode and not self.get_valid_moves())
        solve_rect = pygame.Rect(290, 15, 100, 30)
        if not game_ended:
            pygame.draw.rect(screen, BLUE, solve_rect)
            pygame.draw.rect(screen, BLACK, solve_rect, 1)
            solve_text = small_font.render("Solve", True, WHITE)
            screen.blit(solve_text, (solve_rect.x + 30, solve_rect.y + 5))

        new_game_rect = pygame.Rect(410, 15, 120, 30)
        pygame.draw.rect(screen, BLUE, new_game_rect)
        pygame.draw.rect(screen, BLACK, new_game_rect, 1)
        new_game_text = small_font.render("New Game", True, WHITE)
        screen.blit(new_game_text, (new_game_rect.x + 20, new_game_rect.y + 5))

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

        difficulty_start_x = 750
        difficulties = [
            ("Easy", "easy", LIGHT_GREEN),
            ("Medium", "medium", LIGHT_ORANGE),
            ("Hard", "hard", LIGHT_RED),
        ]
        for i, (label, diff_level, color) in enumerate(difficulties):
            diff_rect = pygame.Rect(difficulty_start_x, 15, 70, 30)
            if self.difficulty == diff_level:
                pygame.draw.rect(screen, WHITE, (difficulty_start_x - 2, 13, 74, 34), 2)
            pygame.draw.rect(screen, color, diff_rect)
            pygame.draw.rect(screen, BLACK, diff_rect, 1)
            diff_text = small_font.render(label, True, BLACK)
            screen.blit(diff_text, (difficulty_start_x + 15, 20))
            difficulty_start_x += 80

        timer_text = small_font.render(f"Time: {game_timer:.1f}s", True, WHITE)
        screen.blit(timer_text, (10, SCREEN_HEIGHT - 30))

        # Draw auto-move toggle button
        auto_toggle_rect = pygame.Rect(SCREEN_WIDTH - 340, SCREEN_HEIGHT - 60, 100, 40)
        pygame.draw.rect(
            screen, YELLOW if auto_move_enabled else DARK_GRAY, auto_toggle_rect
        )
        pygame.draw.rect(screen, BLACK, auto_toggle_rect, 1)
        auto_text = small_font.render(
            "Auto-Move", True, BLACK if auto_move_enabled else WHITE
        )
        screen.blit(auto_text, (SCREEN_WIDTH - 330, SCREEN_HEIGHT - 50))

        source_pos = dest_pos = None
        for i, card in enumerate(self.free_cells):
            x = 50 + i * (CARD_WIDTH + CARD_MARGIN)
            y = 100
            is_regular_highlight = (
                (selected_card and selected_source == ("free_cell", i))
                or (
                    highlight_move
                    and highlight_move[0] == "free_cell"
                    and highlight_move[3] == i
                )
                or (
                    highlight_move
                    and highlight_move[1] == "free_cell"
                    and highlight_move[2] == i
                )
                or (hint_move and hint_move[0] == "free_cell" and hint_move[3] == i)
                or (hint_move and hint_move[1] == "free_cell" and hint_move[2] == i)
            )
            is_step_highlight = (
                solving
                and paused
                and last_moved_card
                and last_moved_card[0] == "free_cell"
                and last_moved_card[1] == i
                and card == last_moved_card[2]
            )
            if is_regular_highlight and highlight_move:
                dest_pos = (
                    (x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2)
                    if highlight_move[0] == "free_cell"
                    else source_pos
                )
                source_pos = (
                    (x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2)
                    if highlight_move[1] == "free_cell"
                    else source_pos
                )
            elif is_regular_highlight and hint_move:
                dest_pos = (
                    (x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2)
                    if hint_move[0] == "free_cell"
                    else dest_pos
                )
                source_pos = (
                    (x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2)
                    if hint_move[1] == "free_cell"
                    else source_pos
                )
            pygame.draw.rect(screen, GRAY, (x, y, CARD_WIDTH, CARD_HEIGHT))
            border_color = (
                STEP_HIGHLIGHT
                if is_step_highlight
                else BLUE
                if is_regular_highlight
                else DARK_GRAY
            )
            pygame.draw.rect(
                screen,
                border_color,
                (x, y, CARD_WIDTH, CARD_HEIGHT),
                3 if (is_regular_highlight or is_step_highlight) else 1,
            )
            if card:
                card.draw(x, y, is_regular_highlight)
            label = mini_font.render(f"Free Cell {i + 1}", True, WHITE)
            screen.blit(label, (x, y - 20))

        for i, suit in enumerate(["H", "D", "C", "S"]):
            x = SCREEN_WIDTH - 50 - CARD_WIDTH - i * (CARD_WIDTH + CARD_MARGIN)
            y = 100
            is_regular_highlight = (
                highlight_move
                and highlight_move[0] == "foundation"
                and highlight_move[3] == suit
            ) or (hint_move and hint_move[0] == "foundation" and hint_move[3] == suit)
            is_step_highlight = (
                solving
                and paused
                and last_moved_card
                and last_moved_card[0] == "foundation"
                and last_moved_card[1] == suit
                and self.foundations[suit]
                and self.foundations[suit][-1] == last_moved_card[2]
            )
            if is_regular_highlight:
                dest_pos = (x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2)
            pygame.draw.rect(screen, GRAY, (x, y, CARD_WIDTH, CARD_HEIGHT))
            border_color = (
                STEP_HIGHLIGHT
                if is_step_highlight
                else BLUE
                if is_regular_highlight
                else DARK_GRAY
            )
            pygame.draw.rect(
                screen,
                border_color,
                (x, y, CARD_WIDTH, CARD_HEIGHT),
                3 if (is_regular_highlight or is_step_highlight) else 1,
            )
            if self.foundations[suit]:
                self.foundations[suit][-1].draw(x, y, is_regular_highlight)
            else:
                suit_symbols = {"H": "♥", "D": "♦", "C": "♣", "S": "♠"}
                suit_color = RED if suit in ["H", "D"] else BLACK
                suit_text = font.render(suit_symbols[suit], True, suit_color)
                screen.blit(
                    suit_text, (x + CARD_WIDTH // 2 - 10, y + CARD_HEIGHT // 2 - 15)
                )
            label = mini_font.render(f"{suit} Foundation", True, WHITE)
            screen.blit(label, (x, y - 20))

        for i, cascade in enumerate(self.cascades):
            x = 50 + i * (CARD_WIDTH + CARD_MARGIN)
            y = 250
            label = mini_font.render(f"Cascade {i + 1}", True, WHITE)
            screen.blit(label, (x, y - 20))
            pygame.draw.rect(screen, GRAY, (x, y, CARD_WIDTH, CARD_HEIGHT), 1)
            for j, card in enumerate(cascade):
                card_y = y + j * 30
                # Check if this card is part of a selected sequence
                is_selected_sequence = (
                    selected_sequence is not None
                    and selected_sequence_source is not None
                    and selected_sequence_source[0] == "cascade"
                    and selected_sequence_source[1] == i
                    and j >= selected_sequence_source[2]
                )

                is_regular_highlight = (
                    is_selected_sequence
                    or (
                        selected_card
                        and selected_source == ("cascade", i)
                        and j == len(cascade) - 1
                    )
                    or (
                        highlight_move
                        and highlight_move[0] == "supermove"
                        and highlight_move[2] == i
                        and j >= len(cascade) - highlight_move[4]
                    )
                    or (
                        highlight_move
                        and highlight_move[0] == "supermove"
                        and highlight_move[3] == i
                        and j == len(cascade) - 1
                    )
                    or (
                        highlight_move
                        and highlight_move[1] == "cascade"
                        and highlight_move[2] == i
                        and j == len(cascade) - 1
                    )
                    or (
                        highlight_move
                        and highlight_move[0] == "cascade"
                        and highlight_move[3] == i
                        and j == len(cascade) - 1
                    )
                    or (
                        hint_move
                        and hint_move[0] == "supermove"
                        and hint_move[2] == i
                        and j >= len(cascade) - hint_move[4]
                    )
                    or (
                        hint_move
                        and hint_move[0] == "supermove"
                        and hint_move[3] == i
                        and j == len(cascade) - 1
                    )
                    or (
                        hint_move
                        and hint_move[1] == "cascade"
                        and hint_move[2] == i
                        and j == len(cascade) - 1
                    )
                    or (
                        hint_move
                        and hint_move[0] == "cascade"
                        and hint_move[3] == i
                        and j == len(cascade) - 1
                    )
                )
                is_step_highlight = (
                    solving
                    and paused
                    and last_moved_card
                    and last_moved_card[0] == "cascade"
                    and last_moved_card[1] == i
                    and card == last_moved_card[2]
                    and j == len(cascade) - 1
                )
                if is_regular_highlight and highlight_move:
                    if (
                        highlight_move[0] == "supermove"
                        and highlight_move[2] == i
                        and j == len(cascade) - highlight_move[4]
                    ):
                        source_pos = (x + CARD_WIDTH // 2, card_y + CARD_HEIGHT // 2)
                    elif (
                        highlight_move[0] in ["supermove", "cascade"]
                        and highlight_move[3] == i
                        and j == len(cascade) - 1
                    ):
                        dest_pos = (x + CARD_WIDTH // 2, card_y + CARD_HEIGHT // 2)
                    elif (
                        highlight_move[1] == "cascade"
                        and highlight_move[2] == i
                        and j == len(cascade) - 1
                    ):
                        source_pos = (x + CARD_WIDTH // 2, card_y + CARD_HEIGHT // 2)
                elif is_regular_highlight and hint_move:
                    if (
                        hint_move[0] == "supermove"
                        and hint_move[2] == i
                        and j == len(cascade) - hint_move[4]
                    ):
                        source_pos = (x + CARD_WIDTH // 2, card_y + CARD_HEIGHT // 2)
                    elif (
                        hint_move[0] in ["supermove", "cascade"]
                        and hint_move[3] == i
                        and j == len(cascade) - 1
                    ):
                        dest_pos = (x + CARD_WIDTH // 2, card_y + CARD_HEIGHT // 2)
                    elif (
                        hint_move[1] == "cascade"
                        and hint_move[2] == i
                        and j == len(cascade) - 1
                    ):
                        source_pos = (x + CARD_WIDTH // 2, card_y + CARD_HEIGHT // 2)
                card.draw(x, card_y, is_regular_highlight)
                border_color = (
                    STEP_HIGHLIGHT
                    if is_step_highlight
                    else BLUE
                    if is_regular_highlight
                    else DARK_GRAY
                )
                pygame.draw.rect(
                    screen,
                    border_color,
                    (x, card_y, CARD_WIDTH, CARD_HEIGHT),
                    3 if (is_regular_highlight or is_step_highlight) else 1,
                )

        if (highlight_move or hint_move) and source_pos and dest_pos:
            pygame.draw.line(
                screen, BLUE if highlight_move else YELLOW, source_pos, dest_pos, 3
            )
            arrow_size = 8
            angle = pygame.math.Vector2(
                dest_pos[0] - source_pos[0], dest_pos[1] - source_pos[1]
            ).normalize()
            pygame.draw.polygon(
                screen,
                BLUE if highlight_move else YELLOW,
                [
                    dest_pos,
                    (
                        dest_pos[0] - arrow_size * angle.x + arrow_size * angle.y / 2,
                        dest_pos[1] - arrow_size * angle.y - arrow_size * angle.x / 2,
                    ),
                    (
                        dest_pos[0] - arrow_size * angle.x - arrow_size * angle.y / 2,
                        dest_pos[1] - arrow_size * angle.y + arrow_size * angle.x / 2,
                    ),
                ],
            )

        button_y = SCREEN_HEIGHT - 60
        if not game_ended:
            step_rect = pygame.Rect(SCREEN_WIDTH - 120, button_y, 100, 40)
            pygame.draw.rect(screen, (0, 140, 0), step_rect)
            pygame.draw.rect(screen, BLACK, step_rect, 1)
            step_text = small_font.render("Step", True, WHITE)
            screen.blit(step_text, (SCREEN_WIDTH - 105, button_y + 10))

            pause_rect = pygame.Rect(SCREEN_WIDTH - 230, button_y, 100, 40)
            pygame.draw.rect(screen, DARK_GRAY, pause_rect)
            pygame.draw.rect(screen, BLACK, pause_rect, 1)
            pause_text = small_font.render(
                "Pause" if not paused else "Resume", True, WHITE
            )
            screen.blit(pause_text, (SCREEN_WIDTH - 215, button_y + 10))

        button_pos_x = SCREEN_WIDTH - 150
        button_pos_y = 250
        if not solving and not player_mode:
            play_rect = pygame.Rect(button_pos_x, button_pos_y, 130, 30)
            pygame.draw.rect(screen, BLUE, play_rect)
            pygame.draw.rect(screen, BLACK, play_rect, 1)
            play_text = small_font.render("I want to play", True, WHITE)
            screen.blit(play_text, (button_pos_x + 5, button_pos_y + 5))
        elif player_mode and not solving and not game_ended:
            hint_rect = pygame.Rect(button_pos_x, button_pos_y, 100, 30)
            pygame.draw.rect(screen, YELLOW, hint_rect)
            pygame.draw.rect(screen, BLACK, hint_rect, 1)
            hint_text = small_font.render("Hint", True, BLACK)
            screen.blit(hint_text, (button_pos_x + 15, button_pos_y + 5))

        pygame.draw.rect(
            screen, DARK_GRAY, (SCREEN_WIDTH - 230, button_y - 50, 210, 30)
        )
        pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH - 230, button_y - 50, 210, 30), 1)
        speed_text = mini_font.render(
            f"Animation Speed: {animation_delay:.1f}s", True, WHITE
        )
        screen.blit(speed_text, (SCREEN_WIDTH - 220, button_y - 45))

        info_text = mini_font.render(
            "Shortcuts: Space=Pause, N=New Game, S=Step, +/- = Speed", True, WHITE
        )
        screen.blit(info_text, (200, SCREEN_HEIGHT - 20))

        # Draw search box (moved to left side)
        search_box_rect = pygame.Rect(50, SCREEN_HEIGHT - 60, 120, 30)
        pygame.draw.rect(screen, WHITE, search_box_rect)
        pygame.draw.rect(screen, BLACK, search_box_rect, 1)
        search_label = mini_font.render("Game #:", True, WHITE)
        screen.blit(search_label, (search_box_rect.x - 50, search_box_rect.y + 5))
        search_content = small_font.render(search_text, True, BLACK)
        screen.blit(search_content, (search_box_rect.x + 5, search_box_rect.y + 5))

        # Display current game number if available
        if current_game_number is not None:
            game_num_text = mini_font.render(
                f"Current Game: {current_game_number}", True, WHITE
            )
            screen.blit(game_num_text, (200, SCREEN_HEIGHT - 50))

        # Display auto-move notification
        if auto_moves and auto_moves > 0:
            auto_move_text = font.render(
                f"{auto_moves} cards auto-moved to foundation!", True, YELLOW
            )
            screen.blit(
                auto_move_text,
                (SCREEN_WIDTH // 2 - auto_move_text.get_width() // 2, 70),
            )

        if search_active:
            # Draw cursor
            cursor_pos = search_box_rect.x + 5 + small_font.size(search_text)[0]
            if int(time.time() * 2) % 2 == 0:  # Blink cursor
                pygame.draw.line(
                    screen,
                    BLACK,
                    (cursor_pos, search_box_rect.y + 5),
                    (cursor_pos, search_box_rect.y + 25),
                    1,
                )

        if game_ended:
            message = (
                "The game has finished!"
                if self.is_solved()
                else "No more available moves!"
            )
            end_text = font.render(message, True, YELLOW)
            screen.blit(
                end_text,
                (SCREEN_WIDTH // 2 - end_text.get_width() // 2, SCREEN_HEIGHT // 2),
            )

        pygame.display.flip()


def load_game_from_file(game_number):
    """Load a specific FreeCell game layout from a file."""
    global current_game_number
    try:
        file_path = f"games/game{game_number}.txt"
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Create a new game state
        game = FreeCellGame()
        game.cascades = [[] for _ in range(8)]
        game.free_cells = [None] * 4
        game.foundations = {"H": [], "D": [], "C": [], "S": []}

        # Split content by rows
        rows = [row.strip() for row in content.split("\n") if row.strip()]

        # Process each row
        for row_idx, row in enumerate(rows):
            cards = [card.strip() for card in row.split("\t") if card.strip()]

            for col_idx, card_str in enumerate(cards):
                if col_idx >= 8:  # Ensure we don't exceed 8 cascades
                    break

                # Parse the card
                if len(card_str) >= 3 and card_str[:2] == "10":
                    rank = 10
                    suit_char = card_str[2]
                else:
                    rank_char = card_str[0]
                    suit_char = card_str[1]

                    # Convert rank to int
                    if rank_char == "A":
                        rank = 1
                    elif rank_char == "J":
                        rank = 11
                    elif rank_char == "Q":
                        rank = 12
                    elif rank_char == "K":
                        rank = 13
                    else:
                        rank = int(rank_char)

                # Convert suit symbol to letter code
                suit_map = {"♥": "H", "♦": "D", "♣": "C", "♠": "S"}
                suit = suit_map.get(suit_char)

                if not suit:
                    raise ValueError(f"Invalid suit in card: {card_str}")

                # Add card to the appropriate cascade
                game.cascades[col_idx].append(Card(suit, rank))

        print(f"Successfully loaded game {game_number}")
        current_game_number = game_number
        return game
    except Exception as e:
        print(f"Error loading game {game_number}: {e}")
        return None


def save_solution_to_file(game_number, solution, metrics):
    """Save solution data to a file."""
    if game_number is None:
        game_number = "unknown"

    filename = f"solution_game_{game_number}.txt"

    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(f"Solution for Game {game_number}\n")
            file.write("=" * 50 + "\n\n")

            # Write performance metrics
            elapsed_time = metrics.end_time - metrics.start_time

            file.write("Performance Metrics:\n")
            file.write("-" * 50 + "\n")
            file.write(f"Time taken: {elapsed_time:.2f} seconds\n")
            file.write(f"States explored: {metrics.states_explored}\n")
            file.write(f"States generated: {metrics.states_generated}\n")
            file.write(f"Maximum queue size: {metrics.max_queue_size}\n")
            file.write(f"Maximum depth reached: {metrics.max_depth_reached}\n")
            file.write(f"Solution length: {len(solution)}\n\n")

            # Write solution moves
            file.write("Solution Moves:\n")
            file.write("-" * 50 + "\n")
            for i, move in enumerate(solution):
                file.write(f"Move {i + 1}: {format_move(move)}\n")

        print(f"Solution saved to {filename}")
        return True
    except Exception as e:
        print(f"Error saving solution: {e}")
        return False


def format_move(move):
    """Format a move into a human-readable string."""
    move_type, source_type, source_idx, dest = move[0], move[1], move[2], move[3]

    if move_type == "supermove":
        num_cards = move[4]
        return f"Move {num_cards} cards from Cascade {source_idx + 1} to Cascade {dest + 1}"

    if source_type == "cascade":
        source_desc = f"Cascade {source_idx + 1}"
    else:  # free_cell
        source_desc = f"Free Cell {source_idx + 1}"

    if move_type == "foundation":
        return f"Move card from {source_desc} to {dest} Foundation"
    elif move_type == "free_cell":
        return f"Move card from {source_desc} to Free Cell {dest + 1}"
    else:  # cascade
        return f"Move card from {source_desc} to Cascade {dest + 1}"


def test_auto_move():
    """
    Create a test game with a specific layout to test auto-move functionality
    """
    game = FreeCellGame()

    # Clear the game state
    game.cascades = [[] for _ in range(8)]
    game.free_cells = [None] * 4
    game.foundations = {"H": [], "D": [], "C": [], "S": []}

    # Add some aces to cascades - these should be auto-moved
    game.cascades[0].append(Card("H", 1))  # Hearts Ace
    game.cascades[1].append(Card("D", 1))  # Diamonds Ace

    # Add some twos - these should not be auto-moved yet
    game.cascades[2].append(Card("H", 2))  # Hearts 2
    game.cascades[3].append(Card("D", 2))  # Diamonds 2

    # Add cards to free cells
    game.free_cells[0] = Card("C", 1)  # Clubs Ace - should be auto-moved
    game.free_cells[1] = Card("S", 1)  # Spades Ace - should be auto-moved

    # Test the auto-move functionality
    auto_moves = game.auto_move_to_foundation()
    print(f"Auto-moved {auto_moves} cards - should be 4 aces")

    # Check which cards are now in foundations
    for suit in ["H", "D", "C", "S"]:
        print(f"{suit} foundation: {[str(card) for card in game.foundations[suit]]}")

    # Now the twos should be auto-moved
    auto_moves = game.auto_move_to_foundation()
    print(f"Auto-moved {auto_moves} more cards - should be 2 twos")

    # Check foundations again
    for suit in ["H", "D", "C", "S"]:
        print(f"{suit} foundation: {[str(card) for card in game.foundations[suit]]}")

    # Add a three of hearts - this should be auto-moved because hearts 2 is on foundation
    game.cascades[4].append(Card("H", 3))
    auto_moves = game.auto_move_to_foundation()
    print(f"Auto-moved {auto_moves} more cards - should be 1 (hearts 3)")

    # Check foundations
    for suit in ["H", "D", "C", "S"]:
        print(f"{suit} foundation: {[str(card) for card in game.foundations[suit]]}")

    # Add a four of hearts and three of clubs (should not auto-move clubs 3 yet)
    game.cascades[5].append(Card("H", 4))
    game.cascades[6].append(Card("C", 3))
    auto_moves = game.auto_move_to_foundation()
    print(f"Auto-moved {auto_moves} more cards - should be 1 (hearts 4)")

    # Now add clubs 2 to foundation manually and see if clubs 3 gets auto-moved
    game.foundations["C"].append(Card("C", 2))
    auto_moves = game.auto_move_to_foundation()
    print(f"Auto-moved {auto_moves} more cards - should be 1 (clubs 3)")

    # Final foundation state
    for suit in ["H", "D", "C", "S"]:
        print(
            f"Final {suit} foundation: {[str(card) for card in game.foundations[suit]]}"
        )

    return game


def solve_freecell_astar(game):
    metrics = PerformanceMetrics()
    metrics.start()
    queue = [(game.heuristic3(), id(game), game, [])]
    heapq.heapify(queue)
    visited = {hash(game)}
    max_states = 150000
    metrics.states_explored = metrics.states_generated = metrics.max_queue_size = 1

    while queue and metrics.states_explored < max_states:
        _, _, current_game, moves = heapq.heappop(queue)
        metrics.states_explored += 1
        metrics.max_depth_reached = max(metrics.max_depth_reached, len(moves))
        if current_game.is_solved():
            metrics.stop(moves)
            return moves, metrics
        for move in current_game.get_valid_moves():
            new_game = FreeCellGame(current_game)
            # Make the move and any resulting auto-moves
            new_game.make_move(move)
            new_game.auto_move_to_foundation()

            metrics.states_generated += 1
            new_hash = hash(new_game)
            if new_hash in visited:
                continue
            heapq.heappush(
                queue,
                (
                    new_game.heuristic3() + len(moves) + 1,
                    id(new_game),
                    new_game,
                    moves + [move],
                ),
            )
            visited.add(new_hash)
            metrics.max_queue_size = max(metrics.max_queue_size, len(queue))
    metrics.stop()
    return None, metrics


def solve_freecell_weighted_astar(game, weight=1.5):
    metrics = PerformanceMetrics()
    metrics.start()

    # Priority queue for WA* search - f(n) = g(n) + w * h(n)
    queue = [(game.heuristic3() * weight, id(game), game, [])]
    heapq.heapify(queue)

    # Set to keep track of visited states
    visited = set()
    visited.add(hash(game))

    # Maximum number of states to explore
    max_states = 15000000
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
            # Make the move and any resulting auto-moves
            new_game.make_move(move)
            new_game.auto_move_to_foundation()

            metrics.states_generated += 1

            # Skip if we've seen this state before
            new_hash = hash(new_game)
            if new_hash in visited:
                continue

            # Add the new state to the queue
            new_moves = moves + [move]
            # WA* uses f(n) = g(n) + w * h(n) for sorting
            heapq.heappush(
                queue,
                (
                    len(new_moves) + weight * new_game.heuristic3(),
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


def get_hint(game):
    moves, _ = solve_freecell_astar(game)
    return moves[0] if moves else None


def solve_freecell_bestfirst(game):
    metrics = PerformanceMetrics()
    metrics.start()
    queue = [(game.heuristic(), id(game), game, [])]
    heapq.heapify(queue)
    visited = {hash(game)}
    max_states = 15000
    metrics.states_explored = metrics.states_generated = metrics.max_queue_size = 1

    while queue and metrics.states_explored < max_states:
        _, _, current_game, moves = heapq.heappop(queue)
        metrics.states_explored += 1
        metrics.max_depth_reached = max(metrics.max_depth_reached, len(moves))
        if current_game.is_solved():
            metrics.stop(moves)
            return moves, metrics
        for move in current_game.get_valid_moves():
            new_game = FreeCellGame(current_game)
            # Make the move and any resulting auto-moves
            new_game.make_move(move)
            new_game.auto_move_to_foundation()

            metrics.states_generated += 1
            new_hash = hash(new_game)
            if new_hash in visited:
                continue
            heapq.heappush(
                queue, (new_game.heuristic(), id(new_game), new_game, moves + [move])
            )
            visited.add(new_hash)
            metrics.max_queue_size = max(metrics.max_queue_size, len(queue))
    metrics.stop()
    return None, metrics


def solve_freecell_bfs(game):
    metrics = PerformanceMetrics()
    metrics.start()
    queue = deque([(game, [])])
    visited = {hash(game)}
    max_states = 15000
    metrics.states_explored = metrics.states_generated = metrics.max_queue_size = 1

    while queue and metrics.states_explored < max_states:
        current_game, moves = queue.popleft()
        metrics.states_explored += 1
        metrics.max_depth_reached = max(metrics.max_depth_reached, len(moves))
        if current_game.is_solved():
            metrics.stop(moves)
            return moves, metrics
        for move in current_game.get_valid_moves():
            new_game = FreeCellGame(current_game)
            # Make the move and any resulting auto-moves
            new_game.make_move(move)
            new_game.auto_move_to_foundation()

            metrics.states_generated += 1
            new_hash = hash(new_game)
            if new_hash in visited:
                continue
            queue.append((new_game, moves + [move]))
            visited.add(new_hash)
            metrics.max_queue_size = max(metrics.max_queue_size, len(queue))
    metrics.stop()
    return None, metrics


def solve_freecell_dfs(game):
    metrics = PerformanceMetrics()
    metrics.start()
    stack = [(game, [])]
    visited = {hash(game)}
    max_states = 15000
    max_depth = 50
    metrics.states_explored = metrics.states_generated = metrics.max_queue_size = 1

    while stack and metrics.states_explored < max_states:
        current_game, moves = stack.pop()
        metrics.states_explored += 1
        metrics.max_depth_reached = max(metrics.max_depth_reached, len(moves))
        if len(moves) > max_depth:
            continue
        if current_game.is_solved():
            metrics.stop(moves)
            return moves, metrics
        for move in reversed(current_game.get_valid_moves()):
            new_game = FreeCellGame(current_game)
            # Make the move and any resulting auto-moves
            new_game.make_move(move)
            new_game.auto_move_to_foundation()

            metrics.states_generated += 1
            new_hash = hash(new_game)
            if new_hash in visited:
                continue
            stack.append((new_game, moves + [move]))
            visited.add(new_hash)
            metrics.max_queue_size = max(metrics.max_queue_size, len(stack))
    metrics.stop()
    return None, metrics


def solve_freecell_ids(game):
    # Initialize performance metrics to track execution details
    metrics = PerformanceMetrics()
    metrics.start()
    max_states = 150000  # Maximum number of states to explore before stopping
    max_depth = 50  # Maximum depth limit for iterative deepening

    # Iteratively increase the depth limit
    for depth_limit in range(max_depth + 1):
        stack = [(game, [], 0)]  # Stack for DFS with (game state, move history, depth)
        visited = set()  # Set to track visited game states
        local_metrics = PerformanceMetrics()  # Metrics for the current depth iteration
        local_metrics.states_explored = local_metrics.states_generated = (
            local_metrics.max_queue_size
        ) = 1
        depth_reached = False  # Flag to indicate if depth limit was reached

        while stack and local_metrics.states_explored < max_states:
            current_game, moves, depth = stack.pop()
            local_metrics.states_explored += 1
            local_metrics.max_depth_reached = max(
                local_metrics.max_depth_reached, depth
            )

            # Check if the game is solved
            if current_game.is_solved():
                metrics.stop(moves)
                return moves, metrics

            # If the current depth limit is reached, mark the flag but continue exploring other nodes
            if depth >= depth_limit:
                depth_reached = True
                continue  # Ensures we backtrack instead of expanding further

            # Explore valid moves from the current game state
            for move in reversed(
                current_game.get_valid_moves()
            ):  # Reverse order for better DFS behavior
                new_game = FreeCellGame(current_game)  # Create a new game state
                # Make the move and any resulting auto-moves
                new_game.make_move(move)
                new_game.auto_move_to_foundation()

                new_hash = hash(new_game)

                # Skip already visited states to avoid loops
                if new_hash in visited:
                    continue

                stack.append(
                    (new_game, moves + [move], depth + 1)
                )  # Push new state to stack
                visited.add(new_hash)  # Mark state as visited
                local_metrics.states_generated += 1
                local_metrics.max_queue_size = max(
                    local_metrics.max_queue_size, len(stack)
                )

        # Aggregate performance metrics across depth iterations
        metrics.states_explored += local_metrics.states_explored
        metrics.states_generated += local_metrics.states_generated
        metrics.max_queue_size = max(
            metrics.max_queue_size, local_metrics.max_queue_size
        )

        # If no deeper states were encountered, stop searching
        if not depth_reached:
            break

    metrics.stop()
    return None, metrics


def solve_freecell(game, algorithm="astar"):
    return {
        "astar": solve_freecell_astar,
        "bestfirst": solve_freecell_bestfirst,
        "bfs": solve_freecell_bfs,
        "dfs": solve_freecell_dfs,
        "ids": solve_freecell_ids,
        "weighted_astar": solve_freecell_weighted_astar,
    }.get(algorithm, solve_freecell_astar)(game)


def main():
    global \
        animation_delay, \
        paused, \
        game_timer, \
        player_mode, \
        selected_card, \
        selected_source, \
        selected_sequence, \
        selected_sequence_source, \
        solving, \
        hint_move, \
        last_moved_card, \
        search_active, \
        search_text, \
        current_game_number, \
        auto_move_enabled, \
        auto_move_count, \
        auto_move_display_time

    deck_size = 52
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
    algorithms = ["A*", "Best-First", "BFS", "DFS", "IDS", "WA*"]
    algorithm_index = 0
    hint_move = None
    last_moved_card = None
    current_game_number = None
    auto_move_enabled = True
    auto_move_count = 0
    auto_move_display_time = 0

    # Initialize supermove selection variables
    selected_sequence = None
    selected_sequence_source = None

    # Search functionality
    search_active = False
    search_text = ""
    search_box_rect = pygame.Rect(50, SCREEN_HEIGHT - 60, 120, 30)

    # Make sure the games directory exists
    os.makedirs("games", exist_ok=True)

    while True:
        current_time = time.time()
        if not paused and not solving:
            game_timer = current_time - start_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if search_active:
                    if event.key == pygame.K_RETURN:
                        try:
                            game_number = int(search_text)
                            new_game = load_game_from_file(game_number)
                            if new_game:
                                game = new_game
                                solution = None
                                solution_index = 0
                                solving = player_mode = False
                                stats = hint_move = last_moved_card = None
                                selected_sequence = selected_sequence_source = None
                                start_time = time.time()
                                game_timer = 0.0
                                print(f"Loaded game {game_number}")
                            search_text = ""
                            search_active = False
                        except ValueError:
                            # Invalid number entered
                            search_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        search_text = search_text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        search_active = False
                        search_text = ""
                    else:
                        # Only add digits to limit to numbers
                        if event.unicode.isdigit() and len(search_text) < 10:
                            search_text += event.unicode
                else:
                    if event.key == pygame.K_SPACE:
                        paused = not paused
                    elif event.key == pygame.K_n:
                        game = FreeCellGame(deck_size=deck_size)
                        solution = None
                        solution_index = 0
                        solving = player_mode = False
                        stats = hint_move = last_moved_card = None
                        selected_sequence = selected_sequence_source = None
                        start_time = time.time()
                        game_timer = 0.0
                        current_game_number = None
                    elif (
                        event.key == pygame.K_s
                        and solution
                        and solution_index < len(solution)
                    ):
                        game.make_move(solution[solution_index])
                        auto_move_count = game.auto_move_to_foundation()
                        if auto_move_count > 0:
                            auto_move_display_time = current_time
                        solution_index += 1
                    elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                        animation_delay = max(0.1, animation_delay - 0.1)
                    elif event.key == pygame.K_MINUS:
                        animation_delay = min(2.0, animation_delay + 0.1)
                    elif event.key == pygame.K_t:  # Test auto-move feature
                        game = test_auto_move()
                        player_mode = True
                        solving = False
                        stats = hint_move = last_moved_card = None
                        selected_sequence = selected_sequence_source = None
                        start_time = time.time()
                        game_timer = 0.0

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                x, y = pygame.mouse.get_pos()

                # Check if search box was clicked
                if search_box_rect.collidepoint((x, y)):
                    search_active = True
                else:
                    if 0 <= y <= 60:
                        if 120 <= x <= 270 and 15 <= y <= 45:
                            algorithm_index = (algorithm_index + 1) % len(algorithms)
                            current_algorithm = algorithms[algorithm_index]
                        elif (
                            290 <= x <= 390
                            and 15 <= y <= 45
                            and not (
                                game.is_solved()
                                or (player_mode and not game.get_valid_moves())
                            )
                        ):
                            solving = True
                            paused = False
                            algo_map = {
                                "A*": "astar",
                                "Best-First": "bestfirst",
                                "BFS": "bfs",
                                "DFS": "dfs",
                                "IDS": "ids",
                                "WA*": "weighted_astar",
                            }
                            algo_key = algo_map.get(current_algorithm, "astar")
                            print(f"Using algorithm: {algo_key}")
                            solution_data, metrics = solve_freecell(game, algo_key)
                            solution = solution_data
                            solution_index = 0
                            hint_move = last_moved_card = (
                                None  # Clear hint and last moved card
                            )
                            selected_sequence = selected_sequence_source = None

                            if solution:
                                print(
                                    f"{current_algorithm} solution found with {len(solution)} moves!"
                                )
                                metrics.print_report(f"{current_algorithm}")
                                stats = (solution, metrics.states_explored)

                                # Save solution to file
                                save_solution_to_file(
                                    current_game_number, solution, metrics
                                )
                            else:
                                print(f"No {current_algorithm} solution found.")
                                metrics.print_report(
                                    f"{current_algorithm} (No Solution)"
                                )
                                solving = False
                        elif 410 <= x <= 530 and 15 <= y <= 45:
                            game = FreeCellGame(deck_size=deck_size)
                            solution = None
                            solution_index = 0
                            solving = player_mode = False
                            stats = hint_move = last_moved_card = None
                            selected_sequence = selected_sequence_source = None
                            start_time = time.time()
                            game_timer = 0.0
                            current_game_number = None
                        elif 540 <= x <= 680 and 15 <= y <= 45:
                            deck_size = (
                                52 if 540 <= x <= 560 else 28 if 600 <= x <= 620 else 12
                            )
                            game = FreeCellGame(deck_size=deck_size)
                            solution = None
                            solution_index = 0
                            solving = player_mode = False
                            stats = hint_move = last_moved_card = None
                            selected_sequence = selected_sequence_source = None
                            start_time = time.time()
                            game_timer = 0.0
                            current_game_number = None
                        # difficulty setting
                        elif 750 <= x <= 1120 and 15 <= y <= 45:
                            difficulty = (
                                "easy"
                                if 750 <= x <= 820
                                else "medium"
                                if 830 <= x <= 900
                                else "hard"
                            )
                            game = FreeCellGame(
                                deck_size=deck_size, difficulty=difficulty
                            )
                            solution = None
                            solution_index = 0
                            solving = player_mode = False
                            stats = hint_move = last_moved_card = None
                            selected_sequence = selected_sequence_source = None
                            start_time = time.time()
                            game_timer = 0.0
                            current_game_number = None
                    elif (
                        SCREEN_WIDTH - 230 <= x <= SCREEN_WIDTH - 130
                        and SCREEN_HEIGHT - 60 <= y <= SCREEN_HEIGHT - 20
                        and not (
                            game.is_solved()
                            or (player_mode and not game.get_valid_moves())
                        )
                    ):
                        paused = not paused
                    elif (
                        SCREEN_WIDTH - 120 <= x <= SCREEN_WIDTH - 20
                        and SCREEN_HEIGHT - 60 <= y <= SCREEN_HEIGHT - 20
                        and solution
                        and solution_index < len(solution)
                    ):
                        game.make_move(solution[solution_index])
                        auto_move_count = game.auto_move_to_foundation()
                        if auto_move_count > 0:
                            auto_move_display_time = current_time
                        solution_index += 1
                    elif (
                        not solving
                        and not player_mode
                        and SCREEN_WIDTH - 150 <= x <= SCREEN_WIDTH - 20
                        and 250 <= y <= 280
                    ):
                        player_mode = True
                        solution = None
                        solving = False
                        stats = hint_move = last_moved_card = None
                        selected_sequence = selected_sequence_source = None
                    elif (
                        player_mode
                        and not solving
                        and SCREEN_WIDTH - 150 <= x <= SCREEN_WIDTH - 50
                        and 250 <= y <= 280
                        and not (game.is_solved() or not game.get_valid_moves())
                    ):
                        hint_move = get_hint(game)
                    elif player_mode and not solving:
                        game.handle_click(x, y)

                    # Deactivate search when clicking elsewhere
                    if not search_box_rect.collidepoint((x, y)):
                        search_active = False

        if solving and solution and solution_index < len(solution) and not paused:
            if current_time - last_move_time >= animation_delay:
                highlight_move = solution[solution_index]
                game.draw(
                    highlight_move=highlight_move,
                    stats=stats,
                    algorithm=current_algorithm,
                )
                pygame.display.flip()
                time.sleep(0.2)
                game.make_move(highlight_move)
                auto_move_count = game.auto_move_to_foundation()
                if auto_move_count > 0:
                    auto_move_display_time = current_time
                solution_index += 1
                last_move_time = current_time
                if solution_index >= len(solution):
                    solving = False
        else:
            # Display auto-move notification if recent auto-moves happened
            if current_time - auto_move_display_time < 2.0:  # Show for 2 seconds
                game.draw(
                    stats=stats,
                    algorithm=current_algorithm,
                    hint_move=hint_move if player_mode and not solving else None,
                    auto_moves=auto_move_count,
                )
            else:
                game.draw(
                    stats=stats,
                    algorithm=current_algorithm,
                    hint_move=hint_move if player_mode and not solving else None,
                )

        clock.tick(60)


if __name__ == "__main__":
    main()
