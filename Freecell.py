import random
import sys
import time
from collections import deque
import heapq
import pygame
import os
import psutil
import platform


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
selected_sequence = None
selected_sequence_source = None
solving = False
last_moved_card = None  # Tracks the last moved card in paused auto-solve mode
auto_moves_enabled = False  # Start with automoves disabled

# Game timer
game_timer = 0.0

# Search functionality
search_active = False
search_text = ""
current_game_number = None  # Keep track of the current game number


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
    """
    A class representing a FreeCell Solitaire game state and its evaluation heuristics.

    Attributes:
        cascades (list): A list of 8 lists representing the tableau columns where cards are stacked.
        free_cells (list): A list of 4 slots representing temporary card storage.
        foundations (dict): A dictionary with suits ("H", "D", "C", "S") as keys and lists of cards as values,
                            representing foundation piles where cards must be stacked in ascending order.
        moves (list): A list storing moves made by the solver.
        player_moves (list): A list storing moves made by the player, including automatic moves.
        deck_size (int): The number of cards in the deck (default is 52).
        difficulty (str or None): The difficulty level of the game, if specified.
    """

    def __init__(self, initial_state=None, deck_size=52, difficulty=None):
        self.cascades = [[] for _ in range(8)]
        self.free_cells = [None] * 4
        self.foundations = {"H": [], "D": [], "C": [], "S": []}
        self.moves = []  # For solver moves
        self.player_moves = []  # For player moves in single-player mode, including automoves
        self.deck_size = deck_size
        self.difficulty = difficulty

        if initial_state is None:
            if difficulty is not None:
                loaded_game = load_game_from_file(self.setup_difficulty(difficulty))
                if loaded_game:
                    self.cascades = loaded_game.cascades
                    self.free_cells = loaded_game.free_cells
                    self.foundations = loaded_game.foundations
                    self.deck_size = loaded_game.deck_size
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
        """
        Sets up a predefined game configuration based on the specified difficulty level.

        Args:
            difficulty (str): The difficulty level ("easy" or "hard").

        Returns:
            int: A randomly selected game configuration file ID corresponding to the given difficulty level.

        The function selects a game state from predefined setups stored in files, ensuring a consistent challenge.
        """
        self.difficulty = difficulty
        self.cascades = [[] for _ in range(8)]
        self.free_cells = [None] * 4
        self.foundations = {"H": [], "D": [], "C": [], "S": []}
        files = {
            "easy": [164, 1187, 3148, 9998, 10913],
            "hard": [169, 20810, 32483, 44732],
        }
        selected_file = random.choice(files.get(difficulty, []))
        return selected_file

    def new_game(self):
        """
        Initializes a new FreeCell game with a shuffled deck.

        Creates a deck of cards based on the game mode (standard 52-card deck or smaller variants).
        Shuffles the deck and distributes the cards into the 8 cascades.

        Returns:
            None
        """
        suits = ["H", "D", "C", "S"]
        ranks = list(
            range(1, 14 if self.deck_size == 52 else 8 if self.deck_size == 28 else 4)
        )
        deck = [Card(suit, rank) for suit in suits for rank in ranks]
        random.shuffle(deck)
        for i, card in enumerate(deck):
            self.cascades[i % 8].append(card)

    def is_solved(self):
        """
        Checks whether the game is in a solved state.

        The game is considered solved when all cascades and free cells are empty,
        meaning all cards have been moved to the foundations.

        Returns:
            bool: True if the game is solved, False otherwise.
        """
        return not any(self.cascades) and not any(self.free_cells)

    def can_move_to_foundation(self, card):
        """
        Determines if a given card can be moved to its respective foundation pile.

        A card can be moved to the foundation if:
        - The foundation is empty, and the card is an Ace (rank 1).
        - The card follows the correct ascending sequence for its suit.

        Args:
            card (Card): The card being checked for movement.

        Returns:
            bool: True if the card can be moved to the foundation, False otherwise.
        """
        if not card:
            return False
        foundation = self.foundations[card.suit]
        return (
            not foundation
            and card.rank == 1
            or (foundation and card.rank == foundation[-1].rank + 1)
        )

    def can_move_to_cascade(self, card, cascade_idx):
        """
        Determines if a given card can be moved to a specified cascade.

        A card can be moved to a cascade if:
        - The cascade is empty.
        - The card follows a descending sequence and alternates in color with the top card of the cascade.

        Args:
            card (Card): The card being checked for movement.
            cascade_idx (int): The index of the target cascade.

        Returns:
            bool: True if the card can be placed in the cascade, False otherwise.
        """

        if not card:
            return False
        cascade = self.cascades[cascade_idx]
        if not cascade:
            return True
        top_card = cascade[-1]
        return card.rank == top_card.rank - 1 and card.color != top_card.color

    def _is_valid_sequence(self, cards):
        if len(cards) <= 1:
            return True
        for i in range(len(cards) - 1):
            if not (
                cards[i].rank == cards[i + 1].rank + 1
                and cards[i].color != cards[i + 1].color
            ):
                return False
        return True

    def max_cards_movable(self, dest_idx=None):
        """
        Calculates the maximum number of cards that can be moved at once based on the number of free cells and empty cascades.

        The number of movable cards is determined by:
        - The number of available free cells.
        - The number of empty cascades, which increase mobility.

        The formula used is:
            (free cells + 1) * (2 ^ empty cascades)

        Args:
            dest_idx (int, optional): The index of the destination cascade (used to exclude it from empty cascade calculations). Defaults to None.

        Returns:
            int: The maximum number of cards that can be moved in a single action.
        """
        num_free_cells = self.free_cells.count(None)
        num_empty_cascades = sum(
            1
            for i, cascade in enumerate(self.cascades)
            if not cascade and (dest_idx is None or i != dest_idx)
        )
        return (num_free_cells + 1) * (2**num_empty_cascades)

    def get_valid_moves(self):
        """
        Generates a list of all valid moves available in the current game state.

        The method evaluates possible moves from cascades and free cells to:
        - The foundation (if the card is eligible).
        - An empty or valid cascade.
        - An available free cell.

        Additionally, it checks for "supermoves"—moving multiple validly sequenced cards at once.

        Returns:
            list: A list of tuples representing valid moves. Each tuple follows one of these formats:
                - ("foundation", source_type, source_idx, suit)  -> Move to foundation
                - ("free_cell", source_type, source_idx, free_cell_idx)  -> Move to a free cell
                - ("cascade", source_type, source_idx, dest_idx)  -> Move to a cascade
                - ("supermove", "cascade", src_idx, dest_idx, num_cards)  -> Multi-card sequence move
        """
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

    def get_automatic_foundation_moves(self):
        """
        Identifies moves that automatically transfer cards to the foundation.

        A card can be automatically moved if:
        - It is an Ace or a 2.
        - All lower-ranked cards of all suits are already in the foundation.

        The function checks both cascades and free cells for such moves.

        Returns:
            list: A list containing at most one automatic move, formatted as:
                  ("foundation", source_type, source_idx, suit).
        """
        global auto_moves_enabled
        if not auto_moves_enabled:
            return []

        auto_moves = []

        # Check all cascades for cards that can be moved to the foundation
        for i, cascade in enumerate(self.cascades):
            if cascade:
                card = cascade[-1]
                if self.can_move_to_foundation(card):
                    # Check if all lower ranks of all suits are in the foundation
                    all_lower_present = True
                    for rank in range(1, card.rank):
                        for suit in ["H", "D", "C", "S"]:
                            foundation = self.foundations[suit]
                            if not foundation or foundation[-1].rank < rank:
                                all_lower_present = False
                                break
                        if not all_lower_present:
                            break
                    if all_lower_present:
                        auto_moves.append(("foundation", "cascade", i, card.suit))
                        return auto_moves  # Return the first move found

        # Check free cells for cards that can be moved to the foundation
        for i, card in enumerate(self.free_cells):
            if card and self.can_move_to_foundation(card):
                all_lower_present = True
                for rank in range(1, card.rank):
                    for suit in ["H", "D", "C", "S"]:
                        foundation = self.foundations[suit]
                        if not foundation or foundation[-1].rank < rank:
                            all_lower_present = False
                            break
                    if not all_lower_present:
                        break
                if all_lower_present:
                    auto_moves.append(("foundation", "free_cell", i, card.suit))
                    return auto_moves  # Return the first move found

        return []  # No moves found

    def get_valid_moves_with_automoves(self, original_get_valid_moves=None):
        """
        Retrieves valid moves, prioritizing automatic foundation moves if enabled.

        If automatic foundation moves are available, they take precedence.
        Otherwise, standard valid moves are retrieved.

        Args:
            original_get_valid_moves (function, optional): If provided, uses this function
                to get valid moves, avoiding recursion.

        Returns:
            list: A list of valid moves, including automatic foundation moves if applicable.
        """
        auto_moves = self.get_automatic_foundation_moves()
        if auto_moves:
            return auto_moves

        # If original method is provided, use it to avoid recursion
        if original_get_valid_moves:
            return original_get_valid_moves(self)
        else:
            # Otherwise, use direct implementation to avoid calling self.get_valid_moves() which would cause recursion
            return self._get_valid_moves_implementation()

    def _get_valid_moves_implementation(self):
        """
        Direct implementation of `get_valid_moves`, avoiding recursion.

        Identifies valid moves from cascades and free cells to:
        - The foundation (if applicable).
        - An empty or valid cascade.
        - An available free cell.
        - Multi-card "supermoves" if conditions allow.

        Returns:
            list: A list of valid moves, including ("foundation", ...), ("cascade", ...), and ("supermove", ...).
        """
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

    def make_move(self, move, is_player_move=False):
        """
        Executes a move, updating the game state accordingly.

        Moves can be of the following types:
        - "foundation": Moves a card to the foundation.
        - "free_cell": Moves a card to an empty free cell.
        - "cascade": Moves a card to another cascade.
        - "supermove": Moves multiple sequenced cards at once.

        Args:
            move (tuple): The move to be executed.
            is_player_move (bool): Whether the move was made by the player.

        Updates:
            - Modifies the game state by moving the card(s).
            - Records moves in `player_moves` (if player-move) or `moves`.
        """
        global last_moved_card
        move_type, source_type, source_idx, dest = move[0], move[1], move[2], move[3]
        if move_type == "supermove":
            num_cards = move[4]
            cards = self.cascades[source_idx][-num_cards:]
            self.cascades[source_idx] = self.cascades[source_idx][:-num_cards]
            self.cascades[dest].extend(cards)
            if solving and paused:
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
        if is_player_move:
            self.player_moves.append(
                ("manual" if move_type != "foundation" else "auto", move)
            )
        else:
            self.moves.append(move)

    def auto_move_to_foundations(self):
        """
        Automatically moves cards to foundations when eligible.

        Cards are moved only if:
        - `auto_moves_enabled` is active.
        - The player has made at least one manual move.
        - All lower-ranked cards of all suits are already in the foundation.

        Moves are executed in a loop until no more automatic moves are available.

        Returns:
            list: A list of automatic moves made.
        """
        global auto_moves_enabled
        if (
            not auto_moves_enabled or not self.player_moves
        ):  # Only after first manual move
            return []
        auto_moves = []
        changed = True
        while changed:
            changed = False
            for i, cascade in enumerate(self.cascades):
                if cascade:
                    card = cascade[-1]
                    if self.can_move_to_foundation(card):
                        all_lower_present = True
                        for rank in range(1, card.rank):
                            for suit in ["H", "D", "C", "S"]:
                                foundation = self.foundations[suit]
                                if not foundation or foundation[-1].rank < rank:
                                    all_lower_present = False
                                    break
                            if not all_lower_present:
                                break
                        if all_lower_present:
                            auto_moves.append(("foundation", "cascade", i, card.suit))
                            self.make_move(
                                ("foundation", "cascade", i, card.suit),
                                is_player_move=True,
                            )
                            self.player_moves[-1] = (
                                "auto",
                                ("foundation", "cascade", i, card.suit),
                            )  # Tag as automove
                            changed = True
                            break
            if not changed:
                for i, card in enumerate(self.free_cells):
                    if card and self.can_move_to_foundation(card):
                        all_lower_present = True
                        for rank in range(1, card.rank):
                            for suit in ["H", "D", "C", "S"]:
                                foundation = self.foundations[suit]
                                if not foundation or foundation[-1].rank < rank:
                                    all_lower_present = False
                                    break
                            if not all_lower_present:
                                break
                        if all_lower_present:
                            auto_moves.append(("foundation", "free_cell", i, card.suit))
                            self.make_move(
                                ("foundation", "free_cell", i, card.suit),
                                is_player_move=True,
                            )
                            self.player_moves[-1] = (
                                "auto",
                                ("foundation", "free_cell", i, card.suit),
                            )  # Tag as automove
                            changed = True
                            break
        return auto_moves

    def undo_last_move(self):
        """
        Undoes the last move made by the player, either manual or automatic.

        The function removes the last action from the list of player moves and
        reverts the board state to the previous configuration. The move is checked
        to determine whether it was a cascade, free cell, or foundation move, and
        the state of the relevant piles (cascades, foundations, and free cells)
        is updated accordingly.

        Returns:
            bool: Returns True if the move was successfully undone, False if no
                  moves are available to undo.
        """
        if not self.player_moves:
            return False
        last_action = self.player_moves.pop()
        _, move = last_action  # Ignore action_type, treat all moves the same

        move_type, source_type, source_idx, dest = move
        if move_type == "supermove":
            num_cards = move[4]
            cards = self.cascades[dest][-num_cards:]
            self.cascades[dest] = self.cascades[dest][:-num_cards]
            self.cascades[source_idx].extend(cards)
        else:
            if move_type == "foundation":
                card = self.foundations[dest].pop()
            elif move_type == "free_cell":
                card = self.free_cells[dest]
                self.free_cells[dest] = None
            else:  # cascade
                card = self.cascades[dest].pop()
            if source_type == "cascade":
                self.cascades[source_idx].append(card)
            else:  # free_cell
                self.free_cells[source_idx] = card

        return True

    def handle_click(self, x, y):
        """
        Handles the click event on the game board and processes the player's actions.

        Depending on the coordinates of the click, the function selects a card or
        sequence of cards, or determines the destination for the selected card(s).
        It also makes the corresponding move if valid, such as moving a card to a
        cascade, foundation, or free cell. Additionally, the function provides
        feedback on valid moves for the player and updates the game state accordingly.

        Args:
            x (int): The x-coordinate of the mouse click on the game board.
            y (int): The y-coordinate of the mouse click on the game board.

        Returns:
            None: The function modifies the game state directly based on the click.
        """
        global \
            selected_card, \
            selected_source, \
            hint_move, \
            selected_sequence, \
            selected_sequence_source

        if selected_card is None and selected_sequence is None:
            for i, cascade in enumerate(self.cascades):
                if (
                    cascade
                    and 50 + i * (CARD_WIDTH + CARD_MARGIN)
                    <= x
                    <= 50 + i * (CARD_WIDTH + CARD_MARGIN) + CARD_WIDTH
                ):
                    for j in range(len(cascade)):
                        card_y = 250 + j * 30
                        if card_y <= y <= card_y + CARD_HEIGHT:
                            if j < len(cascade) - 1:
                                sequence = cascade[j:]
                                if (
                                    self._is_valid_sequence(sequence)
                                    and len(sequence) <= self.max_cards_movable()
                                ):
                                    selected_sequence = sequence
                                    selected_sequence_source = ("cascade", i, j)
                                    return
                            if j == len(cascade) - 1:
                                selected_card = cascade[-1]
                                selected_source = ("cascade", i)
                                return
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

        else:
            move_made = False

            if selected_sequence is not None:
                for i in range(8):
                    cascade_x = 50 + i * (CARD_WIDTH + CARD_MARGIN)
                    if cascade_x <= x <= cascade_x + CARD_WIDTH and 250 <= y:
                        src_idx = selected_sequence_source[1]
                        src_start_idx = selected_sequence_source[2]
                        if src_idx != i and (
                            not self.cascades[i]
                            or (
                                selected_sequence[0].rank
                                == self.cascades[i][-1].rank - 1
                                and selected_sequence[0].color
                                != self.cascades[i][-1].color
                            )
                        ):
                            num_cards = len(selected_sequence)
                            self.make_move(
                                ("supermove", "cascade", src_idx, i, num_cards),
                                is_player_move=True,
                            )
                            self.auto_move_to_foundations()
                            move_made = True

            else:
                for i, suit in enumerate(["H", "D", "C", "S"]):
                    if (
                        SCREEN_WIDTH - 50 - CARD_WIDTH - i * (CARD_WIDTH + CARD_MARGIN)
                        <= x
                        <= SCREEN_WIDTH - 50 - i * (CARD_WIDTH + CARD_MARGIN)
                        and 100 <= y <= 220
                    ):
                        if (
                            self.can_move_to_foundation(selected_card)
                            and selected_card.suit == suit
                        ):
                            self.make_move(
                                (
                                    "foundation",
                                    selected_source[0],
                                    selected_source[1],
                                    suit,
                                ),
                                is_player_move=True,
                            )
                            self.auto_move_to_foundations()
                            move_made = True
                for i in range(8):
                    cascade_x = 50 + i * (CARD_WIDTH + CARD_MARGIN)
                    if cascade_x <= x <= cascade_x + CARD_WIDTH and 250 <= y:
                        if self.can_move_to_cascade(selected_card, i):
                            self.make_move(
                                ("cascade", selected_source[0], selected_source[1], i),
                                is_player_move=True,
                            )
                            self.auto_move_to_foundations()
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
                            self.make_move(
                                (
                                    "free_cell",
                                    selected_source[0],
                                    selected_source[1],
                                    i,
                                ),
                                is_player_move=True,
                            )
                            self.auto_move_to_foundations()
                            move_made = True

            if move_made:
                selected_card = selected_source = selected_sequence = (
                    selected_sequence_source
                ) = hint_move = None
            else:
                selected_card = selected_source = selected_sequence = (
                    selected_sequence_source
                ) = None

    def meta_heuristic(self):
        """
        Metaheuristic scoring function for FreeCell game state evaluation
        Lower score indicates a better game state

        Scoring Strategy:
        - Penalize incomplete foundations
        - Penalize occupied free cells
        - Penalize suboptimal card sequences
        """
        score = 0

        # Foundations Scoring
        # Heavily penalize incomplete foundations
        for suit, cards in self.foundations.items():
            # Higher penalty for fewer cards in foundations
            score += (
                13 - len(cards)
            ) * 50  # More points for fewer cards in foundations

        # Free Cells Evaluation
        # Penalize occupied free cells
        occupied_free_cells = sum(1 for cell in self.free_cells if cell)
        score += occupied_free_cells * 100  # High penalty for each occupied free cell

        # Cascade Analysis
        # Penalize suboptimal sequences and color patterns
        for cascade in self.cascades:
            sequence_penalty = 0

            # Analyze card sequences
            for i in range(len(cascade) - 1):
                # Penalty for non-decreasing rank sequence
                if not (cascade[i].rank == cascade[i + 1].rank + 1):
                    sequence_penalty += 20

                # Penalty for same color adjacency
                if cascade[i].color == cascade[i + 1].color:
                    sequence_penalty += 10

            score += sequence_penalty

        # Mobility Penalty
        # Penalize limited move possibilities
        mobility_penalty = self.calculate_mobility_penalty()
        score += mobility_penalty

        return score

    def calculate_mobility_penalty(self):
        """
        Calculate mobility penalty for the game state

        Focuses on:
        - Number of potentially unmovable cards
        - Lack of move opportunities
        """
        mobility_penalty = 0

        # Check movability of cards
        for cascade_idx, cascade in enumerate(self.cascades):
            if not cascade:
                continue

            # Check top card of each cascade
            top_card = cascade[-1]

            # Check if top card can move to foundations
            if not self.can_move_to_foundation(top_card):
                # Check if top card can move to any other cascade
                move_possible = False
                for other_idx in range(len(self.cascades)):
                    if other_idx != cascade_idx and self.can_move_to_cascade(
                        top_card, other_idx
                    ):
                        move_possible = True
                        break

                # If no move is possible, add mobility penalty
                if not move_possible:
                    mobility_penalty += 50

        # Additional penalty for lack of free cells
        empty_free_cells = 4 - sum(1 for cell in self.free_cells if cell)
        mobility_penalty += (4 - empty_free_cells) * 50

        return mobility_penalty

    def meta_heuristic2(self):
        """
        Computes a score for the current state of the game using a custom meta-heuristic.

        The function calculates a score based on the following criteria:
        - A negative score is applied for each card in the foundations, with a penalty of 10 points per card.
        - A positive score is awarded for each free cell occupied by a card, with 5 points for each card.
        - A positive score is applied for each pair of consecutive cards in the cascades that are not in the correct sequence (i.e., rank and color mismatched).

        Returns:
            int: The computed score reflecting the current game state.
        """
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

    def heuristic1(self):
        """
        Computes the heuristic value based on the total number of cards missing from the foundations.

        The heuristic is the difference between 52 (total number of cards in the game) and the sum of the cards
        in the foundations across all suits.

        Returns:
            int: The number of cards missing to complete the foundations.
        """
        total_missing = 52 - sum(
            len(self.foundations[suit]) for suit in ["H", "D", "C", "S"]
        )
        return total_missing

    def heuristic2(self):
        """
        Computes the total minimum number of moves required to complete the foundations based on the current game state.

        The function calculates the number of moves required by considering the cards in the cascades and free cells,
        estimating how many moves are needed to get each card to its respective foundation.

        Returns:
            int: The estimated minimum number of moves required to complete the game.
        """
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

    def heuristic3(self):
        """
        Computes the estimated minimum number of moves required to complete the foundations using a more detailed approach.

        The function calculates the minimum number of moves by processing each card in the cascades and free cells,
        considering the blockers (cards in the way) and the gap between the current card rank and the required rank
        in the foundations. It accounts for cards already moved to the foundations and estimates the required moves
        based on the current game state.

        Returns:
            int: The estimated total number of moves required to complete the game.
        """
        # Track cards in foundations
        cards_in_foundations = {
            suit: set(card.rank for card in self.foundations[suit])
            for suit in ["H", "D", "C", "S"]
        }

        total_min_moves = 0
        # Track next rank needed for each suit
        next_rank_needed = {
            suit: max(cards_in_foundations[suit], default=0) + 1
            for suit in ["H", "D", "C", "S"]
        }

        # Track which cards have been "moved" to foundation (suit, rank)
        moved_to_foundation = set(
            (suit, rank)
            for suit in cards_in_foundations
            for rank in cards_in_foundations[suit]
        )

        # Flatten all cards with context
        all_cards = []
        for i, cascade in enumerate(self.cascades):
            for j, card in enumerate(cascade):
                all_cards.append((card, "cascade", i, j))
        for i, card in enumerate(self.free_cells):
            if card:
                all_cards.append((card, "free_cell", i, 0))

        # Sort by suit and rank (low to high)
        all_cards.sort(key=lambda x: (x[0].suit, x[0].rank))

        # Process cards sequentially
        for card, location, idx, pos in all_cards:
            suit = card.suit
            rank = card.rank

            if rank >= next_rank_needed[suit]:
                if location == "cascade":
                    # Count blockers, excluding cards already "moved"
                    cascade = self.cascades[idx]
                    blockers = 0
                    for blocking_card in cascade[pos + 1 :]:  # Cards above current card
                        if (
                            blocking_card.suit,
                            blocking_card.rank,
                        ) not in moved_to_foundation:
                            blockers += 1
                else:  # free_cell
                    blockers = 0

                if rank == next_rank_needed[suit]:
                    # Exact next card needed
                    moves = max(1, blockers + 1)  # 1 to move to foundation + blockers
                    total_min_moves += moves
                    next_rank_needed[suit] = rank + 1
                    moved_to_foundation.add((suit, rank))  # Mark as moved
                else:
                    # Higher than needed, estimate with gap
                    gap = rank - next_rank_needed[suit]
                    moves = max(1, blockers + gap + 1)
                    total_min_moves += moves

        return total_min_moves

    def __lt__(self, other):
        return self.heuristic3() < other.heuristic3()

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
        solution_index=0,
    ):
        """
        Renders the graphical interface of the FreeCell Solitaire game, including
        the game state, cards, buttons, and other interactive elements. This method
        is responsible for updating the visual elements based on the current game state.

        Parameters:
        - highlight_move (tuple, optional): Specifies the move to highlight, represented by a tuple. Default is None.
        - stats (dict, optional): Contains game statistics, such as score or time, to display on the screen. Default is None.
        - algorithm (str, optional): The algorithm currently in use (e.g., "A*", "Greedy"). Default is "A*".
        - hint_move (tuple, optional): Specifies a move to provide as a hint. Default is None.
        - solution_index (int, optional): Index representing the current solution step if the game is being solved automatically. Default is 0.

        This function draws:
        - The game screen with all cells (free cells, cascades, foundations) and their respective cards.
        - Controls and buttons for actions such as "Solve", "New Game", "Step Back", "Pause", and "Undo".
        - Additional information such as time, number of moves, and algorithm in use.
        - Highlighted moves or hints as visual cues for the user.
        - Dynamic updates based on the game’s progress, including handling player mode and solver mode.
        """
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
        difficulties = [("Easy", "easy", LIGHT_GREEN), ("Hard", "hard", LIGHT_RED)]
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

        # Add move counter - positioned near the game number
        moves_count = len(self.player_moves) if player_mode else solution_index
        moves_text = small_font.render(f"Moves: {moves_count}", True, WHITE)
        screen.blit(moves_text, (20, SCREEN_HEIGHT - 90))  # Position above game number

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
            # Add Step Back button (to the left of pause button)
            step_back_rect = pygame.Rect(SCREEN_WIDTH - 340, button_y, 100, 40)
            pygame.draw.rect(
                screen, (0, 140, 0), step_back_rect
            )  # Same green color as Step button
            pygame.draw.rect(screen, BLACK, step_back_rect, 1)
            step_back_text = small_font.render("Step Back", True, WHITE)
            screen.blit(step_back_text, (SCREEN_WIDTH - 325, button_y + 10))

            # Existing pause button
            pause_rect = pygame.Rect(SCREEN_WIDTH - 230, button_y, 100, 40)
            pygame.draw.rect(screen, DARK_GRAY, pause_rect)
            pygame.draw.rect(screen, BLACK, pause_rect, 1)
            pause_text = small_font.render(
                "Pause" if not paused else "Resume", True, WHITE
            )
            screen.blit(pause_text, (SCREEN_WIDTH - 215, button_y + 10))

            # Existing step button
            step_rect = pygame.Rect(SCREEN_WIDTH - 120, button_y, 100, 40)
            pygame.draw.rect(screen, (0, 140, 0), step_rect)
            pygame.draw.rect(screen, BLACK, step_rect, 1)
            step_text = small_font.render("Step", True, WHITE)
            screen.blit(step_text, (SCREEN_WIDTH - 105, button_y + 10))

        button_pos_x = SCREEN_WIDTH - 150
        button_pos_y = 250
        if not solving and not player_mode:
            play_rect = pygame.Rect(button_pos_x, button_pos_y, 130, 30)
            pygame.draw.rect(screen, BLUE, play_rect)
            pygame.draw.rect(screen, BLACK, play_rect, 1)
            play_text = small_font.render("I want to play", True, WHITE)
            screen.blit(play_text, (button_pos_x + 5, button_pos_y + 5))

            # Solver Auto Moves Button below "I want to play"
            global auto_moves_enabled
            solver_auto_rect = pygame.Rect(button_pos_x, button_pos_y + 40, 130, 30)
            if auto_moves_enabled:
                pygame.draw.rect(screen, LIGHT_GREEN, solver_auto_rect)
                pygame.draw.rect(screen, BLACK, solver_auto_rect, 1)
                auto_text = small_font.render("AutoMove On", True, BLACK)
            else:
                pygame.draw.rect(screen, LIGHT_RED, solver_auto_rect)
                pygame.draw.rect(screen, BLACK, solver_auto_rect, 1)
                auto_text = small_font.render("AutoMove off", True, BLACK)
            screen.blit(auto_text, (button_pos_x + 10, button_pos_y + 45))

        elif player_mode and not solving and not game_ended:
            hint_rect = pygame.Rect(button_pos_x, button_pos_y, 100, 30)
            pygame.draw.rect(screen, YELLOW, hint_rect)
            pygame.draw.rect(screen, BLACK, hint_rect, 1)
            hint_text = small_font.render("Hint", True, BLACK)
            screen.blit(hint_text, (button_pos_x + 15, button_pos_y + 5))
            # Add Undo button below Hint
            if self.player_moves:  # Show only if there are moves to undo
                undo_rect = pygame.Rect(
                    button_pos_x, button_pos_y + 40, 100, 30
                )  # 40px below Hint
                pygame.draw.rect(screen, LIGHT_ORANGE, undo_rect)
                pygame.draw.rect(screen, BLACK, undo_rect, 1)
                undo_text = small_font.render("Undo", True, BLACK)
                screen.blit(undo_text, (button_pos_x + 15, button_pos_y + 45))
            # Add Auto On/Off buttons below Undo - for Player mode auto-moves
            auto_rect_y = button_pos_y + 80  # 80px below Hint (40px Undo + 40px gap)
            player_auto_enabled = auto_moves_enabled  # We're using the same variable for both player and solver
            if player_auto_enabled:
                auto_off_rect = pygame.Rect(button_pos_x, auto_rect_y, 100, 30)
                pygame.draw.rect(screen, RED, auto_off_rect)
                pygame.draw.rect(screen, BLACK, auto_off_rect, 1)
                auto_off_text = small_font.render("Auto Off", True, WHITE)
                screen.blit(auto_off_text, (button_pos_x + 10, auto_rect_y + 5))
            else:
                auto_on_rect = pygame.Rect(button_pos_x, auto_rect_y, 100, 30)
                pygame.draw.rect(screen, GREEN, auto_on_rect)
                pygame.draw.rect(screen, BLACK, auto_on_rect, 1)
                auto_on_text = small_font.render("Auto On", True, WHITE)
                screen.blit(auto_on_text, (button_pos_x + 15, auto_rect_y + 5))

        pygame.draw.rect(
            screen, DARK_GRAY, (SCREEN_WIDTH - 230, button_y - 50, 210, 30)
        )
        pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH - 230, button_y - 50, 210, 30), 1)
        speed_text = mini_font.render(
            f"Animation Speed: {animation_delay:.1f}s", True, WHITE
        )
        screen.blit(speed_text, (SCREEN_WIDTH - 220, button_y - 45))

        info_text = mini_font.render(
            "Shortcuts: Space=Pause, N=New Game, S=Step, B=Step Back, +/- = Speed",
            True,
            WHITE,
        )
        screen.blit(info_text, (200, SCREEN_HEIGHT - 20))

        # Search box and Load button
        search_box_rect = pygame.Rect(50, SCREEN_HEIGHT - 60, 120, 30)
        pygame.draw.rect(screen, WHITE, search_box_rect)
        pygame.draw.rect(screen, BLACK, search_box_rect, 1)
        search_label = small_font.render(
            "Game #:", True, WHITE
        )  # Changed from mini_font to small_font
        screen.blit(search_label, (search_box_rect.x - 50, search_box_rect.y + 5))
        search_content = small_font.render(search_text, True, BLACK)
        screen.blit(search_content, (search_box_rect.x + 5, search_box_rect.y + 5))

        # Add Load button
        load_button_rect = pygame.Rect(180, SCREEN_HEIGHT - 60, 60, 30)
        pygame.draw.rect(screen, BLUE, load_button_rect)
        pygame.draw.rect(screen, BLACK, load_button_rect, 1)
        load_text = small_font.render("Load", True, WHITE)
        screen.blit(load_text, (load_button_rect.x + 15, load_button_rect.y + 5))

        if current_game_number is not None:
            game_num_text = mini_font.render(
                f"Current Game: {current_game_number}", True, WHITE
            )
            screen.blit(
                game_num_text, (300, SCREEN_HEIGHT - 50)
            )  # Moved down from SCREEN_HEIGHT - 50

        if search_active:
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


class PerformanceMetrics:
    """
    A class to track and report performance metrics for algorithms, including time,
    memory usage, and search statistics. This class is useful for monitoring the
    efficiency of algorithms and understanding their resource consumption during execution.

    Attributes:
        start_time (float): Start time of the algorithm's execution in seconds.
        end_time (float): End time of the algorithm's execution in seconds.
        start_memory (float): Memory usage at the start of execution in MB.
        end_memory (float): Memory usage at the end of execution in MB.
        states_explored (int): Number of states explored by the algorithm.
        states_generated (int): Number of states generated by the algorithm.
        max_queue_size (int): Maximum size of the queue during search.
        solution_length (int): Length of the solution, measured in moves.
        max_depth_reached (int): Maximum depth reached in the search tree.
        branching_factor (float): Average branching factor during search.
        memory_used (float): Total memory used during the execution in MB.
        max_memory (float): Maximum memory usage recorded during execution in MB.
        peak_memory (float): Peak memory usage observed during the execution in MB.
        avg_memory (float): Average memory usage over the execution.
        memory_snapshots (list): List of memory snapshots taken throughout the execution.
    """

    def __init__(self):
        # Initialize process tracking and reset metrics
        self.process = psutil.Process(os.getpid())
        self.memory_snapshots = []
        self.reset()

    def reset(self):
        """
        Resets all performance metrics to their initial state, clearing memory snapshots
        and algorithm statistics.
        """
        self.start_time = 0
        self.end_time = 0
        self.start_memory = 0
        self.end_memory = 0
        self.states_explored = 0
        self.states_generated = 0
        self.max_queue_size = 0
        self.solution_length = 0
        self.max_depth_reached = 0
        self.branching_factor = 0
        self.memory_used = 0
        self.max_memory = 0
        self.peak_memory = 0
        self.avg_memory = 0
        self.memory_snapshots = []

        # Take initial memory snapshot
        self.track_peak_memory()

    def track_peak_memory(self):
        """
        Updates the peak memory usage if the current memory usage is higher
        than the previously recorded peak. Stores the current memory snapshot.
        """
        current = self.process.memory_info().rss / 1024 / 1024  # Convert bytes to MB
        self.memory_snapshots.append(current)
        if current > self.peak_memory:
            self.peak_memory = current

    def sample_memory(self):
        """
        Takes a snapshot of the current memory usage for calculating average memory usage.
        """
        current = self.process.memory_info().rss / 1024 / 1024  # MB
        self.memory_snapshots.append(current)

    def start(self):
        """
        Begins performance tracking by recording the start time and initial memory usage.
        Clears any garbage from memory to ensure accurate measurements.
        """
        self.start_time = time.time()
        # Force garbage collection for accurate memory measurement
        import gc

        gc.collect()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.start_memory  # Reset peak memory tracking

    def stop(self, solution=None):
        """
        Ends performance tracking by recording the end time, final memory usage, and
        the solution length if provided.

        Args:
            solution (optional): The solution found by the algorithm, used to measure solution length.
        """
        self.end_time = time.time()
        self.track_peak_memory()  # Final memory check

        # Ensure memory measurements are stable
        time.sleep(0.1)
        import gc

        gc.collect()

        self.end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        if solution:
            self.solution_length = len(solution)

    def print_report(self, algorithm_name):
        """
        Generate and print a comprehensive performance report for the algorithm.

        Args:
            algorithm_name: Name of the algorithm being evaluated
        """
        elapsed_time = self.end_time - self.start_time

        # Calculate memory difference with noise handling
        memory_diff = self.end_memory - self.start_memory
        if abs(memory_diff) < 0.1:  # Treat small differences as measurement noise
            self.memory_used = self.peak_memory - self.start_memory
        else:
            self.memory_used = max(0.01, memory_diff)  # Ensure positive value

        # Calculate average memory usage
        if self.memory_snapshots:
            self.avg_memory = sum(self.memory_snapshots) / len(self.memory_snapshots)

        print("\n" + "=" * 50)
        print(f"PERFORMANCE REPORT - {algorithm_name}")
        print("=" * 50)
        print(f"Time used: {elapsed_time:.4f} seconds")
        print(f"Memory used: {self.memory_used:.2f} MB")
        print(f"Average memory: {self.avg_memory:.2f} MB")
        print(f"States explored: {self.states_explored}")
        print(f"States generated: {self.states_generated}")
        if elapsed_time > 0:
            print(f"States per second: {self.states_explored / elapsed_time:.2f}")
        print(f"Maximum queue size: {self.max_queue_size}")
        print(f"Solution length: {self.solution_length} moves")
        print(f"Maximum depth reached: {self.max_depth_reached}")

        # Get platform-specific peak memory usage
        system = platform.system()
        if system == "Windows":
            try:
                # Windows-specific memory tracking
                mem_info = self.process.memory_info()
                if hasattr(mem_info, "peak_wset"):
                    self.max_memory = mem_info.peak_wset / 1024 / 1024  # MB
                else:
                    self.max_memory = self.peak_memory
            except:
                self.max_memory = self.peak_memory
        else:
            # For macOS, Linux and others, use tracked peak value
            self.max_memory = self.peak_memory

        print(f"Peak memory usage: {self.max_memory:.2f} MB")
        print("=" * 50)


def load_game_from_file(game_number):
    """
    Loads a FreeCell game from a file.

    Args:
        game_number (int): The game number to load. The file path is expected to be
                            "games/game{game_number}.txt".

    Returns:
        FreeCellGame: The game object containing the cascades, free cells, and foundations,
                      or None if there was an error loading the game.

    Raises:
        ValueError: If the file contains invalid card data, such as an invalid suit.
    """
    global current_game_number
    try:
        file_path = f"games/game{game_number}.txt"
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        game = FreeCellGame()
        game.cascades = [[] for _ in range(8)]
        game.free_cells = [None] * 4
        game.foundations = {"H": [], "D": [], "C": [], "S": []}

        rows = [row.strip() for row in content.split("\n") if row.strip()]
        for row_idx, row in enumerate(rows):
            cards = [card.strip() for card in row.split("\t") if card.strip()]
            for col_idx, card_str in enumerate(cards):
                if col_idx >= 8:
                    break
                if len(card_str) >= 3 and card_str[:2] == "10":
                    rank = 10
                    suit_char = card_str[2]
                else:
                    rank_char = card_str[0]
                    suit_char = card_str[1]
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
                suit_map = {"♥": "H", "♦": "D", "♣": "C", "♠": "S"}
                suit = suit_map.get(suit_char)
                if not suit:
                    raise ValueError(f"Invalid suit in card: {card_str}")
                game.cascades[col_idx].append(Card(suit, rank))

        print(f"Successfully loaded game {game_number}")
        current_game_number = game_number
        return game
    except Exception as e:
        print(f"Error loading game {game_number}: {e}")
        return None


def save_solution_to_file(
    game_number, solution, metrics, current_algorithm, initial_game=None
):
    """
    Saves the solution of a FreeCell game to a file, along with the performance metrics and
    the initial game state if available.

    Args:
        game_number (int): The game number to be saved in the filename.
        solution (list): The list of moves that make up the solution for the game.
        metrics (PerformanceMetrics): The performance metrics of the algorithm used to solve the game.
        current_algorithm (str): The name of the algorithm used to solve the game.
        initial_game (FreeCellGame, optional): The initial game state. If provided, it will be written
                                                at the top of the solution file.

    Returns:
        bool: True if the solution was successfully saved, False if there was an error.

    Raises:
        IOError: If there is an issue with file access or writing.
    """
    if game_number is None:
        os.makedirs("solutions", exist_ok=True)
        existing_files = os.listdir("solutions")
        unknown_count = 1
        while (
            f"solution_game_unknown{unknown_count}_{current_algorithm.replace('*', '')}.txt"
            in existing_files
        ):
            unknown_count += 1
        game_number = f"unknown{unknown_count}"

    os.makedirs("solutions", exist_ok=True)

    algorithm = current_algorithm.replace("*", "")
    filename = f"solutions/solution_game_{game_number}_{algorithm}.txt"

    try:
        with open(filename, "w", encoding="utf-8") as file:
            # Write the initial game state at the top of the file if available
            if initial_game:
                # Get the maximum depth of any cascade
                max_depth = max(len(cascade) for cascade in initial_game.cascades)

                # Create a transposed representation of the cascades
                for row_idx in range(max_depth):
                    row = []
                    for cascade in initial_game.cascades:
                        if row_idx < len(cascade):
                            card = cascade[row_idx]
                            ranks = {1: "A", 11: "J", 12: "Q", 13: "K"}
                            rank_str = ranks.get(card.rank, str(card.rank))
                            suit_symbols = {"H": "♥", "D": "♦", "C": "♣", "S": "♠"}
                            row.append(f"{rank_str}{suit_symbols[card.suit]}")
                        else:
                            row.append("")
                    file.write("\t".join(row) + "\n")

                file.write("\n\n")

            # Write solution information
            file.write(f"Solution for Game {game_number}\n")
            file.write("=" * 50 + "\n\n")

            # Write performance metrics
            elapsed_time = metrics.end_time - metrics.start_time

            file.write("Performance Metrics:\n")
            file.write("-" * 50 + "\n")
            file.write(f"Time taken: {elapsed_time:.2f} seconds\n")
            file.write(f"Memory used:{metrics.memory_used:.2f} MB\n")
            file.write(f"Average memory::{metrics.avg_memory:.2f} MB\n")
            file.write(f"Peak memory usage: {metrics.max_memory:.2f} MB\n")
            file.write(f"States explored: {metrics.states_explored}\n")
            file.write(f"States generated: {metrics.states_generated}\n")
            file.write(
                f"States per second: {metrics.states_explored / elapsed_time:.2f}\n"
            )
            file.write(f"Maximum queue size: {metrics.max_queue_size}\n")
            file.write(f"Maximum depth reached: {metrics.max_depth_reached}\n")
            file.write(f"Solution length: {len(solution)}\n")
            file.write(f"Peak memory usage:{metrics.max_memory:.2f} MB\n\n")

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
    """
    Formats a move into a human-readable string.

    Args:
        move (tuple): A tuple representing a move. The tuple has the following structure:
                      (move_type, source_type, source_idx, dest, [num_cards]).

    Returns:
        str: A formatted string describing the move.

    Notes:
        The move_type could be:
            - "supermove": Move multiple cards from one cascade to another.
            - "foundation": Move a card to the foundation.
            - "free_cell": Move a card to a free cell.
            - "cascade": Move a card from a source cascade to another cascade.
    """
    move_type, source_type, source_idx, dest = move[0], move[1], move[2], move[3]
    if move_type == "supermove":
        num_cards = move[4]
        return f"Move {num_cards} cards from Cascade {source_idx + 1} to Cascade {dest + 1}"
    if source_type == "cascade":
        source_desc = f"Cascade {source_idx + 1}"
    else:
        source_desc = f"Free Cell {source_idx + 1}"
    if move_type == "foundation":
        return f"Move card from {source_desc} to {dest} Foundation"
    elif move_type == "free_cell":
        return f"Move card from {source_desc} to Free Cell {dest + 1}"
    else:
        return f"Move card from {source_desc} to Cascade {dest + 1}"


def solve_freecell_astar(game):
    """
    Solves FreeCell using A* search with heuristic1. Returns solution moves
    and performance metrics, or (None, metrics) if no solution found within
    500,000 states.
    """
    metrics = PerformanceMetrics()
    metrics.start()
    queue = [(game.heuristic1(), id(game), game, [])]
    heapq.heapify(queue)
    visited = {hash(game)}
    max_states = 500000
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
            new_game.make_move(move)
            metrics.states_generated += 1
            new_hash = hash(new_game)
            if new_hash in visited:
                continue
            heapq.heappush(
                queue,
                (
                    new_game.heuristic1() + len(moves) + 1,
                    id(new_game),
                    new_game,
                    moves + [move],
                ),
            )
            visited.add(new_hash)
            metrics.max_queue_size = max(metrics.max_queue_size, len(queue))
    metrics.stop()
    return None, metrics


def solve_freecell_astar2(game):
    """
    Solves FreeCell using A* search with heuristic2. Returns solution moves
    and performance metrics, or (None, metrics) if no solution found within
    500,000 states.
    """
    metrics = PerformanceMetrics()
    metrics.start()
    queue = [(game.heuristic2(), id(game), game, [])]
    heapq.heapify(queue)
    visited = {hash(game)}
    max_states = 500000
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
            new_game.make_move(move)
            metrics.states_generated += 1
            new_hash = hash(new_game)
            if new_hash in visited:
                continue
            heapq.heappush(
                queue,
                (
                    new_game.heuristic2() + len(moves) + 1,
                    id(new_game),
                    new_game,
                    moves + [move],
                ),
            )
            visited.add(new_hash)
            metrics.max_queue_size = max(metrics.max_queue_size, len(queue))
    metrics.stop()
    return None, metrics


def solve_freecell_astar3(game):
    """
    Solves FreeCell using A* search with heuristic3. Returns solution moves
    and performance metrics, or (None, metrics) if no solution found within
    500,000 states.
    """
    metrics = PerformanceMetrics()
    metrics.start()
    queue = [(game.heuristic3(), id(game), game, [])]
    heapq.heapify(queue)
    visited = {hash(game)}
    max_states = 500000
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
            new_game.make_move(move)
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


def solve_freecell_metaheuristic(game):
    """
    Solves FreeCell using A* search with meta_heuristic. Returns solution moves
    and performance metrics, or (None, metrics) if no solution found within
    500,000 states.
    """
    metrics = PerformanceMetrics()
    metrics.start()
    queue = [(game.meta_heuristic(), id(game), game, [])]
    heapq.heapify(queue)
    visited = {hash(game)}
    max_states = 500000
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
            new_game.make_move(move)
            metrics.states_generated += 1
            new_hash = hash(new_game)
            if new_hash in visited:
                continue
            heapq.heappush(
                queue,
                (
                    new_game.meta_heuristic() + len(moves) + 1,
                    id(new_game),
                    new_game,
                    moves + [move],
                ),
            )
            visited.add(new_hash)
            metrics.max_queue_size = max(metrics.max_queue_size, len(queue))
    metrics.stop()
    return None, metrics


def solve_freecell_metaheuristic2(game):
    """
    Solves FreeCell using A* search with meta_heuristic2. Returns solution moves
    and performance metrics, or (None, metrics) if no solution found within
    500,000 states.
    """
    metrics = PerformanceMetrics()
    metrics.start()
    queue = [(game.meta_heuristic2(), id(game), game, [])]
    heapq.heapify(queue)
    visited = {hash(game)}
    max_states = 500000
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
            new_game.make_move(move)
            metrics.states_generated += 1
            new_hash = hash(new_game)
            if new_hash in visited:
                continue
            heapq.heappush(
                queue,
                (
                    new_game.meta_heuristic2() + len(moves) + 1,
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
    """
    Solves FreeCell using weighted A* search with heuristic3. Weight parameter
    controls heuristic influence. Returns solution moves and metrics, or
    (None, metrics) if no solution within 500,000 states.
    """
    metrics = PerformanceMetrics()
    metrics.start()
    queue = [(game.heuristic3() * weight, id(game), game, [])]
    heapq.heapify(queue)
    visited = set()
    visited.add(hash(game))
    max_states = 500000
    metrics.states_explored = 0
    metrics.states_generated = 1
    metrics.max_queue_size = 1

    while queue and metrics.states_explored < max_states:
        _, _, current_game, moves = heapq.heappop(queue)
        metrics.states_explored += 1
        metrics.max_depth_reached = max(metrics.max_depth_reached, len(moves))
        if current_game.is_solved():
            metrics.stop(moves)
            return moves, metrics
        valid_moves = current_game.get_valid_moves()
        for move in valid_moves:
            new_game = FreeCellGame(current_game)
            new_game.make_move(move)
            metrics.states_generated += 1
            new_hash = hash(new_game)
            if new_hash in visited:
                continue
            heapq.heappush(
                queue,
                (
                    len(moves) + 1 + weight * new_game.heuristic3(),
                    id(new_game),
                    new_game,
                    moves + [move],
                ),
            )
            visited.add(new_hash)
            metrics.max_queue_size = max(metrics.max_queue_size, len(queue))
    metrics.stop()
    return None, metrics


def get_hint(game):
    """
    Provides a hint (first move) to solve the current FreeCell game using the selected algorithm.

    This function uses the current algorithm selected by the user to solve the game and returns the
    first move in the solution. If no solution is found, it returns None.

    Args:
        game (FreeCellGame): The current state of the FreeCell game to be solved.

    Returns:
        str or None: The first move in the solution, formatted as a string, or None if no solution
                     could be found.

    Notes:
        The function maps the current algorithm (stored in `current_algorithm`) to a corresponding
        algorithm identifier and calls the `solve_freecell` function to get the solution.
        The first move of the solution is returned as the hint.
    """
    global current_algorithm
    algo_map = {
        "A*": "astar",
        "Greedy": "greedy",
        "BFS": "bfs",
        "DFS": "dfs",
        "IDS": "ids",
        "WA*": "weighted_astar",
        "Meta": "metaheuristic",
        "Meta2": "metaheuristic2",
        "A* Heu2": "astar2",
        "A* Heu3": "astar3",
    }
    algo_key = algo_map.get(current_algorithm, "astar")
    moves, _ = solve_freecell(game, algo_key)
    return moves[0] if moves else None


def solve_freecell_greedy(game):
    """
    Solves FreeCell using greedy search with heuristic3. Returns
    solution moves and metrics, or (None, metrics) if no solution found within
    500,000 states.
    """
    metrics = PerformanceMetrics()
    metrics.start()
    queue = [(game.heuristic3(), id(game), game, [])]
    heapq.heapify(queue)
    visited = {hash(game)}
    max_states = 500000
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
            new_game.make_move(move)
            metrics.states_generated += 1
            new_hash = hash(new_game)
            if new_hash in visited:
                continue
            heapq.heappush(
                queue, (new_game.heuristic3(), id(new_game), new_game, moves + [move])
            )
            visited.add(new_hash)
            metrics.max_queue_size = max(metrics.max_queue_size, len(queue))
    metrics.stop()
    return None, metrics


def solve_freecell_bfs(game):
    """
    Solves FreeCell using breadth-first search. Returns solution moves and
    metrics, or (None, metrics) if no solution found within 200,000 states.
    """
    metrics = PerformanceMetrics()
    metrics.start()
    queue = deque([(game, [])])
    visited = {hash(game)}
    max_states = 200000
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
            new_game.make_move(move)
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
    """
    Solves FreeCell using depth-first search with depth limit of 150. Returns
    solution moves and metrics, or (None, metrics) if no solution found within
    200,000 states.
    """
    metrics = PerformanceMetrics()
    metrics.start()
    stack = [(game, [])]
    visited = {hash(game)}
    max_states = 200000
    max_depth = 150
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
            new_game.make_move(move)
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
    """
    Solves FreeCell using iterative deepening search with max depth of 150. Returns
    solution moves and metrics, or (None, metrics) if no solution found within
    200,000 states.
    """
    metrics = PerformanceMetrics()
    metrics.start()
    max_states = 200000
    max_depth = 150

    for depth_limit in range(max_depth + 1):
        stack = [(game, [], 0)]
        visited = set()
        local_metrics = PerformanceMetrics()
        local_metrics.states_explored = local_metrics.states_generated = (
            local_metrics.max_queue_size
        ) = 1
        depth_reached = False

        while stack and local_metrics.states_explored < max_states:
            current_game, moves, depth = stack.pop()
            local_metrics.states_explored += 1
            local_metrics.max_depth_reached = max(
                local_metrics.max_depth_reached, depth
            )
            if depth >= depth_limit:
                depth_reached = True
                continue
            if current_game.is_solved():
                metrics.stop(moves)
                return moves, metrics
            for move in reversed(current_game.get_valid_moves()):
                new_game = FreeCellGame(current_game)
                new_game.make_move(move)
                new_hash = hash(new_game)
                if new_hash in visited:
                    continue
                stack.append((new_game, moves + [move], depth + 1))
                visited.add(new_hash)
                local_metrics.states_generated += 1
                local_metrics.max_queue_size = max(
                    local_metrics.max_queue_size, len(stack)
                )
        metrics.states_explored += local_metrics.states_explored
        metrics.states_generated += local_metrics.states_generated
        metrics.max_queue_size = max(
            metrics.max_queue_size, local_metrics.max_queue_size
        )
        if not depth_reached:
            break
    metrics.stop()
    return None, metrics


def solve_freecell(game, algorithm="astar"):
    """
    Solves FreeCell using specified algorithm (default: astar). Returns solution
    moves and metrics by delegating to the appropriate algorithm-specific solver.
    """
    return {
        "astar": solve_freecell_astar,
        "greedy": solve_freecell_greedy,
        "bfs": solve_freecell_bfs,
        "dfs": solve_freecell_dfs,
        "ids": solve_freecell_ids,
        "weighted_astar": solve_freecell_weighted_astar,
        "metaheuristic": solve_freecell_metaheuristic,
        "metaheuristic2": solve_freecell_metaheuristic2,
        "astar2": solve_freecell_astar2,
        "astar3": solve_freecell_astar3,
    }.get(algorithm, solve_freecell_astar)(game)


def main():
    """
    Main function to run the FreeCell game using Pygame. This function handles the game loop,
    user inputs (keyboard and mouse events), game state management, and algorithm selection for solving the game.

    The game starts with a shuffled deck and the user can choose from various algorithms to solve the puzzle.
    The game can run in two modes: automatic solving (with an algorithm) or player mode (where the player makes moves).

    The function also handles game state persistence, such as loading, saving, and resetting games.

    Game Flow:
    - Initialization of the game and setting the game state.
    - Event handling for key presses and mouse clicks.
    - Algorithm selection for solving the game automatically.
    - Execution of solving steps if the algorithm is selected.
    - Player interaction with game elements (making moves, pausing, etc.).
    - Drawing the game board and updating the display.

    Global Variables:
        - `animation_delay`: Delay between animations.
        - `paused`: Whether the game is paused.
        - `game_timer`: Timer to track the game duration.
        - `player_mode`: Whether the player is making manual moves.
        - `selected_card`, `selected_source`, `selected_sequence`, `selected_sequence_source`: Variables for card selection and movement.
        - `solving`: Flag indicating if the game is being solved automatically.
        - `hint_move`: Stores the next best move in player mode.
        - `last_moved_card`: Stores the last moved card.
        - `search_active`, `search_text`: Search functionality for loading games by number.
        - `current_game_number`: Number of the current game.
        - `current_algorithm`: The algorithm currently selected for solving the game.
        - `auto_moves_enabled`: Flag to enable or disable automatic moves for solving.
        - `initial_game`: Stores the initial game state for undo functionality.

    """
    global animation_delay, paused, game_timer, player_mode, selected_card, selected_source, selected_sequence, selected_sequence_source, solving, hint_move, last_moved_card, search_active, search_text, current_game_number, current_algorithm, auto_moves_enabled, initial_game  # Added initial_game to globals

    deck_size = 52
    game = FreeCellGame(deck_size=deck_size)
    solution = None
    solution_index = 0
    solving = False
    current_algorithm = "A* Heu3"
    stats = None
    clock = pygame.time.Clock()
    last_move_time = 0
    game_timer = 0.0
    start_time = time.time()
    algorithms = [
        "A* Heu3",
        "A* Heu2",
        "A*",
        "Greedy",
        "BFS",
        "DFS",
        "IDS",
        "WA*",
        "Meta",
        "Meta2",
    ]
    algorithm_index = 0
    hint_move = None
    last_moved_card = None
    current_game_number = None
    auto_moves_enabled = False  # Start with automoves disabled
    initial_game = None  # Initialize initial_game variable

    selected_sequence = None
    selected_sequence_source = None

    search_active = False
    search_text = ""
    search_box_rect = pygame.Rect(50, SCREEN_HEIGHT - 60, 120, 30)
    load_button_rect = pygame.Rect(180, SCREEN_HEIGHT - 60, 60, 30)

    os.makedirs("games", exist_ok=True)

    while True:
        """
        Game loop that continuously handles user input, updates the game state, and renders the game.
        
        The loop processes events like key presses, mouse clicks, and algorithm interactions, 
        and performs actions such as pausing the game, solving it, resetting it, or moving cards.
        
        It also tracks the time elapsed for gameplay and updates the display to reflect changes.
        """
        current_time = time.time()
        if not paused and not solving:
            game_timer = current_time - start_time

        for event in pygame.event.get():
            """
            Event handling for different user inputs (keyboard, mouse).
            
            Depending on the input, the function toggles pause, starts a new game, loads a saved game, 
            changes the algorithm, or handles player-specific actions such as making moves or undoing moves.
            """
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                """
                Handle keydown events for various actions such as:
                - Pausing the game (spacebar)
                - Navigating through the solution (S for next, B for previous)
                - Adjusting animation speed (equals and minus keys)
                """
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
                                initial_game = None
                                print(f"Loaded game {game_number}")
                            search_text = ""
                            search_active = False
                        except ValueError:
                            search_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        search_text = search_text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        search_active = False
                        search_text = ""
                    else:
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
                        initial_game = None
                    elif (
                        event.key == pygame.K_s
                        and solution
                        and solution_index < len(solution)
                    ):
                        game.make_move(solution[solution_index])
                        solution_index += 1
                    elif (
                        event.key == pygame.K_b
                        and solution
                        and solution_index > 0
                        and initial_game is not None
                    ):
                        solution_index -= 1
                        game = FreeCellGame(initial_game)
                        for i in range(solution_index):
                            game.make_move(solution[i])
                    elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                        animation_delay = max(0.1, animation_delay - 0.1)
                    elif event.key == pygame.K_MINUS:
                        animation_delay = min(2.0, animation_delay + 0.1)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                """
                Handle mouse button down events for:
                - Selecting a search box
                - Loading a saved game
                - Interacting with game control buttons
                - Making player moves or undoing them
                """
                x, y = pygame.mouse.get_pos()
                if search_box_rect.collidepoint((x, y)):
                    search_active = True
                elif load_button_rect.collidepoint((x, y)):
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
                            initial_game = None
                            print(f"Loaded game {game_number}")
                        search_text = ""
                        search_active = False
                    except ValueError:
                        search_text = ""
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
                                "Greedy": "greedy",
                                "BFS": "bfs",
                                "DFS": "dfs",
                                "IDS": "ids",
                                "WA*": "weighted_astar",
                                "Meta": "metaheuristic",
                                "Meta2": "metaheuristic2",
                                "A* Heu2": "astar2",
                                "A* Heu3": "astar3",
                            }
                            algo_key = algo_map.get(current_algorithm, "astar")
                            print(f"Using algorithm: {algo_key}")

                            # Create a deep copy of the initial game state before solving
                            initial_game = FreeCellGame(game)

                            # Create a wrapper for solving with automoves
                            original_get_valid_moves = FreeCellGame.get_valid_moves

                            def automove_wrapper(self):
                                """Wrapper that applies automoves logic using original method to avoid recursion"""
                                auto_moves = self.get_automatic_foundation_moves()
                                if auto_moves:
                                    return auto_moves
                                return original_get_valid_moves(self)

                            # Replace get_valid_moves with our wrapper
                            FreeCellGame.get_valid_moves = automove_wrapper

                            try:
                                solution_data, metrics = solve_freecell(game, algo_key)
                                solution = solution_data
                                solution_index = 0
                                hint_move = last_moved_card = None
                                selected_sequence = selected_sequence_source = None

                                if solution:
                                    print(
                                        f"{current_algorithm} solution found with {len(solution)} moves!"
                                    )
                                    metrics.print_report(f"{current_algorithm}")
                                    stats = (solution, metrics.states_explored)
                                    save_solution_to_file(
                                        current_game_number,
                                        solution,
                                        metrics,
                                        current_algorithm,
                                        initial_game,
                                    )
                                else:
                                    print(f"No {current_algorithm} solution found.")
                                    metrics.print_report(
                                        f"{current_algorithm} (No Solution)"
                                    )
                                    solving = False
                            finally:
                                # Restore the original method
                                FreeCellGame.get_valid_moves = original_get_valid_moves

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
                            initial_game = None
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
                            initial_game = None
                        elif 750 <= x <= 1120 and 15 <= y <= 45:
                            difficulty = (
                                "easy"
                                if 750 <= x <= 820
                                else "hard"
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
                            initial_game = None
                    elif (
                        SCREEN_WIDTH - 340 <= x <= SCREEN_WIDTH - 240
                        and SCREEN_HEIGHT - 60 <= y <= SCREEN_HEIGHT - 20
                        and solution
                        and solution_index > 0
                        and initial_game is not None
                    ):
                        solution_index -= 1
                        game = FreeCellGame(initial_game)
                        for i in range(solution_index):
                            game.make_move(solution[i])
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
                        not solving
                        and not player_mode
                        and SCREEN_WIDTH - 150 <= x <= SCREEN_WIDTH - 20
                        and 290 <= y <= 320
                    ):
                        # Toggle auto moves for solver
                        auto_moves_enabled = not auto_moves_enabled
                    elif (
                        player_mode
                        and not solving
                        and SCREEN_WIDTH - 150 <= x <= SCREEN_WIDTH - 50
                        and 250 <= y <= 280
                        and not (game.is_solved() or not game.get_valid_moves())
                    ):
                        hint_move = get_hint(game)
                    elif (
                        player_mode
                        and not solving
                        and SCREEN_WIDTH - 150 <= x <= SCREEN_WIDTH - 50
                        and 290 <= y <= 320
                        and game.player_moves
                    ):  # Undo button click area
                        game.undo_last_move()
                    elif (
                        player_mode
                        and not solving
                        and SCREEN_WIDTH - 150 <= x <= SCREEN_WIDTH - 50
                        and 330 <= y <= 360
                    ):  # Auto On/Off button click area
                        auto_moves_enabled = not auto_moves_enabled
                    elif player_mode and not solving:
                        game.handle_click(x, y)
                    if not search_box_rect.collidepoint((x, y)):
                        search_active = False

        if solving and solution and solution_index < len(solution) and not paused:
            if current_time - last_move_time >= animation_delay:
                highlight_move = solution[solution_index]
                game.draw(
                    highlight_move=highlight_move,
                    stats=stats,
                    algorithm=current_algorithm,
                    solution_index=solution_index,
                )
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
                hint_move=hint_move if player_mode and not solving else None,
                solution_index=solution_index,
            )

        clock.tick(60)


if __name__ == "__main__":
    main()
