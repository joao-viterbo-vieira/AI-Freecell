import random
import sys
import time
from collections import deque
import heapq
import pygame


from PerformaceMetrics import PerformanceMetrics


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
LIGHT_GREEN = (144, 238, 144)  # Light green for easy difficulty
LIGHT_ORANGE = (255, 165, 0)  # Orange for medium difficulty
LIGHT_RED = (255, 99, 71)  # Tomato color for hard difficulty
YELLOW = (255, 255, 0)  # For selected card highlighting

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

# Game mode
player_mode = True  # Default to player mode

# Game timer
game_timer = 0.0

# Variables for card selection in player mode
selected_card = None
selected_source = None


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

        # If the card is the globally selected card, add a yellow border
        global selected_card
        if selected_card and self == selected_card:
            pygame.draw.rect(screen, YELLOW, (x, y, CARD_WIDTH, CARD_HEIGHT), 3)


# Game state class
class FreeCellGame:
    def __init__(self, initial_state=None, deck_size=52, difficulty=None):
        self.cascades = [[] for _ in range(8)]
        self.free_cells = [None] * 4
        self.foundations = {"H": [], "D": [], "C": [], "S": []}
        self.moves = []
        self.deck_size = deck_size  # Store deck size (52, 28, or 12)
        self.difficulty = difficulty  # Store the difficulty level

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
        """Set up a predefined game with specified difficulty"""
        self.difficulty = difficulty
        
        # Clear all cascades and initialize foundations and free cells
        self.cascades = [[] for _ in range(8)]
        self.free_cells = [None] * 4
        self.foundations = {"H": [], "D": [], "C": [], "S": []}
        
        if difficulty == "easy":
            # Example setup for easy difficulty
            self.cascades[0] = [Card("H", 1), Card("S", 2), Card("H", 3)]
            self.cascades[1] = [Card("D", 1), Card("C", 2), Card("D", 3)]
            # Add more cards to other cascades as needed
            
        elif difficulty == "medium":
            # Example setup for medium difficulty
            self.cascades[0] = [Card("H", 1), Card("S", 2), Card("H", 3), Card("S", 4)]
            self.cascades[1] = [Card("D", 1), Card("C", 2), Card("D", 3), Card("C", 4)]
            # Add more cards to other cascades as needed
            
        elif difficulty == "hard":
            # Example setup for hard difficulty
            self.cascades[0] = [Card("H", 1), Card("S", 2), Card("H", 3), Card("S", 4), Card("H", 5)]
            self.cascades[1] = [Card("D", 1), Card("C", 2), Card("D", 3), Card("C", 4), Card("D", 5)]
            # Add more cards to other cascades as needed
            
        else:
            # Default to random if difficulty is not recognized
            self.new_game()

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
        # Check if all cascades and free cells are empty
        if any(self.cascades) or any(self.free_cells):
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
                    bottom_seq_card = sequence[0]  # This is actually the top card in the sequence (visually at the bottom)
                    top_dest_card = dest_cascade[-1]

                    if (
                        bottom_seq_card.rank + 1 == top_dest_card.rank
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

    def handle_click(self, x, y):
        global selected_card, selected_source
    
        # Check cascades
        for i, cascade in enumerate(self.cascades):
            cascade_x = 50 + i * (CARD_WIDTH + CARD_MARGIN)
            if cascade and cascade_x <= x <= cascade_x + CARD_WIDTH:
                # Calculate the position of each card in the cascade
                if not cascade:
                    continue
                    
                for j in range(len(cascade)):
                    card_y = 250 + j * 30  # Based on the card overlap
                    # Check if click is on this card and it's either the top card or no card is selected yet
                    if card_y <= y <= card_y + CARD_HEIGHT:
                        # If it's the top card
                        if j == len(cascade) - 1:
                            # If no card is selected, select this one
                            if selected_card is None:
                                selected_card = cascade[j]
                                selected_source = ("cascade", i)
                                print(f"Selected card from cascade {i}: {selected_card}")
                                return
                            # If card is already selected, try to move to this cascade
                            elif self.can_move_to_cascade(selected_card, i):
                                self.make_move(("cascade", selected_source[0], selected_source[1], i))
                                print(f"Moved card to cascade {i}")
                                selected_card = None
                                selected_source = None
                                return
                            # If can't move, deselect
                            else:
                                selected_card = None
                                selected_source = None
                                print("Can't move card here. Deselected.")
                                return
                        # If not top card and already have a card selected, deselect it
                        elif selected_card is not None:
                            selected_card = None
                            selected_source = None
                            print("Deselected card")
                            return
    
        # Check free cells
        for i, card in enumerate(self.free_cells):
            free_cell_x = 50 + i * (CARD_WIDTH + CARD_MARGIN)
            if free_cell_x <= x <= free_cell_x + CARD_WIDTH and 100 <= y <= 100 + CARD_HEIGHT:
                # If cell has a card and no card is selected, select this card
                if card is not None and selected_card is None:
                    selected_card = card
                    selected_source = ("free_cell", i)
                    print(f"Selected card from free cell {i}: {selected_card}")
                    return
                # If cell is empty and we have a card selected, move the card here
                elif card is None and selected_card is not None:
                    self.make_move(("free_cell", selected_source[0], selected_source[1], i))
                    print(f"Moved card to free cell {i}")
                    selected_card = None
                    selected_source = None
                    return
                # If can't do either, deselect
                elif selected_card is not None:
                    selected_card = None
                    selected_source = None
                    print("Deselected card")
                    return
    
        # Check foundations
        for i, suit in enumerate(["H", "D", "C", "S"]):
            foundation_x = SCREEN_WIDTH - 50 - CARD_WIDTH - i * (CARD_WIDTH + CARD_MARGIN)
            if foundation_x <= x <= foundation_x + CARD_WIDTH and 100 <= y <= 100 + CARD_HEIGHT:
                # If a card is selected and can move to foundation, move it
                if selected_card is not None:
                    if self.can_move_to_foundation(selected_card) and selected_card.suit == suit:
                        self.make_move(("foundation", selected_source[0], selected_source[1], suit))
                        print(f"Moved card to {suit} foundation")
                        selected_card = None
                        selected_source = None
                        return
                    else:
                        print(f"Can't move {selected_card} to {suit} foundation")
                # If clicking on foundation without a card selected, deselect any card
                elif selected_card is not None:
                    selected_card = None
                    selected_source = None
                    print("Deselected card")
                    return
        
        # If clicked elsewhere and a card is selected, deselect it
        if selected_card is not None:
            selected_card = None
            selected_source = None
            print("Deselected card")



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

        # Player Mode toggle
        player_mode_rect = pygame.Rect(SCREEN_WIDTH - 140, 15, 120, 30)
        mode_color = LIGHT_GREEN if player_mode else LIGHT_RED
        pygame.draw.rect(screen, mode_color, player_mode_rect)
        pygame.draw.rect(screen, BLACK, player_mode_rect, 1)
        mode_text = small_font.render("Player Mode", True, BLACK)
        screen.blit(mode_text, (player_mode_rect.x + 10, player_mode_rect.y + 5))

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
            
        # Difficulty buttons
        difficulty_start_x = 750
        difficulties = [
            ("Easy", "easy", LIGHT_GREEN), 
            ("Medium", "medium", LIGHT_ORANGE), 
            ("Hard", "hard", LIGHT_RED)
        ]    
        
        for i, (label, diff_level, color) in enumerate(difficulties):
            diff_rect = pygame.Rect(difficulty_start_x, 15, 70, 30)
            # Highlight the selected difficulty
            rect_color = color
            if self.difficulty == diff_level:
                # Draw a highlight border around selected difficulty
                pygame.draw.rect(screen, WHITE, (difficulty_start_x-2, 13, 74, 34), 2)
            
            pygame.draw.rect(screen, rect_color, diff_rect)
            pygame.draw.rect(screen, BLACK, diff_rect, 1)
            diff_text = small_font.render(label, True, BLACK)
            screen.blit(diff_text, (difficulty_start_x + 15, 20))
            difficulty_start_x += 80  # Move to next button position

        # Timer display
        timer_text = small_font.render(f"Time: {game_timer:.1f}s", True, WHITE)
        screen.blit(timer_text, (10, SCREEN_HEIGHT- 50 ))

        # Player mode status
        if player_mode:
            if selected_card:
                status_text = mini_font.render(f"Selected: {selected_card}", True, YELLOW)
                screen.blit(status_text, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 50))

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
                move_type = highlight_move[0]
                source_type = highlight_move[1]
                source_idx = highlight_move[2]
                dest = highlight_move[3]
                # Use safer indexing to prevent errors with different move types
                if move_type == "cascade" and dest == i:
                    is_highlighted = True
                    dest_pos = (x + CARD_WIDTH // 2, card_y + CARD_HEIGHT // 2)
                elif source_type == "cascade" and source_idx == i and j == len(cascade) - 1:
                    is_highlighted = True
                    source_pos = (x + CARD_WIDTH // 2, card_y + CARD_HEIGHT // 2)

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

            # Draw empty cascade placeholder
            if not cascade:
                cascade_color = GRAY
                pygame.draw.rect(screen, cascade_color, (x, y, CARD_WIDTH, CARD_HEIGHT))
                border_color = DARK_GRAY
                pygame.draw.rect(screen, border_color, (x, y, CARD_WIDTH, CARD_HEIGHT), 1)
            else:
                # Draw cards in the cascade
                for j, card in enumerate(cascade):
                    card_y = y + j * 30  # Adjust the y position based on the card overlap
                    is_highlighted = False
                    if highlight_move:
                        move_type, source_type, source_idx, dest = (
                            highlight_move[0],
                            highlight_move[1],
                            highlight_move[2],
                            highlight_move[3],
                        )
                        if move_type == "cascade" and dest == i:
                            is_highlighted = True
                            dest_pos = (x + CARD_WIDTH // 2, card_y + CARD_HEIGHT // 2)
                        elif source_type == "cascade" and source_idx == i and j == len(cascade) - 1:
                            is_highlighted = True
                            source_pos = (x + CARD_WIDTH // 2, card_y + CARD_HEIGHT // 2)

                    card.draw(x, card_y, is_highlighted)